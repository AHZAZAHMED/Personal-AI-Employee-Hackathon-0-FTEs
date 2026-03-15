# AI Employee - Bronze Tier Implementation

**Personal AI Employee Hackathon 0** - Building Autonomous FTEs in 2026

---

## Overview

This is the **Bronze Tier** implementation of the Personal AI Employee system. It provides the foundational layer for an AI-powered assistant that:

- Monitors a folder for new files
- Processes tasks using Qwen Code
- Maintains an Obsidian vault as the knowledge base and dashboard
- Follows rules defined in a Company Handbook
- Requests human approval for sensitive actions

---

## What's Included

### 📁 Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status dashboard
├── Company_Handbook.md       # Rules and boundaries
├── Business_Goals.md         # Objectives and metrics
├── Inbox/                    # Processed files storage
├── Needs_Action/             # Pending tasks
├── In_Progress/qwen_agent/   # Tasks being processed
├── Plans/                    # Task plans
├── Pending_Approval/         # Awaiting human decision
├── Approved/                 # Approved actions
├── Rejected/                 # Declined actions
├── Done/                     # Completed tasks
├── Logs/                     # Activity logs
├── Briefings/                # Daily/weekly summaries
└── Skills/                   # Qwen Code skill definitions
```

### 📜 Python Scripts

| Script | Purpose |
|--------|---------|
| `scripts/base_watcher.py` | Base class for all watchers |
| `scripts/filesystem_watcher.py` | Monitors folder for new files |
| `scripts/orchestrator.py` | Coordinates task processing |

### 📚 Documentation

| File | Purpose |
|------|---------|
| `AI_Employee_Vault/Skills/vault-operations.md` | Qwen Code skill definitions |
| `QWEN.md` | Project context and reference |

---

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13+ | Watcher scripts |
| Qwen Code | Latest | AI reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base (optional for viewing) |

---

## Quick Start

### 1. Verify Python Installation

```bash
python --version
# Should show Python 3.13 or higher
```

### 2. Test the File System Watcher (Dry Run)

```bash
# Navigate to project root
cd E:\Personal-AI-Employee-Hackathon-0-FTEs

# Create a test drop folder
mkdir test_drop

# Drop a test file
echo "Test content" > test_drop/test_file.txt

# Run watcher in dry-run mode
python scripts/filesystem_watcher.py --vault AI_Employee_Vault --watch test_drop --dry-run
```

### 3. Run the File System Watcher

```bash
# Start the watcher (monitors test_drop folder)
python scripts/filesystem_watcher.py --vault AI_Employee_Vault --watch test_drop
```

**What happens:**
- Watches `test_drop` folder for new files
- When a file is added, creates an action file in `AI_Employee_Vault/Needs_Action/`
- Moves the original file to `AI_Employee_Vault/Inbox/`

### 4. Run the Orchestrator (Single Cycle)

```bash
# Process pending tasks once
python scripts/orchestrator.py --vault AI_Employee_Vault --once
```

**What happens:**
- Reads all files in `/Needs_Action`
- Moves them to `/In_Progress/qwen_agent/`
- Would trigger Qwen Code to process (if available)
- Updates Dashboard.md with current stats

### 5. Run the Orchestrator (Continuous)

```bash
# Start continuous monitoring (checks every 60 seconds)
python scripts/orchestrator.py --vault AI_Employee_Vault --interval 60
```

---

## Usage Examples

### Example 1: Process a Dropped File

```bash
# 1. Start the file watcher in one terminal
python scripts/filesystem_watcher.py --vault AI_Employee_Vault --watch test_drop

# 2. In another terminal, drop a file
echo "Invoice data here" > test_drop/invoice_jan.txt

# 3. Watcher creates action file in Needs_Action/
# 4. Orchestrator picks it up and processes
```

### Example 2: Manual Task Creation

Create a task file directly in `Needs_Action/`:

```bash
cat > AI_Employee_Vault/Needs_Action/TASK_review_document.md << 'EOF'
---
type: manual_task
created: 2026-02-26T10:00:00Z
status: pending
priority: high
---

## Task

Review the document in /Inbox/report.pdf and summarize key points.

## Suggested Actions

- [ ] Read the document
- [ ] Extract key information
- [ ] Create summary
- [ ] File in appropriate folder
EOF
```

Then run the orchestrator to process it.

---

## Configuration

### File System Watcher Options

```bash
python scripts/filesystem_watcher.py \
  --vault AI_Employee_Vault \      # Required: Vault path
  --watch /path/to/watch \         # Required: Folder to monitor
  --interval 30 \                  # Optional: Check interval (default: 30)
  --dry-run \                      # Optional: Log only, no actions
  --no-move                        # Optional: Don't move files to vault
```

### Orchestrator Options

```bash
python scripts/orchestrator.py \
  --vault AI_Employee_Vault \      # Required: Vault path
  --qwen-cmd qwen \                # Optional: Qwen Code command (default: qwen)
  --interval 60 \                  # Optional: Check interval (default: 60)
  --once                           # Optional: Run once and exit
```

---

## Testing the Bronze Tier

### Test Checklist

- [ ] Vault folders exist
- [ ] Dashboard.md is readable
- [ ] Company_Handbook.md defines rules
- [ ] File watcher detects new files
- [ ] Action files are created in `/Needs_Action/`
- [ ] Orchestrator moves files to `/In_Progress/`
- [ ] Dashboard.md stats update correctly
- [ ] Logs are written to `/Logs/`

### Run All Tests

```bash
# 1. Verify vault structure
python -c "
from pathlib import Path
vault = Path('AI_Employee_Vault')
folders = ['Inbox', 'Needs_Action', 'In_Progress', 'Plans', 
           'Pending_Approval', 'Approved', 'Rejected', 'Done', 'Logs']
for f in folders:
    assert (vault / f).exists(), f'Missing: {f}'
print('✓ All vault folders exist')
"

# 2. Test watcher import
python -c "
import sys
sys.path.insert(0, 'scripts')
from base_watcher import BaseWatcher
from filesystem_watcher import FileSystemWatcher
print('✓ Watcher modules import successfully')
"

# 3. Test orchestrator import
python -c "
import sys
sys.path.insert(0, 'scripts')
from orchestrator import Orchestrator
print('✓ Orchestrator module imports successfully')
"

# 4. Verify key files exist
python -c "
from pathlib import Path
vault = Path('AI_Employee_Vault')
files = ['Dashboard.md', 'Company_Handbook.md', 'Business_Goals.md']
for f in files:
    assert (vault / f).exists(), f'Missing: {f}'
print('✓ All key vault files exist')
"
```

---

## File Formats

### Action File Format

```markdown
---
type: file_drop
original_name: document.pdf
size_bytes: 1024
created: 2026-02-26T10:00:00Z
status: pending
priority: normal
---

## Item Content

*File: `document.pdf` (1.00 KB)*

## Suggested Actions

- [ ] Review file content
- [ ] Determine required action
- [ ] File or archive after processing
```

### Approval Request Format

```markdown
---
type: approval_request
action: file_review
created: 2026-02-26T10:00:00Z
status: pending
---

# Approval Required

## Action Details
- **Action:** Review and categorize document
- **Reason:** New file dropped for processing
- **Risk Level:** Low

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.
```

---

## Troubleshooting

### Issue: "Module not found" error

**Solution:** Ensure you're running from the project root:
```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs
python scripts/filesystem_watcher.py ...
```

### Issue: Watcher doesn't detect files

**Solution:** 
1. Check the watch folder path is correct
2. Verify file permissions
3. Check watcher logs in `/Logs/`

### Issue: Orchestrator doesn't process tasks

**Solution:**
1. Ensure task files are in `/Needs_Action/`
2. Check file extension is `.md`
3. Review orchestrator logs

### Issue: Dashboard not updating

**Solution:**
1. Verify Dashboard.md exists
2. Check file permissions allow writing
3. Run orchestrator with `--once` to test

---

## Next Steps (Silver Tier)

To advance to Silver Tier, add:

1. **Gmail Watcher** - Monitor Gmail for new emails
2. **WhatsApp Watcher** - Monitor WhatsApp messages (using Playwright)
3. **Plan Generation** - Auto-create detailed plans for tasks
4. **MCP Server** - Integrate one external action (e.g., send email)
5. **Scheduling** - Set up cron/Task Scheduler for automated runs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE TIER                               │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ File System  │────▶│  Orchestrator │────▶│  Qwen Code   │
│   Watcher    │     │   (Python)    │     │  (Processing)│
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                    ┌─────────────────────────────────────┐
                    │         Obsidian Vault              │
                    │  ┌─────────────────────────────┐    │
                    │  │ Dashboard.md                │    │
                    │  │ Company_Handbook.md         │    │
                    │  │ Business_Goals.md           │    │
                    │  │ Needs_Action/               │    │
                    │  │ In_Progress/                │    │
                    │  │ Done/                       │    │
                    │  └─────────────────────────────┘    │
                    └─────────────────────────────────────┘
```

---

## License

This project is part of the Personal AI Employee Hackathon 0.

---

*AI Employee Bronze Tier v0.1.0 | Built for Qwen Code*
