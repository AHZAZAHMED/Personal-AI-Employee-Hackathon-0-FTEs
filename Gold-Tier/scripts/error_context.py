"""
Error Context Logger - Rich Error Capture for Debugging

Captures comprehensive error context including:
- Stack traces
- Input parameters
- System state
- Correlation IDs
- Request/response data

Solves AUDIT-2 DEGRADED #2: Error Context Loss

Usage:
    from error_context import capture_error_context, log_error_with_context

    try:
        result = some_operation(param1, param2)
    except Exception as e:
        error_context = capture_error_context(e, locals())
        log_error_with_context(error_context, vault_path)
        return {"success": False, "error": str(e), "error_id": error_context['error_id']}
"""

import sys
import json
import uuid
import traceback
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def capture_error_context(
    exception: Exception,
    local_vars: Dict[str, Any] = None,
    correlation_id: str = "",
    sanitize_sensitive: bool = True
) -> Dict[str, Any]:
    """
    Capture comprehensive error context for debugging.

    Args:
        exception: The exception that was raised
        local_vars: Local variables from locals() at exception site
        correlation_id: Correlation ID for audit trail
        sanitize_sensitive: Remove sensitive data from context

    Returns:
        Dict with complete error context
    """
    error_id = str(uuid.uuid4())[:8]  # Short error ID for reference

    # Capture exception details
    exc_type, exc_value, exc_traceback = sys.exc_info()

    context = {
        'error_id': error_id,
        'timestamp': datetime.now().isoformat(),
        'correlation_id': correlation_id,
        'exception': {
            'type': type(exception).__name__,
            'message': str(exception),
            'args': exception.args if hasattr(exception, 'args') else []
        },
        'stack_trace': traceback.format_exc(),
        'traceback_lines': traceback.format_tb(exc_traceback) if exc_traceback else [],
        'local_variables': {},
        'system_state': _capture_system_state()
    }

    # Capture local variables (sanitized)
    if local_vars:
        context['local_variables'] = _sanitize_variables(local_vars, sanitize_sensitive)

    return context


def log_error_with_context(
    error_context: Dict[str, Any],
    vault_path: str = "AI_Employee_Vault"
) -> str:
    """
    Log error context to file for debugging.

    Args:
        error_context: Error context from capture_error_context()
        vault_path: Path to AI Employee Vault

    Returns:
        Path to error log file
    """
    vault = Path(vault_path)
    error_logs = vault / "Logs" / "errors"
    error_logs.mkdir(parents=True, exist_ok=True)

    # Create daily error log file
    today = datetime.now().strftime('%Y-%m-%d')
    error_file = error_logs / f"{today}_errors.jsonl"

    try:
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_context, ensure_ascii=False) + '\n')

        logger.info(f"Error logged: {error_context['error_id']} -> {error_file}")
        return str(error_file)

    except Exception as e:
        logger.error(f"Failed to log error context: {e}")
        return ""


def _sanitize_variables(variables: Dict[str, Any], sanitize: bool) -> Dict[str, Any]:
    """
    Sanitize local variables to remove sensitive data.

    Args:
        variables: Dictionary of local variables
        sanitize: Whether to sanitize sensitive data

    Returns:
        Sanitized variables dictionary
    """
    if not sanitize:
        return _serialize_variables(variables)

    sanitized = {}
    sensitive_keys = {
        'password', 'token', 'secret', 'api_key', 'auth', 'credential',
        'private_key', 'access_token', 'refresh_token', 'session_id'
    }

    for key, value in variables.items():
        # Skip internal Python variables
        if key.startswith('_'):
            continue

        # Check if key contains sensitive terms
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
            continue

        # Serialize and truncate large values
        try:
            serialized = _serialize_value(value)
            if isinstance(serialized, str) and len(serialized) > 500:
                sanitized[key] = serialized[:500] + "... [TRUNCATED]"
            else:
                sanitized[key] = serialized
        except Exception:
            sanitized[key] = f"<{type(value).__name__}>"

    return sanitized


def _serialize_variables(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize variables for JSON storage."""
    serialized = {}
    for key, value in variables.items():
        if key.startswith('_'):
            continue
        try:
            serialized[key] = _serialize_value(value)
        except Exception:
            serialized[key] = f"<{type(value).__name__}>"
    return serialized


def _serialize_value(value: Any) -> Any:
    """Serialize a single value for JSON storage."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value[:10]]  # Limit to 10 items
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in list(value.items())[:10]}
    elif isinstance(value, Path):
        return str(value)
    elif hasattr(value, '__dict__'):
        return f"<{type(value).__name__} object>"
    else:
        return str(value)


def _capture_system_state() -> Dict[str, Any]:
    """Capture current system state."""
    import psutil
    import platform

    try:
        process = psutil.Process()
        return {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
            'cpu_percent': process.cpu_percent(interval=0.1),
            'num_threads': process.num_threads(),
            'cwd': str(Path.cwd())
        }
    except Exception:
        return {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'cwd': str(Path.cwd())
        }


def format_error_for_user(error_context: Dict[str, Any]) -> str:
    """
    Format error context for user-friendly display.

    Args:
        error_context: Error context dictionary

    Returns:
        Formatted error message
    """
    exc = error_context['exception']
    return (
        f"Error {error_context['error_id']}: {exc['type']} - {exc['message']}\n"
        f"Time: {error_context['timestamp']}\n"
        f"See logs for details: AI_Employee_Vault/Logs/errors/"
    )


def query_errors_by_correlation_id(
    correlation_id: str,
    vault_path: str = "AI_Employee_Vault",
    days: int = 30
) -> list:
    """
    Query all errors for a specific correlation ID.

    Args:
        correlation_id: Correlation ID to search for
        vault_path: Path to AI Employee Vault
        days: Number of days to search back

    Returns:
        List of error contexts matching the correlation ID
    """
    from datetime import timedelta

    vault = Path(vault_path)
    error_logs = vault / "Logs" / "errors"

    if not error_logs.exists():
        return []

    errors = []
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        error_file = error_logs / f"{date.strftime('%Y-%m-%d')}_errors.jsonl"

        if not error_file.exists():
            continue

        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        error = json.loads(line.strip())
                        if error.get('correlation_id') == correlation_id:
                            errors.append(error)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue

    return errors


def get_recent_errors(
    vault_path: str = "AI_Employee_Vault",
    limit: int = 10
) -> list:
    """
    Get most recent errors.

    Args:
        vault_path: Path to AI Employee Vault
        limit: Maximum number of errors to return

    Returns:
        List of recent error contexts
    """
    vault = Path(vault_path)
    error_logs = vault / "Logs" / "errors"

    if not error_logs.exists():
        return []

    errors = []
    today = datetime.now().strftime('%Y-%m-%d')
    error_file = error_logs / f"{today}_errors.jsonl"

    if not error_file.exists():
        return []

    try:
        with open(error_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in reversed(lines[-limit:]):
                try:
                    errors.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return errors
