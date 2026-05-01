"""
Test Idempotency Key System

Tests the idempotency system that prevents duplicate operations:
- Check idempotency
- Record operations
- Duplicate detection
- Cached result retrieval
- Expiration handling
- Cleanup
- Statistics
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from idempotency import (
    check_idempotency,
    record_operation,
    is_duplicate,
    get_cached_result,
    cleanup_expired,
    get_operation_stats
)


def test_record_and_check_idempotency():
    """Test recording and checking idempotency."""
    print("\n[TEST] Record and Check Idempotency")

    with tempfile.TemporaryDirectory() as tmpdir:
        correlation_id = "test-invoice-123"
        operation_type = "invoice_creation"
        result = {"success": True, "invoice_id": "INV-001", "amount": 500.0}

        # Record operation
        recorded = record_operation(correlation_id, operation_type, result, tmpdir, ttl_hours=24)
        assert recorded, "Operation should be recorded successfully"

        # Check idempotency - should find the operation
        cached = check_idempotency(correlation_id, operation_type, tmpdir)
        assert cached is not None, "Should find cached operation"
        assert cached['idempotency_key'] == correlation_id
        assert cached['operation_type'] == operation_type
        assert cached['result'] == result

        print("  [OK] Record and check idempotency works")
        return True


def test_duplicate_detection():
    """Test duplicate operation detection."""
    print("\n[TEST] Duplicate Detection")

    with tempfile.TemporaryDirectory() as tmpdir:
        correlation_id = "test-email-456"
        operation_type = "email_send"

        # First check - should not be duplicate
        assert not is_duplicate(correlation_id, operation_type, tmpdir), "Should not be duplicate initially"

        # Record operation
        result = {"success": True, "message_id": "MSG-001"}
        record_operation(correlation_id, operation_type, result, tmpdir)

        # Second check - should be duplicate
        assert is_duplicate(correlation_id, operation_type, tmpdir), "Should be duplicate after recording"

        print("  [OK] Duplicate detection works")
        return True


def test_cached_result_retrieval():
    """Test retrieving cached results."""
    print("\n[TEST] Cached Result Retrieval")

    with tempfile.TemporaryDirectory() as tmpdir:
        correlation_id = "test-post-789"
        operation_type = "linkedin_post"
        result = {"success": True, "post_id": "POST-001", "screenshot": "/path/to/screenshot.png"}

        # Record operation
        record_operation(correlation_id, operation_type, result, tmpdir)

        # Retrieve cached result
        cached_result = get_cached_result(correlation_id, operation_type, tmpdir)
        assert cached_result is not None, "Should retrieve cached result"
        assert cached_result == result, "Cached result should match original"

        print("  [OK] Cached result retrieval works")
        return True


def test_different_operation_types():
    """Test that different operation types are isolated."""
    print("\n[TEST] Different Operation Types")

    with tempfile.TemporaryDirectory() as tmpdir:
        correlation_id = "test-multi-001"

        # Record same correlation_id for different operations
        record_operation(correlation_id, "invoice_creation", {"invoice_id": "INV-001"}, tmpdir)
        record_operation(correlation_id, "email_send", {"message_id": "MSG-001"}, tmpdir)
        record_operation(correlation_id, "linkedin_post", {"post_id": "POST-001"}, tmpdir)

        # Check each operation type separately
        assert is_duplicate(correlation_id, "invoice_creation", tmpdir)
        assert is_duplicate(correlation_id, "email_send", tmpdir)
        assert is_duplicate(correlation_id, "linkedin_post", tmpdir)

        # Verify results are different
        invoice_result = get_cached_result(correlation_id, "invoice_creation", tmpdir)
        email_result = get_cached_result(correlation_id, "email_send", tmpdir)
        post_result = get_cached_result(correlation_id, "linkedin_post", tmpdir)

        assert invoice_result.get("invoice_id") == "INV-001"
        assert email_result.get("message_id") == "MSG-001"
        assert post_result.get("post_id") == "POST-001"

        print("  [OK] Different operation types are isolated")
        return True


def test_expiration():
    """Test that expired entries are not returned."""
    print("\n[TEST] Expiration Handling")

    with tempfile.TemporaryDirectory() as tmpdir:
        correlation_id = "test-expired-001"
        operation_type = "email_send"
        result = {"success": True, "message_id": "MSG-001"}

        # Record with very short TTL (1 hour in the past)
        record_operation(correlation_id, operation_type, result, tmpdir, ttl_hours=-1)

        # Check - should not find expired entry
        cached = check_idempotency(correlation_id, operation_type, tmpdir)
        assert cached is None, "Should not return expired entry"

        print("  [OK] Expiration handling works")
        return True


def test_no_correlation_id():
    """Test behavior with empty correlation_id."""
    print("\n[TEST] No Correlation ID")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Check with empty correlation_id
        cached = check_idempotency("", "email_send", tmpdir)
        assert cached is None, "Should return None for empty correlation_id"

        # Record with empty correlation_id
        recorded = record_operation("", "email_send", {"success": True}, tmpdir)
        assert not recorded, "Should not record with empty correlation_id"

        print("  [OK] Empty correlation_id handled correctly")
        return True


def test_operation_stats():
    """Test operation statistics."""
    print("\n[TEST] Operation Statistics")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Record multiple operations
        record_operation("corr-001", "invoice_creation", {"success": True}, tmpdir)
        record_operation("corr-002", "invoice_creation", {"success": True}, tmpdir)
        record_operation("corr-003", "email_send", {"success": True}, tmpdir)
        record_operation("corr-004", "linkedin_post", {"success": True}, tmpdir)
        record_operation("corr-005", "linkedin_post", {"success": True}, tmpdir)

        # Get stats
        stats = get_operation_stats(tmpdir, days=1)

        assert stats['total_operations'] == 5, f"Should have 5 operations, got {stats['total_operations']}"
        assert stats['by_type']['invoice_creation'] == 2
        assert stats['by_type']['email_send'] == 1
        assert stats['by_type']['linkedin_post'] == 2

        print("  [OK] Operation statistics work")
        print(f"  [OK] Total operations: {stats['total_operations']}")
        print(f"  [OK] By type: {stats['by_type']}")
        return True


def test_cleanup_expired():
    """Test cleanup of expired entries."""
    print("\n[TEST] Cleanup Expired Entries")

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        idempotency_dir = vault / "Logs" / "idempotency"
        idempotency_dir.mkdir(parents=True, exist_ok=True)

        # Create old log files
        old_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
        old_file = idempotency_dir / f"{old_date}_idempotency.jsonl"
        old_file.write_text('{"test": "data"}\n')

        # Create recent log file
        recent_date = datetime.now().strftime('%Y-%m-%d')
        recent_file = idempotency_dir / f"{recent_date}_idempotency.jsonl"
        recent_file.write_text('{"test": "data"}\n')

        # Cleanup (keep 30 days)
        cleaned = cleanup_expired(tmpdir, days=30)

        assert cleaned >= 1, "Should clean up at least 1 old file"
        assert not old_file.exists(), "Old file should be deleted"
        assert recent_file.exists(), "Recent file should remain"

        print("  [OK] Cleanup expired entries works")
        print(f"  [OK] Cleaned up {cleaned} old files")
        return True


def test_retry_scenario():
    """Test idempotency in retry scenario."""
    print("\n[TEST] Retry Scenario")

    with tempfile.TemporaryDirectory() as tmpdir:
        correlation_id = "test-retry-001"
        operation_type = "invoice_creation"

        # Simulate first attempt
        cached = check_idempotency(correlation_id, operation_type, tmpdir)
        assert cached is None, "First attempt should not find cached result"

        # Perform operation
        result = {"success": True, "invoice_id": "INV-001", "amount": 500.0}
        record_operation(correlation_id, operation_type, result, tmpdir)

        # Simulate retry (network failure, then retry)
        cached = check_idempotency(correlation_id, operation_type, tmpdir)
        assert cached is not None, "Retry should find cached result"
        assert cached['result'] == result, "Cached result should match"

        # Verify we don't create duplicate
        print("  [OK] Retry scenario prevents duplicate operation")
        return True


def test_multiple_correlation_ids():
    """Test multiple correlation IDs for same operation type."""
    print("\n[TEST] Multiple Correlation IDs")

    with tempfile.TemporaryDirectory() as tmpdir:
        operation_type = "email_send"

        # Record multiple operations
        for i in range(5):
            correlation_id = f"email-{i}"
            result = {"success": True, "message_id": f"MSG-{i}"}
            record_operation(correlation_id, operation_type, result, tmpdir)

        # Verify each is tracked separately
        for i in range(5):
            correlation_id = f"email-{i}"
            cached = get_cached_result(correlation_id, operation_type, tmpdir)
            assert cached is not None, f"Should find result for {correlation_id}"
            assert cached['message_id'] == f"MSG-{i}"

        print("  [OK] Multiple correlation IDs tracked separately")
        return True


def run_all_tests():
    """Run all idempotency tests."""
    print("="*80)
    print("IDEMPOTENCY KEY SYSTEM TESTS")
    print("="*80)

    tests = [
        test_record_and_check_idempotency,
        test_duplicate_detection,
        test_cached_result_retrieval,
        test_different_operation_types,
        test_expiration,
        test_no_correlation_id,
        test_operation_stats,
        test_cleanup_expired,
        test_retry_scenario,
        test_multiple_correlation_ids
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
