"""Test Email to Invoice Skill"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'skills' / 'email_to_invoice'))

from service import EmailInvoiceService

print("Testing Email to Invoice Skill...")
print("=" * 60)

# Test email content with customer request
email_content = """---
from: john.doe@example.com
subject: Website Development Quote Request
date: 2026-04-22
---

Hi,

I need a website for my business. Can you provide a quote for:
- 5 page website design
- Contact form integration
- Mobile responsive design

My company is Doe Enterprises.

Thanks,
John Doe
Phone: +1-555-0123
"""

print("\nProcessing email to create invoice...")
print("Email from: john.doe@example.com")
print("Subject: Website Development Quote Request")
print()

service = EmailInvoiceService(vault_path="AI_Employee_Vault")
result = service.process_email(
    email_content=email_content,
    send_invoice_email=False  # Don't actually send email in test
)

print("Result:")
print(f"  Success: {result.get('success', False)}")

if result.get('success'):
    customer = result.get('customer', {})
    invoice = result.get('invoice', {})
    email = result.get('email', {})

    print(f"\n  Customer:")
    print(f"    Name: {customer.get('name', 'N/A')}")
    print(f"    Email: {customer.get('email', 'N/A')}")
    print(f"    Service: {customer.get('service', 'N/A')}")
    print(f"    Amount: ${customer.get('amount', 0):.2f}")

    print(f"\n  Invoice:")
    print(f"    Created: {invoice.get('invoice_created', False)}")
    print(f"    Invoice ID: {invoice.get('invoice_id', 'N/A')}")
    print(f"    Invoice Number: {invoice.get('invoice_number', 'N/A')}")
    if invoice.get('errors'):
        print(f"    Errors: {invoice.get('errors')}")

    print(f"\n  Email:")
    print(f"    Sent: {email.get('success', False)}")
    if email.get('error'):
        print(f"    Error: {email.get('error')}")
else:
    print(f"  Error: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 60)
print("Email to Invoice test completed!")
