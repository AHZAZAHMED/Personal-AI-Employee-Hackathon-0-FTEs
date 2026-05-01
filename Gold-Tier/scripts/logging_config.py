"""
Centralized Logging Configuration for AI Employee - Gold Tier

Provides rotating file handlers to prevent unbounded log growth.
Fixes AUDIT-1 RISK #3: Unbounded Log Growth

Features:
- RotatingFileHandler with size limits
- Configurable backup count
- Separate logs per component
- Console output for development
- Production-ready retention policies

Usage:
    from logging_config import get_logger

    logger = get_logger('orchestrator', vault_path='AI_Employee_Vault')
    logger.info('Processing task...')
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# Default configuration
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per log file
DEFAULT_BACKUP_COUNT = 5  # Keep 5 backup files (50 MB total per component)
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_logger(
    name: str,
    vault_path: str = "AI_Employee_Vault",
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    console_output: bool = True,
    log_level: int = logging.INFO
) -> logging.Logger:
    """
    Get a configured logger with rotating file handler.

    Args:
        name: Logger name (e.g., 'orchestrator', 'gmail_watcher')
        vault_path: Path to AI Employee Vault
        max_bytes: Maximum size per log file (default: 10 MB)
        backup_count: Number of backup files to keep (default: 5)
        console_output: Whether to also log to console (default: True)
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger('orchestrator', vault_path='AI_Employee_Vault')
        logger.info('Starting orchestrator...')
        logger.error('Failed to process task', exc_info=True)
    """
    # Get or create logger
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    # Create logs directory
    vault = Path(vault_path)
    logs_dir = vault / 'Logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)

    # Add rotating file handler
    log_file = logs_dir / f'{name}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_component_logger(
    component: str,
    vault_path: str = "AI_Employee_Vault",
    **kwargs
) -> logging.Logger:
    """
    Get a logger for a specific component with standard naming.

    Components:
    - orchestrator: Main orchestration loop
    - approval_handler: Approval workflow
    - gmail_watcher: Gmail monitoring
    - ralph_wiggum: Autonomous loop
    - skill_registry: Skill discovery and execution
    - audit: Audit logging
    - error_context: Error tracking

    Args:
        component: Component name
        vault_path: Path to AI Employee Vault
        **kwargs: Additional arguments passed to get_logger()

    Returns:
        Configured logger instance
    """
    return get_logger(component, vault_path=vault_path, **kwargs)


def configure_root_logger(
    vault_path: str = "AI_Employee_Vault",
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT
):
    """
    Configure the root logger with rotating file handler.

    Use this for scripts that don't use get_logger() directly.

    Args:
        vault_path: Path to AI Employee Vault
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep
    """
    vault = Path(vault_path)
    logs_dir = vault / 'Logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / 'root.log'

    # Create formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )


def get_log_stats(vault_path: str = "AI_Employee_Vault") -> dict:
    """
    Get statistics about log files.

    Returns:
        Dictionary with log file statistics:
        - total_size: Total size of all log files in bytes
        - file_count: Number of log files
        - files: List of (filename, size) tuples
    """
    vault = Path(vault_path)
    logs_dir = vault / 'Logs'

    if not logs_dir.exists():
        return {'total_size': 0, 'file_count': 0, 'files': []}

    files = []
    total_size = 0

    for log_file in logs_dir.glob('*.log*'):
        if log_file.is_file():
            size = log_file.stat().st_size
            files.append((log_file.name, size))
            total_size += size

    return {
        'total_size': total_size,
        'file_count': len(files),
        'files': sorted(files, key=lambda x: x[1], reverse=True)
    }


def cleanup_old_logs(
    vault_path: str = "AI_Employee_Vault",
    days_to_keep: int = 30
):
    """
    Clean up log files older than specified days.

    Args:
        vault_path: Path to AI Employee Vault
        days_to_keep: Number of days to keep logs (default: 30)

    Returns:
        Number of files deleted
    """
    import time

    vault = Path(vault_path)
    logs_dir = vault / 'Logs'

    if not logs_dir.exists():
        return 0

    cutoff_time = time.time() - (days_to_keep * 86400)
    deleted = 0

    for log_file in logs_dir.glob('*.log*'):
        if log_file.is_file():
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted += 1

    return deleted


# Recommended configurations for different components
COMPONENT_CONFIGS = {
    'orchestrator': {
        'max_bytes': 10 * 1024 * 1024,  # 10 MB
        'backup_count': 5,  # 50 MB total
    },
    'gmail_watcher': {
        'max_bytes': 5 * 1024 * 1024,  # 5 MB
        'backup_count': 3,  # 15 MB total
    },
    'ralph_wiggum': {
        'max_bytes': 10 * 1024 * 1024,  # 10 MB
        'backup_count': 5,  # 50 MB total
    },
    'approval_handler': {
        'max_bytes': 5 * 1024 * 1024,  # 5 MB
        'backup_count': 5,  # 25 MB total
    },
    'skill_registry': {
        'max_bytes': 5 * 1024 * 1024,  # 5 MB
        'backup_count': 3,  # 15 MB total
    },
    'audit': {
        'max_bytes': 20 * 1024 * 1024,  # 20 MB (audit logs are important)
        'backup_count': 10,  # 200 MB total
    },
}


def get_recommended_logger(component: str, vault_path: str = "AI_Employee_Vault") -> logging.Logger:
    """
    Get a logger with recommended configuration for the component.

    Args:
        component: Component name (orchestrator, gmail_watcher, etc.)
        vault_path: Path to AI Employee Vault

    Returns:
        Configured logger instance
    """
    config = COMPONENT_CONFIGS.get(component, {
        'max_bytes': DEFAULT_MAX_BYTES,
        'backup_count': DEFAULT_BACKUP_COUNT
    })

    return get_logger(component, vault_path=vault_path, **config)
