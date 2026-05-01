"""
Test Logging Configuration with Rotation

Tests the centralized logging system with rotating file handlers:
- Log file creation
- Rotation when size limit reached
- Backup file creation
- Log statistics
- Old log cleanup
- Component-specific configurations
"""

import sys
import time
import logging
import tempfile
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from logging_config import (
    get_logger,
    get_component_logger,
    get_log_stats,
    cleanup_old_logs,
    get_recommended_logger
)


def cleanup_logger(logger):
    """Close and remove all handlers from a logger."""
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)


def test_basic_logging():
    """Test basic logger creation and logging."""
    print("\n[TEST] Basic Logging")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger('test_basic', vault_path=tmpdir, console_output=False)

        # Write some logs
        logger.info('Test info message')
        logger.warning('Test warning message')
        logger.error('Test error message')

        # Check log file exists
        log_file = Path(tmpdir) / 'Logs' / 'test_basic.log'
        assert log_file.exists()

        # Check content
        content = log_file.read_text()
        assert 'Test info message' in content
        assert 'Test warning message' in content
        assert 'Test error message' in content

        # Cleanup
        cleanup_logger(logger)

        print("  [OK] Basic logging works")
        return True


def test_log_rotation():
    """Test log rotation when size limit is reached."""
    print("\n[TEST] Log Rotation")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create logger with small max size (1 KB)
        logger = get_logger(
            'test_rotation',
            vault_path=tmpdir,
            max_bytes=1024,  # 1 KB
            backup_count=3,
            console_output=False
        )

        # Write enough logs to trigger rotation
        for i in range(100):
            logger.info(f'Log message {i} - ' + 'x' * 100)

        logs_dir = Path(tmpdir) / 'Logs'

        # Check that rotation occurred
        log_files = list(logs_dir.glob('test_rotation.log*'))
        assert len(log_files) > 1, f"Expected rotation, found {len(log_files)} files"

        # Check backup files exist
        assert (logs_dir / 'test_rotation.log').exists()
        backup_files = list(logs_dir.glob('test_rotation.log.*'))
        assert len(backup_files) > 0, "No backup files created"

        # Cleanup
        cleanup_logger(logger)

        print(f"  [OK] Log rotation works ({len(log_files)} files created)")
        return True


def test_backup_count_limit():
    """Test that backup count is respected."""
    print("\n[TEST] Backup Count Limit")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create logger with small max size and backup count
        logger = get_logger(
            'test_backup',
            vault_path=tmpdir,
            max_bytes=500,  # 500 bytes
            backup_count=2,  # Keep only 2 backups
            console_output=False
        )

        # Write lots of logs to trigger multiple rotations
        for i in range(200):
            logger.info(f'Log message {i} - ' + 'x' * 100)

        logs_dir = Path(tmpdir) / 'Logs'
        log_files = list(logs_dir.glob('test_backup.log*'))

        # Should have main log + 2 backups = 3 files max
        assert len(log_files) <= 3, f"Expected max 3 files, found {len(log_files)}"

        # Cleanup
        cleanup_logger(logger)

        print(f"  [OK] Backup count limit respected ({len(log_files)} files)")
        return True


def test_multiple_loggers():
    """Test multiple independent loggers."""
    print("\n[TEST] Multiple Loggers")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger1 = get_logger('component1', vault_path=tmpdir, console_output=False)
        logger2 = get_logger('component2', vault_path=tmpdir, console_output=False)

        logger1.info('Message from component 1')
        logger2.info('Message from component 2')

        logs_dir = Path(tmpdir) / 'Logs'

        # Check both log files exist
        log1 = logs_dir / 'component1.log'
        log2 = logs_dir / 'component2.log'

        assert log1.exists()
        assert log2.exists()

        # Check content is separate
        content1 = log1.read_text()
        content2 = log2.read_text()

        assert 'component 1' in content1
        assert 'component 1' not in content2
        assert 'component 2' in content2
        assert 'component 2' not in content1

        # Cleanup
        cleanup_logger(logger1)
        cleanup_logger(logger2)

        print("  [OK] Multiple loggers work independently")
        return True


def test_component_logger():
    """Test component-specific logger."""
    print("\n[TEST] Component Logger")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_component_logger('orchestrator', vault_path=tmpdir, console_output=False)

        logger.info('Orchestrator started')
        logger.info('Processing task')

        log_file = Path(tmpdir) / 'Logs' / 'orchestrator.log'
        assert log_file.exists()

        content = log_file.read_text()
        assert 'Orchestrator started' in content
        assert 'Processing task' in content

        # Cleanup
        cleanup_logger(logger)

        print("  [OK] Component logger works")
        return True


def test_log_stats():
    """Test log statistics function."""
    print("\n[TEST] Log Statistics")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some logs
        logger1 = get_logger('stats1', vault_path=tmpdir, console_output=False)
        logger2 = get_logger('stats2', vault_path=tmpdir, console_output=False)

        for i in range(10):
            logger1.info(f'Message {i}')
            logger2.info(f'Message {i}')

        # Get stats
        stats = get_log_stats(vault_path=tmpdir)

        assert stats['file_count'] == 2
        assert stats['total_size'] > 0
        assert len(stats['files']) == 2

        # Cleanup
        cleanup_logger(logger1)
        cleanup_logger(logger2)

        print(f"  [OK] Log stats: {stats['file_count']} files, {stats['total_size']} bytes")
        return True


def test_cleanup_old_logs():
    """Test cleanup of old log files."""
    print("\n[TEST] Cleanup Old Logs")

    with tempfile.TemporaryDirectory() as tmpdir:
        logs_dir = Path(tmpdir) / 'Logs'
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Create some log files
        old_log = logs_dir / 'old.log'
        new_log = logs_dir / 'new.log'

        old_log.write_text('old log')
        new_log.write_text('new log')

        # Make old log appear old (modify mtime)
        import os
        old_time = time.time() - (40 * 86400)  # 40 days ago
        os.utime(old_log, (old_time, old_time))

        # Cleanup logs older than 30 days
        deleted = cleanup_old_logs(vault_path=tmpdir, days_to_keep=30)

        assert deleted == 1
        assert not old_log.exists()
        assert new_log.exists()

        print(f"  [OK] Cleaned up {deleted} old log file(s)")
        return True


def test_recommended_logger():
    """Test recommended logger configurations."""
    print("\n[TEST] Recommended Logger")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Get recommended logger for orchestrator
        logger = get_recommended_logger('orchestrator', vault_path=tmpdir)

        logger.info('Using recommended configuration')

        log_file = Path(tmpdir) / 'Logs' / 'orchestrator.log'
        assert log_file.exists()

        # Cleanup
        cleanup_logger(logger)

        print("  [OK] Recommended logger works")
        return True


def test_logger_singleton():
    """Test that same logger name returns same instance."""
    print("\n[TEST] Logger Singleton")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger1 = get_logger('singleton', vault_path=tmpdir, console_output=False)
        logger2 = get_logger('singleton', vault_path=tmpdir, console_output=False)

        # Should be same instance
        assert logger1 is logger2

        # Should not add duplicate handlers
        assert len(logger1.handlers) == 1  # Only file handler (console_output=False)

        # Cleanup
        cleanup_logger(logger1)

        print("  [OK] Logger singleton works")
        return True


def test_log_levels():
    """Test different log levels."""
    print("\n[TEST] Log Levels")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger(
            'levels',
            vault_path=tmpdir,
            log_level=logging.WARNING,
            console_output=False
        )

        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')

        log_file = Path(tmpdir) / 'Logs' / 'levels.log'
        content = log_file.read_text()

        # Only WARNING and above should be logged
        assert 'Debug message' not in content
        assert 'Info message' not in content
        assert 'Warning message' in content
        assert 'Error message' in content

        # Cleanup
        cleanup_logger(logger)

        print("  [OK] Log levels work correctly")
        return True


def run_all_tests():
    """Run all logging configuration tests."""
    print("="*80)
    print("LOGGING CONFIGURATION TESTS")
    print("="*80)

    tests = [
        test_basic_logging,
        test_log_rotation,
        test_backup_count_limit,
        test_multiple_loggers,
        test_component_logger,
        test_log_stats,
        test_cleanup_old_logs,
        test_recommended_logger,
        test_logger_singleton,
        test_log_levels
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

    if failed == 0:
        print("\n[OK] AUDIT-1 RISK #3 IS FIXED")
        print("[OK] Log rotation prevents unbounded growth")
        print("[OK] Configurable retention policies")
    else:
        print("\n[ERROR] SOME TESTS FAILED")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
