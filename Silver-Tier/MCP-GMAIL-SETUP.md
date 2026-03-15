# Silver Tier - MCP Gmail Integration

## Overview

Silver Tier uses **@cablate/mcp-gmail** MCP server for sending emails, as per the hackathon requirements.

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
3. MCP Gmail Sender (@cablate/mcp-gmail) attempts to send
   │
   ├── MCP Server available → Send via MCP ✓
   │
   └── MCP Server unavailable → Fallback to Gmail API ✓
```

---

## Setup Instructions

### Step 1: Install MCP Gmail Server

```bash
npx -y @cablate/mcp-gmail
```

This package is automatically installed when you run the email sender.

### Step 2: MCP Configuration

The MCP config is at: `%APPDATA%\qwen-code\mcp.json`

```json
{
  "servers": [
    {
      "name": "gmail",
      "command": "npx",
      "args": ["-y", "@cablate/mcp-gmail"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  ]
}
```

### Step 3: Gmail API Credentials

Ensure you have:
- `credentails.json` in project root
- `.gmail_token.json` in `AI_Employee_Vault/` (created on first auth)

---

## Files

| File | Purpose |
|------|---------|
| `scripts/email_sender_mcp.py` | MCP Gmail sender with Gmail API fallback |
| `scripts/approval_handler.py` | Uses MCP email sender |
| `%APPDATA%\qwen-code\mcp.json` | MCP configuration |

---

## Testing MCP Gmail

### Test 1: Direct Email Send

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs

# Test MCP email sender
python scripts\email_sender_mcp.py --vault AI_Employee_Vault ^
  --send "test@example.com" ^
  --subject "MCP Test" ^
  --body "Testing MCP Gmail sending"
```

**Expected Output:**
```
Email Sender (MCP Gmail) ready
MCP Server: @cablate/mcp-gmail
    Sending email via MCP Gmail...
    To: test@example.com
    Subject: MCP Test
    Trying tool: sendEmail
    Calling MCP tool: sendEmail
    Server: @cablate/mcp-gmail
    ✓ Email sent via MCP!

✓ Email sent!
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

If MCP server fails, the system **automatically falls back** to Gmail API:

```
MCP Call Failed
    ↓
Gmail API Fallback
    ↓
Email Sent Successfully ✓
```

This ensures emails are always sent, even if MCP has issues.

---

## MCP vs Direct API

| Feature | MCP (@cablate/mcp-gmail) | Direct Gmail API |
|---------|--------------------------|------------------|
| Protocol | Model Context Protocol | REST API |
| Architecture | Modular, decoupled | Direct coupling |
| Hackathon Compliance | ✅ Silver Tier | ❌ Bronze Tier |
| Fallback | ✅ Gmail API | N/A |
| Setup Complexity | Medium | Lower |

---

## Troubleshooting

### MCP Tool Not Found

```bash
# The package tries multiple tool names
# If all fail, it falls back to Gmail API
# Check logs for which tool worked
type AI_Employee_Vault\Logs\*.jsonl | findstr "mcp"
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

The system automatically falls back if MCP fails. No action needed.

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
{"event_type": "email_sent_mcp", "method": "mcp_cablate_gmail"}
{"event_type": "email_sent_fallback", "method": "fallback_gmail"}
```

---

## Silver Tier Compliance

✅ **MCP Server Used**: `@cablate/mcp-gmail`
✅ **Fallback Available**: Gmail API
✅ **Approval Workflow**: Working
✅ **Plan Generation**: Working
✅ **Multiple Watchers**: Gmail + File System

---

*AI Employee Silver Tier v0.4.0 | MCP Gmail Integration*
