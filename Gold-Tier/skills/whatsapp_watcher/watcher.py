"""
WhatsApp Watcher - Continuous Monitoring

Monitors WhatsApp messages via Twilio API and Neon PostgreSQL.

Checks for:
- New incoming messages
- Unread messages

Creates action files in Needs_Action/ for human/AI review.

Usage:
    python skills/whatsapp_watcher/watcher.py --vault AI_Employee_Vault --check-interval 60
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
from whatsapp.service import WhatsAppService


class WhatsAppWatcher(BaseWatcher):
    """
    Continuous watcher for WhatsApp messages via Twilio.

    Monitors:
    - New incoming messages from database
    - Unread messages
    """

    def __init__(self, vault_path: str, check_interval: int = 60, dry_run: bool = False):
        """
        Initialize WhatsApp watcher.

        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between checks (default: 60 = 1 minute)
            dry_run: If True, log actions but don't create files
        """
        super().__init__(vault_path, check_interval, dry_run)

        # Use centralized logging with rotation
        self.logger = get_recommended_logger('whatsapp_watcher', vault_path=vault_path)

        # Initialize WhatsApp service
        try:
            self.whatsapp = WhatsAppService(vault_path=vault_path)
            self.logger.info("WhatsApp service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WhatsApp service: {e}")
            raise

        # Track last check time
        self.last_check_file = self.logs_dir / 'whatsapp_last_check.txt'
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
        Check WhatsApp for new incoming messages.

        Returns:
            List of items to process (messages)
        """
        items = []

        try:
            # Get recent messages from database
            self.logger.info("Checking WhatsApp messages from database...")

            # Query database for messages since last check
            query = """
                SELECT id, message_sid, from_number, to_number, body,
                       direction, status, created_at
                FROM whatsapp_messages
                WHERE direction = 'inbound'
                  AND created_at > %s
                ORDER BY created_at DESC
                LIMIT 50
            """

            messages = self.whatsapp.db.execute_query(
                query,
                (self.last_check_time,)
            )

            if messages:
                for msg in messages:
                    # Create unique ID for deduplication
                    item_id = f"message_{msg.get('message_sid', msg.get('id', ''))}"

                    if item_id not in self.processed_ids:
                        items.append({
                            'type': 'message',
                            'id': item_id,
                            'data': msg
                        })
                        self.processed_ids.add(item_id)

                self.logger.info(f"Found {len(messages)} messages, {len(items)} new")
            else:
                self.logger.info("No new messages")

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}", exc_info=True)
            self.stats['errors'] += 1

        return items

    def create_action_file(self, item: Dict[str, Any]) -> str:
        """
        Create action file for WhatsApp message.

        Args:
            item: Item dictionary with type, id, and data

        Returns:
            Path to created file
        """
        item_type = item['type']
        data = item['data']

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Clean phone number for filename
        from_number = data.get('from_number', 'unknown')
        clean_number = from_number.replace('whatsapp:', '').replace('+', '').replace(' ', '')

        filename = f"whatsapp_{item_type}_{clean_number}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Build content
        if item_type == 'message':
            content = f"""---
type: whatsapp_message
source: whatsapp
created: {datetime.now().isoformat()}
status: needs_action
message_sid: {data.get('message_sid', 'unknown')}
from_number: {data.get('from_number', 'unknown')}
to_number: {data.get('to_number', 'unknown')}
direction: {data.get('direction', 'inbound')}
---

# WhatsApp Message - Action Required

## Message Details
- **From:** {data.get('from_number', 'Unknown')}
- **To:** {data.get('to_number', 'Unknown')}
- **Received:** {data.get('created_at', 'N/A')}
- **Status:** {data.get('status', 'unknown')}

## Message Content
```
{data.get('body', 'N/A')}
```

## Message ID
- **SID:** {data.get('message_sid', 'unknown')}
- **Database ID:** {data.get('id', 'unknown')}

## Suggested Actions
1. Reply to the message
2. Forward to team member
3. Create task from message
4. Archive/ignore
5. Mark as spam

## Reply Template
To reply, use the WhatsApp skill:
```
whatsapp_send(
    to="{data.get('from_number', '')}",
    message="Your reply here"
)
```

---
*Created by WhatsApp Watcher*
"""

        else:
            content = f"""---
type: whatsapp_{item_type}
source: whatsapp
created: {datetime.now().isoformat()}
status: needs_action
---

# WhatsApp {item_type.title()} - Action Required

{data}

---
*Created by WhatsApp Watcher*
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
        self.logger.info("WHATSAPP WATCHER STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")
        self.logger.info(f"Dry run: {self.dry_run}")

        try:
            while True:
                try:
                    self.logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking WhatsApp...")

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
            self.logger.info("WHATSAPP WATCHER STOPPED (Ctrl+C)")
            self.logger.info("=" * 80)
            self.logger.info(f"Final stats: {self.stats}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='WhatsApp Watcher - Continuous Monitoring')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Path to Obsidian vault')
    parser.add_argument('--check-interval', type=int, default=60, help='Seconds between checks (default: 60)')
    parser.add_argument('--dry-run', action='store_true', help='Log actions but don\'t create files')

    args = parser.parse_args()

    watcher = WhatsAppWatcher(
        vault_path=args.vault,
        check_interval=args.check_interval,
        dry_run=args.dry_run
    )

    watcher.run()


if __name__ == '__main__':
    main()
