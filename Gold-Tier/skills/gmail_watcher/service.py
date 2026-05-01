"""
Gmail Service - Core Business Logic

Handles Gmail API operations: authenticate, fetch unread messages,
decode messages, and create action files.
No agent-related code — pure business logic only.
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add scripts/ to path for base_watcher and error_recovery
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

logger = logging.getLogger(__name__)


class GmailService:
    """Core Gmail API service — authentication, fetching, decoding."""

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose',
    ]

    URGENT_KEYWORDS = [
        'urgent', 'asap', 'immediate', 'emergency',
        'invoice', 'payment', 'help'
    ]

    def __init__(
        self,
        vault_path: str = "AI_Employee_Vault",
        credentials_path: Optional[str] = None
    ):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        for d in [self.needs_action, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

        if credentials_path:
            self.credentials_path = Path(credentials_path)
        else:
            self.credentials_path = Path(__file__).parent.parent.parent / "credentials.json"

        self.token_path = self.vault_path / ".gmail_token.json"
        self.processed_ids_file = self.logs_dir / "gmail_processed_ids.json"
        self.processed_ids = self._load_processed_ids()
        self._service = None  # Lazy init — only auth when actually needed

    @property
    def service(self):
        """Lazy Gmail API connection — authenticates on first use only."""
        if self._service is None and GMAIL_API_AVAILABLE:
            self._service = self._authenticate()
        return self._service

    @service.setter
    def service(self, value):
        self._service = value

    def _load_processed_ids(self) -> set:
        """Load previously processed Gmail message IDs."""
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('message_ids', []))
            except Exception as e:
                logger.warning(f"Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed Gmail message IDs to disk."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'message_ids': list(self.processed_ids)
            }
            with open(self.processed_ids_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save processed IDs: {e}")

    def _authenticate(self):
        """Authenticate with Gmail API."""
        if not GMAIL_API_AVAILABLE:
            logger.error("Gmail API not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return None

        creds = None

        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
            except RefreshError:
                logger.warning("Token expired, will re-authenticate")
                self.token_path.unlink(missing_ok=True)
                creds = None

        if not creds or not creds.valid:
            if not self.credentials_path.exists():
                logger.error(f"Credentials file not found at {self.credentials_path}")
                return None

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Gmail authentication successful")
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                return None

        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def get_unread_messages(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch unread messages from Gmail.

        Args:
            max_results: Max messages to retrieve

        Returns:
            List of decoded message dicts
        """
        # Use _service to avoid triggering auth via property
        if not self._service:
            return []

        new_messages = []
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    decoded = self._decode_message(msg['id'])
                    if decoded:
                        subject_lower = decoded['subject'].lower()
                        snippet_lower = decoded.get('snippet', '').lower()
                        decoded['is_urgent'] = any(
                            kw in subject_lower or kw in snippet_lower
                            for kw in self.URGENT_KEYWORDS
                        )
                        new_messages.append(decoded)
                        self.processed_ids.add(msg['id'])

            self._save_processed_ids()

        except Exception as e:
            logger.error(f"Error fetching unread messages: {e}")

        return new_messages

    def _decode_message(self, msg_id: str) -> Optional[Dict[str, Any]]:
        """Decode a single Gmail message into a dict."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

            from_email = headers.get('From', 'Unknown')
            from_name = from_email
            if '<' in from_email:
                from_email = from_email.split('<')[1].strip('>')

            return {
                'id': msg_id,
                'from': from_email,
                'from_name': from_name,
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', 'No Subject'),
                'date': headers.get('Date', ''),
                'body': body,
                'snippet': message.get('snippet', '')
            }
        except Exception as e:
            logger.error(f"Error decoding message {msg_id}: {e}")
            return None

    def create_action_file(self, message: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in Needs_Action/ for an email.

        Args:
            message: Decoded email dict

        Returns:
            Path to created file
        """
        unique_id = message['id'][:8]
        priority = 'high' if message.get('is_urgent') else 'normal'

        suggested_actions = [
            "Read full email content",
            "Determine if reply needed",
            "Archive after processing"
        ]
        if message.get('is_urgent'):
            suggested_actions.insert(0, "URGENT: Respond within 24 hours")
        subj_lower = message['subject'].lower()
        if 'invoice' in subj_lower or 'payment' in subj_lower:
            suggested_actions.extend(["Forward to accounting", "Check payment status"])

        body_preview = message.get('body', '')[:500] or message.get('snippet', '')
        if len(message.get('body', '')) > 500:
            body_preview += "..."

        actions_md = "\n".join(f"- [ ] {a}" for a in suggested_actions)

        content = f"""---
type: email
from: {message['from']}
from_name: {message.get('from_name', message['from'])}
to: {message.get('to', '')}
subject: {message['subject']}
date: {message['date']}
gmail_id: {message['id']}
priority: {priority}
is_urgent: {str(message.get('is_urgent', False))}
created: {datetime.now().isoformat()}
status: pending
---

## Email Content

From: {message.get('from_name', message['from'])}
Subject: {message['subject']}

{body_preview}

## Suggested Actions

{actions_md}

---
*Created by AI Employee Gmail Watcher*
"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"EMAIL_{unique_id}_{timestamp}.md"
        filepath = self.needs_action / filename
        filepath.write_text(content, encoding='utf-8')
        return filepath

    def mark_processed(self, gmail_id: str) -> bool:
        """Mark a Gmail message as processed so it won't be fetched again."""
        self.processed_ids.add(gmail_id)
        self._save_processed_ids()
        return True

    def test_connection(self) -> bool:
        """Test Gmail API connection — triggers auth if not already connected."""
        if not self.service:  # Use property here to trigger auth on demand
            return False
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Gmail connected to: {profile.get('emailAddress', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Gmail connection test failed: {e}")
            return False
