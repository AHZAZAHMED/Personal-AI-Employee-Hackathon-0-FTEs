"""
Task Processor for AI Employee

This script simulates what Qwen Code would do when processing tasks.
It reads task files, determines actions based on Company Handbook rules,
and moves tasks through the workflow.

In production, this logic would be executed by Qwen Code itself.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class TaskProcessor:
    """
    Processes task files according to Company Handbook rules.
    This simulates what Qwen Code would do.
    """
    
    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.needs_action = self.vault / 'Needs_Action'
        self.in_progress = self.vault / 'In_Progress' / 'qwen_agent'
        self.pending_approval = self.vault / 'Pending_Approval'
        self.approved = self.vault / 'Approved'
        self.done = self.vault / 'Done'
        self.logs = self.vault / 'Logs'
        self.inbox = self.vault / 'Inbox'
        self.dashboard = self.vault / 'Dashboard.md'
        self.handbook = self.vault / 'Company_Handbook.md'
        
        # Auto-approve these task types
        self.auto_approve_types = [
            'file_drop',
            'manual_task',
            'data_analysis',
            'categorization'
        ]
        
        # Require approval for these
        self.require_approval_types = [
            'email_send',
            'payment_request',
            'social_media_post',
            'external_api_call'
        ]
    
    def process_all_tasks(self) -> Dict[str, int]:
        """
        Process all tasks in In_Progress/qwen_agent folder.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'processed': 0,
            'completed': 0,
            'pending_approval': 0,
            'errors': 0
        }
        
        if not self.in_progress.exists():
            return stats
        
        task_files = list(self.in_progress.glob('*.md'))
        
        for task_file in task_files:
            try:
                result = self.process_task(task_file)
                stats['processed'] += 1
                
                if result['status'] == 'completed':
                    stats['completed'] += 1
                elif result['status'] == 'pending_approval':
                    stats['pending_approval'] += 1
                    
            except Exception as e:
                print(f"Error processing {task_file.name}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def process_task(self, task_file: Path) -> Dict[str, str]:
        """
        Process a single task file.
        
        Args:
            task_file: Path to the task file
            
        Returns:
            Result dictionary with status
        """
        # Read task content
        content = task_file.read_text(encoding='utf-8')
        
        # Parse frontmatter to get task type
        task_data = self._parse_frontmatter(content)
        task_type = task_data.get('type', 'unknown')
        
        print(f"Processing: {task_file.name} (type: {task_type})")
        
        # Determine if approval is needed
        if task_type in self.require_approval_types:
            return self._request_approval(task_file, task_data)
        elif task_type in self.auto_approve_types:
            return self._complete_task(task_file, task_data)
        else:
            # Unknown type - request approval
            return self._request_approval(task_file, task_data)
    
    def _complete_task(self, task_file: Path, task_data: Dict) -> Dict[str, str]:
        """
        Mark task as completed and move to Done folder.
        Actually processes the file content for Bronze tier.
        """
        # Read task content
        content = task_file.read_text(encoding='utf-8')
        
        # Extract original file info
        original_name = task_data.get('original_name', 'unknown')
        original_path = task_data.get('original_path', '')
        file_type = task_data.get('type', 'file_drop')
        
        # For file_drop types, read the original file and categorize it
        categorization = self._categorize_content(original_path, content)
        
        # Add completion metadata
        completion_block = f"""
---
completed: {datetime.now().isoformat()}
completion_status: success
processed_by: TaskProcessor (Bronze Tier AI Employee)
---

## Processing Summary

**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** Success

### File Analysis
- **Original File:** {original_name}
- **Type:** {file_type}
- **Category:** {categorization['category']}
- **Priority:** {categorization['priority']}

### Content Summary
{categorization['summary']}

### Actions Taken
- Read file content
- Analyzed for keywords and intent
- Categorized as: {categorization['category']}
- Suggested follow-up: {categorization['suggested_action']}

### Filed Location
Original file remains in: /Inbox/
Action file archived to: /Done/

---
*Processed by AI Employee Bronze Tier v0.1.0*
"""
        
        # Add completion block to content
        content += completion_block
        
        # Generate new filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = task_file.stem + '_completed_' + timestamp + task_file.suffix
        
        # Write and move to Done
        dest_path = self.done / new_name
        dest_path.write_text(content, encoding='utf-8')
        
        # Delete original
        task_file.unlink()
        
        # Log the completion
        self._log_event('task_completed', {
            'file': task_file.name,
            'type': task_data.get('type', 'unknown'),
            'category': categorization['category'],
            'destination': new_name
        })
        
        print(f"  Completed: {new_name} (Category: {categorization['category']})")
        
        return {'status': 'completed', 'destination': str(dest_path)}
    
    def _categorize_content(self, file_path: str, content: str) -> Dict[str, str]:
        """
        Analyze file content and categorize it.
        This simulates what Qwen Code would do with AI understanding.
        """
        content_lower = content.lower()
        
        # Keyword-based categorization (Bronze tier - simple pattern matching)
        # In production, Qwen Code would use AI to understand context
        
        category = "General"
        priority = "Normal"
        suggested_action = "Review and file appropriately"
        summary = "No specific category identified."
        
        # Check for urgent/priority keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical']
        if any(kw in content_lower for kw in urgent_keywords):
            priority = "High"
            suggested_action = "Review within 24 hours"
        
        # Check for invoice/payment keywords
        finance_keywords = ['invoice', 'payment', 'bill', 'receipt', 'paid', 'due', 'amount']
        if any(kw in content_lower for kw in finance_keywords):
            category = "Finance"
            summary = "Document appears to be related to financial matters."
            suggested_action = "Verify payment status and file in accounting records"
        
        # Check for contract/legal keywords
        legal_keywords = ['contract', 'agreement', 'legal', 'terms', 'sign', 'signature']
        if any(kw in content_lower for kw in legal_keywords):
            category = "Legal"
            summary = "Document appears to be a legal or contractual matter."
            suggested_action = "Review terms carefully before signing"
        
        # Check for meeting/schedule keywords
        meeting_keywords = ['meeting', 'schedule', 'calendar', 'appointment', 'zoom', 'call']
        if any(kw in content_lower for kw in meeting_keywords):
            category = "Schedule"
            summary = "Document relates to scheduling or meetings."
            suggested_action = "Add to calendar if action required"
        
        # Check for project/task keywords
        project_keywords = ['project', 'task', 'deadline', 'deliverable', 'milestone']
        if any(kw in content_lower for kw in project_keywords):
            category = "Project"
            summary = "Document relates to project work."
            suggested_action = "Add to project tracker if new task"
        
        # Check for test keywords
        if 'test' in content_lower:
            category = "Test"
            summary = "This appears to be a test document."
            suggested_action = "No action required - test file"
        
        # Generate brief summary from content
        try:
            # Get first 200 chars as preview
            preview = content.replace('\n', ' ').strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            summary = f"Preview: {preview}"
        except:
            pass
        
        return {
            'category': category,
            'priority': priority,
            'suggested_action': suggested_action,
            'summary': summary
        }
    
    def _request_approval(self, task_file: Path, task_data: Dict) -> Dict[str, str]:
        """
        Move task to Pending_Approval folder.
        """
        # Read current content
        content = task_file.read_text(encoding='utf-8')
        
        # Add approval request header
        approval_header = f"""---
approval_requested: {datetime.now().isoformat()}
approval_reason: Task type '{task_data.get('type', 'unknown')}' requires human review
---

## Approval Required

This task requires human review before proceeding.

**Reason:** Task type requires human oversight per Company Handbook

**To Approve:** Move this file to `/Approved` folder
**To Reject:** Move this file to `/Rejected` folder

---
"""
        
        # Prepend approval header
        new_content = approval_header + content
        
        # Move to Pending_Approval
        dest_path = self.pending_approval / task_file.name
        dest_path.write_text(new_content, encoding='utf-8')
        
        # Delete original
        task_file.unlink()
        
        # Log
        self._log_event('approval_requested', {
            'file': task_file.name,
            'type': task_data.get('type', 'unknown')
        })
        
        print(f"  Approval requested: {task_file.name}")
        
        return {'status': 'pending_approval', 'destination': str(dest_path)}
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown content."""
        import re
        
        # Simple frontmatter parser
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return {}
        
        data = {}
        for line in match.group(1).split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                data[key] = value
        
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
    
    def process_approved_tasks(self) -> int:
        """
        Process any tasks that have been approved (moved to /Approved).
        
        Returns:
            Number of tasks processed
        """
        if not self.approved.exists():
            return 0
        
        approved_files = list(self.approved.glob('*.md'))
        count = 0
        
        for task_file in approved_files:
            # Process approved task (same as auto-approved)
            content = task_file.read_text(encoding='utf-8')
            task_data = self._parse_frontmatter(content)
            
            self._complete_task(task_file, task_data)
            count += 1
        
        return count


def main():
    """Run the task processor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Task Processor')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--approved', action='store_true', 
                       help='Process approved tasks instead of in-progress')
    
    args = parser.parse_args()
    
    processor = TaskProcessor(args.vault)
    
    if args.approved:
        count = processor.process_approved_tasks()
        print(f"Processed {count} approved task(s)")
    else:
        stats = processor.process_all_tasks()
        print("\n" + "=" * 40)
        print("Task Processing Summary:")
        print(f"  Processed: {stats['processed']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Pending Approval: {stats['pending_approval']}")
        print(f"  Errors: {stats['errors']}")
        print("=" * 40)


if __name__ == '__main__':
    main()
