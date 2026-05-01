# LinkedIn Posting Skill

**Agent entry point for creating and publishing LinkedIn posts.**

## Quick Use

```python
from skills.linkedin_posting.skill import linkedin_create_post_draft

result = linkedin_create_post_draft(
    content="Excited to announce our new product launch!",
    post_type="announcement"
)
```

## Available Functions

| Function | Purpose |
|---|---|
| `linkedin_create_post_draft(content, post_type)` | Create draft in Pending_Approval/ |
| `linkedin_publish_post(post_content)` | Publish directly via Playwright |
| `linkedin_list_pending()` | List drafts awaiting approval |
| `linkedin_list_approved()` | List approved posts ready to publish |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Playwright → LinkedIn
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/linkedin_poster.py` standalone with `--login-only` mode | `service.py` encapsulates browser logic |
| Monolithic class with CLI arg parsing | Separated: service (browser) + skill (agent entry) |
| No agent tool definition | `schema.json` defines parameters for LLM selection |
| Session management mixed in with posting | Session folder managed in service init |

## Prerequisites

- `pip install playwright && playwright install chromium`
- First login: Run LinkedIn login manually to save session in `linkedin_browser_session/`
- Vault with Approved/, Pending_Approval/, Done/, Screenshots/, Logs/ folders
