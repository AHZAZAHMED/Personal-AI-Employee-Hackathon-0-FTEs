"""
Test Instagram API Connection
Diagnoses Instagram Business Account linking issues.
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent / ".env"
load_dotenv(env_file)

GRAPH_API_URL = "https://graph.facebook.com/v18.0"

def test_instagram_connection():
    """Test Instagram API connection and diagnose issues."""

    page_id = os.getenv("FACEBOOK_PAGE_ID")
    page_token = os.getenv("FACEBOOK_PAGE_TOKEN")
    ig_business_id = os.getenv("INSTAGRAM_BUSSINESS_ACCOUNT_ID")

    print("=" * 60)
    print("Instagram Connection Diagnostic")
    print("=" * 60)

    # Check credentials
    print("\n1. Checking credentials...")
    if not page_id:
        print("   [ERROR] FACEBOOK_PAGE_ID not found in .env")
        return
    if not page_token:
        print("   [ERROR] FACEBOOK_PAGE_TOKEN not found in .env")
        return

    print(f"   [OK] FACEBOOK_PAGE_ID: {page_id}")
    print(f"   [OK] FACEBOOK_PAGE_TOKEN: {page_token[:20]}...")
    if ig_business_id:
        print(f"   [OK] INSTAGRAM_BUSSINESS_ACCOUNT_ID: {ig_business_id}")

    # Test 1: Get Facebook Page info
    print("\n2. Testing Facebook Page access...")
    try:
        resp = requests.get(
            f"{GRAPH_API_URL}/{page_id}",
            params={"fields": "name,id", "access_token": page_token},
            timeout=30
        )
        resp.raise_for_status()
        page_data = resp.json()
        print(f"   [OK] Page Name: {page_data.get('name')}")
        print(f"   [OK] Page ID: {page_data.get('id')}")
    except requests.exceptions.HTTPError as e:
        print(f"   [ERROR] HTTP {e.response.status_code}: {e.response.text}")
        return
    except Exception as e:
        print(f"   [ERROR] {e}")
        return

    # Test 2: Get Instagram Business Account
    print("\n3. Checking Instagram Business Account link...")
    try:
        resp = requests.get(
            f"{GRAPH_API_URL}/{page_id}",
            params={"fields": "instagram_business_account", "access_token": page_token},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        if "instagram_business_account" in data:
            ig_id = data["instagram_business_account"]["id"]
            print(f"   [OK] Instagram Business Account ID: {ig_id}")

            # Test 3: Get Instagram account info
            print("\n4. Testing Instagram account access...")
            resp2 = requests.get(
                f"{GRAPH_API_URL}/{ig_id}",
                params={"fields": "username,biography,followers_count", "access_token": page_token},
                timeout=30
            )
            resp2.raise_for_status()
            ig_data = resp2.json()
            print(f"   [OK] Username: @{ig_data.get('username')}")
            print(f"   [OK] Followers: {ig_data.get('followers_count')}")

            print("\n" + "=" * 60)
            print("SUCCESS: Instagram integration is working!")
            print("=" * 60)

        else:
            print("   [ERROR] No Instagram Business Account linked to this Facebook Page")
            print("\n   To fix this:")
            print("   1. Go to https://business.facebook.com/")
            print("   2. Select your Facebook Page")
            print("   3. Go to Settings > Instagram")
            print("   4. Connect your Instagram Business Account")
            print("   5. Make sure it's a Business or Creator account, not Personal")

    except requests.exceptions.HTTPError as e:
        print(f"   [ERROR] HTTP {e.response.status_code}: {e.response.text}")
        print("\n   Possible causes:")
        print("   - Access token expired or invalid")
        print("   - Missing permissions (instagram_basic, instagram_manage_comments)")
        print("   - Page token doesn't have Instagram permissions")
    except Exception as e:
        print(f"   [ERROR] {e}")

if __name__ == "__main__":
    test_instagram_connection()
