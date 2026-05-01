# Error Recovery Skill

**Agent entry point for error classification, health monitoring, and circuit breaker management.**

## Quick Use

```python
from skills.error_recovery.skill import classify_error

result = classify_error(
    error_type="ConnectionError",
    error_message="Network timeout after 30s"
)
# {"error_type": "transient", "should_retry": True, "strategy": "Retry with exponential backoff"}
```

## Available Functions

| Function | Purpose |
|---|---|
| `classify_error(error_type, error_message)` | Classify error, get retry strategy |
| `get_circuit_breaker_status()` | Check circuit breaker state |
| `get_recent_errors(component, hours)` | Query error logs |
| `report_health_status(component, status)` | Report component health |
| `get_health_status(component)` | Get health status |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py (business logic) → Logs/errors/*.jsonl
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/error_recovery.py` library of decorators/classes used by other modules | Split: `service.py` (ErrorLogger, HealthChecker, CircuitBreaker) + `skill.py` (agent entry) |
| `classify_error()` takes Exception object | `classify_error()` takes `error_type` + `error_message` strings (agent-friendly) |
| No agent tool definition | `schema.json` defines parameters for LLM selection |
| Used only internally by watchers | Now callable as standalone agent skill |

## Prerequisites

- AI Employee Vault with Logs/ folder
