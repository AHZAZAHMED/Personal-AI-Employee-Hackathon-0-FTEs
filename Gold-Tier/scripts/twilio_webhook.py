"""
Twilio WhatsApp Webhook Server

FastAPI server to receive incoming WhatsApp messages from Twilio webhooks.
Stores messages in Neon PostgreSQL database.
"""

import os
import logging
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
from dotenv import load_dotenv

from db_neon import NeonDatabase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Twilio WhatsApp Webhook",
    description="Receives incoming WhatsApp messages from Twilio",
    version="1.0.0"
)

# Security
security = HTTPBasic()

# Database instance
db_instance: Optional[NeonDatabase] = None


def get_db() -> NeonDatabase:
    """Get or create database instance."""
    global db_instance
    if db_instance is None:
        db_instance = NeonDatabase()
    return db_instance


def verify_twilio_token(
    credentials: HTTPBasicCredentials = Depends(security)
) -> str:
    """
    Verify Twilio authentication token.
    
    Args:
        credentials: HTTP Basic credentials from request
        
    Returns:
        Username if authenticated
        
    Raises:
        HTTPException: If authentication fails
    """
    expected_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not expected_token:
        logger.warning("TWILIO_AUTH_TOKEN not set, skipping authentication")
        return credentials.username
    
    if credentials.password != expected_token:
        logger.warning("Invalid authentication token")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Twilio WhatsApp Webhook",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    db = get_db()
    db_status = "connected" if db.test_connection() else "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    AccountSid: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
    _: str = Depends(verify_twilio_token)
):
    """
    Receive incoming WhatsApp messages from Twilio.
    
    Twilio sends POST requests with form-encoded data when a message arrives.
    
    Args:
        From: Sender's WhatsApp number (e.g., 'whatsapp:+1234567890')
        Body: Message text content
        MessageSid: Twilio message SID
        To: Recipient number (your Twilio number)
        MediaUrl0: URL to media attachment (if any)
        MediaContentType0: MIME type of media (if any)
        
    Returns:
        TwiML response or JSON acknowledgment
    """
    logger.info(f"Received WhatsApp message from: {From}")
    logger.debug(f"Message body: {Body[:100]}...")
    
    try:
        db = get_db()
        
        # Insert message into database
        message_id = db.insert_inbound_message(
            sender_number=From,
            message_body=Body,
            twilio_sid=MessageSid
        )
        
        if message_id:
            logger.info(f"Message stored in database with ID: {message_id}")
            
            # Return empty TwiML response (we're just acknowledging receipt)
            # Twilio expects a response within 15 seconds
            return {
                "status": "success",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.error("Failed to store message in database")
            raise HTTPException(status_code=500, detail="Failed to store message")
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/status")
async def twilio_status_callback(
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    To: str = Form(...),
    From: Optional[str] = Form(None),
    AccountSid: Optional[str] = Form(None),
):
    """
    Receive message status updates from Twilio.
    
    Twilio sends status updates when message delivery status changes.
    Status values: queued, sending, sent, delivered, read, failed, undelivered
    
    Args:
        MessageSid: Twilio message SID
        MessageStatus: Current status of the message
        To: Recipient number
        From: Sender number (for inbound messages)
        
    Returns:
        JSON acknowledgment
    """
    logger.info(
        f"Message status update: {MessageSid} -> {MessageStatus}"
    )
    
    try:
        db = get_db()
        
        # Update message status in database
        # Map Twilio status to our status values
        status_mapping = {
            'queued': 'queued',
            'sending': 'sending',
            'sent': 'sent',
            'delivered': 'delivered',
            'read': 'read',
            'failed': 'failed',
            'undelivered': 'failed'
        }
        
        our_status = status_mapping.get(MessageStatus, MessageStatus)
        
        # Try to find and update the message by twilio_sid
        # This requires a method to query by twilio_sid
        # For now, we'll just log the status update
        logger.info(f"Status update recorded: {MessageSid} = {our_status}")
        
        return {
            "status": "success",
            "message_sid": MessageSid,
            "new_status": our_status
        }
        
    except Exception as e:
        logger.error(f"Error processing status update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/messages")
async def get_messages(
    limit: int = 50,
    direction: Optional[str] = None,
    status: Optional[str] = None,
    db: NeonDatabase = Depends(get_db)
):
    """
    Retrieve messages from the database (for debugging/testing).
    
    Args:
        limit: Maximum number of messages to return
        direction: Filter by 'inbound' or 'outbound'
        status: Filter by status (e.g., 'unread', 'sent', 'done')
        
    Returns:
        List of messages
    """
    try:
        if status:
            # Get messages by status
            messages = db.get_unread_inbound_messages(limit=limit)
        elif direction:
            messages = db.get_recent_messages(limit=limit, direction=direction)
        else:
            messages = db.get_recent_messages(limit=limit)
        
        return {
            "count": len(messages),
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the webhook server.
    
    Args:
        host: Host to bind to
        port: Port to listen on
    """
    # Initialize database schema on startup
    db = get_db()
    if db.init_schema():
        logger.info("Database schema initialized")
    else:
        logger.warning("Database schema initialization failed")
    
    logger.info(f"Starting Twilio WhatsApp Webhook server on {host}:{port}")
    logger.info(f"Webhook URL: http://localhost:{port}/webhook")
    logger.info("Configure this URL in your Twilio WhatsApp sandbox settings")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Twilio WhatsApp Webhook Server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database schema and exit"
    )
    
    args = parser.parse_args()
    
    if args.init_db:
        db = get_db()
        if db.init_schema():
            print("✓ Database schema initialized successfully!")
        else:
            print("✗ Database schema initialization failed!")
    else:
        run_server(host=args.host, port=args.port)
