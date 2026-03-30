"""
Set Odoo Currency to USD
"""

import sys
sys.path.insert(0, 'scripts')

from odoo_mcp_server import OdooAccountingMCP

# Initialize Odoo
mcp = OdooAccountingMCP({
    'url': 'http://localhost:8069',
    'db': 'odoo',
    'username': 'admin123@example.com',
    'password': 'admin'
})

print("=" * 60)
print("ODOO CURRENCY CONFIGURATION")
print("=" * 60)
print()

# Check if USD currency exists
print("Step 1: Checking for USD currency...")
currencies = mcp.client.execute_kw(
    'res.currency',
    'search_read',
    [[['name', 'in', ['USD', 'PKR']]]],
    {'fields': ['name', 'symbol', 'position']}
)

print(f"Found {len(currencies)} currencies:")
for curr in currencies:
    print(f"  - {curr['name']} ({curr['symbol']}) - Position: {curr['position']}")

# Activate USD if not active
usd_exists = any(c['name'] == 'USD' for c in currencies)
if not usd_exists:
    print("\nStep 2: Activating USD currency...")
    try:
        mcp.client.execute_kw(
            'res.currency',
            'create',
            [{
                'name': 'USD',
                'symbol': '$',
                'position': 'before',
                'active': True
            }]
        )
        print("✅ USD currency activated")
    except Exception as e:
        print(f"⚠️  Could not activate USD: {e}")

# Get company info
print("\nStep 3: Getting company information...")
companies = mcp.client.execute_kw(
    'res.company',
    'search_read',
    [],
    {'fields': ['name', 'currency_id']}
)

if companies:
    company = companies[0]
    print(f"Company: {company['name']}")
    print(f"Current Currency ID: {company['currency_id'][0]} ({company['currency_id'][1]})")
    
    # Change to USD
    print("\nStep 4: Changing company currency to USD...")
    try:
        # Find USD currency ID
        usd_curr = mcp.client.execute_kw(
            'res.currency',
            'search_read',
            [[['name', '=', 'USD']]],
            {'fields': ['id']}
        )
        
        if usd_curr:
            usd_id = usd_curr[0]['id']
            mcp.client.execute_kw(
                'res.company',
                'write',
                [company['id'], {'currency_id': usd_id}]
            )
            print("✅ Company currency changed to USD")
        else:
            print("⚠️  USD currency not found")
    except Exception as e:
        print(f"⚠️  Could not change currency: {e}")

print("\n" + "=" * 60)
print("CURRENCY CONFIGURATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Go to http://localhost:8069")
print("2. Create a new invoice")
print("3. Verify currency shows as $ (USD) instead of Rs. (PKR)")
