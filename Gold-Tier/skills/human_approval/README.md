# Human Approval Skill

**Agent entry point for human-in-the-loop approval workflow.**

## Quick Use

```python
from skills.human_approval.skill import create_approval_request

result = create_approval_request(
    action_type="email_send",
    details={
        "to": "client@example.com",
        "subject": "Re: Inquiry",
        "draft_body": "Dear Client,\n\nThank you...",
        "risk_level": "medium"
    }
)
```

## Available Functions

| Function | Purpose |
|---|---|
| `create_approval_request(action_type, details)` | Create approval request in Pending_Approval/ |
| `list_pending_approvals()` | List all pending approvals |
| `list_approved_actions()` | List approved actions ready to execute |
| `approve_action(filename)` | Move from Pending → Approved |
| `reject_action(filename)` | Move from Pending → Rejected |
| `process_approved_action(filename)` | Execute approved action, move to Done/ |
| `archive_rejected_action(filename)` | Archive rejected action to Done/ |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Vault files
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/approval_handler.py` monolithic class with mixed concerns | Split: `service.py` (file ops, workflow) + `skill.py` (agent entry) |
| Approval requests created via direct class method calls | Callable functions with structured dict returns |
| No agent tool definition | `schema.json` defines parameters for LLM selection |
| Executor callback coupled into ApprovalHandler | Separated — skill handles approval flow, executor (orchestrator) handles execution |

## Prerequisites

- AI Employee Vault with standard folder structure (Pending_Approval/, Approved/, Rejected/, Done/, Logs/)
