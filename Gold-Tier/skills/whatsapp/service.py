"""
WhatsApp Service - Core Business Logic

Handles all WhatsApp operations via Twilio API and Neon PostgreSQL.
No agent-related code — pure business logic only.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Try to import Twilio
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException, TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Import DB module from existing codebase
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from db_neon import NeonDatabase

load_dotenv()

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Core service for sending/receiving WhatsApp messages via Twilio."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        vault_path: str = "AI_Employee_Vault"
    ):
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_WHATSAPP_NUMBER')
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        if not self.account_sid:
            raise ValueError("TWILIO_ACCOUNT_SID not found")
        if not self.auth_token:
            raise ValueError("TWILIO_AUTH_TOKEN not found")
        if not self.from_number:
            raise ValueError("TWILIO_WHATSAPP_NUMBER not found")

        self.client = Client(self.account_sid, self.auth_token) if TWILIO_AVAILABLE else None
        self.db = NeonDatabase()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((TwilioRestException, ConnectionError, TimeoutError)),
        reraise=True
    )
    def send_message(self, target_number: str, message_text: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message via Twilio.

        Args:
            target_number: Recipient number (e.g., 'whatsapp:+923001234567')
            message_text: Message content

        Returns:
            Result dict with success, error, message_sid, database_id
        """
        result = {
            "success": False,
            "message_sid": None,
            "error": None,
            "database_id": None,
            "timestamp": datetime.utcnow().isoformat()
        }

        if not TWILIO_AVAILABLE or not self.client:
            error_msg = "Twilio package not installed or client not initialized"
            result["error"] = error_msg
            logger.error(error_msg)
            return result

        try:
            if not target_number.startswith('whatsapp:'):
                target_number = f"whatsapp:{target_number}"

            message = self.client.messages.create(
                body=message_text,
                from_=self.from_number,
                to=target_number
            )

            result["success"] = True
            result["message_sid"] = message.sid
            result["status"] = message.status

            # Log to database
            db_id = self.db.insert_outbound_message(
                recipient_number=target_number,
                message_body=message_text,
                twilio_sid=message.sid,
                status='sent',
                sender_number=self.from_number
            )
            result["database_id"] = db_id

            # Log to vault
            self._log_sent(target_number, message_text, message.sid, db_id)

            return result

        except TwilioRestException as e:
            error_msg = f"Twilio API error: {e}"
            result["error"] = error_msg
            logger.error(error_msg)
            self._log_error(error_msg, target_number, message_text)
            self.db.insert_outbound_message(
                recipient_number=target_number,
                message_body=message_text,
                status='failed'
            )
            return result

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            result["error"] = error_msg
            logger.error(error_msg)
            self._log_error(error_msg, target_number, message_text)
            return result

    def send_reply(self, original_message: Dict[str, Any], reply_text: str) -> Dict[str, Any]:
        """
        Reply to an original WhatsApp message.

        Args:
            original_message: Original message dict from Vault JSON
            reply_text: Reply content

        Returns:
            Result dict
        """
        sender = original_message.get('sender', {})
        target_number = sender.get('number', '')
        if not target_number:
            return {"success": False, "error": "Cannot extract sender number"}
        return self.send_message(target_number, reply_text)

    def sync_inbox(self, limit: int = 100) -> Dict[str, Any]:
        """
        Sync unread messages from Neon DB to Vault Inbox.

        Args:
            limit: Max messages to sync

        Returns:
            Dict with synced files list and stats
        """
        inbox_dir = self.vault_path / "Inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)

        messages = self.db.get_unread_inbound_messages(limit=limit)
        synced_files = []

        for msg in messages:
            formatted = self._format_message(msg)
            sender_clean = formatted['sender']['display']
            ts = datetime.fromisoformat(
                formatted['message']['timestamp'].replace('+00:00', '+00:00')
            ).strftime('%Y%m%d_%H%M%S')
            filename = f"wa_twilio_{msg['id']}_{sender_clean}_{ts}.json"
            filepath = inbox_dir / filename

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(formatted, f, indent=2, ensure_ascii=False)
                self.db.mark_message_as_processing(msg['id'])
                synced_files.append(str(filepath))
            except Exception as e:
                logger.error(f"Failed to save message {msg['id']} to Vault: {e}")

        return {
            "success": True,
            "synced_count": len(synced_files),
            "files": synced_files
        }

    def mark_done(self, database_id: int) -> bool:
        """Mark a message as done in the database."""
        return self.db.mark_message_as_done(database_id)

    def test_connection(self) -> bool:
        """Test Twilio API connection."""
        if not TWILIO_AVAILABLE or not self.client:
            return False
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            logger.info(f"Twilio connection test successful: {account.friendly_name}")
            return True
        except Exception as e:
            logger.error(f"Twilio connection test failed: {e}")
            return False

    def _format_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Format a DB message into a Vault-compatible JSON structure."""
        sender_clean = message['sender_number'].replace('whatsapp:', '').replace('+', '')
        return {
            "id": f"wa_twilio_{message['id']}",
            "database_id": message['id'],
            "type": "whatsapp",
            "source": "twilio",
            "direction": "inbound",
            "status": "processing",
            "sender": {"number": message['sender_number'], "display": sender_clean},
            "recipient": {"number": message.get('recipient_number', ''), "display": ''},
            "message": {
                "body": message['message_body'],
                "timestamp": message['timestamp'],
                "twilio_sid": message.get('twilio_sid', '')
            },
            "metadata": {
                "synced_at": datetime.utcnow().isoformat(),
                "original_status": message['status'],
                "error_message": message.get('error_message', '')
            },
            "ai_employee": {
                "requires_action": True,
                "action_type": "whatsapp_reply",
                "priority": "normal",
                "processed": False,
                "response_sent": False
            }
        }

    def _log_sent(self, target_number: str, message_text: str,
                  message_sid: str, database_id: Optional[int]):
        """Log successful message to Vault."""
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f"whatsapp_sent_{ts}.json"
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "whatsapp_sent",
            "target_number": target_number,
            "message_text": message_text,
            "message_sid": message_sid,
            "status": "sent",
            "database_id": database_id
        }
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log message to file: {e}")

    def _log_error(self, error_message: str, target_number: str, message_text: str):
        """Log error to Vault."""
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f"whatsapp_error_{ts}.json"
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "whatsapp_error",
            "target_number": target_number,
            "message_text": message_text,
            "error": error_message
        }
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log error to file: {e}")
