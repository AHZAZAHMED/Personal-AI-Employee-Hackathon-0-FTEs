# Facebook Posting Skill

**Agent entry point for monitoring Facebook mentions and creating posts.**

## Quick Use

```python
from skills.facebook_posting.skill import facebook_check_mentions

result = facebook_check_mentions(since_hours=24)
print(f"New mentions: {result['count']}")
```

## Available Functions

| Function | Purpose |
|---|---|
| `facebook_check_mentions(since_hours)` | Check Page mentions |
| `facebook_create_post(message)` | Create a Facebook post |
| `facebook_get_insights(days)` | Get Page analytics |
| `facebook_test_connection()` | Test API connection |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py → Facebook Graph API
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/facebook_watcher.py` standalone daemon with polling loop | `service.py` with callable methods, no infinite loop |
| `FacebookWatcher.run()` blocked forever | Agent calls `facebook_check_mentions()` on demand |
| Mixed concerns: client, watcher, action file creation all in one class | Split: `FacebookClient` (API) + `FacebookService` (business logic) + `skill.py` (agent entry) |
| No agent tool definition | `schema.json` defines parameters for LLM selection |

## Prerequisites

- Facebook App ID, App Secret, Page ID, Page Token in `.env`
- `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_TOKEN`
