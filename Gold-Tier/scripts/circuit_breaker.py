"""
Circuit Breaker Pattern - Error Recovery and Graceful Degradation

Prevents cascading failures by detecting when external services are failing
and temporarily blocking requests to give them time to recover.

Solves AUDIT-1 RISK #1: NO ERROR RECOVERY STRATEGY

Critical for:
- Gmail API calls (email sending)
- Odoo API calls (invoice creation)
- Facebook/Instagram/LinkedIn API calls (social posting)
- Any external service that can fail

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests blocked immediately
- HALF_OPEN: Testing recovery, limited requests allowed

Usage:
    from circuit_breaker import circuit_breaker, CircuitBreaker

    # Decorator (recommended)
    @circuit_breaker('gmail_api', failure_threshold=5, timeout=60)
    def send_email(to, subject, body):
        return gmail_service.send(to, subject, body)

    # Manual usage
    breaker = CircuitBreaker('odoo_api')
    if breaker.can_execute():
        try:
            result = odoo_client.create_invoice(...)
            breaker.record_success()
        except Exception as e:
            breaker.record_failure()
            raise
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Tracks failures and automatically opens circuit when threshold exceeded.
    """

    def __init__(self, name: str, failure_threshold: int = 5,
                 timeout: int = 60, success_threshold: int = 2,
                 vault_path: str = "AI_Employee_Vault"):
        """
        Initialize circuit breaker.

        Args:
            name: Unique name for this circuit (e.g., 'gmail_api', 'odoo_api')
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (open → half-open)
            success_threshold: Successes needed in half-open to close circuit
            vault_path: Path to AI Employee Vault for state persistence
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.vault_path = Path(vault_path)

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None

        # Load persisted state
        self._load_state()

    def _get_state_file(self) -> Path:
        """Get path to state file."""
        state_dir = self.vault_path / "Logs" / "circuit_breakers"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / f"{self.name}.json"

    def _load_state(self):
        """Load circuit breaker state from disk."""
        state_file = self._get_state_file()
        if not state_file.exists():
            return

        try:
            with open(state_file, 'r') as f:
                data = json.load(f)

            self.state = CircuitState(data.get('state', 'closed'))
            self.failure_count = data.get('failure_count', 0)
            self.success_count = data.get('success_count', 0)

            if data.get('last_failure_time'):
                self.last_failure_time = datetime.fromisoformat(data['last_failure_time'])
            if data.get('opened_at'):
                self.opened_at = datetime.fromisoformat(data['opened_at'])

            logger.info(f"Circuit breaker '{self.name}' loaded: state={self.state.value}")

        except Exception as e:
            logger.warning(f"Failed to load circuit breaker state: {e}")

    def _save_state(self):
        """Save circuit breaker state to disk."""
        state_file = self._get_state_file()

        data = {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'updated_at': datetime.now().isoformat()
        }

        try:
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save circuit breaker state: {e}")

    def can_execute(self) -> bool:
        """
        Check if request can be executed.

        Returns:
            True if request should proceed, False if blocked
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.opened_at and datetime.now() - self.opened_at >= timedelta(seconds=self.timeout):
                # Transition to half-open
                self._transition_to_half_open()
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests in half-open state
            return True

        return False

    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(f"Circuit breaker '{self.name}': success {self.success_count}/{self.success_threshold}")

            if self.success_count >= self.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
                self._save_state()

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        logger.warning(f"Circuit breaker '{self.name}': failure {self.failure_count}/{self.failure_threshold}")

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open → back to open
            self._transition_to_open()

        self._save_state()

    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        self.success_count = 0
        logger.error(f"Circuit breaker '{self.name}' OPENED (failures: {self.failure_count})")
        self._save_state()

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker '{self.name}' HALF-OPEN (testing recovery)")
        self._save_state()

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        logger.info(f"Circuit breaker '{self.name}' CLOSED (recovered)")
        self._save_state()

    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'failure_threshold': self.failure_threshold,
            'success_threshold': self.success_threshold,
            'timeout': self.timeout,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None
        }

    def reset(self):
        """Reset circuit breaker to closed state."""
        self._transition_to_closed()
        logger.info(f"Circuit breaker '{self.name}' manually reset")


# Global registry of circuit breakers
_circuit_breakers = {}


def get_circuit_breaker(name: str, failure_threshold: int = 5,
                        timeout: int = 60, success_threshold: int = 2,
                        vault_path: str = "AI_Employee_Vault") -> CircuitBreaker:
    """
    Get or create a circuit breaker.

    Args:
        name: Unique name for this circuit
        failure_threshold: Number of failures before opening
        timeout: Seconds to wait before recovery attempt
        success_threshold: Successes needed to close circuit
        vault_path: Path to AI Employee Vault

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            timeout=timeout,
            success_threshold=success_threshold,
            vault_path=vault_path
        )
    return _circuit_breakers[name]


def circuit_breaker(name: str, failure_threshold: int = 5,
                    timeout: int = 60, success_threshold: int = 2,
                    vault_path: str = "AI_Employee_Vault",
                    fallback: Optional[Callable] = None):
    """
    Decorator to wrap function with circuit breaker.

    Args:
        name: Unique name for this circuit
        failure_threshold: Number of failures before opening
        timeout: Seconds to wait before recovery attempt
        success_threshold: Successes needed to close circuit
        vault_path: Path to AI Employee Vault
        fallback: Optional fallback function to call when circuit is open

    Usage:
        @circuit_breaker('gmail_api', failure_threshold=5, timeout=60)
        def send_email(to, subject, body):
            return gmail_service.send(to, subject, body)
    """
    def decorator(func: Callable) -> Callable:
        breaker = get_circuit_breaker(name, failure_threshold, timeout, success_threshold, vault_path)

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check if circuit allows execution
            if not breaker.can_execute():
                logger.warning(f"Circuit breaker '{name}' is OPEN, blocking call to {func.__name__}")

                if fallback:
                    logger.info(f"Using fallback for {func.__name__}")
                    return fallback(*args, **kwargs)

                raise CircuitBreakerError(f"Circuit breaker '{name}' is open")

            # Execute function
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise

        return wrapper
    return decorator


def get_all_circuit_breakers(vault_path: str = "AI_Employee_Vault") -> list:
    """
    Get state of all circuit breakers.

    Args:
        vault_path: Path to AI Employee Vault

    Returns:
        List of circuit breaker state dicts
    """
    state_dir = Path(vault_path) / "Logs" / "circuit_breakers"
    if not state_dir.exists():
        return []

    breakers = []
    for state_file in state_dir.glob("*.json"):
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
                breakers.append(data)
        except Exception:
            continue

    return breakers


def reset_circuit_breaker(name: str, vault_path: str = "AI_Employee_Vault"):
    """
    Reset a circuit breaker to closed state.

    Args:
        name: Circuit breaker name
        vault_path: Path to AI Employee Vault
    """
    breaker = get_circuit_breaker(name, vault_path=vault_path)
    breaker.reset()
