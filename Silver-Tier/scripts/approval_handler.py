"""
Approval Handler for AI Employee - Silver Tier

Manages human-in-the-loop approval workflow:
- Creates approval requests for sensitive actions
- Processes approved actions (executes them)
- Archives rejected actions
- Maintains audit trail

Usage:
    python scripts/approval_handler.py --vault AI_Employee_Vault
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class ApprovalHandler:
    """Manages approval workflow for AI Employee."""
    
    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        
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
                                 description: str = "") -> Path:
        """
        Create a new approval request file.
        
        Args:
            action_type: Type of action (email_reply, payment, etc.)
            details: Dictionary with action details
            description: Human-readable description
            
        Returns:
            Path to created approval request file
        """
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
        
        self._log_event('approval_requested', {
            'file': filename,
            'action_type': action_type,
            'details': details
        })
        
        print(f"  Created approval request: {filename}")
        return filepath
    
    def get_pending_approvals(self) -> List[Path]:
        """Get all pending approval requests."""
        if not self.pending_approval.exists():
            return []
        return list(self.pending_approval.glob('*.md'))
    
    def get_approved_actions(self) -> List[Path]:
        """Get approved actions ready to execute."""
        if not self.approved.exists():
            return []
        return [f for f in self.approved.glob('*.md') 
                if f.name not in self.processed_approvals]
    
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
        
        # If no executor provided, try to use email sender (MCP-based)
        if executor_callback is None:
            try:
                from email_sender_mcp import execute_approved_email
                executor_callback = execute_approved_email
                print("  Using MCP Email Sender for email actions")
            except Exception as e:
                print(f"  MCP Email Sender not available: {e}")
                print("  Will mark as executed only")
        
        for filepath in approved_files:
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
        
        print(f"\n  Executing: {filepath.name}")
        print(f"    Type: {action_type}")
        
        # Execute based on action type
        result = {'success': False, 'action_type': action_type}
        
        if executor_callback:
            # Use custom executor
            result = executor_callback(action_type, metadata, content)
        else:
            # Default: just mark as executed
            print(f"    No executor configured - marking as executed")
            result['success'] = True
        
        if result['success']:
            # Add execution metadata
            execution_block = f"""
---
executed: {datetime.now().isoformat()}
execution_status: success
executed_by: ApprovalHandler (Silver Tier)
action_type: {action_type}
---

## Execution Result

**Executed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** ✓ Success
**Action:** {action_type.replace('_', ' ').title()}

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
        else:
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
                
                # Add rejection metadata
                rejection_block = f"""
---
rejected: {datetime.now().isoformat()}
status: rejected
---

*This action was rejected by human reviewer.*
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
            print(f"\n✓ Archived: {rejected_stats['archived']} rejected action(s)")
        
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
