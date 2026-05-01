import sys, json
sys.path.insert(0, '.')

print("1. Testing imports...")
from skills.gmail_watcher.skill import gmail_check_unread, gmail_test_connection, gmail_mark_processed
print("   ✅ All 3 skill functions imported")

from skills.gmail_watcher.service import GmailService
print("   ✅ GmailService class imported")

s = json.load(open("skills/gmail_watcher/schema.json"))
assert s["name"] == "gmail_check_unread"
print("   ✅ schema.json valid")

print("\n2. Testing docstrings...")
assert gmail_check_unread.__doc__ is not None
print("   ✅ gmail_check_unread has docstring")

print("\n3. Testing GmailService methods...")
for m in ["get_unread_messages", "create_action_file", "mark_processed", "test_connection"]:
    assert hasattr(GmailService, m), f"Missing {m}"
    print(f"   ✅ {m}")

print("\n4. Testing file structure...")
from pathlib import Path
base = Path("skills/gmail_watcher")
for f in ["skill.py", "service.py", "schema.json", "README.md", "__init__.py"]:
    assert (base / f).exists(), f"Missing {f}"
    print(f"   ✅ {f}")

print("\n5. Testing error handling (bad vault path)...")
result = gmail_check_unread(vault_path="/nonexistent_xyz_123")
assert isinstance(result, dict)
assert "success" in result
assert "messages" in result
assert "error" in result
print(f"   ✅ Returns structured error dict: success={result['success']}")

print("\n6. Testing agent compatibility...")
import inspect
sig = inspect.signature(gmail_check_unread)
schema_params = set(s["parameters"]["properties"].keys())
func_params = set(sig.parameters.keys())
assert schema_params.issubset(func_params), f"Schema {schema_params} not subset of {func_params}"
print(f"   ✅ Schema params match function signature")

print("\n" + "=" * 50)
print("ALL TESTS PASSED — Gmail watcher skill is agent-ready!")
print("=" * 50)
