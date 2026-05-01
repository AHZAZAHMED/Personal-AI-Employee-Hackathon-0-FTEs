"""
Test Audit Logging System

Tests the structured audit logging implementation including:
- Correlation ID generation and tracking
- Approval chain logging
- Action execution logging
- Query capabilities
- Compliance report generation
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from audit_logger import AuditLogger, get_audit_logger


def test_correlation_id_generation():
    """Test correlation ID generation."""
    print("\n[TEST] Correlation ID Generation")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)

        # Generate multiple correlation IDs
        ids = [logger.generate_correlation_id() for _ in range(5)]

        # Check all are unique
        assert len(ids) == len(set(ids)), "Correlation IDs should be unique"

        # Check format (UUID)
        for cid in ids:
            assert len(cid) == 36, f"Correlation ID should be 36 chars: {cid}"
            assert cid.count('-') == 4, f"Correlation ID should have 4 dashes: {cid}"

        print("  [OK] Correlation IDs are unique and properly formatted")


def test_basic_logging():
    """Test basic audit logging."""
    print("\n[TEST] Basic Audit Logging")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)
        correlation_id = logger.generate_correlation_id()

        # Log a simple event
        logger.log({
            'correlation_id': correlation_id,
            'action': 'test_action',
            'actor': 'test_actor',
            'result': 'success'
        })

        # Verify log file was created
        log_dir = Path(tmpdir) / "Logs" / "audit"
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f"{today}_audit.jsonl"

        assert log_file.exists(), "Audit log file should be created"

        # Read and verify content
        with open(log_file, 'r') as f:
            line = f.readline()
            event = json.loads(line)

            assert event['correlation_id'] == correlation_id
            assert event['action'] == 'test_action'
            assert event['actor'] == 'test_actor'
            assert event['result'] == 'success'
            assert 'timestamp' in event

        print("  [OK] Basic logging works correctly")


def test_task_lifecycle_logging():
    """Test task lifecycle logging."""
    print("\n[TEST] Task Lifecycle Logging")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)
        correlation_id = logger.generate_correlation_id()

        # Log task lifecycle
        logger.log_task_created(correlation_id, 'email', {'task_id': 'EMAIL_001', 'priority': 'high'})
        logger.log_task_processing_started(correlation_id, 'EMAIL_001', 'email')
        logger.log_task_completed(correlation_id, 'EMAIL_001', 'success')

        # Query events
        events = logger.query_by_correlation_id(correlation_id)

        assert len(events) == 3, f"Should have 3 events, got {len(events)}"
        assert events[0]['action'] == 'task_created'
        assert events[1]['action'] == 'task_processing_started'
        assert events[2]['action'] == 'task_completed'

        print("  [OK] Task lifecycle logging works correctly")


def test_approval_workflow_logging():
    """Test approval workflow logging."""
    print("\n[TEST] Approval Workflow Logging")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)
        correlation_id = logger.generate_correlation_id()

        # Log approval workflow
        logger.log_approval_requested(correlation_id, 'email_send',
                                     {'to': 'test@example.com', 'risk_level': 'medium'},
                                     'APPROVAL_email_001.md')

        approval_time = datetime.now().isoformat()
        logger.log_approval_granted(correlation_id, 'john@example.com',
                                   approval_time, 'email_send', 'APPROVAL_email_001.md')

        logger.log_action_completed(correlation_id, 'email_send', 'email_sender_skill',
                                   'success', 'john@example.com', approval_time)

        # Get approval chain
        chain = logger.get_approval_chain(correlation_id)

        assert chain['approved_by'] == 'john@example.com'
        assert chain['approved_at'] == approval_time
        assert chain['action_type'] == 'email_send'
        assert chain['result'] == 'success'

        print("  [OK] Approval workflow logging works correctly")


def test_query_by_correlation_id():
    """Test querying events by correlation ID."""
    print("\n[TEST] Query by Correlation ID")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)

        # Create multiple correlation IDs with events
        cid1 = logger.generate_correlation_id()
        cid2 = logger.generate_correlation_id()

        logger.log({'correlation_id': cid1, 'action': 'action1', 'actor': 'actor1'})
        logger.log({'correlation_id': cid1, 'action': 'action2', 'actor': 'actor1'})
        logger.log({'correlation_id': cid2, 'action': 'action3', 'actor': 'actor2'})

        # Query each correlation ID
        events1 = logger.query_by_correlation_id(cid1)
        events2 = logger.query_by_correlation_id(cid2)

        assert len(events1) == 2, f"Should have 2 events for cid1, got {len(events1)}"
        assert len(events2) == 1, f"Should have 1 event for cid2, got {len(events2)}"

        assert events1[0]['action'] == 'action1'
        assert events1[1]['action'] == 'action2'
        assert events2[0]['action'] == 'action3'

        print("  [OK] Query by correlation ID works correctly")


def test_compliance_report():
    """Test compliance report generation."""
    print("\n[TEST] Compliance Report Generation")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)

        # Create sample events
        today = datetime.now().strftime('%Y-%m-%d')

        for i in range(5):
            cid = logger.generate_correlation_id()
            logger.log_approval_requested(cid, 'email_send', {}, f'APPROVAL_{i}.md')
            logger.log_approval_granted(cid, 'approver1', datetime.now().isoformat(),
                                       'email_send', f'APPROVAL_{i}.md')
            logger.log_action_completed(cid, 'email_send', 'skill', 'success',
                                       'approver1', datetime.now().isoformat())

        # Generate report
        report = logger.generate_compliance_report(today, today)

        assert report['total_approvals_requested'] == 5
        assert report['total_approvals_granted'] == 5
        assert report['total_actions_executed'] == 5
        assert 'email_send' in report['actions_by_type']
        assert 'approver1' in report['approvers']

        print("  [OK] Compliance report generation works correctly")


def test_email_sent_logging():
    """Test email-specific logging."""
    print("\n[TEST] Email Sent Logging")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)
        correlation_id = logger.generate_correlation_id()

        approval_time = datetime.now().isoformat()
        logger.log_email_sent(correlation_id, 'client@example.com',
                             'Re: Inquiry', 'john@example.com',
                             approval_time, 'success')

        events = logger.query_by_correlation_id(correlation_id)

        assert len(events) == 1
        assert events[0]['action'] == 'email_sent'
        assert events[0]['approver'] == 'john@example.com'
        assert events[0]['metadata']['to'] == 'client@example.com'
        assert events[0]['metadata']['subject'] == 'Re: Inquiry'

        print("  [OK] Email sent logging works correctly")


def test_action_failure_logging():
    """Test action failure logging."""
    print("\n[TEST] Action Failure Logging")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)
        correlation_id = logger.generate_correlation_id()

        logger.log_action_started(correlation_id, 'email_send', 'email_skill')
        logger.log_action_failed(correlation_id, 'email_send', 'email_skill',
                                'Connection timeout')

        events = logger.query_by_correlation_id(correlation_id)

        assert len(events) == 2
        assert events[0]['action'] == 'action_started'
        assert events[1]['action'] == 'action_failed'
        assert events[1]['error'] == 'Connection timeout'

        print("  [OK] Action failure logging works correctly")


def test_singleton_instance():
    """Test singleton pattern for audit logger."""
    print("\n[TEST] Singleton Instance")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger1 = get_audit_logger(tmpdir)
        logger2 = get_audit_logger(tmpdir)

        assert logger1 is logger2, "Should return same instance"

        print("  [OK] Singleton pattern works correctly")


def test_thread_safety():
    """Test thread-safe logging."""
    print("\n[TEST] Thread Safety")

    import threading

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(tmpdir)

        def log_events(thread_id):
            for i in range(10):
                cid = logger.generate_correlation_id()
                logger.log({
                    'correlation_id': cid,
                    'action': f'thread_{thread_id}_action_{i}',
                    'actor': f'thread_{thread_id}'
                })

        # Create multiple threads
        threads = [threading.Thread(target=log_events, args=(i,)) for i in range(5)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify all events were logged
        log_dir = Path(tmpdir) / "Logs" / "audit"
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f"{today}_audit.jsonl"

        with open(log_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 50, f"Should have 50 events, got {len(lines)}"

        print("  [OK] Thread-safe logging works correctly")


def run_all_tests():
    """Run all audit logging tests."""
    print("="*80)
    print("AUDIT LOGGING SYSTEM TESTS")
    print("="*80)

    tests = [
        test_correlation_id_generation,
        test_basic_logging,
        test_task_lifecycle_logging,
        test_approval_workflow_logging,
        test_query_by_correlation_id,
        test_compliance_report,
        test_email_sent_logging,
        test_action_failure_logging,
        test_singleton_instance,
        test_thread_safety
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] ERROR: {e}")
            failed += 1

    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
