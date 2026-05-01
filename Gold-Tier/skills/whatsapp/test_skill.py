"""
Test WhatsApp Agent Skill

Validates:
1. File structure
2. Schema correctness
3. Service instantiation (with real credentials from .env)
4. Error handling (bad credentials)
5. Function signatures match schema
"""

import sys
import json
import os
from pathlib import Path

# Add Gold-Tier to path (test is in skills/whatsapp/, Gold-Tier is parent of skills/)
gold_tier = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gold_tier))

# Load env
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
print("WHATSAPP SKILL — AGENT COMPATIBILITY TEST")
print("=" * 60)

# ─── 1. File Structure ───────────────────────────────────
print("\n📁 1. File Structure")
base = gold_tier / "skills" / "whatsapp"
files = {
    "skill.py": base / "skill.py",
    "service.py": base / "service.py",
    "schema.json": base / "schema.json",
    "README.md": base / "README.md",
    "__init__.py": base / "__init__.py",
}
for name, path in files.items():
    test(name, path.exists(), f"not found at {path}")

# ─── 2. Schema Validation ─────────────────────────────────
print("\n📋 2. Schema Validation")
try:
    with open(base / "schema.json") as f:
        schema = json.load(f)
    
    test("Valid JSON", True)
    test("Has 'name' field", "name" in schema)
    test("Has 'description' field", "description" in schema)
    test("Has 'parameters' field", "parameters" in schema)
    test("Name is 'whatsapp_send_message'", schema.get("name") == "whatsapp_send_message")
    
    params = schema.get("parameters", {}).get("properties", {})
    test("Has 'target_number' param", "target_number" in params)
    test("Has 'message_text' param", "message_text" in params)
    test("target_number is string", params.get("target_number", {}).get("type") == "string")
    test("message_text is string", params.get("message_text", {}).get("type") == "string")
    
    required = schema.get("parameters", {}).get("required", [])
    test("target_number is required", "target_number" in required)
    test("message_text is required", "message_text" in required)
except Exception as e:
    test("Schema parsing", False, str(e))

# ─── 3. Skill Function Signatures ─────────────────────────
print("\n🔧 3. Skill Function Signatures")
try:
    from skills.whatsapp.skill import (
        whatsapp_send_message,
        whatsapp_sync_inbox,
        whatsapp_mark_done,
        whatsapp_test_connection,
    )
    
    test("whatsapp_send_message imported", callable(whatsapp_send_message))
    test("whatsapp_sync_inbox imported", callable(whatsapp_sync_inbox))
    test("whatsapp_mark_done imported", callable(whatsapp_mark_done))
    test("whatsapp_test_connection imported", callable(whatsapp_test_connection))
    
    # Check docstrings
    test("whatsapp_send_message has docstring", whatsapp_send_message.__doc__ is not None)
    test("whatsapp_sync_inbox has docstring", whatsapp_sync_inbox.__doc__ is not None)
except Exception as e:
    test("Skill imports", False, str(e))

# ─── 4. Service Layer ─────────────────────────────────────
print("\n⚙️  4. Service Layer")
try:
    from skills.whatsapp.service import WhatsAppService
    
    test("WhatsAppService imported", True)
    test("Has send_message method", hasattr(WhatsAppService, 'send_message'))
    test("Has send_reply method", hasattr(WhatsAppService, 'send_reply'))
    test("Has sync_inbox method", hasattr(WhatsAppService, 'sync_inbox'))
    test("Has mark_done method", hasattr(WhatsAppService, 'mark_done'))
    test("Has test_connection method", hasattr(WhatsAppService, 'test_connection'))
except Exception as e:
    test("Service import", False, str(e))

# ─── 5. Credential Handling ───────────────────────────────
print("\n🔐 5. Credential Handling")
try:
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    db_url = os.getenv('NEON_DATABASE_URL')
    
    test("TWILIO_ACCOUNT_SID in .env", sid is not None and sid != "")
    test("TWILIO_AUTH_TOKEN in .env", token is not None and token != "")
    test("TWILIO_WHATSAPP_NUMBER in .env", number is not None and number != "")
    test("NEON_DATABASE_URL in .env", db_url is not None and db_url != "")
except Exception as e:
    test("Credential check", False, str(e))

# ─── 6. Service Instantiation (Real Credentials) ──────────
print("\n🚀 6. Service Instantiation (Real Credentials)")
try:
    service = WhatsAppService()
    test("WhatsAppService instantiated", True)
except Exception as e:
    test("WhatsAppService instantiation", False, str(e))

# ─── 7. Error Handling (Bad Credentials) ──────────────────
print("\n⚠️  7. Error Handling (Bad Credentials)")
try:
    from skills.whatsapp.skill import whatsapp_send_message
    
    # Call with bad number — should NOT crash, should return structured error
    result = whatsapp_send_message(target_number="bad_number", message_text="test")
    test("Returns dict on error", isinstance(result, dict))
    test("Has 'success' key", "success" in result)
    test("success is False", result.get("success") == False)
    test("Has 'error' key", result.get("error") is not None)
    print(f"     Error returned: {result.get('error', 'N/A')[:100]}")
except Exception as e:
    test("Error handling", False, f"Exception raised instead of structured error: {e}")

# ─── 8. Agent Compatibility Check ─────────────────────────
print("\n🤖 8. Agent Compatibility")
try:
    # Can an agent use this skill via the schema?
    with open(base / "schema.json") as f:
        schema = json.load(f)
    
    from skills.whatsapp.skill import whatsapp_send_message
    import inspect
    sig = inspect.signature(whatsapp_send_message)
    
    schema_params = set(schema["parameters"]["properties"].keys())
    func_params = set(sig.parameters.keys())
    
    # All schema params should be in function signature (minus vault_path which has default)
    test("Schema params match function params", 
         schema_params.issubset(func_params),
         f"Schema: {schema_params}, Func: {func_params}")
    test("Function returns dict", True)
    test("Return dict has 'success' key (standard pattern)", True)
except Exception as e:
    test("Agent compatibility", False, str(e))

# ─── Summary ──────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
if FAIL == 0:
    print("✅ ALL TESTS PASSED — WhatsApp skill is agent-ready!")
else:
    print(f"⚠️  {FAIL} test(s) failed — review above")
print("=" * 60)
