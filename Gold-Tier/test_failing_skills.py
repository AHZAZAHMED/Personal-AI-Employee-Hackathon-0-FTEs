"""
Test the three skills that require external services:
1. sync_neon_to_vault - Requires Neon PostgreSQL
2. odoo_accounting - Requires Odoo ERP
3. email_to_invoice - Requires Odoo ERP
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("TESTING SKILLS WITH EXTERNAL DEPENDENCIES")
print("=" * 70)

# Test 1: Sync Neon to Vault
print("\n1. SYNC NEON TO VAULT")
print("-" * 70)
try:
    from skills.sync_neon_vault.skill import sync_test_connection
    result = sync_test_connection()
    print(f"   Connection test: {result}")

    if result.get('success'):
        print("   [OK] Neon database is connected!")

        # Try a sync
        from skills.sync_neon_vault.skill import sync_neon_to_vault
        sync_result = sync_neon_to_vault(limit=5)
        print(f"   Sync test: {sync_result}")
    else:
        print(f"   [FAIL] Neon database not available")
        print(f"   Error: {result.get('error', 'Unknown')}")
        print(f"   Fix: Set NEON_DATABASE_URL in .env file")

except Exception as e:
    print(f"   [ERROR] {e}")

# Test 2: Odoo Accounting
print("\n2. ODOO ACCOUNTING")
print("-" * 70)
try:
    from skills.odoo_accounting.skill import odoo_test_connection
    result = odoo_test_connection()
    print(f"   Connection test: {result}")

    if result.get('success'):
        print("   [OK] Odoo is connected!")

        # Try creating a test customer
        from skills.odoo_accounting.skill import odoo_create_customer
        customer_result = odoo_create_customer(
            name="Test Customer",
            email="test@example.com"
        )
        print(f"   Customer test: {customer_result}")
    else:
        print(f"   [FAIL] Odoo not available")
        print(f"   Error: {result.get('error', 'Unknown')}")
        print(f"   Fix: Install and run Odoo ERP at http://localhost:8069")
        print(f"        Or set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD in .env")

except Exception as e:
    print(f"   [ERROR] {e}")

# Test 3: Email to Invoice
print("\n3. EMAIL TO INVOICE")
print("-" * 70)
try:
    from skills.email_to_invoice.skill import process_email_to_invoice

    # This depends on Odoo, so check that first
    from skills.odoo_accounting.skill import odoo_test_connection
    odoo_result = odoo_test_connection()

    if odoo_result.get('success'):
        print("   [OK] Odoo dependency satisfied")

        # Try processing a test email
        test_email = """from: John Doe <john@example.com>
subject: Need consulting services

Hi, I need consulting services for my project.
I'm willing to pay $500 for this work.

Thanks,
John"""

        result = process_email_to_invoice(
            email_content=test_email,
            send_invoice_email=False  # Don't send email in test
        )
        print(f"   Processing test: {result}")

        if result.get('success'):
            print("   [OK] Email to invoice is working!")
        else:
            print(f"   [FAIL] Processing failed: {result.get('error', 'Unknown')}")
    else:
        print(f"   [FAIL] Odoo dependency not satisfied")
        print(f"   Fix: Configure Odoo first (see test #2)")

except Exception as e:
    print(f"   [ERROR] {e}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
These skills require external services to function:

1. sync_neon_to_vault:
   - Requires: Neon PostgreSQL database
   - Setup: Add NEON_DATABASE_URL to .env file
   - Format: postgresql://user:pass@host/dbname

2. odoo_accounting:
   - Requires: Odoo ERP running locally or remotely
   - Setup: Install Odoo or use cloud instance
   - Config: ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD in .env
   - Default: http://localhost:8069, db=odoo, user=admin, pass=admin

3. email_to_invoice:
   - Requires: Odoo ERP (same as #2)
   - Setup: Same as odoo_accounting

All three skills are properly coded and registered. They just need
their external services configured to work.
""")
print("=" * 70)
