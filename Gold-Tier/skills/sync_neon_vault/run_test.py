import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("SYNC NEON VAULT SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/sync_neon_vault")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="sync_neon_to_vault")
    for k in ["limit", "vault_path"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.sync_neon_vault.skill import sync_neon_to_vault, sync_mark_done, sync_get_status, sync_test_connection
    for fn in [sync_neon_to_vault, sync_mark_done, sync_get_status, sync_test_connection]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.sync_neon_vault.service import NeonVaultSyncService
    for m in ["run_sync", "mark_done", "mark_failed", "get_status", "test_connection", "format_message", "save_to_inbox"]:
        t(f"NeonVaultSyncService.{m}", hasattr(NeonVaultSyncService, m))
except Exception: t("service import", False)

print("\n5. Service Instantiation (with Neon)")
try:
    vault = os.path.join(tempfile.gettempdir(), "test_sync_vault")
    os.makedirs(os.path.join(vault, "Inbox"), exist_ok=True)
    svc = NeonVaultSyncService(vault_path=vault)
    t("service instantiated", True)
    # test_connection will try to connect to Neon DB
    r = svc.test_connection()
    t("test_connection returns dict", isinstance(r, dict))
    t("has success key", "success" in r)
    # get_status also uses DB
    r2 = svc.get_status()
    t("get_status returns dict", isinstance(r2, dict))
except Exception as e:
    t("service init", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(sync_neon_to_vault)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
