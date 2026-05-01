"""
Test Error Context Logging System

Tests the rich error capture functionality including:
- Error context capture
- Stack trace preservation
- Variable sanitization
- Error logging to files
- Query capabilities
"""

import sys
import tempfile
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from error_context import (
    capture_error_context,
    log_error_with_context,
    query_errors_by_correlation_id,
    get_recent_errors,
    format_error_for_user
)


def test_capture_error_context():
    """Test capturing error context."""
    print("\n[TEST] Capture Error Context")

    try:
        # Simulate an error with local variables
        user_email = "test@example.com"
        api_key = "secret_key_12345"
        count = 42

        # Raise an error
        raise ValueError("Test error message")

    except Exception as e:
        # Capture context
        context = capture_error_context(e, locals(), correlation_id="test-123")

        # Verify context structure
        assert 'error_id' in context
        assert 'timestamp' in context
        assert 'correlation_id' in context
        assert context['correlation_id'] == "test-123"
        assert 'exception' in context
        assert context['exception']['type'] == 'ValueError'
        assert context['exception']['message'] == 'Test error message'
        assert 'stack_trace' in context
        assert 'local_variables' in context
        assert 'system_state' in context

        # Verify sensitive data is sanitized
        assert context['local_variables'].get('api_key') == '[REDACTED]'
        assert context['local_variables'].get('user_email') == 'test@example.com'
        assert context['local_variables'].get('count') == 42

        print("  [OK] Error context captured correctly")
        print(f"  [OK] Error ID: {context['error_id']}")
        print(f"  [OK] Sensitive data sanitized")
        return True


def test_log_error_with_context():
    """Test logging error context to file."""
    print("\n[TEST] Log Error With Context")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Simulate an error
            raise RuntimeError("Database connection failed")

        except Exception as e:
            # Capture and log
            context = capture_error_context(e, locals(), correlation_id="db-error-456")
            log_file = log_error_with_context(context, tmpdir)

            # Verify log file was created
            assert log_file, "Log file path should be returned"
            log_path = Path(log_file)
            assert log_path.exists(), "Log file should exist"

            # Verify log content
            import json
            with open(log_path, 'r') as f:
                line = f.readline()
                logged_context = json.loads(line)

                assert logged_context['error_id'] == context['error_id']
                assert logged_context['correlation_id'] == "db-error-456"
                assert logged_context['exception']['type'] == 'RuntimeError'

            print("  [OK] Error logged to file")
            print(f"  [OK] Log file: {log_path.name}")
            return True


def test_query_errors_by_correlation_id():
    """Test querying errors by correlation ID."""
    print("\n[TEST] Query Errors by Correlation ID")

    with tempfile.TemporaryDirectory() as tmpdir:
        correlation_id = "query-test-789"

        # Log multiple errors with same correlation ID
        for i in range(3):
            try:
                raise ValueError(f"Error {i}")
            except Exception as e:
                context = capture_error_context(e, locals(), correlation_id=correlation_id)
                log_error_with_context(context, tmpdir)

        # Log error with different correlation ID
        try:
            raise ValueError("Different error")
        except Exception as e:
            context = capture_error_context(e, locals(), correlation_id="different-id")
            log_error_with_context(context, tmpdir)

        # Query by correlation ID
        errors = query_errors_by_correlation_id(correlation_id, tmpdir, days=1)

        assert len(errors) == 3, f"Should find 3 errors, found {len(errors)}"
        assert all(e['correlation_id'] == correlation_id for e in errors)

        print("  [OK] Query by correlation ID works")
        print(f"  [OK] Found {len(errors)} errors")
        return True


def test_get_recent_errors():
    """Test getting recent errors."""
    print("\n[TEST] Get Recent Errors")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Log multiple errors
        for i in range(5):
            try:
                raise ValueError(f"Recent error {i}")
            except Exception as e:
                context = capture_error_context(e, locals())
                log_error_with_context(context, tmpdir)

        # Get recent errors
        recent = get_recent_errors(tmpdir, limit=3)

        assert len(recent) <= 3, "Should return at most 3 errors"
        assert all('error_id' in e for e in recent)

        print("  [OK] Get recent errors works")
        print(f"  [OK] Retrieved {len(recent)} recent errors")
        return True


def test_format_error_for_user():
    """Test formatting error for user display."""
    print("\n[TEST] Format Error for User")

    try:
        raise ConnectionError("API connection timeout")
    except Exception as e:
        context = capture_error_context(e, locals(), correlation_id="user-error-123")
        formatted = format_error_for_user(context)

        assert context['error_id'] in formatted
        assert 'ConnectionError' in formatted
        assert 'API connection timeout' in formatted
        assert 'See logs for details' in formatted

        print("  [OK] Error formatted for user")
        print(f"  [OK] Formatted message:\n{formatted}")
        return True


def test_stack_trace_preservation():
    """Test that stack traces are preserved."""
    print("\n[TEST] Stack Trace Preservation")

    def inner_function():
        raise ValueError("Inner error")

    def outer_function():
        inner_function()

    try:
        outer_function()
    except Exception as e:
        context = capture_error_context(e, locals())

        # Verify stack trace contains function names
        stack_trace = context['stack_trace']
        assert 'inner_function' in stack_trace
        assert 'outer_function' in stack_trace
        assert 'ValueError' in stack_trace

        print("  [OK] Stack trace preserved")
        print(f"  [OK] Stack trace contains function names")
        return True


def test_sensitive_data_sanitization():
    """Test that sensitive data is sanitized."""
    print("\n[TEST] Sensitive Data Sanitization")

    try:
        password = "super_secret_password"
        access_token = "Bearer abc123xyz"
        api_key = "sk-1234567890"
        normal_var = "public_data"

        raise ValueError("Test error")

    except Exception as e:
        context = capture_error_context(e, locals(), sanitize_sensitive=True)
        vars = context['local_variables']

        # Verify sensitive data is redacted
        assert vars.get('password') == '[REDACTED]'
        assert vars.get('access_token') == '[REDACTED]'
        assert vars.get('api_key') == '[REDACTED]'
        assert vars.get('normal_var') == 'public_data'

        print("  [OK] Sensitive data sanitized")
        print(f"  [OK] Password: {vars.get('password')}")
        print(f"  [OK] Normal var: {vars.get('normal_var')}")
        return True


def run_all_tests():
    """Run all error context tests."""
    print("="*80)
    print("ERROR CONTEXT LOGGING TESTS")
    print("="*80)

    tests = [
        test_capture_error_context,
        test_log_error_with_context,
        test_query_errors_by_correlation_id,
        test_get_recent_errors,
        test_format_error_for_user,
        test_stack_trace_preservation,
        test_sensitive_data_sanitization
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
