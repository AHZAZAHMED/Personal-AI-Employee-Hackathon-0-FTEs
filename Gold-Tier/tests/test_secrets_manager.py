"""
Test Secrets Manager

Verifies that the secrets management system works correctly.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from secrets_manager import (
    get_secret,
    has_secret,
    get_secrets_manager,
    SecretNotFoundError,
    get_facebook_credentials,
    get_twitter_credentials,
    get_twilio_credentials,
)

PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [OK] {name}")
        PASS += 1
    else:
        print(f"  [FAIL] {name} - {detail}")
        FAIL += 1

print("=" * 60)
print("SECRETS MANAGER TEST")
print("=" * 60)

# Test 1: Module imports
print("\n1. Module Imports")
test("secrets_manager imported", True)
test("get_secret function available", callable(get_secret))
test("has_secret function available", callable(has_secret))
test("get_secrets_manager function available", callable(get_secrets_manager))

# Test 2: Backend detection
print("\n2. Backend Detection")
manager = get_secrets_manager()
test("Manager instantiated", manager is not None)
test("Backend detected", manager._backend in ['env', 'aws', 'azure', 'vault'])
print(f"     Backend: {manager._backend}")

# Test 3: Environment variable access
print("\n3. Environment Variable Access")
os.environ['TEST_SECRET'] = 'test_value_123'
try:
    value = get_secret('TEST_SECRET')
    test("Get existing secret", value == 'test_value_123')
except Exception as e:
    test("Get existing secret", False, str(e))

# Test 4: Default values
print("\n4. Default Values")
try:
    value = get_secret('NONEXISTENT_KEY', default='default_value', required=False)
    test("Get with default", value == 'default_value')
except Exception as e:
    test("Get with default", False, str(e))

# Test 5: Required secrets
print("\n5. Required Secrets")
try:
    get_secret('DEFINITELY_DOES_NOT_EXIST', required=True)
    test("Required secret raises exception", False, "Should have raised SecretNotFoundError")
except SecretNotFoundError:
    test("Required secret raises exception", True)
except Exception as e:
    test("Required secret raises exception", False, f"Wrong exception: {e}")

# Test 6: has_secret function
print("\n6. Secret Existence Check")
test("has_secret returns True for existing", has_secret('TEST_SECRET'))
test("has_secret returns False for missing", not has_secret('DEFINITELY_DOES_NOT_EXIST'))

# Test 7: Caching
print("\n7. Secret Caching")
manager.clear_cache()
os.environ['CACHE_TEST'] = 'cached_value'
value1 = get_secret('CACHE_TEST')
del os.environ['CACHE_TEST']  # Remove from env
value2 = get_secret('CACHE_TEST')  # Should still work from cache
test("Cache works", value1 == value2 == 'cached_value')

# Test 8: Convenience functions (if credentials exist)
print("\n8. Convenience Functions")
if has_secret('FACEBOOK_APP_ID'):
    try:
        fb_creds = get_facebook_credentials()
        test("get_facebook_credentials works", isinstance(fb_creds, dict))
        test("Facebook credentials complete", all(k in fb_creds for k in ['app_id', 'app_secret', 'page_id']))
    except Exception as e:
        test("get_facebook_credentials works", False, str(e))
else:
    print("     [SKIP] Facebook credentials not configured")

if has_secret('TWITTER_API_KEY'):
    try:
        tw_creds = get_twitter_credentials()
        test("get_twitter_credentials works", isinstance(tw_creds, dict))
        test("Twitter credentials complete", all(k in tw_creds for k in ['api_key', 'api_secret']))
    except Exception as e:
        test("get_twitter_credentials works", False, str(e))
else:
    print("     [SKIP] Twitter credentials not configured")

if has_secret('TWILIO_ACCOUNT_SID'):
    try:
        tw_creds = get_twilio_credentials()
        test("get_twilio_credentials works", isinstance(tw_creds, dict))
        test("Twilio credentials complete", all(k in tw_creds for k in ['account_sid', 'auth_token']))
    except Exception as e:
        test("get_twilio_credentials works", False, str(e))
else:
    print("     [SKIP] Twilio credentials not configured")

# Test 9: Security - secrets not logged
print("\n9. Security Checks")
import logging
import io

# Capture log output
log_stream = io.StringIO()
handler = logging.StreamHandler(log_stream)
handler.setLevel(logging.DEBUG)
logger = logging.getLogger('SecretsManager')
logger.addHandler(handler)

os.environ['SECRET_VALUE'] = 'super_secret_password_123'
get_secret('SECRET_VALUE')
log_output = log_stream.getvalue()

test("Secret values not logged", 'super_secret_password_123' not in log_output)
test("Secret keys are logged", 'SECRET_VALUE' in log_output)

# Summary
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
if FAIL == 0:
    print("[OK] ALL TESTS PASSED - Secrets manager is working correctly!")
else:
    print(f"[FAIL] {FAIL} test(s) failed - review above")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)
