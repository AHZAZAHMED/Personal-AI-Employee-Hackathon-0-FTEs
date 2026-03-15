"""
File System Watcher for AI Employee

Monitors a drop folder for new files and creates action files in the vault.
Useful for:
- Processing downloaded attachments
- Handling manually dropped files
- Monitoring export folders from other applications
"""

import hashlib
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from base_watcher import BaseWatcher


class FileSystemWatcher(BaseWatcher):
    """
    Watches a folder for new files and creates action files in the vault.
    """
    
    def __init__(self, vault_path: str, watch_folder: str, 
                 check_interval: int = 30, dry_run: bool = False,
                 move_processed: bool = True):
        """
        Initialize the file system watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            watch_folder: Path to folder to monitor for new files
            check_interval: Seconds between checks (default: 30)
            dry_run: If True, log actions but don't create files
            move_processed: If True, move processed files to vault/Inbox
        """
        super().__init__(vault_path, check_interval, dry_run)

        self.watch_folder = Path(watch_folder)
        self.move_processed = move_processed

        # Create watch folder if it doesn't exist
        self.watch_folder.mkdir(parents=True, exist_ok=True)

        # Track processed files by hash to avoid duplicates
        # Load previously processed hashes from file
        self.processed_hashes_file = self.logs_dir / 'processed_files.json'
        self.processed_hashes = self._load_processed_hashes()

        # Supported file extensions (None = all files)
        self.supported_extensions = None  # ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx']
        
        self.logger.info(f"Watching folder: {self.watch_folder}")

    def _load_processed_hashes(self) -> set:
        """Load previously processed file hashes from disk."""
        if self.processed_hashes_file.exists():
            try:
                with open(self.processed_hashes_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('hashes', []))
            except Exception as e:
                self.logger.warning(f"Could not load processed hashes: {e}")
        return set()

    def _save_processed_hashes(self):
        """Save processed file hashes to disk."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'hashes': list(self.processed_hashes)
            }
            with open(self.processed_hashes_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save processed hashes: {e}")

    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of file for duplicate detection."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _should_process_file(self, filepath: Path) -> bool:
        """
        Check if file should be processed.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file should be processed
        """
        # Skip hidden files
        if filepath.name.startswith('.'):
            return False
        
        # Skip directories
        if filepath.is_dir():
            return False
        
        # Check extension if filter is set
        if self.supported_extensions:
            if filepath.suffix.lower() not in self.supported_extensions:
                return False
        
        # Check if already processed
        file_hash = self._get_file_hash(filepath)
        if file_hash in self.processed_hashes:
            return False
        
        return True
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check the watch folder for new files.
        
        Returns:
            List of file information dictionaries
        """
        new_files = []
        
        try:
            for filepath in self.watch_folder.iterdir():
                if self._should_process_file(filepath):
                    file_stat = filepath.stat()
                    
                    file_info = {
                        'filename': filepath.name,
                        'filepath': str(filepath),
                        'size': file_stat.st_size,
                        'modified': file_stat.st_mtime,
                        'extension': filepath.suffix.lower(),
                        'hash': self._get_file_hash(filepath)
                    }
                    
                    new_files.append(file_info)
                    self.processed_hashes.add(file_info['hash'])
                    
            # Save processed hashes after each scan
            self._save_processed_hashes()

        except Exception as e:
            self.logger.error(f"Error scanning watch folder: {e}")

        return new_files
    
    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create an action file for the dropped file.
        
        Args:
            item: File information dictionary
            
        Returns:
            Path to created action file, or None if dry_run
        """
        # Generate unique ID from filename
        unique_id = Path(item['filename']).stem.replace(' ', '_').replace('-', '_')
        
        # Create suggested actions based on file type
        suggested_actions = [
            "Review file content",
            "Determine required action",
            "File or archive after processing"
        ]
        
        # Add type-specific actions
        if item['extension'] in ['.pdf', '.doc', '.docx']:
            suggested_actions.insert(0, "Extract key information from document")
        elif item['extension'] in ['.xls', '.xlsx', '.csv']:
            suggested_actions.insert(0, "Analyze spreadsheet data")
        elif item['extension'] in ['.jpg', '.jpeg', '.png', '.gif']:
            suggested_actions.insert(0, "Review image content")
            suggested_actions.insert(1, "Extract text if applicable (OCR)")
        
        # Create markdown content
        content = self._create_markdown_content(
            item_type='file_drop',
            item_data={
                'original_name': item['filename'],
                'original_path': item['filepath'],
                'size_bytes': item['size'],
                'size_human': self._human_readable_size(item['size']),
                'extension': item['extension'],
                'file_hash': item['hash'],
                'content': f"*File: `{item['filename']}` ({self._human_readable_size(item['size'])})*"
            },
            suggested_actions=suggested_actions
        )
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create action file for: {item['filename']}")
            return None
        
        # Generate filename and write file
        filename = self._generate_filename('FILE', unique_id)
        filepath = self.needs_action / filename
        filepath.write_text(content)
        
        # Move original file to vault inbox if configured
        if self.move_processed:
            try:
                source = Path(item['filepath'])
                dest = self.inbox / item['filename']
                
                # Handle duplicate filenames
                if dest.exists():
                    dest = self.inbox / f"{source.stem}_{self._timestamp()}{source.suffix}"
                
                shutil.move(str(source), str(dest))
                self.logger.info(f"Moved file to vault inbox: {dest.name}")
                
            except Exception as e:
                self.logger.warning(f"Could not move file to inbox: {e}")
        
        # Log the action
        self.log_action('file_processed', {
            'filename': item['filename'],
            'size': item['size'],
            'action_file': filename
        })
        
        return filepath
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def _timestamp(self) -> str:
        """Generate timestamp string for filename."""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d_%H%M%S')


def main():
    """Run the file system watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='File System Watcher for AI Employee')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--watch', required=True, help='Folder to watch for new files')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Log actions without creating files')
    parser.add_argument('--no-move', action='store_true', help="Don't move processed files to vault")
    
    args = parser.parse_args()
    
    watcher = FileSystemWatcher(
        vault_path=args.vault,
        watch_folder=args.watch,
        check_interval=args.interval,
        dry_run=args.dry_run,
        move_processed=not args.no_move
    )
    
    watcher.run()


if __name__ == '__main__':
    main()
