"""Test Odoo connection"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'skills' / 'odoo_accounting'))

from service import OdooClient

print("Testing Odoo connection...")
print("=" * 60)

# Try credentials from .env
client = OdooClient(
    url="http://localhost:8069",
    db="odoo",
    username="admin123@example.com",
    password="admin"
)

print(f"URL: {client.url}")
print(f"Database: {client.db}")
print(f"Username: {client.username}")
print()

print("Attempting authentication...")
if client.authenticate():
    print("[OK] Authentication successful!")
    print(f"  User ID: {client.uid}")
else:
    print("[FAIL] Authentication failed")
    print("  Check Odoo credentials")
