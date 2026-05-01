"""
Email Responder Service - Core Business Logic

Generates email responses (AI or fallback) and sends emails via Gmail API.
No agent-related code — pure business logic only.
"""

import os
import re
import sys
import json
import base64
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add scripts/ to path for AI integration
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from claude_ai_integration import call_ai_model, call_claude
from audit_logger import get_audit_logger
from error_context import capture_error_context, log_error_with_context
from idempotency import check_idempotency, record_operation

logger = logging.getLogger(__name__)

# Try Gmail API
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False


class EmailResponseService:
    """Generate and send email responses."""

    URGENT_KEYWORDS = ['urgent', 'asap', 'immediate', 'emergency']

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.token_path = self.vault_path / ".gmail_token.json"
        self.credentials_path = Path(__file__).parent.parent.parent / "credentials.json"
        self._gmail_service = None

        # Initialize audit logger
        self.audit_logger = get_audit_logger(str(vault_path))

    # ─── Response Generation ──────────────────────────────────────

    def generate_response(self, from_email: str, subject: str,
                          body: str, date: str = "") -> Dict[str, Any]:
        """
        Generate an email response. Tries AI first, falls back to template.

        Returns dict with 'success', 'response', 'method'.
        """
        email_data = {"from": from_email, "subject": subject, "body": body, "date": date}

        # Try AI first
        result = self._try_ai_generation(email_data)
        if result and result.get("success"):
            return result

        # Fallback to template
        return self._fallback_template(email_data)

    def _try_ai_generation(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try Claude AI generation using smart retry logic."""
        # 1. Clean the email body
        body = email_data.get("body", "")
        for marker in ["## Email Content", "## Content", "## Suggested Actions", "---"]:
            body = body.replace(marker, "").strip()
        email_data["body"] = body

        max_retries = 2
        context_answers = {}

        for attempt in range(max_retries):
            # 2. Generate the strict prompt using custom methods
            context = self._analyze_context(email_data)
            prompt = self._build_ai_prompt(email_data, context)

            # Add previous answers to the prompt if retrying
            if context_answers:
                answers_text = "\n".join([f"- **{q}**: {a}" for q, a in context_answers.items()])
                prompt += f"\n\nPREVIOUS ANSWERS TO YOUR QUESTIONS:\n{answers_text}\n\nNOW GENERATE THE EMAIL:"

            # 3. Call Claude API
            start_time = datetime.now()
            try:
                logger.info(f"[AI] Attempt {attempt + 1}: Calling Claude API (timeout: 300s)...")
                response = call_ai_model(prompt, model="claude-sonnet-4-6")
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"[AI] Attempt {attempt + 1}: Claude responded in {elapsed:.1f}s")
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.error(f"[AI] Attempt {attempt + 1}: Claude call failed after {elapsed:.1f}s: {e}")
                return None

            if not response:
                logger.warning(f"[AI] Attempt {attempt + 1}: Claude returned empty response")
                continue

            # 4. Check if Claude asked a question instead of writing the email
            questions = self._extract_questions(response)
            if questions:
                logger.info(f"Claude asked questions on attempt {attempt + 1}: {questions}")

                # Check edge cases file for answers
                new_answers = self._find_answers_in_edge_cases(questions)
                context_answers.update(new_answers)

                # If we found answers to ALL questions, retry immediately
                if all(q in context_answers for q in questions):
                    continue

                # If we can't answer all questions, tell Claude to decide itself
                decision_prompt = "I cannot provide specific answers for all your questions. " \
                                  "Please use your best professional judgment to write the email anyway. " \
                                  "Make reasonable assumptions based on the context. " \
                                  "Do NOT ask more questions. Just write the email."
                response = call_ai_model(prompt + f"\n\nEXTRA INSTRUCTION: {decision_prompt}", model="claude-sonnet-4-6")

                if response:
                    # Save the new answers we found/generated
                    self._update_edge_cases_file(context_answers)
                    if self._is_valid_email(response):
                        return {"success": True, "response": response, "method": "claude_ai"}

                return None

            # 5. Validate response
            if "<email>" in response and "</email>" in response:
                response = response.split("<email>")[1].split("</email>")[0].strip()
            else:
                for prefix in ["Here is the email:", "Here's a reply:", "Certainly!", "Sure!", "I'd be happy to help:", "Here you go:"]:
                    if response.startswith(prefix):
                        response = response[len(prefix):].strip()

            if self._is_valid_email(response):
                return {"success": True, "response": response, "method": "claude_ai"}

            logger.warning(f"Attempt {attempt + 1} didn't look like an email, retrying...")

        logger.warning("AI generation failed after retries; falling back to template.")
        return None

    def _extract_questions(self, response: str) -> List[str]:
        """Extract questions from a text response."""
        import re
        # Match sentences ending with ?
        matches = re.findall(r'([^.!?]+\?)', response)
        return [m.strip() for m in matches if m.strip()]

    def _find_answers_in_edge_cases(self, questions: List[str]) -> Dict[str, str]:
        """Look for answers to questions in edge_cases.md."""
        answers = {}
        edge_file = self.vault_path / "Logs" / "email_edge_cases.md"
        if not edge_file.exists():
            return answers

        try:
            content = edge_file.read_text(encoding="utf-8").lower()
            for q in questions:
                q_lower = q.lower()
                # Simple keyword match: look for the question text in the file
                # and extract the answer associated with it
                if q_lower in content:
                    # Look for pattern: Q: ... A: ...
                    pattern = rf"{re.escape(q_lower)}.*?answer[:\s]+(.*?)(?:\n\n|$)"
                    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                    if match:
                        answers[q] = match.group(1).strip()
        except Exception as e:
            logger.error(f"Error reading edge cases file: {e}")
        
        return answers

    def _update_edge_cases_file(self, answers: Dict[str, str]):
        """Save new Q&A pairs to edge_cases.md."""
        edge_file = self.vault_path / "Logs" / "email_edge_cases.md"
        edge_file.parent.mkdir(parents=True, exist_ok=True)
        
        new_entries = []
        for q, a in answers.items():
            new_entries.append(f"**Q:** {q}\n**A:** {a}\n")
        
        try:
            if edge_file.exists():
                content = edge_file.read_text(encoding="utf-8")
            else:
                content = "# Email Edge Cases\n\n"
            
            content += "\n" + "\n".join(new_entries)
            edge_file.write_text(content, encoding="utf-8")
            logger.info(f"Updated edge cases file with {len(new_entries)} new entries")
        except Exception as e:
            logger.error(f"Failed to update edge cases file: {e}")

    def _is_valid_email(self, response: str) -> bool:
        """Check if response looks like a real email (has greeting and sign-off)."""
        lower = response.lower()
        has_greeting = any(w in lower for w in ["dear ", "hello ", "hi ", "good morning", "good afternoon"])
        has_signoff = any(w in lower for w in ["best regards", "sincerely", "kind regards", "thank you", "warm regards"])
        # Must have both greeting and sign-off, and be at least 50 chars
        return has_greeting and has_signoff and len(response) > 50

    def _analyze_context(self, email_data: Dict[str, Any]) -> Dict[str, str]:
        """Analyze email to extract context for AI."""
        from_email = email_data.get("from", "")
        full_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}".lower()

        recipient = "client"
        if any(w in from_email.lower() for w in ["@gmail", "@yahoo", "@hotmail"]):
            recipient = "individual"
        elif any(w in full_text for w in ["colleague", "team", "coworker"]):
            recipient = "colleague"
        elif any(w in full_text for w in ["vendor", "supplier", "partner"]):
            recipient = "vendor"

        topic = "general inquiry"
        if any(w in full_text for w in ["invoice", "payment", "bill", "price"]):
            topic = "billing/payment inquiry"
        elif any(w in full_text for w in ["meeting", "schedule", "appointment"]):
            topic = "scheduling request"
        elif any(w in full_text for w in ["support", "help", "issue", "problem"]):
            topic = "support request"
        elif any(w in full_text for w in ["complaint", "unhappy", "disappointed"]):
            topic = "complaint"

        tone = "professional and friendly"
        if any(w in full_text for w in ["urgent", "emergency", "asap"]):
            tone = "professional and prompt"
        elif any(w in full_text for w in ["complaint", "unhappy"]):
            tone = "professional and empathetic"

        sender_name = "Valued Contact"
        if "<" in from_email:
            sender_name = from_email.split("<")[0].strip()
        elif from_email:
            sender_name = from_email.split("@")[0].replace(".", " ").title()

        return {
            "recipient": recipient, "topic": topic, "tone": tone,
            "sender_name": sender_name,
            "outcome": "provide information and offer assistance"
        }

    def _build_ai_prompt(self, email_data: Dict[str, Any],
                          context: Dict[str, str]) -> str:
        """Build AI prompt for email generation - concise direct format."""
        return f"""Write a professional email reply. Output ONLY the email text.

Reply to: {email_data.get('from', 'Unknown')}
Subject: Re: {email_data.get('subject', 'No Subject')}

Original message:
{email_data.get('body', 'No content')}

Instructions:
- Start with "Dear {context['sender_name']},"
- Write 2-3 professional paragraphs
- Sign off with "Best regards, AI Employee Response System"
- Do NOT ask questions or provide commentary
- Just write the email reply
"""

    def _contains_questions(self, response: str) -> bool:
        """Check if response contains questions (bad — means AI didn't generate email).
        
        This check is now more lenient to avoid rejecting valid emails that 
        happen to contain question marks in legitimate content (e.g., "Please let us know 
        if you have any questions?").
        """
        question_patterns = [
            "could you please tell me", "can you please tell me",
            "would you mind telling me", "please provide me with",
            "please share with me", "please tell me what",
            "i need you to", "i need to know from you",
            "what is your", "what are your", "who is your",
            "how can i reach",
            "please let me know what you think?",
            "could you provide", "can you share",
        ]
        lower = response.lower()
        
        # Only count STRONG question patterns (not just "?" or "let me know")
        count = sum(1 for p in question_patterns if p in lower)
        
        # If 2+ strong question patterns found, it's asking questions
        if count >= 2:
            return True
        
        # Check if response looks like an email (has greeting and sign-off)
        has_greeting = any(w in lower for w in ["dear ", "hello ", "hi ", "good morning", "good afternoon"])
        has_signoff = any(w in lower for w in ["best regards", "sincerely", "kind regards", "thank you", "warm regards"])
        
        # If it has greeting and sign-off, it's probably a valid email
        if has_greeting and has_signoff:
            return False
        
        # Only reject if it has strong question patterns AND lacks email structure
        return count >= 1

    def _fallback_template(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate professional template response."""
        logger.info("[Fallback] Using template for email response")
        sender_email = email_data.get("from", "Unknown")
        subject = email_data.get("subject", "your inquiry")
        ts = datetime.now().strftime("%Y%m%d%H%M%S")

        sender_name = "Valued Contact"
        if "<" in sender_email:
            sender_name = sender_email.split("<")[0].strip()
        elif sender_email and sender_email != "Unknown":
            sender_name = sender_email.split("@")[0].replace(".", " ").title()

        response = f"""Dear {sender_name},


Thank you for contacting us regarding "{subject}".


We have received your message and our team will review it shortly. If your inquiry matches our current requirements, we will reach out to you regarding the next steps.


We appreciate your interest and look forward to assisting you.


Best regards,


AI Employee Response System
Automated Customer Service

---
Reference ID: {ts}
This is an automated response. For urgent matters, please reply with "URGENT" in the subject line."""

        return {"success": True, "response": response, "method": "fallback_template"}

    # ─── Email Sending ────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def send_email(self, to: str, subject: str, body: str,
                   in_reply_to: Optional[str] = None,
                   correlation_id: str = "",
                   approver: str = "",
                   approval_time: str = "") -> Dict[str, Any]:
        """
        Send an email via Gmail API with audit logging and idempotency.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            in_reply_to: Optional message ID for threading
            correlation_id: Correlation ID for audit trail and idempotency
            approver: Who approved this email
            approval_time: When it was approved

        Returns:
            Dict with success status and message_id or error
        """
        # Check idempotency - return cached result if already sent
        if correlation_id:
            cached = check_idempotency(correlation_id, 'email_send', str(self.vault_path))
            if cached:
                logger.info(f"Idempotency hit: Email already sent for {correlation_id}")
                return cached.get('result', {})

        # Log action started
        if correlation_id:
            self.audit_logger.log_action_started(
                correlation_id=correlation_id,
                action_type='email_send',
                actor='email_responder_skill',
                approver=approver,
                approval_time=approval_time,
                metadata={'to': to, 'subject': subject}
            )

        try:
            service = self._get_gmail_service()
            if not service:
                error = "Gmail API not available or not authenticated"

                # Log failure
                if correlation_id:
                    self.audit_logger.log_action_failed(
                        correlation_id=correlation_id,
                        action_type='email_send',
                        actor='email_responder_skill',
                        error=error,
                        approver=approver,
                        approval_time=approval_time
                    )

                return {"success": False, "error": error}

            # Create MIME message
            mime_msg = MIMEText(body.replace("\n\n", "\r\n\r\n").replace("\n", " "), "plain", "utf-8")
            mime_msg["From"] = "AI Employee"
            mime_msg["To"] = to
            mime_msg["Subject"] = subject
            if in_reply_to:
                mime_msg["In-Reply-To"] = in_reply_to

            raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")
            sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()

            # Log to old system (backward compatibility)
            self._log_event("email_sent", {"to": to, "subject": subject, "message_id": sent["id"]})

            # Log to audit system with approval chain
            if correlation_id:
                self.audit_logger.log_email_sent(
                    correlation_id=correlation_id,
                    to=to,
                    subject=subject,
                    approver=approver,
                    approval_time=approval_time,
                    result='success'
                )

            result = {"success": True, "message_id": sent["id"], "method": "gmail_api"}

            # Record successful operation for idempotency
            if correlation_id:
                record_operation(correlation_id, 'email_send', result, str(self.vault_path), ttl_hours=168)

            return result

        except Exception as e:
            logger.error(f"Email send failed: {e}")

            # Capture rich error context
            error_context = capture_error_context(e, locals(), correlation_id)
            log_error_with_context(error_context, str(self.vault_path))

            # Log failure to audit system
            if correlation_id:
                self.audit_logger.log_action_failed(
                    correlation_id=correlation_id,
                    action_type='email_send',
                    actor='email_responder_skill',
                    error=str(e),
                    approver=approver,
                    approval_time=approval_time
                )

            return {"success": False, "error": str(e), "error_id": error_context['error_id']}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def _get_gmail_service(self):
        """Lazy Gmail service init."""
        if self._gmail_service is not None:
            return self._gmail_service
        if not GMAIL_API_AVAILABLE:
            return None

        try:
            creds = None
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path),
                    ["https://www.googleapis.com/auth/gmail.send",
                     "https://www.googleapis.com/auth/gmail.compose"]
                )

            if not creds or not creds.valid:
                if self.credentials_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path),
                        ["https://www.googleapis.com/auth/gmail.send",
                         "https://www.googleapis.com/auth/gmail.compose"]
                    )
                    creds = flow.run_local_server(port=0)
                    with open(self.token_path, "w") as f:
                        f.write(creds.to_json())
                else:
                    return None

            self._gmail_service = build("gmail", "v1", credentials=creds)
            return self._gmail_service
        except Exception as e:
            logger.error(f"Gmail auth failed: {e}")
            return None

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log event to daily log."""
        entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type, **details}
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def test_connection(self) -> Dict[str, Any]:
        """Test Gmail API connection."""
        service = self._get_gmail_service()
        if not service:
            return {"success": False, "error": "Gmail API not available or not authenticated"}
        try:
            profile = service.users().getProfile(userId="me").execute()
            return {"success": True, "email": profile.get("emailAddress", "unknown")}
        except Exception as e:
            return {"success": False, "error": str(e)}
