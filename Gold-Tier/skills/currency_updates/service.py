"""
Currency Updates Service - Core Business Logic

Fetches live exchange rates from European Central Bank (free API),
converts to USD base, and provides currency conversion.

No agent-related code — pure business logic only.
"""

import json
import re
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Default fallback rates
DEFAULT_RATES = {
    'USD': 1.0, 'AED': 0.2727, 'AUD': 0.6545, 'CAD': 0.7448,
    'CNY': 0.1385, 'GBP': 1.2706, 'INR': 0.0120, 'JPY': 0.0068,
    'PKR': 0.0036, 'SAR': 0.2667,
}

# Path to rates in the email_to_invoice service
RATES_FILE = Path(__file__).parent.parent.parent / "skills" / "email_to_invoice" / "service.py"


class CurrencyService:
    """Core currency management service."""

    def __init__(self):
        self.rates = dict(DEFAULT_RATES)
        self._load_current_rates()

    def _load_current_rates(self):
        """Load current rates from email_to_invoice service."""
        if RATES_FILE.exists():
            try:
                content = RATES_FILE.read_text(encoding="utf-8")
                match = re.search(r"CURRENCY_RATES\s*=\s*\{([^}]+)\}", content, re.DOTALL)
                if match:
                    rates_block = match.group(1)
                    for line in rates_block.split("\n"):
                        line = line.strip().rstrip(",")
                        if "'" in line and ":" in line:
                            key, val = line.split(":", 1)
                            key = key.strip().strip("'\"")
                            val = val.strip().split("#")[0].strip()
                            try:
                                self.rates[key] = float(val)
                            except ValueError:
                                pass
            except Exception as e:
                logger.warning(f"Could not load current rates: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout)),
        reraise=True
    )
    def fetch_ecb_rates(self) -> Optional[Dict[str, float]]:
        """Fetch latest exchange rates from European Central Bank."""
        try:
            resp = requests.get("https://api.exchangerate.host/latest?base=EUR", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if "rates" in data:
                return data["rates"]
            logger.warning("No rates in ECB response")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch ECB rates: {e}")
            return None

    def convert_to_usd_base(self, eur_rates: Dict[str, float]) -> Dict[str, float]:
        """Convert EUR-based rates to USD-based rates."""
        if not eur_rates:
            return {}
        eur_usd = eur_rates.get("USD", 1.08)
        usd_rates = {}
        for currency, rate in eur_rates.items():
            if currency == "USD":
                usd_rates[currency] = 1.0
            elif rate > 0:
                usd_rates[currency] = (1.0 / rate) * eur_usd
        return usd_rates

    def update_rates_file(self, usd_rates: Dict[str, float]) -> bool:
        """
        Update CURRENCY_RATES in email_to_invoice/service.py.

        Args:
            usd_rates: USD-based rate dictionary

        Returns:
            True if file was updated
        """
        if not usd_rates or not RATES_FILE.exists():
            return False

        rates_text = f"# Currency conversion rates (to USD) - Auto-updated\n"
        rates_text += f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        rates_text += "CURRENCY_RATES = {\n"
        rates_text += "    'USD': 1.0,\n"
        for currency in sorted(usd_rates.keys()):
            if currency != "USD":
                rate = usd_rates[currency]
                rates_text += f"    '{currency}': {rate:.4f},  # 1 {currency} = {rate:.4f} USD\n"
        rates_text += "}\n"

        try:
            content = RATES_FILE.read_text(encoding="utf-8")
            pattern = r"# Currency conversion rates.*?CURRENCY_RATES = \{[^}]+\}"
            new_content = re.sub(pattern, rates_text, content, flags=re.DOTALL)
            if new_content == content:
                logger.warning("Could not find CURRENCY_RATES block")
                return False
            RATES_FILE.write_text(new_content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to update rates file: {e}")
            return False

    def run_update(self, show_comparison: bool = False) -> Dict[str, Any]:
        """
        Fetch live rates and update the system.

        Args:
            show_comparison: Include old vs new comparison

        Returns:
            Dict with update result
        """
        old_rates = dict(self.rates)
        result = {"success": False, "rates_updated": 0, "error": None, "comparison": None}

        # Fetch
        eur_rates = self.fetch_ecb_rates()
        if not eur_rates:
            result["error"] = "Failed to fetch ECB rates, using defaults"
            eur_rates = {"USD": 1.08, "GBP": 0.85, "INR": 90.0, "CAD": 1.45,
                         "AUD": 1.65, "JPY": 160.0, "CNY": 7.8, "PKR": 300.0,
                         "AED": 3.96, "SAR": 4.05}

        # Convert
        usd_rates = self.convert_to_usd_base(eur_rates)
        if not usd_rates:
            result["error"] = "Failed to convert rates to USD base"
            return result

        result["rates_updated"] = len(usd_rates)

        # Update file
        updated = self.update_rates_file(usd_rates)
        if updated:
            self.rates = usd_rates
            result["success"] = True
            result["message"] = f"Updated {len(usd_rates)} currency rates"

        # Comparison
        if show_comparison:
            comparison = {}
            for cur in sorted(set(list(old_rates.keys()) + list(usd_rates.keys()))):
                if cur == "USD":
                    continue
                old = old_rates.get(cur, 0)
                new = usd_rates.get(cur, 0)
                change = ((new - old) / old * 100) if old > 0 else 0
                comparison[cur] = {"old": round(old, 4), "new": round(new, 4), "change_pct": round(change, 2)}
            result["comparison"] = comparison

        return result

    def convert(self, amount: float, from_currency: str) -> float:
        """Convert an amount to USD using current rates."""
        if from_currency == "USD":
            return amount
        rate = self.rates.get(from_currency, 1.0)
        return amount * rate

    def get_current_rates(self) -> Dict[str, float]:
        """Get current currency rates."""
        return dict(self.rates)
