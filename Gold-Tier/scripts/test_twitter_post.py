"""
Test Twitter Posting

Tests creating tweets on your Twitter account.

Usage:
    python scripts\test_twitter_post.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("TWITTER POSTING TEST")
print("=" * 60)
print()

try:
    from twitter_watcher import TwitterClient
    
    # Initialize Twitter client
    print("Step 1: Connecting to Twitter...")
    twitter = TwitterClient()
    print("✅ Connected!")
    print()
    
    # Get user info
    print("Step 2: Getting user information...")
    user_info = twitter.get_me()
    print(f"✅ @{user_info.get('username')}")
    print()
    
    # Test 1: Create simple tweet
    print("Step 3: Creating test tweet...")
    print()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_tweet = f"""🤖 AI Employee Test Tweet

This is a test post from the AI Employee Twitter integration!

Timestamp: {timestamp}

#AIEmployee #Automation #GoldTier #Hackathon2026 #TwitterAPI
"""
    
    result = twitter.create_tweet(text=test_tweet)
    
    if result.get('success'):
        print("✅ TWEET POSTED SUCCESSFULLY!")
        print()
        print(f"Tweet ID: {result.get('tweet_id')}")
        print(f"Text: {result.get('text')[:100]}...")
        print()
        print("View your tweet:")
        username = user_info.get('username')
        print(f"https://twitter.com/{username}/status/{result.get('tweet_id')}")
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
    print("  1. Missing write permissions")
    print("  2. Token expired")
    print("  3. Rate limit exceeded")
    print()
    print("To fix:")
    print("  1. Go to Twitter Developer Portal")
    print("  2. Check app permissions are 'Read and Write'")
    print("  3. Regenerate tokens if needed")
    print("  4. Update .env file")
    print("  5. Run test again")
