"""
Test Health Monitoring Enhancements

Tests the new health monitoring features:
- Automated alerting system
- Prometheus metrics exporter
- Deadlock watchdog

Verifies:
- Alert sending and throttling
- Metrics collection and export
- Heartbeat monitoring
- Stale lock detection
- Process activity tracking
"""

import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_alerter_initialization():
    """Test alerter initialization."""
    print("\n[TEST] Alerter Initialization")

    with tempfile.TemporaryDirectory() as tmpdir:
        from alerting import Alerter

        config = {
            'email_enabled': False,
            'slack_enabled': False,
            'throttle_minutes': 15
        }

        alerter = Alerter(vault_path=tmpdir, config=config)

        assert alerter.vault == Path(tmpdir)
        assert alerter.alerts_dir.exists()
        assert alerter.throttle_minutes == 15

        print("  [OK] Alerter initialized correctly")
        return True


def test_alert_throttling():
    """Test that alerts are throttled correctly."""
    print("\n[TEST] Alert Throttling")

    with tempfile.TemporaryDirectory() as tmpdir:
        from alerting import Alerter, AlertSeverity

        config = {
            'email_enabled': False,
            'slack_enabled': False,
            'throttle_minutes': 1  # 1 minute for testing
        }

        alerter = Alerter(vault_path=tmpdir, config=config)

        # Send first alert
        result1 = alerter.send_alert(
            title="Test Alert",
            message="First alert",
            severity=AlertSeverity.WARNING,
            service="test_service"
        )

        assert 'console' in result1
        assert result1['console'] is True

        # Send same alert immediately - should be throttled
        result2 = alerter.send_alert(
            title="Test Alert",
            message="Second alert",
            severity=AlertSeverity.WARNING,
            service="test_service"
        )

        assert result2.get('throttled') is True

        print("  [OK] Alert throttling works correctly")
        return True


def test_alert_console_output():
    """Test console alert output."""
    print("\n[TEST] Console Alert Output")

    with tempfile.TemporaryDirectory() as tmpdir:
        from alerting import Alerter, AlertSeverity

        config = {'email_enabled': False, 'slack_enabled': False}
        alerter = Alerter(vault_path=tmpdir, config=config)

        result = alerter.send_alert(
            title="Test Console Alert",
            message="This is a test message",
            severity=AlertSeverity.ERROR,
            service="test_service",
            metadata={'key1': 'value1', 'key2': 'value2'}
        )

        assert result['console'] is True

        # Check alert log file
        log_files = list(alerter.alerts_dir.glob('*_alerts.jsonl'))
        assert len(log_files) > 0

        print("  [OK] Console alert works correctly")
        return True


def test_metrics_collector_initialization():
    """Test metrics collector initialization."""
    print("\n[TEST] Metrics Collector Initialization")

    with tempfile.TemporaryDirectory() as tmpdir:
        from metrics_exporter import MetricsCollector

        collector = MetricsCollector(vault_path=tmpdir)

        assert collector.vault == Path(tmpdir)
        assert collector.metrics is not None

        print("  [OK] Metrics collector initialized correctly")
        return True


def test_metrics_recording():
    """Test recording various metrics."""
    print("\n[TEST] Metrics Recording")

    with tempfile.TemporaryDirectory() as tmpdir:
        from metrics_exporter import MetricsCollector

        collector = MetricsCollector(vault_path=tmpdir)

        # Record various metrics
        collector.record_task_completed('email_send', 1.5)
        collector.record_task_failed('email_send')
        collector.record_error('orchestrator', 'timeout')
        collector.record_approval_requested('email_send')
        collector.record_approval_granted('email_send')
        collector.update_queue_size('pending_approval', 5)

        # Export metrics
        output = collector.export_metrics()

        assert 'ai_employee_tasks_completed_total' in output
        assert 'ai_employee_tasks_failed_total' in output
        assert 'ai_employee_errors_total' in output
        assert 'ai_employee_approvals_requested_total' in output
        assert 'ai_employee_queue_size' in output

        print("  [OK] Metrics recording works correctly")
        return True


def test_metrics_export_format():
    """Test Prometheus export format."""
    print("\n[TEST] Metrics Export Format")

    with tempfile.TemporaryDirectory() as tmpdir:
        from metrics_exporter import MetricsCollector

        collector = MetricsCollector(vault_path=tmpdir)

        # Record some metrics
        collector.record_task_completed('test_task', 2.0)
        collector.update_queue_size('test_queue', 10)

        # Export
        output = collector.export_metrics()

        # Check format
        lines = output.strip().split('\n')

        # Should have HELP and TYPE comments
        assert any(line.startswith('# HELP') for line in lines)
        assert any(line.startswith('# TYPE') for line in lines)

        # Should have metric values
        assert any('ai_employee_tasks_completed_total' in line and not line.startswith('#') for line in lines)

        print("  [OK] Metrics export format is correct")
        return True


def test_watchdog_heartbeat_recording():
    """Test heartbeat recording."""
    print("\n[TEST] Watchdog Heartbeat Recording")

    with tempfile.TemporaryDirectory() as tmpdir:
        from deadlock_watchdog import DeadlockWatchdog

        watchdog = DeadlockWatchdog(vault_path=tmpdir)

        # Record heartbeat
        watchdog.record_heartbeat('test_service')

        # Check heartbeat file exists
        heartbeat_file = watchdog.heartbeat_dir / 'test_service.heartbeat'
        assert heartbeat_file.exists()

        # Check heartbeat is recent
        is_healthy, time_since = watchdog.check_heartbeat('test_service')
        assert is_healthy is True
        assert time_since.total_seconds() < 5

        print("  [OK] Heartbeat recording works correctly")
        return True


def test_watchdog_stale_heartbeat_detection():
    """Test detection of stale heartbeats."""
    print("\n[TEST] Watchdog Stale Heartbeat Detection")

    with tempfile.TemporaryDirectory() as tmpdir:
        from deadlock_watchdog import DeadlockWatchdog

        watchdog = DeadlockWatchdog(
            vault_path=tmpdir,
            heartbeat_timeout_seconds=2  # 2 seconds for testing
        )

        # Record heartbeat
        watchdog.record_heartbeat('test_service')

        # Wait for it to become stale
        time.sleep(3)

        # Check - should be stale
        is_healthy, time_since = watchdog.check_heartbeat('test_service')
        assert is_healthy is False
        assert time_since.total_seconds() >= 2

        print("  [OK] Stale heartbeat detection works correctly")
        return True


def test_watchdog_stale_lock_detection():
    """Test detection of stale locks."""
    print("\n[TEST] Watchdog Stale Lock Detection")

    with tempfile.TemporaryDirectory() as tmpdir:
        from deadlock_watchdog import DeadlockWatchdog

        watchdog = DeadlockWatchdog(
            vault_path=tmpdir,
            lock_timeout_seconds=2  # 2 seconds for testing
        )

        # Create a fake lock file
        lock_file = watchdog.locks_dir / 'test.lock'
        lock_content = f"""pid: 12345
acquired_by: test_process
acquired_at: {datetime.now().isoformat()}
"""
        lock_file.write_text(lock_content)

        # Immediately check - should not be stale yet
        stale_locks = watchdog.check_stale_locks()
        assert len(stale_locks) == 0

        # Wait for it to become stale
        time.sleep(3)

        # Check again - should be stale now
        stale_locks = watchdog.check_stale_locks()
        assert len(stale_locks) == 1
        assert stale_locks[0]['lock_file'] == 'test.lock'
        assert stale_locks[0]['age_seconds'] >= 2

        print("  [OK] Stale lock detection works correctly")
        return True


def test_watchdog_process_activity():
    """Test process activity checking."""
    print("\n[TEST] Watchdog Process Activity")

    with tempfile.TemporaryDirectory() as tmpdir:
        from deadlock_watchdog import DeadlockWatchdog
        import os

        watchdog = DeadlockWatchdog(vault_path=tmpdir)

        # Check current process
        current_pid = os.getpid()
        result = watchdog.check_process_activity('test', pid=current_pid)

        assert result['status'] in ['active', 'running', 'sleeping']
        assert result['pid'] == current_pid
        assert 'cpu_percent' in result
        assert 'memory_mb' in result

        print("  [OK] Process activity checking works correctly")
        return True


def test_integration_alerting_with_watchdog():
    """Test integration of alerting with watchdog."""
    print("\n[TEST] Integration: Alerting with Watchdog")

    with tempfile.TemporaryDirectory() as tmpdir:
        from alerting import Alerter, AlertSeverity
        from deadlock_watchdog import DeadlockWatchdog

        # Create alerter
        config = {'email_enabled': False, 'slack_enabled': False}
        alerter = Alerter(vault_path=tmpdir, config=config)

        # Create watchdog with alerter
        watchdog = DeadlockWatchdog(
            vault_path=tmpdir,
            heartbeat_timeout_seconds=1,
            alerter=alerter
        )

        # Record heartbeat for a real service
        watchdog.record_heartbeat('orchestrator')

        # Wait for it to become stale
        time.sleep(2)

        # Check heartbeats - should trigger alert
        results = watchdog.check_all_heartbeats()

        assert results['orchestrator']['healthy'] is False

        # Check that alert was logged
        alert_logs = list(alerter.alerts_dir.glob('*_alerts.jsonl'))
        assert len(alert_logs) > 0

        print("  [OK] Alerting integration with watchdog works")
        return True


def test_metrics_system_collection():
    """Test system metrics collection."""
    print("\n[TEST] Metrics System Collection")

    with tempfile.TemporaryDirectory() as tmpdir:
        from metrics_exporter import MetricsCollector

        collector = MetricsCollector(vault_path=tmpdir)

        # Collect system metrics
        collector.collect_system_metrics()

        # Export and check
        output = collector.export_metrics()

        assert 'ai_employee_cpu_usage_percent' in output
        assert 'ai_employee_memory_usage_percent' in output
        assert 'ai_employee_disk_usage_percent' in output

        print("  [OK] System metrics collection works correctly")
        return True


def run_all_tests():
    """Run all health monitoring enhancement tests."""
    print("="*80)
    print("HEALTH MONITORING ENHANCEMENT TESTS - PHASE 4")
    print("="*80)

    tests = [
        test_alerter_initialization,
        test_alert_throttling,
        test_alert_console_output,
        test_metrics_collector_initialization,
        test_metrics_recording,
        test_metrics_export_format,
        test_watchdog_heartbeat_recording,
        test_watchdog_stale_heartbeat_detection,
        test_watchdog_stale_lock_detection,
        test_watchdog_process_activity,
        test_integration_alerting_with_watchdog,
        test_metrics_system_collection
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
        print("\n[OK] AUDIT-1 RISK #5 IS FIXED")
        print("[OK] Health monitoring enhancements complete")
        print("[OK] Alerting, metrics, and watchdog working")
    else:
        print("\n[ERROR] SOME TESTS FAILED")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
