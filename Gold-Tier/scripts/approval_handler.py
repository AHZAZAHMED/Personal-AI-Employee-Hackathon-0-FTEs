"""
Approval Handler for AI Employee - Silver Tier

Manages human-in-the-loop approval workflow:
- Creates approval requests for sensitive actions
- Processes approved actions (executes them)
- Archives rejected actions
- Maintains audit trail with correlation IDs

Usage:
    python scripts/approval_handler.py --vault AI_Employee_Vault
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import audit logger
sys.path.insert(0, str(Path(__file__).parent))
from audit_logger import get_audit_logger
from file_locking import try_lock
from approval_tokens import get_token_manager


class ApprovalHandler:
    """Manages approval workflow for AI Employee."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)

        # Initialize audit logger
        self.audit_logger = get_audit_logger(str(vault_path))
        
        # Folders
        self.pending_approval = self.vault / 'Pending_Approval'
        self.approved = self.vault / 'Approved'
        self.rejected = self.vault / 'Rejected'
        self.done = self.vault / 'Done'
        self.logs = self.vault / 'Logs'
        
        # Ensure folders exist
        for folder in [self.pending_approval, self.approved, self.rejected, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed approvals
        self.processed_file = self.logs / 'processed_approvals.json'
        self.processed_approvals = self._load_processed()
        
        # Approval rules (from Company Handbook)
        self.approval_rules = {
            'email_reply': 'Email replies to contacts require approval',
            'email_send': 'Sending emails requires approval',
            'payment': 'All payments require human approval',
            'social_post': 'Social media posts require approval',
            'invoice': 'Invoice-related actions require approval',
        }
    
    def _load_processed(self) -> set:
        """Load previously processed approval files."""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('files', []))
            except:
                pass
        return set()
    
    def _save_processed(self):
        """Save processed approvals to disk."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'files': list(self.processed_approvals)
            }
            with open(self.processed_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving processed: {e}")
    
    def create_approval_request(self, action_type: str, details: Dict[str, Any],
                                 description: str = "", correlation_id: str = "") -> Path:
        """
        Create a new approval request file.

        Args:
            action_type: Type of action (email_reply, payment, etc.)
            details: Dictionary with action details
            description: Human-readable description
            correlation_id: Correlation ID for audit trail (generated if not provided)

        Returns:
            Path to created approval request file
        """
        # Generate correlation_id if not provided
        if not correlation_id:
            correlation_id = self.audit_logger.generate_correlation_id()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"APPROVAL_{action_type}_{timestamp}.md"
        filepath = self.pending_approval / filename

        # Build frontmatter with ALL details as top-level fields
        frontmatter_lines = [
            "---",
            f"type: approval_request",
            f"action: {action_type}",
            f"created: {datetime.now().isoformat()}",
            f"status: pending",
            f"expires: {(datetime.now().replace(hour=23, minute=59)).isoformat()}",
            f"risk_level: {details.get('risk_level', 'medium')}",
            f"correlation_id: {correlation_id}",
        ]
        
        # Add all detail fields to frontmatter
        for key, value in details.items():
            if key != 'risk_level':  # Already added above
                # Clean the value for YAML
                if isinstance(value, str):
                    # Special handling for draft_body - preserve line breaks using YAML multiline format
                    if key == 'draft_body' and '\n' in value:
                        # Use YAML literal block scalar (|) for multiline text
                        frontmatter_lines.append(f"{key}: |")
                        # Indent each line for YAML multiline
                        for line in value.split('\n'):
                            frontmatter_lines.append(f"  {line}")
                    else:
                        # Single-line values - replace newlines and quotes
                        value = value.replace('\n', ' ').replace('"', "'")
                        frontmatter_lines.append(f"{key}: {value}")
                else:
                    frontmatter_lines.append(f"{key}: {value}")
        
        frontmatter_lines.append("---")
        
        # Build details section for human reading
        details_text = ""
        for key, value in details.items():
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            details_text += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        
        content = "\n".join(frontmatter_lines)
        content += f"""

# Approval Required

## Action Details
- **Action Type:** {action_type.replace('_', ' ').title()}
- **Description:** {description}
- **Risk Level:** {details.get('risk_level', 'medium').upper()}

{details_text}
## Why Approval is Required
{self.approval_rules.get(action_type, 'This action requires human review per Company Handbook.')}

## To Approve
**Move this file to `/Approved` folder.**

## To Reject
**Move this file to `/Rejected` folder with a note explaining why.**

## Deadline
Please respond within 24 hours.

---
*Created by AI Employee Approval Handler v0.1.0*
"""
        
        filepath.write_text(content, encoding='utf-8')

        # Log to old system (backward compatibility)
        self._log_event('approval_requested', {
            'file': filename,
            'action_type': action_type,
            'details': details
        })

        # Log to audit system with correlation ID
        self.audit_logger.log_approval_requested(
            correlation_id=correlation_id,
            action_type=action_type,
            details=details,
            approval_file=filename
        )

        print(f"  Created approval request: {filename}")
        print(f"  Correlation ID: {correlation_id}")
        return filepath
    
    def get_pending_approvals(self) -> List[Path]:
        """Get all pending approval requests."""
        if not self.pending_approval.exists():
            return []
        return list(self.pending_approval.glob('*.md'))
    
    def get_approved_actions(self) -> List[Path]:
        """Get approved actions ready to execute (respects multi-approver threshold)."""
        if not self.approved.exists():
            return []

        ready_actions = []
        for f in self.approved.glob('*.md'):
            if f.name in self.processed_approvals:
                continue

            # Check if multi-approver threshold is met
            try:
                content = f.read_text(encoding='utf-8')
                metadata = self._parse_frontmatter(content)

                required_approvals = int(metadata.get('required_approvals', 1))

                # If multi-approver is configured, check threshold
                if required_approvals > 1:
                    approvers_str = metadata.get('approvers', '')
                    approvers = [a.strip() for a in approvers_str.split(',') if a.strip()] if approvers_str else []

                    if len(approvers) < required_approvals:
                        # Not enough approvals yet
                        continue

                ready_actions.append(f)
            except Exception as e:
                print(f"Warning: Error checking approval threshold for {f.name}: {e}")
                # Include it anyway to avoid blocking
                ready_actions.append(f)

        return ready_actions
    
    def get_rejected_actions(self) -> List[Path]:
        """Get rejected actions to archive."""
        if not self.rejected.exists():
            return []
        return [f for f in self.rejected.glob('*.md')
                if f.name not in self.processed_approvals]
    
    def process_approved_actions(self, executor_callback=None) -> Dict[str, int]:
        """
        Process all approved actions.
        
        Args:
            executor_callback: Function to execute the action
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'processed': 0,
            'executed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        approved_files = self.get_approved_actions()
        
        if not approved_files:
            return stats
        
        print(f"\nProcessing {len(approved_files)} approved action(s)...")
        
        # If no executor provided, try to use email sender (Gmail API)
        if executor_callback is None:
            try:
                from email_sender_mcp import execute_approved_email
                executor_callback = execute_approved_email
                print("  Using Gmail API Sender for email actions")
            except Exception as e:
                print(f"  Gmail API Sender not available: {e}")
                print("  Will mark as executed only")
        
        for filepath in approved_files:
            # Use file locking to prevent concurrent processing
            lock_id = f"approval_{filepath.name}"

            with try_lock(lock_id, timeout=0, vault_path=str(self.vault)) as locked:
                if not locked:
                    print(f"  Approval {filepath.name} is locked by another process, skipping")
                    stats['skipped'] += 1
                    continue

                try:
                    result = self._execute_approved_action(filepath, executor_callback)
                    stats['processed'] += 1

                    if result['success']:
                        stats['executed'] += 1
                        self.processed_approvals.add(filepath.name)
                        self._save_processed()
                    else:
                        stats['errors'] += 1

                except Exception as e:
                    print(f"  Error processing {filepath.name}: {e}")
                    stats['errors'] += 1
        
        return stats
    
    def _execute_approved_action(self, filepath: Path, executor_callback=None) -> Dict[str, Any]:
        """
        Execute a single approved action.

        Args:
            filepath: Path to approved action file
            executor_callback: Optional callback to execute action

        Returns:
            Result dictionary
        """
        content = filepath.read_text(encoding='utf-8')
        metadata = self._parse_frontmatter(content)

        action_type = metadata.get('action', 'unknown')
        correlation_id = metadata.get('correlation_id', '')

        print(f"\n  Executing: {filepath.name}")
        print(f"    Type: {action_type}")
        if correlation_id:
            print(f"    Correlation ID: {correlation_id}")

        # Check if approval has expired
        expires_str = metadata.get('expires', '')
        if expires_str:
            try:
                expires_time = datetime.fromisoformat(expires_str)
                if datetime.now() > expires_time:
                    print(f"    [EXPIRED] Approval expired at {expires_time.strftime('%Y-%m-%d %H:%M:%S')}")

                    # Log expiration event
                    if correlation_id:
                        self.audit_logger.log_action_completed(
                            correlation_id=correlation_id,
                            action_type=action_type,
                            actor='approval_handler',
                            result='expired',
                            metadata={'expires': expires_str, 'reason': 'Approval deadline passed'}
                        )

                    # Move to rejected folder with expiration note
                    expired_content = content + f"""

---
## [WARNING] APPROVAL EXPIRED

This approval expired at {expires_time.strftime('%Y-%m-%d %H:%M:%S')} and was not executed.

**Expired:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Reason:** Approval deadline passed before execution

If this action is still needed, please create a new approval request.

---
*AI Employee Approval Handler - Expiration Enforcement*
"""
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    expired_name = filepath.stem + '_expired_' + timestamp + filepath.suffix
                    expired_path = self.rejected / expired_name
                    expired_path.write_text(expired_content, encoding='utf-8')
                    filepath.unlink()

                    self._log_event('approval_expired', {
                        'file': filepath.name,
                        'action_type': action_type,
                        'expires': expires_str,
                        'destination': expired_name
                    })

                    return {'success': False, 'action_type': action_type, 'error': 'expired',
                            'message': f'Approval expired at {expires_time.strftime("%Y-%m-%d %H:%M:%S")}'}
            except ValueError:
                print(f"    [WARNING] Warning: Invalid expiration date format: {expires_str}")

        # Check if approval has been revoked
        status = metadata.get('status', 'pending')
        if status == 'revoked':
            print(f"    [ERROR] REVOKED: This approval has been revoked")

            # Log revocation
            if correlation_id:
                self.audit_logger.log_action_completed(
                    correlation_id=correlation_id,
                    action_type=action_type,
                    actor='approval_handler',
                    result='revoked',
                    metadata={'revoked_by': metadata.get('revoked_by', 'unknown'),
                             'revoked_at': metadata.get('revoked_at', 'unknown'),
                             'revocation_reason': metadata.get('revocation_reason', 'No reason provided')}
                )

            # Move to rejected folder
            revoked_content = content + f"""

---
## [WARNING] APPROVAL REVOKED

This approval was revoked and will not be executed.

**Revoked By:** {metadata.get('revoked_by', 'Unknown')}
**Revoked At:** {metadata.get('revoked_at', 'Unknown')}
**Reason:** {metadata.get('revocation_reason', 'No reason provided')}

---
*AI Employee Approval Handler - Revocation Enforcement*
"""
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            revoked_name = filepath.stem + '_revoked_' + timestamp + filepath.suffix
            revoked_path = self.rejected / revoked_name
            revoked_path.write_text(revoked_content, encoding='utf-8')
            filepath.unlink()

            self._log_event('approval_revoked', {
                'file': filepath.name,
                'action_type': action_type,
                'revoked_by': metadata.get('revoked_by', 'unknown'),
                'destination': revoked_name
            })

            return {'success': False, 'action_type': action_type, 'error': 'revoked',
                    'message': 'Approval has been revoked'}

        # Detect approval time (when file was moved to /Approved)
        approval_time = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
        approver = "human"  # Default - could be enhanced to track actual user

        # Log approval granted
        if correlation_id:
            self.audit_logger.log_approval_granted(
                correlation_id=correlation_id,
                approver=approver,
                approval_time=approval_time,
                action_type=action_type,
                approval_file=filepath.name,
                metadata=metadata
            )

        # Generate approval token for secure execution
        token_manager = get_token_manager(str(self.vault))
        approval_token = token_manager.generate_token(
            action_type=action_type,
            metadata=metadata,
            expires_hours=24,
            single_use=True
        )
        print(f"    Generated approval token: {approval_token[:16]}...")

        # Execute based on action type
        result = {'success': False, 'action_type': action_type}

        if executor_callback:
            # Pass approval token along with other metadata
            result = executor_callback(action_type, metadata, content,
                                      correlation_id=correlation_id,
                                      approver=approver,
                                      approval_time=approval_time,
                                      approval_token=approval_token)
        else:
            # Default: just mark as executed
            print(f"    No executor configured - marking as executed")
            result['success'] = True
        
        if result['success']:
            # Log action completed to audit system
            if correlation_id:
                self.audit_logger.log_action_completed(
                    correlation_id=correlation_id,
                    action_type=action_type,
                    actor='approval_handler',
                    result='success',
                    approver=approver,
                    approval_time=approval_time,
                    metadata=result.get('metadata', {})
                )

            # Add execution metadata
            execution_block = f"""
---
executed: {datetime.now().isoformat()}
execution_status: success
executed_by: ApprovalHandler (Silver Tier)
action_type: {action_type}
correlation_id: {correlation_id}
approver: {approver}
approval_time: {approval_time}
---

## Execution Result

**Executed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** [OK] Success
**Action:** {action_type.replace('_', ' ').title()}
**Approved By:** {approver}
**Approved At:** {datetime.fromisoformat(approval_time).strftime('%Y-%m-%d %H:%M:%S')}
**Correlation ID:** {correlation_id}

---
*AI Employee Approval Handler v0.1.0*
"""
            content += execution_block

            # Move to Done
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_name = filepath.stem + '_executed_' + timestamp + filepath.suffix
            dest_path = self.done / new_name
            dest_path.write_text(content, encoding='utf-8')

            # Delete original
            filepath.unlink()

            self._log_event('action_executed', {
                'file': filepath.name,
                'action_type': action_type,
                'destination': new_name
            })

            print(f"    [OK] Executed successfully -> {new_name}")

            # Emit completion signal for Ralph Wiggum loop detection
            print("TASK_COMPLETE")
        else:
            # Log action failed to audit system
            if correlation_id:
                self.audit_logger.log_action_failed(
                    correlation_id=correlation_id,
                    action_type=action_type,
                    actor='approval_handler',
                    error=result.get('error', 'Unknown error'),
                    approver=approver,
                    approval_time=approval_time
                )
            print(f"    [ERROR] Execution failed")
        
        return result
    
    def process_rejected_actions(self) -> Dict[str, int]:
        """
        Process rejected actions (archive with rejection note).

        Returns:
            Statistics dictionary
        """
        stats = {
            'processed': 0,
            'archived': 0
        }

        rejected_files = self.get_rejected_actions()

        if not rejected_files:
            return stats

        print(f"\nArchiving {len(rejected_files)} rejected action(s)...")

        for filepath in rejected_files:
            try:
                content = filepath.read_text(encoding='utf-8')
                metadata = self._parse_frontmatter(content)

                correlation_id = metadata.get('correlation_id', '')
                action_type = metadata.get('action', 'unknown')
                rejection_time = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                rejector = "human"

                # Log rejection to audit system
                if correlation_id:
                    self.audit_logger.log_approval_rejected(
                        correlation_id=correlation_id,
                        rejector=rejector,
                        rejection_time=rejection_time,
                        action_type=action_type,
                        approval_file=filepath.name,
                        reason="Moved to /Rejected folder"
                    )

                # Add rejection metadata
                rejection_block = f"""
---
rejected: {datetime.now().isoformat()}
status: rejected
correlation_id: {correlation_id}
rejected_by: {rejector}
rejection_time: {rejection_time}
---

*This action was rejected by human reviewer.*
**Rejected By:** {rejector}
**Rejected At:** {datetime.fromisoformat(rejection_time).strftime('%Y-%m-%d %H:%M:%S')}
**Correlation ID:** {correlation_id}
"""
                content += rejection_block

                # Move to Done
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_name = filepath.stem + '_rejected_' + timestamp + filepath.suffix
                dest_path = self.done / new_name
                dest_path.write_text(content, encoding='utf-8')

                # Delete original
                filepath.unlink()

                self.processed_approvals.add(filepath.name)
                self._save_processed()

                self._log_event('action_rejected', {
                    'file': filepath.name,
                    'destination': new_name
                })

                stats['processed'] += 1
                stats['archived'] += 1
                print(f"    [OK] Archived: {new_name}")

            except Exception as e:
                print(f"    [ERROR] Error archiving {filepath.name}: {e}")

        return stats
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown (supports multi-line values)."""
        data = {}
        in_frontmatter = False
        current_key = None
        current_value = []
        in_multiline = False

        for line in content.split('\n'):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    # End of frontmatter - save any pending multiline value
                    if current_key and current_value:
                        data[current_key] = '\n'.join(current_value)
                    break

            if in_frontmatter:
                # Check if this is a new key:value pair
                if ':' in line and not line.startswith('  ') and not line.startswith('    '):
                    # Save previous key's value if any
                    if current_key and current_value:
                        data[current_key] = '\n'.join(current_value)
                    
                    # Parse new key:value
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # Check if it's a multiline value (starts with |)
                    if value == '|':
                        in_multiline = True
                        current_value = []
                    else:
                        in_multiline = False
                        current_value = [value] if value else []
                elif in_multiline or (current_key and line.startswith('  ')):
                    # Continuation of multiline value
                    current_value.append(line.rstrip())

        return data
    
    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an event to the daily log file."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            **details
        }
        
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def revoke_approval(self, filepath: Path, revoker: str, reason: str = "") -> bool:
        """
        Revoke an approval (pending or approved).

        Args:
            filepath: Path to approval file
            revoker: Who is revoking the approval
            reason: Reason for revocation

        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            if not filepath.exists():
                print(f"Error: Approval file not found: {filepath}")
                return False

            content = filepath.read_text(encoding='utf-8')
            metadata = self._parse_frontmatter(content)

            correlation_id = metadata.get('correlation_id', '')
            action_type = metadata.get('action', 'unknown')

            # Update frontmatter with revocation info
            revocation_time = datetime.now().isoformat()

            # Parse and update frontmatter
            lines = content.split('\n')
            new_lines = []
            in_frontmatter = False
            frontmatter_ended = False

            for line in lines:
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        new_lines.append(line)
                    elif not frontmatter_ended:
                        # End of frontmatter - add revocation fields
                        new_lines.append(f"status: revoked")
                        new_lines.append(f"revoked_by: {revoker}")
                        new_lines.append(f"revoked_at: {revocation_time}")
                        new_lines.append(f"revocation_reason: {reason or 'No reason provided'}")
                        new_lines.append(line)
                        frontmatter_ended = True
                    else:
                        new_lines.append(line)
                elif in_frontmatter and not frontmatter_ended:
                    # Skip old status line if present
                    if not line.strip().startswith('status:'):
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            updated_content = '\n'.join(new_lines)

            # Add revocation notice
            revocation_notice = f"""

---
## [WARNING] APPROVAL REVOKED

This approval has been revoked and will not be executed.

**Revoked By:** {revoker}
**Revoked At:** {datetime.fromisoformat(revocation_time).strftime('%Y-%m-%d %H:%M:%S')}
**Reason:** {reason or 'No reason provided'}

---
*AI Employee Approval Handler - Revocation*
"""
            updated_content += revocation_notice

            # Write back to file
            filepath.write_text(updated_content, encoding='utf-8')

            # Log revocation
            if correlation_id:
                self.audit_logger.log_action_completed(
                    correlation_id=correlation_id,
                    action_type=action_type,
                    actor=revoker,
                    result='revoked',
                    metadata={'reason': reason, 'revoked_at': revocation_time}
                )

            self._log_event('approval_revoked', {
                'file': filepath.name,
                'action_type': action_type,
                'revoked_by': revoker,
                'reason': reason
            })

            print(f"[OK] Revoked approval: {filepath.name}")
            return True

        except Exception as e:
            print(f"Error revoking approval: {e}")
            return False

    def add_approver(self, filepath: Path, approver: str, required_approvals: int = 1) -> Dict[str, Any]:
        """
        Add an approver to a multi-approver workflow.

        Args:
            filepath: Path to approval file
            approver: Name/ID of approver
            required_approvals: Number of approvals required (default: 1)

        Returns:
            Dictionary with approval status
        """
        try:
            if not filepath.exists():
                return {'success': False, 'error': 'File not found'}

            content = filepath.read_text(encoding='utf-8')
            metadata = self._parse_frontmatter(content)

            # Get existing approvers
            approvers_str = metadata.get('approvers', '')
            approvers = [a.strip() for a in approvers_str.split(',') if a.strip()] if approvers_str else []

            # Add new approver if not already present
            if approver not in approvers:
                approvers.append(approver)

            approval_count = len(approvers)
            approval_met = approval_count >= required_approvals

            # Update frontmatter
            lines = content.split('\n')
            new_lines = []
            in_frontmatter = False
            frontmatter_ended = False
            approvers_updated = False
            required_updated = False

            for line in lines:
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        new_lines.append(line)
                    elif not frontmatter_ended:
                        # End of frontmatter - add fields if not present
                        if not approvers_updated:
                            new_lines.append(f"approvers: {', '.join(approvers)}")
                        if not required_updated:
                            new_lines.append(f"required_approvals: {required_approvals}")
                        new_lines.append(f"approval_count: {approval_count}")
                        new_lines.append(f"approval_met: {approval_met}")
                        new_lines.append(line)
                        frontmatter_ended = True
                    else:
                        new_lines.append(line)
                elif in_frontmatter and not frontmatter_ended:
                    if line.strip().startswith('approvers:'):
                        new_lines.append(f"approvers: {', '.join(approvers)}")
                        approvers_updated = True
                    elif line.strip().startswith('required_approvals:'):
                        new_lines.append(f"required_approvals: {required_approvals}")
                        required_updated = True
                    elif line.strip().startswith('approval_count:') or line.strip().startswith('approval_met:'):
                        # Skip - will be recalculated
                        pass
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            updated_content = '\n'.join(new_lines)

            # Add approval record
            approval_record = f"""

---
## Approval Record

**Approver:** {approver}
**Approved At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Approval Count:** {approval_count}/{required_approvals}
**Status:** {'[OK] Approval threshold met' if approval_met else f'[WAITING] Waiting for {required_approvals - approval_count} more approval(s)'}

---
"""
            updated_content += approval_record

            # Write back
            filepath.write_text(updated_content, encoding='utf-8')

            # Log approval
            correlation_id = metadata.get('correlation_id', '')
            if correlation_id:
                self.audit_logger.log_approval_granted(
                    correlation_id=correlation_id,
                    approver=approver,
                    approval_time=datetime.now().isoformat(),
                    action_type=metadata.get('action', 'unknown'),
                    approval_file=filepath.name,
                    metadata={'approval_count': approval_count, 'required_approvals': required_approvals}
                )

            print(f"[OK] Added approver {approver} to {filepath.name} ({approval_count}/{required_approvals})")

            return {
                'success': True,
                'approvers': approvers,
                'approval_count': approval_count,
                'required_approvals': required_approvals,
                'approval_met': approval_met
            }

        except Exception as e:
            print(f"Error adding approver: {e}")
            return {'success': False, 'error': str(e)}

    def check_multi_approver_ready(self, filepath: Path) -> bool:
        """
        Check if a multi-approver approval has met the required threshold.

        Args:
            filepath: Path to approval file

        Returns:
            True if approval threshold met, False otherwise
        """
        try:
            content = filepath.read_text(encoding='utf-8')
            metadata = self._parse_frontmatter(content)

            required_approvals = int(metadata.get('required_approvals', 1))
            approvers_str = metadata.get('approvers', '')
            approvers = [a.strip() for a in approvers_str.split(',') if a.strip()] if approvers_str else []

            return len(approvers) >= required_approvals

        except Exception as e:
            print(f"Error checking multi-approver status: {e}")
            return False

    def run_cycle(self, executor_callback=None):
        """Run one complete approval processing cycle."""
        print("=" * 60)
        print("APPROVAL HANDLER - Processing Cycle")
        print("=" * 60)
        
        # Check pending
        pending = self.get_pending_approvals()
        if pending:
            print(f"\nPending Approvals: {len(pending)}")
            for p in pending:
                meta = self._parse_frontmatter(p.read_text())
                print(f"  - {p.name}: {meta.get('action', 'unknown')} ({meta.get('created', '')})")
        else:
            print("\nNo pending approvals")
        
        # Process approved
        approved_stats = self.process_approved_actions(executor_callback)
        if approved_stats['executed'] > 0:
            print(f"\n[OK] Executed: {approved_stats['executed']} action(s)")
        
        # Process rejected
        rejected_stats = self.process_rejected_actions()
        if rejected_stats['archived'] > 0:
            print(f"\n[OK] Archived: {rejected_stats['archived']} rejected action(s)")
        
        print("\n" + "=" * 60)
        print("Approval Handler Cycle Complete")
        print("=" * 60)


def main():
    """Run the approval handler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Approval Handler')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--create', help='Create approval request')
    parser.add_argument('--type', help='Action type for approval')
    parser.add_argument('--details', help='JSON details for approval')
    
    args = parser.parse_args()
    
    handler = ApprovalHandler(args.vault)
    
    if args.create and args.type:
        # Create approval request
        details = json.loads(args.details) if args.details else {}
        filepath = handler.create_approval_request(args.type, details, args.create)
        print(f"\nCreated: {filepath}")
        print("Move to /Approved/ to execute")
        print("Move to /Rejected/ to decline")
    else:
        # Run processing cycle
        handler.run_cycle()


if __name__ == '__main__':
    main()
