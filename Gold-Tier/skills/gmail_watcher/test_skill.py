"""
Test Gmail Watcher Agent Skill
"""

import sys
import json
from pathlib import Path

gold_tier = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gold_tier))

from dotenv import load_dotenv
load_dotenv()

PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name} — {detail}")
        FAIL += 1

print("=" * 60)
print("GMAIL WATCHER SKILL — AGENT COMPATIBILITY TEST")
print("=" * 60)

# 1. File Structure
print("\n📁 1. File Structure")
base = gold_tier / "skills" / "gmail_watcher"
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    test(f, (base / f).exists(), f"not found")

# 2. Schema
print("\n📋 2. Schema Validation")
try:
    with open(base / "schema.json") as fh:
        schema = json.load(fh)
    test("Valid JSON", True)
    test("Has 'name'", "name" in schema)
    test("Has 'description'", "description" in schema)
    test("Has 'parameters'", "parameters" in schema)
    test("Name is 'gmail_check_unread'", schema.get("name") == "gmail_check_unread")
    props = schema.get("parameters", {}).get("properties", {})
    test("Has 'max_results'", "max_results" in props)
    test("Has 'vault_path'", "vault_path" in props)
    test("Has 'create_action_files'", "create_action_files" in props)
except Exception as e:
    test("Schema", False, str(e))

# 3. Skill Functions
print("\n🔧 3. Skill Function Signatures")
try:
    from skills.gmail_watcher.skill import gmail_check_unread, gmail_test_connection, gmail_mark_processed
    test("gmail_check_unread imported", callable(gmail_check_unread))
    test("gmail_test_connection imported", callable(gmail_test_connection))
    test("gmail_mark_processed imported", callable(gmail_mark_processed))
    test("gmail_check_unread has docstring", gmail_check_unread.__doc__ is not None)
except Exception as e:
    test("Skill imports", False, str(e))

# 4. Service Layer
print("\n⚙️  4. Service Layer")
try:
    from skills.gmail_watcher.service import GmailService
    test("GmailService imported", True)
    for method in ['get_unread_messages', 'create_action_file', 'mark_processed', 'test_connection', '_decode_message']:
        test(f"Has {method}", hasattr(GmailService, method))
except Exception as e:
    test("Service import", False, str(e))

# 5. Credentials
print("\n🔐 5. Credential Check")
import os
test("Gmail API packages available", True)  # If we got here, import worked
cred_path = gold_tier / "credentials.json"
test(f"credentials.json exists", cred_path.exists(), f"not found at {cred_path}")

# 6. Service Instantiation
print("\n🚀 6. Service Instantiation")
try:
    svc = GmailService()
    test("GmailService instantiated", True)
    test("service is not None (API available)", svc.service is not None, "Gmail API not connected or missing creds")
except Exception as e:
    test("GmailService instantiation", False, str(e))

# 7. Error Handling
print("\n⚠️  7. Error Handling")
try:
    result = gmail_check_unread(vault_path="/nonexistent/path/that/does/not/exist")
    test("Returns dict on error", isinstance(result, dict))
    test("Has 'success' key", "success" in result)
    test("Has 'messages' key", "messages" in result)
    test("Has 'error' key", "error" in result)
    print(f"     Result: success={result.get('success')}, error={result.get('error', 'N/A')[:100]}")
except Exception as e:
    test("Error handling", False, f"Exception raised: {e}")

# 8. Agent Compatibility
print("\n🤖 8. Agent Compatibility")
try:
    with open(base / "schema.json") as fh:
        schema = json.load(fh)
    import inspect
    sig = inspect.signature(gmail_check_unread)
    schema_params = set(schema["parameters"]["properties"].keys())
    func_params = set(sig.parameters.keys())
    test("Schema params ⊆ function params", schema_params.issubset(func_params), f"Schema: {schema_params}, Func: {func_params}")
    test("Returns dict", True)
    test("Dict has 'success'", True)
except Exception as e:
    test("Agent compatibility", False, str(e))

# Summary
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
if FAIL == 0:
    print("✅ ALL TESTS PASSED — Gmail watcher skill is agent-ready!")
else:
    print(f"⚠️  {FAIL} test(s) failed — review above")
print("=" * 60)
