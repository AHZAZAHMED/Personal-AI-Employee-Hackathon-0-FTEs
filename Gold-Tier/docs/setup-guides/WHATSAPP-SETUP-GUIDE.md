# WhatsApp Integration Setup Guide (Twilio + Neon)

**Gold Tier Feature | Production Ready**

---

## Overview

This guide walks you through setting up WhatsApp integration for your AI Employee using:
- **Twilio WhatsApp API** - For sending/receiving messages
- **Neon PostgreSQL** - Serverless database for message storage
- **AI Employee Vault** - File-based coordination with autonomous agents

---

## Prerequisites

| Component | Purpose | Cost |
|-----------|---------|------|
| Twilio Account | WhatsApp API | Free tier: 1,000 msgs/month |
| Neon Account | PostgreSQL database | Free tier available |
| ngrok (optional) | Local webhook tunnel | Free tier available |

---

## Step 1: Twilio Setup

### 1.1 Create Twilio Account

1. Go to https://www.twilio.com
2. Sign up for a free account
3. Verify your email and phone number

### 1.2 Enable WhatsApp Sandbox

1. Go to **Console** → **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Follow the instructions to connect your WhatsApp to the sandbox
3. Note your sandbox number (e.g., `whatsapp:+14155238886`)

### 1.3 Get Your Credentials

1. Go to **Console** → **Account** → **Settings** → **General**
2. Copy these values:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click "Show" to reveal)

### 1.4 (Optional) Production WhatsApp Number

For production use (beyond sandbox):

1. Go to **Console** → **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Click "Set up production number"
3. Follow Meta Business verification process
4. This can take 24-48 hours for approval

---

## Step 2: Neon Database Setup

### 2.1 Create Neon Account

1. Go to https://neon.tech
2. Sign up (GitHub or email)
3. Create a new project

### 2.2 Get Connection String

1. In your project dashboard, find **Connection Details**
2. Copy the **PostgreSQL connection string**
3. It looks like:
   ```
   postgresql://username:password@host.neon.tech/dbname?sslmode=require
   ```

### 2.3 Test Connection (Optional)

Use any PostgreSQL client to verify:
```bash
psql "postgresql://username:password@host.neon.tech/dbname?sslmode=require"
```

---

## Step 3: Configure Environment Variables

### 3.1 Create .env File

In the `Gold-Tier` directory, create a `.env` file:

```bash
# Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Neon Database
NEON_DATABASE_URL=postgresql://username:password@host.neon.tech/dbname?sslmode=require

# Vault Path
VAULT_PATH=AI_Employee_Vault

# Optional: Webhook authentication
TWILIO_AUTH_TOKEN_WEBHOOK=your_webhook_secret_here
```

### 3.2 Security Notes

- ⚠️ **NEVER commit `.env` to Git** (it's in `.gitignore`)
- ⚠️ Keep your Auth Token secret
- ⚠️ Use different tokens for webhook auth if deploying publicly

---

## Step 4: Install Dependencies

### 4.1 Install Python Packages

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

pip install twilio psycopg2-binary fastapi uvicorn python-dotenv
```

### 4.2 Verify Installation

```bash
python -c "from twilio.rest import Client; print('Twilio OK')"
python -c "import psycopg2; print('PostgreSQL OK')"
python -c "from fastapi import FastAPI; print('FastAPI OK')"
```

---

## Step 5: Initialize Database

### 5.1 Run Database Initialization

```bash
python scripts\db_neon.py
```

**Expected Output:**
```
Testing Neon database connection...
✓ Connection successful!

Initializing schema...
✓ Schema initialized!
```

### 5.2 Verify Tables

Connect to your Neon database and check:
```sql
\dt whatsapp_messages
```

You should see the `whatsapp_messages` table.

---

## Step 6: Start Webhook Server

### 6.1 Local Testing (with ngrok)

**Terminal 1 - Start ngrok:**
```bash
ngrok http 8000
```

Note the HTTPS URL (e.g., `https://abc123.ngrok.io`)

**Terminal 2 - Start webhook server:**
```bash
python scripts\twilio_webhook.py --host 0.0.0.0 --port 8000
```

### 6.2 Configure Twilio Webhook URL

1. Go to Twilio Console → WhatsApp Sandbox Settings
2. Find **"When a message comes in"**
3. Set to: `https://your-subdomain.ngrok.io/webhook`
4. Save settings

### 6.3 Test Webhook

Send a WhatsApp message to your sandbox number.

Check webhook logs - you should see:
```
Received WhatsApp message from: whatsapp:+1234567890
Message stored in database with ID: 1
```

---

## Step 7: Sync Messages to Vault

### 7.1 Run Sync (Manual)

```bash
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault
```

### 7.2 Run Sync (Continuous)

```bash
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --interval 30
```

This checks for new messages every 30 seconds.

### 7.3 Verify Inbox Files

Check `AI_Employee_Vault/Inbox/` for new JSON files:
```
wa_twilio_1_sender_20260331_103000.json
```

---

## Step 8: Send Test Message

### 8.1 Test Twilio Connection

```bash
python scripts\whatsapp_responder.py --test
```

**Expected Output:**
```
Twilio connection test successful! Account: Your Account Name
✓ Twilio connection successful!
```

### 8.2 Send Test WhatsApp Message

```bash
python scripts\whatsapp_responder.py \
  --to "whatsapp:+1234567890" \
  --message "Hello from AI Employee!"
```

**Expected Output:**
```
✓ Message sent successfully!
  SID: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  Status: sent
```

---

## Step 9: Production Deployment

### Option A: PM2 (Recommended)

```bash
# Install PM2
npm install -g pm2

# Start webhook server
pm2 start scripts/twilio_webhook.py --name whatsapp_webhook --interpreter python

# Start sync process (every 30 seconds)
pm2 start scripts/sync_neon_to_vault.py --name whatsapp_sync --interpreter python -- --interval 30

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

### Option B: Windows Task Scheduler

```powershell
# Create task for webhook (runs at startup)
schtasks /Create /TN "WhatsApp_Webhook" /TR "python scripts\twilio_webhook.py" /SC ONSTART /RL HIGHEST

# Create task for sync (every 30 seconds)
schtasks /Create /TN "WhatsApp_Sync" /TR "python scripts\sync_neon_to_vault.py --interval 30" /SC ONSTART /RL HIGHEST
```

### Option C: Docker Deployment

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  whatsapp-webhook:
    build: .
    command: python scripts/twilio_webhook.py --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped

  whatsapp-sync:
    build: .
    command: python scripts/sync_neon_to_vault.py --interval 30
    env_file:
      - .env
    restart: unless-stopped
```

---

## Step 10: AI Integration

### 10.1 Manual Processing

1. Check `AI_Employee_Vault/Inbox/` for new WhatsApp messages
2. Read JSON file to see message content
3. Draft response
4. Send via `whatsapp_responder.py`
5. Move JSON to `AI_Employee_Vault/Done/`

### 10.2 Automated Processing (Ralph Wiggum)

```bash
python scripts\ralph_wiggum.py \
  --vault AI_Employee_Vault \
  --prompt "Process all WhatsApp messages in Inbox and send replies"
```

### 10.3 Custom Orchestrator

Add WhatsApp processing to your orchestrator:

```python
from pathlib import Path
import json
from whatsapp_responder import WhatsAppResponder
from db_neon import NeonDatabase

def process_whatsapp_messages():
    inbox_dir = Path("AI_Employee_Vault/Inbox")
    responder = WhatsAppResponder()
    db = NeonDatabase()
    
    for wa_file in inbox_dir.glob("wa_twilio_*.json"):
        with open(wa_file) as f:
            msg = json.load(f)
        
        # Generate AI response (use your AI here)
        response = generate_ai_response(msg['message']['body'])
        
        # Send reply
        result = responder.send_reply(msg, response)
        
        if result['success']:
            # Move to Done
            shutil.move(str(wa_file), f"AI_Employee_Vault/Done/{wa_file.name}")
            db.mark_message_as_done(msg['database_id'])
```

---

## Troubleshooting

### Database Connection Failed

**Problem:** `NEON_DATABASE_URL not found`

**Solution:**
1. Check `.env` file exists in Gold-Tier directory
2. Verify connection string is correct
3. Ensure SSL is enabled (`?sslmode=require`)

### Twilio Authentication Failed

**Problem:** `Twilio API error 401`

**Solution:**
1. Verify Account SID and Auth Token in `.env`
2. Check for extra spaces in values
3. Regenerate Auth Token in Twilio console if needed

### Webhook Not Receiving Messages

**Problem:** Messages not appearing in database

**Solution:**
1. Check ngrok tunnel is running
2. Verify webhook URL in Twilio console matches ngrok URL
3. Check webhook server logs for errors
4. Test webhook manually: `curl -X POST http://localhost:8000/webhook`

### Messages Not Syncing to Vault

**Problem:** Inbox folder is empty

**Solution:**
1. Run sync manually: `python scripts\sync_neon_to_vault.py`
2. Check database has unread messages: `SELECT * FROM whatsapp_messages WHERE status='unread'`
3. Verify Vault path is correct

### Message Send Failed

**Problem:** `Twilio API error 404`

**Solution:**
1. Verify recipient number format: `whatsapp:+1234567890`
2. Ensure number is connected to WhatsApp sandbox
3. Check your Twilio sandbox allows sending to that number

---

## Architecture Reference

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
                 └──────────────────┘
```

---

## Quick Reference Commands

```bash
# Initialize database
python scripts\db_neon.py

# Start webhook server
python scripts\twilio_webhook.py --host 0.0.0.0 --port 8000

# Sync messages to Vault
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --interval 30

# Send WhatsApp message
python scripts\whatsapp_responder.py --to "whatsapp:+1234567890" --message "Hello"

# Test Twilio connection
python scripts\whatsapp_responder.py --test

# Check sync status
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --status
```

---

## Cost Estimate

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Twilio WhatsApp | 1,000 msgs/month | $0.005/msg after |
| Neon PostgreSQL | 0.5 GB storage | $19/month for 10GB |
| ngrok tunnel | 40 requests/min | $8/month for more |

**Total: $0/month** for testing and light usage!

---

## Related Documentation

- [WhatsApp Twilio Integration Skill](AI_Employee_Vault/Skills/whatsapp-twilio-integration.md)
- [Twilio WhatsApp API Docs](https://www.twilio.com/docs/whatsapp)
- [Neon PostgreSQL Docs](https://neon.tech/docs)
- [Gold Tier Complete](GOLD-TIER-COMPLETE.md)

---

*WhatsApp Integration Setup Guide v1.0 | Gold Tier | AI Employee Hackathon 0*
