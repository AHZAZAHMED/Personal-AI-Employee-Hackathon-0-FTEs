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
print("HUMAN APPROVAL SKILL — STRUCTURAL TEST")
print("=" * 50)

base = Path("skills/human_approval")

print("\n1. Files")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    t(f, (base / f).exists())

print("\n2. Schema")
try:
    s = json.loads((base / "schema.json").read_text())
    t("valid JSON", True)
    t("name", s.get("name") == "create_approval_request")
    t("has params", "parameters" in s)
    for k in ["action_type", "details", "vault_path"]:
        t(f"param: {k}", k in s["parameters"]["properties"])
except Exception as e:
    t("schema", False)

print("\n3. Skill Functions")
try:
    from skills.human_approval.skill import (
        create_approval_request, list_pending_approvals,
        list_approved_actions, approve_action, reject_action,
        process_approved_action, archive_rejected_action
    )
    for fn in [create_approval_request, list_pending_approvals, approve_action, process_approved_action]:
        t(f"{fn.__name__} callable + doc", callable(fn) and fn.__doc__ is not None)
except Exception as e:
    t("imports", False)

print("\n4. Service Layer")
try:
    from skills.human_approval.service import ApprovalService
    for m in ["create_approval_request", "mark_approved", "mark_rejected",
              "process_approved", "archive_rejected", "get_pending_approvals"]:
        t(f"ApprovalService.{m}", hasattr(ApprovalService, m))
except Exception as e:
    t("service import", False)

print("\n5. Functional Test (create + list + approve)")
try:
    import tempfile, os
    vault = os.path.join(tempfile.gettempdir(), "test_approval_vault")
    for d in ['Pending_Approval', 'Approved', 'Rejected', 'Done', 'Logs']:
        os.makedirs(os.path.join(vault, d), exist_ok=True)

    svc = ApprovalService(vault_path=vault)

    # Create
    r = svc.create_approval_request("email_send", {"to": "test@test.com", "risk_level": "medium"}, "Test")
    t("create returns success", r.get("success") == True)
    t("create returns filename", "filename" in r)
    filename = r.get("filename", "")

    # List
    pending = svc.get_pending_approvals()
    t("pending count = 1", len(pending) == 1)

    # Approve
    r2 = svc.mark_approved(filename)
    t("mark_approved success", r2.get("success") == True)

    # Process
    r3 = svc.process_approved(filename)
    t("process_approved success", r3.get("success") == True)
except Exception as e:
    t("functional test", False)

print("\n6. Agent Compatibility")
try:
    import inspect
    s2 = json.loads((base / "schema.json").read_text())
    sig = inspect.signature(create_approval_request)
    sp = set(s2["parameters"]["properties"].keys())
    fp = set(sig.parameters.keys())
    ok = sp.issubset(fp)
    print(f"  Schema: {sp}, Func: {fp}, Match: {ok}")
    t("schema params ⊆ func params", ok)
except Exception as e:
    print(f"  Error: {e}")
    t("agent compat", False)

print(f"\n{'='*50}")
print(f"RESULT: {PASS}/{PASS+FAIL} passed")
if FAIL == 0:
    print("ALL TESTS PASSED — Human approval skill is agent-ready!")
else:
    print(f"{FAIL} FAILED")
print("=" * 50)
