"""
Test Odoo Invoice Creation
"""

import sys
sys.path.insert(0, 'scripts')

from odoo_mcp_server import OdooAccountingMCP
import json

print("=" * 60)
print("ODOO INVOICE CREATION TEST")
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

# Create test invoice
print("Step 3: Creating test invoice...")
print("   Customer: Test Customer")
print("   Email: customer@example.com")
print("   Lines:")
print("     - Consulting Service: 5 hours × $100 = $500")
print("     - Support Service: 2 hours × $50 = $100")
print()

result = mcp.create_invoice(
    partner_name='Test Customer',
    partner_email='customer@example.com',
    lines=[
        {'name': 'Consulting Service', 'quantity': 5, 'price_unit': 100},
        {'name': 'Support Service', 'quantity': 2, 'price_unit': 50}
    ]
)

print("Step 4: Result:")
print(json.dumps(result, indent=2))
print()

if result.get('success'):
    print("=" * 60)
    print("✅ INVOICE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"   Invoice Number: {result.get('invoice_number')}")
    print(f"   Invoice ID: {result.get('invoice_id')}")
    print(f"   Total Amount: ${result.get('amount_total')}")
    print(f"   Amount Due: ${result.get('amount_due')}")
    print(f"   Customer: {result.get('partner_name')}")
    print(f"   Status: {result.get('state')}")
    print("=" * 60)
    print()
    print("You can view this invoice in Odoo:")
    print("1. Go to http://localhost:8069")
    print("2. Login with admin123@example.com / admin")
    print("3. Go to Invoicing → Customers → Invoices")
    print(f"4. Look for invoice {result.get('invoice_number')}")
else:
    print("=" * 60)
    print("❌ INVOICE CREATION FAILED")
    print("=" * 60)
    print(f"Error: {result.get('error')}")
    print()
    print("Possible issues:")
    print("1. Invoicing module not installed")
    print("2. Insufficient permissions")
    print("3. Odoo server error")
