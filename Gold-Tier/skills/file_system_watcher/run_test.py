import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("FILE SYSTEM WATCHER SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/file_system_watcher")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="scan_watch_folder")
    for k in ["watch_folder", "vault_path", "move_processed"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.file_system_watcher.skill import scan_watch_folder, list_unprocessed_files
    for fn in [scan_watch_folder, list_unprocessed_files]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.file_system_watcher.service import FileWatcherService
    for m in ["scan_folder", "list_unprocessed_files", "_create_action_file", "_file_hash"]:
        t(f"FileWatcherService.{m}", hasattr(FileWatcherService, m))
except Exception: t("service import", False)

print("\n5. Functional Test (scan empty folder)")
try:
    vault = os.path.join(tempfile.gettempdir(), "test_fsw_vault")
    watch = os.path.join(tempfile.gettempdir(), "test_fsw_watch")
    for d in ['Needs_Action', 'Inbox', 'Logs']:
        os.makedirs(os.path.join(vault, d), exist_ok=True)
    os.makedirs(watch, exist_ok=True)

    svc = FileWatcherService(vault_path=vault)
    r = svc.scan_folder(watch, move_processed=False)
    t("scan returns dict", isinstance(r, dict))
    t("success=True", r.get("success") == True)
    t("count=0 (empty folder)", r.get("count") == 0)

    # Create a test file and scan again
    test_file = Path(watch) / "test_doc.pdf"
    test_file.write_text("test content", encoding="utf-8")

    r2 = svc.scan_folder(watch, move_processed=False)
    t("scan finds file", r2.get("count") == 1)
    t("action file created", len(r2.get("action_files", [])) >= 1)
    if r2.get("action_files"):
        ap = Path(r2["action_files"][0])
        t("action file exists", ap.exists())
        if ap.exists():
            content = ap.read_text(encoding="utf-8")
            t("action file has frontmatter", "type: file_drop" in content)
            t("action file has filename", "test_doc.pdf" in content)

    # Clean up
    test_file.unlink(missing_ok=True)
except Exception as e:
    t("functional test", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(scan_watch_folder)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
