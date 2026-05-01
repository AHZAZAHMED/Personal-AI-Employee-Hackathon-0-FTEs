"""
Currency Updates Skill - Agent Entry Point

Fetches live currency exchange rates and updates the system's
conversion table for multi-currency invoice processing.
"""

from typing import Dict, Any
from .service import CurrencyService


def update_currency_rates(
    show_comparison: bool = False
) -> Dict[str, Any]:
    """
    Fetch live currency exchange rates and update the system.

    Use this skill when:
    - You need current exchange rates for multi-currency invoices
    - Processing emails with foreign currency amounts
    - Running daily/weekly rate maintenance
    - Updating the system's currency conversion table

    Fetches rates from the European Central Bank (free API, no auth needed),
    converts to USD base, and updates the rates file used by email-to-invoice
    processing.

    Args:
        show_comparison: Whether to include old vs new rate comparison

    Returns:
        Dict with keys:
        - success (bool): Whether rates were updated
        - rates_updated (int): Number of currencies updated
        - message (str): Status message
        - comparison (dict|None): Old vs new comparison (if show_comparison=True)
        - error (str|None): Error message if failed

    Example:
        result = update_currency_rates(show_comparison=True)
        print(f"Updated: {result['rates_updated']} rates")
    """
    try:
        service = CurrencyService()
        return service.run_update(show_comparison=show_comparison)
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_current_rates() -> Dict[str, Any]:
    """Get current currency conversion rates."""
    try:
        service = CurrencyService()
        return {"success": True, "rates": service.get_current_rates()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def convert_currency(
    amount: float,
    from_currency: str
) -> Dict[str, Any]:
    """
    Convert an amount to USD using current rates.

    Args:
        amount: Amount in source currency
        from_currency: Source currency code (e.g., 'GBP', 'EUR', 'PKR')

    Returns:
        Dict with converted amount in USD
    """
    try:
        service = CurrencyService()
        usd_amount = service.convert(amount, from_currency)
        return {"success": True, "amount": amount, "from_currency": from_currency,
                "usd_amount": round(usd_amount, 2)}
    except Exception as e:
        return {"success": False, "error": str(e)}
