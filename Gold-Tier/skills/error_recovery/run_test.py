import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok):
    global PASS, FAIL
    if ok: print(f"  ✅ {name}"); PASS += 1
    else: print(f"  ❌ {name}"); FAIL += 1

print("=" * 50)
print("ERROR RECOVERY SKILL — STRUCTURAL TEST")
print("=" * 50)
base = Path("skills/error_recovery")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base/f).exists())

print("\n2. Schema")
try:
    s = json.loads((base/"schema.json").read_text())
    t("valid JSON", True); t("name", s.get("name")=="classify_error")
    for k in ["error_type", "error_message"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception: t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.error_recovery.skill import classify_error, get_circuit_breaker_status, get_recent_errors, report_health_status, get_health_status
    for fn in [classify_error, get_recent_errors, report_health_status, get_health_status]:
        t(f"{fn.__name__}", callable(fn) and fn.__doc__ is not None)
except Exception: t("imports", False)

print("\n4. Service Layer")
try:
    from skills.error_recovery.service import ErrorLogger, HealthChecker, CircuitBreaker, classify_error_from_string, with_retry
    for cls in [ErrorLogger, HealthChecker, CircuitBreaker]:
        t(f"{cls.__name__}", True)
    t("classify_error_from_string", callable(classify_error_from_string))
    t("with_retry decorator", callable(with_retry))
except Exception: t("service import", False)

print("\n5. Functional Test (classify error)")
try:
    r = classify_error("ConnectionError", "Network timeout after 30s")
    t("classify returns success", r.get("success") == True)
    t("error_type=transient", r.get("error_type") == "transient")
    t("should_retry=True", r.get("should_retry") == True)

    r2 = classify_error("KeyError", "'missing_field'")
    t("auth error classified", r2.get("error_type") == "logic")
    t("logic should_retry=False", r2.get("should_retry") == False)
except Exception as e: t("classify test", False)

print("\n6. Functional Test (health status)")
try:
    vault = os.path.join(tempfile.gettempdir(), "test_err_vault")
    os.makedirs(os.path.join(vault, "Logs"), exist_ok=True)
    from skills.error_recovery.service import HealthChecker
    hc = HealthChecker(vault_path=vault)
    hc.report_status("test_component", "healthy")
    st = hc.get_status("test_component")
    t("health status=healthy", st.get("status") == "healthy")
    all_st = hc.get_status()
    t("all health status has components", "components" in all_st)
except Exception as e: t("health test", False)

print("\n7. Functional Test (error logging)")
try:
    vault = os.path.join(tempfile.gettempdir(), "test_err_vault2")
    os.makedirs(os.path.join(vault, "Logs", "errors"), exist_ok=True)
    from skills.error_recovery.service import ErrorLogger
    el = ErrorLogger(vault_path=vault)
    el.log_error("test_comp", ValueError("test error"))
    errors = el.get_recent_errors(hours=1)
    t("error logged", len(errors) >= 1)
except Exception: t("error logging test", False)

print("\n8. Functional Test (circuit breaker)")
try:
    from skills.error_recovery.service import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
    t("initial state=closed", cb.state.value == "closed")
    status = cb.get_status()
    t("status has state", "state" in status)
except Exception: t("circuit breaker test", False)

print("\n9. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base/"schema.json").read_text())
    sig = inspect.signature(classify_error)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    t("schema params match", sp.issubset(fp))
except Exception: t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0: print("ALL TESTS PASSED")
else: print(f"{FAIL} FAILED")
print("=" * 50)
