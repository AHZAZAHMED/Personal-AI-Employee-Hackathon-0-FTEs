"""
Test Facebook Posting

Tests creating posts on your Facebook Page.

Usage:
    python scripts\test_facebook_post.py
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("FACEBOOK POSTING TEST")
print("=" * 60)
print()

try:
    from facebook_watcher import FacebookClient
    
    # Initialize Facebook client
    print("Step 1: Connecting to Facebook...")
    fb = FacebookClient()
    print("✅ Connected!")
    print()
    
    # Get page info
    print("Step 2: Getting Page information...")
    page_info = fb.get_page_info()
    print(f"✅ Page: {page_info.get('name')}")
    print()
    
    # Test 1: Create simple text post
    print("Step 3: Creating test post (text only)...")
    print()
    
    test_message = f"""🤖 AI Employee Test Post

This is a test post from the AI Employee Facebook integration!

Timestamp: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#AIEmployee #Automation #GoldTier #Hackathon2026
"""
    
    result = fb.create_post(message=test_message)
    
    if result.get('success'):
        print("✅ POST CREATED SUCCESSFULLY!")
        print()
        print(f"Post ID: {result.get('post_id')}")
        print(f"Message: {result.get('message')[:100]}...")
        print()
        print("View your post:")
        print(f"https://www.facebook.com/{result.get('post_id')}")
    else:
        print("❌ POST FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print("=" * 60)
    print("❌ TEST FAILED")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    print("Possible issues:")
    print("  1. Missing publish_pages permission")
    print("  2. Token expired")
    print("  3. Not admin of the Page")
    print()
    print("To fix:")
    print("  1. Go to Graph API Explorer")
    print("  2. Get new token with 'publish_pages' permission")
    print("  3. Update .env file")
    print("  4. Run test again")
