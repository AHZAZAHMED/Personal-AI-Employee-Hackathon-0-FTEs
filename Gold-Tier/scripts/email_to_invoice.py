"""
Email-to-Invoice Automation for AI Employee - Gold Tier

Automated workflow:
1. Customer emails requesting service
2. AI extracts client info and service details
3. Creates customer in Odoo (if new)
4. Creates invoice in Odoo
5. Sends email reply with invoice
6. Logs action

Usage:
    python scripts/email_to_invoice.py --vault AI_Employee_Vault --email-file <path_to_email>
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Odoo MCP
try:
    from odoo_mcp_server import OdooAccountingMCP
    ODOO_AVAILABLE = True
except:
    ODOO_AVAILABLE = False
    print("⚠️  Odoo MCP not available")

# Currency conversion rates (to USD) - Auto-updated
# Last updated: 2026-03-23 15:30:21
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


# Import Email Sender
try:
    from email_sender_mcp import EmailSender
    EMAIL_AVAILABLE = True
except:
    EMAIL_AVAILABLE = False
    print("⚠️  Email Sender not available")


class EmailToInvoiceAutomation:
    """Automates invoice creation from customer emails."""
    
    def __init__(self, vault_path: str):
        """
        Initialize automation.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault = Path(vault_path)
        self.logs_folder = self.vault / 'Logs'
        self.done_folder = self.vault / 'Done'
        
        # Initialize Odoo
        if ODOO_AVAILABLE:
            self.odoo = OdooAccountingMCP({
                'url': 'http://localhost:8069',
                'db': 'odoo',
                'username': 'admin123@example.com',
                'password': 'admin'
            })
            print("✅ Odoo connected")
        else:
            self.odoo = None
        
        # Initialize Email Sender
        if EMAIL_AVAILABLE:
            self.email_sender = EmailSender(str(vault_path))
            print("✅ Email Sender connected")
        else:
            self.email_sender = None
    
    def extract_customer_info(self, email_content: str) -> Dict[str, Any]:
        """
        Extract customer information from email.
        
        Args:
            email_content: Email content
            
        Returns:
            Customer information dictionary
        """
        customer = {
            'name': '',
            'email': '',
            'company': '',
            'phone': '',
            'service': '',
            'amount': 0.0
        }
        
        # Extract email from frontmatter
        email_match = re.search(r'from:\s*.+?<([^>]+)>', email_content, re.IGNORECASE)
        if email_match:
            customer['email'] = email_match.group(1).strip()
        
        # Extract name from frontmatter
        name_match = re.search(r'from:\s*([^<]+)<', email_content, re.IGNORECASE)
        if name_match:
            customer['name'] = name_match.group(1).strip()
        
        # If name still empty, try to extract from email
        if not customer['name'] and customer['email']:
            customer['name'] = customer['email'].split('@')[0].replace('.', ' ').title()
        
        # Extract company name from email body
        company_patterns = [
            r'(?:from|at|working at)\s+([A-Z][A-Za-z\s]+(?:Inc|Ltd|Corp|LLC|Company))',
            r'([A-Z][A-Za-z\s]+(?:Inc|Ltd|Corp|LLC))',
        ]
        for pattern in company_patterns:
            company_match = re.search(pattern, email_content)
            if company_match:
                customer['company'] = company_match.group(1)
                break
        
        # Extract service type
        service_keywords = {
            'consulting': ['consulting', 'consultation', 'consult'],
            'support': ['support', 'help', 'assistance'],
            'development': ['development', 'develop', 'build', 'create'],
            'design': ['design', 'mockup', 'prototype'],
            'training': ['training', 'teach', 'workshop']
        }
        
        for service, keywords in service_keywords.items():
            if any(keyword in email_content.lower() for keyword in keywords):
                customer['service'] = service
                break
        
        # Extract amount (look for dollar amounts)
        amount_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', email_content)
        if amount_matches:
            # Take the largest amount (likely the total)
            amounts = [float(a.replace(',', '')) for a in amount_matches]
            customer['amount'] = max(amounts)
        else:
            # Default amount if not specified
            customer['amount'] = 500.0  # Default service fee
        
        return customer
    
    def detect_currency(self, email_content: str) -> str:
        """
        Detect currency from email content.
        
        Args:
            email_content: Email content
            
        Returns:
            Currency code (default: USD)
        """
        # Currency patterns
        currency_patterns = {
            'PKR': [r'PKR', r'Rs\.?\s*\d', r'rupee', r'pakistani'],
            'EUR': [r'EUR', r'€', r'euro', r'eur'],
            'GBP': [r'GBP', r'£', r'pound', r'sterling'],
            'INR': [r'INR', r'₹', r'rupee', r'indian'],
            'CAD': [r'CAD', r'C\$', r'canadian'],
            'AUD': [r'AUD', r'A\$', r'australian'],
            'JPY': [r'JPY', r'¥', r'yen', r'japanese'],
            'CNY': [r'CNY', r'元', r'yuan', r'chinese'],
            'AED': [r'AED', r'Dh', r'dirham', r'uae'],
            'SAR': [r'SAR', r'﷼', r'riyal', r'saudi'],
        }
        
        email_upper = email_content.upper()
        
        for currency, patterns in currency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, email_upper, re.IGNORECASE):
                    print(f"  Detected currency: {currency} (pattern: {pattern})")
                    return currency
        
        # Default to USD
        print("  No currency detected, defaulting to USD")
        return 'USD'
    
    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """
        Convert amount to USD.
        
        Args:
            amount: Amount in original currency
            from_currency: Original currency code
            
        Returns:
            Amount in USD
        """
        if from_currency == 'USD':
            return amount
        
        rate = CURRENCY_RATES.get(from_currency, 1.0)
        usd_amount = amount * rate
        
        print(f"  Converting {amount:.2f} {from_currency} to USD")
        print(f"  Rate: 1 {from_currency} = {rate:.4f} USD")
        print(f"  Converted amount: ${usd_amount:.2f} USD")
        
        return usd_amount
    
    def create_customer_and_invoice(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create customer and invoice in Odoo.
        
        Args:
            customer: Customer information
            
        Returns:
            Result dictionary
        """
        result = {
            'customer_created': False,
            'invoice_created': False,
            'customer_id': None,
            'invoice_id': None,
            'invoice_number': '',
            'errors': []
        }
        
        if not self.odoo:
            result['errors'].append('Odoo not available')
            return result
        
        # Step 1: Create customer
        print(f"Creating customer: {customer['name']} ({customer['email']})")
        customer_result = self.odoo.create_customer(
            name=customer['name'],
            email=customer['email'],
            company=customer['company'],
            phone=customer['phone']
        )
        
        if customer_result.get('success'):
            result['customer_created'] = True
            result['customer_id'] = customer_result.get('customer_id')
            print(f"✅ Customer created: ID {result['customer_id']}")
        else:
            result['errors'].append(customer_result.get('error', 'Failed to create customer'))
            # Try to continue with just name/email if customer exists
            if 'already exists' in customer_result.get('error', '').lower() or 'already exists' in customer_result.get('message', '').lower():
                # Search for existing customer
                result['customer_created'] = True
                result['customer_id'] = customer_result.get('customer_id')
        
        # Step 2: Create invoice
        if result['customer_created']:
            print(f"Creating invoice for ${customer['amount']:.2f} - Service: {customer['service']}")
            invoice_result = self.odoo.create_invoice(
                partner_name=customer['name'],
                partner_email=customer['email'],
                lines=[{
                    'name': f"{customer['service'].title()} Service",
                    'quantity': 1,
                    'price_unit': customer['amount']
                }]
            )
            
            if invoice_result.get('success'):
                result['invoice_created'] = True
                result['invoice_id'] = invoice_result.get('invoice_id')
                result['invoice_number'] = invoice_result.get('invoice_number')
                print(f"✅ Invoice created: {result['invoice_number']}")
            else:
                result['errors'].append(invoice_result.get('error', 'Failed to create invoice'))
        
        return result
    
    def send_invoice_email(self, customer: Dict[str, Any], invoice_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send invoice email to customer.
        
        Args:
            customer: Customer information
            invoice_result: Invoice creation result
            
        Returns:
            Email send result
        """
        if not self.email_sender:
            return {'success': False, 'error': 'Email sender not available'}
        
        # Compose email
        reference_id = datetime.now().strftime('%Y%m%d%H%M%S')
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

WHAT THESE NUMBERS MEAN
=======================
• Invoice Number ({invoice_result.get('invoice_number')}): Your official invoice identifier for tax and accounting purposes
• Reference ID ({reference_id}): Our internal tracking number for this transaction

PAYMENT INSTRUCTIONS
====================
Please reference the Invoice Number when making payment.

If you have any questions about this invoice, please contact us and quote your Invoice Number.

Best regards,

AI Employee Response System
Automated Invoicing

---
Invoice Number: {invoice_result.get('invoice_number')}
Reference ID: {reference_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send email
        result = self.email_sender.send_email(
            to=customer['email'],
            subject=subject,
            body=body
        )
        
        return result
    
    def log_action(self, customer: Dict[str, Any], invoice_result: Dict[str, Any], email_result: Dict[str, Any]):
        """
        Log the automation action.
        
        Args:
            customer: Customer information
            invoice_result: Invoice result
            email_result: Email result
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'email_to_invoice',
            'customer': customer,
            'invoice': {
                'created': invoice_result.get('invoice_created'),
                'invoice_number': invoice_result.get('invoice_number'),
                'amount': customer.get('amount')
            },
            'email': {
                'sent': email_result.get('success', False)
            }
        }
        
        # Save to log file
        log_file = self.logs_folder / f"{datetime.now().strftime('%Y-%m-%d')}_invoices.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        print(f"✅ Action logged to: {log_file}")
    
    def process_email(self, email_file: Path) -> Dict[str, Any]:
        """
        Process a single email and create invoice.
        
        Args:
            email_file: Path to email file
            
        Returns:
            Processing result
        """
        print("=" * 60)
        print("EMAIL TO INVOICE AUTOMATION")
        print("=" * 60)
        print()
        
        # Read email
        content = email_file.read_text(encoding='utf-8')
        
        # Extract customer info
        print("Step 1: Extracting customer information...")
        customer = self.extract_customer_info(content)
        print(f"  Name: {customer['name']}")
        print(f"  Email: {customer['email']}")
        
        # Detect and convert currency
        print("\nStep 1b: Detecting currency...")
        detected_currency = self.detect_currency(content)
        customer['original_currency'] = detected_currency
        customer['original_amount'] = customer['amount']
        
        # Convert to USD
        if detected_currency != 'USD':
            print("\nStep 1c: Converting to USD...")
            customer['amount'] = self.convert_to_usd(customer['amount'], detected_currency)
        
        print(f"  Service: {customer['service']}")
        print(f"  Original Amount: {customer['original_amount']:.2f} {detected_currency}")
        print(f"  USD Amount: ${customer['amount']:.2f}")
        print()
        
        # Create customer and invoice
        print("Step 2: Creating customer and invoice in Odoo...")
        invoice_result = self.create_customer_and_invoice(customer)
        print()
        
        # Send invoice email
        if invoice_result.get('invoice_created'):
            print("Step 3: Sending invoice email...")
            email_result = self.send_invoice_email(customer, invoice_result)
            if email_result.get('success'):
                print("✅ Invoice email sent")
            else:
                print(f"⚠️  Email send failed: {email_result.get('error')}")
            print()
        else:
            email_result = {'success': False, 'error': 'Invoice not created'}
            print("⚠️  Skipping email (invoice not created)")
            print()
        
        # Log action
        print("Step 4: Logging action...")
        self.log_action(customer, invoice_result, email_result)
        print()
        
        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Customer: {customer['name']} ({customer['email']})")
        print(f"Service: {customer['service'].title()}")
        if customer.get('original_currency') != 'USD':
            print(f"Original Amount: {customer.get('original_amount', 0):.2f} {customer.get('original_currency', 'USD')}")
            print(f"Converted Amount: ${customer['amount']:.2f} USD")
        else:
            print(f"Amount: ${customer['amount']:.2f} USD")
        print(f"Invoice: {invoice_result.get('invoice_number', 'N/A')}")
        print(f"Email Sent: {email_result.get('success', False)}")
        print("=" * 60)
        
        return {
            'success': invoice_result.get('invoice_created', False),
            'customer': customer,
            'invoice': invoice_result,
            'email': email_result
        }


def main():
    """Process email to invoice."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email to Invoice Automation')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--email-file', help='Path to email file to process')
    
    args = parser.parse_args()
    
    # Initialize automation
    automation = EmailToInvoiceAutomation(args.vault)
    
    if args.email_file:
        # Process specific email
        email_path = Path(args.email_file)
        if email_path.exists():
            automation.process_email(email_path)
        else:
            print(f"❌ Email file not found: {email_path}")
    else:
        # Process all emails in Needs_Action
        vault = Path(args.vault)
        needs_action = vault / 'Needs_Action'
        
        if needs_action.exists():
            email_files = list(needs_action.glob('EMAIL_*.md'))
            if email_files:
                print(f"Found {len(email_files)} email(s) to process")
                for email_file in email_files:
                    automation.process_email(email_file)
                    print()
            else:
                print("No emails found in Needs_Action folder")
        else:
            print("Needs_Action folder not found")


if __name__ == '__main__':
    main()
