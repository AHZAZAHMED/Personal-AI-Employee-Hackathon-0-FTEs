import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("EMAIL TO INVOICE SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/email_to_invoice")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="process_email_to_invoice")
    for k in ["email_content", "vault_path", "send_invoice_email"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.email_to_invoice.skill import process_email_to_invoice
    t("process_email_to_invoice callable", callable(process_email_to_invoice))
    t("has docstring", process_email_to_invoice.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.email_to_invoice.service import EmailInvoiceService
    for m in ["process_email", "extract_customer_info", "detect_currency", "convert_to_usd",
              "create_customer_and_invoice", "send_invoice_email", "log_action"]:
        t(f"EmailInvoiceService.{m}", hasattr(EmailInvoiceService, m))
except Exception: t("service import", False)

print("\n5. Functional Test (customer extraction)")
try:
    vault = os.path.join(tempfile.gettempdir(), "test_inv_vault")
    for d in ['Logs', 'Done']:
        os.makedirs(os.path.join(vault, d), exist_ok=True)
    svc = EmailInvoiceService(vault_path=vault)
    t("service instantiated", True)

    # Test extraction
    test_email = """---
from: John Smith <john@acme.com>
subject: Consulting service inquiry
---

I need consulting services for $2500.00.
Please invoice me at Acme Corp.
"""
    customer = svc.extract_customer_info(test_email)
    t("extracts name", customer["name"] == "John Smith")
    t("extracts email", customer["email"] == "john@acme.com")
    t("extracts amount", customer["amount"] == 2500.0)
    t("detects service", customer["service"] == "consulting")

    # Test currency detection
    currency = svc.detect_currency("Amount: PKR 50,000")
    t("detects PKR", currency == "PKR")
    currency2 = svc.detect_currency("Please send $500")
    t("defaults to USD", currency2 == "USD")

    # Test currency conversion
    usd = svc.convert_to_usd(1000.0, "GBP")
    t("converts GBP to USD", abs(usd - 1270.6) < 1)

    # Test full process (will fail on Odoo but returns structured error)
    result = svc.process_email(test_email, send_invoice_email=False)
    t("process_email returns dict", isinstance(result, dict))
    t("has success key", "success" in result)
    t("has customer key", "customer" in result)
    t("has invoice key", "invoice" in result)
    # Odoo won't be available so success will be False, but structure should be correct
except Exception as e:
    t("functional test", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(process_email_to_invoice)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
