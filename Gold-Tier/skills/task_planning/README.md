# Task Planning Skill

**Agent entry point for creating detailed action plans for complex tasks.**

## Quick Use

```python
from skills.task_planning.skill import create_task_plan

result = create_task_plan(
    task_type="email_reply",
    task_data={
        "from": "client@example.com",
        "subject": "Inquiry",
        "priority": "high"
    },
    task_content="[full email content here]"
)
```

## Available Functions

| Function | Purpose |
|---|---|
| `create_task_plan(task_type, task_data, task_content)` | Generate plan (AI → template) |
| `update_plan_step(plan_filepath, step_number, step_status)` | Mark a step as done |
| `complete_plan(plan_filepath, summary)` | Archive plan to Done/ |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Plans/ files
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/plan_generator.py` monolithic class with AI subprocess calls | Split: `service.py` (plan generation, templates, updates) + `skill.py` (agent entry) |
| Templates defined as methods on class with `Path` params | Simplified template functions taking just `task_data` dict |
| No agent tool definition | `schema.json` defines parameters for LLM selection |
| AI generation tightly coupled to class | Extracted into `_try_ai_generation()` method in service |

## Prerequisites

- AI Employee Vault with Plans/ and Logs/ folders
- Qwen Code CLI on PATH (optional — falls back to templates)
