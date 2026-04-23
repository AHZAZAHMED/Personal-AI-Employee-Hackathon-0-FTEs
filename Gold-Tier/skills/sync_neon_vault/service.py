"""
Sync Neon to Vault Service - Core Business Logic

Syncs unread WhatsApp messages from Neon PostgreSQL database
to the AI Employee Vault Inbox as JSON files.

No agent-related code — pure business logic only.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from dotenv import load_dotenv
load_dotenv()

# Import Neon DB from scripts
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from db_neon import NeonDatabase

logger = logging.getLogger(__name__)


class NeonVaultSyncService:
    """Core Neon → Vault sync service."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.inbox = self.vault / "Inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.db = NeonDatabase()

    def format_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Format a DB message into Vault JSON structure."""
        sender_clean = msg["sender_number"].replace("whatsapp:", "").replace("+", "")
        return {
            "id": f"wa_twilio_{msg['id']}",
            "database_id": msg["id"],
            "type": "whatsapp",
            "source": "twilio",
            "direction": "inbound",
            "status": "processing",
            "sender": {"number": msg["sender_number"], "display": sender_clean},
            "recipient": {"number": msg.get("recipient_number", ""), "display": ""},
            "message": {
                "body": msg["message_body"],
                "timestamp": msg["timestamp"],
                "twilio_sid": msg.get("twilio_sid", "")
            },
            "metadata": {
                "synced_at": datetime.utcnow().isoformat(),
                "original_status": msg["status"],
                "error_message": msg.get("error_message", "")
            },
            "ai_employee": {
                "requires_action": True,
                "action_type": "whatsapp_reply",
                "priority": "normal",
                "processed": False,
                "response_sent": False
            }
        }

    def save_to_inbox(self, message_data: Dict[str, Any], message_id: int) -> Optional[Path]:
        """Save formatted message to Vault Inbox."""
        sender = message_data["sender"]["display"]
        ts = datetime.fromisoformat(
            message_data["message"]["timestamp"].replace("+00:00", "+00:00")
        ).strftime("%Y%m%d_%H%M%S")
        filename = f"wa_twilio_{message_id}_{sender}_{ts}.json"
        filepath = self.inbox / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(message_data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def run_sync(self, limit: int = 100) -> Dict[str, Any]:
        """
        Sync unread messages from Neon DB to Vault Inbox.

        Args:
            limit: Max messages to sync

        Returns:
            Dict with retrieved, synced, failed counts and synced_files list
        """
        stats = {"retrieved": 0, "synced": 0, "failed": 0, "skipped": 0, "synced_files": []}
        try:
            messages = self.db.get_unread_inbound_messages(limit=limit)
            stats["retrieved"] = len(messages)

            for msg in messages:
                try:
                    formatted = self.format_message(msg)
                    filepath = self.save_to_inbox(formatted, msg["id"])
                    if filepath:
                        if self.db.mark_message_as_processing(msg["id"]):
                            stats["synced"] += 1
                            stats["synced_files"].append(str(filepath))
                        else:
                            stats["failed"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Error syncing message {msg['id']}: {e}")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            stats["failed"] += stats["retrieved"]

        return stats

    def mark_done(self, database_id: int) -> Dict[str, Any]:
        """Mark a message as done in the database."""
        try:
            ok = self.db.mark_message_as_done(database_id)
            return {"success": ok}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_failed(self, database_id: int, error_message: str) -> Dict[str, Any]:
        """Mark a message as failed in the database."""
        try:
            ok = self.db.mark_message_as_failed(database_id, error_message)
            return {"success": ok}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        try:
            inbox_count = len(list(self.inbox.glob("wa_twilio_*.json")))
            unread = self.db.get_unread_inbound_messages(limit=1)
            return {
                "success": True,
                "vault_inbox_count": inbox_count,
                "database_unread_count": len(unread),
                "last_sync": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_connection(self) -> Dict[str, Any]:
        """Test Neon database connection."""
        try:
            ok = self.db.test_connection()
            return {"success": ok, "message": "Connected" if ok else "Connection failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
