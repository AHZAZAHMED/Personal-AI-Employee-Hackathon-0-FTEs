"""
Twitter Integration for AI Employee - Gold Tier

Uses official Twitter API v2 for monitoring and posting.

NOTE: Twitter API v2 requires payment for read access ($100/month).
This implementation is code-complete and ready to use once Twitter app is elevated.

Requirements:
- Twitter Developer Account
- Twitter App with elevated access
- TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

Setup:
1. Go to https://developer.twitter.com/
2. Create Developer Account
3. Create App and get credentials
4. Add to .env file
5. Elevate app access (required for read operations)

Usage:
    python scripts/twitter_watcher_official.py --vault AI_Employee_Vault --interval 300
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

# Load credentials from .env file
load_dotenv(Path(__file__).parent.parent / '.env')

# Twitter API Configuration
TWITTER_API_URL = 'https://api.twitter.com/2'
TWITTER_API_V1_URL = 'https://api.twitter.com/1.1'


class TwitterClient:
    """Client for Twitter API v2."""
    
    def __init__(self):
        """Initialize Twitter client with OAuth 1.0a credentials."""
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validate credentials
        self._validate_credentials()
        
        # Create OAuth 1.0a session
        self.oauth_session = OAuth1Session(
            client_key=self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret
        )
    
    def _validate_credentials(self):
        """Check if all required credentials are present."""
        missing = []
        if not self.api_key:
            missing.append('TWITTER_API_KEY')
        if not self.api_secret:
            missing.append('TWITTER_API_SECRET')
        if not self.access_token:
            missing.append('TWITTER_ACCESS_TOKEN')
        if not self.access_secret:
            missing.append('TWITTER_ACCESS_SECRET')
        
        if missing:
            raise ValueError(f"Missing Twitter credentials: {', '.join(missing)}")
    
    def get_me(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        try:
            url = f'{TWITTER_API_URL}/users/me'
            params = {'user.fields': 'username,description,public_metrics'}
            
            response = self.oauth_session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get('data', {})
            
        except Exception as e:
            self.logger.error(f"Failed to get user info: {e}")
            return {}
    
    def get_mentions(self, since_id: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent mentions using Twitter API v2.
        
        NOTE: Requires elevated access ($100/month or app elevation)
        
        Args:
            since_id: Get mentions since this tweet ID
            max_results: Maximum number of mentions (max 100)
            
        Returns:
            List of mentions
        """
        try:
            # Get my user ID first
            me = self.get_me()
            user_id = me.get('id')
            
            if not user_id:
                self.logger.error("Could not get user ID")
                return []
            
            url = f'{TWITTER_API_URL}/users/{user_id}/mentions'
            
            params = {
                'max_results': min(max_results, 100),
                'tweet.fields': 'created_at,author_id,text,public_metrics',
                'expansions': 'author_id'
            }
            
            if since_id:
                params['since_id'] = since_id
            
            response = self.oauth_session.get(url, params=params, timeout=30)
            
            if response.status_code == 403:
                self.logger.error("Twitter API requires elevated access for mentions")
                self.logger.error("Please elevate your app at: https://developer.twitter.com/en/portal/dashboard")
                return []
            
            response.raise_for_status()
            result = response.json()
            
            mentions = result.get('data', [])
            self.logger.info(f"Found {len(mentions)} mentions")
            
            return mentions
            
        except Exception as e:
            self.logger.error(f"Failed to get mentions: {e}")
            return []
    
    def post_tweet(self, tweet_text: str) -> Dict[str, Any]:
        """
        Post a tweet using Twitter API v1.1 (FREE tier).
        
        Args:
            tweet_text: Tweet text (max 280 characters)
            
        Returns:
            Post result
        """
        try:
            # Use Twitter API v1.1 for posting (FREE tier works)
            url = f'{TWITTER_API_V1_URL}/statuses/update.json'
            
            params = {
                'status': tweet_text,
                'tweet_mode': 'extended'
            }
            
            response = self.oauth_session.post(url, params=params, timeout=30)
            
            if response.status_code == 403:
                self.logger.error("Twitter app needs elevation for posting")
                self.logger.error("Please elevate your app at: https://developer.twitter.com/en/portal/dashboard")
                return {
                    'success': False,
                    'error': 'Twitter app requires elevation. Please visit developer portal.'
                }
            
            response.raise_for_status()
            result = response.json()
            
            tweet_id = result.get('id_str')
            self.logger.info(f"Posted tweet: {tweet_id}")
            
            return {
                'success': True,
                'tweet_id': tweet_id,
                'text': tweet_text,
                'url': f'https://twitter.com/i/web/status/{tweet_id}'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to post tweet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def post_reply(self, tweet_text: str, in_reply_to_tweet_id: str) -> Dict[str, Any]:
        """
        Post a reply tweet using Twitter API v1.1 (FREE tier).
        
        Args:
            tweet_text: Reply text
            in_reply_to_tweet_id: ID of tweet to reply to
            
        Returns:
            Post result
        """
        try:
            url = f'{TWITTER_API_V1_URL}/statuses/update.json'
            
            params = {
                'status': tweet_text,
                'in_reply_to_status_id': in_reply_to_tweet_id,
                'auto_populate_reply_metadata': 'true'
            }
            
            response = self.oauth_session.post(url, params=params, timeout=30)
            
            if response.status_code == 403:
                self.logger.error("Twitter app needs elevation for posting")
                return {
                    'success': False,
                    'error': 'Twitter app requires elevation'
                }
            
            response.raise_for_status()
            result = response.json()
            
            tweet_id = result.get('id_str')
            self.logger.info(f"Posted reply: {tweet_id}")
            
            return {
                'success': True,
                'tweet_id': tweet_id,
                'text': tweet_text,
                'in_reply_to': in_reply_to_tweet_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to post reply: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class TwitterWatcher:
    """Watches Twitter for mentions using official API."""
    
    def __init__(self, vault_path: str, check_interval: int = 300):
        """
        Initialize Twitter Watcher.
        
        Args:
            vault_path: Path to Obsidian vault
            check_interval: Check interval in seconds (default: 5 minutes)
        """
        self.vault = Path(vault_path)
        self.check_interval = check_interval
        self.needs_action = self.vault / 'Needs_Action'
        self.logs = self.vault / 'Logs'
        
        # Ensure folders exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # Initialize Twitter client
        try:
            self.twitter = TwitterClient()
            user_info = self.twitter.get_me()
            self.logger = logging.getLogger('TwitterWatcher')
            self.logger.info(f"Connected to Twitter: @{user_info.get('username')}")
        except Exception as e:
            self.logger = logging.getLogger('TwitterWatcher')
            self.logger.error(f"Failed to initialize Twitter client: {e}")
            self.twitter = None
        
        # Track processed tweets
        self.processed_file = self.logs / 'twitter_processed.json'
        self.processed_ids = self._load_processed()
        
        # Last since_id
        self.since_id = None
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs / 'twitter_watcher.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def _load_processed(self) -> set:
        """Load processed tweet IDs."""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except:
                pass
        return set()
    
    def _save_processed(self):
        """Save processed IDs to file."""
        processed_list = list(self.processed_ids)[-1000:]
        
        with open(self.processed_file, 'w') as f:
            json.dump({'processed_ids': processed_list}, f, indent=2)
    
    def _create_action_file(self, mention: Dict[str, Any]) -> Path:
        """Create action file in Needs_Action folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"TWITTER_mention_{timestamp}.md"
        filepath = self.needs_action / filename
        
        content = f"""---
type: twitter_mention
twitter_id: {mention.get('id')}
author_id: {mention.get('author_id')}
received: {mention.get('created_at')}
priority: normal
status: pending
---

# Twitter Mention

**Received:** {mention.get('created_at')}
**Text:** {mention.get('text', '')}

## Suggested Actions

- [ ] Review mention
- [ ] Draft response
- [ ] Post reply (requires approval)
- [ ] Archive after processing

---
*Detected by Twitter Watcher (Gold Tier)*
"""
        
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f"Created action file: {filename}")
        
        return filepath
    
    def check_for_updates(self):
        """Check Twitter for new mentions."""
        if not self.twitter:
            self.logger.error("Twitter client not initialized")
            return
        
        self.logger.info("Checking Twitter for mentions...")
        
        try:
            mentions = self.twitter.get_mentions(since_id=self.since_id, max_results=10)
            
            for mention in mentions:
                tweet_id = mention.get('id')
                if tweet_id and tweet_id not in self.processed_ids:
                    self._create_action_file(mention)
                    self.processed_ids.add(tweet_id)
                    
                    if not self.since_id or int(tweet_id) > int(self.since_id):
                        self.since_id = tweet_id
            
            self._save_processed()
            self.logger.info(f"Check complete. Found {len(mentions)} mentions.")
            
        except Exception as e:
            self.logger.error(f"Error checking Twitter: {e}")
    
    def run(self):
        """Run the watcher continuously."""
        if not self.twitter:
            self.logger.error("Twitter client not initialized. Cannot start watcher.")
            print("❌ Twitter client not initialized. Check credentials and app elevation.")
            return
        
        self.logger.info(f"Starting Twitter Watcher (interval: {self.check_interval}s)")
        print(f"🟢 Twitter Watcher started (checking every {self.check_interval} seconds)")
        print(f"📁 Vault: {self.vault}")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.check_for_updates()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Watcher stopped by user")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter Watcher (Official API)')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=300, help='Check interval (seconds)')
    parser.add_argument('--test-post', action='store_true', help='Test posting')
    
    args = parser.parse_args()
    
    if args.test_post:
        # Test Twitter posting
        print("=" * 60)
        print("TESTING TWITTER POSTING (Official API)")
        print("=" * 60)
        print()
        
        try:
            twitter = TwitterClient()
            user_info = twitter.get_me()
            
            if user_info:
                print(f"✅ Connected to Twitter: @{user_info.get('username')}")
                print()
                
                # Post test tweet
                test_tweet = f"""🤖 AI Employee Twitter Integration Test

Testing official Twitter API for posting (FREE tier).

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#AIEmployee #Automation #GoldTier #Hackathon2026"""
                
                print("Posting test tweet...")
                result = twitter.post_tweet(test_tweet)
                
                if result.get('success'):
                    print()
                    print("✅ TWEET POSTED SUCCESSFULLY!")
                    print()
                    print(f"Tweet ID: {result.get('tweet_id')}")
                    print(f"URL: {result.get('url')}")
                else:
                    print()
                    print("❌ POST FAILED")
                    print(f"Error: {result.get('error')}")
                    print()
                    print("To fix:")
                    print("  1. Go to https://developer.twitter.com/en/portal/dashboard")
                    print("  2. Select your app")
                    print("  3. Click 'Elevate your access'")
                    print("  4. Fill out use case description")
                    print("  5. Wait for approval (24-48 hours)")
                    print("  6. Regenerate credentials")
                    print("  7. Test again")
            else:
                print("❌ Failed to connect to Twitter")
                print("Check your credentials in .env file")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
            print("Twitter API requires app elevation for full functionality.")
            print("Visit: https://developer.twitter.com/en/portal/dashboard")
        
        print()
        print("=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        return
    
    # Run watcher
    watcher = TwitterWatcher(args.vault, args.interval)
    watcher.run()


if __name__ == '__main__':
    main()
