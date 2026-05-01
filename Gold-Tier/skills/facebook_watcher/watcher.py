"""
Facebook Watcher - Continuous Monitoring

Monitors Facebook Page for:
- New mentions/tags
- New comments on posts
- New messages (if configured)

Creates action files in Needs_Action/ for human/AI review.

Usage:
    python skills/facebook_watcher/watcher.py --vault AI_Employee_Vault --check-interval 300
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_watcher import BaseWatcher
from logging_config import get_recommended_logger
from facebook_posting.service import FacebookService


class FacebookWatcher(BaseWatcher):
    """
    Continuous watcher for Facebook Page.

    Monitors:
    - Mentions/tags of the page
    - Comments on posts
    - Page feed activity
    """

    def __init__(self, vault_path: str, check_interval: int = 300, dry_run: bool = False):
        """
        Initialize Facebook watcher.

        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between checks (default: 300 = 5 minutes)
            dry_run: If True, log actions but don't create files
        """
        super().__init__(vault_path, check_interval, dry_run)

        # Use centralized logging with rotation
        self.logger = get_recommended_logger('facebook_watcher', vault_path=vault_path)

        # Initialize Facebook service
        try:
            self.facebook = FacebookService(vault_path=vault_path)
            self.logger.info("Facebook service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Facebook service: {e}")
            raise

        # Track last check time
        self.last_check_file = self.logs_dir / 'facebook_last_check.txt'
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
        return datetime.now() - timedelta(hours=1)

    def _save_last_check_time(self):
        """Save last check time to file."""
        self.last_check_file.write_text(datetime.now().isoformat())

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Facebook for new mentions and activity.

        Returns:
            List of items to process (mentions, comments, etc.)
        """
        items = []

        try:
            # Calculate hours since last check
            hours_since = max(1, int((datetime.now() - self.last_check_time).total_seconds() / 3600))

            # Check mentions
            self.logger.info(f"Checking Facebook mentions (last {hours_since} hours)...")
            mentions_result = self.facebook.check_mentions(since_hours=hours_since)

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
            else:
                self.logger.info("No new mentions")

        except Exception as e:
            self.logger.error(f"Error checking Facebook: {e}", exc_info=True)
            self.stats['errors'] += 1

        return items

    def create_action_file(self, item: Dict[str, Any]) -> str:
        """
        Create action file for Facebook item.

        Args:
            item: Item dictionary with type, id, and data

        Returns:
            Path to created file
        """
        item_type = item['type']
        data = item['data']

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"facebook_{item_type}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Build content based on type
        if item_type == 'mention':
            content = f"""---
type: facebook_mention
source: facebook
created: {datetime.now().isoformat()}
status: needs_action
post_id: {data.get('id', 'unknown')}
from_name: {data.get('from', {}).get('name', 'unknown')}
from_id: {data.get('from', {}).get('id', 'unknown')}
---

# Facebook Mention - Action Required

## Mention Details
- **From:** {data.get('from', {}).get('name', 'Unknown')}
- **Message:** {data.get('message', 'N/A')[:500]}...
- **Created:** {data.get('created_time', 'N/A')}
- **Post URL:** {data.get('permalink_url', 'N/A')}

## Post ID
{data.get('id', 'unknown')}

## Suggested Actions
1. Reply to the mention
2. Like the post
3. Share the post
4. Thank the user
5. Ignore

## Raw Data
```json
{data}
```

---
*Created by Facebook Watcher*
"""

        else:
            content = f"""---
type: facebook_{item_type}
source: facebook
created: {datetime.now().isoformat()}
status: needs_action
---

# Facebook {item_type.title()} - Action Required

{data}

---
*Created by Facebook Watcher*
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
        self.logger.info("FACEBOOK WATCHER STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")
        self.logger.info(f"Dry run: {self.dry_run}")

        try:
            while True:
                try:
                    self.logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking Facebook...")

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
            self.logger.info("FACEBOOK WATCHER STOPPED (Ctrl+C)")
            self.logger.info("=" * 80)
            self.logger.info(f"Final stats: {self.stats}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Facebook Watcher - Continuous Monitoring')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Path to Obsidian vault')
    parser.add_argument('--check-interval', type=int, default=300, help='Seconds between checks (default: 300)')
    parser.add_argument('--dry-run', action='store_true', help='Log actions but don\'t create files')

    args = parser.parse_args()

    watcher = FacebookWatcher(
        vault_path=args.vault,
        check_interval=args.check_interval,
        dry_run=args.dry_run
    )

    watcher.run()


if __name__ == '__main__':
    main()
