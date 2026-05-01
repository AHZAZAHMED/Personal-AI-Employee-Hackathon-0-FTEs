# Instagram Posting Skill

**Agent entry point for monitoring Instagram comments/mentions and posting images.**

## Quick Use

```python
from skills.instagram_posting.skill import instagram_check_comments

result = instagram_check_comments(recent_posts_limit=5)
print(f"New comments: {result['count']}")
```

## Available Functions

| Function | Purpose |
|---|---|
| `instagram_check_comments(recent_posts_limit)` | Check comments on recent posts |
| `instagram_check_mentions()` | Check tagged media (mentions) |
| `instagram_post_image(image_url, caption)` | Post an image |
| `instagram_get_insights(metric, days)` | Get analytics |
| `instagram_test_connection()` | Test API connection |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py → Instagram Graph API (via Facebook credentials)
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/instagram_watcher.py` standalone daemon with infinite polling loop | `service.py` with callable methods, no infinite loop |
| `InstagramWatcher.run()` blocked forever | Agent calls `instagram_check_comments()` on demand |
| Mixed concerns: client, watcher, action file creation in one class | Split: `InstagramClient` (API) + `InstagramService` (logic) + `skill.py` (agent entry) |
| No agent tool definition | `schema.json` defines parameters for LLM selection |

## Prerequisites

- Instagram Business Account linked to Facebook Page
- Facebook credentials in `.env` (`FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_TOKEN`)
