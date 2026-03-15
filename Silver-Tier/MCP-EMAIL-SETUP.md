# Silver Tier - MCP Email Server Setup

## Overview

Silver Tier now uses **MCP (Model Context Protocol)** for sending emails, as per the hackathon requirements.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              EMAIL SENDING FLOW (MCP)                        │
└─────────────────────────────────────────────────────────────┘

1. Approval Handler detects approved email
   │
2. Calls: execute_approved_email()
   │
3. MCP Email Sender attempts MCP call
   │
   ├── MCP Server available → Send via MCP ✓
   │
   └── MCP Server unavailable → Fallback to Gmail API ✓
```

---

## Setup Instructions

### Step 1: Install MCP Email Server

```bash
npm install -g @modelcontextprotocol/server-email
```

### Step 2: Start MCP Email Server

```bash
# Start the MCP email server
npx @modelcontextprotocol/server-email --port 8808
```

### Step 3: Configure Qwen Code MCP

The MCP config is at: `%APPDATA%\qwen-code\mcp.json`

```json
{
  "servers": [
    {
      "name": "email",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-email"],
      "env": {
        "GMAIL_API_KEY": "your-api-key"
      }
    }
  ]
}
```

---

## Files Changed

| File | Purpose |
|------|---------|
| `scripts/email_sender_mcp.py` | NEW - MCP-based email sender |
| `scripts/approval_handler.py` | UPDATED - Uses MCP email sender |
| `scripts/orchestrator.py` | No change needed |
| `scripts/gmail_watcher.py` | No change needed |

---

## Testing MCP Email

### Test 1: Direct MCP Call

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs

# Start MCP server in one terminal
npx @modelcontextprotocol/server-email --port 8808

# Test in another terminal
python scripts\email_sender_mcp.py --vault AI_Employee_Vault ^
  --send "test@example.com" ^
  --subject "MCP Test" ^
  --body "Testing MCP email sending"
```

### Test 2: Complete Flow

```bash
# 1. Start Gmail Watcher
python scripts\gmail_watcher.py --vault AI_Employee_Vault --interval 30

# 2. Send yourself an email from a different account

# 3. Stop watcher (Ctrl+C)

# 4. Run orchestrator
python scripts\orchestrator.py --vault AI_Employee_Vault --once

# 5. Approve
move AI_Employee_Vault\Pending_Approval\*.md AI_Employee_Vault\Approved\

# 6. Execute (uses MCP)
python scripts\approval_handler.py --vault AI_Employee_Vault
```

---

## Fallback Behavior

If MCP server is not available, the system **automatically falls back** to Gmail API:

```
MCP Call Failed
    ↓
Gmail API Fallback
    ↓
Email Sent Successfully ✓
```

This ensures emails are always sent, even if MCP is not running.

---

## MCP vs Direct API

| Feature | MCP | Direct Gmail API |
|---------|-----|------------------|
| Protocol | Model Context Protocol | REST API |
| Architecture | Modular, decoupled | Direct coupling |
| Hackathon Compliance | ✅ Silver Tier | ❌ Bronze Tier |
| Fallback | ✅ Gmail API | N/A |
| Setup Complexity | Higher | Lower |

---

## Troubleshooting

### MCP Server Not Starting

```bash
# Check if port 8808 is in use
netstat -ano | findstr :8808

# Try different port
npx @modelcontextprotocol/server-email --port 8809
```

### MCP Call Fails

Check logs:
```bash
type AI_Employee_Vault\Logs\*.jsonl
```

Look for:
- `email_sent_mcp` - MCP succeeded
- `email_sent_fallback` - Gmail API fallback used

### Force Gmail API Fallback

If MCP is causing issues, the system automatically uses Gmail API. No action needed.

---

## Verification

After sending, check:

1. **Gmail Sent Folder** - Email should appear
2. **Logs** - Check which method was used:
   ```bash
   type AI_Employee_Vault\Logs\*.jsonl | findstr "email_sent"
   ```

Expected log entries:
```json
{"event_type": "email_sent_mcp", ...}  // MCP succeeded
{"event_type": "email_sent_fallback", ...}  // Fallback used
```

---

*AI Employee Silver Tier v0.3.0 | MCP-Based Email Sending*
