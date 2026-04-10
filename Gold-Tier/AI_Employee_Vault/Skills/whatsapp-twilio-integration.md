---
name: whatsapp-twilio-integration
description: |
  Send and receive WhatsApp messages via Twilio API.
  Uses Neon PostgreSQL for message storage and AI Employee Vault for agent coordination.
version: 1.0.0
requirements:
  - twilio Python package
  - Neon PostgreSQL database
  - Twilio account with WhatsApp enabled
---

# WhatsApp Twilio Integration Skill

## Overview

This skill enables the AI Employee to send and receive WhatsApp messages using the **Twilio WhatsApp API** with **Neon PostgreSQL** for reliable message storage.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHATSAPP INTEGRATION                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Twilio Cloud   │     │   Neon Database  │     │  AI Employee     │
│                  │     │                  │     │  Vault           │
│  - WhatsApp API  │────▶│  - Messages      │────▶│  - Inbox/        │
│  - Webhooks      │     │  - Status track  │     │  - Done/         │
│                  │     │                  │     │  - Logs/         │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                       │                        │
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   AI Orchestrator│
                 │   (ralph_wiggum) │
                 │                  │
                 │  - Reads Inbox   │
                 │  - Drafts reply  │
                 │  - Sends via API │
                 │  - Moves to Done │
                 └──────────────────┘
```

## Prerequisites

### 1. Twilio Account Setup

1. Sign up at https://www.twilio.com
2. Enable WhatsApp sandbox (for testing) or production number
3. Get your credentials:
   - Account SID
   - Auth Token
   - WhatsApp Number

### 2. Neon Database Setup

1. Sign up at https://neon.tech
2. Create a new project
3. Get your connection string

### 3. Environment Variables

Create a `.env` file in the Gold-Tier directory:

```bash
# Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Neon Database
NEON_DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# Vault Path
VAULT_PATH=AI_Employee_Vault
```

## File Structure

```
Gold-Tier/
├── scripts/
│   ├── db_neon.py              # Database connection module
│   ├── twilio_webhook.py       # FastAPI webhook server
│   ├── sync_neon_to_vault.py   # Database to Vault bridge
│   └── whatsapp_responder.py   # Message sending client
├── AI_Employee_Vault/
│   ├── Inbox/                  # New messages (JSON files)
│   ├── Done/                   # Processed messages
│   └── Logs/
│       ├── whatsapp_sent_*.json
│       └── whatsapp_error_*.json
└── .env                        # Credentials (DO NOT COMMIT)
```

---

## Skill 1: Initialize Database

Run this once to set up the database schema:

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

python scripts\db_neon.py
```

**Expected Output:**
```
Testing Neon database connection...
✓ Connection successful!

Initializing schema...
✓ Schema initialized!
```

### Database Schema

The `whatsapp_messages` table has these columns:

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `sender_number` | VARCHAR(20) | Sender's WhatsApp number |
| `message_body` | TEXT | Message content |
| `timestamp` | TIMESTAMP | When message was received |
| `status` | VARCHAR(20) | unread/processing/sent/done/failed |
| `direction` | VARCHAR(10) | inbound or outbound |
| `recipient_number` | VARCHAR(20) | Recipient (for outbound) |
| `twilio_sid` | VARCHAR(100) | Twilio message ID |
| `error_message` | TEXT | Error details (if failed) |

---

## Skill 2: Start Webhook Server

The webhook server receives incoming messages from Twilio:

```bash
# Start the webhook server
python scripts\twilio_webhook.py --host 0.0.0.0 --port 8000
```

**For production (with ngrok tunnel):**

```bash
# In one terminal, start ngrok
ngrok http 8000

# In another terminal, start webhook server
python scripts\twilio_webhook.py --host 0.0.0.0 --port 8000
```

### Configure Twilio Webhook URL

1. Go to Twilio Console → WhatsApp Sandbox Settings
2. Set "When a message comes in" to your ngrok URL:
   ```
   https://your-subdomain.ngrok.io/webhook
   ```
3. Save settings

### Webhook Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/webhook` | POST | Receive incoming messages |
| `/webhook/status` | POST | Message status updates |
| `/messages` | GET | Retrieve messages (debug) |

---

## Skill 3: Sync Messages to Vault

Bridge database messages to the file-based AI Employee system:

```bash
# Run sync once
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault

# Run continuously (every 30 seconds)
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --interval 30

# Check sync status
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --status
```

### What Sync Does

1. Queries Neon for `direction='inbound'` AND `status='unread'`
2. Creates JSON file in `AI_Employee_Vault/Inbox/`
3. Updates database status to `'processing'`

### Inbox File Format

```json
{
  "id": "wa_twilio_123",
  "database_id": 123,
  "type": "whatsapp",
  "source": "twilio",
  "direction": "inbound",
  "status": "processing",
  "sender": {
    "number": "whatsapp:+1234567890",
    "display": "1234567890"
  },
  "message": {
    "body": "Hello, I need help with my order",
    "timestamp": "2026-03-31T10:30:00+00:00",
    "twilio_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  },
  "ai_employee": {
    "requires_action": true,
    "action_type": "whatsapp_reply",
    "priority": "normal",
    "processed": false,
    "response_sent": false
  }
}
```

---

## Skill 4: Send WhatsApp Messages

### Basic Usage

```bash
python scripts\whatsapp_responder.py \
  --to "whatsapp:+1234567890" \
  --message "Hello from AI Employee!"
```

### Test Connection

```bash
python scripts\whatsapp_responder.py --test
```

### Python API Usage

```python
from whatsapp_responder import WhatsAppResponder

# Initialize
responder = WhatsAppResponder()

# Send message
result = responder.send_message(
    target_number="whatsapp:+1234567890",
    message_text="Thank you for your message. We'll get back to you soon."
)

if result["success"]:
    print(f"Message sent! SID: {result['message_sid']}")
else:
    print(f"Failed: {result['error']}")
```

### Response Format

```json
{
  "success": true,
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "sent",
  "timestamp": "2026-03-31T10:35:00.000000",
  "database_id": 124
}
```

---

## Skill 5: AI Orchestrator Workflow

The AI Employee processes WhatsApp messages automatically:

### Step 1: Read Inbox Files

```python
import json
from pathlib import Path

inbox_dir = Path("AI_Employee_Vault/Inbox")
wa_files = list(inbox_dir.glob("wa_twilio_*.json"))

for wa_file in wa_files:
    with open(wa_file) as f:
        message_data = json.load(f)
    
    # Process message
    print(f"Processing: {message_data['message']['body']}")
```

### Step 2: Generate AI Response

Use Qwen Code or your AI orchestrator to draft a response:

```
You are an AI Employee handling WhatsApp customer messages.

Message from +1234567890:
"Hello, I need help with my order"

Draft a professional, helpful response.
```

### Step 3: Send Reply

```python
from whatsapp_responder import WhatsAppResponder

responder = WhatsAppResponder()

# Reply using original sender info
result = responder.send_reply(
    original_message=message_data,
    reply_text="Hello! I'd be happy to help with your order. Could you please provide your order number?"
)
```

### Step 4: Move to Done

```python
import shutil

if result["success"]:
    # Move to Done folder
    done_dir = Path("AI_Employee_Vault/Done")
    shutil.move(str(wa_file), str(done_dir / wa_file.name))
    
    # Update database
    from db_neon import NeonDatabase
    db = NeonDatabase()
    db.mark_message_as_done(message_data["database_id"])
```

---

## Complete Workflow Example

```bash
# Terminal 1: Start webhook server (receives messages)
python scripts\twilio_webhook.py --port 8000

# Terminal 2: Sync messages to Vault (run every 30 seconds)
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --interval 30

# Terminal 3: Process messages with AI
python scripts\ralph_wiggum.py --vault AI_Employee_Vault --prompt "Process WhatsApp messages"
```

---

## Error Handling

### Common Issues

| Issue | Solution |
|-------|----------|
| "TWILIO_ACCOUNT_SID not found" | Check `.env` file exists and has correct values |
| "Database connection failed" | Verify NEON_DATABASE_URL is correct |
| "Twilio API error 401" | Check Account SID and Auth Token |
| "Twilio API error 404" | Verify WhatsApp number format (whatsapp:+123...) |
| Webhook not receiving messages | Check ngrok tunnel is running and URL is in Twilio console |

### Error Logs

Check error logs in:
```
AI_Employee_Vault/Logs/whatsapp_error_*.json
```

---

## Testing

### Test Full Flow

1. **Send test message to Twilio WhatsApp number**
2. **Check webhook logs** - Should show message received
3. **Check database** - Message should be inserted
4. **Run sync** - JSON file should appear in Inbox
5. **Process with AI** - Response should be drafted
6. **Send reply** - Message should be sent via Twilio
7. **Check Done folder** - JSON file should be moved

### Quick Test Commands

```bash
# 1. Test database
python scripts\db_neon.py

# 2. Test Twilio connection
python scripts\whatsapp_responder.py --test

# 3. Send test message
python scripts\whatsapp_responder.py \
  --to "whatsapp:+1234567890" \
  --message "Test from AI Employee"

# 4. Check sync status
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --status
```

---

## Production Deployment

### Run as Windows Service

```powershell
# Create scheduled task for webhook
schtasks /Create /TN "WhatsApp_Webhook" /TR "python scripts\twilio_webhook.py" /SC ONSTART /RL HIGHEST

# Create scheduled task for sync (every 30 seconds)
schtasks /Create /TN "WhatsApp_Sync" /TR "python scripts\sync_neon_to_vault.py --interval 30" /SC ONSTART /RL HIGHEST
```

### Run with PM2 (Node.js Process Manager)

```bash
npm install -g pm2

# Start webhook server
pm2 start scripts/twilio_webhook.py --name whatsapp_webhook --interpreter python

# Start sync process
pm2 start scripts/sync_neon_to_vault.py --name whatsapp_sync --interpreter python -- --interval 30

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

---

## Security Best Practices

1. **Never commit `.env`** - Add to `.gitignore`
2. **Use HTTPS for webhooks** - Use ngrok or deploy behind HTTPS proxy
3. **Validate Twilio signatures** - Verify requests are from Twilio
4. **Rate limiting** - Implement rate limits for outbound messages
5. **Audit logging** - All messages logged to database and Vault

---

## API Reference

### db_neon.py

| Method | Purpose |
|--------|---------|
| `init_schema()` | Create database tables |
| `insert_inbound_message()` | Store incoming message |
| `insert_outbound_message()` | Store outgoing message |
| `get_unread_inbound_messages()` | Get messages to sync |
| `mark_message_as_done()` | Mark as processed |

### whatsapp_responder.py

| Method | Purpose |
|--------|---------|
| `send_message()` | Send WhatsApp message |
| `send_reply()` | Reply to original message |
| `test_connection()` | Verify Twilio credentials |

### sync_neon_to_vault.py

| Method | Purpose |
|--------|---------|
| `run()` | Sync unread messages to Vault |
| `mark_as_done()` | Mark message complete |
| `get_sync_status()` | Get sync statistics |

---

## Troubleshooting

### Messages not appearing in Inbox

1. Check webhook server is running
2. Verify Twilio webhook URL is correct
3. Check database has messages: `SELECT * FROM whatsapp_messages`
4. Run sync manually: `python scripts\sync_neon_to_vault.py`

### Messages not being sent

1. Test Twilio connection: `python scripts\whatsapp_responder.py --test`
2. Check credentials in `.env`
3. Verify phone number format (must include `whatsapp:` prefix)
4. Check error logs in `AI_Employee_Vault/Logs/`

### Database connection issues

1. Test connection: `python scripts\db_neon.py`
2. Verify NEON_DATABASE_URL format
3. Check network/firewall settings
4. Ensure SSL is enabled in connection string

---

## Related Documentation

- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [Neon PostgreSQL](https://neon.tech/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [AI Employee Orchestrator](../QWEN.md)

---

*WhatsApp Twilio Integration Skill v1.0 | Gold Tier | AI Employee Hackathon 0*
