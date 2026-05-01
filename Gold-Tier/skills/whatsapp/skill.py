"""
WhatsApp Skill - Agent Entry Point

Sends and receives WhatsApp messages via Twilio API.
This is the bridge between the AI agent and the WhatsApp service layer.
"""

from typing import Dict, Any
from .service import WhatsAppService


def whatsapp_send_message(
    target_number: str,
    message_text: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Send a WhatsApp message via Twilio API.

    Use this skill when:
    - You need to send a WhatsApp message to a phone number
    - Replying to a customer WhatsApp inquiry
    - Notifying someone via WhatsApp about a status update

    Args:
        target_number: Recipient's WhatsApp number with 'whatsapp:' prefix
                       (e.g., 'whatsapp:+923001234567')
        message_text: The message content to send
        vault_path: Path to AI Employee Vault for logging

    Returns:
        Dict with keys:
        - success (bool): Whether the message was sent
        - message_sid (str|None): Twilio message SID
        - database_id (int|None): Neon DB record ID
        - error (str|None): Error message if failed
        - timestamp (str): ISO timestamp

    Example:
        result = whatsapp_send_message(
            target_number="whatsapp:+923001234567",
            message_text="Hello! Your order has been shipped."
        )
        if result["success"]:
            print(f"Sent! SID: {result['message_sid']}")
    """
    try:
        service = WhatsAppService(vault_path=vault_path)
        result = service.send_message(target_number, message_text)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message_sid": None,
            "database_id": None,
            "timestamp": None
        }


def whatsapp_sync_inbox(
    vault_path: str = "AI_Employee_Vault",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Sync unread WhatsApp messages from Neon DB to Vault Inbox.

    Use this skill when:
    - Checking for new WhatsApp messages that arrived in the database
    - Bridging the gap between Twilio webhooks and the file-based AI Employee system

    Args:
        vault_path: Path to AI Employee Vault
        limit: Maximum number of messages to sync

    Returns:
        Dict with keys:
        - success (bool): Whether sync was successful
        - synced_count (int): Number of messages synced
        - files (list): List of synced file paths
    """
    try:
        service = WhatsAppService(vault_path=vault_path)
        return service.sync_inbox(limit=limit)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "synced_count": 0,
            "files": []
        }


def whatsapp_mark_done(
    database_id: int,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Mark a WhatsApp message as done in the database after processing.

    Args:
        database_id: The Neon DB message ID to mark as done
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status
    """
    try:
        service = WhatsAppService(vault_path=vault_path)
        success = service.mark_done(database_id)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}


def whatsapp_test_connection(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Test the Twilio API connection.

    Returns:
        Dict with connection status
    """
    try:
        service = WhatsAppService(vault_path=vault_path)
        success = service.test_connection()
        return {"success": success, "message": "Connection OK" if success else "Connection failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}
