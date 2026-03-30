"""
Test Odoo Financial Reports
"""

import sys
sys.path.insert(0, 'scripts')

from odoo_mcp_server import OdooAccountingMCP
import json

print("=" * 60)
print("ODOO FINANCIAL REPORTS TEST")
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

# Test 1: Profit & Loss Report
print("=" * 60)
print("TEST 1: PROFIT & LOSS REPORT")
print("=" * 60)
print()

print("Generating Profit & Loss report...")
result = mcp.generate_financial_report(report_type='profit_loss')

print()
print("Result:")
print(json.dumps(result, indent=2))
print()

if result.get('success'):
    print("=" * 60)
    print("✅ PROFIT & LOSS REPORT GENERATED!")
    print("=" * 60)
    print(f"   Report Type: {result.get('report_type')}")
    print(f"   Income: ${result.get('income')}")
    print(f"   Expenses: ${result.get('expenses')}")
    print(f"   Net Profit: ${result.get('net_profit')}")
    print(f"   Income Accounts: {result.get('income_accounts')}")
    print(f"   Expense Accounts: {result.get('expense_accounts')}")
    print("=" * 60)
else:
    print("=" * 60)
    print("❌ PROFIT & LOSS REPORT FAILED")
    print("=" * 60)
    print(f"Error: {result.get('error')}")

print()
print()

# Test 2: Balance Sheet Report
print("=" * 60)
print("TEST 2: BALANCE SHEET REPORT")
print("=" * 60)
print()

print("Generating Balance Sheet report...")
result = mcp.generate_financial_report(report_type='balance_sheet')

print()
print("Result:")
print(json.dumps(result, indent=2))
print()

if result.get('success'):
    print("=" * 60)
    print("✅ BALANCE SHEET REPORT GENERATED!")
    print("=" * 60)
    print(f"   Report Type: {result.get('report_type')}")
    print(f"   Assets: ${result.get('assets')}")
    print(f"   Liabilities: ${result.get('liabilities')}")
    print(f"   Equity: ${result.get('equity')}")
    print(f"   Asset Accounts: {result.get('asset_accounts')}")
    print(f"   Liability Accounts: {result.get('liability_accounts')}")
    print("=" * 60)
else:
    print("=" * 60)
    print("❌ BALANCE SHEET REPORT FAILED")
    print("=" * 60)
    print(f"Error: {result.get('error')}")

print()
print("=" * 60)
print("FINANCIAL REPORTS TEST COMPLETE")
print("=" * 60)
