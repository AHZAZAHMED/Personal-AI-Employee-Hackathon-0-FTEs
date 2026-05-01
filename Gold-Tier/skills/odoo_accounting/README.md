# Odoo Accounting Skill

**Agent entry point for Odoo accounting operations: invoices, payments, balances, and reports.**

## Quick Use

```python
from skills.odoo_accounting.skill import odoo_create_invoice

result = odoo_create_invoice(
    partner_name="Acme Corp",
    partner_email="billing@acme.com",
    lines=[{"name": "Web Design", "quantity": 1, "price_unit": 2000}]
)
```

## Available Functions

| Function | Purpose |
|---|---|
| `odoo_create_invoice(partner_name, partner_email, lines)` | Create customer/vendor invoice |
| `odoo_create_customer(name, email)` | Create a customer record |
| `odoo_record_payment(invoice_number, amount)` | Record payment against invoice |
| `odoo_get_account_balance(account_code)` | Get account balance(s) |
| `odoo_list_transactions(days, limit)` | List recent transactions |
| `odoo_generate_financial_report(report_type)` | P&L or balance sheet |
| `odoo_test_connection()` | Test Odoo connection |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py → Odoo JSON-RPC API
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/odoo_mcp_server.py` monolithic MCP server class | Split: `service.py` (OdooClient + OdooAccountingService) + `skill.py` (agent entry) |
| `OdooAccountingMCP` class required manual instantiation | Callable functions with structured dict returns |
| No agent tool definition | `schema.json` defines parameters for LLM selection |
| Hardcoded credentials in class init | Same defaults, configurable via service init |

## Prerequisites

- Odoo server running (default: http://localhost:8069)
- Database name, username, password configured
