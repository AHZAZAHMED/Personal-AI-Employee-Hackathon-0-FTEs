"""
Test Instagram Credentials and Connection

Verifies that your Instagram Business Account is properly linked.

Usage:
    python scripts\test_instagram_credentials.py
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("INSTAGRAM CREDENTIALS TEST")
print("=" * 60)
print()

# First check if Instagram Business Account ID is in .env
import os
from pathlib import Path
from dotenv import load_dotenv

env_file = Path(__file__).parent.parent / '.env'
load_dotenv(env_file)

instagram_id = os.getenv('INSTAGRAM_BUSSINESS_ACCOUNT_ID')
page_token = os.getenv('FACEBOOK_PAGE_TOKEN')

print("Step 1: Checking Instagram credentials...")
print()

if instagram_id:
    print(f"✅ INSTAGRAM_BUSSINESS_ACCOUNT_ID: {instagram_id[:20]}...")
else:
    print("❌ INSTAGRAM_BUSSINESS_ACCOUNT_ID not found in .env")
    print()
    print("Please add your Instagram Business Account ID to .env file")
    print("See INSTAGRAM-SETUP-GUIDE.md")
    sys.exit(1)

if page_token:
    print(f"✅ FACEBOOK_PAGE_TOKEN: {page_token[:20]}...")
else:
    print("❌ FACEBOOK_PAGE_TOKEN not found in .env")
    sys.exit(1)

print()
print("Step 2: Testing Instagram Graph API connection...")
print()

try:
    # Test direct API call
    import requests
    
    url = f'https://graph.facebook.com/v18.0/{instagram_id}'
    params = {
        'fields': 'username,biography,website,followers_count,follows_count,media_count',
        'access_token': page_token
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    account_info = response.json()
    
    print("=" * 60)
    print("✅ INSTAGRAM CONNECTED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Instagram Business Account:")
    print(f"  Username: @{account_info.get('username', 'N/A')}")
    print(f"  Followers: {account_info.get('followers_count', 0)}")
    print(f"  Following: {account_info.get('follows_count', 0)}")
    print(f"  Posts: {account_info.get('media_count', 0)}")
    print(f"  Bio: {account_info.get('biography', 'N/A')[:100]}")
    print(f"  Website: {account_info.get('website', 'N/A')}")
    print()
    print("Next steps:")
    print("  1. Instagram Watcher is ready to use")
    print("  2. Run: python scripts\\instagram_watcher.py --vault AI_Employee_Vault")
    print("  3. Test posting: python scripts\\test_instagram_post.py")
    print()

except Exception as e:
    print("=" * 60)
    print("⚠️  INSTAGRAM CONNECTION FAILED")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    print("Possible issues:")
    print("  1. Instagram Business Account ID is incorrect")
    print("  2. Facebook Page Token expired")
    print("  3. Instagram not linked to Facebook Page")
    print()
    print("To fix:")
    print("  1. Check INSTAGRAM_BUSSINESS_ACCOUNT_ID in .env file")
    print("  2. Regenerate Facebook Page Token from Graph API Explorer")
    print("  3. Make sure Instagram is linked to Facebook Page")
    print("  4. See INSTAGRAM-SETUP-GUIDE.md for detailed instructions")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
