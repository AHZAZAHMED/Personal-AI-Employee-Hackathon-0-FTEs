import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("CEO BRIEFING SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/ceo_briefing")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="generate_ceo_briefing")
    for k in ["days", "vault_path", "save_to_file"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.ceo_briefing.skill import generate_ceo_briefing
    t("generate_ceo_briefing callable", callable(generate_ceo_briefing))
    t("has docstring", generate_ceo_briefing.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.ceo_briefing.service import CEOBriefingService
    for m in ["generate_briefing", "save_briefing", "_analyze_completed_tasks", "_analyze_revenue", "_identify_bottlenecks", "_generate_suggestions"]:
        t(f"CEOBriefingService.{m}", hasattr(CEOBriefingService, m))
except Exception: t("service import", False)

print("\n5. Functional Test (generate briefing)")
try:
    vault = os.path.join(tempfile.gettempdir(), "test_ceo_vault")
    for d in ['Done', 'Plans', 'In_Progress/qwen_agent', 'Logs', 'Briefings']:
        os.makedirs(os.path.join(vault, d), exist_ok=True)
    svc = CEOBriefingService(vault_path=vault)
    r = svc.generate_briefing(days=7)
    t("generate returns success", r.get("success") == True)
    t("has content", "content" in r and len(r.get("content", "")) > 200)
    t("has period", "period" in r)
    t("has completed_tasks", "completed_tasks" in r)
    t("has revenue", "revenue" in r)
    t("has bottlenecks", "bottlenecks" in r)
    t("has suggestions", "suggestions" in r)
    t("content has CEO title", "CEO Briefing" in r.get("content", ""))
    t("content has revenue section", "📊 Revenue" in r.get("content", ""))
    # Save test
    r2 = svc.save_briefing(r["content"])
    t("save_briefing success", r2.get("success") == True)
    t("file exists", Path(r2.get("filepath", "")).exists())
except Exception as e: t("functional test", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(generate_ceo_briefing)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
