"""
WhatsApp Responder - Twilio API Client

Sends WhatsApp messages via Twilio API and logs to Neon database.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_neon import NeonDatabase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import Twilio
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException, TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio package not installed. Install with: pip install twilio")


class WhatsAppResponder:
    """
    Send WhatsApp messages via Twilio API.
    
    Usage:
        responder = WhatsAppResponder()
        result = responder.send_message(
            target_number="whatsapp:+1234567890",
            message_text="Hello from AI Employee!"
        )
    """
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        db: Optional[NeonDatabase] = None
    ):
        """
        Initialize WhatsApp Responder.
        
        Args:
            account_sid: Twilio Account SID (or use TWILIO_ACCOUNT_SID env var)
            auth_token: Twilio Auth Token (or use TWILIO_AUTH_TOKEN env var)
            from_number: Twilio WhatsApp number (or use TWILIO_WHATSAPP_NUMBER env var)
            db: Optional NeonDatabase instance
        """
        # Get credentials from parameters or environment
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        # Validate credentials
        if not self.account_sid:
            raise ValueError(
                "TWILIO_ACCOUNT_SID not found. Set it in .env or pass as parameter."
            )
        if not self.auth_token:
            raise ValueError(
                "TWILIO_AUTH_TOKEN not found. Set it in .env or pass as parameter."
            )
        if not self.from_number:
            raise ValueError(
                "TWILIO_WHATSAPP_NUMBER not found. Set it in .env or pass as parameter."
            )
        
        # Initialize Twilio client
        if TWILIO_AVAILABLE:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
        
        # Initialize database
        self.db = db or NeonDatabase()
        
        # Vault paths for logging
        self.vault_path = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"WhatsApp Responder initialized")
        logger.info(f"From number: {self.from_number}")
    
    def send_message(
        self,
        target_number: str,
        message_text: str,
        log_to_vault: bool = True
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message.
        
        Args:
            target_number: Recipient's WhatsApp number (e.g., 'whatsapp:+1234567890')
            message_text: Message content
            log_to_vault: Whether to log to Vault (default: True)
            
        Returns:
            Dictionary with result status and details
        """
        result = {
            "success": False,
            "message_sid": None,
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check if Twilio is available
        if not TWILIO_AVAILABLE:
            error_msg = "Twilio package not installed"
            result["error"] = error_msg
            logger.error(error_msg)
            self._log_error(error_msg, target_number, message_text)
            return result
        
        # Check if client is initialized
        if not self.client:
            error_msg = "Twilio client not initialized"
            result["error"] = error_msg
            logger.error(error_msg)
            self._log_error(error_msg, target_number, message_text)
            return result
        
        try:
            # Ensure target number has 'whatsapp:' prefix
            if not target_number.startswith('whatsapp:'):
                target_number = f"whatsapp:{target_number}"
            
            # Send message via Twilio
            logger.info(f"Sending WhatsApp message to: {target_number}")
            logger.debug(f"Message: {message_text[:100]}...")
            
            message = self.client.messages.create(
                body=message_text,
                from_=self.from_number,
                to=target_number
            )
            
            result["success"] = True
            result["message_sid"] = message.sid
            result["status"] = message.status
            
            logger.info(f"Message sent successfully! SID: {message.sid}")
            
            # Log to database
            db_message_id = self.db.insert_outbound_message(
                recipient_number=target_number,
                message_body=message_text,
                twilio_sid=message.sid,
                status='sent',
                sender_number=self.from_number
            )
            result["database_id"] = db_message_id
            
            # Log to Vault
            if log_to_vault:
                self._log_to_vault(
                    target_number=target_number,
                    message_text=message_text,
                    message_sid=message.sid,
                    status='sent',
                    database_id=db_message_id
                )
            
            return result
            
        except TwilioRestException as e:
            error_msg = f"Twilio API error: {e}"
            result["error"] = error_msg
            logger.error(error_msg)
            self._log_error(error_msg, target_number, message_text)
            
            # Log failure to database
            self.db.insert_outbound_message(
                recipient_number=target_number,
                message_body=message_text,
                status='failed'
            )
            
            return result
            
        except TwilioException as e:
            error_msg = f"Twilio error: {e}"
            result["error"] = error_msg
            logger.error(error_msg)
            self._log_error(error_msg, target_number, message_text)
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            result["error"] = error_msg
            logger.error(error_msg)
            self._log_error(error_msg, target_number, message_text)
            
            return result
    
    def _log_error(
        self,
        error_message: str,
        target_number: str,
        message_text: str
    ):
        """
        Log error to Vault Logs directory.
        
        Args:
            error_message: Error description
            target_number: Target WhatsApp number
            message_text: Original message text
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f"whatsapp_error_{timestamp}.json"
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "whatsapp_error",
            "target_number": target_number,
            "message_text": message_text,
            "error": error_message
        }
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(log_data, f, indent=2)
            logger.debug(f"Error logged to: {log_file}")
        except Exception as e:
            logger.error(f"Failed to log error to file: {e}")
    
    def _log_to_vault(
        self,
        target_number: str,
        message_text: str,
        message_sid: str,
        status: str,
        database_id: Optional[int] = None
    ):
        """
        Log successful message to Vault.
        
        Args:
            target_number: Target WhatsApp number
            message_text: Message content
            message_sid: Twilio message SID
            status: Message status
            database_id: Database record ID
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f"whatsapp_sent_{timestamp}.json"
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "whatsapp_sent",
            "target_number": target_number,
            "message_text": message_text,
            "message_sid": message_sid,
            "status": status,
            "database_id": database_id
        }
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(log_data, f, indent=2)
            logger.debug(f"Message logged to: {log_file}")
        except Exception as e:
            logger.error(f"Failed to log message to file: {e}")
    
    def send_reply(
        self,
        original_message: Dict[str, Any],
        reply_text: str,
        log_to_vault: bool = True
    ) -> Dict[str, Any]:
        """
        Send a reply to an original message.
        
        Args:
            original_message: Original message dictionary (from Vault JSON)
            reply_text: Reply message content
            log_to_vault: Whether to log to Vault
            
        Returns:
            Dictionary with result status
        """
        # Extract sender number from original message
        sender = original_message.get('sender', {})
        target_number = sender.get('number', '')
        
        if not target_number:
            logger.error("Cannot extract sender number from original message")
            return {
                "success": False,
                "error": "Cannot extract sender number"
            }
        
        # Send the reply
        return self.send_message(
            target_number=target_number,
            message_text=reply_text,
            log_to_vault=log_to_vault
        )
    
    def test_connection(self) -> bool:
        """
        Test Twilio API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if not TWILIO_AVAILABLE:
            logger.error("Twilio package not installed")
            return False
        
        try:
            # Make a simple API call to verify credentials
            account = self.client.api.accounts(self.account_sid).fetch()
            logger.info(f"Twilio connection test successful! Account: {account.friendly_name}")
            return True
        except Exception as e:
            logger.error(f"Twilio connection test failed: {e}")
            return False


def send_whatsapp_message(
    target_number: str,
    message_text: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Convenience function to send a WhatsApp message.
    
    Args:
        target_number: Recipient's WhatsApp number
        message_text: Message content
        vault_path: Path to AI Employee Vault
        
    Returns:
        Dictionary with result status
    """
    os.environ['VAULT_PATH'] = vault_path
    responder = WhatsAppResponder()
    return responder.send_message(target_number, message_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WhatsApp Responder - Send messages via Twilio"
    )
    parser.add_argument(
        "--to",
        required=True,
        help="Target WhatsApp number (e.g., whatsapp:+1234567890)"
    )
    parser.add_argument(
        "--message",
        required=True,
        help="Message text to send"
    )
    parser.add_argument(
        "--vault",
        default="AI_Employee_Vault",
        help="Path to AI Employee Vault (default: AI_Employee_Vault)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test Twilio connection and exit"
    )
    
    args = parser.parse_args()
    
    # Set vault path
    os.environ['VAULT_PATH'] = args.vault
    
    if args.test:
        # Test connection
        responder = WhatsAppResponder()
        if responder.test_connection():
            print("✓ Twilio connection successful!")
        else:
            print("✗ Twilio connection failed!")
    else:
        # Send message
        responder = WhatsAppResponder()
        result = responder.send_message(
            target_number=args.to,
            message_text=args.message
        )
        
        if result["success"]:
            print(f"✓ Message sent successfully!")
            print(f"  SID: {result['message_sid']}")
            print(f"  Status: {result['status']}")
        else:
            print(f"✗ Failed to send message!")
            print(f"  Error: {result['error']}")
