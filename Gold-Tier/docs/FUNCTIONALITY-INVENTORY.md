# Gold-Tier Functionality Inventory

> **How each feature actually works vs. how it's documented as an Agent Skill**

---

## Core Architecture

The system has **three execution patterns**:

| Pattern | How It Works | Examples |
|---|---|---|
| **A — AI CLI Delegation** | Ralph Wiggum spawns Qwen Code/Claude with a prompt → AI reads inbox files → AI decides which script to call via subprocess | WhatsApp reply, Email reply, Social media processing |
| **B — Hardcoded Import** | A Python script directly `import`s another module and calls its functions — no dynamic discovery | Plan generation, Approval handling, Odoo accounting |
| **C — Standalone Daemon** | A script runs independently as a watcher/server — no orchestration from a central dispatcher | Gmail watcher, WhatsApp webhook, File system watcher |

**⚠️ No script reads `.md` skill files at runtime.** The files in `AI_Employee_Vault/Skills/` are documentation-only reference for humans and AI context.

---

## Functionality Details

### 1. WhatsApp (Twilio) Integration

| Property | Value |
|---|---|
| **Skill File** | `Skills/whatsapp-twilio-integration.md` ✅ exists |
| **How It Actually Works** | **Pattern A + C** |
| **Components** | `twilio_webhook.py` (standalone Flask server, Pattern C), `whatsapp_responder.py` (standalone sender), `db_neon.py` (Neon PostgreSQL), `sync_neon_to_vault.py` (DB → Vault file sync) |
| **Flow** | 1. `twilio_webhook.py` receives WhatsApp webhook → stores message in Neon DB<br>2. `sync_neon_to_vault.py` polls DB → writes JSON to `Inbox/`<br>3. `ralph_wiggum.py` spawns AI CLI → AI reads `Inbox/*.json` → AI calls `whatsapp_responder.py` via subprocess → AI moves file to `Done/` |
| **Skill File Used At Runtime?** | ❌ No |

---

### 2. Gmail Watcher

| Property | Value |
|---|---|
| **Skill File** | `Skills/gmail-watcher-integration.md` ✅ exists |
| **How It Actually Works** | **Pattern C** |
| **Components** | `gmail_watcher.py` (standalone), `authenticate-gmail.py` (one-time OAuth setup) |
| **Flow** | 1. `gmail_watcher.py` polls Gmail API via OAuth token<br>2. New emails → saved as `.md` files in `Inbox/`<br>3. AI (Ralph Wiggum or Orchestrator) reads inbox files and processes them |
| **Skill File Used At Runtime?** | ❌ No |

---

### 3. AI Email Responder

| Property | Value |
|---|---|
| **Skill File** | `Skills/ai-email-responder.md` ✅ exists |
| **How It Actually Works** | **Pattern A** |
| **Components** | `ai_email_generator.py`, `email_sender_mcp.py` |
| **Flow** | 1. Email `.md` file exists in `Inbox/`<br>2. Ralph Wiggum spawns AI CLI with prompt to "process emails"<br>3. AI reads email content → generates reply text → calls `email_sender_mcp.py` via subprocess<br>4. AI moves file to `Done/` |
| **Skill File Used At Runtime?** | ❌ No (but AI may use it as context if pointed to it) |

---

### 4. Human Approval Workflow

| Property | Value |
|---|---|
| **Skill File** | `Skills/human-approval-workflow.md` ✅ exists |
| **How It Actually Works** | **Pattern B** |
| **Components** | `approval_handler.py`, integrated into `orchestrator.py` |
| **Flow** | 1. `orchestrator.py` reads task from `Needs_Action/`<br>2. Determines if task type requires approval (hardcoded list: `email_send`, `payment_request`, `social_media_post`, `external_api_call`)<br>3. If yes → `ApprovalHandler.create_approval_request()` writes to `Pending_Approval/`<br>4. Human moves file to `Approved/`<br>5. Orchestrator executes approved actions via direct method calls |
| **Skill File Used At Runtime?** | ❌ No |

---

### 5. Task/Plan Generation

| Property | Value |
|---|---|
| **Skill File** | `Skills/task-plan-generation.md` ✅ exists |
| **How It Actually Works** | **Pattern B** |
| **Components** | `plan_generator.py`, integrated into `orchestrator.py` |
| **Flow** | 1. `orchestrator.py` receives task<br>2. For complex task types (`email`, `payment`, `social_media`) → calls `PlanGenerator.create_plan()`<br>3. Writes `Plan.md` to `Plans/` folder<br>4. Plan guides subsequent execution |
| **Skill File Used At Runtime?** | ❌ No |

---

### 6. Vault Operations

| Property | Value |
|---|---|
| **Skill File** | `Skills/vault-operations.md` ✅ exists |
| **How It Actually Works** | **Pattern B** |
| **Components** | `orchestrator.py`, `task_processor.py` |
| **Flow** | 1. `orchestrator.py` manages file movement between vault folders (`Needs_Action/` → `In_Progress/` → `Pending_Approval/` → `Approved/` → `Done/`)<br>2. `task_processor.py` simulates what Qwen Code would do — reads task `.md` files, determines action based on hardcoded rules<br>3. `Dashboard.md` updated with current status |
| **Skill File Used At Runtime?** | ❌ No |

---

### 7. Scheduled Operations (Windows Task Scheduler)

| Property | Value |
|---|---|
| **Skill File** | `Skills/scheduled-operations.md` ✅ exists |
| **How It Actually Works** | **Pattern C** |
| **Components** | PowerShell scripts (`Create-CEOBriefing-Task.ps1`, `Create-CurrencyUpdate-Task.ps1`), Windows Task Scheduler |
| **Flow** | 1. PowerShell script registers a Windows Scheduled Task<br>2. Task triggers at scheduled time → runs Python script directly<br>3. No dynamic skill discovery |
| **Skill File Used At Runtime?** | ❌ No |

---

### 8. LinkedIn Auto-Posting

| Property | Value |
|---|---|
| **Skill File** | `Skills/linkedin-auto-posting.md` ✅ exists |
| **How It Actually Works** | **Pattern C** |
| **Components** | `linkedin_poster.py` |
| **Flow** | 1. Task file dropped in `Needs_Action/` with type `linkedin_post`<br>2. Orchestrator or Ralph Wiggum processes it<br>3. AI CLI calls `linkedin_poster.py` via subprocess with post content<br>4. Script uses LinkedIn API to publish |
| **Skill File Used At Runtime?** | ❌ No |

---

### 9. CEO Briefing Generation

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern B** |
| **Components** | `ceo_briefing_generator.py`, `odoo_mcp_server.py` |
| **Flow** | 1. Scheduled task or manual trigger calls `ceo_briefing_generator.py`<br>2. Script imports `OdooAccountingMCP` → pulls financial data (invoices, payments, reports)<br>3. Generates weekly briefing `.md` file in `Briefings/` folder<br>4. Optionally emails via email sender |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 10. Ralph Wiggum Autonomous Loop

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern A** (itself the AI dispatcher) |
| **Components** | `ralph_wiggum.py` |
| **Flow** | 1. User runs `ralph_wiggum.py --prompt "Process all WhatsApp messages"`<br>2. Script spawns Qwen Code/Claude CLI with the prompt<br>3. Reads stdout for completion signal (`TASK_COMPLETE`)<br>4. Checks `Needs_Action/` folder — if empty, loop ends<br>5. Otherwise re-runs with same prompt (up to `max_iterations`) |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 11. Error Recovery System

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern B + C** |
| **Components** | `error_recovery.py`, `watchdog.py` |
| **Flow** | 1. `watchdog.py` monitors running processes for crashes<br>2. On failure → `error_recovery.py` logs error JSON to `Logs/`<br>3. Can auto-restart failed processes<br>4. Errors written as structured JSON for later analysis |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 12. Facebook Monitoring/Posting

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern A + C** |
| **Components** | `facebook_watcher.py` |
| **Flow** | 1. `facebook_watcher.py` can run standalone to monitor Facebook feed<br>2. For posting, AI (via Ralph Wiggum) calls the script with post content<br>3. Uses Facebook Graph API with credentials from `.facebook_credentials.env.template` |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 13. Instagram Monitoring/Posting

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern A + C** |
| **Components** | `instagram_watcher.py`, `get_instagram_id.py` (one-time setup) |
| **Flow** | 1. `get_instagram_id.py` retrieves Instagram Business Account ID<br>2. `instagram_watcher.py` monitors and posts via Facebook Graph API (Instagram endpoint)<br>3. AI delegates posting via Ralph Wiggum loop |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 14. Twitter/X Monitoring

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern C** (Apify workaround) |
| **Components** | `twitter_apify_watcher.py`, `twitter_watcher.py`, `twitter_watcher_official.py` |
| **Flow** | 1. `twitter_apify_watcher.py` uses Apify free scraper to monitor tweets (no API key needed)<br>2. `twitter_watcher_official.py` uses Twitter API v2 (requires paid tier)<br>3. Posting done via credentials in `.twitter_credentials.env.template` |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 15. Odoo Accounting MCP Server

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern B** |
| **Components** | `odoo_mcp_server.py` |
| **Flow** | 1. `OdooAccountingMCP` class provides methods: `create_invoice()`, `register_payment()`, `get_reports()`, etc.<br>2. Imported directly by `ceo_briefing_generator.py`, `email_to_invoice.py`, `set_odoo_currency_usd.py`<br>3. Connects to Odoo instance via XML-RPC API |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 16. Email-to-Invoice Automation

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern B** |
| **Components** | `email_to_invoice.py` |
| **Flow** | 1. Script reads email from `Inbox/` or Gmail API<br>2. Parses invoice data (amount, vendor, date)<br>3. Calls `OdooAccountingMCP.create_invoice()` to create in Odoo<br>4. Logs result to `Logs/` |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 17. Multi-Currency / Rate Updates

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern B + C** |
| **Components** | `update_currency_rates.py`, `set_odoo_currency_usd.py` |
| **Flow** | 1. `update_currency_rates.py` fetches exchange rates from a rate API<br>2. `set_odoo_currency_usd.py` sets USD as base currency in Odoo<br>3. Can be scheduled via Windows Task Scheduler |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 18. Email Sending (Gmail MCP)

| Property | Value |
|---|---|
| **Skill File** | ❌ **No dedicated skill** (covered within `gmail-watcher-integration.md` and `human-approval-workflow.md`) |
| **How It Actually Works** | **Pattern B** |
| **Components** | `email_sender_mcp.py` |
| **Flow** | 1. Imported by `orchestrator.py` → called as `execute_approved_email()`<br>2. Uses Gmail API via MCP server (`@cablate/mcp-gmail`)<br>3. Sends email with generated reply body |
| **Skill File Used At Runtime?** | N/A (no dedicated skill file) |

---

### 19. File System Watcher

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern C** |
| **Components** | `filesystem_watcher.py` |
| **Flow** | 1. Watches specified directories for new files using `watchdog` library<br>2. On new file → creates task in `Inbox/` or `Needs_Action/`<br>3. Triggers downstream processing |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

### 20. Base Watcher Framework

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** (infrastructure, not a feature) |
| **How It Actually Works** | **Pattern B** |
| **Components** | `base_watcher.py` |
| **Flow** | 1. Abstract base class providing common watcher functionality (logging, config loading, error handling)<br>2. Inherited by `gmail_watcher.py`, `filesystem_watcher.py`, etc. |
| **Skill File Used At Runtime?** | N/A |

---

### 21. WhatsApp DB Schema Fix

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** (utility script) |
| **How It Actually Works** | **Standalone one-time fix** |
| **Components** | `fix_whatsapp_db_schema.py` |
| **Flow** | 1. Run once to repair/initialize Neon DB schema for WhatsApp messages<br>2. Not called by any orchestrator or loop |
| **Skill File Used At Runtime?** | N/A |

---

### 22. Sync Neon to Vault

| Property | Value |
|---|---|
| **Skill File** | ❌ **MISSING** |
| **How It Actually Works** | **Pattern C** |
| **Components** | `sync_neon_to_vault.py` |
| **Flow** | 1. Polls Neon DB for unread messages (`--interval` flag for continuous mode)<br>2. Writes each message as JSON to `Inbox/`<br>3. Marks as read in DB after successful write |
| **Skill File Used At Runtime?** | N/A (no skill file) |

---

## Summary Table

| # | Functionality | Has Skill File? | Execution Pattern | Dynamically Dispatched? |
|---|---|---|---|---|
| 1 | WhatsApp (Twilio) | ✅ | A + C | ❌ AI prompt decides |
| 2 | Gmail Watcher | ✅ | C | ❌ Standalone |
| 3 | AI Email Responder | ✅ | A | ❌ AI prompt decides |
| 4 | Human Approval Workflow | ✅ | B | ❌ Hardcoded import |
| 5 | Task/Plan Generation | ✅ | B | ❌ Hardcoded import |
| 6 | Vault Operations | ✅ | B | ❌ Hardcoded import |
| 7 | Scheduled Operations | ✅ | C | ❌ Windows Task Scheduler |
| 8 | LinkedIn Auto-Posting | ✅ | A + C | ❌ AI prompt decides |
| 9 | CEO Briefing Generation | ❌ | B | ❌ Hardcoded import |
| 10 | Ralph Wiggum Loop | ❌ | A | ✅ (it is the dispatcher) |
| 11 | Error Recovery System | ❌ | B + C | ❌ Hardcoded |
| 12 | Facebook Monitoring/Posting | ❌ | A + C | ❌ AI prompt decides |
| 13 | Instagram Monitoring/Posting | ❌ | A + C | ❌ AI prompt decides |
| 14 | Twitter/X Monitoring | ❌ | C | ❌ Standalone |
| 15 | Odoo Accounting MCP | ❌ | B | ❌ Hardcoded import |
| 16 | Email-to-Invoice | ❌ | B | ❌ Hardcoded import |
| 17 | Multi-Currency / Rate Updates | ❌ | B + C | ❌ Standalone/Scheduled |
| 18 | Email Sending (Gmail MCP) | ❌ | B | ❌ Hardcoded import |
| 19 | File System Watcher | ❌ | C | ❌ Standalone |
| 20 | Base Watcher Framework | ❌ | B | N/A (infrastructure) |
| 21 | WhatsApp DB Schema Fix | ❌ | Standalone | ❌ One-time utility |
| 22 | Sync Neon to Vault | ❌ | C | ❌ Standalone |

---

## Key Takeaways

1. **0 out of 22 functionalities use dynamic `.md` skill file reading at runtime.**
2. **8 have proper Agent Skill documentation** — these serve as human/AI reference only.
3. **14 have no skill documentation** — functionality lives purely in code.
4. **The "intelligence" layer is the AI CLI tool** (Qwen Code / Claude). Ralph Wiggum just keeps re-invoking it. The AI reads inbox `.md`/`.json` files and decides which Python scripts to call via subprocess.
5. **Standalone scripts** (`gmail_watcher.py`, `twilio_webhook.py`, etc.) run independently — they are not dispatched by any central orchestrator.
