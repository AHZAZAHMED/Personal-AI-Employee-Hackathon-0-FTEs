import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("FACEBOOK POSTING SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/facebook_posting")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="facebook_check_mentions")
    for k in ["since_hours", "vault_path", "create_action_files"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.facebook_posting.skill import facebook_check_mentions, facebook_create_post, facebook_get_insights, facebook_test_connection
    for fn in [facebook_check_mentions, facebook_create_post, facebook_get_insights]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.facebook_posting.service import FacebookService, FacebookClient
    for m in ["check_mentions", "create_post", "get_insights", "test_connection", "create_action_files"]:
        t(f"FacebookService.{m}", hasattr(FacebookService, m))
except Exception: t("service import", False)

print("\n5. Service Instantiation (no creds)")
try:
    import tempfile, os
    vault = os.path.join(tempfile.gettempdir(), "test_fb_vault")
    for d in ['Needs_Action', 'Logs']:
        os.makedirs(os.path.join(vault, d), exist_ok=True)
    svc = FacebookService(vault_path=vault)
    # Without FB creds, client_available will be False but service should still init
    t("service instantiated", True)
    # Test error handling
    r = svc.check_mentions()
    t("check_mentions returns dict", isinstance(r, dict))
    t("has success key", "success" in r)
except Exception: t("service init", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(facebook_check_mentions)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
