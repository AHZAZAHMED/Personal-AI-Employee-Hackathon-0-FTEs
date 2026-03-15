---
name: whatsapp-watcher-integration
description: |
  Monitor WhatsApp Web for new messages and create action files.
  Uses Playwright MCP for browser automation to read WhatsApp messages.
  Detects urgent keywords and creates high-priority tasks.
  Use for real-time message monitoring and quick response.
---

# WhatsApp Watcher Integration

Monitor WhatsApp Web and create action files for new messages.

---

## When to Use

- Monitor business WhatsApp for client inquiries
- Detect urgent messages (asap, invoice, payment, help)
- Create tasks from important WhatsApp messages
- Track response times for WhatsApp communications

---

## Prerequisites

1. **Playwright MCP Server** installed and running
2. **WhatsApp Web** account (business or personal)
3. **Active WhatsApp session** (QR code scanned)
4. **Chromium browser** installed (for Playwright)

---

## Skill 1: Playwright Setup for WhatsApp

### Step 1: Install Playwright

```bash
npm install -g @playwright/mcp
npm install playwright
```

### Step 2: Start Playwright MCP Server

```bash
# Start server with persistent browser context
npx @playwright/mcp@latest --port 8808 --shared-browser-context
```

### Step 3: Create WhatsApp Session Directory

```bash
# Create directory for WhatsApp session data
mkdir E:\Personal-AI-Employee-Hackathon-0-FTEs\whatsapp_session
```

### Step 4: First-Time WhatsApp Login

```
1. Start Playwright MCP server
2. Navigate to https://web.whatsapp.com
3. Scan QR code with your phone
4. Session will be saved in whatsapp_session folder
5. Future runs will auto-login
```

---

## Skill 2: Run WhatsApp Watcher

### Continuous Monitoring

```bash
python scripts\whatsapp_watcher.py ^
  --vault AI_Employee_Vault ^
  --session-path whatsapp_session ^
  --interval 30
```

**Options:**
- `--vault`: Path to Obsidian vault
- `--session-path`: Path to store WhatsApp session
- `--interval`: Check every N seconds (default: 30)
- `--keywords`: Custom keywords to detect (comma-separated)
- `--dry-run`: Log only, don't create files

### Run via Task Scheduler

```powershell
# Create WhatsApp Watcher task
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "scripts\whatsapp_watcher.py --vault AI_Employee_Vault --session-path whatsapp_session" `
  -WorkingDirectory "E:\Personal-AI-Employee-Hackathon-0-FTEs"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Seconds 30) `
  -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask `
  -TaskName "AI_Employee_WhatsApp_Watcher" `
  -Action $action `
  -Trigger $trigger `
  -Description "Monitor WhatsApp Web for new messages every 30 seconds"
```

---

## Skill 3: Action File Format

### WhatsApp Message Action File

```markdown
---
type: whatsapp
from: +1234567890 (John Doe)
chat: John Doe - Client
message_id: msg_abc123
received: 2026-02-28T10:30:00
priority: normal
is_urgent: false
keywords_detected: []
created: 2026-02-28T10:30:15
status: pending
---

## Message Content

**From:** +1234567890 (John Doe)
**Chat:** John Doe - Client
**Received:** 2026-02-28 10:30:00

Hi, I wanted to follow up on the proposal we discussed last week. 
When can we schedule a call?

Thanks,
John

## Suggested Actions

- [ ] Read full message content
- [ ] Determine if reply needed
- [ ] Schedule call if requested
- [ ] Reply via WhatsApp (approval may be required)
- [ ] Archive after processing

---
*Created by AI Employee WhatsApp Watcher v0.2.0*
```

### Urgent Message Detection

Messages are marked urgent if they contain:
- "urgent"
- "asap"
- "immediately"
- "emergency"
- "invoice"
- "payment"
- "help"
- "as soon as possible"

```markdown
---
type: whatsapp
from: +1234567890 (Jane Smith)
chat: Jane Smith - Vendor
message_id: msg_def456
received: 2026-02-28T14:00:00
priority: high
is_urgent: true
keywords_detected: ["urgent", "payment"]
---

## Message Content

**From:** +1234567890 (Jane Smith)
**Received:** 2026-02-28 14:00:00
**Urgent:** YES

URGENT: We need to process the payment today or there will be delays.

## Suggested Actions

- [ ] URGENT: Respond within 1 hour
- [ ] Check payment status immediately
- [ ] Reply with resolution timeline
- [ ] Escalate if cannot resolve
```

---

## Skill 4: WhatsApp Watcher Workflow

### Detection Workflow

```
┌─────────────────────────────────────────────────────────────┐
│           WHATSAPP WATCHER WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

1. Start Playwright MCP Server
   │
2. Open WhatsApp Web in browser
   │
3. Wait for page to load (auto-login if session exists)
   │
4. Find chat list element
   │
5. Identify unread messages
   │
6. For each unread message:
   │   ├── Extract sender info
   │   ├── Extract message text
   │   ├── Check for urgent keywords
   │   └── Create action file if new
   │
7. Mark message as processed (track in JSON file)
   │
8. Wait for next interval (30 seconds)
   │
9. Repeat from step 4
```

### Keyword Detection

```python
# Default urgent keywords
URGENT_KEYWORDS = [
    'urgent',
    'asap', 
    'immediately',
    'emergency',
    'invoice',
    'payment',
    'help',
    'as soon as possible'
]

# Custom keywords (via --keywords flag)
--keywords "quote,price,pricing,deadline"
```

---

## Skill 5: Process WhatsApp Tasks

### Workflow

```
1. WhatsApp Watcher detects new message
   │
2. Creates action file in /Needs_Action/
   │
3. Orchestrator picks up task
   │
4. Check message priority
   │
   ├── Urgent → Flag for immediate response
   │
   └── Normal → Process in queue
       │
       Check if reply needed
       │
       ├── Reply needed → Create approval request (new contact)
       │                  OR send directly (approved contact)
       │
       └── No reply needed → Archive with note
```

### Check WhatsApp Watcher Status

```bash
# View recent logs
type AI_Employee_Vault\Logs\watcher_WhatsAppWatcher_*.log

# Check processed messages
type AI_Employee_Vault\Logs\whatsapp_processed_ids.json

# View pending WhatsApp tasks
dir AI_Employee_Vault\Needs_Action\WHATSAPP_*.md
```

---

## Skill 6: Reply to WhatsApp Messages

### Reply via Playwright MCP

```bash
# Navigate to WhatsApp Web
mcp_call browser_navigate \
  --url "https://web.whatsapp.com"

# Get page snapshot
mcp_call browser_snapshot

# Search for contact
mcp_call browser_type \
  --ref "e10" \
  --element "Search input" \
  --text "John Doe"

# Click on chat
mcp_call browser_click \
  --ref "e25" \
  --element "John Doe chat"

# Type reply
mcp_call browser_type \
  --ref "e30" \
  --element "Message input" \
  --text "Hi John, thanks for your message. I'll get back to you shortly."

# Send message
mcp_call browser_click \
  --ref "e35" \
  --element "Send button"
```

### Reply Approval Template

```markdown
---
type: approval_request
action: whatsapp_reply
created: 2026-02-28T10:35:00
status: pending
risk_level: medium
---

# Approval Required

## Action Details
- **Action:** Send WhatsApp Reply
- **To:** +1234567890 (New Contact)
- **Chat:** John Doe - Client
- **Risk Level:** Medium (new contact)

## Reply Draft
```
Hi John, thanks for your message. I'll get back to you shortly.
```

## Why Approval is Required
Per Company Handbook Section 3.1:
"Messages to new contacts require human review"

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with a note.
```

---

## Error Handling

| Error | Response |
|-------|----------|
| WhatsApp Web not loading | Refresh page, retry 3 times |
| QR code required | Alert human to scan QR code |
| Session expired | Re-authenticate, save new session |
| Element not found | Update element refs via snapshot |
| Network timeout | Retry with exponential backoff |

---

## Best Practices

1. **Keep session data secure** - Contains authentication tokens
2. **Monitor for QR code** - Session may expire
3. **Check logs regularly** - Detect errors early
4. **Respect rate limits** - Don't poll too frequently (min 30 seconds)
5. **Backup session folder** - Avoid re-scanning QR code
6. **Test with personal number first** - Before business use

---

## Session Management

### Backup Session

```bash
# Backup WhatsApp session data
xcopy /E /I whatsapp_session whatsapp_session_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%
```

### Restore Session

```bash
# Restore from backup
xcopy /E /I whatsapp_session_backup_20260228 whatsapp_session
```

### Clear Session (Force Re-login)

```bash
# Delete session and re-authenticate
rmdir /S /Q whatsapp_session
mkdir whatsapp_session
# Then scan QR code again
```

---

## Quick Reference

```bash
# First-time setup (scan QR code)
npx @playwright/mcp@latest --port 8808 --shared-browser-context
# Navigate to https://web.whatsapp.com and scan QR

# Run watcher
python scripts\whatsapp_watcher.py --vault AI_Employee_Vault --interval 30

# Run with custom keywords
python scripts\whatsapp_watcher.py --vault AI_Employee_Vault --keywords "quote,price,deadline"

# Check status
type AI_Employee_Vault\Logs\watcher_WhatsAppWatcher_*.log

# View pending WhatsApp tasks
dir AI_Employee_Vault\Needs_Action\WHATSAPP_*.md
```

---

## WhatsApp vs Gmail Comparison

| Feature | Gmail Watcher | WhatsApp Watcher |
|---------|---------------|------------------|
| Check Interval | 2 minutes | 30 seconds |
| Urgency Detection | Subject/Snippet | Message content |
| Session Type | OAuth Token | Browser Session |
| Reply Method | Email MCP | Playwright MCP |
| Best For | Formal communication | Quick responses |

---

*AI Employee Skill v0.2.0 | Silver Tier*
