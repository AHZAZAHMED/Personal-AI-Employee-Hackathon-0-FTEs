# Currency Updates Skill

**Agent entry point for fetching live exchange rates and updating the system's currency conversion table.**

## Quick Use

```python
from skills.currency_updates.skill import update_currency_rates

result = update_currency_rates(show_comparison=True)
print(f"Updated: {result['rates_updated']} rates")
```

## Available Functions

| Function | Purpose |
|---|---|
| `update_currency_rates(show_comparison)` | Fetch live rates, update system |
| `get_current_rates()` | Get current conversion rates |
| `convert_currency(amount, from_currency)` | Convert amount to USD |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py → ECB API → email_to_invoice/service.py rates
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/update_currency_rates.py` standalone CLI with argparse | `service.py` with callable methods |
| Rates updated by writing to `email_to_invoice.py` script | Same mechanism but encapsulated in service |
| Hardcoded fallback rates in script | `DEFAULT_RATES` constant in service |
| No agent tool definition | `schema.json` defines parameters for LLM selection |
| Rate comparison printed to stdout only | Returned as structured dict in result |

## Prerequisites

- Internet access (free ECB API, no auth needed)
- `requests` library installed
