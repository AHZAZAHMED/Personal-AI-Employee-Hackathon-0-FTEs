"""
Test Instagram Posting

Tests posting an image to your Instagram Business Account.

Usage:
    python scripts\test_instagram_post.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("INSTAGRAM POSTING TEST")
print("=" * 60)
print()

try:
    from instagram_watcher import InstagramClient
    
    # Initialize Instagram client
    print("Step 1: Connecting to Instagram...")
    instagram = InstagramClient()
    
    # Get account info
    account_info = instagram.get_account_info()
    
    if 'error' in account_info:
        print("❌ Instagram Business Account not linked!")
        print()
        print("Please follow INSTAGRAM-SETUP-GUIDE.md to link your account")
        sys.exit(1)
    
    print(f"✅ Connected to @{account_info.get('username')}")
    print()
    
    # Test post
    print("Step 2: Creating test post...")
    print()
    
    # Use a placeholder image (AI-generated tech image)
    test_image_url = "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1080"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_caption = f"""🤖 AI Employee Test Post

This is a test post from the AI Employee Instagram integration!

Timestamp: {timestamp}

Posted automatically via Instagram Graph API.

#AIEmployee #Automation #GoldTier #Hackathon2026 #InstagramAPI #SocialMediaAutomation
"""
    
    print(f"Image URL: {test_image_url}")
    print(f"Caption: {test_caption[:100]}...")
    print()
    print("Posting to Instagram...")
    print("(This may take 10-20 seconds)")
    print()
    
    # Post image
    result = instagram.post_image(
        image_url=test_image_url,
        caption=test_caption
    )
    
    if result.get('success'):
        print("✅ IMAGE POSTED SUCCESSFULLY!")
        print()
        print(f"Post ID: {result.get('post_id')}")
        print(f"Caption: {test_caption[:100]}...")
        print()
        print("View your post:")
        username = account_info.get('username')
        print(f"https://www.instagram.com/{username}/")
        print()
        print("Note: It may take a few minutes for the post to appear on your profile.")
    else:
        print("❌ POST FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print()
        print("Common issues:")
        print("  1. Image URL must be publicly accessible (not localhost)")
        print("  2. Image must be in JPG or PNG format")
        print("  3. Instagram Business Account must be properly linked")
        print("  4. Facebook Page token must have instagram_content_publish permission")
    
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
    print("  1. Instagram Business Account not linked")
    print("  2. Missing Facebook credentials")
    print("  3. Insufficient permissions")
    print()
    print("To fix:")
    print("  1. Run: python scripts\\test_instagram_credentials.py")
    print("  2. Follow INSTAGRAM-SETUP-GUIDE.md")
    print("  3. Ensure Instagram is linked to Facebook Page")
