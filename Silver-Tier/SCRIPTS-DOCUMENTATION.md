# Silver Tier - Scripts Documentation

## ✅ Production Scripts (Keep)

These are the **ONLY** scripts needed for Silver Tier functionality.

---

### Core Scripts

| Script | Purpose | Required For |
|--------|---------|--------------|
| `base_watcher.py` | Base class for all watchers | Gmail + File System Watchers |
| `filesystem_watcher.py` | Monitors folder for new files | Bronze + Silver Tier |
| `gmail_watcher.py` | Monitors Gmail for new emails | Silver Tier |
| `orchestrator.py` | Main task coordinator | Silver Tier |
| `approval_handler.py` | Manages approval workflow | Silver Tier |
| `plan_generator.py` | Creates Plan.md files | Silver Tier |
| `task_processor.py` | Processes tasks (fallback) | Bronze + Silver Tier |

### MCP/Email Scripts

| Script | Purpose | Required For |
|--------|---------|--------------|
| `email_sender_mcp.py` | Sends emails via Gmail API | Silver Tier |

### LinkedIn Scripts

| Script | Purpose | Required For |
|--------|---------|--------------|
| `linkedin_poster.py` | Posts to LinkedIn via Playwright | Silver Tier |

### Setup Scripts

| Script | Purpose | Required For |
|--------|---------|--------------|
| `Create-SilverTier-Tasks.ps1` | Windows Task Scheduler setup | Silver Tier |

---

## ❌ Removed Scripts (Duplicates/Tests)

These scripts were removed to clean up the project:

| Script | Reason for Removal |
|--------|-------------------|
| `email_sender.py` | Old version, replaced by `email_sender_mcp.py` |
| `linkedin_post_working.py` | Test version, duplicate of `linkedin_poster.py` |
| `linkedin_test_post.py` | Test version, duplicate |
| `linkedin_diagnose.py` | Diagnostic tool, not needed in production |
| `test_gmail.py` | Test script, not needed |
| `test_silver_tier.py` | Test script, not needed |
| `run_complete_flow.py` | Test script, not needed |

---

## Script Functions

### base_watcher.py
**Purpose:** Abstract base class for all watcher scripts

**Key Classes:**
- `BaseWatcher` - Base class with common functionality

**Used By:**
- `gmail_watcher.py`
- `filesystem_watcher.py`

---

### filesystem_watcher.py
**Purpose:** Monitor a folder for new files and create action files

**Key Features:**
- Watches folder for new files
- Creates action files in `/Needs_Action/`
- Tracks processed files to avoid duplicates
- Moves files to `/Inbox/` after processing

**Usage:**
```bash
python scripts/filesystem_watcher.py --vault AI_Employee_Vault --watch <folder>
```

---

### gmail_watcher.py
**Purpose:** Monitor Gmail for new unread emails

**Key Features:**
- Connects to Gmail API
- Detects new unread emails
- Creates action files in `/Needs_Action/`
- Detects urgent keywords (invoice, payment, asap)
- Tracks processed message IDs

**Usage:**
```bash
python scripts/gmail_watcher.py --vault AI_Employee_Vault --interval 120
```

---

### orchestrator.py
**Purpose:** Main task coordinator for Silver Tier

**Key Features:**
- Reads tasks from `/Needs_Action/`
- Creates Plan.md files for complex tasks
- Creates approval requests for sensitive actions
- Moves tasks through workflow
- Updates Dashboard.md

**Usage:**
```bash
python scripts/orchestrator.py --vault AI_Employee_Vault --once
```

---

### approval_handler.py
**Purpose:** Manage human-in-the-loop approval workflow

**Key Features:**
- Creates approval requests
- Processes approved actions
- Archives rejected actions
- Executes email sending after approval

**Usage:**
```bash
python scripts/approval_handler.py --vault AI_Employee_Vault
```

---

### plan_generator.py
**Purpose:** Generate detailed Plan.md files for tasks

**Key Features:**
- Creates plans for emails, payments, social media
- Tracks step-by-step progress
- Archives completed plans

**Usage:**
```bash
python scripts/plan_generator.py --vault AI_Employee_Vault --task <task_file>
```

---

### task_processor.py
**Purpose:** Process tasks and categorize content

**Key Features:**
- Categorizes files by content
- Analyzes keywords
- Moves tasks to Done folder

**Usage:**
```bash
python scripts/task_processor.py --vault AI_Employee_Vault
```

---

### email_sender_mcp.py
**Purpose:** Send emails via Gmail API

**Key Features:**
- Integrates with Gmail API directly
- Professional email templates
- Logs all sent emails

**Usage:**
```bash
python scripts/email_sender_mcp.py --vault AI_Employee_Vault --send "email@example.com" --subject "Test" --body "Message"
```

---

### linkedin_poster.py
**Purpose:** Post to LinkedIn automatically

**Key Features:**
- Uses Playwright for browser automation
- Saves LinkedIn session
- Requires human approval before posting
- Takes screenshots for audit trail

**Usage:**
```bash
# First time login
python scripts/linkedin_poster.py --vault AI_Employee_Vault --login-only

# Post (after approval)
python scripts/linkedin_poster.py --vault AI_Employee_Vault
```

---

### Create-SilverTier-Tasks.ps1
**Purpose:** Set up Windows Task Scheduler tasks

**Key Features:**
- Creates scheduled tasks for:
  - Gmail Watcher (every 2 min)
  - Orchestrator (every hour)
  - Daily Briefing (8 AM daily)
  - LinkedIn Poster (every 30 min)

**Usage:**
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts/Create-SilverTier-Tasks.ps1
```

---

## Complete Silver Tier Flow

```
1. Gmail Watcher detects new email
   ↓
2. Creates action file in /Needs_Action/
   ↓
3. Orchestrator picks up task
   ↓
4. Plan Generator creates Plan.md
   ↓
5. Approval Handler creates approval request
   ↓
6. Human approves (moves to /Approved/)
   ↓
7. Email Sender sends email via Gmail API
   ↓
8. Task moved to /Done/
   ↓
9. Dashboard updated
```

---

## File Count Summary

| Category | Count |
|----------|-------|
| Production Scripts | 10 |
| Removed (duplicates/tests) | 7 |
| **Total Clean Scripts** | **10** |

---

*Silver Tier Scripts | Cleaned & Organized*
