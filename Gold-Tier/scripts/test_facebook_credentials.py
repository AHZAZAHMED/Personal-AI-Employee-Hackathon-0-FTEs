"""
Test Facebook Credentials

Verifies that your Facebook API credentials are valid and working.

Usage:
    python scripts\test_facebook_credentials.py
"""

import os
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("FACEBOOK CREDENTIALS TEST")
print("=" * 60)
print()

# Check if credentials file exists
env_file = Path(__file__).parent.parent / '.facebook_credentials.env'
env_file_alt = Path(__file__).parent.parent / '.env'

# Try alternative filename
if not env_file.exists() and env_file_alt.exists():
    env_file = env_file_alt

if not env_file.exists():
    print("❌ Credentials file not found!")
    print()
    print("Steps to fix:")
    print("1. Copy .facebook_credentials.env.template to .facebook_credentials.env")
    print("2. Fill in your Facebook credentials")
    print("3. Run this test again")
    print()
    print("Template location:")
    print(f"  {Path(__file__).parent.parent / '.facebook_credentials.env.template'}")
    sys.exit(1)

# Load credentials
from dotenv import load_dotenv
load_dotenv(env_file)

print("Step 1: Checking credentials file...")
print(f"✅ Found: {env_file}")
print()

# Check each credential
print("Step 2: Validating credentials...")
print()

credentials = {
    'FACEBOOK_APP_ID': os.getenv('FACEBOOK_APP_ID'),
    'FACEBOOK_APP_SECRET': os.getenv('FACEBOOK_APP_SECRET'),
    'FACEBOOK_PAGE_ID': os.getenv('FACEBOOK_PAGE_ID'),
    'FACEBOOK_USER_TOKEN': os.getenv('FACEBOOK_USER_TOKEN'),
    'FACEBOOK_PAGE_TOKEN': os.getenv('FACEBOOK_PAGE_TOKEN')
}

all_valid = True

for name, value in credentials.items():
    if value and value != 'your_app_id_here' and len(value) > 10:
        # Mask sensitive values
        if 'SECRET' in name or 'TOKEN' in name:
            masked = value[:10] + '...' + value[-5:]
        else:
            masked = value
        print(f"✅ {name}: {masked}")
    else:
        print(f"❌ {name}: Missing or invalid")
        all_valid = False

print()

if not all_valid:
    print("=" * 60)
    print("❌ CREDENTIALS INVALID")
    print("=" * 60)
    print()
    print("Please update your .facebook_credentials.env file")
    print("See FACEBOOK-SETUP-GUIDE.md for setup instructions")
    sys.exit(1)

# Test Facebook API connection
print("Step 3: Testing Facebook API connection...")
print()

try:
    from facebook_watcher import FacebookClient
    
    fb = FacebookClient()
    
    # Get page info
    print("Fetching Page information...")
    page_info = fb.get_page_info()
    
    print()
    print("=" * 60)
    print("✅ CREDENTIALS VALID!")
    print("=" * 60)
    print()
    print("Connected to Facebook Page:")
    print(f"  Name: {page_info.get('name')}")
    print(f"  ID: {page_info.get('id')}")
    print(f"  Username: @{page_info.get('username', 'N/A')}")
    print(f"  Followers: {page_info.get('followers_count', 'N/A')}")
    print()
    print("Next steps:")
    print("  1. Facebook Watcher is ready to use")
    print("  2. Run: python scripts\\facebook_watcher.py --vault AI_Employee_Vault")
    print()
    
except Exception as e:
    print("=" * 60)
    print("⚠️  API CONNECTION FAILED")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    print("Possible issues:")
    print("  1. Tokens expired - regenerate from Graph API Explorer")
    print("  2. App not in development mode - enable in App Dashboard")
    print("  3. Missing permissions - check token permissions")
    print()
    print("Credentials are saved, but API connection failed.")
    print("You can still proceed, but Facebook features won't work until API is connected.")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
