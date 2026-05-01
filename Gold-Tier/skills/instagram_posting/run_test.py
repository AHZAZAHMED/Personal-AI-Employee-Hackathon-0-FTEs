import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("INSTAGRAM POSTING SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/instagram_posting")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="instagram_check_comments")
    for k in ["recent_posts_limit", "vault_path", "create_action_files"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.instagram_posting.skill import instagram_check_comments, instagram_check_mentions, instagram_post_image, instagram_get_insights
    for fn in [instagram_check_comments, instagram_check_mentions, instagram_post_image]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.instagram_posting.service import InstagramService, InstagramClient
    for m in ["check_comments", "check_mentions", "post_image", "get_insights", "test_connection", "create_action_files"]:
        t(f"InstagramService.{m}", hasattr(InstagramService, m))
except Exception: t("service import", False)

print("\n5. Service Instantiation (no IG account)")
try:
    vault = os.path.join(tempfile.gettempdir(), "test_ig_vault")
    for d in ['Needs_Action', 'Logs']:
        os.makedirs(os.path.join(vault, d), exist_ok=True)
    svc = InstagramService(vault_path=vault)
    t("service instantiated", True)
    r = svc.check_comments()
    t("check_comments returns dict", isinstance(r, dict))
    t("has success key", "success" in r)
except Exception: t("service init", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(instagram_check_comments)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
