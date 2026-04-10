# WhatsApp Integration - Testing Guide

**Complete testing commands for WhatsApp (Twilio + Neon) integration**

---

## Prerequisites

Before testing, ensure you have:
- ✅ Twilio account with WhatsApp sandbox enabled
- ✅ Neon database created
- ✅ `.env` file configured with credentials
- ✅ Python dependencies installed

---

## Step 1: Verify Environment Setup

### Check .env File

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

# View your .env file (verify credentials are set)
type .env
```

**Expected `.env` contents:**
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
NEON_DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require
VAULT_PATH=AI_Employee_Vault
```

---

## Step 2: Test Database Connection

### Command:
```bash
python scripts\db_neon.py
```

### Expected Output:
```
Testing Neon database connection...
✓ Connection successful!

Initializing schema...
✓ Schema initialized!
```

### Troubleshooting:

**If you see "Connection failed":**
```bash
# Check your NEON_DATABASE_URL
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('NEON_DATABASE_URL'))"

# Test connection manually (replace with your URL)
psql "postgresql://user:pass@host.neon.tech/dbname?sslmode=require" -c "SELECT 1"
```

---

## Step 3: Verify Database Schema

### Command:
```bash
python -c "from db_neon import NeonDatabase; db = NeonDatabase(); print(db.test_connection())"
```

### Expected Output:
```
True
```

### Check Table Exists:
```bash
python -c """
from db_neon import NeonDatabase
db = NeonDatabase()
with db.get_cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'whatsapp_messages'
    \"\"\")
    result = cursor.fetchone()
    print('Table exists:', result is not None)
"""
```

---

## Step 4: Start Webhook Server

### Terminal 1 - Start ngrok (for local testing):
```bash
# Install ngrok if not already installed
# Download from: https://ngrok.com/download

ngrok http 8000
```

**Note the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Terminal 2 - Start Webhook Server:
```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

python scripts\twilio_webhook.py --host 0.0.0.0 --port 8000
```

### Expected Output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Database schema initialized
INFO:     Starting Twilio WhatsApp Webhook server on 0.0.0.0:8000
INFO:     Webhook URL: http://localhost:8000/webhook
```

### Test Health Endpoint:
```bash
# Open new terminal and run:
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-03-31T10:00:00.000000"
}
```

---

## Step 5: Configure Twilio Webhook URL

1. **Go to Twilio Console:**
   - URL: https://console.twilio.com
   - Navigate to: **Messaging** → **Try it out** → **Send a WhatsApp message**

2. **Find Sandbox Settings:**
   - Scroll to "When a message comes in"
   - Click "Edit"

3. **Set Webhook URL:**
   ```
   https://your-subdomain.ngrok.io/webhook
   ```
   (Replace `your-subdomain` with your actual ngrok subdomain)

4. **Save Settings**

---

## Step 6: Test Receiving WhatsApp Messages

### Send Test Message:

1. **Open WhatsApp on your phone**

2. **Send message to Twilio sandbox number:**
   ```
   whatsapp:+14155238886
   ```

3. **Message content:**
   ```
   Hello from testing!
   ```

### Check Webhook Logs:

In the terminal running `twilio_webhook.py`, you should see:
```
INFO:     Received WhatsApp message from: whatsapp:+923001234567
INFO:     Message stored in database with ID: 1
```

### Verify in Database:

```bash
python -c """
from db_neon import NeonDatabase
db = NeonDatabase()
messages = db.get_unread_inbound_messages(limit=10)
print(f'Unread messages: {len(messages)}')
for msg in messages:
    print(f\"ID: {msg['id']}, From: {msg['sender_number']}, Body: {msg['message_body'][:50]}...\")
"""
```

**Expected Output:**
```
Unread messages: 1
ID: 1, From: whatsapp:+923001234567, Body: Hello from testing!...
```

---

## Step 7: Test Sync to Vault

### Run Sync Once:
```bash
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault
```

### Expected Output:
```
INFO:     Starting Neon to Vault sync...
INFO:     Retrieved 1 unread messages from database
INFO:     Saved message to Vault: wa_twilio_1_923001234567_20260331_103000.json
Sync complete: 1 synced, 0 failed
```

### Verify Inbox File:
```bash
dir AI_Employee_Vault\Inbox\wa_twilio_*.json
```

### View File Contents:
```bash
type AI_Employee_Vault\Inbox\wa_twilio_1_*.json
```

**Expected JSON:**
```json
{
  "id": "wa_twilio_1",
  "database_id": 1,
  "type": "whatsapp",
  "source": "twilio",
  "direction": "inbound",
  "status": "processing",
  "sender": {
    "number": "whatsapp:+923001234567",
    "display": "923001234567"
  },
  "message": {
    "body": "Hello from testing!",
    "timestamp": "2026-03-31T10:30:00+00:00"
  },
  "ai_employee": {
    "requires_action": true,
    "action_type": "whatsapp_reply",
    "priority": "normal"
  }
}
```

### Check Sync Status:
```bash
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --status
```

**Expected Output:**
```json
{
  "vault_inbox_count": 1,
  "database_unread_count": 0,
  "last_sync": "2026-03-31T10:30:00.000000",
  "vault_path": "E:\\...\\AI_Employee_Vault",
  "inbox_path": "E:\\...\\AI_Employee_Vault\\Inbox"
}
```

---

## Step 8: Test Sending WhatsApp Messages

### Test Twilio Connection:
```bash
python scripts\whatsapp_responder.py --test
```

### Expected Output:
```
INFO:     Twilio connection test successful! Account: Your Account Name
✓ Twilio connection successful!
```

### Send Test Message:
```bash
python scripts\whatsapp_responder.py \
  --to "whatsapp:+923001234567" \
  --message "Test from AI Employee!"
```

### Expected Output:
```
INFO:     Sending WhatsApp message to: whatsapp:+9234567890
INFO:     Message sent successfully! SID: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
✓ Message sent successfully!
  SID: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  Status: sent
  Database ID: 2
```

### Verify on WhatsApp:
Check your WhatsApp - you should receive the test message!

### Check Database for Outbound Message:
```bash
python -c """
from db_neon import NeonDatabase
db = NeonDatabase()
messages = db.get_recent_messages(limit=5, direction='outbound')
print(f'Outbound messages: {len(messages)}')
for msg in messages:
    print(f\"ID: {msg['id']}, To: {msg['recipient_number']}, Body: {msg['message_body'][:50]}...\")
"""
```

---

## Step 9: Test Continuous Sync

### Run Sync in Background (every 30 seconds):
```bash
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --interval 30
```

### Expected Output:
```
INFO:     Running sync every 30 seconds...
INFO:     Starting Neon to Vault sync...
INFO:     Retrieved 0 unread messages from database
INFO:     Sync complete: 0 synced, 0 failed
INFO:     Starting Neon to Vault sync...
(repeats every 30 seconds)
```

### Test While Running:
1. Send another WhatsApp message to sandbox
2. Watch sync logs - should detect and process new message within 30 seconds

---

## Step 10: Full Integration Test

### Start All Services:

**Terminal 1 - Webhook:**
```bash
python scripts\twilio_webhook.py --host 0.0.0.0 --port 8000
```

**Terminal 2 - Sync:**
```bash
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --interval 30
```

### Send Message Flow:

1. **Send WhatsApp to sandbox:**
   ```
   I need help with my order
   ```

2. **Check webhook receives it:**
   ```
   INFO: Received WhatsApp message from: whatsapp:+923001234567
   ```

3. **Check sync processes it:**
   ```
   INFO: Retrieved 1 unread messages from database
   INFO: Saved message to Vault: wa_twilio_2_...json
   ```

4. **Check Inbox file created:**
   ```bash
   dir AI_Employee_Vault\Inbox\wa_twilio_*.json
   ```

5. **Process with AI (manual test):**
   ```bash
   # Read the message
   type AI_Employee_Vault\Inbox\wa_twilio_2_*.json
   
   # Send reply
   python scripts\whatsapp_responder.py ^
     --to "whatsapp:+923001234567" ^
     --message "Hello! I'd be happy to help with your order. Could you please provide your order number?"
   
   # Move to Done
   move AI_Employee_Vault\Inbox\wa_twilio_2_*.json AI_Employee_Vault\Done\
   ```

6. **Verify reply received on WhatsApp**

---

## Step 11: Test with Ralph Wiggum (AI Automation)

### Process All WhatsApp Messages:
```bash
python scripts\ralph_wiggum.py ^
  --vault AI_Employee_Vault ^
  --prompt "Process all WhatsApp messages in Inbox. Read each message, draft a helpful response, send via whatsapp_responder.py, and move processed files to Done/"
```

### Watch AI Processing:
The Ralph Wiggum loop will:
1. Find WhatsApp JSON files in `Inbox/`
2. Read message content
3. Generate AI response
4. Call `whatsapp_responder.py` to send reply
5. Move file to `Done/`
6. Update database status to 'done'

---

## Step 12: Test Error Handling

### Test Invalid Phone Number:
```bash
python scripts\whatsapp_responder.py \
  --to "invalid_number" \
  --message "Test"
```

**Expected Output:**
```
✗ Failed to send message!
  Error: Twilio API error: The 'To' number is not a valid WhatsApp number
```

### Test Missing Credentials:
```bash
# Temporarily rename .env
move .env .env.backup

# Try to send message
python scripts\whatsapp_responder.py --test

# Restore .env
move .env.backup .env
```

**Expected Output:**
```
✗ Twilio connection failed!
  Error: TWILIO_ACCOUNT_SID not found
```

### Check Error Logs:
```bash
dir AI_Employee_Vault\Logs\whatsapp_error_*.json
type AI_Employee_Vault\Logs\whatsapp_error_*.json
```

---

## Step 13: Production Deployment Test (PM2)

### Install PM2:
```bash
npm install -g pm2
```

### Start Services:
```bash
# Start webhook server
pm2 start scripts/twilio_webhook.py --name whatsapp_webhook --interpreter python

# Start sync process
pm2 start scripts/sync_neon_to_vault.py --name whatsapp_sync --interpreter python -- --interval 30 --vault AI_Employee_Vault

# Check status
pm2 status

# View logs
pm2 logs whatsapp_webhook
pm2 logs whatsapp_sync
```

### Expected Output:
```
┌────────────────────┬────┬──────┬────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┐
│ App name           │ id │ mode │ status │ cpu     │ memory   │ ...    │      │           │          │
├────────────────────┼────┼──────┼────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┤
│ whatsapp_webhook   │ 0  │ fork │ online │ 0%      │ 50MB     │        │      │           │          │
│ whatsapp_sync      │ 1  │ fork │ online │ 0%      │ 45MB     │        │      │           │          │
└────────────────────┴────┴──────┴────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┘
```

### Test While Running:
1. Send WhatsApp message
2. Check PM2 logs: `pm2 logs whatsapp_webhook --lines 50`
3. Verify message processed

### Stop Services:
```bash
pm2 stop whatsapp_webhook whatsapp_sync
pm2 delete whatsapp_webhook whatsapp_sync
```

---

## Quick Test Commands Reference

```bash
# 1. Test database
python scripts\db_neon.py

# 2. Test Twilio connection
python scripts\whatsapp_responder.py --test

# 3. Send test message
python scripts\whatsapp_responder.py --to "whatsapp:+1234567890" --message "Hello"

# 4. Check database messages
python -c "from db_neon import NeonDatabase; db = NeonDatabase(); print(db.get_unread_inbound_messages())"

# 5. Run sync once
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault

# 6. Check sync status
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault --status

# 7. Start webhook (test)
python scripts\twilio_webhook.py --port 8000

# 8. Test webhook health
curl http://localhost:8000/health

# 9. View inbox files
dir AI_Employee_Vault\Inbox\wa_twilio_*.json

# 10. View error logs
dir AI_Employee_Vault\Logs\whatsapp_error_*.json
```

---

## Test Checklist

| Test | Command | Expected Result | Status |
|------|---------|-----------------|--------|
| Database connection | `python scripts\db_neon.py` | ✓ Connection successful | ☐ |
| Schema initialized | `python scripts\db_neon.py` | ✓ Schema initialized | ☐ |
| Webhook starts | `python scripts\twilio_webhook.py` | Server running on :8000 | ☐ |
| Webhook health | `curl localhost:8000/health` | status: healthy | ☐ |
| Receive message | Send WhatsApp to sandbox | Log shows message received | ☐ |
| Database insert | Check database | 1 unread message | ☐ |
| Sync to Vault | `python scripts\sync_neon_to_vault.py` | JSON file in Inbox/ | ☐ |
| Send message | `python scripts\whatsapp_responder.py` | ✓ Message sent | ☐ |
| Receive reply | Check WhatsApp | Message received | ☐ |
| Continuous sync | `--interval 30` | Syncs every 30s | ☐ |
| PM2 deployment | `pm2 start ...` | Services online | ☐ |

---

## Troubleshooting

### "NEON_DATABASE_URL not found"
```bash
# Check .env exists
dir .env

# Verify content
type .env | findstr NEON
```

### "Twilio API error 401"
```bash
# Verify credentials
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('SID:', os.getenv('TWILIO_ACCOUNT_SID')[:10] + '...')"
```

### "Webhook not receiving messages"
```bash
# Check ngrok is running
curl http://localhost:4040/api/tunnels

# Verify webhook URL in Twilio console
# Must be: https://your-subdomain.ngrok.io/webhook
```

### "Messages not syncing to Vault"
```bash
# Check database for unread messages
python -c "from db_neon import NeonDatabase; db = NeonDatabase(); print(db.get_unread_inbound_messages())"

# Run sync manually
python scripts\sync_neon_to_vault.py --vault AI_Employee_Vault
```

---

*WhatsApp Integration Testing Guide v1.0 | Gold Tier | AI Employee Hackathon 0*
