"""
Test Approval Enforcement - End-to-End Security Test

Tests that AUDIT-2 BROKEN #1 is fixed: "Approval Enforcement is Bypassable"

This test verifies that sensitive skills CANNOT be called without valid approval tokens:
- Email sending (email_responder)
- Invoice creation (email_to_invoice)
- Social media posting (LinkedIn, Instagram, Facebook)

Security Requirements:
1. Skills must reject calls without approval tokens
2. Skills must reject calls with invalid tokens
3. Skills must reject calls with expired tokens
4. Skills must reject calls with wrong action_type tokens
5. Skills must accept calls with valid tokens
6. Single-use tokens must be consumed after use
"""

import sys
import tempfile
from pathlib import Path

# Add scripts and skills to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills"))

from approval_tokens import ApprovalTokenManager, get_token_manager


def test_email_send_without_token():
    """Test that email_send rejects calls without approval token."""
    print("\n[TEST] Email Send - No Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Import skill
        from email_responder.skill import email_send

        # Try to send email without token
        result = email_send(
            to="test@example.com",
            subject="Test",
            body="Test body",
            vault_path=tmpdir
        )

        # Should be rejected
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'
        # Message field should indicate approval required
        assert result.get('message') and 'approval' in result['message'].lower()

        print("  [OK] Email send blocked without token")
        return True


def test_email_send_with_invalid_token():
    """Test that email_send rejects calls with invalid token."""
    print("\n[TEST] Email Send - Invalid Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        from email_responder.skill import email_send

        # Try with fake token
        result = email_send(
            to="test@example.com",
            subject="Test",
            body="Test body",
            vault_path=tmpdir,
            approval_token="fake_invalid_token"
        )

        # Should be rejected
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'

        print("  [OK] Email send blocked with invalid token")
        return True


def test_email_send_with_valid_token():
    """Test that email_send accepts calls with valid token."""
    print("\n[TEST] Email Send - Valid Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate valid token using singleton (same as skills use)
        token_manager = get_token_manager(tmpdir)
        token = token_manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'},
            single_use=False  # Multi-use for testing
        )

        from email_responder.skill import email_send

        # Try with valid token (will fail at Gmail API, but should pass token check)
        result = email_send(
            to="test@example.com",
            subject="Test",
            body="Test body",
            vault_path=tmpdir,
            approval_token=token
        )

        # Should pass token verification (will fail at Gmail API level, which is expected)
        # The key is it should NOT return APPROVAL_REQUIRED
        # It should fail with a different error (like "No credentials")
        if not result.get('success'):
            # If it failed, make sure it's NOT because of approval
            assert result.get('error') != 'APPROVAL_REQUIRED', \
                f"Token verification failed when it should have passed. Error: {result.get('error')}"

        print("  [OK] Email send passed token verification")
        return True


def test_invoice_create_without_token():
    """Test that invoice creation rejects calls without approval token."""
    print("\n[TEST] Invoice Create - No Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        from email_to_invoice.skill import process_email_to_invoice

        # Try to create invoice without token
        result = process_email_to_invoice(
            email_content="Test email content",
            vault_path=tmpdir
        )

        # Should be rejected
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'

        print("  [OK] Invoice creation blocked without token")
        return True


def test_invoice_create_with_wrong_action_type():
    """Test that invoice creation rejects tokens with wrong action type."""
    print("\n[TEST] Invoice Create - Wrong Action Type")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate token for email_send (wrong type)
        token_manager = ApprovalTokenManager(tmpdir)
        token = token_manager.generate_token(
            action_type='email_send',  # Wrong type!
            metadata={'to': 'test@example.com'}
        )

        from email_to_invoice.skill import process_email_to_invoice

        # Try with wrong action type token
        result = process_email_to_invoice(
            email_content="Test email content",
            vault_path=tmpdir,
            approval_token=token
        )

        # Should be rejected
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'

        print("  [OK] Invoice creation blocked with wrong action type token")
        return True


def test_linkedin_post_without_token():
    """Test that LinkedIn posting rejects calls without approval token."""
    print("\n[TEST] LinkedIn Post - No Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        from linkedin_posting.skill import linkedin_publish_post

        # Try to post without token
        result = linkedin_publish_post(
            post_content="Test post",
            vault_path=tmpdir
        )

        # Should be rejected
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'

        print("  [OK] LinkedIn post blocked without token")
        return True


def test_instagram_post_without_token():
    """Test that Instagram posting rejects calls without approval token."""
    print("\n[TEST] Instagram Post - No Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        from instagram_posting.skill import instagram_post_image

        # Try to post without token
        result = instagram_post_image(
            image_url="https://example.com/image.jpg",
            caption="Test caption",
            vault_path=tmpdir
        )

        # Should be rejected
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'

        print("  [OK] Instagram post blocked without token")
        return True


def test_facebook_post_without_token():
    """Test that Facebook posting rejects calls without approval token."""
    print("\n[TEST] Facebook Post - No Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        from facebook_posting.skill import facebook_create_post

        # Try to post without token
        result = facebook_create_post(
            message="Test message",
            vault_path=tmpdir
        )

        # Should be rejected
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'

        print("  [OK] Facebook post blocked without token")
        return True


def test_social_post_with_valid_token():
    """Test that social posting accepts calls with valid token."""
    print("\n[TEST] Social Post - Valid Token")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate valid token for social_post using singleton
        token_manager = get_token_manager(tmpdir)
        token = token_manager.generate_token(
            action_type='social_post',
            metadata={'platform': 'linkedin'},
            single_use=False
        )

        from linkedin_posting.skill import linkedin_publish_post

        # Try with valid token (will fail at LinkedIn API, but should pass token check)
        result = linkedin_publish_post(
            post_content="Test post",
            vault_path=tmpdir,
            approval_token=token
        )

        # Should pass token verification (will fail at LinkedIn level, which is expected)
        # The key is it should NOT return APPROVAL_REQUIRED
        if not result.get('success'):
            assert result.get('error') != 'APPROVAL_REQUIRED', \
                f"Token verification failed when it should have passed. Error: {result.get('error')}"

        print("  [OK] Social post passed token verification")
        return True


def test_single_use_token_consumption():
    """Test that single-use tokens are consumed after use."""
    print("\n[TEST] Single-Use Token Consumption")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate single-use token using singleton
        token_manager = get_token_manager(tmpdir)
        token = token_manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'},
            single_use=True
        )

        from email_responder.skill import email_send

        # First call - should pass token verification
        result1 = email_send(
            to="test@example.com",
            subject="Test",
            body="Test body",
            vault_path=tmpdir,
            approval_token=token
        )

        # Should pass token check (may fail at Gmail API level)
        if not result1.get('success'):
            assert result1.get('error') != 'APPROVAL_REQUIRED', \
                f"First call failed token verification: {result1.get('error')}"

        # Second call with same token - should be rejected (token consumed)
        result2 = email_send(
            to="test@example.com",
            subject="Test",
            body="Test body",
            vault_path=tmpdir,
            approval_token=token
        )
        assert not result2['success']
        assert result2['error'] == 'APPROVAL_REQUIRED'

        print("  [OK] Single-use token consumed after first use")
        return True


def test_security_bypass_prevention():
    """
    Test that the security bypass from AUDIT-2 BROKEN #1 is fixed.

    Original vulnerability:
        from skills.email_responder.skill import email_send
        email_send("victim@example.com", "Spam", "Bad")  # NO APPROVAL!

    After fix:
        This should return {"success": False, "error": "APPROVAL_REQUIRED"}
    """
    print("\n[TEST] Security Bypass Prevention (AUDIT-2 BROKEN #1)")

    with tempfile.TemporaryDirectory() as tmpdir:
        from email_responder.skill import email_send

        # Attempt the exact attack from the audit report
        result = email_send(
            to="victim@example.com",
            subject="Spam",
            body="Bad",
            vault_path=tmpdir
        )

        # Should be blocked
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'
        assert 'requires human approval' in result.get('message', '').lower()

        print("  [OK] Security bypass prevented - AUDIT-2 BROKEN #1 FIXED")
        return True


def run_all_tests():
    """Run all approval enforcement tests."""
    print("="*80)
    print("APPROVAL ENFORCEMENT TESTS - AUDIT-2 BROKEN #1 FIX VERIFICATION")
    print("="*80)

    tests = [
        test_email_send_without_token,
        test_email_send_with_invalid_token,
        test_email_send_with_valid_token,
        test_invoice_create_without_token,
        test_invoice_create_with_wrong_action_type,
        test_linkedin_post_without_token,
        test_instagram_post_without_token,
        test_facebook_post_without_token,
        test_social_post_with_valid_token,
        test_single_use_token_consumption,
        test_security_bypass_prevention
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

    if failed == 0:
        print("\n[OK] AUDIT-2 BROKEN #1 IS FIXED")
        print("[OK] Skills cannot be called without valid approval tokens")
        print("[OK] Security bypass vulnerability is closed")
    else:
        print("\n[ERROR] SOME TESTS FAILED - Security enforcement incomplete")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
