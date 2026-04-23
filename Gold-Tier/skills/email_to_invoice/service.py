"""
Email to Invoice Service - Core Business Logic

Processes customer emails to create invoices in Odoo:
- Extracts customer info (name, email, company, service, amount)
- Detects and converts currency to USD
- Creates customer and invoice in Odoo
- Sends invoice email reply
- Logs the action

No agent-related code — pure business logic only.
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Currency conversion rates (to USD) - Auto-updated
# Last updated: 2026-04-21 14:51:41
CURRENCY_RATES = {
    'USD': 1.0,
    'AED': 0.2727,  # 1 AED = 0.2727 USD
    'AUD': 0.6545,  # 1 AUD = 0.6545 USD
    'CAD': 0.7448,  # 1 CAD = 0.7448 USD
    'CNY': 0.1385,  # 1 CNY = 0.1385 USD
    'GBP': 1.2706,  # 1 GBP = 1.2706 USD
    'INR': 0.0120,  # 1 INR = 0.0120 USD
    'JPY': 0.0068,  # 1 JPY = 0.0068 USD
    'PKR': 0.0036,  # 1 PKR = 0.0036 USD
    'SAR': 0.2667,  # 1 SAR = 0.2667 USD
}


# Try Odoo
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
try:
    from odoo_mcp_server import OdooAccountingMCP
    ODOO_AVAILABLE = True
except Exception:
    ODOO_AVAILABLE = False

# Try Email Sender
try:
    from email_sender_mcp import EmailSender
    EMAIL_AVAILABLE = True
except Exception:
    EMAIL_AVAILABLE = False


class EmailInvoiceService:
    """Core email-to-invoice processing service."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.logs = self.vault / "Logs"
        self.done = self.vault / "Done"
        for d in [self.logs, self.done]:
            d.mkdir(parents=True, exist_ok=True)

        # Odoo
        if ODOO_AVAILABLE:
            try:
                self.odoo = OdooAccountingMCP({
                    "url": "http://localhost:8069",
                    "db": "odoo",
                    "username": "admin123@example.com",
                    "password": "admin"
                })
            except Exception:
                self.odoo = None
        else:
            self.odoo = None

        # Email sender
        if EMAIL_AVAILABLE:
            try:
                self.email_sender = EmailSender(str(vault_path))
            except Exception:
                self.email_sender = None
        else:
            self.email_sender = None

    def extract_customer_info(self, email_content: str) -> Dict[str, Any]:
        """Extract customer info from email content."""
        customer = {"name": "", "email": "", "company": "", "phone": "", "service": "", "amount": 0.0}

        email_match = re.search(r"from:\s*.+?<([^>]+)>", email_content, re.IGNORECASE)
        if email_match:
            customer["email"] = email_match.group(1).strip()

        name_match = re.search(r"from:\s*([^<]+)<", email_content, re.IGNORECASE)
        if name_match:
            customer["name"] = name_match.group(1).strip()

        if not customer["name"] and customer["email"]:
            customer["name"] = customer["email"].split("@")[0].replace(".", " ").title()

        company_patterns = [
            r"(?:from|at|working at)\s+([A-Z][A-Za-z\s]+(?:Inc|Ltd|Corp|LLC|Company))",
            r"([A-Z][A-Za-z\s]+(?:Inc|Ltd|Corp|LLC))",
        ]
        for pattern in company_patterns:
            cm = re.search(pattern, email_content)
            if cm:
                customer["company"] = cm.group(1)
                break

        service_keywords = {
            "consulting": ["consulting", "consultation", "consult"],
            "support": ["support", "help", "assistance"],
            "development": ["development", "develop", "build", "create"],
            "design": ["design", "mockup", "prototype"],
            "training": ["training", "teach", "workshop"]
        }
        for service, keywords in service_keywords.items():
            if any(kw in email_content.lower() for kw in keywords):
                customer["service"] = service
                break

        amount_matches = re.findall(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", email_content)
        if amount_matches:
            amounts = [float(a.replace(",", "")) for a in amount_matches]
            customer["amount"] = max(amounts)
        else:
            customer["amount"] = 500.0

        return customer

    def detect_currency(self, email_content: str) -> str:
        """Detect currency from email content."""
        currency_patterns = {
            "PKR": [r"PKR", r"Rs\.?\s*\d", r"rupee", r"pakistani"],
            "EUR": [r"EUR", r"€", r"euro", r"eur"],
            "GBP": [r"GBP", r"£", r"pound", r"sterling"],
            "INR": [r"INR", r"₹", r"rupee", r"indian"],
            "CAD": [r"CAD", r"C\$", r"canadian"],
            "AUD": [r"AUD", r"A\$", r"australian"],
            "JPY": [r"JPY", r"¥", r"yen", r"japanese"],
            "CNY": [r"CNY", r"元", r"yuan", r"chinese"],
            "AED": [r"AED", r"Dh", r"dirham", r"uae"],
            "SAR": [r"SAR", r"﷼", r"riyal", r"saudi"],
        }
        for currency, patterns in currency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, email_content, re.IGNORECASE):
                    return currency
        return "USD"

    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """Convert amount to USD."""
        if from_currency == "USD":
            return amount
        rate = CURRENCY_RATES.get(from_currency, 1.0)
        return amount * rate

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def create_customer_and_invoice(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer and invoice in Odoo."""
        result = {"customer_created": False, "invoice_created": False,
                   "customer_id": None, "invoice_id": None, "invoice_number": "", "errors": []}

        if not self.odoo:
            result["errors"].append("Odoo not available")
            return result

        # Create customer
        customer_result = self.odoo.create_customer(
            name=customer["name"], email=customer["email"],
            company=customer.get("company"), phone=customer.get("phone"))

        if customer_result.get("success"):
            result["customer_created"] = True
            result["customer_id"] = customer_result.get("customer_id")
        else:
            err = customer_result.get("error", "") + customer_result.get("message", "")
            if "already exists" in err.lower():
                result["customer_created"] = True
                result["customer_id"] = customer_result.get("customer_id")
            else:
                result["errors"].append(customer_result.get("error", "Failed to create customer"))

        # Create invoice
        if result["customer_created"]:
            invoice_result = self.odoo.create_invoice(
                partner_name=customer["name"], partner_email=customer["email"],
                lines=[{"name": f"{customer['service'].title()} Service", "quantity": 1, "price_unit": customer["amount"]}])
            if invoice_result.get("success"):
                result["invoice_created"] = True
                result["invoice_id"] = invoice_result.get("invoice_id")
                result["invoice_number"] = invoice_result.get("invoice_number")
            else:
                result["errors"].append(invoice_result.get("error", "Failed to create invoice"))

        return result

    def send_invoice_email(self, customer: Dict[str, Any], invoice_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send invoice email to customer."""
        if not self.email_sender:
            return {"success": False, "error": "Email sender not available"}

        reference_id = datetime.now().strftime("%Y%m%d%H%M%S")
        subject = f"Invoice {invoice_result.get('invoice_number')} - {customer['name']}"
        body = f"""Dear {customer['name']},

Thank you for your interest in our {customer['service']} services.

Please find your invoice details below:

INVOICE INFORMATION
===================
Invoice Number: {invoice_result.get('invoice_number')}
Amount: ${customer['amount']:.2f}
Service: {customer['service'].title()} Service
Reference ID: {reference_id}

PAYMENT INSTRUCTIONS
====================
Please reference the Invoice Number when making payment.

Best regards,
AI Employee Response System
Automated Invoicing

---
Invoice Number: {invoice_result.get('invoice_number')}
Reference ID: {reference_id}
"""
        return self.email_sender.send_email(to=customer["email"], subject=subject, body=body)

    def log_action(self, customer: Dict[str, Any], invoice_result: Dict[str, Any], email_result: Dict[str, Any]):
        """Log the automation action."""
        entry = {
            "timestamp": datetime.now().isoformat(), "action": "email_to_invoice",
            "customer": customer,
            "invoice": {"created": invoice_result.get("invoice_created"),
                        "invoice_number": invoice_result.get("invoice_number"),
                        "amount": customer.get("amount")},
            "email": {"sent": email_result.get("success", False)}
        }
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}_invoices.jsonl"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log action: {e}")

    def process_email(self, email_content: str, send_invoice_email: bool = True) -> Dict[str, Any]:
        """
        Process a customer email to create an invoice.

        Args:
            email_content: Full email content including frontmatter
            send_invoice_email: Whether to send invoice email reply

        Returns:
            Dict with success, customer, invoice, email results
        """
        customer = self.extract_customer_info(email_content)
        detected_currency = self.detect_currency(email_content)
        customer["original_currency"] = detected_currency
        customer["original_amount"] = customer["amount"]
        if detected_currency != "USD":
            customer["amount"] = self.convert_to_usd(customer["amount"], detected_currency)

        invoice_result = self.create_customer_and_invoice(customer)

        email_result = {"success": False, "error": "Invoice not created"}
        if invoice_result.get("invoice_created") and send_invoice_email:
            email_result = self.send_invoice_email(customer, invoice_result)

        self.log_action(customer, invoice_result, email_result)

        return {
            "success": invoice_result.get("invoice_created", False),
            "customer": customer,
            "invoice": invoice_result,
            "email": email_result
        }
