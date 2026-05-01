import sys, json
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("TASK PLANNING SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/task_planning")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="create_task_plan")
    for k in ["task_type", "task_data", "task_content", "vault_path"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.task_planning.skill import create_task_plan, update_plan_step, complete_plan
    for fn in [create_task_plan, update_plan_step, complete_plan]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.task_planning.service import PlanningService
    for m in ["generate_plan", "create_plan_file", "update_plan", "complete_plan"]:
        t(f"PlanningService.{m}", hasattr(PlanningService, m))
    # Test template generation only (no AI subprocess)
    import tempfile, os
    vault = os.path.join(tempfile.gettempdir(), "test_pv")
    os.makedirs(os.path.join(vault, "Plans"), exist_ok=True)
    os.makedirs(os.path.join(vault, "Logs"), exist_ok=True)
    os.makedirs(os.path.join(vault, "Done"), exist_ok=True)
    svc = PlanningService(vault_path=vault)
    content = svc._get_template("email", {"from": "a@b.com", "subject": "Test"})
    t("template generates content", len(content) > 100)
    t("template includes from", "a@b.com" in content)
except Exception as e: t("service", False)

print("\n5. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(create_task_plan)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    ok = sp.issubset(fp)
    t("schema params match", ok)
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
