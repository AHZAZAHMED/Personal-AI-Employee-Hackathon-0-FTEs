import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("ODOO ACCOUNTING SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/odoo_accounting")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="odoo_create_invoice")
    for k in ["partner_name", "partner_email", "lines", "invoice_type"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.odoo_accounting.skill import (
        odoo_create_invoice, odoo_create_customer, odoo_record_payment,
        odoo_get_account_balance, odoo_list_transactions, odoo_generate_financial_report)
    for fn in [odoo_create_invoice, odoo_create_customer, odoo_record_payment,
               odoo_get_account_balance, odoo_list_transactions]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.odoo_accounting.service import OdooAccountingService, OdooClient
    for m in ["create_invoice", "create_customer", "record_payment", "get_account_balance",
              "list_transactions", "generate_financial_report", "test_connection"]:
        t(f"OdooAccountingService.{m}", hasattr(OdooAccountingService, m))
except Exception: t("service import", False)

print("\n5. Service Instantiation (no Odoo)")
try:
    svc = OdooAccountingService()
    t("service instantiated", True)
    r = svc.test_connection()
    t("test_connection returns dict", isinstance(r, dict))
    t("has success key", "success" in r)
except Exception: t("service init", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(odoo_create_invoice)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
