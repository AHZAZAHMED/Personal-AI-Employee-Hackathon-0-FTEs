import sys, json
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0

def t(name, ok):
    global PASS, FAIL
    if ok:
        print(f"  ✅ {name}"); PASS += 1
    else:
        print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("EMAIL RESPONDER SKILL — STRUCTURAL TEST")
print("=" * 50)

base = Path("skills/email_responder")

# 1. Files
print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base / f).exists())

# 2. Schema
print("\n2. Schema")
try:
    s = json.loads((base / "schema.json").read_text())
    t("valid JSON", True)
    t("name", s.get("name") == "email_generate_response")
    t("has params", "parameters" in s)
    for k in ["from_email", "subject", "body"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception as e:
    t("schema", False)

# 3. Schema ↔ function params match
print("\n3. Agent Compatibility")
try:
    from skills.email_responder.skill import email_generate_response
    import inspect
    sig = inspect.signature(email_generate_response)
    sp = set(s["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("params match", sp.issubset(fp), )
    t("has docstring", email_generate_response.__doc__ is not None)
except Exception as e:
    t("import + inspect", False)

print(f"\n{'=' * 50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0:
    print("ALL TESTS PASSED")
else:
    print(f"{FAIL} FAILED")
print("=" * 50)
