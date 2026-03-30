"""
Error Recovery System for AI Employee - Gold Tier

Reusable error handling module for all watchers.
Provides retry logic, circuit breaker, and error classification.

Usage:
    from error_recovery import with_retry, CircuitBreaker, classify_error
    
    @with_retry(max_attempts=3, base_delay=1)
    def check_service():
        # Your code here
        pass
"""

import time
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Any, Dict, Optional, List
from enum import Enum


# ============================================================================
# ERROR CLASSIFICATION
# ============================================================================

class ErrorType(Enum):
    """Types of errors with retry strategies."""
    TRANSIENT = "transient"  # Retry with backoff (network timeout, rate limit)
    AUTH = "auth"  # Don't retry, alert human (expired token)
    LOGIC = "logic"  # Don't retry, fix code (parsing error)
    SYSTEM = "system"  # Retry immediately (disk full, permission)
    UNKNOWN = "unknown"  # Default, retry with caution


def classify_error(error: Exception) -> ErrorType:
    """
    Classify an error to determine retry strategy.
    
    Args:
        error: The exception to classify
        
    Returns:
        ErrorType enum value
    """
    error_msg = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Transient errors (retry with backoff)
    transient_keywords = [
        'timeout', 'timed out', 'connection', 'network',
        'rate limit', 'too many requests', '503', '502', '504',
        'temporary', 'transient', 'retry'
    ]
    
    # Auth errors (don't retry, alert human)
    auth_keywords = [
        'authentication', 'unauthorized', '401', '403',
        'token expired', 'invalid token', 'access denied',
        'permission denied', 'forbidden'
    ]
    
    # Logic errors (don't retry, fix code)
    logic_keywords = [
        'parse', 'invalid format', 'missing field',
        'type error', 'attribute error', 'key error'
    ]
    
    # System errors (retry immediately)
    system_keywords = [
        'disk full', 'no space', 'out of memory',
        'file locked', 'in use'
    ]
    
    # Check error message
    for keyword in auth_keywords:
        if keyword in error_msg or keyword in error_type:
            return ErrorType.AUTH
    
    for keyword in logic_keywords:
        if keyword in error_msg or keyword in error_type:
            return ErrorType.LOGIC
    
    for keyword in system_keywords:
        if keyword in error_msg or keyword in error_type:
            return ErrorType.SYSTEM
    
    for keyword in transient_keywords:
        if keyword in error_msg or keyword in error_type:
            return ErrorType.TRANSIENT
    
    return ErrorType.UNKNOWN


# ============================================================================
# RETRY DECORATOR
# ============================================================================

def with_retry(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator that adds retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds (exponential backoff)
        max_delay: Maximum delay between retries
        
    Usage:
        @with_retry(max_attempts=3, base_delay=1)
        def check_gmail():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_error = e
                    error_type = classify_error(e)
                    
                    # Don't retry auth or logic errors
                    if error_type in [ErrorType.AUTH, ErrorType.LOGIC]:
                        logging.error(f"{func.__name__}: {error_type.value} error - {e}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == max_attempts:
                        logging.error(f"{func.__name__}: Failed after {max_attempts} attempts - {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    
                    # Add jitter (±10%)
                    import random
                    jitter = delay * 0.1 * (random.random() * 2 - 1)
                    delay = delay + jitter
                    
                    logging.warning(
                        f"{func.__name__}: Attempt {attempt}/{max_attempts} failed - {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_error
            
        return wrapper
    return decorator


# ============================================================================
# CIRCUIT BREAKER PATTERN
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, don't try
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
        
        def check_service():
            with breaker:
                # Your code here
                pass
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing again
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def __enter__(self):
        """Enter context manager."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker: Testing recovery...")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type is not None:
            # Error occurred
            self._on_failure()
        else:
            # Success
            self._on_success()
        
        return False  # Don't suppress exceptions
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def _on_failure(self):
        """Handle failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"Circuit breaker OPEN after {self.failure_count} failures. "
                f"Will retry in {self.recovery_timeout}s"
            )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning("Circuit breaker: Recovery test failed, reopening")
    
    def _on_success(self):
        """Handle success."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.logger.info("Circuit breaker: Recovery successful, closing circuit")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'recovery_timeout': self.recovery_timeout
        }


# ============================================================================
# ENHANCED LOGGING WITH 90-DAY RETENTION
# ============================================================================

class ErrorLogger:
    """
    Enhanced error logging with 90-day retention.
    
    Usage:
        error_logger = ErrorLogger(vault_path)
        error_logger.log_error('gmail_watcher', error, context)
    """
    
    def __init__(self, vault_path: str, retention_days: int = 90):
        """
        Initialize error logger.
        
        Args:
            vault_path: Path to Obsidian vault
            retention_days: Days to retain logs (default: 90)
        """
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / 'Logs' / 'errors'
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = retention_days
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Clean old logs on init
        self._cleanup_old_logs()
    
    def log_error(
        self,
        component: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = 'ERROR'
    ):
        """
        Log an error with context.
        
        Args:
            component: Component name (e.g., 'gmail_watcher')
            error: The exception that occurred
            context: Additional context information
            severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'severity': severity,
            'context': context or {}
        }
        
        # Write to daily log file
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Also log to standard logging
        log_method = getattr(self.logger, severity.lower(), self.logger.error)
        log_method(f"{component}: {error}")
    
    def _cleanup_old_logs(self):
        """Delete logs older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        try:
            for log_file in self.logs_dir.glob('*.jsonl'):
                # Extract date from filename
                try:
                    file_date = datetime.strptime(log_file.stem, '%Y-%m-%d')
                    if file_date < cutoff_date:
                        log_file.unlink()
                        self.logger.info(f"Deleted old log: {log_file.name}")
                except ValueError:
                    continue
        except Exception as e:
            self.logger.error(f"Error cleaning up logs: {e}")
    
    def get_recent_errors(
        self,
        component: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent errors for a component.
        
        Args:
            component: Component name (None for all)
            hours: Number of hours to look back
            
        Returns:
            List of error log entries
        """
        errors = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get log files for the time period
        for log_file in self.logs_dir.glob('*.jsonl'):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            
                            if entry_time >= cutoff_time:
                                if component is None or entry.get('component') == component:
                                    errors.append(entry)
                        except:
                            continue
            except:
                continue
        
        return errors


# ============================================================================
# HEALTH CHECK SYSTEM
# ============================================================================

class HealthChecker:
    """
    Health check system for watchers.
    
    Usage:
        health = HealthChecker(vault_path)
        health.report_status('gmail_watcher', 'healthy')
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize health checker.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.health_file = self.vault_path / 'Logs' / 'health_status.json'
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def report_status(
        self,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Report component health status.
        
        Args:
            component: Component name
            status: Status (healthy, degraded, unhealthy)
            details: Additional details
        """
        health_data = self._load_health_status()
        
        health_data['components'][component] = {
            'status': status,
            'last_check': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self._save_health_status(health_data)
    
    def report_error(
        self,
        component: str,
        error: Exception,
        recoverable: bool = True
    ):
        """
        Report an error for a component.
        
        Args:
            component: Component name
            error: The exception
            recoverable: Whether the error is recoverable
        """
        status = 'degraded' if recoverable else 'unhealthy'
        
        self.report_status(component, status, {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'recoverable': recoverable
        })
    
    def get_status(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get health status for a component or all.
        
        Args:
            component: Component name (None for all)
            
        Returns:
            Health status dictionary
        """
        health_data = self._load_health_status()
        
        if component:
            return health_data['components'].get(component, {
                'status': 'unknown',
                'last_check': None
            })
        
        return health_data
    
    def _load_health_status(self) -> Dict[str, Any]:
        """Load health status from file."""
        if self.health_file.exists():
            try:
                with open(self.health_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'last_updated': datetime.now().isoformat(),
            'components': {}
        }
    
    def _save_health_status(self, health_data: Dict[str, Any]):
        """Save health status to file."""
        health_data['last_updated'] = datetime.now().isoformat()
        
        with open(self.health_file, 'w', encoding='utf-8') as f:
            json.dump(health_data, f, indent=2)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_error_recovery(vault_path: str) -> tuple:
    """
    Create error recovery components for a watcher.
    
    Args:
        vault_path: Path to Obsidian vault
        
    Returns:
        Tuple of (ErrorLogger, HealthChecker, CircuitBreaker)
    """
    error_logger = ErrorLogger(vault_path)
    health_checker = HealthChecker(vault_path)
    circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
    
    return error_logger, health_checker, circuit_breaker


def safe_execute(
    func: Callable,
    component: str,
    error_logger: ErrorLogger,
    health_checker: HealthChecker,
    default_return: Any = None
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        component: Component name
        error_logger: ErrorLogger instance
        health_checker: HealthChecker instance
        default_return: Default value to return on error
        
    Returns:
        Function result or default_return
    """
    try:
        result = func()
        health_checker.report_status(component, 'healthy')
        return result
        
    except Exception as e:
        error_type = classify_error(e)
        recoverable = error_type in [ErrorType.TRANSIENT, ErrorType.SYSTEM]
        
        error_logger.log_error(component, e, {
            'function': func.__name__,
            'recoverable': recoverable
        })
        
        health_checker.report_error(component, e, recoverable)
        
        return default_return


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Example: How to use error recovery in a watcher
    
    logging.basicConfig(level=logging.INFO)
    
    # Create recovery components
    error_logger = ErrorLogger('AI_Employee_Vault')
    health_checker = HealthChecker('AI_Employee_Vault')
    circuit_breaker = CircuitBreaker()
    
    # Example 1: Using retry decorator
    @with_retry(max_attempts=3, base_delay=1)
    def check_service():
        """Simulate a service check that might fail."""
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise ConnectionError("Network timeout")
        return "Success!"
    
    try:
        result = check_service()
        print(f"Service check: {result}")
    except Exception as e:
        print(f"Service check failed: {e}")
    
    # Example 2: Using circuit breaker
    def check_with_breaker():
        """Check service with circuit breaker."""
        try:
            with circuit_breaker:
                return check_service()
        except Exception as e:
            return f"Circuit breaker: {e}"
    
    result = check_with_breaker()
    print(f"Circuit breaker test: {result}")
    
    # Example 3: Safe execute
    result = safe_execute(
        check_service,
        'test_service',
        error_logger,
        health_checker,
        default_return="Failed"
    )
    print(f"Safe execute: {result}")
    
    # Example 4: Check health status
    status = health_checker.get_status()
    print(f"Health status: {status}")
