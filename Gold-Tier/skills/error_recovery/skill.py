"""
Error Recovery Skill - Agent Entry Point

Classify errors, check circuit breaker status, view recent errors,
and report health status for system components.
"""

from typing import Dict, Any, Optional
from .service import (
    classify_error_from_string, CircuitBreaker,
    ErrorLogger, HealthChecker
)


def classify_error(
    error_type: str,
    error_message: str
) -> Dict[str, Any]:
    """
    Classify an error and get recommended retry strategy.

    Use this skill when:
    - An error occurs and you need to decide whether to retry
    - You need to understand if an error is transient, auth-related, or a code bug
    - Determining severity and next steps for error handling

    Args:
        error_type: Exception class name (e.g., 'ConnectionError', 'TimeoutError')
        error_message: The error message string

    Returns:
        Dict with keys:
        - success (bool)
        - error_type (str): 'transient', 'auth', 'logic', 'system', 'unknown'
        - should_retry (bool): Whether to retry
        - strategy (str): Recommended action
        - severity (str): 'critical', 'medium', 'low'

    Example:
        result = classify_error(
            error_type="ConnectionError",
            error_message="Network timeout after 30s"
        )
        # result: {"error_type": "transient", "should_retry": True, ...}
    """
    try:
        return classify_error_from_string(error_type, error_message)
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_circuit_breaker_status(
    failure_threshold: int = 5,
    recovery_timeout: int = 300
) -> Dict[str, Any]:
    """
    Get circuit breaker status for a service.

    Args:
        failure_threshold: Failures before opening (default: 5)
        recovery_timeout: Seconds before testing recovery (default: 300)

    Returns:
        Dict with circuit breaker state and stats
    """
    try:
        breaker = CircuitBreaker(failure_threshold=failure_threshold, recovery_timeout=recovery_timeout)
        return {"success": True, "status": breaker.get_status()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_recent_errors(
    vault_path: str = "AI_Employee_Vault",
    component: Optional[str] = None,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Get recent errors from error logs.

    Use this skill when:
    - Investigating system issues
    - Reviewing error history for a component
    - Debugging recurring problems

    Args:
        vault_path: Path to AI Employee Vault
        component: Component name filter (None for all)
        hours: How far back to look (default: 24)

    Returns:
        Dict with list of recent errors
    """
    try:
        logger = ErrorLogger(vault_path=vault_path)
        errors = logger.get_recent_errors(component=component, hours=hours)
        return {"success": True, "errors": errors, "count": len(errors)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def report_health_status(
    component: str,
    status: str,
    vault_path: str = "AI_Employee_Vault",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Report a component's health status.

    Args:
        component: Component name (e.g., 'gmail_watcher')
        status: 'healthy', 'degraded', or 'unhealthy'
        vault_path: Path to AI Employee Vault
        details: Additional details dict

    Returns:
        Dict with success status
    """
    try:
        checker = HealthChecker(vault_path=vault_path)
        checker.report_status(component, status, details)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_health_status(
    component: Optional[str] = None,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Get health status for all components or a specific one.

    Args:
        component: Component name (None for all)
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with health status data
    """
    try:
        checker = HealthChecker(vault_path=vault_path)
        return {"success": True, "status": checker.get_status(component)}
    except Exception as e:
        return {"success": False, "error": str(e)}
