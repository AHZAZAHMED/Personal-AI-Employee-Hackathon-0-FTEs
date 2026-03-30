"""
Twitter/X Watcher & Poster for AI Employee - Gold Tier

Monitors Twitter for mentions and posts tweets automatically.
Uses Twitter API v2 for all operations.

Features:
- Monitor mentions and replies
- Auto-post tweets
- Engagement tracking
- Summary reports

Requirements:
- Twitter API Key
- Twitter API Secret
- Twitter Access Token
- Twitter Access Secret

Setup:
1. Follow TWITTER-SETUP-GUIDE.md
2. Add credentials to .env file
3. Run test_twitter_credentials.py

Usage:
    python scripts/twitter_watcher.py --vault AI_Employee_Vault --interval 60
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
TWITTER_UPLOAD_URL = 'https://upload.twitter.com/1.1'


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
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None, json_data: Dict = None) -> Dict:
        """
        Make request to Twitter API v2 using OAuth 1.0a.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Request parameters
            json_data: JSON payload
            
        Returns:
            API response
        """
        url = f'{TWITTER_API_URL}/{endpoint}'
        
        try:
            if method == 'GET':
                response = self.oauth_session.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = self.oauth_session.post(url, json=json_data, timeout=30)
            elif method == 'DELETE':
                response = self.oauth_session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Twitter API request failed: {e}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def get_me(self) -> Dict[str, Any]:
        """
        Get authenticated user information.
        
        Returns:
            User details
        """
        result = self._make_request('users/me', params={'user.fields': 'username,description,public_metrics'})
        
        self.logger.info(f"Connected to Twitter: @{result.get('data', {}).get('username')}")
        return result.get('data', {})
    
    def get_mentions(self, since_id: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent mentions.
        
        Args:
            since_id: Get mentions since this tweet ID
            max_results: Maximum number of mentions
            
        Returns:
            List of mentions
        """
        params = {
            'max_results': min(max_results, 100),
            'tweet.fields': 'created_at,author_id,text,public_metrics',
            'expansions': 'author_id'
        }
        
        if since_id:
            params['since_id'] = since_id
        
        result = self._make_request(f'tweets/search/recent', params=params)
        
        mentions = result.get('data', [])
        self.logger.info(f"Found {len(mentions)} recent mentions")
        
        return mentions
    
    def create_tweet(
        self,
        text: str,
        reply_tweet_id: Optional[str] = None,
        quote_tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a tweet.
        
        Args:
            text: Tweet text (max 280 characters)
            reply_tweet_id: ID of tweet to reply to
            quote_tweet_id: ID of tweet to quote
            
        Returns:
            Tweet creation result
        """
        json_data = {'text': text}
        
        if reply_tweet_id:
            json_data['reply'] = {'in_reply_to_tweet_id': reply_tweet_id}
        
        if quote_tweet_id:
            json_data['quote_tweet_id'] = quote_tweet_id
        
        result = self._make_request('tweets', method='POST', json_data=json_data)
        
        tweet_id = result.get('data', {}).get('id')
        self.logger.info(f"Created tweet: {tweet_id}")
        
        return {
            'success': True,
            'tweet_id': tweet_id,
            'text': text
        }
    
    def create_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """
        Create a thread of tweets.
        
        Args:
            tweets: List of tweet texts
            
        Returns:
            Thread creation result
        """
        if not tweets:
            return {'success': False, 'error': 'No tweets provided'}
        
        tweet_ids = []
        
        # Post first tweet
        result = self.create_tweet(text=tweets[0])
        if not result.get('success'):
            return result
        
        first_tweet_id = result.get('tweet_id')
        tweet_ids.append(first_tweet_id)
        previous_tweet_id = first_tweet_id
        
        # Post replies
        for i, tweet_text in enumerate(tweets[1:], 1):
            result = self.create_tweet(
                text=tweet_text,
                reply_tweet_id=previous_tweet_id
            )
            if result.get('success'):
                tweet_ids.append(result.get('tweet_id'))
                previous_tweet_id = result.get('tweet_id')
                self.logger.info(f"Posted thread tweet {i}: {result.get('tweet_id')}")
            else:
                self.logger.error(f"Failed to post thread tweet {i}")
                break
        
        return {
            'success': True,
            'tweet_ids': tweet_ids,
            'count': len(tweet_ids)
        }
    
    def get_user_tweets(self, user_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's recent tweets.
        
        Args:
            user_id: Twitter user ID
            max_results: Maximum number of tweets
            
        Returns:
            List of tweets
        """
        params = {
            'max_results': min(max_results, 100),
            'tweet.fields': 'created_at,text,public_metrics'
        }
        
        result = self._make_request(f'users/{user_id}/tweets', params=params)
        
        tweets = result.get('data', [])
        self.logger.info(f"Found {len(tweets)} tweets")
        
        return tweets
    
    def get_engagement_metrics(self, tweet_id: str) -> Dict[str, Any]:
        """
        Get engagement metrics for a tweet.
        
        Args:
            tweet_id: Tweet ID
            
        Returns:
            Engagement metrics
        """
        params = {
            'tweet.fields': 'public_metrics,created_at'
        }
        
        result = self._make_request(f'tweets/{tweet_id}', params=params)
        
        data = result.get('data', {})
        metrics = data.get('public_metrics', {})
        
        return {
            'tweet_id': tweet_id,
            'retweets': metrics.get('retweet_count', 0),
            'replies': metrics.get('reply_count', 0),
            'likes': metrics.get('like_count', 0),
            'quotes': metrics.get('quote_count', 0),
            'impressions': metrics.get('impression_count', 0),
            'created_at': data.get('created_at')
        }


class TwitterWatcher:
    """Watches Twitter for mentions and engagement."""
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize Twitter Watcher.
        
        Args:
            vault_path: Path to Obsidian vault
            check_interval: Check interval in seconds
        """
        self.vault = Path(vault_path)
        self.check_interval = check_interval
        self.needs_action = self.vault / 'Needs_Action'
        self.logs = self.vault / 'Logs'
        
        # Ensure folders exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # Initialize Twitter client
        self.twitter = TwitterClient()
        
        # Get user info
        self.user_info = self.twitter.get_me()
        self.user_id = self.user_info.get('id')
        
        # Track processed tweets
        self.processed_file = self.logs / 'twitter_processed.json'
        self.processed_ids = self._load_processed()
        
        # Last since_id
        self.since_id = None
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info("Twitter Watcher initialized")
    
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
        
        self.logger = logging.getLogger('TwitterWatcher')
    
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
    
    def _create_action_file(self, tweet: Dict[str, Any]) -> Path:
        """
        Create action file in Needs_Action folder.
        
        Args:
            tweet: Twitter mention
            
        Returns:
            Path to created file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"TWITTER_mention_{timestamp}.md"
        filepath = self.needs_action / filename
        
        # Extract data
        author_id = tweet.get('author_id')
        text = tweet.get('text', '')
        created_at = tweet.get('created_at', '')
        tweet_id = tweet.get('id')
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
        
        content = f"""---
type: twitter_mention
twitter_id: {tweet_id}
author_id: {author_id}
received: {created_at}
priority: normal
status: pending
tweet_url: {tweet_url}
---

# Twitter Mention

**Tweet ID:** {tweet_id}  
**Received:** {created_at}  
**Type:** Mention

## Content

{text}

## Link

[View on Twitter]({tweet_url})

## Suggested Actions

- [ ] Review mention
- [ ] Determine if response needed
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
        self.logger.info("Checking Twitter for updates...")
        
        try:
            # Get mentions
            mentions = self.twitter.get_mentions(since_id=self.since_id, max_results=10)
            
            for mention in mentions:
                tweet_id = mention.get('id')
                if tweet_id and tweet_id not in self.processed_ids:
                    self._create_action_file(mention)
                    self.processed_ids.add(tweet_id)
                    
                    # Update since_id
                    if not self.since_id or int(tweet_id) > int(self.since_id):
                        self.since_id = tweet_id
            
            # Save processed IDs
            self._save_processed()
            
            self.logger.info(f"Check complete. Found {len(mentions)} mentions.")
            
        except Exception as e:
            self.logger.error(f"Error checking Twitter: {e}")
    
    def run(self):
        """Run the watcher continuously."""
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
    
    parser = argparse.ArgumentParser(description='Twitter Watcher')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=60, help='Check interval (seconds)')
    
    args = parser.parse_args()
    
    watcher = TwitterWatcher(args.vault, args.interval)
    watcher.run()


if __name__ == '__main__':
    main()
