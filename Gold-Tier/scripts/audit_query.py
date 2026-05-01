"""
Audit Query Tool - Query and analyze audit logs

Provides CLI interface to query audit logs by correlation ID,
generate compliance reports, and answer audit questions like:
- "Who approved this email?"
- "When was this action executed?"
- "What was the approval chain for this task?"

Usage:
    python scripts/audit_query.py --vault AI_Employee_Vault --correlation-id <id>
    python scripts/audit_query.py --vault AI_Employee_Vault --report --start 2026-04-01 --end 2026-04-23
    python scripts/audit_query.py --vault AI_Employee_Vault --approval-chain <correlation-id>
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Import audit logger
sys.path.insert(0, str(Path(__file__).parent))
from audit_logger import get_audit_logger


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return iso_timestamp


def print_event(event: Dict[str, Any], indent: int = 0):
    """Pretty print an audit event."""
    prefix = "  " * indent
    print(f"{prefix}[{format_timestamp(event.get('timestamp', ''))}] {event.get('action', 'unknown')}")
    print(f"{prefix}  Actor: {event.get('actor', 'unknown')}")

    if event.get('approver'):
        print(f"{prefix}  Approver: {event.get('approver')}")
    if event.get('approval_time'):
        print(f"{prefix}  Approved At: {format_timestamp(event.get('approval_time'))}")
    if event.get('result'):
        print(f"{prefix}  Result: {event.get('result')}")
    if event.get('error'):
        print(f"{prefix}  Error: {event.get('error')}")

    metadata = event.get('metadata', {})
    if metadata:
        print(f"{prefix}  Metadata:")
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"{prefix}    {key}: {value}")


def query_by_correlation_id(vault_path: str, correlation_id: str):
    """Query all events for a correlation ID."""
    logger = get_audit_logger(vault_path)

    print(f"\n{'='*80}")
    print(f"AUDIT TRAIL FOR CORRELATION ID: {correlation_id}")
    print(f"{'='*80}\n")

    events = logger.query_by_correlation_id(correlation_id, days=90)

    if not events:
        print("No events found for this correlation ID.")
        return

    print(f"Found {len(events)} event(s):\n")

    for i, event in enumerate(events, 1):
        print(f"\n{i}. ", end="")
        print_event(event)

    print(f"\n{'='*80}\n")


def show_approval_chain(vault_path: str, correlation_id: str):
    """Show the complete approval chain for a correlation ID."""
    logger = get_audit_logger(vault_path)

    print(f"\n{'='*80}")
    print(f"APPROVAL CHAIN FOR: {correlation_id}")
    print(f"{'='*80}\n")

    chain = logger.get_approval_chain(correlation_id)

    if not chain.get('requested_at'):
        print("No approval chain found for this correlation ID.")
        return

    print(f"Action Type: {chain.get('action_type', 'unknown')}")
    print(f"\nTimeline:")
    print(f"  1. Approval Requested: {format_timestamp(chain.get('requested_at', ''))}")

    if chain.get('approved_by'):
        print(f"  2. Approved By: {chain.get('approved_by')}")
        print(f"     Approved At: {format_timestamp(chain.get('approved_at', ''))}")
    elif chain.get('rejected_by'):
        print(f"  2. Rejected By: {chain.get('rejected_by')}")
        print(f"     Rejected At: {format_timestamp(chain.get('rejected_at', ''))}")

    if chain.get('executed_at'):
        print(f"  3. Executed At: {format_timestamp(chain.get('executed_at', ''))}")
        print(f"     Result: {chain.get('result', 'unknown')}")

    print(f"\nComplete Event Log ({len(chain.get('events', []))} events):")
    for event in chain.get('events', []):
        print_event(event, indent=1)

    print(f"\n{'='*80}\n")


def generate_compliance_report(vault_path: str, start_date: str, end_date: str):
    """Generate a compliance report for a date range."""
    logger = get_audit_logger(vault_path)

    print(f"\n{'='*80}")
    print(f"COMPLIANCE REPORT")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*80}\n")

    report = logger.generate_compliance_report(start_date, end_date)

    print(f"Summary:")
    print(f"  Total Approvals Requested: {report['total_approvals_requested']}")
    print(f"  Total Approvals Granted: {report['total_approvals_granted']}")
    print(f"  Total Approvals Rejected: {report['total_approvals_rejected']}")
    print(f"  Total Actions Executed: {report['total_actions_executed']}")
    print(f"  Total Actions Failed: {report['total_actions_failed']}")

    print(f"\nActions by Type:")
    for action_type, count in sorted(report['actions_by_type'].items()):
        print(f"  {action_type}: {count}")

    print(f"\nApprovers:")
    for approver in report['approvers']:
        print(f"  - {approver}")

    print(f"\n{'='*80}\n")


def search_recent_actions(vault_path: str, action_type: str = None, days: int = 7):
    """Search for recent actions of a specific type."""
    logger = get_audit_logger(vault_path)

    print(f"\n{'='*80}")
    print(f"RECENT ACTIONS (Last {days} days)")
    if action_type:
        print(f"Filter: {action_type}")
    print(f"{'='*80}\n")

    # Read recent audit logs
    from datetime import timedelta
    today = datetime.now()

    all_events = []
    for i in range(days):
        date = today - timedelta(days=i)
        log_file = Path(vault_path) / "Logs" / "audit" / f"{date.strftime('%Y-%m-%d')}_audit.jsonl"

        if not log_file.exists():
            continue

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if action_type is None or event.get('action') == action_type:
                            all_events.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue

    if not all_events:
        print("No events found.")
        return

    # Sort by timestamp (newest first)
    all_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    print(f"Found {len(all_events)} event(s):\n")

    for i, event in enumerate(all_events[:50], 1):  # Limit to 50 most recent
        print(f"{i}. ", end="")
        print_event(event)
        print()

    if len(all_events) > 50:
        print(f"... and {len(all_events) - 50} more events (showing first 50)")

    print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Query and analyze AI Employee audit logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query by correlation ID
  python audit_query.py --vault AI_Employee_Vault --correlation-id abc-123-def

  # Show approval chain
  python audit_query.py --vault AI_Employee_Vault --approval-chain abc-123-def

  # Generate compliance report
  python audit_query.py --vault AI_Employee_Vault --report --start 2026-04-01 --end 2026-04-23

  # Search recent actions
  python audit_query.py --vault AI_Employee_Vault --recent --action email_sent --days 7
        """
    )

    parser.add_argument('--vault', required=True, help='Path to AI Employee Vault')
    parser.add_argument('--correlation-id', help='Query events by correlation ID')
    parser.add_argument('--approval-chain', help='Show approval chain for correlation ID')
    parser.add_argument('--report', action='store_true', help='Generate compliance report')
    parser.add_argument('--start', help='Start date for report (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date for report (YYYY-MM-DD)')
    parser.add_argument('--recent', action='store_true', help='Show recent actions')
    parser.add_argument('--action', help='Filter by action type')
    parser.add_argument('--days', type=int, default=7, help='Number of days to search (default: 7)')

    args = parser.parse_args()

    # Validate vault path
    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {args.vault}")
        sys.exit(1)

    # Execute requested operation
    if args.correlation_id:
        query_by_correlation_id(args.vault, args.correlation_id)

    elif args.approval_chain:
        show_approval_chain(args.vault, args.approval_chain)

    elif args.report:
        if not args.start or not args.end:
            print("Error: --report requires --start and --end dates")
            sys.exit(1)
        generate_compliance_report(args.vault, args.start, args.end)

    elif args.recent:
        search_recent_actions(args.vault, args.action, args.days)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
