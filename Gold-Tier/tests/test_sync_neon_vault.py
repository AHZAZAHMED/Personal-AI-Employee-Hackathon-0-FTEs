"""Test Sync Neon to Vault Skill"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'skills' / 'sync_neon_vault'))

from service import NeonVaultSyncService

print("Testing Sync Neon to Vault Service...")
print("=" * 60)

# Initialize service
service = NeonVaultSyncService(vault_path="AI_Employee_Vault")

# Test 1: Test database connection
print("\n[TEST 1] Testing database connection...")
result = service.test_connection()
print(f"Result: {result}")

if not result.get("success"):
    print("\n[ERROR] Database connection failed!")
    print("Make sure PostgreSQL is running and credentials are correct in .env")
    sys.exit(1)

# Test 2: Get current status
print("\n[TEST 2] Getting sync status...")
result = service.get_status()
print(f"Result: {result}")
if result.get("success"):
    print(f"  Vault Inbox Count: {result.get('vault_inbox_count', 0)}")
    print(f"  Database Unread Count: {result.get('database_unread_count', 0)}")

# Test 3: Run sync
print("\n[TEST 3] Running sync (limit 10)...")
result = service.run_sync(limit=10)
print(f"Result:")
print(f"  Retrieved: {result.get('retrieved', 0)}")
print(f"  Synced: {result.get('synced', 0)}")
print(f"  Failed: {result.get('failed', 0)}")
print(f"  Skipped: {result.get('skipped', 0)}")

if result.get('synced_files'):
    print(f"\n  Synced files:")
    for f in result['synced_files'][:3]:  # Show first 3
        print(f"    - {Path(f).name}")

print("\n" + "=" * 60)
print("Sync Neon to Vault test completed!")
