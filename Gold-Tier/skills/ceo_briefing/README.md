# CEO Briefing Skill

**Agent entry point for generating weekly CEO business briefings.**

## Quick Use

```python
from skills.ceo_briefing.skill import generate_ceo_briefing

result = generate_ceo_briefing(days=7)
print(result["content"])
```

## Available Functions

| Function | Purpose |
|---|---|
| `generate_ceo_briefing(days, vault_path, save_to_file)` | Generate + optionally save briefing |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Briefings/ files
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/ceo_briefing_generator.py` CLI-only script | `service.py` with callable methods |
| No agent tool definition | `schema.json` defines parameters for LLM selection |
| Hardcoded Odoo credentials in class init | Same Odoo connection, but in service layer |
| CLI argparse for running | Callable function with structured dict return |

## Prerequisites

- AI Employee Vault with Done/, Plans/, In_Progress/, Logs/ folders
- Odoo server at localhost:8069 (optional — falls back to vault data)
