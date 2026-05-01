# Email Responder Skill

**Agent entry point for generating and sending email responses.**

## Quick Use

```python
from skills.email_responder.skill import email_generate_response, email_send

# Generate a response
result = email_generate_response(
    from_email="client@example.com",
    subject="Inquiry about services",
    body="Hi, I am interested in your services."
)
print(result["response"])  # Generated email text
print(result["method"])    # 'qwen_code_ai' or 'fallback_template'

# Send it
send_result = email_send(
    to="client@example.com",
    subject="Re: Inquiry about services",
    body=result["response"]
)

# Or do both in one call
full_result = email_generate_and_send(
    from_email="client@example.com",
    subject="Inquiry about services",
    body="Hi, I am interested."
)
```

## Available Functions

| Function | Purpose |
|---|---|
| `email_generate_response(from_email, subject, body)` | Generate reply (AI → fallback) |
| `email_send(to, subject, body)` | Send email via Gmail API |
| `email_generate_and_send(from_email, subject, body)` | Generate + send in one call |
| `email_test_connection()` | Test Gmail connection |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Qwen CLI / Gmail API
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/ai_email_generator.py` standalone with subprocess Qwen calls | `service.py` encapsulates AI + fallback logic |
| `scripts/email_sender_mcp.py` separate sender | Merged into `EmailResponseService` |
| AI asks questions → fallback not triggered | `_contains_questions()` check built into service |
| Two separate scripts to import | Single skill with `generate`, `send`, and `generate_and_send` |
| No structured input/output | `schema.json` defines params, structured dict returned |

## Prerequisites

- Gmail API: `credentials.json` in project root, `.gmail_token.json` in vault
- Qwen Code CLI on PATH (for AI generation; optional — falls back to template)
- `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
