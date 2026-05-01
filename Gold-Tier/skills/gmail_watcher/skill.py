"""
Gmail Watcher Skill - Agent Entry Point

Checks Gmail for unread messages, returns structured data,
and optionally creates action files in the vault.
"""

from typing import Dict, Any, List, Optional
from .service import GmailService


def gmail_check_unread(
    max_results: int = 10,
    vault_path: str = "AI_Employee_Vault",
    credentials_path: Optional[str] = None,
    create_action_files: bool = True
) -> Dict[str, Any]:
    """
    Check Gmail for new unread messages.

    Use this skill when:
    - You need to monitor the inbox for new emails
    - Triage incoming mail and create tasks
    - Check for urgent/high-priority emails

    Args:
        max_results: Maximum number of unread messages to retrieve (default: 10)
        vault_path: Path to AI Employee Vault
        credentials_path: Path to Gmail OAuth credentials.json
        create_action_files: Whether to create .md files in Needs_Action/

    Returns:
        Dict with keys:
        - success (bool): Whether the check succeeded
        - messages (list): List of unread email dicts
        - action_files (list): Paths of created action files (if create_action_files=True)
        - count (int): Number of new messages found
        - error (str|None): Error message if failed

    Example:
        result = gmail_check_unread(max_results=5)
        for msg in result["messages"]:
            print(f"From: {msg['from']}, Subject: {msg['subject']}")
    """
    try:
        service = GmailService(vault_path=vault_path, credentials_path=credentials_path)
        messages = service.get_unread_messages(max_results=max_results)

        action_files = []
        if create_action_files:
            for msg in messages:
                filepath = service.create_action_file(msg)
                if filepath:
                    action_files.append(str(filepath))

        return {
            "success": True,
            "messages": messages,
            "action_files": action_files,
            "count": len(messages),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "messages": [],
            "action_files": [],
            "count": 0,
            "error": str(e)
        }


def gmail_test_connection(
    vault_path: str = "AI_Employee_Vault",
    credentials_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test Gmail API connection.

    Returns:
        Dict with connection status and email address
    """
    try:
        service = GmailService(vault_path=vault_path, credentials_path=credentials_path)
        success = service.test_connection()
        return {
            "success": success,
            "message": "Gmail connected" if success else "Gmail connection failed"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def gmail_mark_processed(
    gmail_id: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Mark a Gmail message ID as processed so it won't be fetched again.

    Args:
        gmail_id: The Gmail message ID to mark
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status
    """
    try:
        service = GmailService(vault_path=vault_path)
        service.mark_processed(gmail_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
