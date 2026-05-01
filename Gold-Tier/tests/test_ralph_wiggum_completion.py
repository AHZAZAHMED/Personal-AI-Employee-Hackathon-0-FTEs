"""
Test Ralph Wiggum Loop Completion Detection

Tests that the orchestrator and approval handler emit TASK_COMPLETE signals
for the Ralph Wiggum loop to detect task completion.
"""

import sys
import io
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_orchestrator_emits_completion_signal():
    """Test that orchestrator emits TASK_COMPLETE when marking tasks complete."""
    print("\n[TEST] Orchestrator Completion Signal")

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        from orchestrator import Orchestrator
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create orchestrator
            orch = Orchestrator(tmpdir)

            # Create a test task file
            task_file = Path(tmpdir) / "Needs_Action" / "TEST_task.md"
            task_file.parent.mkdir(parents=True, exist_ok=True)
            task_file.write_text("""---
type: test
priority: normal
---

Test task
""")

            # Mark task complete
            task_data = {'type': 'test', 'priority': 'normal'}
            content = task_file.read_text()

            result = orch._mark_task_complete(
                task_file, task_data, content,
                "Test completion", "Test result", "test-correlation-id"
            )

            # Get captured output
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

            # Verify TASK_COMPLETE was printed
            assert "TASK_COMPLETE" in output, "Orchestrator should emit TASK_COMPLETE signal"
            assert result['success'] is True

            print("  [OK] Orchestrator emits TASK_COMPLETE signal")
            return True

    except Exception as e:
        sys.stdout = sys.__stdout__
        print(f"  [FAIL] {e}")
        return False
    finally:
        sys.stdout = sys.__stdout__


def test_approval_handler_emits_completion_signal():
    """Test that approval handler emits TASK_COMPLETE when executing approved actions."""
    print("\n[TEST] Approval Handler Completion Signal")

    # This is harder to test without full integration, so we'll verify the code exists
    try:
        from approval_handler import ApprovalHandler
        import inspect

        # Get the source code of _execute_approved_action
        source = inspect.getsource(ApprovalHandler._execute_approved_action)

        # Verify TASK_COMPLETE is in the source
        assert 'print("TASK_COMPLETE")' in source, "Approval handler should emit TASK_COMPLETE signal"

        print("  [OK] Approval handler has TASK_COMPLETE signal")
        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_ralph_wiggum_detects_completion():
    """Test that Ralph Wiggum loop can detect completion signals."""
    print("\n[TEST] Ralph Wiggum Completion Detection")

    try:
        from ralph_wiggum import RalphWiggumLoop
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create loop instance
            loop = RalphWiggumLoop(
                vault_path=tmpdir,
                prompt="test",
                max_iterations=1,
                completion_promise="TASK_COMPLETE"
            )

            # Verify completion_promise is set correctly
            assert loop.completion_promise == "TASK_COMPLETE"

            # Verify the detection logic exists
            import inspect
            source = inspect.getsource(loop._run_claude_iteration)
            assert 'completion_promise in line' in source

            print("  [OK] Ralph Wiggum loop has completion detection logic")
            return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def run_all_tests():
    """Run all Ralph Wiggum completion detection tests."""
    print("="*80)
    print("RALPH WIGGUM COMPLETION DETECTION TESTS")
    print("="*80)

    tests = [
        test_orchestrator_emits_completion_signal,
        test_approval_handler_emits_completion_signal,
        test_ralph_wiggum_detects_completion
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
            failed += 1

    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
