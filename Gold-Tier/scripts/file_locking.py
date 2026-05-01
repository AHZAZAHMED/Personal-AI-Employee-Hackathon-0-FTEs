"""
File-Based Locking System - Prevent Concurrent Processing

Prevents multiple processes from processing the same task simultaneously
using file-based locks with timeout and stale lock cleanup.

Solves AUDIT-1 BLOCKER #5: NO DUPLICATE PREVENTION (concurrent processing)

Critical for:
- Orchestrator task processing (prevent duplicate processing)
- Approval file handling (prevent race conditions)
- File move operations (atomic operations)
- Multi-process coordination

Usage:
    from file_locking import acquire_lock, release_lock, FileLock

    # Manual lock management
    if acquire_lock('task-123', timeout=30):
        try:
            process_task()
        finally:
            release_lock('task-123')

    # Context manager (recommended)
    with FileLock('task-123', timeout=30):
        process_task()
"""

import os
import sys
import time
import json
import logging
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Platform-specific imports
if sys.platform == 'win32':
    import msvcrt
    PLATFORM = 'windows'
else:
    import fcntl
    PLATFORM = 'posix'


class LockError(Exception):
    """Raised when lock cannot be acquired."""
    pass


class LockTimeout(LockError):
    """Raised when lock acquisition times out."""
    pass


def _get_lock_dir(vault_path: str = "AI_Employee_Vault") -> Path:
    """Get or create locks directory."""
    vault = Path(vault_path)
    lock_dir = vault / "Locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir


def _get_lock_file(resource_id: str, vault_path: str = "AI_Employee_Vault") -> Path:
    """Get lock file path for resource."""
    lock_dir = _get_lock_dir(vault_path)
    # Sanitize resource_id for filename
    safe_id = resource_id.replace('/', '_').replace('\\', '_').replace(':', '_')
    return lock_dir / f"{safe_id}.lock"


def _write_lock_metadata(lock_file: Path, resource_id: str):
    """Write lock metadata (owner process, timestamp)."""
    metadata = {
        'resource_id': resource_id,
        'pid': os.getpid(),
        'timestamp': datetime.now().isoformat(),
        'hostname': os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'unknown'))
    }
    try:
        with open(lock_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write lock metadata: {e}")


def _read_lock_metadata(lock_file: Path) -> Optional[dict]:
    """Read lock metadata."""
    try:
        with open(lock_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def _is_process_alive(pid: int) -> bool:
    """Check if process is still running."""
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def _is_lock_stale(lock_file: Path, max_age_seconds: int = 3600) -> bool:
    """Check if lock is stale (process dead or too old)."""
    if not lock_file.exists():
        return False

    metadata = _read_lock_metadata(lock_file)
    if not metadata:
        # Can't read metadata, consider stale if file is old
        try:
            age = time.time() - lock_file.stat().st_mtime
            return age > max_age_seconds
        except Exception:
            return True

    # Check if owning process is alive
    pid = metadata.get('pid')
    if pid and not _is_process_alive(pid):
        logger.info(f"Lock is stale: process {pid} is dead")
        return True

    # Check age
    try:
        timestamp = datetime.fromisoformat(metadata.get('timestamp', ''))
        age = (datetime.now() - timestamp).total_seconds()
        if age > max_age_seconds:
            logger.info(f"Lock is stale: age {age}s exceeds max {max_age_seconds}s")
            return True
    except Exception:
        pass

    return False


def acquire_lock(resource_id: str, timeout: int = 30,
                 vault_path: str = "AI_Employee_Vault") -> bool:
    """
    Acquire a lock on a resource.

    Args:
        resource_id: Unique identifier for the resource
        timeout: Maximum seconds to wait for lock (0 = no wait)
        vault_path: Path to AI Employee Vault

    Returns:
        True if lock acquired, False if timeout

    Raises:
        LockTimeout: If lock cannot be acquired within timeout
    """
    lock_file = _get_lock_file(resource_id, vault_path)
    start_time = time.time()

    while True:
        # Check for stale lock and clean it up
        if lock_file.exists() and _is_lock_stale(lock_file):
            logger.info(f"Cleaning up stale lock: {resource_id}")
            try:
                lock_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove stale lock: {e}")

        # Try to acquire lock
        try:
            # Create lock file exclusively (fails if exists)
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)

            # Write metadata
            _write_lock_metadata(lock_file, resource_id)

            logger.info(f"Lock acquired: {resource_id}")
            return True

        except FileExistsError:
            # Lock already held
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(f"Lock timeout: {resource_id} (waited {elapsed:.1f}s)")
                return False

            # Wait and retry
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"Lock acquisition error: {e}")
            return False


def release_lock(resource_id: str, vault_path: str = "AI_Employee_Vault") -> bool:
    """
    Release a lock on a resource.

    Args:
        resource_id: Unique identifier for the resource
        vault_path: Path to AI Employee Vault

    Returns:
        True if lock released, False if lock not held or error
    """
    lock_file = _get_lock_file(resource_id, vault_path)

    if not lock_file.exists():
        logger.warning(f"Lock not held: {resource_id}")
        return False

    # Verify we own the lock
    metadata = _read_lock_metadata(lock_file)
    if metadata and metadata.get('pid') != os.getpid():
        logger.warning(f"Lock owned by different process: {resource_id}")
        return False

    try:
        lock_file.unlink()
        logger.info(f"Lock released: {resource_id}")
        return True
    except Exception as e:
        logger.error(f"Lock release error: {e}")
        return False


def is_locked(resource_id: str, vault_path: str = "AI_Employee_Vault") -> bool:
    """
    Check if a resource is locked.

    Args:
        resource_id: Unique identifier for the resource
        vault_path: Path to AI Employee Vault

    Returns:
        True if locked (and not stale), False otherwise
    """
    lock_file = _get_lock_file(resource_id, vault_path)

    if not lock_file.exists():
        return False

    # Check if stale
    if _is_lock_stale(lock_file):
        return False

    return True


def cleanup_stale_locks(max_age_seconds: int = 3600,
                        vault_path: str = "AI_Employee_Vault") -> int:
    """
    Clean up stale locks (dead processes or too old).

    Args:
        max_age_seconds: Maximum age for locks (default: 1 hour)
        vault_path: Path to AI Employee Vault

    Returns:
        Number of stale locks cleaned up
    """
    lock_dir = _get_lock_dir(vault_path)
    cleaned = 0

    for lock_file in lock_dir.glob("*.lock"):
        if _is_lock_stale(lock_file, max_age_seconds):
            try:
                lock_file.unlink()
                cleaned += 1
                logger.info(f"Cleaned stale lock: {lock_file.name}")
            except Exception as e:
                logger.warning(f"Failed to clean stale lock {lock_file.name}: {e}")

    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} stale locks")

    return cleaned


def get_lock_info(resource_id: str, vault_path: str = "AI_Employee_Vault") -> Optional[dict]:
    """
    Get information about a lock.

    Args:
        resource_id: Unique identifier for the resource
        vault_path: Path to AI Employee Vault

    Returns:
        Lock metadata dict or None if not locked
    """
    lock_file = _get_lock_file(resource_id, vault_path)

    if not lock_file.exists():
        return None

    metadata = _read_lock_metadata(lock_file)
    if metadata:
        # Add stale status
        metadata['is_stale'] = _is_lock_stale(lock_file)
        metadata['process_alive'] = _is_process_alive(metadata.get('pid', 0))

    return metadata


class FileLock:
    """
    Context manager for file-based locks.

    Usage:
        with FileLock('task-123', timeout=30):
            process_task()
    """

    def __init__(self, resource_id: str, timeout: int = 30,
                 vault_path: str = "AI_Employee_Vault"):
        """
        Initialize file lock.

        Args:
            resource_id: Unique identifier for the resource
            timeout: Maximum seconds to wait for lock
            vault_path: Path to AI Employee Vault
        """
        self.resource_id = resource_id
        self.timeout = timeout
        self.vault_path = vault_path
        self.acquired = False

    def __enter__(self):
        """Acquire lock on entry."""
        self.acquired = acquire_lock(self.resource_id, self.timeout, self.vault_path)
        if not self.acquired:
            raise LockTimeout(f"Could not acquire lock: {self.resource_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock on exit."""
        if self.acquired:
            release_lock(self.resource_id, self.vault_path)
        return False


@contextmanager
def try_lock(resource_id: str, timeout: int = 0,
             vault_path: str = "AI_Employee_Vault"):
    """
    Context manager that yields True if lock acquired, False otherwise.
    Does not raise exception on timeout.

    Usage:
        with try_lock('task-123', timeout=5) as locked:
            if locked:
                process_task()
            else:
                print("Could not acquire lock")
    """
    acquired = acquire_lock(resource_id, timeout, vault_path)
    try:
        yield acquired
    finally:
        if acquired:
            release_lock(resource_id, vault_path)


def get_all_locks(vault_path: str = "AI_Employee_Vault") -> list:
    """
    Get information about all current locks.

    Args:
        vault_path: Path to AI Employee Vault

    Returns:
        List of lock metadata dicts
    """
    lock_dir = _get_lock_dir(vault_path)
    locks = []

    for lock_file in lock_dir.glob("*.lock"):
        metadata = _read_lock_metadata(lock_file)
        if metadata:
            metadata['is_stale'] = _is_lock_stale(lock_file)
            metadata['process_alive'] = _is_process_alive(metadata.get('pid', 0))
            locks.append(metadata)

    return locks
