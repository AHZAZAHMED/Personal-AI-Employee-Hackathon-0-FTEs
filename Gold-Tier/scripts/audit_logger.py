"""
Centralized Audit Logger for AI Employee - Gold Tier

Provides structured audit logging with correlation IDs for compliance (SOX, GDPR).
Tracks complete action chains: Task → Approval → Execution → Result

Features:
- Correlation IDs to trace related events
- Approval chain tracking (who, when, what, why)
- JSONL format for easy parsing
- Daily log rotation
- Query capabilities by correlation_id
- Thread-safe operations

Usage:
    from audit_logger import get_audit_logger

    logger = get_audit_logger(vault_path)
    correlation_id = logger.generate_correlation_id()

    logger.log_task_created(correlation_id, task_type, task_data)
    logger.log_approval_requested(correlation_id, action_type, details)
    logger.log_approval_granted(correlation_id, approver, approval_time)
    logger.log_action_executed(correlation_id, action_type, result)
"""

import json
import uuid
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class AuditLogger:
    """Centralized audit logger with correlation ID tracking."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.audit_logs = self.vault / "Logs" / "audit"
        self.audit_logs.mkdir(parents=True, exist_ok=True)

        # Thread lock for safe concurrent writes
        self._lock = threading.Lock()

    def generate_correlation_id(self) -> str:
        """Generate a unique correlation ID for tracking related events."""
        return str(uuid.uuid4())

    def log(self, event_data: Dict[str, Any]):
        """
        Write a structured audit log entry.

        Args:
            event_data: Dictionary with audit event data
                Required fields: correlation_id, action, actor
                Optional fields: approver, approval_time, task_id, result, metadata
        """
        # Add timestamp if not present
        if 'timestamp' not in event_data:
            event_data['timestamp'] = datetime.now().isoformat()

        # Validate required fields
        required = ['correlation_id', 'action', 'actor']
        for field in required:
            if field not in event_data:
                raise ValueError(f"Missing required field: {field}")

        # Write to daily log file
        log_file = self.audit_logs / f"{datetime.now().strftime('%Y-%m-%d')}_audit.jsonl"

        with self._lock:
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(event_data, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"[AUDIT ERROR] Failed to write audit log: {e}")

    # ─── Task Lifecycle Events ────────────────────────────────────

    def log_task_created(self, correlation_id: str, task_type: str,
                         task_data: Dict[str, Any], source: str = "inbox"):
        """Log when a new task is created/received."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'task_created',
            'actor': 'orchestrator',
            'task_type': task_type,
            'task_id': task_data.get('task_id', ''),
            'source': source,
            'priority': task_data.get('priority', 'normal'),
            'metadata': {
                'from': task_data.get('from', ''),
                'subject': task_data.get('subject', ''),
                'filename': task_data.get('filename', '')
            }
        })

    def log_task_processing_started(self, correlation_id: str, task_id: str,
                                     task_type: str):
        """Log when task processing begins."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'task_processing_started',
            'actor': 'orchestrator',
            'task_id': task_id,
            'task_type': task_type
        })

    def log_task_completed(self, correlation_id: str, task_id: str,
                           result: str, metadata: Dict[str, Any] = None):
        """Log when task is completed."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'task_completed',
            'actor': 'orchestrator',
            'task_id': task_id,
            'result': result,
            'metadata': metadata or {}
        })

    # ─── Approval Workflow Events ─────────────────────────────────

    def log_approval_requested(self, correlation_id: str, action_type: str,
                                details: Dict[str, Any], approval_file: str):
        """Log when approval is requested."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'approval_requested',
            'actor': 'orchestrator',
            'action_type': action_type,
            'approval_file': approval_file,
            'risk_level': details.get('risk_level', 'medium'),
            'metadata': {
                'to': details.get('to', ''),
                'subject': details.get('subject', ''),
                'amount': details.get('amount', ''),
                'recipient': details.get('recipient', '')
            }
        })

    def log_approval_granted(self, correlation_id: str, approver: str,
                             approval_time: str, action_type: str,
                             approval_file: str, metadata: Dict[str, Any] = None):
        """Log when approval is granted by human."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'approval_granted',
            'actor': 'approval_handler',
            'approver': approver,
            'approval_time': approval_time,
            'action_type': action_type,
            'approval_file': approval_file,
            'metadata': metadata or {}
        })

    def log_approval_rejected(self, correlation_id: str, rejector: str,
                              rejection_time: str, action_type: str,
                              approval_file: str, reason: str = ""):
        """Log when approval is rejected by human."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'approval_rejected',
            'actor': 'approval_handler',
            'rejector': rejector,
            'rejection_time': rejection_time,
            'action_type': action_type,
            'approval_file': approval_file,
            'reason': reason
        })

    # ─── Action Execution Events ──────────────────────────────────

    def log_action_started(self, correlation_id: str, action_type: str,
                           actor: str, approver: str = "",
                           approval_time: str = "", metadata: Dict[str, Any] = None):
        """Log when an action execution starts."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'action_started',
            'actor': actor,
            'action_type': action_type,
            'approver': approver,
            'approval_time': approval_time,
            'metadata': metadata or {}
        })

    def log_action_completed(self, correlation_id: str, action_type: str,
                             actor: str, result: str, approver: str = "",
                             approval_time: str = "", metadata: Dict[str, Any] = None):
        """Log when an action execution completes successfully."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'action_completed',
            'actor': actor,
            'action_type': action_type,
            'result': result,
            'approver': approver,
            'approval_time': approval_time,
            'metadata': metadata or {}
        })

    def log_action_failed(self, correlation_id: str, action_type: str,
                          actor: str, error: str, approver: str = "",
                          approval_time: str = "", metadata: Dict[str, Any] = None):
        """Log when an action execution fails."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'action_failed',
            'actor': actor,
            'action_type': action_type,
            'error': error,
            'approver': approver,
            'approval_time': approval_time,
            'metadata': metadata or {}
        })

    # ─── Skill-Specific Events ────────────────────────────────────

    def log_email_sent(self, correlation_id: str, to: str, subject: str,
                       approver: str, approval_time: str, result: str):
        """Log email sending with approval chain."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'email_sent',
            'actor': 'email_sender_skill',
            'approver': approver,
            'approval_time': approval_time,
            'result': result,
            'metadata': {
                'to': to,
                'subject': subject
            }
        })

    def log_payment_processed(self, correlation_id: str, amount: str,
                              recipient: str, approver: str,
                              approval_time: str, result: str):
        """Log payment processing with approval chain."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'payment_processed',
            'actor': 'payment_skill',
            'approver': approver,
            'approval_time': approval_time,
            'result': result,
            'metadata': {
                'amount': amount,
                'recipient': recipient
            }
        })

    def log_social_post_published(self, correlation_id: str, platform: str,
                                   approver: str, approval_time: str, result: str):
        """Log social media post with approval chain."""
        self.log({
            'correlation_id': correlation_id,
            'action': 'social_post_published',
            'actor': f'{platform}_posting_skill',
            'approver': approver,
            'approval_time': approval_time,
            'result': result,
            'metadata': {
                'platform': platform
            }
        })

    # ─── Query Methods ────────────────────────────────────────────

    def query_by_correlation_id(self, correlation_id: str,
                                days: int = 30) -> List[Dict[str, Any]]:
        """
        Query all audit events for a specific correlation ID.

        Args:
            correlation_id: The correlation ID to search for
            days: Number of days to search back (default 30)

        Returns:
            List of audit events matching the correlation ID
        """
        events = []

        # Search through recent log files
        from datetime import timedelta
        today = datetime.now()

        for i in range(days):
            date = today - timedelta(days=i)
            log_file = self.audit_logs / f"{date.strftime('%Y-%m-%d')}_audit.jsonl"

            if not log_file.exists():
                continue

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            if event.get('correlation_id') == correlation_id:
                                events.append(event)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[AUDIT QUERY ERROR] Failed to read {log_file}: {e}")

        # Sort by timestamp
        events.sort(key=lambda x: x.get('timestamp', ''))
        return events

    def get_approval_chain(self, correlation_id: str) -> Dict[str, Any]:
        """
        Get the complete approval chain for a correlation ID.

        Returns:
            Dictionary with approval chain details:
            - requested_at: when approval was requested
            - approved_by: who approved
            - approved_at: when it was approved
            - executed_at: when action was executed
            - result: execution result
        """
        events = self.query_by_correlation_id(correlation_id)

        chain = {
            'correlation_id': correlation_id,
            'requested_at': None,
            'approved_by': None,
            'approved_at': None,
            'rejected_by': None,
            'rejected_at': None,
            'executed_at': None,
            'result': None,
            'action_type': None,
            'events': events
        }

        for event in events:
            action = event.get('action', '')

            if action == 'approval_requested':
                chain['requested_at'] = event.get('timestamp')
                chain['action_type'] = event.get('action_type')

            elif action == 'approval_granted':
                chain['approved_by'] = event.get('approver')
                chain['approved_at'] = event.get('approval_time')

            elif action == 'approval_rejected':
                chain['rejected_by'] = event.get('rejector')
                chain['rejected_at'] = event.get('rejection_time')

            elif action in ['action_completed', 'email_sent', 'payment_processed', 'social_post_published']:
                chain['executed_at'] = event.get('timestamp')
                chain['result'] = event.get('result', 'success')

        return chain

    def generate_compliance_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Generate a compliance report for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary with compliance statistics
        """
        from datetime import datetime as dt, timedelta

        start = dt.strptime(start_date, '%Y-%m-%d')
        end = dt.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days + 1

        stats = {
            'period': {'start': start_date, 'end': end_date},
            'total_approvals_requested': 0,
            'total_approvals_granted': 0,
            'total_approvals_rejected': 0,
            'total_actions_executed': 0,
            'total_actions_failed': 0,
            'actions_by_type': {},
            'approvers': set()
        }

        for i in range(days):
            date = start + timedelta(days=i)
            log_file = self.audit_logs / f"{date.strftime('%Y-%m-%d')}_audit.jsonl"

            if not log_file.exists():
                continue

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            action = event.get('action', '')

                            if action == 'approval_requested':
                                stats['total_approvals_requested'] += 1
                            elif action == 'approval_granted':
                                stats['total_approvals_granted'] += 1
                                if event.get('approver'):
                                    stats['approvers'].add(event['approver'])
                            elif action == 'approval_rejected':
                                stats['total_approvals_rejected'] += 1
                            elif action == 'action_completed':
                                stats['total_actions_executed'] += 1
                                action_type = event.get('action_type', 'unknown')
                                stats['actions_by_type'][action_type] = stats['actions_by_type'].get(action_type, 0) + 1
                            elif action == 'action_failed':
                                stats['total_actions_failed'] += 1
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

        stats['approvers'] = list(stats['approvers'])
        return stats


# ─── Singleton Instance ───────────────────────────────────────────

_audit_logger_instance = None
_audit_logger_lock = threading.Lock()


def get_audit_logger(vault_path: str = "AI_Employee_Vault") -> AuditLogger:
    """
    Get the singleton AuditLogger instance.

    Args:
        vault_path: Path to AI Employee Vault

    Returns:
        AuditLogger instance
    """
    global _audit_logger_instance

    with _audit_logger_lock:
        if _audit_logger_instance is None:
            _audit_logger_instance = AuditLogger(vault_path)
        return _audit_logger_instance
