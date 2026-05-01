# Sync Neon to Vault Skill

**Agent entry point for syncing WhatsApp messages from Neon PostgreSQL to the Vault Inbox.**

## Quick Use

```python
from skills.sync_neon_vault.skill import sync_neon_to_vault

result = sync_neon_to_vault(limit=50)
print(f"Synced: {result['synced']} files")
```

## Available Functions

| Function | Purpose |
|---|---|
| `sync_neon_to_vault(limit)` | Sync unread DB messages to Vault Inbox/ |
| `sync_mark_done(database_id)` | Mark message as done in DB |
| `sync_get_status()` | Get inbox count and DB unread count |
| `sync_test_connection()` | Test Neon DB connection |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py → Neon DB → Vault Inbox/*.json
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/sync_neon_to_vault.py` standalone daemon with `--interval` polling | `service.py` with callable `run_sync()` method |
| Infinite loop blocking forever | Agent calls `sync_neon_to_vault()` on demand |
| Mixed CLI argparse with business logic | Clean separation: service (sync logic) + skill (agent entry) |
| No agent tool definition | `schema.json` defines parameters for LLM selection |

## Prerequisites

- Neon PostgreSQL database (`NEON_DATABASE_URL` in `.env`)
- WhatsApp messages stored in Neon DB (via `db_neon.py`)
- `pip install psycopg2-binary python-dotenv`
