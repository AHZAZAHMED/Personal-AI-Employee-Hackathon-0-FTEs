"""
Test Approval Token System

Tests the approval token system that prevents unauthorized skill execution:
- Token generation
- Token verification
- Expiration enforcement
- Single-use enforcement
- Action type validation
- Security bypass prevention
- Token revocation
"""

import sys
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from approval_tokens import (
    ApprovalTokenManager,
    ApprovalRequiredError,
    get_token_manager
)


def test_token_generation():
    """Test token generation."""
    print("\n[TEST] Token Generation")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com', 'subject': 'Test'}
        )

        assert token is not None
        assert len(token) > 20  # Should be cryptographically secure
        assert token in manager.tokens

        print("  [OK] Token generated successfully")
        return True


def test_token_verification_valid():
    """Test verification of valid token."""
    print("\n[TEST] Token Verification (Valid)")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'}
        )

        # Should verify successfully
        assert manager.verify_token(token, 'email_send', consume=False)

        print("  [OK] Valid token verified")
        return True


def test_token_verification_invalid():
    """Test verification of invalid token."""
    print("\n[TEST] Token Verification (Invalid)")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        # Non-existent token
        assert not manager.verify_token('fake_token', 'email_send')

        # None token
        assert not manager.verify_token(None, 'email_send')

        # Empty token
        assert not manager.verify_token('', 'email_send')

        print("  [OK] Invalid tokens rejected")
        return True


def test_action_type_mismatch():
    """Test that action type must match."""
    print("\n[TEST] Action Type Mismatch")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'}
        )

        # Wrong action type should fail
        assert not manager.verify_token(token, 'invoice_create')
        assert not manager.verify_token(token, 'social_post')

        # Correct action type should pass
        assert manager.verify_token(token, 'email_send', consume=False)

        print("  [OK] Action type validation works")
        return True


def test_single_use_enforcement():
    """Test that single-use tokens can only be used once."""
    print("\n[TEST] Single-Use Enforcement")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'},
            single_use=True
        )

        # First use should succeed
        assert manager.verify_token(token, 'email_send', consume=True)

        # Second use should fail (token consumed)
        assert not manager.verify_token(token, 'email_send', consume=True)

        print("  [OK] Single-use enforcement works")
        return True


def test_multi_use_tokens():
    """Test that multi-use tokens can be used multiple times."""
    print("\n[TEST] Multi-Use Tokens")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'},
            single_use=False
        )

        # Should work multiple times
        assert manager.verify_token(token, 'email_send', consume=True)
        assert manager.verify_token(token, 'email_send', consume=True)
        assert manager.verify_token(token, 'email_send', consume=True)

        print("  [OK] Multi-use tokens work")
        return True


def test_token_expiration():
    """Test that expired tokens are rejected."""
    print("\n[TEST] Token Expiration")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        # Create token with very short expiration
        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'},
            expires_hours=0  # Expires immediately
        )

        # Manually set expiration to past
        manager.tokens[token]['expires_at'] = (datetime.now() - timedelta(hours=1)).isoformat()
        manager._save_tokens()

        # Should be rejected as expired
        assert not manager.verify_token(token, 'email_send')

        print("  [OK] Expired tokens rejected")
        return True


def test_token_revocation():
    """Test token revocation."""
    print("\n[TEST] Token Revocation")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'}
        )

        # Token should work before revocation
        assert manager.verify_token(token, 'email_send', consume=False)

        # Revoke token
        assert manager.revoke_token(token)

        # Token should not work after revocation
        assert not manager.verify_token(token, 'email_send')

        print("  [OK] Token revocation works")
        return True


def test_token_persistence():
    """Test that tokens persist across manager instances."""
    print("\n[TEST] Token Persistence")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create token with first manager
        manager1 = ApprovalTokenManager(tmpdir)
        token = manager1.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'}
        )

        # Create new manager instance (should load tokens)
        manager2 = ApprovalTokenManager(tmpdir)

        # Token should still be valid
        assert manager2.verify_token(token, 'email_send', consume=False)

        print("  [OK] Token persistence works")
        return True


def test_expired_token_cleanup():
    """Test automatic cleanup of expired tokens."""
    print("\n[TEST] Expired Token Cleanup")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        # Create expired token
        token = manager.generate_token(
            action_type='email_send',
            metadata={'to': 'test@example.com'}
        )

        # Manually expire it
        manager.tokens[token]['expires_at'] = (datetime.now() - timedelta(hours=1)).isoformat()
        manager._save_tokens()

        # Cleanup should remove it
        manager._clean_expired_tokens()

        assert token not in manager.tokens

        print("  [OK] Expired token cleanup works")
        return True


def test_list_active_tokens():
    """Test listing active tokens."""
    print("\n[TEST] List Active Tokens")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        # Create multiple tokens
        token1 = manager.generate_token('email_send', {'to': 'user1@example.com'})
        token2 = manager.generate_token('invoice_create', {'amount': 100})
        token3 = manager.generate_token('social_post', {'platform': 'linkedin'})

        # List active tokens
        active = manager.list_active_tokens()

        assert len(active) == 3
        assert token1 in active
        assert token2 in active
        assert token3 in active

        print("  [OK] List active tokens works")
        return True


def test_security_bypass_prevention():
    """Test that skills cannot be called without valid token."""
    print("\n[TEST] Security Bypass Prevention")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        # Simulate skill execution without token
        def protected_skill(approval_token=None):
            if not manager.verify_token(approval_token, 'email_send'):
                return {"success": False, "error": "APPROVAL_REQUIRED"}
            return {"success": True, "message": "Email sent"}

        # Without token - should fail
        result = protected_skill()
        assert not result['success']
        assert result['error'] == 'APPROVAL_REQUIRED'

        # With invalid token - should fail
        result = protected_skill(approval_token='fake_token')
        assert not result['success']

        # With valid token - should succeed
        token = manager.generate_token('email_send', {'to': 'test@example.com'})
        result = protected_skill(approval_token=token)
        assert result['success']

        print("  [OK] Security bypass prevention works")
        return True


def test_get_token_info():
    """Test getting token information."""
    print("\n[TEST] Get Token Info")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ApprovalTokenManager(tmpdir)

        metadata = {'to': 'test@example.com', 'subject': 'Test'}
        token = manager.generate_token('email_send', metadata)

        # Get token info
        info = manager.get_token_info(token)

        assert info is not None
        assert info['action_type'] == 'email_send'
        assert info['metadata'] == metadata
        assert 'created_at' in info
        assert 'expires_at' in info

        print("  [OK] Get token info works")
        return True


def test_singleton_instance():
    """Test global singleton instance."""
    print("\n[TEST] Singleton Instance")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Get singleton instances
        manager1 = get_token_manager(tmpdir)
        manager2 = get_token_manager(tmpdir)

        # Should be same instance
        assert manager1 is manager2

        print("  [OK] Singleton instance works")
        return True


def run_all_tests():
    """Run all approval token tests."""
    print("="*80)
    print("APPROVAL TOKEN SYSTEM TESTS")
    print("="*80)

    tests = [
        test_token_generation,
        test_token_verification_valid,
        test_token_verification_invalid,
        test_action_type_mismatch,
        test_single_use_enforcement,
        test_multi_use_tokens,
        test_token_expiration,
        test_token_revocation,
        test_token_persistence,
        test_expired_token_cleanup,
        test_list_active_tokens,
        test_security_bypass_prevention,
        test_get_token_info,
        test_singleton_instance
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

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
