"""
Error Recovery Service - Core Business Logic

Provides error classification, retry logic with exponential backoff,
circuit breaker pattern, error logging with 90-day retention, and
health checking.

No agent-related code — pure business logic only.
"""

import os
import time
import json
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Any, Dict, Optional, List
from enum import Enum


class ErrorType(Enum):
    TRANSIENT = "transient"
    AUTH = "auth"
    LOGIC = "logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


def classify_error(error: Exception) -> ErrorType:
    """Classify an error to determine retry strategy."""
    error_msg = str(error).lower()
    error_type = type(error).__name__.lower()

    for kw in ['authentication', 'unauthorized', '401', '403', 'token expired', 'invalid token', 'access denied', 'permission denied', 'forbidden']:
        if kw in error_msg or kw in error_type:
            return ErrorType.AUTH
    for kw in ['parse', 'invalid format', 'missing field', 'type error', 'attribute error', 'key error', 'keyerror', 'attributeerror', 'typeerror']:
        if kw in error_msg or kw in error_type:
            return ErrorType.LOGIC
    for kw in ['disk full', 'no space', 'out of memory', 'file locked', 'in use']:
        if kw in error_msg or kw in error_type:
            return ErrorType.SYSTEM
    for kw in ['timeout', 'timed out', 'connection', 'network', 'rate limit', 'too many requests', '503', '502', '504', 'temporary', 'transient', 'retry']:
        if kw in error_msg or kw in error_type:
            return ErrorType.TRANSIENT

    return ErrorType.UNKNOWN


def classify_error_from_string(error_type: str, error_message: str) -> Dict[str, Any]:
    """Classify an error from string inputs (for agent use)."""
    class FakeError(Exception):
        pass
    try:
        exc_class = getattr(__import__("builtins"), error_type, Exception)
        error = exc_class(error_message)
    except Exception:
        error = Exception(error_message)

    result = classify_error(error)
    strategies = {
        ErrorType.TRANSIENT: "Retry with exponential backoff",
        ErrorType.AUTH: "Don't retry — alert human, check credentials",
        ErrorType.LOGIC: "Don't retry — fix code bug",
        ErrorType.SYSTEM: "Retry immediately after short delay",
        ErrorType.UNKNOWN: "Retry with caution, max 2 attempts",
    }
    return {
        "success": True,
        "error_type": result.value,
        "should_retry": result in (ErrorType.TRANSIENT, ErrorType.SYSTEM, ErrorType.UNKNOWN),
        "strategy": strategies.get(result, "Unknown"),
        "severity": "critical" if result == ErrorType.AUTH else "medium" if result == ErrorType.UNKNOWN else "low"
    }


def with_retry(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator: retry with exponential backoff."""
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
                    if error_type in (ErrorType.AUTH, ErrorType.LOGIC):
                        logging.error(f"{func.__name__}: {error_type.value} error — {e}")
                        raise
                    if attempt == max_attempts:
                        logging.error(f"{func.__name__}: Failed after {max_attempts} attempts — {e}")
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    jitter = delay * 0.1 * (random.random() * 2 - 1)
                    delay = delay + jitter
                    logging.warning(f"{func.__name__}: Attempt {attempt}/{max_attempts} failed. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
            raise last_error
        return wrapper
    return decorator


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        self.logger = logging.getLogger(self.__class__.__name__)

    def __enter__(self):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker: Testing recovery...")
            else:
                raise Exception("Circuit breaker is OPEN — service unavailable")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._on_failure()
        else:
            self._on_success()
        return False

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning("Circuit breaker: Recovery test failed, reopening")

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.logger.info("Circuit breaker: Recovery successful")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "recovery_timeout": self.recovery_timeout
        }


class ErrorLogger:
    """Error logging with 90-day retention."""

    def __init__(self, vault_path: str, retention_days: int = 90):
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / "Logs" / "errors"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self._cleanup_old_logs()

    def log_error(self, component: str, error: Exception,
                  context: Optional[Dict[str, Any]] = None, severity: str = "ERROR"):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity,
            "context": context or {}
        }
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_recent_errors(self, component: Optional[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        errors = []
        cutoff = datetime.now() - timedelta(hours=hours)
        for log_file in self.logs_dir.glob("*.jsonl"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if datetime.fromisoformat(entry["timestamp"]) >= cutoff:
                                if component is None or entry.get("component") == component:
                                    errors.append(entry)
                        except Exception:
                            continue
            except Exception:
                continue
        return errors

    def _cleanup_old_logs(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        try:
            for log_file in self.logs_dir.glob("*.jsonl"):
                try:
                    file_date = datetime.strptime(log_file.stem, "%Y-%m-%d")
                    if file_date < cutoff:
                        log_file.unlink()
                except ValueError:
                    continue
        except Exception:
            pass


class HealthChecker:
    """Health check system for watchers."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.health_file = self.vault_path / "Logs" / "health_status.json"
        (self.vault_path / "Logs").mkdir(parents=True, exist_ok=True)

    def report_status(self, component: str, status: str, details: Optional[Dict[str, Any]] = None):
        data = self._load()
        data["components"][component] = {
            "status": status,
            "last_check": datetime.now().isoformat(),
            "details": details or {}
        }
        self._save(data)

    def report_error(self, component: str, error: Exception, recoverable: bool = True):
        status = "degraded" if recoverable else "unhealthy"
        self.report_status(component, status, {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "recoverable": recoverable
        })

    def get_status(self, component: Optional[str] = None) -> Dict[str, Any]:
        data = self._load()
        if component:
            return data["components"].get(component, {"status": "unknown", "last_check": None})
        return data

    def _load(self) -> Dict[str, Any]:
        if self.health_file.exists():
            try:
                return json.loads(self.health_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"last_updated": datetime.now().isoformat(), "components": {}}

    def _save(self, data: Dict[str, Any]):
        data["last_updated"] = datetime.now().isoformat()
        self.health_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
