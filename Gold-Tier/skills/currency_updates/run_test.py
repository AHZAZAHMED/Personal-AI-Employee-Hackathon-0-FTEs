import sys, json
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("CURRENCY UPDATES SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/currency_updates")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="update_currency_rates")
    for k in ["show_comparison"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.currency_updates.skill import update_currency_rates, get_current_rates, convert_currency
    for fn in [update_currency_rates, get_current_rates, convert_currency]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.currency_updates.service import CurrencyService
    for m in ["fetch_ecb_rates", "convert_to_usd_base", "update_rates_file", "run_update", "convert", "get_current_rates"]:
        t(f"CurrencyService.{m}", hasattr(CurrencyService, m))
except Exception: t("service import", False)

print("\n5. Functional Test (rate conversion)")
try:
    svc = CurrencyService()
    t("service instantiated", True)
    t("has rates", len(svc.rates) > 0)

    # Test conversion
    usd = svc.convert(1000.0, "GBP")
    t("converts GBP", abs(usd - 1270.6) < 5)
    usd2 = svc.convert(100.0, "USD")
    t("USD passthrough", usd2 == 100.0)

    # Test EUR→USD conversion
    eur_rates = {"USD": 1.08, "GBP": 0.85, "INR": 90.0, "PKR": 300.0}
    usd_rates = svc.convert_to_usd_base(eur_rates)
    t("converts EUR rates", "GBP" in usd_rates)
    t("USD=1.0", usd_rates.get("USD") == 1.0)

    # Test get_current_rates
    rates = svc.get_current_rates()
    t("get_current_rates returns dict", isinstance(rates, dict))
    t("has USD", "USD" in rates)

except Exception: t("functional test", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(update_currency_rates)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
