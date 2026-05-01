"""
Test File-Based Locking System

Tests the file locking system that prevents concurrent processing:
- Lock acquisition and release
- Timeout behavior
- Stale lock detection and cleanup
- Context manager usage
- Concurrent access prevention
- Lock metadata
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from file_locking import (
    acquire_lock,
    release_lock,
    is_locked,
    cleanup_stale_locks,
    get_lock_info,
    get_all_locks,
    FileLock,
    try_lock,
    LockTimeout
)


def test_acquire_and_release():
    """Test basic lock acquisition and release."""
    print("\n[TEST] Acquire and Release Lock")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-001"

        # Acquire lock
        acquired = acquire_lock(resource_id, timeout=5, vault_path=tmpdir)
        assert acquired, "Should acquire lock"
        assert is_locked(resource_id, tmpdir), "Resource should be locked"

        # Release lock
        released = release_lock(resource_id, tmpdir)
        assert released, "Should release lock"
        assert not is_locked(resource_id, tmpdir), "Resource should be unlocked"

        print("  [OK] Acquire and release works")
        return True


def test_lock_timeout():
    """Test lock timeout when already held."""
    print("\n[TEST] Lock Timeout")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-002"

        # Acquire lock
        acquire_lock(resource_id, timeout=5, vault_path=tmpdir)

        # Try to acquire again with short timeout
        start = time.time()
        acquired = acquire_lock(resource_id, timeout=2, vault_path=tmpdir)
        elapsed = time.time() - start

        assert not acquired, "Should not acquire already-held lock"
        assert 1.5 <= elapsed <= 2.5, f"Should timeout after ~2s, got {elapsed:.1f}s"

        # Release
        release_lock(resource_id, tmpdir)

        print("  [OK] Lock timeout works")
        return True


def test_context_manager():
    """Test FileLock context manager."""
    print("\n[TEST] Context Manager (FileLock)")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-003"

        # Use context manager
        with FileLock(resource_id, timeout=5, vault_path=tmpdir):
            assert is_locked(resource_id, tmpdir), "Should be locked inside context"

        # After context, should be unlocked
        assert not is_locked(resource_id, tmpdir), "Should be unlocked after context"

        print("  [OK] Context manager works")
        return True


def test_context_manager_timeout():
    """Test FileLock context manager timeout."""
    print("\n[TEST] Context Manager Timeout")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-004"

        # Acquire lock
        acquire_lock(resource_id, timeout=5, vault_path=tmpdir)

        # Try to use context manager - should raise LockTimeout
        try:
            with FileLock(resource_id, timeout=1, vault_path=tmpdir):
                assert False, "Should not enter context"
        except LockTimeout:
            pass  # Expected

        # Release
        release_lock(resource_id, tmpdir)

        print("  [OK] Context manager timeout works")
        return True


def test_try_lock():
    """Test try_lock context manager."""
    print("\n[TEST] Try Lock Context Manager")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-005"

        # Try lock - should succeed
        with try_lock(resource_id, timeout=5, vault_path=tmpdir) as locked:
            assert locked, "Should acquire lock"
            assert is_locked(resource_id, tmpdir), "Should be locked"

        # After context, should be unlocked
        assert not is_locked(resource_id, tmpdir), "Should be unlocked"

        # Acquire lock
        acquire_lock(resource_id, timeout=5, vault_path=tmpdir)

        # Try lock - should fail but not raise exception
        with try_lock(resource_id, timeout=1, vault_path=tmpdir) as locked:
            assert not locked, "Should not acquire already-held lock"

        # Release
        release_lock(resource_id, tmpdir)

        print("  [OK] Try lock context manager works")
        return True


def test_lock_metadata():
    """Test lock metadata storage and retrieval."""
    print("\n[TEST] Lock Metadata")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-006"

        # Acquire lock
        acquire_lock(resource_id, timeout=5, vault_path=tmpdir)

        # Get lock info
        info = get_lock_info(resource_id, tmpdir)
        assert info is not None, "Should get lock info"
        assert info['resource_id'] == resource_id
        assert info['pid'] == os.getpid()
        assert 'timestamp' in info
        assert 'hostname' in info
        assert info['process_alive'] is True
        assert info['is_stale'] is False

        # Release
        release_lock(resource_id, tmpdir)

        # After release, no info
        info = get_lock_info(resource_id, tmpdir)
        assert info is None, "Should not get info for unlocked resource"

        print("  [OK] Lock metadata works")
        return True


def test_stale_lock_cleanup():
    """Test stale lock detection and cleanup."""
    print("\n[TEST] Stale Lock Cleanup")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-007"

        # Create lock file manually with old timestamp
        lock_dir = Path(tmpdir) / "Locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_file = lock_dir / f"{resource_id}.lock"

        # Write metadata with old timestamp
        import json
        old_metadata = {
            'resource_id': resource_id,
            'pid': 99999,  # Non-existent process
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'hostname': 'test-host'
        }
        with open(lock_file, 'w') as f:
            json.dump(old_metadata, f)

        # Cleanup stale locks (max age 1 hour)
        cleaned = cleanup_stale_locks(max_age_seconds=3600, vault_path=tmpdir)
        assert cleaned >= 1, "Should clean up stale lock"
        assert not lock_file.exists(), "Stale lock file should be removed"

        print("  [OK] Stale lock cleanup works")
        return True


def test_stale_lock_auto_cleanup():
    """Test automatic stale lock cleanup during acquisition."""
    print("\n[TEST] Automatic Stale Lock Cleanup")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-008"

        # Create stale lock manually
        lock_dir = Path(tmpdir) / "Locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_file = lock_dir / f"{resource_id}.lock"

        import json
        stale_metadata = {
            'resource_id': resource_id,
            'pid': 99999,  # Non-existent process
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'hostname': 'test-host'
        }
        with open(lock_file, 'w') as f:
            json.dump(stale_metadata, f)

        # Try to acquire - should clean up stale lock and succeed
        acquired = acquire_lock(resource_id, timeout=5, vault_path=tmpdir)
        assert acquired, "Should acquire after cleaning stale lock"

        # Verify new lock has current process
        info = get_lock_info(resource_id, tmpdir)
        assert info['pid'] == os.getpid(), "Should have current process ID"

        # Release
        release_lock(resource_id, tmpdir)

        print("  [OK] Automatic stale lock cleanup works")
        return True


def test_multiple_resources():
    """Test locking multiple resources independently."""
    print("\n[TEST] Multiple Resources")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Acquire locks on multiple resources
        resources = ["resource-A", "resource-B", "resource-C"]

        for resource in resources:
            acquired = acquire_lock(resource, timeout=5, vault_path=tmpdir)
            assert acquired, f"Should acquire lock on {resource}"

        # Verify all locked
        for resource in resources:
            assert is_locked(resource, tmpdir), f"{resource} should be locked"

        # Get all locks
        all_locks = get_all_locks(tmpdir)
        assert len(all_locks) == 3, "Should have 3 locks"

        # Release all
        for resource in resources:
            release_lock(resource, tmpdir)

        # Verify all unlocked
        for resource in resources:
            assert not is_locked(resource, tmpdir), f"{resource} should be unlocked"

        print("  [OK] Multiple resources work independently")
        return True


def test_release_not_held():
    """Test releasing a lock that is not held."""
    print("\n[TEST] Release Not Held Lock")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-009"

        # Try to release lock that was never acquired
        released = release_lock(resource_id, tmpdir)
        assert not released, "Should not release non-existent lock"

        print("  [OK] Release not held lock handled correctly")
        return True


def test_concurrent_access_prevention():
    """Test that locks prevent concurrent access."""
    print("\n[TEST] Concurrent Access Prevention")

    with tempfile.TemporaryDirectory() as tmpdir:
        resource_id = "test-resource-010"

        # Process 1 acquires lock
        acquired1 = acquire_lock(resource_id, timeout=5, vault_path=tmpdir)
        assert acquired1, "Process 1 should acquire lock"

        # Process 2 tries to acquire (simulated with timeout=0)
        acquired2 = acquire_lock(resource_id, timeout=0, vault_path=tmpdir)
        assert not acquired2, "Process 2 should not acquire held lock"

        # Process 1 releases
        release_lock(resource_id, tmpdir)

        # Process 2 can now acquire
        acquired2 = acquire_lock(resource_id, timeout=5, vault_path=tmpdir)
        assert acquired2, "Process 2 should acquire after release"

        # Cleanup
        release_lock(resource_id, tmpdir)

        print("  [OK] Concurrent access prevention works")
        return True


def test_lock_with_special_characters():
    """Test locking resources with special characters in ID."""
    print("\n[TEST] Lock with Special Characters")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Resource IDs with special characters
        resource_ids = [
            "task/123/subtask",
            "file:path:with:colons",
            "windows\\path\\style"
        ]

        for resource_id in resource_ids:
            acquired = acquire_lock(resource_id, timeout=5, vault_path=tmpdir)
            assert acquired, f"Should acquire lock on {resource_id}"
            assert is_locked(resource_id, tmpdir), f"{resource_id} should be locked"
            release_lock(resource_id, tmpdir)

        print("  [OK] Special characters in resource ID handled correctly")
        return True


def run_all_tests():
    """Run all file locking tests."""
    print("="*80)
    print("FILE-BASED LOCKING SYSTEM TESTS")
    print("="*80)

    tests = [
        test_acquire_and_release,
        test_lock_timeout,
        test_context_manager,
        test_context_manager_timeout,
        test_try_lock,
        test_lock_metadata,
        test_stale_lock_cleanup,
        test_stale_lock_auto_cleanup,
        test_multiple_resources,
        test_release_not_held,
        test_concurrent_access_prevention,
        test_lock_with_special_characters
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
