"""
Test Approval Token System - Security Validation

Tests the approval token system to ensure:
1. Skills CANNOT be called without valid approval tokens
2. Tokens are properly generated and verified
3. Expired tokens are rejected
4. Single-use tokens cannot be reused
5. Token action types are validated
6. Bypass attempts are blocked

This test validates the fix for CRITICAL SECURITY ISSUE:
"Approval Enforcement is Bypassable"
"""

import sys
import time
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

# Add paths - add parent directory so skills can be imported as packages
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from approval_tokens import ApprovalTokenManager, get_token_manager

print("=" * 70)
print("APPROVAL TOKEN SYSTEM - SECURITY VALIDATION TESTS")
print("=" * 70)
print()

# Initialize token manager - use singleton to match what skills use
vault_path = Path(__file__).parent.parent / "AI_Employee_Vault"
token_manager = get_token_manager(str(vault_path))

# Test counters
tests_passed = 0
tests_failed = 0

def test_result(test_name, passed, details=""):
    global tests_passed, tests_failed
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"      {details}")
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    print()

# ============================================================================
# TEST 1: Token Generation
# ============================================================================
print("TEST 1: Token Generation")
print("-" * 70)

try:
    token = token_manager.generate_token(
        action_type="email_send",
        metadata={"to": "test@example.com", "subject": "Test"},
        expires_hours=24,
        single_use=True
    )

    test_result(
        "Token generation",
        len(token) > 0,
        f"Generated token: {token[:20]}..."
    )
except Exception as e:
    test_result("Token generation", False, f"Error: {e}")

# ============================================================================
# TEST 2: Token Verification (Valid Token)
# ============================================================================
print("TEST 2: Token Verification (Valid Token)")
print("-" * 70)

try:
    # Generate a fresh token
    valid_token = token_manager.generate_token(
        action_type="email_send",
        metadata={"to": "test@example.com"},
        expires_hours=1
    )

    # Verify it
    is_valid = token_manager.verify_token(valid_token, "email_send", consume=False)

    test_result(
        "Valid token verification",
        is_valid == True,
        f"Token verified successfully"
    )
except Exception as e:
    test_result("Valid token verification", False, f"Error: {e}")

# ============================================================================
# TEST 3: Token Verification (Invalid Token)
# ============================================================================
print("TEST 3: Token Verification (Invalid Token)")
print("-" * 70)

try:
    # Try to verify a fake token
    is_valid = token_manager.verify_token("fake_token_12345", "email_send")

    test_result(
        "Invalid token rejection",
        is_valid == False,
        "Fake token correctly rejected"
    )
except Exception as e:
    test_result("Invalid token rejection", False, f"Error: {e}")

# ============================================================================
# TEST 4: Token Verification (Wrong Action Type)
# ============================================================================
print("TEST 4: Token Verification (Wrong Action Type)")
print("-" * 70)

try:
    # Generate token for email_send
    email_token = token_manager.generate_token(
        action_type="email_send",
        metadata={"to": "test@example.com"}
    )

    # Try to use it for odoo_create_invoice
    is_valid = token_manager.verify_token(email_token, "odoo_create_invoice")

    test_result(
        "Wrong action type rejection",
        is_valid == False,
        "Token for email_send correctly rejected for odoo_create_invoice"
    )
except Exception as e:
    test_result("Wrong action type rejection", False, f"Error: {e}")

# ============================================================================
# TEST 5: Single-Use Token Consumption
# ============================================================================
print("TEST 5: Single-Use Token Consumption")
print("-" * 70)

try:
    # Generate single-use token
    single_use_token = token_manager.generate_token(
        action_type="email_send",
        metadata={"to": "test@example.com"},
        single_use=True
    )

    # First use - should succeed
    first_use = token_manager.verify_token(single_use_token, "email_send", consume=True)

    # Second use - should fail
    second_use = token_manager.verify_token(single_use_token, "email_send", consume=True)

    test_result(
        "Single-use token consumption",
        first_use == True and second_use == False,
        f"First use: {first_use}, Second use: {second_use}"
    )
except Exception as e:
    test_result("Single-use token consumption", False, f"Error: {e}")

# ============================================================================
# TEST 6: Token Expiration
# ============================================================================
print("TEST 6: Token Expiration")
print("-" * 70)

try:
    # Generate token that expires in 1 second
    short_token = token_manager.generate_token(
        action_type="email_send",
        metadata={"to": "test@example.com"},
        expires_hours=0.0003  # ~1 second
    )

    # Verify immediately - should succeed
    immediate_check = token_manager.verify_token(short_token, "email_send", consume=False)

    # Wait 2 seconds
    print("      Waiting 2 seconds for token to expire...")
    time.sleep(2)

    # Verify after expiration - should fail
    expired_check = token_manager.verify_token(short_token, "email_send", consume=False)

    test_result(
        "Token expiration",
        immediate_check == True and expired_check == False,
        f"Before expiry: {immediate_check}, After expiry: {expired_check}"
    )
except Exception as e:
    test_result("Token expiration", False, f"Error: {e}")

# ============================================================================
# TEST 7: Bypass Attempt - Email Send Without Token
# ============================================================================
print("TEST 7: CRITICAL - Bypass Attempt (Email Send Without Token)")
print("-" * 70)

try:
    # Import email_responder skill as a proper package
    from skills.email_responder import skill as email_skill

    # Try to send email WITHOUT approval token (SHOULD FAIL)
    result = email_skill.email_send(
        to="victim@example.com",
        subject="Unauthorized Email",
        body="This should NOT be sent",
        vault_path=str(vault_path)
        # NO approval_token parameter
    )

    # Check if it was blocked
    blocked = (result.get("success") == False and
               result.get("error") == "APPROVAL_REQUIRED")

    test_result(
        "Email send bypass attempt blocked",
        blocked,
        f"Result: {result.get('error', 'No error')}"
    )
except Exception as e:
    test_result("Email send bypass attempt blocked", False, f"Error: {e}")

# ============================================================================
# TEST 8: Authorized Email Send With Valid Token
# ============================================================================
print("TEST 8: Authorized Email Send With Valid Token")
print("-" * 70)

try:
    # Generate valid approval token
    approval_token = token_manager.generate_token(
        action_type="email_send",
        metadata={"to": "authorized@example.com", "approved_by": "test_suite"},
        expires_hours=1,
        single_use=False  # Don't consume on first verify
    )

    # Verify token is valid before using it
    token_is_valid = token_manager.verify_token(approval_token, "email_send", consume=False)

    if not token_is_valid:
        test_result(
            "Authorized email send (approval check)",
            False,
            f"Token verification failed before skill call"
        )
    else:
        # Try to send email WITH approval token
        # Note: This will fail at Gmail API level (no credentials in test)
        # but should pass the approval check
        result = email_skill.email_send(
            to="authorized@example.com",
            subject="Authorized Email",
            body="This has approval",
            vault_path=str(vault_path),
            approval_token=approval_token
        )

        # Check if approval check passed (even if Gmail API fails)
        # If error is NOT "APPROVAL_REQUIRED", then approval passed
        approval_passed = result.get("error") != "APPROVAL_REQUIRED"

        test_result(
            "Authorized email send (approval check)",
            approval_passed,
            f"Approval check passed: {approval_passed}, Error: {result.get('error', 'None')}"
        )
except Exception as e:
    test_result("Authorized email send", False, f"Error: {e}")

# ============================================================================
# TEST 9: Bypass Attempt - Odoo Invoice Without Token
# ============================================================================
print("TEST 9: CRITICAL - Bypass Attempt (Odoo Invoice Without Token)")
print("-" * 70)

try:
    # Import Odoo skill as a proper package
    from skills.odoo_accounting import skill as odoo_skill

    # Try to create invoice WITHOUT approval token (SHOULD FAIL)
    result = odoo_skill.odoo_create_invoice(
        partner_name="Unauthorized Customer",
        partner_email="victim@example.com",
        lines=[{"name": "Unauthorized Service", "quantity": 1, "price_unit": 1000}]
        # NO approval_token parameter
    )

    # Check if it was blocked
    blocked = (result.get("success") == False and
               result.get("error") == "APPROVAL_REQUIRED")

    test_result(
        "Odoo invoice bypass attempt blocked",
        blocked,
        f"Result: {result.get('error', 'No error')}"
    )
except Exception as e:
    test_result("Odoo invoice bypass attempt blocked", False, f"Error: {e}")

# ============================================================================
# TEST 10: Token Revocation
# ============================================================================
print("TEST 10: Token Revocation")
print("-" * 70)

try:
    # Generate token
    revoke_token = token_manager.generate_token(
        action_type="email_send",
        metadata={"to": "test@example.com"}
    )

    # Verify it works
    before_revoke = token_manager.verify_token(revoke_token, "email_send", consume=False)

    # Revoke it
    revoked = token_manager.revoke_token(revoke_token)

    # Try to verify after revocation
    after_revoke = token_manager.verify_token(revoke_token, "email_send", consume=False)

    test_result(
        "Token revocation",
        before_revoke == True and revoked == True and after_revoke == False,
        f"Before: {before_revoke}, Revoked: {revoked}, After: {after_revoke}"
    )
except Exception as e:
    test_result("Token revocation", False, f"Error: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Total Tests:  {tests_passed + tests_failed}")
print()

if tests_failed == 0:
    print("[SUCCESS] All security tests passed!")
    print("The approval token system is working correctly.")
    print("Skills CANNOT be bypassed without valid approval tokens.")
else:
    print(f"[WARNING] {tests_failed} test(s) failed!")
    print("Review the failures above.")

print("=" * 70)
