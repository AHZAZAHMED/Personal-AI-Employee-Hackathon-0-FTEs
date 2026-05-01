import sys, json
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("LINKEDIN POSTING SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/linkedin_posting")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="linkedin_create_post_draft")
    for k in ["content", "post_type", "vault_path"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.linkedin_posting.skill import linkedin_create_post_draft, linkedin_publish_post, linkedin_list_pending, linkedin_list_approved
    for fn in [linkedin_create_post_draft, linkedin_publish_post, linkedin_list_pending]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.linkedin_posting.service import LinkedInService
    for m in ["create_post_draft", "publish_post", "get_pending_posts", "get_approved_posts", "mark_post_published"]:
        t(f"LinkedInService.{m}", hasattr(LinkedInService, m))
except Exception: t("service import", False)

print("\n5. Functional Test (create draft)")
try:
    import tempfile, os
    vault = os.path.join(tempfile.gettempdir(), "test_li_vault")
    for d in ['Pending_Approval', 'Approved', 'Done', 'Logs', 'Screenshots']:
        os.makedirs(os.path.join(vault, d), exist_ok=True)
    svc = LinkedInService(vault_path=vault)
    r = svc.create_post_draft("Test post content", "announcement")
    t("create returns success", r.get("success") == True)
    t("returns filename", "filename" in r)
    t("file exists", Path(r.get("filepath", "")).exists())
except Exception as e: t("functional test", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(linkedin_create_post_draft)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
