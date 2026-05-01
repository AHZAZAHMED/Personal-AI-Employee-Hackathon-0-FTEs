"""
Orchestrator for AI Employee - Gold Tier

Main coordination script that:
1. Monitors /Needs_Action folder for new tasks
2. Creates Plan.md files for complex tasks via Skill Registry
3. Requests approval for sensitive actions
4. Executes approved actions via dynamic skill dispatch
5. Updates Dashboard.md with current status

Gold Tier Features:
- Dynamic Skill Registry (auto-discovers skills/)
- Plan generation
- Approval workflow with correlation IDs
- Email sending after approval
- Skill-based task routing
- Structured audit logging
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import Silver Tier modules
sys.path.insert(0, str(Path(__file__).parent))
from approval_handler import ApprovalHandler
from plan_generator import PlanGenerator
from audit_logger import get_audit_logger
from file_locking import try_lock
from alerting import AlertManager, AlertSeverity

# Import Gold Tier Skill Registry (dynamic discovery)
try:
    from skill_registry import SkillRegistry
    SKILL_REGISTRY_AVAILABLE = True
except ImportError:
    SKILL_REGISTRY_AVAILABLE = False


class Orchestrator:
    """Main orchestrator for AI Employee - Gold Tier."""
    
    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        
        # Folders
        self.needs_action = self.vault / 'Needs_Action'
        self.in_progress = self.vault / 'In_Progress' / 'qwen_agent'
        self.pending_approval = self.vault / 'Pending_Approval'
        self.approved = self.vault / 'Approved'
        self.done = self.vault / 'Done'
        self.logs = self.vault / 'Logs'
        self.plans = self.vault / 'Plans'
        
        # Key files
        self.dashboard = self.vault / 'Dashboard.md'
        self.handbook = self.vault / 'Company_Handbook.md'
        
        # Ensure folders exist
        for folder in [self.needs_action, self.in_progress, self.plans,
                       self.pending_approval, self.approved, self.rejected if hasattr(self, 'rejected') else self.vault / 'Rejected',
                       self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize Silver Tier handlers
        self.approval_handler = ApprovalHandler(str(vault_path))
        self.plan_generator = PlanGenerator(str(vault_path))

        # Initialize audit logger
        self.audit_logger = get_audit_logger(str(vault_path))

        # Initialize alert manager
        self.alert_manager = AlertManager(vault_path=str(vault_path))

        # Initialize Gold Tier Skill Registry (dynamic discovery)
        self.skill_registry = None
        if SKILL_REGISTRY_AVAILABLE:
            try:
                skills_dir = Path(__file__).parent.parent / 'skills'
                self.skill_registry = SkillRegistry(skills_dir=str(skills_dir))
                count = self.skill_registry.discover()
                print(f"  Skill Registry: {count} skills discovered")
            except Exception as e:
                print(f"  Warning: Skill Registry init failed: {e}")
                self.skill_registry = None

        # Statistics
        self.stats = {
            'tasks_processed': 0,
            'plans_created': 0,
            'approvals_requested': 0,
            'approvals_executed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def get_pending_tasks(self) -> List[Path]:
        """Get all pending task files from /Needs_Action."""
        if not self.needs_action.exists():
            return []
        return sorted(self.needs_action.glob('*.md'), key=lambda p: p.stat().st_mtime)
    
    def move_to_in_progress(self, filepath: Path) -> Path:
        """Move task to /In_Progress/qwen_agent."""
        dest = self.in_progress / filepath.name
        
        # If destination already exists, add timestamp to avoid conflict
        if dest.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest = self.in_progress / f'{filepath.stem}_{timestamp}{filepath.suffix}'
        
        filepath.rename(dest)
        return dest
    
    def process_task(self, task_file: Path) -> Dict[str, Any]:
        """
        Process a single task with Silver Tier features.

        Args:
            task_file: Path to task file

        Returns:
            Processing result
        """
        content = task_file.read_text(encoding='utf-8')
        task_data = self._parse_frontmatter(content)

        task_type = task_data.get('type', 'unknown')
        priority = task_data.get('priority', 'normal')

        # Generate correlation ID for this task
        correlation_id = self.audit_logger.generate_correlation_id()

        print(f"\nProcessing: {task_file.name}")
        print(f"  Type: {task_type}")
        print(f"  Priority: {priority}")
        print(f"  Correlation ID: {correlation_id}")

        # Log task creation
        self.audit_logger.log_task_created(
            correlation_id=correlation_id,
            task_type=task_type,
            task_data={
                'task_id': task_file.name,
                'priority': priority,
                'from': task_data.get('from', ''),
                'subject': task_data.get('subject', ''),
                'filename': task_file.name
            },
            source='needs_action'
        )

        # Log task processing started
        self.audit_logger.log_task_processing_started(
            correlation_id=correlation_id,
            task_id=task_file.name,
            task_type=task_type
        )

        result = {'success': False, 'action': 'none', 'correlation_id': correlation_id}
        
        # Step 1: Create Plan.md for complex tasks
        if task_type in ['email', 'email_reply', 'payment', 'social_media']:
            print(f"  Creating plan...")
            plan_path = self.plan_generator.create_plan(task_file, task_data)
            self.stats['plans_created'] += 1
            result['plan'] = str(plan_path)
        
        # Step 2: Determine if approval is needed
        requires_approval = self._requires_approval(task_type, task_data)
        
        if requires_approval:
            # Create approval request with correlation ID
            print(f"  Creating approval request...")
            approval_details = self._get_approval_details(task_type, task_data, content)
            approval_file = self.approval_handler.create_approval_request(
                action_type=task_type,
                details=approval_details,
                description=f"Task from {task_file.name}",
                correlation_id=correlation_id
            )
            self.stats['approvals_requested'] += 1
            result['action'] = 'approval_requested'
            result['approval_file'] = str(approval_file)

            # Move original file to In_Progress to mark as being processed
            # This prevents re-processing on next orchestrator run
            try:
                if task_file.exists():
                    self.move_to_in_progress(task_file)
                    print(f"  Original file moved to: {self.in_progress / task_file.name}")
            except Exception as e:
                print(f"  Warning: Could not move original file: {e}")

            print(f"  Approval request created: {approval_file.name}")
            print(f"  Human must approve in /Pending_Approval/ folder")

            # Update dashboard immediately to show pending approvals
            self.update_dashboard()

        else:
            # Auto-approved - process directly
            print(f"  Auto-approved, processing...")
            result = self._execute_task(task_file, task_data, content, correlation_id)

            # Update dashboard after completion
            self.update_dashboard()

        return result
    
    def _requires_approval(self, task_type: str, task_data: Dict) -> bool:
        """Determine if task requires approval."""
        
        # Check for no-reply/automated emails that DON'T need responses
        from_email = task_data.get('from', '').lower()
        subject = task_data.get('subject', '').lower()
        
        # Skip automated/no-reply emails
        no_reply_keywords = [
            'no-reply', 'noreply', 'do-not-reply', 'donotreply',
            'automated', 'notification', 'alert', 'newsletter',
            'linkedin', 'facebook', 'twitter', 'google', 'microsoft',
            'subscription', 'verify', 'confirm', 'security alert',
            'login alert', 'appeared in search', 'profile viewed',
            'job alert', 'digest', 'weekly update', 'monthly update'
        ]
        
        # Check if email is from no-reply or automated source
        if any(keyword in from_email for keyword in no_reply_keywords):
            self.logger.info(f"Skipping automated email from: {from_email}")
            return False  # Auto-archive, no approval needed
        
        # Check subject for automated content
        if any(keyword in subject for keyword in no_reply_keywords):
            self.logger.info(f"Skipping automated email: {subject}")
            return False  # Auto-archive, no approval needed
        
        # These types always require approval
        approval_types = [
            'email',          # ALL emails require approval for reply
            'email_send',
            'email_reply',
            'payment',
            'payment_request',
            'social_media',
            'social_media_post'
        ]

        if task_type in approval_types:
            return True

        return False

    def _generate_fallback_email(self, task_data: Dict) -> str:
        """Generate professional email using template (fallback when AI unavailable)."""
        sender_email = task_data.get('from', 'Unknown')
        subject = task_data.get('subject', 'your inquiry')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Extract sender name
        sender_name = 'Valued Contact'
        if '<' in sender_email:
            sender_name = sender_email.split('<')[0].strip()
        elif sender_email and sender_email != 'Unknown':
            sender_name = sender_email.split('@')[0].replace('.', ' ').title()
        
        # Professional template with EXTRA line breaks for email clients
        return f"""Dear {sender_name},


Thank you for contacting us regarding "{subject}".


We have received your message and our team will review it shortly. If your inquiry matches our current requirements, we will reach out to you regarding the next steps.


We appreciate your interest and look forward to assisting you.


Best regards,


AI Employee Response System
Automated Customer Service

---
Reference ID: {timestamp}
This is an automated response. For urgent matters, please reply with "URGENT" in the subject line."""
    
    def _get_approval_details(self, task_type: str, task_data: Dict, content: str) -> Dict[str, Any]:
        """Extract details for approval request using skill-based AI analysis."""
        details = {
            'task_type': task_type,
            'priority': task_data.get('priority', 'normal'),
        }

        if task_type in ['email', 'email_reply', 'email_send']:
            # Extract email fields
            sender_email = task_data.get('from', 'Unknown')

            details['to'] = sender_email
            details['from_email'] = sender_email
            details['subject'] = f"Re: {task_data.get('subject', 'No Subject')}"
            details['gmail_id'] = task_data.get('gmail_id', '')
            details['original_subject'] = task_data.get('subject', '')
            details['risk_level'] = 'medium'

            # Generate draft reply using email_responder skill
            print(f"  [Skill] Generating email response via skill...")

            # Extract clean email body from task_data
            email_body = task_data.get('body', '')
            if not email_body:
                if '## Email Content' in content:
                    email_body = content.split('## Email Content')[1].split('##')[0].strip()
                elif '## Content' in content:
                    email_body = content.split('## Content')[1].split('##')[0].strip()

            if self.skill_registry:
                result = self.skill_registry.dispatch_by_task_type(
                    'email',
                    from_email=sender_email,
                    subject=task_data.get('subject', ''),
                    body=email_body,
                    vault_path=str(self.vault)
                )
                if result.get('success') and result.get('response'):
                    # Sanitize Unicode from Claude response
                    from claude_ai_integration import sanitize_unicode
                    details['draft_body'] = sanitize_unicode(result['response'])
                    details['method'] = result.get('method', 'skill')
                    print(f"  [Skill] [OK] Response generated via skill (method: {result.get('method')})")
                else:
                    print(f"  [Skill] [WARN] Skill returned without response, using template")
                    details['draft_body'] = self._generate_fallback_email(task_data)
            else:
                print(f"  [INFO] No skill registry, using smart template")
                details['draft_body'] = self._generate_fallback_email(task_data)

        elif task_type == 'payment':
            details['amount'] = task_data.get('amount', 'Unknown')
            details['recipient'] = task_data.get('recipient', 'Unknown')
            details['risk_level'] = 'high'

        elif task_type == 'social_media':
            details['platform'] = task_data.get('platform', 'Unknown')
            details['post_type'] = task_data.get('post_type', 'Unknown')
            details['risk_level'] = 'medium'

        else:
            details['risk_level'] = 'low'

        return details
    
    def _execute_task(self, task_file: Path, task_data: Dict, content: str,
                      correlation_id: str = "") -> Dict[str, Any]:
        """Execute an auto-approved task — uses skill registry ONLY."""
        task_type = task_data.get('type', 'unknown')

        if self.skill_registry:
            print(f"  Dispatching via Skill Registry: task_type='{task_type}'")

            # Pass all task_data fields plus vault_path and correlation_id
            # This allows each skill to receive the parameters it needs
            kwargs = dict(task_data)
            kwargs['vault_path'] = str(self.vault)
            kwargs['correlation_id'] = correlation_id

            # Remove task_type from kwargs to avoid duplicate argument error
            kwargs.pop('task_type', None)
            kwargs.pop('type', None)
            kwargs.pop('status', None)
            kwargs.pop('created_at', None)

            # Also add common aliases for backward compatibility
            if 'from' in task_data and 'from_email' not in kwargs:
                kwargs['from_email'] = task_data['from']
            if 'body' not in kwargs and 'content' in task_data:
                kwargs['body'] = task_data['content']
            # For email_to_invoice skill
            if 'body' in task_data and 'email_content' not in kwargs:
                kwargs['email_content'] = task_data['body']

            result = self.skill_registry.dispatch_by_task_type(task_type, **kwargs)
            if result.get('success'):
                print(f"  [OK] Skill executed: {task_type} -> success")

                # Log task completion
                if correlation_id:
                    self.audit_logger.log_task_completed(
                        correlation_id=correlation_id,
                        task_id=task_file.name,
                        result='success',
                        metadata={'task_type': task_type}
                    )

                return self._mark_task_complete(task_file, task_data, content,
                                               f"Executed via Skill Registry: {task_type}",
                                               str(result), correlation_id)
            else:
                error_msg = result.get('error', 'unknown')
                print(f"  [WARN] Skill failed: {error_msg}")

                # Log task failure
                if correlation_id:
                    self.audit_logger.log_task_completed(
                        correlation_id=correlation_id,
                        task_id=task_file.name,
                        result='failed',
                        metadata={'task_type': task_type, 'error': error_msg}
                    )

                # Send alert for skill failure
                try:
                    self.alert_manager.send_alert(
                        severity=AlertSeverity.ERROR,
                        title=f"Skill Execution Failed: {task_type}",
                        message=f"Task: {task_file.name}\nSkill: {task_type}\nError: {error_msg}",
                        context={'task_file': task_file.name, 'task_type': task_type, 'error': error_msg}
                    )
                except Exception as alert_error:
                    print(f"  [WARN] Failed to send alert: {alert_error}")

        print(f"  No skill/handler for task type '{task_type}', marking complete")
        return self._mark_task_complete(task_file, task_data, content,
                                        f"No skill registered (type: {task_type})",
                                        "", correlation_id)

    def _mark_task_complete(self, task_file: Path, task_data: Dict, content: str,
                            action_desc: str, result_str: str, correlation_id: str = "") -> Dict[str, Any]:
        """Mark a task as complete — moved to Done/."""
        task_type = task_data.get('type', 'unknown')

        completion_block = f"""
---
completed: {datetime.now().isoformat()}
completion_status: success
processed_by: Orchestrator (Gold Tier)
action: {action_desc}
correlation_id: {correlation_id}
---

## Processing Summary

**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** Success
**Type:** {task_type}
**Action:** {action_desc}
**Correlation ID:** {correlation_id}
"""
        if result_str:
            completion_block += f"\n**Result:**\n```\n{result_str[:500]}\n```\n"

        completion_block += f"""
---
*AI Employee Orchestrator v1.0.0 (Gold Tier)*
"""
        content += completion_block

        # Move to Done
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = task_file.stem + '_completed_' + timestamp + task_file.suffix
        dest_path = self.done / new_name
        dest_path.write_text(content, encoding='utf-8')
        task_file.unlink()

        # Clean up associated plan file if exists
        plan_prefix = task_file.stem.replace('EMAIL_', 'PLAN_EMAIL_').replace('FILE_', 'PLAN_FILE_')
        plan_files = list(self.plans.glob(f'{plan_prefix}*.md'))
        for plan_file in plan_files:
            try:
                plan_file.unlink()
                self.logger.info(f"Cleaned up plan file: {plan_file.name}")
            except Exception as e:
                self.logger.debug(f"Could not clean up plan: {e}")

        print(f"  [DONE] Completed -> {new_name}")

        # Emit completion signal for Ralph Wiggum loop detection
        print("TASK_COMPLETE")

        return {'success': True, 'action': 'completed', 'destination': str(dest_path)}
    
    def process_approved_actions(self):
        """Process actions that have been approved — uses skill registry ONLY."""
        # Import approval token manager
        from approval_tokens import get_token_manager
        token_manager = get_token_manager(str(self.vault))

        def executor(action_type, metadata, content, correlation_id="", approver="", approval_time=""):
            if self.skill_registry:
                # Generate approval token for this action
                approval_token = token_manager.generate_token(
                    action_type=action_type,
                    metadata={
                        'to': metadata.get('to', ''),
                        'subject': metadata.get('subject', ''),
                        'approved_at': approval_time or datetime.now().isoformat(),
                        'approved_by': approver or 'human',
                        'correlation_id': correlation_id
                    },
                    expires_hours=1,  # Short expiration for approved actions
                    single_use=True
                )

                # For email approvals, route to email_send to actually send the draft
                if action_type in ['email', 'email_reply', 'email_send']:
                    return self.skill_registry.dispatch_by_task_type(
                        'email_send',
                        to=metadata.get('to', ''),
                        subject=metadata.get('subject', ''),
                        body=metadata.get('draft_body', metadata.get('body', '')),
                        in_reply_to=metadata.get('gmail_id', ''),
                        approval_token=approval_token,
                        correlation_id=correlation_id,
                        approver=approver,
                        approval_time=approval_time,
                        vault_path=str(self.vault)
                    )
                # For other types, use standard routing
                return self.skill_registry.dispatch_by_task_type(
                    action_type,
                    from_email=metadata.get('from_email', metadata.get('to', '')),
                    subject=metadata.get('subject', ''),
                    body=metadata.get('draft_body', metadata.get('body', '')),
                    to=metadata.get('to', ''),
                    approval_token=approval_token,
                    correlation_id=correlation_id,
                    approver=approver,
                    approval_time=approval_time,
                    vault_path=str(self.vault)
                )
            return {'success': False, 'error': 'No skill registry available'}

        stats = self.approval_handler.process_approved_actions(executor)
        self.stats['approvals_executed'] += stats.get('executed', 0)
        self.update_dashboard()
    
    def run_cycle(self):
        """Run one complete orchestration cycle."""
        import logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('Orchestrator')
        
        self.logger.info("Starting Gold Tier orchestration cycle")
        
        # Step 1: Get pending tasks
        pending_tasks = self.get_pending_tasks()
        
        if pending_tasks:
            self.logger.info(f"Found {len(pending_tasks)} pending task(s)")

            # Step 2: Process each task (BEFORE moving)
            for task in pending_tasks:
                # Use file locking to prevent concurrent processing
                lock_id = f"task_{task.name}"

                with try_lock(lock_id, timeout=0, vault_path=str(self.vault)) as locked:
                    if not locked:
                        self.logger.info(f"Task {task.name} is locked by another process, skipping")
                        continue

                    try:
                        # Process FIRST (creates plan, approval request, or executes)
                        # process_task now moves the file internally when needed
                        result = self.process_task(task)
                        self.stats['tasks_processed'] += 1

                        # Move to in_progress only if file still exists and wasn't moved internally
                        # (e.g., for auto-approved tasks that don't create approval requests)
                        if task.exists() and result.get('action') != 'approval_requested':
                            self.move_to_in_progress(task)

                    except Exception as e:
                        self.logger.error(f"Error processing {task.name}: {e}")
                        self.stats['errors'] += 1

                        # Send alert for critical processing errors
                        try:
                            self.alert_manager.send_alert(
                                severity=AlertSeverity.ERROR,
                                title=f"Task Processing Error",
                                message=f"Failed to process task: {task.name}\nError: {str(e)}",
                                context={'task_file': task.name, 'error': str(e)}
                            )
                        except Exception as alert_error:
                            self.logger.error(f"Failed to send alert: {alert_error}")
        else:
            self.logger.info("No pending tasks")
        
        # Step 3: Process approved actions
        self.logger.info("Checking for approved actions...")
        self.process_approved_actions()
        
        # Step 4: Update dashboard
        self.update_dashboard()
        
        self.logger.info("Orchestration cycle complete")
        self._print_stats()
    
    def update_dashboard(self):
        """Update Dashboard.md with comprehensive current stats."""
        if not self.dashboard.exists():
            self.logger.warning("Dashboard not found")
            return

        # Count files in all folders
        needs_action_count = len(list(self.needs_action.glob('*.md')))
        in_progress_count = len(list(self.in_progress.glob('*.md')))
        pending_approval_count = len(list(self.pending_approval.glob('*.md')))
        approved_count = len(list(self.approved.glob('*.md')))
        done_today = len([f for f in self.done.glob('*.md') if self._is_today(f)])
        done_week = len([f for f in self.done.glob('*.md') if self._is_this_week(f)])
        
        # Get recent activity
        recent_files = sorted(self.done.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True)[:5]
        
        # Read dashboard
        content = self.dashboard.read_text(encoding='utf-8')
        
        # Update Quick Stats
        content = self._update_stat(content, 'Pending Tasks', needs_action_count)
        content = self._update_stat(content, 'In Progress', in_progress_count)
        content = self._update_stat(content, 'Awaiting Approval', pending_approval_count)
        content = self._update_stat(content, 'Completed Today', done_today)
        content = self._update_stat(content, 'Completed This Week', done_week)
        
        # Update timestamp
        import re
        content = re.sub(
            r'last_updated:.*',
            f'last_updated: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}',
            content
        )
        
        # Update Inbox Summary
        if needs_action_count > 0:
            inbox_summary = f"*{needs_action_count} new item(s) awaiting processing*"
        else:
            inbox_summary = "*No new items*"
        content = re.sub(
            r'## 📥 Inbox Summary\s*\n\s*\*[^*]+\*',
            f'## 📥 Inbox Summary\n\n{inbox_summary}',
            content,
            flags=re.MULTILINE
        )
        
        # Update Active Tasks
        if in_progress_count > 0:
            active_summary = f"*{in_progress_count} task(s) being processed*"
        else:
            active_summary = "*No active tasks*"
        content = re.sub(
            r'## 🎯 Active Tasks\s*\n\s*\*[^*]+\*',
            f'## 🎯 Active Tasks\n\n{active_summary}',
            content,
            flags=re.MULTILINE
        )
        
        # Update Pending Approvals
        if pending_approval_count > 0:
            pending_summary = f"*{pending_approval_count} approval(s) awaiting review*"
        else:
            pending_summary = "*No pending approvals*"
        content = re.sub(
            r'## ⏳ Pending Approvals\s*\n\s*\*[^*]+\*',
            f'## ⏳ Pending Approvals\n\n{pending_summary}',
            content,
            flags=re.MULTILINE
        )
        
        # Update Recent Activity (show unique recent files, max 5)
        if recent_files:
            activity_rows = []
            seen = set()
            for f in recent_files:
                if f.name not in seen and len(activity_rows) < 5:
                    seen.add(f.name)
                    timestamp = datetime.fromtimestamp(f.stat().st_mtime).strftime('%H:%M')
                    activity_rows.append(f"| {timestamp} | Task completed | ✅ |")
            activity_table = "\n".join(activity_rows)
            content = re.sub(
                r'\| Time \| Action \| Status \|\s*\n\|------\|--------\|--------\|\s*\n(.*?)(?=\n---|\n##|\Z)',
                f'| Time | Action | Status |\n|------|--------|--------|\n{activity_table}\n',
                content,
                flags=re.MULTILINE | re.DOTALL
            )
        else:
            content = re.sub(
                r'\| Time \| Action \| Status \|\s*\n\|------\|--------\|--------\|\s*\n(\| -- \| -- \| -- \|\s*)?',
                '| Time | Action | Status |\n|------|--------|--------|\n| -- | -- | -- |\n',
                content,
                flags=re.MULTILINE
            )
        
        # Write updated dashboard
        self.dashboard.write_text(content, encoding='utf-8')
        self.logger.info("Dashboard updated")
    
    def _update_stat(self, content: str, label: str, value: int) -> str:
        """Update a stat value in dashboard Quick Stats table."""
        import re
        # Match the row: | Pending Tasks | 0     | → | Pending Tasks | 5     |
        pattern = rf'(\|\s*{re.escape(label)}\s*\|)\s*\S+\s*(\|)'
        replacement = rf'\g<1> {value} \g<2>'
        content = re.sub(pattern, replacement, content)
        return content
    
    def _is_today(self, filepath: Path) -> bool:
        """Check if file was modified today."""
        today = datetime.now().date()
        file_date = datetime.fromtimestamp(filepath.stat().st_mtime).date()
        return file_date == today

    def _is_this_week(self, filepath: Path) -> bool:
        """Check if file was modified this week."""
        from datetime import timedelta
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        file_date = datetime.fromtimestamp(filepath.stat().st_mtime)
        return file_date >= week_start
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter."""
        data = {}
        in_frontmatter = False
        
        for line in content.split('\n'):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip().strip('"\'')
        
        return data
    
    def _print_stats(self):
        """Print statistics."""
        print("\n" + "=" * 50)
        print("Orchestrator Statistics:")
        print(f"  Tasks processed: {self.stats['tasks_processed']}")
        print(f"  Plans created: {self.stats['plans_created']}")
        print(f"  Approvals requested: {self.stats['approvals_requested']}")
        print(f"  Approvals executed: {self.stats['approvals_executed']}")
        print(f"  Errors: {self.stats['errors']}")
        print("=" * 50)


def main():
    """Run the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator (Silver Tier)')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=60, help='Check interval (seconds)')
    
    args = parser.parse_args()
    
    orchestrator = Orchestrator(args.vault)
    
    if args.once:
        orchestrator.run_cycle()
    else:
        import time
        print(f"Running continuous orchestration (interval: {args.interval}s)")
        while True:
            orchestrator.run_cycle()
            time.sleep(args.interval)


if __name__ == '__main__':
    main()
