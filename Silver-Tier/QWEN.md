# Personal AI Employee Hackathon 0 - QWEN.md

## Project Overview

This repository is a **hackathon project** for building a "Personal AI Employee" (Digital FTE - Full-Time Equivalent). It's a local-first, agent-driven automation system where an AI agent (powered by **Qwen Code**) proactively manages personal and business affairs 24/7 using Obsidian as the management dashboard.

### Core Concept

The system transforms Qwen Code from a chatbot into a **proactive business partner** that:
- Monitors Gmail, WhatsApp, and filesystems via "Watcher" scripts
- Uses Obsidian Markdown files as long-term memory and GUI
- Takes actions through MCP (Model Context Protocol) servers
- Requires human-in-the-loop approval for sensitive operations (payments, emails to new contacts)

### Architecture Layers

| Layer | Components | Purpose |
|-------|------------|---------|
| **Perception** | Gmail Watcher, WhatsApp Watcher, File System Watcher (Python scripts) | Monitor external inputs, create action files in `/Needs_Action/` |
| **Memory/GUI** | Obsidian Vault (Dashboard.md, Company_Handbook.md, Business_Goals.md) | Local-first knowledge base and status dashboard |
| **Reasoning** | Qwen Code (with persistence loop for multi-step tasks) | Read tasks, create plans, request approvals |
| **Action** | MCP Servers (Email, Browser/Playwright, Payment, Calendar) | Execute external actions |
| **Orchestration** | Orchestrator.py, Watchdog.py | Schedule tasks, manage processes, health monitoring |

### Key Features

- **Monday Morning CEO Briefing**: Autonomous weekly audit generating revenue reports and bottleneck analysis
- **Human-in-the-Loop (HITL)**: File-based approval workflow (`/Pending_Approval/` → `/Approved/` → `/Rejected/`)
- **Ralph Wiggum Loop**: Stop hook pattern that keeps Qwen Code iterating until tasks are complete
- **Watcher Architecture**: Lightweight Python daemons that "wake up" Qwen Code when events occur

## Project Structure

```
E:\Personal-AI-Employee-Hackathon-0-FTEs\
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md  # Main blueprint (1201 lines)
├── README.md                       # Minimal readme
├── skills-lock.json                # Skill dependencies (browsing-with-playwright)
├── QWEN.md                         # This file
└── .qwen/
    └── skills/
        └── browsing-with-playwright/
            ├── SKILL.md            # Playwright MCP usage guide
            ├── references/
            │   └── playwright-tools.md
            └── scripts/
                ├── mcp-client.py   # MCP client for browser automation
                ├── start-server.sh
                ├── stop-server.sh
                └── verify.py
```

## Obsidian Vault Structure (To Be Created)

The hackathon requires creating an Obsidian vault with this structure:

```
Vault/
├── Dashboard.md              # Real-time status summary
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Q1/Q2 objectives and metrics
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Items awaiting processing
├── In_Progress/<agent>/      # Claimed items (prevents double-work)
├── Plans/                    # Generated plan files
├── Pending_Approval/         # Awaiting human decision
├── Approved/                 # Approved actions ready to execute
├── Rejected/                 # Declined actions
├── Done/                     # Completed tasks
├── Logs/                     # YYYY-MM-DD.json audit logs
├── Accounting/               # Bank transactions, invoices
└── Briefings/                # CEO briefing reports
```

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Qwen Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts, orchestration |
| Node.js | v24+ LTS | MCP servers |
| GitHub Desktop | Latest | Version control |

### Setup Commands

```bash
# 1. Create Obsidian vault
mkdir AI_Employee_Vault
cd AI_Employee_Vault

# 2. Create folder structure
mkdir -p Inbox Needs_Action In_Progress Plans Pending_Approval Approved Rejected Done Logs Accounting Briefings

# 3. Install Playwright MCP (for browser automation)
npm install -g @playwright/mcp

# 4. Start Playwright MCP server
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# 5. Verify server
python3 .qwen/skills/browsing-with-playwright/scripts/verify.py

# 6. Configure MCP servers in ~/.config/qwen-code/mcp.json
```

### Running Watchers (Daemon Mode)

```bash
# Using PM2 (recommended for production)
npm install -g pm2
pm2 start gmail_watcher.py --interpreter python3
pm2 start whatsapp_watcher.py --interpreter python3
pm2 start orchestrator.py --interpreter python3
pm2 save
pm2 startup

# Or using Python watchdog pattern
python watchdog.py  # Monitors and restarts failed processes
```

### Scheduled Operations

```bash
# Linux/Mac: Daily briefing at 8 AM
crontab -e
# Add: 0 8 * * * qwen --cwd /path/to/vault "Generate Monday Morning CEO Briefing"

# Windows: Task Scheduler
# Create task: Trigger = Daily 8:00 AM, Action = qwen.exe --cwd "E:\Vault" "Generate briefing"
```

## Development Conventions

### Coding Style

- **Python**: Use type hints, follow PEP 8, include docstrings for watcher classes
- **Markdown**: Use YAML frontmatter for all action files (type, status, timestamps)
- **Logging**: JSON format with timestamp, action_type, actor, target, parameters, approval_status, result

### Testing Practices

- **Dry Run Mode**: All action scripts support `--dry-run` flag
- **Dev Mode**: `DEV_MODE=true` prevents real external actions
- **Sandbox Accounts**: Use test accounts for Gmail, banking during development

### Security Rules

1. **Never commit credentials**: Use `.env` files (added to `.gitignore`)
2. **Environment variables**: `export GMAIL_API_KEY="your-key"`
3. **Secrets manager**: Use macOS Keychain, Windows Credential Manager, or 1Password CLI
4. **Audit logging**: Log every action to `/Vault/Logs/YYYY-MM-DD.json`
5. **HITL for sensitive actions**: Payments >$100, new payees, bulk emails require approval

### File Naming Conventions

```
/Needs_Action/EMAIL_<message_id>.md
/Needs_Action/WHATSAPP_<contact>_<date>.md
/Plans/PLAN_<objective>_<date>.md
/Pending_Approval/<ACTION>_<description>_<date>.md
Logs/YYYY-MM-DD.json
Briefings/YYYY-MM-DD_Briefing.md
```

## Achievement Tiers

| Tier | Time | Requirements |
|------|------|--------------|
| **Bronze** | 8-12h | Obsidian dashboard, 1 watcher, Qwen Code reading/writing to vault, basic folder structure |
| **Silver** | 20-30h | 2+ watchers, Plan.md generation, 1 MCP server, HITL workflow, basic scheduling |
| **Gold** | 40+h | Full integration, Odoo accounting, social media integration, weekly audit, Ralph Wiggum loop |
| **Platinum** | 60+h | Cloud deployment (24/7), Cloud/Local split, vault sync, Odoo on VM, A2A upgrade |

## Key Commands Reference

### Playwright MCP (Browser Automation)

```bash
# Start/Stop server
bash scripts/start-server.sh
bash scripts/stop-server.sh

# Navigate
python3 scripts/mcp-client.py call -u http://localhost:8808 -t browser_navigate -p '{"url": "https://example.com"}'

# Get page state (accessibility snapshot)
python3 scripts/mcp-client.py call -u http://localhost:8808 -t browser_snapshot -p '{}'

# Click/type using element refs
python3 scripts/mcp-client.py call -u http://localhost:8808 -t browser_click -p '{"element": "Submit", "ref": "e42"}'
python3 scripts/mcp-client.py call -u http://localhost:8808 -t browser_type -p '{"element": "Search", "ref": "e15", "text": "query", "submit": true}'
```

### Ralph Wiggum Loop (Persistence)

```bash
# Start Ralph loop (keeps Qwen Code working until task complete)
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Qwen Code "command not found" | Install Qwen Code CLI, ensure PATH is configured, restart terminal |
| Watcher scripts stop overnight | Use PM2 or supervisord for process management |
| Gmail API 403 Forbidden | Enable Gmail API in Google Cloud Console, verify OAuth consent |
| MCP server won't connect | Check server is running (`ps aux | grep mcp`), verify absolute path in mcp.json |
| Element click fails | Run `browser_snapshot` first to get current element refs |

## Learning Resources

### Prerequisites (Before Hackathon)
- [Qwen Code Fundamentals](https://agentfactory.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)
- [Obsidian Fundamentals](https://help.obsidian.md/Getting+started)
- [Agent Skills Documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Introduction](https://modelcontextprotocol.io/introduction)

### Core Learning (During Hackathon)
- [Qwen Code + Obsidian Integration](https://www.youtube.com/watch?v=sCIS05Qt79Y)
- [Building MCP Servers](https://modelcontextprotocol.io/quickstart)
- [Gmail API Setup](https://developers.google.com/gmail/api/quickstart)
- [Playwright Automation](https://playwright.dev/python/docs/intro)

### Community
- **Weekly Meeting**: Wednesdays 10:00 PM PKT on Zoom
- **Zoom Link**: https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1
- **YouTube**: https://www.youtube.com/@panaversity

## Submission Requirements

- GitHub repository with code and documentation
- README.md with setup instructions
- Demo video (5-10 minutes)
- Security disclosure document
- Submit form: https://forms.gle/JR9T1SJq5rmQyGkGA

## Judging Criteria

| Criterion | Weight |
|-----------|--------|
| Functionality | 30% |
| Innovation | 25% |
| Practicality | 20% |
| Security | 15% |
| Documentation | 10% |
