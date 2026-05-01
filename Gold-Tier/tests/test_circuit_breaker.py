"""
Test Circuit Breaker Pattern

Tests the circuit breaker system for error recovery and graceful degradation:
- State transitions (closed → open → half-open → closed)
- Failure threshold
- Timeout recovery
- Success threshold
- Decorator usage
- Fallback functionality
- State persistence
"""

import sys
import time
import tempfile
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    circuit_breaker,
    get_circuit_breaker,
    get_all_circuit_breakers,
    reset_circuit_breaker
)


def test_initial_state():
    """Test circuit breaker starts in closed state."""
    print("\n[TEST] Initial State")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', vault_path=tmpdir)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.can_execute() is True

        print("  [OK] Circuit breaker starts in CLOSED state")
        return True


def test_failure_threshold():
    """Test circuit opens after failure threshold."""
    print("\n[TEST] Failure Threshold")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', failure_threshold=3, vault_path=tmpdir)

        # Record failures
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1

        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 2

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

        print("  [OK] Circuit opens after failure threshold")
        return True


def test_open_blocks_requests():
    """Test open circuit blocks requests."""
    print("\n[TEST] Open Circuit Blocks Requests")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', failure_threshold=2, vault_path=tmpdir)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Should block requests
        assert breaker.can_execute() is False

        print("  [OK] Open circuit blocks requests")
        return True


def test_timeout_recovery():
    """Test circuit transitions to half-open after timeout."""
    print("\n[TEST] Timeout Recovery")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', failure_threshold=2, timeout=2, vault_path=tmpdir)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Should block immediately
        assert breaker.can_execute() is False

        # Wait for timeout
        time.sleep(2.1)

        # Should transition to half-open
        assert breaker.can_execute() is True
        assert breaker.state == CircuitState.HALF_OPEN

        print("  [OK] Circuit transitions to HALF-OPEN after timeout")
        return True


def test_half_open_success():
    """Test half-open transitions to closed after successes."""
    print("\n[TEST] Half-Open Success Recovery")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', failure_threshold=2, timeout=1, success_threshold=2, vault_path=tmpdir)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)
        breaker.can_execute()  # Trigger transition to half-open
        assert breaker.state == CircuitState.HALF_OPEN

        # Record successes
        breaker.record_success()
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.success_count == 1

        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.success_count == 0

        print("  [OK] Half-open transitions to CLOSED after successes")
        return True


def test_half_open_failure():
    """Test half-open returns to open on failure."""
    print("\n[TEST] Half-Open Failure")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', failure_threshold=2, timeout=1, vault_path=tmpdir)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)
        breaker.can_execute()  # Trigger transition to half-open
        assert breaker.state == CircuitState.HALF_OPEN

        # Record failure - should go back to open
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        print("  [OK] Half-open returns to OPEN on failure")
        return True


def test_decorator_success():
    """Test circuit breaker decorator with successful calls."""
    print("\n[TEST] Decorator Success")

    with tempfile.TemporaryDirectory() as tmpdir:
        call_count = [0]

        @circuit_breaker('test-api', failure_threshold=3, vault_path=tmpdir)
        def api_call():
            call_count[0] += 1
            return "success"

        # Should work normally
        result = api_call()
        assert result == "success"
        assert call_count[0] == 1

        result = api_call()
        assert result == "success"
        assert call_count[0] == 2

        print("  [OK] Decorator allows successful calls")
        return True


def test_decorator_failure():
    """Test circuit breaker decorator with failures."""
    print("\n[TEST] Decorator Failure")

    with tempfile.TemporaryDirectory() as tmpdir:
        call_count = [0]

        @circuit_breaker('test-api-failure', failure_threshold=2, vault_path=tmpdir)
        def api_call():
            call_count[0] += 1
            raise Exception("API error")

        # First failure
        try:
            api_call()
            assert False, "Should raise exception"
        except Exception as e:
            assert str(e) == "API error"
        assert call_count[0] == 1

        # Second failure - should open circuit
        try:
            api_call()
            assert False, "Should raise exception"
        except Exception as e:
            assert str(e) == "API error"
        assert call_count[0] == 2

        # Third call - should be blocked by circuit breaker
        try:
            api_call()
            assert False, "Should raise CircuitBreakerError"
        except CircuitBreakerError:
            pass  # Expected
        except Exception as e:
            assert False, f"Should raise CircuitBreakerError, got {type(e).__name__}: {e}"
        assert call_count[0] == 2  # Function not called

        print("  [OK] Decorator blocks calls when circuit open")
        return True


def test_decorator_fallback():
    """Test circuit breaker decorator with fallback."""
    print("\n[TEST] Decorator Fallback")

    with tempfile.TemporaryDirectory() as tmpdir:
        def fallback_func():
            return "fallback_result"

        @circuit_breaker('test-api-fallback', failure_threshold=2, vault_path=tmpdir, fallback=fallback_func)
        def api_call():
            raise Exception("API error")

        # Open circuit
        try:
            api_call()
        except Exception:
            pass
        try:
            api_call()
        except Exception:
            pass

        # Should use fallback
        result = api_call()
        assert result == "fallback_result"

        print("  [OK] Decorator uses fallback when circuit open")
        return True


def test_state_persistence():
    """Test circuit breaker state persists to disk."""
    print("\n[TEST] State Persistence")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create breaker and open it
        breaker1 = CircuitBreaker('test-service', failure_threshold=2, vault_path=tmpdir)
        breaker1.record_failure()
        breaker1.record_failure()
        assert breaker1.state == CircuitState.OPEN

        # Create new breaker with same name - should load state
        breaker2 = CircuitBreaker('test-service', failure_threshold=2, vault_path=tmpdir)
        assert breaker2.state == CircuitState.OPEN
        assert breaker2.failure_count == 2

        print("  [OK] Circuit breaker state persists")
        return True


def test_reset():
    """Test manual circuit breaker reset."""
    print("\n[TEST] Manual Reset")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', failure_threshold=2, vault_path=tmpdir)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Reset
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.can_execute() is True

        print("  [OK] Manual reset works")
        return True


def test_multiple_breakers():
    """Test multiple independent circuit breakers."""
    print("\n[TEST] Multiple Circuit Breakers")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker1 = CircuitBreaker('service-1', failure_threshold=2, vault_path=tmpdir)
        breaker2 = CircuitBreaker('service-2', failure_threshold=2, vault_path=tmpdir)

        # Open breaker1
        breaker1.record_failure()
        breaker1.record_failure()
        assert breaker1.state == CircuitState.OPEN

        # breaker2 should still be closed
        assert breaker2.state == CircuitState.CLOSED
        assert breaker2.can_execute() is True

        print("  [OK] Multiple circuit breakers work independently")
        return True


def test_get_all_breakers():
    """Test getting all circuit breaker states."""
    print("\n[TEST] Get All Circuit Breakers")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple breakers
        breaker1 = CircuitBreaker('service-1', vault_path=tmpdir)
        breaker2 = CircuitBreaker('service-2', vault_path=tmpdir)
        breaker1.record_failure()
        breaker2.record_failure()

        # Get all breakers
        all_breakers = get_all_circuit_breakers(tmpdir)
        assert len(all_breakers) >= 2

        names = [b['name'] for b in all_breakers]
        assert 'service-1' in names
        assert 'service-2' in names

        print("  [OK] Get all circuit breakers works")
        return True


def test_success_resets_failures():
    """Test success resets failure count in closed state."""
    print("\n[TEST] Success Resets Failures")

    with tempfile.TemporaryDirectory() as tmpdir:
        breaker = CircuitBreaker('test-service', failure_threshold=3, vault_path=tmpdir)

        # Record some failures
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2
        assert breaker.state == CircuitState.CLOSED

        # Record success - should reset failures
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

        print("  [OK] Success resets failure count")
        return True


def run_all_tests():
    """Run all circuit breaker tests."""
    print("="*80)
    print("CIRCUIT BREAKER PATTERN TESTS")
    print("="*80)

    tests = [
        test_initial_state,
        test_failure_threshold,
        test_open_blocks_requests,
        test_timeout_recovery,
        test_half_open_success,
        test_half_open_failure,
        test_decorator_success,
        test_decorator_failure,
        test_decorator_fallback,
        test_state_persistence,
        test_reset,
        test_multiple_breakers,
        test_get_all_breakers,
        test_success_resets_failures
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
