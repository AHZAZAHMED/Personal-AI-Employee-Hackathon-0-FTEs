"""
Test Ralph Wiggum Improvements

Tests the Ralph Wiggum enhancements:
- Dynamic Claude path configuration
- Infinite loop protection
- Exponential backoff

Verifies:
- Environment variable support
- Command-line configuration
- Progress tracking
- Stuck detection
- Adaptive delay calculation
"""

import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_dynamic_claude_path_env_var():
    """Test Claude path detection from environment variable."""
    print("\n[TEST] Dynamic Claude Path - Environment Variable")

    tmpdir = tempfile.mkdtemp()
    try:
        from ralph_wiggum import RalphWiggumLoop

        # Set environment variable
        with patch.dict(os.environ, {'CLAUDE_CODE_PATH': 'test-claude'}):
            with patch('shutil.which', return_value='/usr/bin/test-claude'):
                loop = RalphWiggumLoop(
                    vault_path=tmpdir,
                    prompt="test",
                    max_iterations=1
                )

                # Returns env_path directly, not the which() result
                assert loop.claude_path == 'test-claude'

        print("  [OK] Environment variable detection works")
        return True
    finally:
        import shutil
        try:
            shutil.rmtree(tmpdir)
        except:
            pass  # Ignore cleanup errors on Windows


def test_dynamic_claude_path_command_line():
    """Test Claude path from command-line argument."""
    print("\n[TEST] Dynamic Claude Path - Command Line")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=1,
            claude_command='custom-claude'
        )

        assert loop.claude_path == 'custom-claude'

        print("  [OK] Command-line configuration works")
        return True


def test_dynamic_claude_path_auto_detect():
    """Test Claude path auto-detection."""
    print("\n[TEST] Dynamic Claude Path - Auto-detect")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        with patch('shutil.which') as mock_which:
            # Simulate finding 'claude' command
            def which_side_effect(cmd):
                if cmd == 'claude':
                    return '/usr/bin/claude'
                return None

            mock_which.side_effect = which_side_effect

            loop = RalphWiggumLoop(
                vault_path=tmpdir,
                prompt="test",
                max_iterations=1
            )

            assert loop.claude_path == '/usr/bin/claude'

        print("  [OK] Auto-detection works")
        return True


def test_progress_tracking():
    """Test progress tracking functionality."""
    print("\n[TEST] Progress Tracking")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=5,
            claude_command='test-claude'
        )

        # Track progress with changes
        result1 = loop._track_progress(needs_action_count=5, done_count=0)
        assert result1 is True  # First iteration, no history yet

        result2 = loop._track_progress(needs_action_count=4, done_count=1)
        assert result2 is True  # Progress made

        result3 = loop._track_progress(needs_action_count=3, done_count=2)
        assert result3 is True  # Progress made

        # Check history
        assert len(loop.progress_history) == 3

        print("  [OK] Progress tracking works")
        return True


def test_stuck_detection():
    """Test stuck detection when no progress is made."""
    print("\n[TEST] Stuck Detection")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=10,
            claude_command='test-claude'
        )

        # Set stuck threshold to 3
        loop.stuck_threshold = 3

        # Track same state multiple times (no progress)
        loop._track_progress(needs_action_count=5, done_count=0)
        loop._track_progress(needs_action_count=5, done_count=0)
        result = loop._track_progress(needs_action_count=5, done_count=0)

        # Should detect stuck after 3 iterations with no progress
        assert result is False

        print("  [OK] Stuck detection works")
        return True


def test_exponential_backoff_no_progress():
    """Test exponential backoff increases delay when no progress."""
    print("\n[TEST] Exponential Backoff - No Progress")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=5,
            claude_command='test-claude'
        )

        initial_delay = loop.current_delay

        # Calculate backoff with no progress
        delay1 = loop._calculate_backoff_delay(progress_made=False)
        assert delay1 > initial_delay

        delay2 = loop._calculate_backoff_delay(progress_made=False)
        assert delay2 > delay1

        delay3 = loop._calculate_backoff_delay(progress_made=False)
        assert delay3 > delay2

        # Should not exceed max_delay
        assert delay3 <= loop.max_delay

        print("  [OK] Exponential backoff increases correctly")
        return True


def test_exponential_backoff_with_progress():
    """Test exponential backoff decreases delay when progress is made."""
    print("\n[TEST] Exponential Backoff - With Progress")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=5,
            claude_command='test-claude'
        )

        # Increase delay first
        loop._calculate_backoff_delay(progress_made=False)
        loop._calculate_backoff_delay(progress_made=False)
        high_delay = loop.current_delay

        # Now make progress - delay should decrease
        delay1 = loop._calculate_backoff_delay(progress_made=True)
        assert delay1 < high_delay

        delay2 = loop._calculate_backoff_delay(progress_made=True)
        assert delay2 < delay1

        # Should not go below min_delay
        assert delay2 >= loop.min_delay

        print("  [OK] Exponential backoff decreases correctly")
        return True


def test_exponential_backoff_bounds():
    """Test exponential backoff respects min/max bounds."""
    print("\n[TEST] Exponential Backoff - Bounds")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=20,
            claude_command='test-claude'
        )

        # Test max bound
        for _ in range(20):
            delay = loop._calculate_backoff_delay(progress_made=False)

        assert delay <= loop.max_delay

        # Test min bound
        for _ in range(20):
            delay = loop._calculate_backoff_delay(progress_made=True)

        assert delay >= loop.min_delay

        print("  [OK] Backoff bounds respected")
        return True


def test_progress_history_tracking():
    """Test that progress history is properly maintained."""
    print("\n[TEST] Progress History Tracking")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=5,
            claude_command='test-claude'
        )

        # Track multiple states
        loop._track_progress(needs_action_count=10, done_count=0)
        loop._track_progress(needs_action_count=8, done_count=2)
        loop._track_progress(needs_action_count=5, done_count=5)

        # Check history
        assert len(loop.progress_history) == 3
        assert loop.progress_history[0]['needs_action'] == 10
        assert loop.progress_history[1]['needs_action'] == 8
        assert loop.progress_history[2]['needs_action'] == 5

        print("  [OK] Progress history tracked correctly")
        return True


def test_stuck_detection_threshold():
    """Test stuck detection threshold configuration."""
    print("\n[TEST] Stuck Detection Threshold")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        loop = RalphWiggumLoop(
            vault_path=tmpdir,
            prompt="test",
            max_iterations=10,
            claude_command='test-claude'
        )

        # Set custom threshold
        loop.stuck_threshold = 5

        # Track same state 4 times - should not be stuck yet
        for _ in range(4):
            result = loop._track_progress(needs_action_count=5, done_count=0)

        assert result is True  # Not stuck yet

        # 5th time should detect stuck
        result = loop._track_progress(needs_action_count=5, done_count=0)
        assert result is False  # Now stuck

        print("  [OK] Stuck threshold configuration works")
        return True


def test_integration_all_features():
    """Test integration of all Ralph Wiggum improvements."""
    print("\n[TEST] Integration - All Features")

    with tempfile.TemporaryDirectory() as tmpdir:
        from ralph_wiggum import RalphWiggumLoop

        # Create vault structure
        vault = Path(tmpdir)
        needs_action = vault / 'Needs_Action'
        done = vault / 'Done'
        needs_action.mkdir(parents=True)
        done.mkdir(parents=True)

        # Create test files
        (needs_action / 'task1.md').write_text('Task 1')
        (needs_action / 'task2.md').write_text('Task 2')

        # Create loop with custom Claude command
        with patch.dict(os.environ, {'CLAUDE_CODE_PATH': 'test-claude'}):
            loop = RalphWiggumLoop(
                vault_path=tmpdir,
                prompt="test",
                max_iterations=3,
                claude_command='custom-claude'
            )

            # Verify configuration
            assert loop.claude_path == 'custom-claude'
            assert loop.max_iterations == 3
            assert loop.stuck_threshold == 3
            assert loop.min_delay == 2
            assert loop.max_delay == 60

            # Test progress tracking
            loop._track_progress(needs_action_count=2, done_count=0)
            assert len(loop.progress_history) == 1

            # Test backoff
            delay = loop._calculate_backoff_delay(progress_made=False)
            assert delay > loop.min_delay

        print("  [OK] All features integrate correctly")
        return True


def run_all_tests():
    """Run all Ralph Wiggum improvement tests."""
    print("="*80)
    print("RALPH WIGGUM IMPROVEMENT TESTS - PHASE 5")
    print("="*80)

    tests = [
        test_dynamic_claude_path_env_var,
        test_dynamic_claude_path_command_line,
        test_dynamic_claude_path_auto_detect,
        test_progress_tracking,
        test_stuck_detection,
        test_exponential_backoff_no_progress,
        test_exponential_backoff_with_progress,
        test_exponential_backoff_bounds,
        test_progress_history_tracking,
        test_stuck_detection_threshold,
        test_integration_all_features
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
        print("\n[OK] AUDIT-1 BLOCKER #4 IS FIXED")
        print("[OK] Ralph Wiggum improvements complete")
        print("[OK] Dynamic config, loop protection, exponential backoff working")
    else:
        print("\n[ERROR] SOME TESTS FAILED")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
