# Email to Invoice Skill

**Agent entry point for processing customer emails to create invoices in Odoo.**

## Quick Use

```python
from skills.email_to_invoice.skill import process_email_to_invoice

result = process_email_to_invoice(
    email_content="[full email with frontmatter, service details, and amount]"
)
```

## Available Functions

| Function | Purpose |
|---|---|
| `process_email_to_invoice(email_content)` | Extract info, create invoice, send email |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py → Odoo API + Email Sender → Invoice
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/email_to_invoice.py` standalone CLI with argparse | `service.py` with callable `process_email()` method |
| Hardcoded Odoo/Email imports mixed with business logic | Split: service (extraction, currency, Odoo) + skill (agent entry) |
| Currency detection hardcoded in class | Moved to service layer, still uses same rates |
| No agent tool definition | `schema.json` defines parameters for LLM selection |

## Prerequisites

- Odoo server at localhost:8069 (for invoice creation)
- Gmail API configured (for sending invoice emails)
- Vault with Logs/ and Done/ folders
