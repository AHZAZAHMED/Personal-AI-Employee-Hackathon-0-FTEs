"""
Email Responder Skill - Agent Entry Point

Generates professional email responses (AI or fallback template)
and sends emails via Gmail API.
"""

from typing import Dict, Any, Optional
from .service import EmailResponseService


def email_generate_response(
    from_email: str,
    subject: str,
    body: str,
    date: str = "",
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Generate a professional email response for an incoming email.

    Use this skill when:
    - You need to draft a reply to an incoming email
    - Creating an auto-response for customer inquiries
    - Generating context-aware email content

    The system tries AI generation first, then falls back to a
    professional template if AI is unavailable or asks questions.

    Args:
        from_email: Sender's email address
                    (e.g., 'john@example.com' or 'John Smith <john@example.com>')
        subject: Email subject line
        body: Email body content
        date: Email date (optional)
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with keys:
        - success (bool): Whether generation succeeded
        - response (str): Generated email text
        - method (str): 'qwen_code_ai' or 'fallback_template'
        - error (str|None): Error message if failed

    Example:
        result = email_generate_response(
            from_email="client@example.com",
            subject="Inquiry about services",
            body="Hi, I am interested in your services."
        )
        print(result["response"])
    """
    try:
        service = EmailResponseService(vault_path=vault_path)
        return service.generate_response(from_email, subject, body, date)
    except Exception as e:
        return {"success": False, "response": "", "method": "error", "error": str(e)}


def email_send(
    to: str,
    subject: str,
    body: str,
    vault_path: str = "AI_Employee_Vault",
    in_reply_to: Optional[str] = None,
    approval_token: Optional[str] = None,
    correlation_id: str = "",
    approver: str = "",
    approval_time: str = ""
) -> Dict[str, Any]:
    """
    Send an email via Gmail API with audit logging.

    **REQUIRES APPROVAL TOKEN** - This is a sensitive action that requires
    human approval. The approval_token parameter must be provided and valid.

    Use this skill when:
    - You need to actually send/deliver an email
    - Replying to a customer after generating the response
    - Sending notifications or updates

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        vault_path: Path to AI Employee Vault
        in_reply_to: Gmail message ID to reply to (optional)
        approval_token: Required approval token from human approval workflow
        correlation_id: Correlation ID for audit trail (optional)
        approver: Who approved this action (optional)
        approval_time: When it was approved (optional)

    Returns:
        Dict with keys:
        - success (bool): Whether email was sent
        - message_id (str|None): Gmail message ID
        - method (str): 'gmail_api'
        - error (str|None): Error message if failed

    Example:
        # This will FAIL without approval token:
        result = email_send(
            to="client@example.com",
            subject="Re: Inquiry about services",
            body="Dear Client,\n\nThank you for your inquiry..."
        )
        # Returns: {"success": False, "error": "APPROVAL_REQUIRED"}

        # Correct usage (with approval token from orchestrator):
        result = email_send(
            to="client@example.com",
            subject="Re: Inquiry",
            body="...",
            approval_token="secure_token_from_approval_workflow",
            correlation_id="abc-123",
            approver="human",
            approval_time="2026-04-23T10:30:00"
        )
    """
    # SECURITY: Verify approval token before executing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from approval_tokens import get_token_manager

    token_manager = get_token_manager(vault_path)

    if not token_manager.verify_token(approval_token, "email_send"):
        return {
            "success": False,
            "message_id": None,
            "method": "blocked",
            "error": "APPROVAL_REQUIRED",
            "message": "This action requires human approval. Email was NOT sent."
        }

    # Token verified - proceed with execution
    try:
        service = EmailResponseService(vault_path=vault_path)
        return service.send_email(to, subject, body, in_reply_to,
                                 correlation_id, approver, approval_time)
    except Exception as e:
        return {"success": False, "message_id": None, "method": "error", "error": str(e)}


def email_generate_and_send(
    from_email: str,
    subject: str,
    body: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Generate a response AND send it in one call.

    Use this skill when:
    - You want to auto-reply to an email in one step
    - Combining response generation and sending

    Args:
        from_email: Original sender's email
        subject: Original subject line
        body: Original email body
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with keys from both generate and send operations
    """
    try:
        service = EmailResponseService(vault_path=vault_path)
        gen_result = service.generate_response(from_email, subject, body)
        if not gen_result.get("success"):
            return gen_result

        send_result = service.send_email(from_email, f"Re: {subject}", gen_result["response"])
        return {
            "success": send_result.get("success", False),
            "response": gen_result.get("response", ""),
            "method": gen_result.get("method", "unknown"),
            "send_method": send_result.get("method", "unknown"),
            "message_id": send_result.get("message_id"),
            "error": send_result.get("error")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def email_test_connection(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Test Gmail API connection.

    Returns:
        Dict with connection status and email address
    """
    try:
        service = EmailResponseService(vault_path=vault_path)
        return service.test_connection()
    except Exception as e:
        return {"success": False, "error": str(e)}
