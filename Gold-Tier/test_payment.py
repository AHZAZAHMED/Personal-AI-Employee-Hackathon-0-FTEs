"""Test payment with invoice ID"""
import sys
sys.path.insert(0, 'scripts')
from odoo_mcp_server import OdooAccountingMCP
import json

mcp = OdooAccountingMCP({
    'url': 'http://localhost:8069',
    'db': 'odoo',
    'username': 'admin123@example.com',
    'password': 'admin'
})

print('Testing payment recording with invoice ID (2)...')
result = mcp.record_payment(
    invoice_number='2',
    amount=600.0,
    payment_reference='Bank Transfer Payment'
)

print(json.dumps(result, indent=2))
