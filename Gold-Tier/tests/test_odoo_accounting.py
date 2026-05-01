"""Test Odoo Accounting Service"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'skills' / 'odoo_accounting'))

from service import OdooAccountingService

print("Testing Odoo Accounting Service...")
print("=" * 60)

# Initialize service (will use credentials from .env)
service = OdooAccountingService()

# Test 1: Create Customer
print("\n[TEST 1] Creating customer...")
result = service.create_customer(
    name="Test Customer",
    email="testcustomer@example.com",
    phone="+1234567890",
    company="Test Company Inc"
)
print(f"Result: {result}")

# Test 2: Create Invoice
print("\n[TEST 2] Creating invoice...")
result = service.create_invoice(
    partner_name="Test Customer",
    partner_email="testcustomer@example.com",
    lines=[
        {"name": "Web Development Service", "quantity": 10, "price_unit": 100.0},
        {"name": "Consulting Hours", "quantity": 5, "price_unit": 150.0}
    ]
)
print(f"Result: {result}")
invoice_number = result.get("invoice_number", "")

# Test 3: Record Payment (if invoice was created)
if result.get("success") and invoice_number:
    print("\n[TEST 3] Recording payment...")
    result = service.record_payment(
        invoice_number=invoice_number,
        amount=500.0,
        payment_reference="Test Payment"
    )
    print(f"Result: {result}")

# Test 4: Get Account Balances
print("\n[TEST 4] Getting account balances...")
result = service.get_account_balance()
print(f"Found {result.get('count', 0)} accounts")
if result.get("success") and result.get("accounts"):
    for acc in result["accounts"][:5]:  # Show first 5
        print(f"  {acc['code']} - {acc['name']}: {acc['balance']}")

# Test 5: List Transactions
print("\n[TEST 5] Listing recent transactions...")
result = service.list_transactions(days=30, limit=10)
print(f"Found {result.get('count', 0)} transactions in last 30 days")
if result.get("success") and result.get("transactions"):
    for txn in result["transactions"][:3]:  # Show first 3
        print(f"  {txn['date']} - {txn['name']}: {txn['amount']}")

# Test 6: Generate Financial Report
print("\n[TEST 6] Generating profit/loss report...")
result = service.generate_financial_report(report_type="profit_loss")
print(f"Result: {result}")

print("\n" + "=" * 60)
print("Odoo Accounting Service tests completed!")
