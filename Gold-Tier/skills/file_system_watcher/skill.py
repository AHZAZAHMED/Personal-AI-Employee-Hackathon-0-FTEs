"""
File System Watcher Skill - Agent Entry Point

Scan folders for new files, create action tasks, and move
processed files to the vault inbox.
"""

from typing import Dict, Any, Optional
from .service import FileWatcherService


def scan_watch_folder(
    watch_folder: str,
    vault_path: str = "AI_Employee_Vault",
    move_processed: bool = True
) -> Dict[str, Any]:
    """
    Scan a watched folder for new files and create action tasks.

    Use this skill when:
    - Processing files dropped into a folder
    - Handling downloaded attachments
    - Monitoring export folders from other applications
    - Checking a drop folder for new work items

    For each new file found, creates a .md action file in Needs_Action/
    and optionally moves the original file to Vault Inbox/.

    Args:
        watch_folder: Path to the folder to monitor
        vault_path: Path to AI Employee Vault
        move_processed: Whether to move processed files to Vault Inbox/

    Returns:
        Dict with keys:
        - success (bool)
        - new_files (list): File info dicts
        - action_files (list): Paths of created action files
        - count (int): Number of new files found
        - error (str|None)

    Example:
        result = scan_watch_folder(watch_folder="C:/Users/me/Downloads/WorkDrop")
        print(f"New files: {result['count']}")
    """
    try:
        service = FileWatcherService(vault_path=vault_path)
        return service.scan_folder(watch_folder, move_processed=move_processed)
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_unprocessed_files(
    watch_folder: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    List files in a watch folder that haven't been processed yet.

    Args:
        watch_folder: Path to folder to check
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with list of unprocessed files
    """
    try:
        service = FileWatcherService(vault_path=vault_path)
        return service.list_unprocessed_files(watch_folder)
    except Exception as e:
        return {"success": False, "error": str(e)}
