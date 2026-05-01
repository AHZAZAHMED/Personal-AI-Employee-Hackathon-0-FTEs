# WhatsApp Skill

**Agent entry point for sending/receiving WhatsApp messages via Twilio API.**

## Quick Use

```python
from skills.whatsapp.skill import whatsapp_send_message

result = whatsapp_send_message(
    target_number="whatsapp:+923001234567",
    message_text="Hello! Your order has been shipped."
)
```

## Available Functions

| Function | Purpose |
|---|---|
| `whatsapp_send_message(target_number, message_text)` | Send a WhatsApp message |
| `whatsapp_sync_inbox()` | Sync unread DB messages to Vault Inbox |
| `whatsapp_mark_done(database_id)` | Mark a message as processed |
| `whatsapp_test_connection()` | Test Twilio API connection |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Twilio API + Neon DB
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/whatsapp_responder.py` standalone CLI | `skill.py` exposes callable functions |
| `scripts/sync_neon_to_vault.py` standalone daemon | `whatsapp_sync_inbox()` function |
| AI CLI prompt decides whether to call script | Agent selects skill via schema, calls directly |
| No structured input/output | `schema.json` defines parameters, structured dict returned |

## Prerequisites

- Twilio account with WhatsApp sandbox
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` in `.env`
- Neon PostgreSQL (`NEON_DATABASE_URL` in `.env`)
- `pip install twilio psycopg2-binary python-dotenv`
