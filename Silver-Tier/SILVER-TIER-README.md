# AI Employee - Silver Tier Implementation

**Personal AI Employee Hackathon 0** - Building Autonomous FTEs in 2026

---

## Overview

Silver Tier extends Bronze Tier with advanced automation capabilities:

- ✅ **Two or more Watcher scripts** (File System + Gmail)
- ✅ **Automatically Post on LinkedIn** about business updates
- ✅ **Plan.md generation** for complex tasks
- ✅ **Gmail API integration** for external actions
- ✅ **Human-in-the-loop approval workflow** for sensitive actions
- ✅ **Basic scheduling** via Windows Task Scheduler
- ✅ **All AI functionality as Agent Skills** (in `/Skills/`)

---

## What's New in Silver Tier

### Compared to Bronze Tier

| Feature | Bronze | Silver |
|---------|--------|--------|
| Watchers | 1 (File System) | 2+ (File System + Gmail) |
| Task Planning | Basic | Detailed Plan.md files |
| External Actions | None | Email + LinkedIn via Gmail API |
| Approval Workflow | Basic | Full HITL with folders |
| Scheduling | Manual | Windows Task Scheduler |
| Skills Documentation | 1 file | 7 files |

---

## Project Structure

```
E:\Personal-AI-Employee-Hackathon-0-FTEs\
├── scripts/
│   ├── base_watcher.py         # Base class for all watchers
│   ├── filesystem_watcher.py   # Bronze: File system monitoring
│   ├── gmail_watcher.py        # Silver: Gmail monitoring
│   ├── orchestrator.py         # Task coordination
│   ├── task_processor.py       # Task execution
│   ├── linkedin_poster.py      # Silver: LinkedIn posting
│   └── Create-SilverTier-Tasks.ps1  # Task Scheduler setup
├── credentails.json            # Gmail API credentials
├── AI_Employee_Vault/
│   ├── Skills/
│   │   ├── vault-operations.md        # Bronze skill
│   │   ├── task-plan-generation.md    # Silver: Plans
│   │   ├── human-approval-workflow.md # Silver: Approval
│   │   ├── gmail-api-integration.md   # Silver: Email (updated skill)
│   │   ├── linkedin-auto-posting.md   # Silver: LinkedIn
│   │   ├── scheduled-operations.md    # Silver: Scheduling
│   │   └── gmail-watcher-integration.md # Silver: Gmail
│   ├── Needs_Action/
│   ├── In_Progress/qwen_agent/
│   ├── Plans/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Rejected/
│   ├── Done/
│   └── Logs/
```

---

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13+ | Watcher scripts |
| Node.js | v24+ LTS | Playwright for LinkedIn |
| Gmail API | Enabled | Email monitoring & sending |
| Playwright | Latest | LinkedIn posting |

### Install Dependencies

```bash
# For Gmail Watcher
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# For LinkedIn Poster (Playwright Direct - No MCP needed!)
pip install playwright
playwright install chromium
```

---

## Quick Start

### 1. Verify Gmail Credentials

```bash
# Check credentials file exists
dir credentails.json
```

### 2. First-Time Gmail Authentication

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs
python scripts\gmail_watcher.py --vault AI_Employee_Vault
```

This will:
- Open browser for OAuth consent
- Create token file at: `AI_Employee_Vault/.gmail_token.json`
- Start monitoring Gmail

### 3. First-Time LinkedIn Login

```bash
# Install Playwright and Chromium
pip install playwright
playwright install chromium

# Login to LinkedIn (saves session)
python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only
```

This will:
- Open Chromium browser
- Navigate to LinkedIn
- You log in manually
- Session saved to `linkedin_browser_session/`
- Press Ctrl+C to save and exit

### 4. Set Up Scheduled Tasks

```powershell
# Run as Administrator
cd E:\Personal-AI-Employee-Hackathon-0-FTEs
powershell -ExecutionPolicy Bypass -File scripts\Create-SilverTier-Tasks.ps1
```

---

## Usage Examples

### Example 1: Monitor Gmail

```bash
# Run Gmail Watcher (checks every 2 minutes)
python scripts\gmail_watcher.py --vault AI_Employee_Vault --interval 120

# Dry run (log only)
python scripts\gmail_watcher.py --vault AI_Employee_Vault --dry-run
```

**What happens:**
1. Connects to Gmail API
2. Checks for unread messages
3. Creates action files in `/Needs_Action/` for new emails
4. Marks urgent emails (invoice, payment, asap) as high priority

### Example 2: Post to LinkedIn

```bash
# First time: Install Playwright and login
pip install playwright
playwright install chromium
python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only

# Create a post draft
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "Excited to announce our Q1 2026 growth! #business #milestone" ^
  --type milestone

# Review and approve (move file to /Approved/)
# Then execute:
python scripts\linkedin_poster.py --vault AI_Employee_Vault
```

**What happens:**
1. Creates draft in `/Pending_Approval/`
2. Human reviews and moves to `/Approved/`
3. LinkedIn Poster launches Chromium (with saved session)
4. Posts to LinkedIn automatically
5. Saves screenshot to `/Screenshots/`

### Example 3: Process Tasks with Plans

```bash
# Run orchestrator (creates Plan.md for complex tasks)
python scripts\orchestrator.py --vault AI_Employee_Vault --once
```

**What happens:**
1. Reads tasks from `/Needs_Action/`
2. Creates detailed Plan.md in `/Plans/`
3. Executes auto-approved tasks
4. Creates approval requests for sensitive tasks
5. Moves completed to `/Done/`

---

## Gmail Watcher

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--vault` | Required | Path to Obsidian vault |
| `--credentials` | `credentails.json` | Gmail API credentials |
| `--interval` | 120 | Check interval (seconds) |

### Urgent Keywords

Emails are marked urgent if they contain:
- urgent, asap, immediate, emergency
- invoice, payment, help

### Action File Format

```markdown
---
type: email
from: client@example.com
subject: Pricing Inquiry
gmail_id: abc123
priority: normal
is_urgent: false
---

## Email Content

From: client@example.com
Subject: Pricing Inquiry

[Email body]

## Suggested Actions

- [ ] Read full email content
- [ ] Determine if reply needed
- [ ] Draft response
- [ ] Send reply (approval for new contacts)
```

---

## LinkedIn Poster

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--vault` | Required | Path to Obsidian vault |
| `--create` | - | Create post draft with content |
| `--type` | `announcement` | Post type (announcement, milestone, update, client_win) |
| `--visible` | (headless) | Show browser window during posting |
| `--login-only` | - | Just open LinkedIn for login |

### Installation (First Time)

```bash
# Install Playwright and Chromium
pip install playwright
playwright install chromium

# Login to LinkedIn (saves session)
python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only
```

### Post Types

- `announcement` - General business announcement
- `milestone` - Company milestone/achievement
- `update` - Business update
- `client_win` - New client announcement

### Approval Workflow

```
1. Create draft → /Pending_Approval/
2. Human reviews → Move to /Approved/
3. Poster executes → Posts to LinkedIn (using saved session)
4. Move to /Done/ with screenshot
```

---

## Human-in-the-Loop Approval

### When Approval is Required

| Action | Approval Required |
|--------|-------------------|
| Email to new contact | ✅ Yes |
| Email to approved contact | ❌ No |
| LinkedIn post | ✅ Yes |
| Payment | ✅ Yes |
| File categorization | ❌ No |

### Approval Folders

```
/Pending_Approval/  → Awaiting human decision
/Approved/          → Approved, ready to execute
/Rejected/          → Rejected by human
/Done/              → Executed or archived
```

### Approve an Action

```bash
# Manual approval (using file explorer)
1. Open AI_Employee_Vault/Pending_Approval/
2. Review the action file
3. Move to ../Approved/ to approve
4. Or move to ../Rejected/ to reject
```

---

## Scheduled Tasks

### Tasks Created

| Task Name | Frequency | Purpose |
|-----------|-----------|---------|
| AI_Employee_Gmail_Watcher | Every 2 min | Monitor Gmail |
| AI_Employee_Orchestrator | Every 1 hour | Process tasks |
| AI_Employee_Daily_Briefing | Daily 8 AM | Generate briefing |
| AI_Employee_LinkedIn_Poster | Every 30 min | Post approved content |

### Manage Tasks

```powershell
# View all tasks
Get-ScheduledTask -TaskName "AI_Employee_*"

# View task status
Get-ScheduledTaskInfo -TaskName "AI_Employee_Gmail_Watcher"

# Run task manually
Start-ScheduledTask -TaskName "AI_Employee_Gmail_Watcher"

# Delete all tasks
Get-ScheduledTask -TaskName "AI_Employee_*" | Unregister-ScheduledTask
```

---

## Testing Silver Tier

### Test Checklist

- [ ] Gmail Watcher detects new emails
- [ ] Action files created in `/Needs_Action/`
- [ ] Orchestrator creates Plan.md files
- [ ] Approval workflow functional
- [ ] LinkedIn Poster posts successfully
- [ ] Scheduled tasks running

### Run All Tests

```bash
# 1. Test Gmail Watcher (dry run)
python scripts\gmail_watcher.py --vault AI_Employee_Vault --dry-run

# 2. Test Orchestrator
python scripts\orchestrator.py --vault AI_Employee_Vault --once

# 3. Test LinkedIn Poster
python scripts\linkedin_poster.py --vault AI_Employee_Vault

# 4. Check logs
type AI_Employee_Vault\Logs\*.jsonl
```

---

## Troubleshooting

### Gmail Watcher Issues

**Problem:** "Credentials file not found"
```
Solution: Ensure credentails.json exists in project root
```

**Problem:** "Token expired"
```
Solution: Delete AI_Employee_Vault/.gmail_token.json and re-authenticate
```

**Problem:** "No new emails detected"
```
Solution: Check Gmail API is enabled in Google Cloud Console
```

### LinkedIn Poster Issues

**Problem:** "Playwright not installed"
```
Solution: Install Playwright and Chromium
  pip install playwright
  playwright install chromium
```

**Problem:** "Not logged in" or "Login page appears"
```
Solution: Re-login to LinkedIn
  python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only

Log in manually in the browser window, then press Ctrl+C to save session.
```

**Problem:** "Post button not found"
```
Solution: Run with --visible to see what's happening
  python scripts\linkedin_poster.py --vault AI_Employee_Vault --visible

Then check the output for clues about what's different.
```

**Problem:** "Browser doesn't close" or "Hangs"
```
Solution: Kill stuck Python processes
  taskkill /F /IM python.exe

Then clear session and re-login:
  rmdir /S /Q linkedin_browser_session
  python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only
```

### Scheduled Task Issues

**Problem:** Task not running
```
Solution: Check Task Scheduler history for errors
  Get-ScheduledTaskInfo -TaskName "AI_Employee_*"
```

---

## Silver Tier vs Hackathon Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 2+ Watcher scripts | ✅ | File System + Gmail |
| LinkedIn auto-posting | ✅ | linkedin_poster.py |
| Plan.md generation | ✅ | orchestrator.py |
| External action integration | ✅ | Gmail API + Playwright |
| HITL approval workflow | ✅ | /Approved/, /Rejected/ folders |
| Windows Task Scheduler | ✅ | Create-SilverTier-Tasks.ps1 |
| Agent Skills documentation | ✅ | 7 skill files in /Skills/ |

---

## Next Steps (Gold Tier)

To advance to Gold Tier, add:

1. **Odoo Accounting Integration** - Self-hosted ERP
2. **Facebook/Instagram Integration** - Social media posting
3. **Twitter (X) Integration** - Tweet posting
4. **Weekly CEO Briefing** - Comprehensive audit
5. **Ralph Wiggum Loop** - Persistent agent execution

---

## Support

- **Weekly Meeting:** Wednesdays 10:00 PM PKT on Zoom
- **Zoom Link:** https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1
- **YouTube:** https://www.youtube.com/@panaversity

---

*AI Employee Silver Tier v0.2.0 | Built for Qwen Code*
