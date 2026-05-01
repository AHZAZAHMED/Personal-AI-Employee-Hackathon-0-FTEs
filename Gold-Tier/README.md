# AI Employee - Gold Tier

Autonomous AI Employee system with 15 operational skills for handling emails, social media, accounting, and task management.

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

3. **Run the System**
   ```bash
   python scripts/orchestrator.py --vault AI_Employee_Vault
   ```

## System Overview

**Status:** Production Ready (15/15 skills operational)

**AI Brain:** Google Gemini 2.5 Flash

**External Services:**
- Odoo ERP (accounting/invoicing)
- PostgreSQL/Neon (data storage)
- Gmail API (email monitoring)
- Twilio (WhatsApp)
- Facebook/Instagram/LinkedIn APIs

## Skills (15 Total)

### Communication (7)
- WhatsApp Messaging
- Facebook Posting
- Instagram Posting
- LinkedIn Draft Creation
- Gmail Watcher
- Email Responder
- Email to Invoice

### Financial (3)
- Odoo Accounting (create invoices, record payments)
- Currency Rate Updates
- Email to Invoice Processing

### Management (5)
- Task Planning
- CEO Briefing Generation
- Error Recovery
- Health Monitoring
- File System Watcher
- Sync Neon to Vault

## Directory Structure

```
Gold-Tier/
├── AI_Employee_Vault/          # Task files and data
│   ├── Inbox/                  # New tasks
│   ├── Needs_Action/           # Pending tasks
│   ├── Pending_Approval/       # Awaiting human approval
│   ├── Approved/               # Approved for execution
│   ├── Done/                   # Completed tasks
│   ├── Logs/                   # System logs
│   └── Dashboard.md            # Current status
├── scripts/                    # Core orchestration
│   ├── orchestrator.py         # Main coordinator
│   ├── skill_registry.py       # Dynamic skill discovery
│   ├── claude_ai_integration.py # AI brain (Gemini)
│   └── ...
├── skills/                     # 15 skill modules
│   ├── whatsapp_messaging/
│   ├── email_to_invoice/
│   ├── odoo_accounting/
│   └── ...
├── tests/                      # Test files
├── docs/                       # Documentation
│   ├── setup-guides/           # Service setup guides
│   └── ...
├── archive/                    # Old documentation
├── .env                        # Environment variables (not in git)
├── .env.example                # Template for .env
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Odoo/PostgreSQL containers
└── SETUP-GUIDE.md              # Detailed setup instructions
```

## Key Features

- **Dynamic Skill Discovery:** Automatically discovers and registers skills
- **Human-in-the-Loop:** Approval workflow for sensitive actions
- **Multi-Service Integration:** Email, social media, accounting, databases
- **Error Recovery:** Automatic error classification and handling
- **Task Orchestration:** Monitors folders, routes tasks, executes skills
- **Logging & Monitoring:** Comprehensive logging and health checks

## Documentation

- **Setup Guide:** `SETUP-GUIDE.md`
- **Verification Report:** `FINAL-VERIFICATION-REPORT.md`
- **Service Setup Guides:** `docs/setup-guides/`
- **System Documentation:** `docs/`

## Testing

Run tests:
```bash
cd tests
python test_odoo_accounting.py
python test_email_to_invoice.py
python test_sync_neon_vault.py
```

## Configuration Files

- `.env` - API keys and credentials (create from .env.example)
- `credentials.json` - Google OAuth credentials
- `docker-compose.yml` - Odoo and PostgreSQL containers

## External Service Setup

See `docs/setup-guides/` for detailed instructions:
- WhatsApp (Twilio)
- Facebook/Instagram
- LinkedIn
- Gmail API
- Odoo ERP

## License

Personal AI Employee Hackathon Project
