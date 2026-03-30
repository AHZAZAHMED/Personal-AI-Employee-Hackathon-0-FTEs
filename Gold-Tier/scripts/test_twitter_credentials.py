"""
Test Twitter Credentials

Verifies that your Twitter API credentials are valid and working.

Usage:
    python scripts\test_twitter_credentials.py
"""

import os
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("TWITTER CREDENTIALS TEST")
print("=" * 60)
print()

# Check if credentials exist in .env
env_file = Path(__file__).parent.parent / '.env'

print("Step 1: Checking credentials file...")
if env_file.exists():
    print(f"✅ Found: {env_file}")
else:
    print("❌ .env file not found!")
    print()
    print("Steps to fix:")
    print("1. Copy .twitter_credentials.env.template to .env")
    print("2. Fill in your Twitter credentials")
    print("3. Run this test again")
    sys.exit(1)

print()

# Load credentials
from dotenv import load_dotenv
load_dotenv(env_file)

# Check each credential
print("Step 2: Validating credentials...")
print()

credentials = {
    'TWITTER_API_KEY': os.getenv('TWITTER_API_KEY'),
    'TWITTER_API_SECRET': os.getenv('TWITTER_API_SECRET'),
    'TWITTER_ACCESS_TOKEN': os.getenv('TWITTER_ACCESS_TOKEN'),
    'TWITTER_ACCESS_SECRET': os.getenv('TWITTER_ACCESS_SECRET')
}

all_valid = True

for name, value in credentials.items():
    if value and value != 'your_api_key_here' and len(value) > 10:
        # Mask sensitive values
        masked = value[:10] + '...' + value[-5:] if len(value) > 20 else value[:5] + '...'
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
    print("Please update your .env file")
    print("See TWITTER-SETUP-GUIDE.md for setup instructions")
    sys.exit(1)

# Test Twitter API connection
print("Step 3: Testing Twitter API connection...")
print()

try:
    from twitter_watcher import TwitterClient
    
    twitter = TwitterClient()
    
    # Get user info
    print("Fetching Twitter user information...")
    user_info = twitter.get_me()
    
    print()
    print("=" * 60)
    print("✅ CREDENTIALS VALID!")
    print("=" * 60)
    print()
    print("Connected to Twitter:")
    print(f"  Username: @{user_info.get('username')}")
    print(f"  User ID: {user_info.get('id')}")
    print(f"  Description: {user_info.get('description', 'N/A')[:100]}")
    metrics = user_info.get('public_metrics', {})
    print(f"  Followers: {metrics.get('followers_count', 0)}")
    print(f"  Following: {metrics.get('following_count', 0)}")
    print(f"  Tweets: {metrics.get('tweet_count', 0)}")
    print()
    print("Next steps:")
    print("  1. Twitter Watcher is ready to use")
    print("  2. Run: python scripts\\twitter_watcher.py --vault AI_Employee_Vault")
    print("  3. Test posting: python scripts\\test_twitter_post.py")
    print()
    
except Exception as e:
    print("=" * 60)
    print("⚠️  API CONNECTION FAILED")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    print("Possible issues:")
    print("  1. Invalid credentials - check .env file")
    print("  2. App not approved - check Twitter Developer Portal")
    print("  3. Rate limit exceeded - wait 15 minutes")
    print()
    print("Credentials are saved, but API connection failed.")
    print("You can still proceed, but Twitter features won't work until API is connected.")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
