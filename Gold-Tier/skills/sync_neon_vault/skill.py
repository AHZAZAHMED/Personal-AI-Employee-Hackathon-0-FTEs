"""
Sync Neon to Vault Skill - Agent Entry Point

Syncs unread WhatsApp messages from Neon PostgreSQL database
to the AI Employee Vault Inbox for processing.
"""

from typing import Dict, Any
from .service import NeonVaultSyncService


def sync_neon_to_vault(
    limit: int = 100,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Sync unread WhatsApp messages from Neon DB to Vault Inbox.

    Use this skill when:
    - Checking for new WhatsApp messages that arrived in the database
    - Bridging Twilio webhooks (stored in Neon DB) to the file-based AI Employee system
    - Preparing messages for AI processing

    For each synced message, creates a JSON file in Vault Inbox/
    and marks it as 'processing' in the database.

    Args:
        limit: Maximum number of messages to sync (default: 100)
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with keys:
        - success (bool)
        - retrieved (int): Messages retrieved from DB
        - synced (int): Messages successfully synced
        - failed (int): Failed syncs
        - synced_files (list): Paths of synced JSON files
        - error (str|None)

    Example:
        result = sync_neon_to_vault(limit=50)
        print(f"Synced: {result['synced']} files")
    """
    try:
        service = NeonVaultSyncService(vault_path=vault_path)
        return service.run_sync(limit=limit)
    except Exception as e:
        return {"success": False, "error": str(e)}


def sync_mark_done(
    database_id: int,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Mark a WhatsApp message as done in the database after processing.

    Args:
        database_id: The Neon DB message ID
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status
    """
    try:
        service = NeonVaultSyncService(vault_path=vault_path)
        return service.mark_done(database_id)
    except Exception as e:
        return {"success": False, "error": str(e)}


def sync_get_status(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Get current sync status (inbox count, DB unread count).

    Args:
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with sync statistics
    """
    try:
        service = NeonVaultSyncService(vault_path=vault_path)
        return service.get_status()
    except Exception as e:
        return {"success": False, "error": str(e)}


def sync_test_connection(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """Test Neon database connection."""
    try:
        service = NeonVaultSyncService(vault_path=vault_path)
        return service.test_connection()
    except Exception as e:
        return {"success": False, "error": str(e)}
