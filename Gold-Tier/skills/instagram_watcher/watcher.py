"""
Instagram Watcher - Continuous Monitoring

Monitors Instagram Business Account for:
- New comments on posts
- New mentions (tagged media)

Creates action files in Needs_Action/ for human/AI review.

Usage:
    python skills/instagram_watcher/watcher.py --vault AI_Employee_Vault --check-interval 300
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_watcher import BaseWatcher
from logging_config import get_recommended_logger
from instagram_posting.service import InstagramService


class InstagramWatcher(BaseWatcher):
    """
    Continuous watcher for Instagram Business Account.

    Monitors:
    - Comments on recent posts
    - Mentions (tagged media)
    """

    def __init__(self, vault_path: str, check_interval: int = 300, dry_run: bool = False):
        """
        Initialize Instagram watcher.

        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between checks (default: 300 = 5 minutes)
            dry_run: If True, log actions but don't create files
        """
        super().__init__(vault_path, check_interval, dry_run)

        # Use centralized logging with rotation
        self.logger = get_recommended_logger('instagram_watcher', vault_path=vault_path)

        # Initialize Instagram service
        try:
            self.instagram = InstagramService(vault_path=vault_path)
            self.logger.info("Instagram service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Instagram service: {e}")
            raise

        # Track last check time
        self.last_check_file = self.logs_dir / 'instagram_last_check.txt'
        self.last_check_time = self._load_last_check_time()

    def _load_last_check_time(self) -> datetime:
        """Load last check time from file."""
        if self.last_check_file.exists():
            try:
                timestamp = self.last_check_file.read_text().strip()
                return datetime.fromisoformat(timestamp)
            except:
                pass
        # Default to 1 hour ago
        return datetime.now()

    def _save_last_check_time(self):
        """Save last check time to file."""
        self.last_check_file.write_text(datetime.now().isoformat())

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Instagram for new comments and mentions.

        Returns:
            List of items to process (comments and mentions)
        """
        items = []

        try:
            # Check comments on recent posts
            self.logger.info("Checking Instagram comments...")
            comments_result = self.instagram.check_comments(recent_posts_limit=5)

            if comments_result.get('success') and comments_result.get('comments'):
                for comment in comments_result['comments']:
                    # Create unique ID for deduplication
                    item_id = f"comment_{comment.get('id', '')}"

                    if item_id not in self.processed_ids:
                        items.append({
                            'type': 'comment',
                            'id': item_id,
                            'data': comment
                        })
                        self.processed_ids.add(item_id)

                self.logger.info(f"Found {len(comments_result['comments'])} comments, {len([i for i in items if i['type'] == 'comment'])} new")

            # Check mentions
            self.logger.info("Checking Instagram mentions...")
            mentions_result = self.instagram.check_mentions()

            if mentions_result.get('success') and mentions_result.get('mentions'):
                for mention in mentions_result['mentions']:
                    # Create unique ID for deduplication
                    item_id = f"mention_{mention.get('id', '')}"

                    if item_id not in self.processed_ids:
                        items.append({
                            'type': 'mention',
                            'id': item_id,
                            'data': mention
                        })
                        self.processed_ids.add(item_id)

                self.logger.info(f"Found {len(mentions_result['mentions'])} mentions, {len([i for i in items if i['type'] == 'mention'])} new")

        except Exception as e:
            self.logger.error(f"Error checking Instagram: {e}", exc_info=True)
            self.stats['errors'] += 1

        return items

    def create_action_file(self, item: Dict[str, Any]) -> str:
        """
        Create action file for Instagram item.

        Args:
            item: Item dictionary with type, id, and data

        Returns:
            Path to created file
        """
        item_type = item['type']
        data = item['data']

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"instagram_{item_type}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Build content based on type
        if item_type == 'comment':
            content = f"""---
type: instagram_comment
source: instagram
created: {datetime.now().isoformat()}
status: needs_action
post_id: {data.get('post_id', 'unknown')}
comment_id: {data.get('id', 'unknown')}
username: {data.get('username', 'unknown')}
---

# Instagram Comment - Action Required

## Comment Details
- **From:** @{data.get('username', 'unknown')}
- **Post:** {data.get('post_caption', 'N/A')[:100]}...
- **Comment:** {data.get('text', 'N/A')}
- **Timestamp:** {data.get('timestamp', 'N/A')}
- **Likes:** {data.get('like_count', 0)}

## Post Context
- **Post ID:** {data.get('post_id', 'unknown')}
- **Post URL:** {data.get('post_permalink', 'N/A')}

## Suggested Actions
1. Reply to comment
2. Like comment
3. Ignore
4. Report (if spam/inappropriate)

---
*Created by Instagram Watcher*
"""

        elif item_type == 'mention':
            content = f"""---
type: instagram_mention
source: instagram
created: {datetime.now().isoformat()}
status: needs_action
media_id: {data.get('id', 'unknown')}
username: {data.get('username', 'unknown')}
---

# Instagram Mention - Action Required

## Mention Details
- **From:** @{data.get('username', 'unknown')}
- **Media Type:** {data.get('media_type', 'unknown')}
- **Caption:** {data.get('caption', 'N/A')[:200]}...
- **Timestamp:** {data.get('timestamp', 'N/A')}
- **Likes:** {data.get('like_count', 0)}
- **Comments:** {data.get('comments_count', 0)}

## Media
- **Media ID:** {data.get('id', 'unknown')}
- **Media URL:** {data.get('media_url', 'N/A')}
- **Permalink:** {data.get('permalink', 'N/A')}

## Suggested Actions
1. Comment on the mention
2. Like the post
3. Share/repost
4. Thank the user
5. Ignore

---
*Created by Instagram Watcher*
"""

        else:
            content = f"""---
type: instagram_{item_type}
source: instagram
created: {datetime.now().isoformat()}
status: needs_action
---

# Instagram {item_type.title()} - Action Required

{data}

---
*Created by Instagram Watcher*
"""

        if not self.dry_run:
            filepath.write_text(content, encoding='utf-8')
            self.logger.info(f"Created action file: {filename}")
        else:
            self.logger.info(f"[DRY RUN] Would create: {filename}")

        return str(filepath)

    def run(self):
        """Run the watcher loop."""
        self.logger.info("=" * 80)
        self.logger.info("INSTAGRAM WATCHER STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")
        self.logger.info(f"Dry run: {self.dry_run}")

        try:
            while True:
                try:
                    self.logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking Instagram...")

                    # Check for updates
                    items = self.check_for_updates()

                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")

                        # Create action files
                        for item in items:
                            try:
                                self.create_action_file(item)
                                self.stats['items_processed'] += 1
                                self.stats['files_created'] += 1
                            except Exception as e:
                                self.logger.error(f"Error creating action file: {e}")
                                self.stats['errors'] += 1
                    else:
                        self.logger.info("No new items")

                    # Save last check time
                    self._save_last_check_time()

                    # Log stats
                    uptime = (datetime.now() - self.stats['start_time']).total_seconds() / 3600
                    self.logger.info(f"Stats: {self.stats['items_processed']} processed, "
                                   f"{self.stats['files_created']} files created, "
                                   f"{self.stats['errors']} errors, "
                                   f"{uptime:.1f}h uptime")

                    # Sleep until next check
                    self.logger.info(f"Sleeping for {self.check_interval} seconds...")
                    time.sleep(self.check_interval)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    self.logger.error(f"Error in check loop: {e}", exc_info=True)
                    self.stats['errors'] += 1
                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("\n" + "=" * 80)
            self.logger.info("INSTAGRAM WATCHER STOPPED (Ctrl+C)")
            self.logger.info("=" * 80)
            self.logger.info(f"Final stats: {self.stats}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Instagram Watcher - Continuous Monitoring')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Path to Obsidian vault')
    parser.add_argument('--check-interval', type=int, default=300, help='Seconds between checks (default: 300)')
    parser.add_argument('--dry-run', action='store_true', help='Log actions but don\'t create files')

    args = parser.parse_args()

    watcher = InstagramWatcher(
        vault_path=args.vault,
        check_interval=args.check_interval,
        dry_run=args.dry_run
    )

    watcher.run()


if __name__ == '__main__':
    main()
