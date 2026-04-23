"""
File System Watcher Service - Core Business Logic

Monitors a folder for new files, creates action tasks in the vault,
and moves processed files to the inbox.

No agent-related code — pure business logic only.
"""

import os
import json
import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FileWatcherService:
    """Core file system watching service."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.needs_action = self.vault / "Needs_Action"
        self.inbox = self.vault / "Inbox"
        self.logs = self.vault / "Logs"
        for d in [self.needs_action, self.inbox, self.logs]:
            d.mkdir(parents=True, exist_ok=True)

        self.processed_hashes_file = self.logs / "processed_files.json"
        self.processed_hashes = self._load_processed()

    def _load_processed(self) -> set:
        if self.processed_hashes_file.exists():
            try:
                with open(self.processed_hashes_file) as f:
                    return set(json.load(f).get("hashes", []))
            except Exception:
                pass
        return set()

    def _save_processed(self):
        try:
            with open(self.processed_hashes_file, "w") as f:
                json.dump({"last_updated": datetime.now().isoformat(), "hashes": list(self.processed_hashes)}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed hashes: {e}")

    def _file_hash(self, filepath: Path) -> str:
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def scan_folder(self, watch_folder: str, move_processed: bool = True) -> Dict[str, Any]:
        """
        Scan a folder for new files, create action files, and optionally move them.

        Args:
            watch_folder: Path to folder to monitor
            move_processed: Whether to move files to vault Inbox/

        Returns:
            Dict with new_files list, action_files list, count
        """
        watch = Path(watch_folder)
        watch.mkdir(parents=True, exist_ok=True)

        new_files = []
        action_files = []

        try:
            for fp in watch.iterdir():
                if fp.is_dir() or fp.name.startswith(".") or fp.suffix.lower() in [".lock"]:
                    continue

                file_hash = self._file_hash(fp)
                if file_hash in self.processed_hashes:
                    continue

                stat = fp.stat()
                file_info = {
                    "filename": fp.name,
                    "filepath": str(fp),
                    "size": stat.st_size,
                    "size_human": self._human_size(stat.st_size),
                    "extension": fp.suffix.lower(),
                    "hash": file_hash,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                new_files.append(file_info)

                # Create action file
                action_path = self._create_action_file(file_info)
                if action_path:
                    action_files.append(str(action_path))

                # Move to inbox
                if move_processed:
                    try:
                        dest = self.inbox / fp.name
                        if dest.exists():
                            dest = self.inbox / f"{fp.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{fp.suffix}"
                        shutil.move(str(fp), str(dest))
                    except Exception as e:
                        logger.warning(f"Could not move file: {e}")

                self.processed_hashes.add(file_hash)

            self._save_processed()

        except Exception as e:
            logger.error(f"Error scanning {watch_folder}: {e}")
            return {"success": False, "error": str(e)}

        return {"success": True, "new_files": new_files, "action_files": action_files, "count": len(new_files)}

    def _create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """Create an action file in Needs_Action/."""
        unique_id = Path(item["filename"]).stem.replace(" ", "_").replace("-", "_")
        ext = item["extension"]

        suggested_actions = ["Review file content", "Determine required action", "File or archive after processing"]
        if ext in [".pdf", ".doc", ".docx"]:
            suggested_actions.insert(0, "Extract key information from document")
        elif ext in [".xls", ".xlsx", ".csv"]:
            suggested_actions.insert(0, "Analyze spreadsheet data")
        elif ext in [".jpg", ".jpeg", ".png", ".gif"]:
            suggested_actions.insert(0, "Review image content")
            suggested_actions.insert(1, "Extract text if applicable (OCR)")

        actions_md = "\n".join(f"- [ ] {a}" for a in suggested_actions)

        content = f"""---
type: file_drop
original_name: {item['filename']}
original_path: {item['filepath']}
size_bytes: {item['size']}
size_human: {item['size_human']}
extension: {item['extension']}
file_hash: {item['hash']}
priority: normal
status: pending
---

# File Drop

**File:** `{item['filename']}` ({item['size_human']})
**Extension:** {item['extension']}
**Received:** {item.get('modified', 'Unknown')}

## Suggested Actions

{actions_md}

---
*Detected by File System Watcher*
"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FILE_{unique_id}_{ts}.md"
        filepath = self.needs_action / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def _human_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def list_unprocessed_files(self, watch_folder: str) -> Dict[str, Any]:
        """List files in watch folder that haven't been processed yet."""
        watch = Path(watch_folder)
        if not watch.exists():
            return {"success": False, "error": f"Folder not found: {watch_folder}"}

        files = []
        for fp in watch.iterdir():
            if fp.is_dir() or fp.name.startswith("."):
                continue
            file_hash = self._file_hash(fp)
            if file_hash not in self.processed_hashes:
                stat = fp.stat()
                files.append({"filename": fp.name, "size": stat.st_size,
                              "size_human": self._human_size(stat.st_size),
                              "extension": fp.suffix.lower()})
        return {"success": True, "files": files, "count": len(files)}
