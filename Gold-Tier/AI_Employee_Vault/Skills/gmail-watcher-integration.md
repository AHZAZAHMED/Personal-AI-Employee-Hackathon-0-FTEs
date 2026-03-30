---
name: gmail-watcher-integration
description: |
  Monitor Gmail for new unread messages and create action files.
  Uses Gmail API to fetch emails and create actionable tasks in the vault.
  Use for email triage and response management.
---

# Gmail Watcher Integration

Monitor Gmail and create action files for new messages.

---

## When to Use

- Monitor business inbox for new inquiries
- Triage incoming emails automatically
- Create tasks from important emails
- Track email response times

---

## Prerequisites

1. **Google Cloud Project** with Gmail API enabled
2. **OAuth 2.0 Credentials** (credentials.json)
3. **Python Gmail API Client** installed

---

## Skill 1: Gmail API Setup

### Step 1: Create Google Cloud Project

```
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials.json
6. Place in: scripts/credentials.json
```

### Step 2: Install Dependencies

```bash
pip install google-api-python-client
pip install google-auth-httplib2
pip install google-auth-oauthlib
```

### Step 3: First-Time Authentication

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs
python scripts\gmail_watcher.py --vault AI_Employee_Vault --credentials scripts\credentials.json
```

This will:
- Open browser for OAuth consent
- Create token file at: `AI_Employee_Vault/.gmail_token.json`
- Start monitoring for new emails

---

## Skill 2: Run Gmail Watcher

### Continuous Monitoring

```bash
python scripts\gmail_watcher.py \
  --vault AI_Employee_Vault \
  --credentials scripts\credentials.json \
  --interval 120
```

**Options:**
- `--vault`: Path to Obsidian vault
- `--credentials`: Path to credentials.json
- `--interval`: Check every N seconds (default: 120)
- `--dry-run`: Log only, don't create files

### Run via Task Scheduler

```powershell
# Create Gmail Watcher task
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "scripts\gmail_watcher.py --vault AI_Employee_Vault --credentials scripts\credentials.json" `
  -WorkingDirectory "E:\Personal-AI-Employee-Hackathon-0-FTEs"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 2) `
  -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask `
  -TaskName "AI_Employee_Gmail_Watcher" `
  -Action $action `
  -Trigger $trigger `
  -Description "Monitor Gmail for new messages every 2 minutes"
```

---

## Skill 3: Action File Format

### Email Action File Template

```markdown
---
type: email
from: client@company.com
to: you@yourcompany.com
subject: Re: Pricing Inquiry
date: Fri, 28 Feb 2026 10:30:00 -0800
gmail_id: abc123xyz
priority: normal
is_urgent: false
created: 2026-02-28T10:31:00
status: pending
---

## Email Content

From: client@company.com
Subject: Re: Pricing Inquiry

Hi,

I'm interested in learning more about your pricing options.
Could you send me a quote for 10 users?

Thanks,
Client Name

## Suggested Actions

- [ ] Read full email content
- [ ] Determine if reply needed
- [ ] Draft response
- [ ] Send reply (approval required for new contacts)
- [ ] Archive after processing

---
*Created by AI Employee Gmail Watcher v0.2.0*
```

### Urgent Email Detection

Emails are marked urgent if subject or snippet contains:
- "urgent"
- "asap"
- "immediate"
- "emergency"
- "invoice"
- "payment"

```markdown
---
type: email
from: vendor@supplier.com
subject: URGENT: Payment Overdue
gmail_id: def456uvw
priority: high
is_urgent: true
---

## Email Content

[Email content]

## Suggested Actions

- [ ] URGENT: Respond within 24 hours
- [ ] Read full email content
- [ ] Check payment status
- [ ] Reply with resolution
```

---

## Skill 4: Process Email Tasks

### Workflow

```
1. Gmail Watcher detects new email
   │
2. Creates action file in /Needs_Action/
   │
3. Orchestrator picks up task
   │
4. Check if sender is approved contact
   │
   ├── Approved → Draft reply, send directly
   │
   └── New Contact → Create approval request
       │
       Human approves in /Approved/
       │
       Send reply via email MCP
```

### Check Gmail Watcher Status

```bash
# View recent logs
type AI_Employee_Vault\Logs\watcher_GmailWatcher_*.log

# Check processed emails
type AI_Employee_Vault\Logs\gmail_processed_ids.json

# View action files created
dir AI_Employee_Vault\Needs_Action\EMAIL_*.md
```

---

## Skill 5: Contact Approval List

### Maintain Approved Contacts

Create `/Company_Handbook_Appendix_Contacts.md`:

```markdown
# Approved Email Contacts

These contacts can receive auto-approved replies:

| Email | Name | Company | Approved Date |
|-------|------|---------|---------------|
| existing@client.com | John Doe | Client Corp | 2026-01-15 |
| partner@vendor.com | Jane Smith | Vendor Inc | 2026-02-01 |
```

### Check Contact Status

```
Read task file frontmatter
Get "from" field
Search /Company_Handbook_Appendix_Contacts.md
If found → Auto-approve reply
If not found → Create approval request
```

---

## Error Handling

| Error | Response |
|-------|----------|
| Credentials not found | Alert human, provide setup link |
| Token expired | Re-authenticate automatically |
| Gmail API quota exceeded | Wait 1 hour, retry |
| Network error | Retry 3 times, then log error |

---

## Best Practices

1. **Check logs daily** for errors
2. **Review urgent emails** within 24 hours
3. **Update approved contacts** list regularly
4. **Archive processed emails** to keep inbox clean
5. **Monitor API quota** usage in Google Cloud Console

---

## Quick Reference

```bash
# First-time setup
python scripts\gmail_watcher.py --vault AI_Employee_Vault --credentials scripts\credentials.json

# Run watcher
python scripts\gmail_watcher.py --vault AI_Employee_Vault --interval 120

# Check status
type AI_Employee_Vault\Logs\watcher_GmailWatcher_*.log

# View pending email tasks
dir AI_Employee_Vault\Needs_Action\EMAIL_*.md
```

---

*AI Employee Skill v0.2.0 | Silver Tier*
