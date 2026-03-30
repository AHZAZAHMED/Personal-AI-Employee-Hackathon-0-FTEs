# Personal AI Employee Hackathon 0 - FTEs

**Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

---

## 📁 Project Structure

```
Personal-AI-Employee-Hackathon-0-FTEs/
├── README.md              # This file - project overview
├── .git/                  # Git configuration
├── .gitignore            # Git ignore rules
│
└── Silver-Tier/          # ✅ COMPLETE - Silver Tier Implementation
    ├── AI_Employee_Vault/
    ├── scripts/
    ├── .qwen/
    ├── QWEN.md
    ├── BRONZE-TIER-README.md
    ├── SILVER-TIER-README.md
    ├── SILVER-TIER-COMPLETE.md
    ├── MCP-GMAIL-SETUP.md
    └── ... (all project files)
```

---

## 🏆 Achievement Status

| Tier | Status | Location |
|------|--------|----------|
| **Bronze Tier** | ✅ Complete | `Silver-Tier/BRONZE-TIER-README.md` |
| **Silver Tier** | ✅ Complete | `Silver-Tier/SILVER-TIER-README.md` |
| Gold Tier | ⏳ Pending | - |
| Platinum Tier | ⏳ Pending | - |

---

## 🚀 Quick Start

### Silver Tier (Current)

```bash
cd Silver-Tier

# 1. Start Gmail Watcher
python scripts\gmail_watcher.py --vault AI_Employee_Vault --interval 30

# 2. Send yourself an email

# 3. Stop watcher (Ctrl+C), then run orchestrator
python scripts\orchestrator.py --vault AI_Employee_Vault --once

# 4. Approve and execute
move AI_Employee_Vault\Pending_Approval\*.md AI_Employee_Vault\Approved\
python scripts\approval_handler.py --vault AI_Employee_Vault
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [`Silver-Tier/QWEN.md`](Silver-Tier/QWEN.md) | Project context and reference |
| [`Silver-Tier/SILVER-TIER-README.md`](Silver-Tier/SILVER-TIER-README.md) | Silver Tier setup and usage |
| [`Silver-Tier/BRONZE-TIER-README.md`](Silver-Tier/BRONZE-TIER-README.md) | Bronze Tier documentation |
| [`Silver-Tier/SILVER-TIER-COMPLETE.md`](Silver-Tier/SILVER-TIER-COMPLETE.md) | Silver Tier completion summary |
| [`Silver-Tier/MCP-GMAIL-SETUP.md`](Silver-Tier/MCP-GMAIL-SETUP.md) | MCP Gmail integration guide |

---

## ✨ Silver Tier Features

- ✅ **Two Watchers**: Gmail + File System
- ✅ **MCP Server**: `@cablate/mcp-gmail` configured
- ✅ **Approval Workflow**: Human-in-the-loop for sensitive actions
- ✅ **Plan Generation**: Automatic Plan.md creation
- ✅ **Email Sending**: Via Gmail API (with MCP configured)
- ✅ **Scheduling**: Windows Task Scheduler scripts
- ✅ **Agent Skills**: 7 skill documentation files

---

## 🔧 Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13+ | Watcher scripts |
| Node.js | v24+ LTS | MCP servers |
| Qwen Code | Active | AI reasoning engine |
| Gmail API | Enabled | Email integration |

---

## 📊 Hackathon Progress

```
Bronze Tier:  ████████████████████ 100%
Silver Tier:  ████████████████████ 100%
Gold Tier:    ░░░░░░░░░░░░░░░░░░░░   0%
Platinum:     ░░░░░░░░░░░░░░░░░░░░   0%
```

---

## 🎯 Next Steps (Gold Tier)

- [ ] Odoo Accounting integration
- [ ] Facebook/Instagram integration
- [ ] Twitter (X) integration
- [ ] Weekly CEO Briefing automation
- [ ] Ralph Wiggum loop implementation

---

## 📞 Community

- **Weekly Meeting:** Wednesdays 10:00 PM PKT on Zoom
- **Zoom Link:** https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1
- **YouTube:** https://www.youtube.com/@panaversity

---

## 📝 License

This project is part of the Personal AI Employee Hackathon 0.

---

*AI Employee Hackathon 0 | Silver Tier Complete*
