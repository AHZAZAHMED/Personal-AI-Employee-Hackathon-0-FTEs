"""
Instagram Watcher & Poster for AI Employee - Gold Tier

Monitors Instagram for comments/mentions and posts automatically.
Uses Facebook Graph API (Instagram uses same credentials as Facebook).

Features:
- Monitor comments and mentions
- Auto-post images and stories
- Engagement tracking
- Summary reports

Requirements:
- Instagram Business Account (free to convert)
- Instagram connected to Facebook Page
- Facebook credentials (same as Facebook integration)

Setup:
1. Convert Instagram to Business Account (Instagram Settings → Account)
2. Link Instagram to Facebook Page (Instagram Settings → Linked Accounts → Facebook)
3. Facebook credentials already in .env file

Usage:
    python scripts/instagram_watcher.py --vault AI_Employee_Vault --interval 60
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

# Load credentials from .env file
load_dotenv(Path(__file__).parent.parent / '.env')

# Instagram/Facebook API Configuration
GRAPH_API_URL = 'https://graph.facebook.com/v18.0'


class InstagramClient:
    """Client for Instagram Graph API."""
    
    def __init__(self):
        """Initialize Instagram client with Facebook credentials."""
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.page_token = os.getenv('FACEBOOK_PAGE_TOKEN')
        self.app_id = os.getenv('FACEBOOK_APP_ID')
        self.app_secret = os.getenv('FACEBOOK_APP_SECRET')
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.instagram_business_account_id = None
        
        # Validate credentials
        self._validate_credentials()
        
        # Get Instagram Business Account ID
        self._get_instagram_account()
    
    def _validate_credentials(self):
        """Check if all required credentials are present."""
        missing = []
        if not self.page_id:
            missing.append('FACEBOOK_PAGE_ID')
        if not self.page_token:
            missing.append('FACEBOOK_PAGE_TOKEN')
        
        if missing:
            raise ValueError(f"Missing Facebook credentials: {', '.join(missing)}")
    
    def _get_instagram_account(self):
        """Get Instagram Business Account ID linked to Facebook Page."""
        try:
            url = f'{GRAPH_API_URL}/{self.page_id}'
            params = {
                'fields': 'instagram_business_account',
                'access_token': self.page_token
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'instagram_business_account' in data:
                self.instagram_business_account_id = data['instagram_business_account']['id']
                self.logger.info(f"Connected to Instagram Business Account: {self.instagram_business_account_id}")
            else:
                self.logger.warning("No Instagram Business Account linked to this Facebook Page")
                self.logger.info("To link: Instagram Settings → Account → Switch to Professional Account → Link Facebook Page")
                
        except Exception as e:
            self.logger.error(f"Failed to get Instagram account: {e}")
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None, json_data: Dict = None) -> Dict:
        """
        Make request to Instagram Graph API.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Request parameters
            json_data: JSON payload
            
        Returns:
            API response
        """
        url = f'{GRAPH_API_URL}/{endpoint}'
        
        if params is None:
            params = {}
        
        # Add access token
        params['access_token'] = self.page_token
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, params=params, json=json_data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Instagram API request failed: {e}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get Instagram Business Account information.
        
        Returns:
            Account details
        """
        if not self.instagram_business_account_id:
            return {'error': 'Instagram Business Account not linked'}
        
        result = self._make_request(
            self.instagram_business_account_id,
            params={'fields': 'username,biography,website,followers_count,follows_count,media_count'}
        )
        
        self.logger.info(f"Connected to Instagram: @{result.get('username')}")
        return result
    
    def get_recent_media(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent media posts.
        
        Args:
            limit: Number of posts to retrieve
            
        Returns:
            List of media posts
        """
        if not self.instagram_business_account_id:
            return []
        
        result = self._make_request(
            f'{self.instagram_business_account_id}/media',
            params={
                'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
                'limit': limit
            }
        )
        
        media = result.get('data', [])
        self.logger.info(f"Found {len(media)} recent media posts")
        
        return media
    
    def get_comments(self, media_id: str) -> List[Dict[str, Any]]:
        """
        Get comments on a media post.
        
        Args:
            media_id: Instagram media ID
            
        Returns:
            List of comments
        """
        result = self._make_request(
            f'{media_id}/comments',
            params={'fields': 'id,from,username,text,timestamp,like_count'}
        )
        
        comments = result.get('data', [])
        self.logger.info(f"Found {len(comments)} comments on media {media_id}")
        
        return comments
    
    def get_mentions(self, since: datetime = None) -> List[Dict[str, Any]]:
        """
        Get recent mentions (tagged media).
        
        Args:
            since: Get mentions since this datetime
            
        Returns:
            List of mentions
        """
        if not self.instagram_business_account_id:
            return []
        
        # Instagram doesn't have direct mentions API, we'll check tagged media
        result = self._make_request(
            f'{self.instagram_business_account_id}/mentioned_media',
            params={
                'fields': 'id,caption,media_type,media_url,permalink,timestamp,owner',
                'limit': 50
            }
        )
        
        mentions = result.get('data', [])
        self.logger.info(f"Found {len(mentions)} recent mentions")
        
        return mentions
    
    def create_media_container(
        self,
        image_url: str,
        caption: str,
        media_type: str = 'IMAGE'
    ) -> Dict[str, Any]:
        """
        Create a media container (first step to posting).
        
        Args:
            image_url: URL of image to post
            caption: Caption text
            media_type: 'IMAGE' or 'CAROUSEL'
            
        Returns:
            Container creation result
        """
        if not self.instagram_business_account_id:
            return {'success': False, 'error': 'Instagram Business Account not linked'}
        
        params = {
            'image_url': image_url,
            'caption': caption,
            'media_type': media_type
        }
        
        result = self._make_request(
            f'{self.instagram_business_account_id}/media',
            method='POST',
            params=params
        )
        
        container_id = result.get('id')
        self.logger.info(f"Created media container: {container_id}")
        
        return {
            'success': True,
            'container_id': container_id,
            'caption': caption
        }
    
    def publish_media(self, container_id: str) -> Dict[str, Any]:
        """
        Publish a media container (second step to posting).
        
        Args:
            container_id: Media container ID from create_media_container
            
        Returns:
            Publication result
        """
        if not self.instagram_business_account_id:
            return {'success': False, 'error': 'Instagram Business Account not linked'}
        
        params = {
            'creation_id': container_id,
            'media_type': 'IMAGE'
        }
        
        result = self._make_request(
            f'{self.instagram_business_account_id}/media_publish',
            method='POST',
            params=params
        )
        
        post_id = result.get('id')
        self.logger.info(f"Published media: {post_id}")
        
        return {
            'success': True,
            'post_id': post_id,
            'message': 'Media published successfully'
        }
    
    def post_image(
        self,
        image_url: str,
        caption: str
    ) -> Dict[str, Any]:
        """
        Post an image to Instagram (combines container creation and publishing).
        
        Args:
            image_url: URL of image to post
            caption: Caption text
            
        Returns:
            Post result
        """
        try:
            # Step 1: Create media container
            container_result = self.create_media_container(image_url, caption)
            
            if not container_result.get('success'):
                return container_result
            
            container_id = container_result.get('container_id')
            
            # Step 2: Wait a moment for Instagram to process
            time.sleep(2)
            
            # Step 3: Publish the media
            publish_result = self.publish_media(container_id)
            
            return publish_result
            
        except Exception as e:
            self.logger.error(f"Failed to post image: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_insights(self, metric: str = 'impressions', days: int = 7) -> Dict[str, Any]:
        """
        Get Instagram insights/analytics.
        
        Args:
            metric: Metric to retrieve (impressions, reach, engagement, etc.)
            days: Number of days to retrieve
            
        Returns:
            Insights data
        """
        if not self.instagram_business_account_id:
            return {'error': 'Instagram Business Account not linked'}
        
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        until = datetime.now().strftime('%Y-%m-%d')
        
        result = self._make_request(
            f'{self.instagram_business_account_id}/insights',
            params={
                'metric': metric,
                'period': 'day',
                'since': since,
                'until': until
            }
        )
        
        insights = result.get('data', [])
        self.logger.info(f"Retrieved {len(insights)} insights")
        
        return insights


class InstagramWatcher:
    """Watches Instagram for comments and mentions."""
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize Instagram Watcher.
        
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
        
        # Initialize Instagram client
        try:
            self.instagram = InstagramClient()
            self.account_info = self.instagram.get_account_info()
        except Exception as e:
            self.logger = logging.getLogger('InstagramWatcher')
            self.logger.error(f"Failed to initialize Instagram client: {e}")
            self.instagram = None
            self.account_info = None
        
        # Track processed items
        self.processed_file = self.logs / 'instagram_processed.json'
        self.processed_ids = self._load_processed()
        
        # Last check time
        self.last_check = datetime.now() - timedelta(minutes=5)
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info("Instagram Watcher initialized")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs / 'instagram_watcher.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('InstagramWatcher')
    
    def _load_processed(self) -> set:
        """Load processed Instagram IDs."""
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
            item: Instagram comment/mention
            item_type: 'comment' or 'mention'
            
        Returns:
            Path to created file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"INSTAGRAM_{item_type}_{timestamp}.md"
        filepath = self.needs_action / filename
        
        # Extract data
        username = item.get('username', 'Unknown')
        text = item.get('text', item.get('caption', ''))
        created_time = item.get('timestamp', '')
        permalink = item.get('permalink', '')
        
        content = f"""---
type: instagram_{item_type}
instagram_id: {item.get('id')}
username: {username}
received: {created_time}
priority: normal
status: pending
permalink: {permalink}
---

# Instagram {item_type.title()}

**Username:** @{username}  
**Received:** {created_time}  
**Type:** {item_type.title()}

## Content

{text}

## Link

[View on Instagram]({permalink})

## Suggested Actions

- [ ] Review {item_type}
- [ ] Determine if response needed
- [ ] Draft response
- [ ] Post reply (requires approval)
- [ ] Archive after processing

---
*Detected by Instagram Watcher (Gold Tier)*
"""
        
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f"Created action file: {filename}")
        
        return filepath
    
    def check_for_updates(self):
        """Check Instagram for new comments and mentions."""
        if not self.instagram:
            self.logger.error("Instagram client not initialized")
            return
        
        self.logger.info("Checking Instagram for updates...")
        
        try:
            # Get recent media
            recent_media = self.instagram.get_recent_media(limit=5)
            
            new_items = 0
            
            # Check comments on each media
            for media in recent_media:
                media_id = media.get('id')
                comments = self.instagram.get_comments(media_id)
                
                for comment in comments:
                    comment_id = comment.get('id')
                    if comment_id and comment_id not in self.processed_ids:
                        self._create_action_file(comment, 'comment')
                        self.processed_ids.add(comment_id)
                        new_items += 1
            
            # Get mentions
            mentions = self.instagram.get_mentions(since=self.last_check)
            
            for mention in mentions:
                mention_id = mention.get('id')
                if mention_id and mention_id not in self.processed_ids:
                    self._create_action_file(mention, 'mention')
                    self.processed_ids.add(mention_id)
                    new_items += 1
            
            # Save processed IDs
            self._save_processed()
            
            # Update last check time
            self.last_check = datetime.now()
            
            self.logger.info(f"Check complete. Found {new_items} new items.")
            
        except Exception as e:
            self.logger.error(f"Error checking Instagram: {e}")
    
    def run(self):
        """Run the watcher continuously."""
        if not self.instagram:
            self.logger.error("Instagram client not initialized. Cannot start watcher.")
            print("❌ Instagram client not initialized. Check credentials and Instagram Business Account setup.")
            return
        
        self.logger.info(f"Starting Instagram Watcher (interval: {self.check_interval}s)")
        print(f"🟢 Instagram Watcher started (checking every {self.check_interval} seconds)")
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
    
    parser = argparse.ArgumentParser(description='Instagram Watcher')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=60, help='Check interval (seconds)')
    
    args = parser.parse_args()
    
    watcher = InstagramWatcher(args.vault, args.interval)
    watcher.run()


if __name__ == '__main__':
    main()
