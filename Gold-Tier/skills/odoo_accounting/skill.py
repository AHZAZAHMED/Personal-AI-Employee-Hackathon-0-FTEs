"""
Odoo Accounting Skill - Agent Entry Point

Create invoices, record payments, get balances, list transactions,
and generate financial reports via Odoo accounting.
"""

from typing import Dict, Any, List, Optional
from .service import OdooAccountingService


def odoo_create_invoice(
    partner_name: str,
    partner_email: str,
    lines: List[Dict[str, Any]],
    invoice_type: str = "out_invoice",
    approval_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a customer invoice in Odoo accounting.

    **REQUIRES APPROVAL TOKEN** - This is a sensitive financial action that
    requires human approval. The approval_token parameter must be provided.

    Use this skill when:
    - Creating an invoice for a customer
    - Billing for services rendered
    - Generating vendor bills

    Args:
        partner_name: Customer name
        partner_email: Customer email (used to find or create the contact)
        lines: Invoice lines, e.g., [{"name": "Consulting", "quantity": 10, "price_unit": 50}]
        invoice_type: "out_invoice" for customer, "in_invoice" for vendor
        approval_token: Required approval token from human approval workflow

    Returns:
        Dict with success, invoice_id, invoice_number, amount_total, etc.

    Example:
        result = odoo_create_invoice(
            partner_name="Acme Corp",
            partner_email="billing@acme.com",
            lines=[{"name": "Web Design", "quantity": 1, "price_unit": 2000}],
            approval_token="secure_token_from_approval_workflow"
        )
    """
    # SECURITY: Verify approval token before executing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from approval_tokens import get_token_manager

    token_manager = get_token_manager()

    if not token_manager.verify_token(approval_token, "odoo_create_invoice"):
        return {
            "success": False,
            "error": "APPROVAL_REQUIRED",
            "message": "Invoice creation requires human approval. Invoice was NOT created."
        }

    # Token verified - proceed with execution
    try:
        service = OdooAccountingService()
        return service.create_invoice(partner_name, partner_email, lines, invoice_type)
    except Exception as e:
        return {"success": False, "error": str(e)}


def odoo_create_customer(
    name: str,
    email: str,
    phone: Optional[str] = None,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """Create a customer in Odoo."""
    try:
        service = OdooAccountingService()
        return service.create_customer(name, email, phone, company)
    except Exception as e:
        return {"success": False, "error": str(e)}


def odoo_record_payment(
    invoice_number: str,
    amount: float,
    payment_reference: Optional[str] = None,
    approval_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a payment for an invoice.

    **REQUIRES APPROVAL TOKEN** - This is a sensitive financial action that
    requires human approval. The approval_token parameter must be provided.

    Args:
        invoice_number: Invoice number (e.g., 'INV/2026/0001')
        amount: Payment amount
        payment_reference: Optional reference/note
        approval_token: Required approval token from human approval workflow

    Returns:
        Dict with success status and payment_id
    """
    # SECURITY: Verify approval token before executing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from approval_tokens import get_token_manager

    token_manager = get_token_manager()

    if not token_manager.verify_token(approval_token, "odoo_record_payment"):
        return {
            "success": False,
            "error": "APPROVAL_REQUIRED",
            "message": "Payment recording requires human approval. Payment was NOT recorded."
        }

    # Token verified - proceed with execution
    try:
        service = OdooAccountingService()
        return service.record_payment(invoice_number, amount, payment_reference)
    except Exception as e:
        return {"success": False, "error": str(e)}


def odoo_get_account_balance(
    account_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get account balance(s).

    Args:
        account_code: Specific account code (e.g., '1000' for cash), or None for all

    Returns:
        Dict with list of accounts and their balances
    """
    try:
        service = OdooAccountingService()
        return service.get_account_balance(account_code)
    except Exception as e:
        return {"success": False, "error": str(e)}


def odoo_list_transactions(
    days: int = 30,
    limit: int = 100
) -> Dict[str, Any]:
    """
    List recent posted transactions.

    Args:
        days: Days to look back
        limit: Max transactions

    Returns:
        Dict with transaction list
    """
    try:
        service = OdooAccountingService()
        return service.list_transactions(days=days, limit=limit)
    except Exception as e:
        return {"success": False, "error": str(e)}


def odoo_generate_financial_report(
    report_type: str = "profit_loss"
) -> Dict[str, Any]:
    """
    Generate a financial report.

    Args:
        report_type: "profit_loss" or "balance_sheet"

    Returns:
        Dict with report data
    """
    try:
        service = OdooAccountingService()
        return service.generate_financial_report(report_type)
    except Exception as e:
        return {"success": False, "error": str(e)}


def odoo_test_connection() -> Dict[str, Any]:
    """Test Odoo connection."""
    try:
        service = OdooAccountingService()
        return service.test_connection()
    except Exception as e:
        return {"success": False, "error": str(e)}
