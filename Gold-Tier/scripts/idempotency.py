"""
Idempotency Key System - Prevent Duplicate Operations

Prevents duplicate operations during retries by tracking processed operations
using correlation IDs as idempotency keys.

Solves AUDIT-1 BLOCKER #5: NO DUPLICATE PREVENTION
Solves AUDIT-1 RISK #4: ODOO DUPLICATE INVOICES

Critical for:
- Invoice creation (prevent duplicate billing)
- Email sending (prevent double-send)
- Social posting (prevent duplicate posts)
- Payment recording (prevent double-charge)

Usage:
    from idempotency import check_idempotency, record_operation

    # Before performing operation
    cached = check_idempotency(correlation_id, 'invoice_creation')
    if cached:
        return cached['result']

    # Perform operation
    result = create_invoice(...)

    # Record successful operation
    record_operation(correlation_id, 'invoice_creation', result, ttl_hours=720)
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def check_idempotency(
    idempotency_key: str,
    operation_type: str,
    vault_path: str = "AI_Employee_Vault"
) -> Optional[Dict[str, Any]]:
    """
    Check if operation was already performed.

    Args:
        idempotency_key: Unique key (usually correlation_id)
        operation_type: Type of operation (e.g., 'invoice_creation', 'email_send')
        vault_path: Path to AI Employee Vault

    Returns:
        Cached result dict if operation already performed, None otherwise
    """
    if not idempotency_key:
        return None

    vault = Path(vault_path)
    idempotency_dir = vault / "Logs" / "idempotency"

    if not idempotency_dir.exists():
        return None

    # Search last 30 days of logs
    today = datetime.now()
    for i in range(30):
        date = today - timedelta(days=i)
        log_file = idempotency_dir / f"{date.strftime('%Y-%m-%d')}_idempotency.jsonl"

        if not log_file.exists():
            continue

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Check if this is our operation
                        if (entry.get('idempotency_key') == idempotency_key and
                            entry.get('operation_type') == operation_type):

                            # Check if expired
                            if _is_expired(entry):
                                continue

                            logger.info(f"Idempotency hit: {idempotency_key} ({operation_type})")
                            return entry

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Error reading idempotency log: {e}")
            continue

    return None


def record_operation(
    idempotency_key: str,
    operation_type: str,
    result: Dict[str, Any],
    vault_path: str = "AI_Employee_Vault",
    ttl_hours: int = 720
) -> bool:
    """
    Record successful operation for idempotency checking.

    Args:
        idempotency_key: Unique key (usually correlation_id)
        operation_type: Type of operation
        result: Operation result to cache
        vault_path: Path to AI Employee Vault
        ttl_hours: Time-to-live in hours (default: 30 days)

    Returns:
        True if recorded successfully, False otherwise
    """
    if not idempotency_key:
        return False

    vault = Path(vault_path)
    idempotency_dir = vault / "Logs" / "idempotency"
    idempotency_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    log_file = idempotency_dir / f"{today}_idempotency.jsonl"

    entry = {
        'idempotency_key': idempotency_key,
        'operation_type': operation_type,
        'timestamp': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
        'result': result
    }

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        logger.info(f"Recorded idempotency: {idempotency_key} ({operation_type})")
        return True

    except Exception as e:
        logger.error(f"Failed to record idempotency: {e}")
        return False


def is_duplicate(
    idempotency_key: str,
    operation_type: str,
    vault_path: str = "AI_Employee_Vault"
) -> bool:
    """
    Check if operation is a duplicate (boolean check only).

    Args:
        idempotency_key: Unique key
        operation_type: Type of operation
        vault_path: Path to AI Employee Vault

    Returns:
        True if operation already performed, False otherwise
    """
    return check_idempotency(idempotency_key, operation_type, vault_path) is not None


def get_cached_result(
    idempotency_key: str,
    operation_type: str,
    vault_path: str = "AI_Employee_Vault"
) -> Optional[Dict[str, Any]]:
    """
    Get cached result from previous operation.

    Args:
        idempotency_key: Unique key
        operation_type: Type of operation
        vault_path: Path to AI Employee Vault

    Returns:
        Cached result dict or None
    """
    entry = check_idempotency(idempotency_key, operation_type, vault_path)
    return entry.get('result') if entry else None


def _is_expired(entry: Dict[str, Any]) -> bool:
    """Check if idempotency entry has expired."""
    try:
        expires_at = datetime.fromisoformat(entry.get('expires_at', ''))
        return datetime.now() > expires_at
    except (ValueError, TypeError):
        return False


def cleanup_expired(
    vault_path: str = "AI_Employee_Vault",
    days: int = 30
) -> int:
    """
    Remove expired idempotency entries.

    Args:
        vault_path: Path to AI Employee Vault
        days: Number of days to keep

    Returns:
        Number of entries cleaned up
    """
    vault = Path(vault_path)
    idempotency_dir = vault / "Logs" / "idempotency"

    if not idempotency_dir.exists():
        return 0

    cleaned = 0
    cutoff = datetime.now() - timedelta(days=days)

    for log_file in idempotency_dir.glob("*_idempotency.jsonl"):
        try:
            # Parse date from filename
            date_str = log_file.stem.split('_')[0]
            file_date = datetime.strptime(date_str, '%Y-%m-%d')

            # Delete old files
            if file_date < cutoff:
                log_file.unlink()
                cleaned += 1
                logger.info(f"Deleted old idempotency log: {log_file.name}")

        except Exception as e:
            logger.error(f"Error cleaning up {log_file}: {e}")
            continue

    return cleaned


def get_operation_stats(
    vault_path: str = "AI_Employee_Vault",
    days: int = 7
) -> Dict[str, Any]:
    """
    Get statistics about idempotency operations.

    Args:
        vault_path: Path to AI Employee Vault
        days: Number of days to analyze

    Returns:
        Dict with operation statistics
    """
    vault = Path(vault_path)
    idempotency_dir = vault / "Logs" / "idempotency"

    if not idempotency_dir.exists():
        return {'total_operations': 0, 'by_type': {}}

    stats = {'total_operations': 0, 'by_type': {}}
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        log_file = idempotency_dir / f"{date.strftime('%Y-%m-%d')}_idempotency.jsonl"

        if not log_file.exists():
            continue

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats['total_operations'] += 1

                        op_type = entry.get('operation_type', 'unknown')
                        stats['by_type'][op_type] = stats['by_type'].get(op_type, 0) + 1

                    except json.JSONDecodeError:
                        continue

        except Exception:
            continue

    return stats
