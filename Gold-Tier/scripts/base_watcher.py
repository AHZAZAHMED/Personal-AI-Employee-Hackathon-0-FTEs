"""
Base Watcher Class for AI Employee

All watcher scripts (Gmail, File System, etc.) should inherit from this class.
Provides common functionality for monitoring, logging, and creating action files.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    
    Watchers monitor external sources and create action files in the vault's
    /Needs_Action folder when new items are detected.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60, dry_run: bool = False):
        """
        Initialize the watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
            dry_run: If True, log actions but don't create files
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs_dir = self.vault_path / 'Logs'
        self.check_interval = check_interval
        self.dry_run = dry_run

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Heartbeat directory for watchdog monitoring
        self.heartbeat_dir = self.logs_dir / 'heartbeats'
        self.heartbeat_dir.mkdir(parents=True, exist_ok=True)
        self.heartbeat_file = self.heartbeat_dir / f'{self.__class__.__name__}.heartbeat'

        # Set up logging
        self._setup_logging()

        # Track processed items to avoid duplicates
        self.processed_ids: set = set()

        # Statistics
        self.stats = {
            'items_processed': 0,
            'files_created': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def _setup_logging(self):
        """Configure logging for this watcher."""
        log_file = self.logs_dir / f'watcher_{self.__class__.__name__}_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check the external source for new items.
        
        Returns:
            List of dictionaries containing item data to process
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create an action file in /Needs_Action for the given item.
        
        Args:
            item: Dictionary containing item data
            
        Returns:
            Path to created file, or None if dry_run
        """
        pass
    
    def _generate_filename(self, prefix: str, unique_id: str) -> str:
        """
        Generate a unique filename for an action file.

        Args:
            prefix: File type prefix (e.g., 'EMAIL', 'FILE')
            unique_id: Unique identifier for the item

        Returns:
            Filename string
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{unique_id}_{timestamp}.md"
    
    def _create_markdown_content(self, item_type: str, item_data: Dict[str, Any],
                                  suggested_actions: List[str]) -> str:
        """
        Create standardized markdown content for an action file.

        Args:
            item_type: Type of item (email, file, etc.)
            item_data: Dictionary of item metadata
            suggested_actions: List of suggested action checkboxes

        Returns:
            Formatted markdown string
        """
        # Build YAML frontmatter
        frontmatter = [
            "---",
            f"type: {item_type}",
            f"created: {datetime.now().isoformat()}",
            "status: pending",
            "priority: normal",
        ]
        
        # Add all item data as frontmatter
        for key, value in item_data.items():
            if isinstance(value, (list, dict)):
                import json
                frontmatter.append(f"{key}: {json.dumps(value)}")
            else:
                frontmatter.append(f"{key}: {value}")
        
        frontmatter.append("---")
        
        # Build content
        content = []
        content.append("")
        content.append("## Item Content")
        content.append("")
        
        if 'content' in item_data:
            content.append(item_data['content'])
        elif 'body' in item_data:
            content.append(item_data['body'])
        elif 'message' in item_data:
            content.append(item_data['message'])
        else:
            content.append("*No content available*")
        
        content.append("")
        content.append("## Suggested Actions")
        content.append("")
        
        for action in suggested_actions:
            content.append(f"- [ ] {action}")
        
        content.append("")
        content.append("---")
        content.append("*Created by AI Employee Watcher v0.1.0*")
        
        return "\n".join(frontmatter + content)
    
    def log_action(self, action_type: str, details: Dict[str, Any]):
        """
        Log an action to the vault's log system.

        Args:
            action_type: Type of action (created, skipped, error, etc.)
            details: Dictionary of action details
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'watcher': self.__class__.__name__,
            'action_type': action_type,
            **details
        }

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would log: {log_entry}")
        else:
            # Append to daily log file
            log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            with open(log_file, 'a') as f:
                import json
                f.write(json.dumps(log_entry) + '\n')

    def _write_heartbeat(self):
        """
        Write heartbeat file for watchdog monitoring.

        The watchdog checks these files to ensure watchers are still running.
        """
        try:
            self.heartbeat_file.write_text(datetime.now().isoformat())
        except Exception as e:
            self.logger.warning(f"Failed to write heartbeat: {e}")
    
    def run(self):
        """
        Main run loop for the watcher.
        
        Continuously checks for updates and creates action files.
        Runs until interrupted (Ctrl+C).
        """
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Dry run: {self.dry_run}")
        
        try:
            while True:
                try:
                    # Write heartbeat for watchdog monitoring
                    self._write_heartbeat()

                    # Check for new items
                    items = self.check_for_updates()

                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")

                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                if filepath:
                                    self.stats['files_created'] += 1
                                    self.logger.info(f"Created action file: {filepath.name}")
                                else:
                                    self.logger.info(f"[DRY RUN] Would create action file")

                                self.stats['items_processed'] += 1

                            except Exception as e:
                                self.logger.error(f"Error creating action file: {e}")
                                self.stats['errors'] += 1
                                self.log_action('error', {'item': str(item), 'error': str(e)})

                    # Wait before next check
                    time.sleep(self.check_interval)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    self.logger.error(f"Error in check loop: {e}")
                    self.stats['errors'] += 1
                    time.sleep(self.check_interval)
                    
        except KeyboardInterrupt:
            self.logger.info(f"Watcher stopped by user")
            self._print_stats()
    
    def _print_stats(self):
        """Print statistics summary."""
        runtime = datetime.now() - self.stats['start_time']
        self.logger.info("=" * 50)
        self.logger.info(f"Watcher Statistics:")
        self.logger.info(f"  Runtime: {runtime}")
        self.logger.info(f"  Items processed: {self.stats['items_processed']}")
        self.logger.info(f"  Files created: {self.stats['files_created']}")
        self.logger.info(f"  Errors: {self.stats['errors']}")
        self.logger.info("=" * 50)
    
    def run_once(self) -> int:
        """
        Run a single check cycle (useful for testing).

        Returns:
            Number of items processed
        """
        items = self.check_for_updates()
        for item in items:
            self.create_action_file(item)
        
        # Save processed hashes if this watcher supports it
        if hasattr(self, '_save_processed_hashes'):
            self._save_processed_hashes()
            
        return len(items)
