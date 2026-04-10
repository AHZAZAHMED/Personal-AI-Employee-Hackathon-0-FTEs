"""
Sync Neon Database to AI Employee Vault

Bridges the Neon PostgreSQL database with the file-based AI Employee architecture.
Converts unread inbound messages from the database into JSON files in the Vault Inbox.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

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


class NeonToVaultSync:
    """
    Synchronizes unread messages from Neon database to the AI Employee Vault.
    
    Usage:
        sync = NeonToVaultSync(vault_path="AI_Employee_Vault")
        sync.run()
    """
    
    def __init__(
        self,
        vault_path: str,
        db: Optional[NeonDatabase] = None
    ):
        """
        Initialize the sync process.
        
        Args:
            vault_path: Path to the AI Employee Vault
            db: Optional NeonDatabase instance (creates one if not provided)
        """
        self.vault_path = Path(vault_path)
        self.db = db or NeonDatabase()
        
        # Ensure vault directories exist
        self.inbox_dir = self.vault_path / "Inbox"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Vault path: {self.vault_path.absolute()}")
        logger.info(f"Inbox directory: {self.inbox_dir.absolute()}")
    
    def format_whatsapp_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a database message into a Vault-compatible JSON structure.
        
        Args:
            message: Message dictionary from database
            
        Returns:
            Formatted message dictionary
        """
        # Clean phone number for filename
        sender_clean = message['sender_number'].replace('whatsapp:', '').replace('+', '')
        timestamp = datetime.fromisoformat(
            message['timestamp'].replace('+00:00', '+00:00')
        )
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        return {
            "id": f"wa_twilio_{message['id']}",
            "database_id": message['id'],
            "type": "whatsapp",
            "source": "twilio",
            "direction": "inbound",
            "status": "processing",
            "sender": {
                "number": message['sender_number'],
                "display": sender_clean
            },
            "recipient": {
                "number": message.get('recipient_number', ''),
                "display": ''
            },
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
    
    def save_to_vault(
        self,
        message_data: Dict[str, Any],
        message_id: int
    ) -> Optional[Path]:
        """
        Save a formatted message to the Vault Inbox.
        
        Args:
            message_data: Formatted message dictionary
            message_id: Database message ID
            
        Returns:
            Path to saved file, or None if failed
        """
        # Generate filename
        sender_clean = message_data['sender']['display']
        timestamp = datetime.fromisoformat(
            message_data['message']['timestamp'].replace('+00:00', '+00:00')
        )
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        filename = f"wa_twilio_{message_id}_{sender_clean}_{timestamp_str}.json"
        filepath = self.inbox_dir / filename
        
        try:
            # Write JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved message to Vault: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save message to Vault: {e}")
            return None
    
    def run(self, limit: int = 100) -> Dict[str, int]:
        """
        Run the sync process.
        
        Args:
            limit: Maximum number of messages to sync
            
        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting Neon to Vault sync...")
        
        stats = {
            "retrieved": 0,
            "synced": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            # Get unread inbound messages from database
            messages = self.db.get_unread_inbound_messages(limit=limit)
            stats["retrieved"] = len(messages)
            
            logger.info(f"Retrieved {len(messages)} unread messages from database")
            
            if not messages:
                logger.info("No unread messages to sync")
                return stats
            
            # Process each message
            for message in messages:
                try:
                    # Format message for Vault
                    formatted = self.format_whatsapp_message(message)
                    
                    # Save to Vault
                    filepath = self.save_to_vault(formatted, message['id'])
                    
                    if filepath:
                        # Update database status to 'processing'
                        if self.db.mark_message_as_processing(message['id']):
                            stats["synced"] += 1
                            logger.debug(
                                f"Synced message {message['id']} to {filepath.name}"
                            )
                        else:
                            stats["failed"] += 1
                            logger.error(
                                f"Failed to update status for message {message['id']}"
                            )
                    else:
                        stats["failed"] += 1
                        logger.error(
                            f"Failed to save message {message['id']} to Vault"
                        )
                        
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(
                        f"Error processing message {message['id']}: {e}"
                    )
            
            logger.info(
                f"Sync complete: {stats['synced']} synced, "
                f"{stats['failed']} failed, {stats['skipped']} skipped"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Sync process failed: {e}")
            stats["failed"] = stats["retrieved"]
            return stats
    
    def mark_as_done(self, database_id: int) -> bool:
        """
        Mark a message as done in the database after AI processing.
        
        Args:
            database_id: The database message ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.db.mark_message_as_done(database_id)
    
    def mark_as_failed(
        self,
        database_id: int,
        error_message: str
    ) -> bool:
        """
        Mark a message as failed in the database.
        
        Args:
            database_id: The database message ID
            error_message: Error description
            
        Returns:
            True if successful, False otherwise
        """
        return self.db.mark_message_as_failed(database_id, error_message)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status.
        
        Returns:
            Dictionary with sync statistics
        """
        try:
            # Count files in Inbox
            inbox_count = len(list(self.inbox_dir.glob("wa_twilio_*.json")))
            
            # Get database stats
            unread_messages = self.db.get_unread_inbound_messages(limit=1)
            
            return {
                "vault_inbox_count": inbox_count,
                "database_unread_count": len(unread_messages),
                "last_sync": datetime.utcnow().isoformat(),
                "vault_path": str(self.vault_path.absolute()),
                "inbox_path": str(self.inbox_dir.absolute())
            }
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


def run_sync(
    vault_path: str = "AI_Employee_Vault",
    limit: int = 100,
    init_db: bool = False
) -> Dict[str, int]:
    """
    Convenience function to run the sync process.
    
    Args:
        vault_path: Path to the AI Employee Vault
        limit: Maximum number of messages to sync
        init_db: Initialize database schema before sync
        
    Returns:
        Sync statistics dictionary
    """
    # Initialize database if requested
    if init_db:
        db = NeonDatabase()
        if db.init_schema():
            logger.info("Database schema initialized")
        else:
            logger.warning("Database schema initialization failed")
    
    # Run sync
    sync = NeonToVaultSync(vault_path=vault_path)
    return sync.run(limit=limit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync Neon Database to AI Employee Vault"
    )
    parser.add_argument(
        "--vault",
        default="AI_Employee_Vault",
        help="Path to AI Employee Vault (default: AI_Employee_Vault)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum messages to sync (default: 100)"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database schema before sync"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show sync status and exit"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Run continuously with interval in seconds (default: 0 = run once)"
    )
    
    args = parser.parse_args()
    
    if args.status:
        # Show status
        sync = NeonToVaultSync(vault_path=args.vault)
        status = sync.get_sync_status()
        print(json.dumps(status, indent=2))
    elif args.interval > 0:
        # Run continuously
        logger.info(f"Running sync every {args.interval} seconds...")
        try:
            while True:
                run_sync(
                    vault_path=args.vault,
                    limit=args.limit,
                    init_db=args.init_db
                )
                import time
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Sync stopped by user")
    else:
        # Run once
        stats = run_sync(
            vault_path=args.vault,
            limit=args.limit,
            init_db=args.init_db
        )
        print(f"\nSync Statistics:")
        print(f"  Retrieved: {stats['retrieved']}")
        print(f"  Synced:    {stats['synced']}")
        print(f"  Failed:    {stats['failed']}")
        print(f"  Skipped:   {stats['skipped']}")
