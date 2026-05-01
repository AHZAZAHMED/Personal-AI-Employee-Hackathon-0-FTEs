# Gmail Watcher Skill

**Agent entry point for checking Gmail unread messages.**

## Quick Use

```python
from skills.gmail_watcher.skill import gmail_check_unread

result = gmail_check_unread(max_results=5)
for msg in result["messages"]:
    print(f"From: {msg['from']}, Subject: {msg['subject']}")
```

## Available Functions

| Function | Purpose |
|---|---|
| `gmail_check_unread(max_results, vault_path, credentials_path, create_action_files)` | Fetch unread emails, optionally create action files |
| `gmail_test_connection()` | Test Gmail OAuth connection |
| `gmail_mark_processed(gmail_id)` | Mark a message as processed (prevent re-fetch) |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Gmail API
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/gmail_watcher.py` standalone polling daemon | `skill.py` exposes callable functions — agent calls on demand |
| Infinite `while True` loop with `time.sleep()` | Single-shot check, agent decides when to call again |
| Processed IDs tracked only in-memory + disk | Same, but exposed via `gmail_mark_processed()` |
| Error recovery via `error_recovery.py` decorators | Errors caught in `skill.py`, returned as structured dict |
| No structured input/output | `schema.json` defines params, structured dict returned |

## Prerequisites

- Google Cloud Project with Gmail API enabled
- `credentials.json` (OAuth 2.0 credentials) in project root
- `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
- First run opens browser for OAuth consent
