"""
Email to Invoice Skill - Agent Entry Point

Processes customer emails to create invoices in Odoo.
Extracts customer info, detects currency, creates customer and invoice,
and optionally sends an invoice email reply.
"""

from typing import Dict, Any
from .service import EmailInvoiceService


def process_email_to_invoice(
    email_content: str,
    vault_path: str = "AI_Employee_Vault",
    send_invoice_email: bool = True,
    approval_token: str = None,
    correlation_id: str = "",
    approver: str = "",
    approval_time: str = ""
) -> Dict[str, Any]:
    """
    Process a customer email to create an invoice in Odoo.

    **REQUIRES APPROVAL TOKEN** - This is a sensitive action that requires
    human approval. The approval_token parameter must be provided and valid.

    Use this skill when:
    - A customer email requests services that need to be invoiced
    - You need to extract billing information from an email
    - Automating the email → invoice workflow

    The system extracts customer name, email, service type, and amount
    from the email content. It detects currency and converts to USD,
    creates the customer in Odoo (if new), creates an invoice, and
    optionally sends an invoice email reply.

    Args:
        email_content: Full email content including frontmatter
                       (from, subject, body with service details)
        vault_path: Path to AI Employee Vault
        send_invoice_email: Whether to send invoice email to customer
        approval_token: Required approval token from human approval workflow
        correlation_id: Correlation ID for audit trail (optional)
        approver: Who approved this action (optional)
        approval_time: When it was approved (optional)

    Returns:
        Dict with keys:
        - success (bool): Whether invoice was created
        - customer (dict): Extracted customer info
        - invoice (dict): Invoice creation result
        - email (dict): Email send result
        - error (str|None)

    Example:
        # This will FAIL without approval token:
        result = process_email_to_invoice(
            email_content="[full email with frontmatter]"
        )
        # Returns: {"success": False, "error": "APPROVAL_REQUIRED"}

        # Correct usage (with approval token from orchestrator):
        result = process_email_to_invoice(
            email_content="[full email]",
            approval_token="secure_token_from_approval_workflow",
            correlation_id="abc-123"
        )
    """
    # SECURITY: Verify approval token before executing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from approval_tokens import get_token_manager

    token_manager = get_token_manager(vault_path)

    if not token_manager.verify_token(approval_token, "invoice_create"):
        return {
            "success": False,
            "error": "APPROVAL_REQUIRED",
            "message": "This action requires human approval. Invoice was NOT created."
        }

    # Token verified - proceed with execution
    try:
        service = EmailInvoiceService(vault_path=vault_path)
        return service.process_email(email_content, send_invoice_email=send_invoice_email)
    except Exception as e:
        return {"success": False, "error": str(e)}
