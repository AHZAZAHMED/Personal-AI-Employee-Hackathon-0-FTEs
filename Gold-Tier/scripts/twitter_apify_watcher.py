"""
Apify Twitter Scraper for AI Employee - Gold Tier

Scrapes Twitter mentions using Apify (FREE) and posts replies using official Twitter API (FREE tier).

Workflow:
1. Apify API → Scrape Twitter mentions (FREE - bypasses read paywall)
2. AI Processing → Generate response
3. Twitter API → Post reply (FREE tier works for posting)

Requirements:
- Apify Account (FREE - $5 credits/month)
- Apify Personal API Token
- Twitter API credentials (for posting only)

Setup:
1. Create Apify account: https://apify.com/
2. Get Personal API Token: Settings → API & Tokens
3. Add to .env: APIFY_API_TOKEN=your_token_here
4. Add Twitter credentials for posting

Usage:
    python scripts/twitter_apify_watcher.py --vault AI_Employee_Vault --interval 300
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

# API Configuration
APIFY_API_URL = 'https://api.apify.com/v2'
TWITTER_API_URL = 'https://api.twitter.com/2'


class ApifyTwitterScraper:
    """Scrapes Twitter mentions using Apify (FREE)."""
    
    def __init__(self):
        """Initialize Apify Twitter Scraper."""
        self.apify_token = os.getenv('APIFY_API_TOKEN')
        self.search_query = os.getenv('TWITTER_SEARCH_QUERY', '@Ahzaz_Ahmed1')
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validate credentials
        if not self.apify_token:
            raise ValueError("Missing APIFY_API_TOKEN in .env file")
        
        self.logger.info(f"Apify Scraper initialized for: {self.search_query}")
    
    def scrape_mentions(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape Twitter mentions using Apify Actor.
        
        Args:
            max_results: Maximum number of mentions to scrape
            
        Returns:
            List of mention dictionaries
        """
        self.logger.info(f"Scraping Twitter for: {self.search_query}")
        
        try:
            # Use Apify's Twitter Scraper Actor
            # Actor ID: apify/instagram-scraper (also works for Twitter)
            # Or use: compass/crawler-x-twitter
            actor_id = 'compass/crawler-x-twitter'
            
            # Prepare input for the actor
            actor_input = {
                'startUrls': [f'https://twitter.com/search?q={self.search_query}&f=live'],
                'maxRequestCount': max_results,
                'searchMode': 'Live',
                'addUserInfo': True,
                'addTweetUrl': True
            }
            
            # Start Apify Actor run
            run_url = f'{APIFY_API_URL}/acts/{actor_id}/runs'
            headers = {
                'Authorization': f'Bearer {self.apify_token}',
                'Content-Type': 'application/json'
            }
            
            self.logger.info("Starting Apify Twitter Scraper Actor...")
            
            response = requests.post(
                run_url,
                headers=headers,
                json=actor_input,
                timeout=60
            )
            response.raise_for_status()
            
            run_data = response.json()
            run_id = run_data.get('data', {}).get('id')
            
            if not run_id:
                raise Exception("Failed to start Apify Actor run")
            
            self.logger.info(f"Actor run started: {run_id}")
            
            # Wait for Actor to complete
            self.logger.info("Waiting for scraper to complete...")
            time.sleep(30)  # Give it time to scrape
            
            # Get results
            dataset_url = f'{APIFY_API_URL}/runs/{run_id}/dataset/items'
            params = {
                'limit': max_results,
                'clean': True  # Clean the data
            }
            
            response = requests.get(
                dataset_url,
                headers=headers,
                params=params,
                timeout=60
            )
            response.raise_for_status()
            
            mentions = response.json()
            
            self.logger.info(f"Scraped {len(mentions)} mentions from Twitter")
            
            # Convert to standard format
            formatted_mentions = []
            for mention in mentions:
                formatted_mentions.append({
                    'id': mention.get('tweetId'),
                    'text': mention.get('text', ''),
                    'username': mention.get('username', 'Unknown'),
                    'user_id': mention.get('userId'),
                    'created_at': mention.get('createdAt'),
                    'url': mention.get('tweetUrl'),
                    'is_reply': mention.get('isReply', False),
                    'is_retweet': mention.get('isRetweet', False)
                })
            
            return formatted_mentions
            
        except Exception as e:
            self.logger.error(f"Apify scraping failed: {e}")
            return []


class TwitterPoster:
    """Posts replies to Twitter using official API (FREE tier)."""
    
    def __init__(self):
        """Initialize Twitter Poster with OAuth 1.0a credentials."""
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
            # Use Twitter API v1.1 (still supports free tier)
            url = 'https://api.twitter.com/1.1/statuses/update.json'
            
            params = {
                'status': tweet_text,
                'in_reply_to_status_id': in_reply_to_tweet_id,
                'auto_populate_reply_metadata': 'true'
            }
            
            response = self.oauth_session.post(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            tweet_id = result.get('id_str')
            
            self.logger.info(f"Posted reply tweet: {tweet_id}")
            
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
    
    def post_tweet(self, tweet_text: str) -> Dict[str, Any]:
        """
        Post a regular tweet using Twitter API v1.1 (FREE tier).
        
        Args:
            tweet_text: Tweet text
            
        Returns:
            Post result
        """
        try:
            # Use Twitter API v1.1 (still supports free tier)
            url = 'https://api.twitter.com/1.1/statuses/update.json'
            
            params = {'status': tweet_text}
            
            response = self.oauth_session.post(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            tweet_id = result.get('id_str')
            
            self.logger.info(f"Posted tweet: {tweet_id}")
            
            return {
                'success': True,
                'tweet_id': tweet_id,
                'text': tweet_text
            }
            
        except Exception as e:
            self.logger.error(f"Failed to post tweet: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class TwitterApifyWatcher:
    """Watches Twitter using Apify scraper and posts with official API."""
    
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
        
        # Initialize scraper and poster
        self.scraper = ApifyTwitterScraper()
        self.poster = TwitterPoster()
        
        # Track processed tweets
        self.processed_file = self.logs / 'twitter_processed.json'
        self.processed_ids = self._load_processed()
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info("Twitter Apify Watcher initialized")
        self.logger.info("Reading: Apify Scraper (FREE)")
        self.logger.info("Posting: Twitter API (FREE tier)")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs / 'twitter_apify_watcher.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('TwitterApifyWatcher')
    
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
        # Keep only last 1000 IDs
        processed_list = list(self.processed_ids)[-1000:]
        
        with open(self.processed_file, 'w') as f:
            json.dump({'processed_ids': processed_list}, f, indent=2)
    
    def _create_action_file(self, mention: Dict[str, Any]) -> Path:
        """
        Create action file in Needs_Action folder.
        
        Args:
            mention: Twitter mention
            
        Returns:
            Path to created file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"TWITTER_mention_{timestamp}.md"
        filepath = self.needs_action / filename
        
        content = f"""---
type: twitter_mention
twitter_id: {mention.get('id')}
username: @{mention.get('username', 'Unknown')}
received: {mention.get('created_at')}
priority: normal
status: pending
tweet_url: {mention.get('url')}
---

# Twitter Mention

**Username:** @{mention.get('username', 'Unknown')}  
**Received:** {mention.get('created_at')}  
**Type:** Mention

## Content

{mention.get('text', '')}

## Link

[View on Twitter]({mention.get('url')})

## Suggested Actions

- [ ] Review mention
- [ ] Determine if response needed
- [ ] Draft response
- [ ] Post reply (requires approval)
- [ ] Archive after processing

---
*Detected by Twitter Apify Watcher (Gold Tier)*
"""
        
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f"Created action file: {filename}")
        
        return filepath
    
    def check_for_updates(self):
        """Check Twitter for new mentions using Apify scraper."""
        self.logger.info("Checking Twitter for mentions (via Apify)...")
        
        try:
            # Scrape mentions using Apify (FREE)
            mentions = self.scraper.scrape_mentions(max_results=50)
            
            new_items = 0
            
            for mention in mentions:
                tweet_id = mention.get('id')
                
                # Skip if already processed
                if tweet_id and tweet_id not in self.processed_ids:
                    # Skip our own tweets
                    if mention.get('username') == 'Ahzaz_Ahmed1':
                        continue
                    
                    # Create action file
                    self._create_action_file(mention)
                    self.processed_ids.add(tweet_id)
                    new_items += 1
                    
                    self.logger.info(f"New mention from @{mention.get('username')}: {mention.get('text', '')[:50]}...")
            
            # Save processed IDs
            self._save_processed()
            
            self.logger.info(f"Check complete. Found {new_items} new mentions.")
            
        except Exception as e:
            self.logger.error(f"Error checking Twitter: {e}")
    
    def post_ai_reply(self, tweet_id: str, reply_text: str) -> Dict[str, Any]:
        """
        Post AI-generated reply to a tweet.
        
        Args:
            tweet_id: ID of tweet to reply to
            reply_text: AI-generated reply text
            
        Returns:
            Post result
        """
        self.logger.info(f"Posting reply to tweet {tweet_id}")
        
        result = self.poster.post_reply(reply_text, tweet_id)
        
        if result.get('success'):
            self.logger.info(f"Reply posted successfully: {result.get('tweet_id')}")
        else:
            self.logger.error(f"Failed to post reply: {result.get('error')}")
        
        return result
    
    def run(self):
        """Run the watcher continuously."""
        self.logger.info(f"Starting Twitter Apify Watcher (interval: {self.check_interval}s)")
        print(f"🟢 Twitter Apify Watcher started")
        print(f"📊 Reading: Apify Scraper (FREE)")
        print(f"📝 Posting: Twitter API (FREE tier)")
        print(f"📁 Vault: {self.vault}")
        print(f"⏰ Check interval: {self.check_interval} seconds")
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
    
    parser = argparse.ArgumentParser(description='Twitter Apify Watcher')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=300, help='Check interval (seconds)')
    parser.add_argument('--test-scrape', action='store_true', help='Test scraping only')
    parser.add_argument('--test-post', action='store_true', help='Test posting only')
    
    args = parser.parse_args()
    
    if args.test_scrape:
        # Test Apify scraping
        print("=" * 60)
        print("TESTING APIFY TWITTER SCRAPER")
        print("=" * 60)
        print()
        
        scraper = ApifyTwitterScraper()
        mentions = scraper.scrape_mentions(max_results=10)
        
        print(f"✅ Scraped {len(mentions)} mentions")
        print()
        
        for i, mention in enumerate(mentions[:5], 1):
            print(f"{i}. @{mention.get('username')}: {mention.get('text', '')[:100]}...")
        
        return
    
    if args.test_post:
        # Test Twitter posting
        print("=" * 60)
        print("TESTING TWITTER POSTING")
        print("=" * 60)
        print()
        
        poster = TwitterPoster()
        
        # Post test tweet
        result = poster.post_tweet("🤖 AI Employee Twitter Integration Test\n\nTesting official Twitter API for posting (FREE tier).\n\n#AIEmployee #Automation #GoldTier")
        
        if result.get('success'):
            print(f"✅ Tweet posted successfully!")
            print(f"Tweet ID: {result.get('tweet_id')}")
            print(f"URL: https://twitter.com/i/web/status/{result.get('tweet_id')}")
        else:
            print(f"❌ Failed to post: {result.get('error')}")
        
        return
    
    # Run watcher
    watcher = TwitterApifyWatcher(args.vault, args.interval)
    watcher.run()


if __name__ == '__main__':
    main()
