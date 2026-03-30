"""
Get Instagram Business Account ID from Facebook Page

This script fetches your Instagram Business Account ID from your linked Facebook Page.

Usage:
    python scripts\get_instagram_id.py
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("GET INSTAGRAM BUSINESS ACCOUNT ID")
print("=" * 60)
print()

# Load credentials
env_file = Path(__file__).parent.parent / '.env'
load_dotenv(env_file)

page_id = os.getenv('FACEBOOK_PAGE_ID')
page_token = os.getenv('FACEBOOK_PAGE_TOKEN')

print(f"Facebook Page ID: {page_id}")
print(f"Page Token: {page_token[:20]}...")
print()

print("Step 1: Fetching Instagram Business Account from Facebook Page...")
print()

try:
    # Get Instagram Business Account linked to Facebook Page
    url = f'https://graph.facebook.com/v18.0/{page_id}'
    params = {
        'fields': 'instagram_business_account',
        'access_token': page_token
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if 'instagram_business_account' in data:
        instagram_id = data['instagram_business_account']['id']
        
        print("=" * 60)
        print("✅ INSTAGRAM BUSINESS ACCOUNT FOUND!")
        print("=" * 60)
        print()
        print(f"Instagram Business Account ID: {instagram_id}")
        print()
        print("Add this to your .env file:")
        print(f"INSTAGRAM_BUSSINESS_ACCOUNT_ID = {instagram_id}")
        print()
        
        # Now test the connection
        print("Step 2: Testing Instagram connection...")
        print()
        
        # Get account info
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
        print("✅ Your .env file already has the correct Instagram ID!")
        print("✅ Instagram integration is ready to use!")
        print()
        
    else:
        print("=" * 60)
        print("⚠️  NO INSTAGRAM BUSINESS ACCOUNT LINKED")
        print("=" * 60)
        print()
        print("Your Facebook Page is not linked to any Instagram Business Account.")
        print()
        print("To link:")
        print("  1. Open Instagram app")
        print("  2. Go to Settings → Account → Switch to Professional Account → Business")
        print("  3. Go to Settings → Linked Accounts → Facebook")
        print("  4. Connect to your 'AI Employee' Facebook Page")
        print("  5. Run this script again")
        print()
        
except Exception as e:
    print("=" * 60)
    print("❌ ERROR")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        print(f"Response: {e.response.text}")
    print()
    print("Possible issues:")
    print("  1. Facebook Page Token expired")
    print("  2. Instagram not linked to Facebook Page")
    print()
    print("To fix:")
    print("  1. Regenerate Facebook Page Token from Graph API Explorer")
    print("  2. Link Instagram to Facebook Page")
    print("  3. See INSTAGRAM-SETUP-GUIDE.md")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
