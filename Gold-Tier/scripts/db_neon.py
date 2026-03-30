"""
Neon PostgreSQL Database Connection Module

Handles all database operations for WhatsApp integration using Neon serverless PostgreSQL.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NeonDatabase:
    """
    Database connection and operations for Neon PostgreSQL.
    
    Usage:
        db = NeonDatabase()
        db.init_schema()
        messages = db.get_unread_inbound_messages()
        db.insert_message(...)
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize Neon database connection.
        
        Args:
            connection_string: Neon database connection string.
                              If None, uses NEON_DATABASE_URL from environment.
        """
        self.connection_string = connection_string or os.getenv('NEON_DATABASE_URL')
        
        if not self.connection_string:
            raise ValueError(
                "NEON_DATABASE_URL not found. Please set it in your .env file or "
                "pass it as a parameter."
            )
        
        self._connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            yield conn
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """Context manager for database cursors."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
                else:
                    conn.rollback()
            except Exception as e:
                conn.rollback()
                raise e
    
    def init_schema(self) -> bool:
        """
        Initialize the database schema for WhatsApp messages.
        
        Returns:
            True if successful, False otherwise.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS whatsapp_messages (
            id SERIAL PRIMARY KEY,
            sender_number VARCHAR(20) NOT NULL,
            message_body TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'unread',
            direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
            recipient_number VARCHAR(20),
            twilio_sid VARCHAR(100),
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_whatsapp_status ON whatsapp_messages(status);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_direction ON whatsapp_messages(direction);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_timestamp ON whatsapp_messages(timestamp);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_sender ON whatsapp_messages(sender_number);
        """
        
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute(create_table_sql)
            logger.info("Database schema initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            return False
    
    def insert_inbound_message(
        self,
        sender_number: str,
        message_body: str,
        twilio_sid: Optional[str] = None
    ) -> Optional[int]:
        """
        Insert an inbound WhatsApp message.
        
        Args:
            sender_number: Sender's WhatsApp number (e.g., 'whatsapp:+1234567890')
            message_body: The message text
            twilio_sid: Twilio message SID
            
        Returns:
            The ID of the inserted message, or None if failed.
        """
        insert_sql = """
        INSERT INTO whatsapp_messages 
        (sender_number, message_body, direction, status, twilio_sid)
        VALUES (%s, %s, 'inbound', 'unread', %s)
        RETURNING id
        """
        
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute(insert_sql, (sender_number, message_body, twilio_sid))
                message_id = cursor.fetchone()['id']
            logger.info(f"Inserted inbound message ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to insert inbound message: {e}")
            return None
    
    def insert_outbound_message(
        self,
        recipient_number: str,
        message_body: str,
        twilio_sid: Optional[str] = None,
        status: str = 'sent'
    ) -> Optional[int]:
        """
        Insert an outbound WhatsApp message.
        
        Args:
            recipient_number: Recipient's WhatsApp number
            message_body: The message text
            twilio_sid: Twilio message SID
            status: Message status ('sent', 'delivered', 'failed')
            
        Returns:
            The ID of the inserted message, or None if failed.
        """
        insert_sql = """
        INSERT INTO whatsapp_messages 
        (sender_number, message_body, direction, status, recipient_number, twilio_sid)
        VALUES (%s, %s, 'outbound', %s, %s, %s)
        RETURNING id
        """
        
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute(
                    insert_sql, 
                    (recipient_number, message_body, status, recipient_number, twilio_sid)
                )
                message_id = cursor.fetchone()['id']
            logger.info(f"Inserted outbound message ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to insert outbound message: {e}")
            return None
    
    def get_unread_inbound_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all unread inbound messages.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries.
        """
        select_sql = """
        SELECT * FROM whatsapp_messages
        WHERE direction = 'inbound' AND status = 'unread'
        ORDER BY timestamp ASC
        LIMIT %s
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(select_sql, (limit,))
                messages = list(cursor.fetchall())
            logger.info(f"Retrieved {len(messages)} unread inbound messages")
            return [dict(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Failed to get unread messages: {e}")
            return []
    
    def update_message_status(self, message_id: int, status: str) -> bool:
        """
        Update the status of a message.
        
        Args:
            message_id: The message ID
            status: New status value
            
        Returns:
            True if successful, False otherwise.
        """
        update_sql = """
        UPDATE whatsapp_messages
        SET status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute(update_sql, (status, message_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update message status: {e}")
            return False
    
    def mark_message_as_processing(self, message_id: int) -> bool:
        """
        Mark a message as being processed.
        
        Args:
            message_id: The message ID
            
        Returns:
            True if successful, False otherwise.
        """
        return self.update_message_status(message_id, 'processing')
    
    def mark_message_as_done(self, message_id: int) -> bool:
        """
        Mark a message as processed/done.
        
        Args:
            message_id: The message ID
            
        Returns:
            True if successful, False otherwise.
        """
        return self.update_message_status(message_id, 'done')
    
    def mark_message_as_failed(self, message_id: int, error_message: str) -> bool:
        """
        Mark a message as failed with an error message.
        
        Args:
            message_id: The message ID
            error_message: The error description
            
        Returns:
            True if successful, False otherwise.
        """
        update_sql = """
        UPDATE whatsapp_messages
        SET status = 'failed', error_message = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute(update_sql, (error_message, message_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to mark message as failed: {e}")
            return False
    
    def get_message_by_id(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: The message ID
            
        Returns:
            Message dictionary or None if not found.
        """
        select_sql = """
        SELECT * FROM whatsapp_messages WHERE id = %s
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(select_sql, (message_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get message by ID: {e}")
            return None
    
    def get_recent_messages(
        self,
        limit: int = 50,
        direction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages with optional direction filter.
        
        Args:
            limit: Maximum number of messages
            direction: Filter by 'inbound' or 'outbound' (optional)
            
        Returns:
            List of message dictionaries.
        """
        if direction:
            select_sql = """
            SELECT * FROM whatsapp_messages
            WHERE direction = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """
            params = (direction, limit)
        else:
            select_sql = """
            SELECT * FROM whatsapp_messages
            ORDER BY timestamp DESC
            LIMIT %s
            """
            params = (limit,)
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(select_sql, params)
                messages = list(cursor.fetchall())
            return [dict(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Convenience functions for simple usage
def get_db() -> NeonDatabase:
    """Get a database instance."""
    return NeonDatabase()


def init_db_schema() -> bool:
    """Initialize the database schema."""
    db = get_db()
    return db.init_schema()


if __name__ == "__main__":
    # Test the database connection
    print("Testing Neon database connection...")
    db = NeonDatabase()
    
    if db.test_connection():
        print("✓ Connection successful!")
        
        # Initialize schema
        print("\nInitializing schema...")
        if db.init_schema():
            print("✓ Schema initialized!")
        else:
            print("✗ Schema initialization failed!")
    else:
        print("✗ Connection failed! Check your NEON_DATABASE_URL")
