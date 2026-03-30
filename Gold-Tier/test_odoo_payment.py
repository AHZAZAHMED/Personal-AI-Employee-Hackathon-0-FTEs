"""
Test Odoo Payment Recording
"""

import sys
sys.path.insert(0, 'scripts')

from odoo_mcp_server import OdooAccountingMCP
import json

print("=" * 60)
print("ODOO PAYMENT RECORDING TEST")
print("=" * 60)
print()

# Initialize MCP server
print("Step 1: Initializing MCP server...")
mcp = OdooAccountingMCP({
    'url': 'http://localhost:8069',
    'db': 'odoo',
    'username': 'admin123@example.com',
    'password': 'admin'
})
print("✅ MCP server initialized")
print()

# Test authentication
print("Step 2: Testing authentication...")
if mcp.client.authenticate():
    print(f"✅ Authentication successful! User ID: {mcp.client.uid}")
else:
    print("❌ Authentication failed!")
    sys.exit(1)
print()

# Record payment for the invoice we created
print("Step 3: Recording payment for invoice INV/2026/00002...")
print("   Invoice: INV/2026/00002")
print("   Amount: $600.00")
print("   Reference: Bank Transfer Payment")
print()

result = mcp.record_payment(
    invoice_number='INV/2026/00002',
    amount=600.0,
    payment_reference='Bank Transfer Payment'
)

print("Step 4: Result:")
print(json.dumps(result, indent=2))
print()

if result.get('success'):
    print("=" * 60)
    print("✅ PAYMENT RECORDED SUCCESSFULLY!")
    print("=" * 60)
    print(f"   Payment ID: {result.get('payment_id')}")
    print(f"   Invoice: {result.get('invoice_number')}")
    print(f"   Amount: ${result.get('amount')}")
    print(f"   Message: {result.get('message')}")
    print("=" * 60)
    print()
    print("You can view this payment in Odoo:")
    print("1. Go to http://localhost:8069")
    print("2. Login with admin123@example.com / admin")
    print("3. Go to Invoicing → Customers → Payments")
    print(f"4. Look for payment of $600.00")
    print()
    print("The invoice status should now show as 'Paid'")
else:
    print("=" * 60)
    print("❌ PAYMENT RECORDING FAILED")
    print("=" * 60)
    print(f"Error: {result.get('error')}")
    print()
    print("Possible issues:")
    print("1. Invoice not found")
    print("2. Payment journal not configured")
    print("3. Insufficient permissions")
