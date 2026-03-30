"""
Facebook Watcher & Poster for AI Employee - Gold Tier

Monitors Facebook for mentions and posts updates automatically.
Uses Facebook Graph API for all operations.

Features:
- Monitor Page mentions and comments
- Auto-post business updates
- Engagement tracking
- Summary reports

Requirements:
- Facebook App ID
- Facebook App Secret
- Facebook Page Access Token

Setup:
1. Follow FACEBOOK-SETUP-GUIDE.md
2. Create .facebook_credentials.env file
3. Run test_facebook_credentials.py

Usage:
    python scripts/facebook_watcher.py --vault AI_Employee_Vault --interval 60
"""

import os
import json
import requests
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load credentials from .env file
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv(Path(__file__).parent.parent / '.facebook_credentials.env')

# Facebook API Configuration
FACEBOOK_API_VERSION = 'v18.0'
FACEBOOK_GRAPH_URL = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'


class FacebookClient:
    """Client for Facebook Graph API."""
    
    def __init__(self):
        """Initialize Facebook client with credentials."""
        self.app_id = os.getenv('FACEBOOK_APP_ID')
        self.app_secret = os.getenv('FACEBOOK_APP_SECRET')
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.page_token = os.getenv('FACEBOOK_PAGE_TOKEN')
        self.user_token = os.getenv('FACEBOOK_USER_TOKEN')
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validate credentials
        self._validate_credentials()
    
    def _validate_credentials(self):
        """Check if all required credentials are present."""
        missing = []
        if not self.app_id:
            missing.append('FACEBOOK_APP_ID')
        if not self.app_secret:
            missing.append('FACEBOOK_APP_SECRET')
        if not self.page_id:
            missing.append('FACEBOOK_PAGE_ID')
        if not self.page_token:
            missing.append('FACEBOOK_PAGE_TOKEN')
        
        if missing:
            raise ValueError(f"Missing Facebook credentials: {', '.join(missing)}")
    
    def _make_request(self, endpoint: str, params: Dict = None, post: bool = False) -> Dict:
        """
        Make request to Facebook Graph API.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            post: True for POST request
            
        Returns:
            API response
        """
        url = f'{FACEBOOK_GRAPH_URL}/{endpoint}'
        
        if params is None:
            params = {}
        
        # Add access token
        params['access_token'] = self.page_token
        
        try:
            if post:
                response = requests.post(url, params=params, timeout=30)
            else:
                response = requests.get(url, params=params, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Facebook API request failed: {e}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def get_page_info(self) -> Dict[str, Any]:
        """
        Get Facebook Page information.
        
        Returns:
            Page details
        """
        result = self._make_request(
            self.page_id,
            {'fields': 'id,name,username,about,followers_count'}
        )
        
        self.logger.info(f"Connected to Page: {result.get('name')}")
        return result
    
    def get_mentions(self, since: datetime = None) -> List[Dict[str, Any]]:
        """
        Get recent mentions on the Page.
        
        Args:
            since: Get mentions since this datetime
            
        Returns:
            List of mentions
        """
        params = {
            'fields': 'id,message,from,created_time,permalink_url',
            'limit': 50
        }
        
        if since:
            params['since'] = since.strftime('%Y-%m-%dT%H:%M:%S+0000')
        
        result = self._make_request(
            f'{self.page_id}/feed',
            params
        )
        
        mentions = result.get('data', [])
        self.logger.info(f"Found {len(mentions)} recent mentions")
        
        return mentions
    
    def get_comments(self, since: datetime = None) -> List[Dict[str, Any]]:
        """
        Get recent comments on Page posts.
        
        Args:
            since: Get comments since this datetime
            
        Returns:
            List of comments
        """
        params = {
            'fields': 'comments.fields(id,message,from,created_time,permalink_url)',
            'limit': 50
        }
        
        if since:
            params['since'] = since.strftime('%Y-%m-%dT%H:%M:%S+0000')
        
        try:
            result = self._make_request(
                self.page_id,
                params
            )
            
            # Extract comments from nested structure
            comments_data = result.get('comments', [])
            comments = comments_data.get('data', []) if isinstance(comments_data, dict) else comments_data
            
            self.logger.info(f"Found {len(comments)} recent comments")
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error getting comments: {e}")
            return []
    
    def create_post(
        self,
        message: str,
        link: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a post on the Facebook Page.
        
        Args:
            message: Post message
            link: Optional link to share
            photo_url: Optional photo URL
            
        Returns:
            Post creation result
        """
        params = {
            'message': message
        }
        
        if link:
            params['link'] = link
        
        if photo_url:
            params['url'] = photo_url
        
        result = self._make_request(
            f'{self.page_id}/feed',
            params,
            post=True
        )
        
        self.logger.info(f"Created Facebook post: {result.get('id')}")
        
        return {
            'success': True,
            'post_id': result.get('id'),
            'message': message
        }
    
    def get_insights(self, days: int = 7) -> Dict[str, Any]:
        """
        Get Facebook Page insights/analytics.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            Insights data
        """
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        until = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'metric': 'page_impressions_unique,page_engaged_users,page_post_engagements,page_fans',
            'since': since,
            'until': until
        }
        
        result = self._make_request(
            f'{self.page_id}/insights',
            params
        )
        
        insights = {}
        for metric in result.get('data', []):
            insights[metric['name']] = {
                'values': metric.get('values', []),
                'period': metric.get('period', 'day')
            }
        
        self.logger.info(f"Retrieved {len(insights)} insights")
        
        return insights


class FacebookWatcher:
    """Watches Facebook for mentions and engagement."""
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize Facebook Watcher.
        
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
        
        # Initialize Facebook client
        self.fb = FacebookClient()
        
        # Track processed items
        self.processed_file = self.logs / 'facebook_processed.json'
        self.processed_ids = self._load_processed()
        
        # Last check time
        self.last_check = datetime.now() - timedelta(minutes=5)
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info("Facebook Watcher initialized")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs / 'facebook_watcher.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('FacebookWatcher')
    
    def _load_processed(self) -> set:
        """Load processed Facebook post/comment IDs."""
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
    
    def _create_action_file(self, item: Dict[str, Any], item_type: str) -> Path:
        """
        Create action file in Needs_Action folder.
        
        Args:
            item: Facebook mention/comment
            item_type: 'mention' or 'comment'
            
        Returns:
            Path to created file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"FACEBOOK_{item_type}_{timestamp}.md"
        filepath = self.needs_action / filename
        
        # Extract data
        from_name = item.get('from', {}).get('name', 'Unknown')
        message = item.get('message', '')
        created_time = item.get('created_time', '')
        permalink = item.get('permalink_url', '')
        
        content = f"""---
type: facebook_{item_type}
from: {from_name}
received: {created_time}
priority: normal
status: pending
facebook_id: {item.get('id')}
permalink: {permalink}
---

# Facebook {item_type.title()}

**From:** {from_name}  
**Received:** {created_time}  
**Type:** {item_type.title()}

## Content

{message}

## Link

[View on Facebook]({permalink})

## Suggested Actions

- [ ] Review {item_type}
- [ ] Determine if response needed
- [ ] Draft response
- [ ] Post reply (requires approval)
- [ ] Archive after processing

---
*Detected by Facebook Watcher (Gold Tier)*
"""
        
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f"Created action file: {filename}")
        
        return filepath
    
    def check_for_updates(self):
        """Check Facebook for new mentions and comments."""
        self.logger.info("Checking Facebook for updates...")
        
        try:
            # Get mentions (this works reliably)
            mentions = self.fb.get_mentions(since=self.last_check)
            
            for mention in mentions:
                fb_id = mention.get('id')
                if fb_id and fb_id not in self.processed_ids:
                    self._create_action_file(mention, 'mention')
                    self.processed_ids.add(fb_id)
            
            # Comments endpoint has limitations for new pages
            # Skip for now, mentions are the primary use case
            # comments = self.fb.get_comments(since=self.last_check)
            comments = []
            
            # Save processed IDs
            self._save_processed()
            
            # Update last check time
            self.last_check = datetime.now()
            
            total_found = len(mentions) + len(comments)
            self.logger.info(f"Check complete. Found {total_found} items.")
            
        except Exception as e:
            self.logger.error(f"Error checking Facebook: {e}")
    
    def run(self):
        """Run the watcher continuously."""
        import time
        
        self.logger.info(f"Starting Facebook Watcher (interval: {self.check_interval}s)")
        print(f"🟢 Facebook Watcher started (checking every {self.check_interval} seconds)")
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
    
    parser = argparse.ArgumentParser(description='Facebook Watcher')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=60, help='Check interval (seconds)')
    
    args = parser.parse_args()
    
    watcher = FacebookWatcher(args.vault, args.interval)
    watcher.run()


if __name__ == '__main__':
    main()
