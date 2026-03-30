"""
Plan Generator for AI Employee - Silver Tier

Creates detailed Plan.md files for complex multi-step tasks.
Uses Qwen Code AI to generate intelligent, contextual plans.
Tracks progress and updates plans with completion status.

Usage:
    python scripts/plan_generator.py --vault AI_Employee_Vault --task <task_file>
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Try to import Qwen AI integration
try:
    from qwen_ai_integration import generate_ai_response
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False


class PlanGenerator:
    """Generates and manages task plans."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.plans_folder = self.vault / 'Plans'
        self.logs = self.vault / 'Logs'

        # Ensure folders exist
        self.plans_folder.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

        # Plan templates for different task types
        self.plan_templates = {
            'email': self._email_plan_template,
            'email_reply': self._email_reply_plan_template,
            'payment': self._payment_plan_template,
            'file_drop': self._file_plan_template,
            'social_media': self._social_plan_template,
            'default': self._default_plan_template
        }

    def generate_ai_plan(self, task_file: Path, task_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """
        Generate AI-powered plan using Qwen Code.
        
        Args:
            task_file: Path to task file
            task_data: Task metadata
            content: Full task file content
            
        Returns:
            Dictionary with AI-generated plan or fallback template
        """
        
        # Read Company Handbook and Business Goals for context
        handbook_path = self.vault / 'Company_Handbook.md'
        goals_path = self.vault / 'Business_Goals.md'
        
        handbook = handbook_path.read_text(encoding='utf-8') if handbook_path.exists() else ""
        goals = goals_path.read_text(encoding='utf-8') if goals_path.exists() else ""
        
        # Build AI prompt for plan generation
        prompt = f"""You are an expert AI Employee project planner. Your task is to analyze a task and create a detailed, actionable plan.

## CONTEXT

### Company Handbook:
{handbook[:2000] if handbook else "No handbook available"}

### Business Goals:
{goals[:1500] if goals else "No business goals available"}

## TASK TO ANALYZE

Type: {task_data.get('type', 'unknown')}
Priority: {task_data.get('priority', 'normal')}
From: {task_data.get('from', 'Unknown')}
Subject: {task_data.get('subject', 'N/A')}

Full Content:
---
{content[:2000]}
---

## YOUR TASK

Analyze this task and create a detailed plan following these steps:

### Step 1: Deep Analysis
1. **Intent**: What is the sender trying to achieve?
2. **Business Value**: What's the potential business impact? (revenue, partnership, support, etc.)
3. **Urgency**: How time-sensitive is this? (Look for: urgent, asap, deadline, by Monday, etc.)
4. **Complexity**: How complex is this task? (simple reply, requires legal review, needs CEO approval, etc.)
5. **Stakeholders**: Who needs to be involved? (legal, CEO, sales, support, etc.)
6. **Risks**: What could go wrong? (time-sensitive, legal implications, high-value client, etc.)

### Step 2: Create Action Plan
Create a numbered list of specific, actionable steps with:
- Clear action verbs
- Estimated time for each step
- Dependencies (if any)
- Responsible party (if applicable)

### Step 3: Output Format

Provide your plan in this EXACT format:

ANALYSIS:
- Intent: [detailed intent]
- Business Value: [revenue/partnership/support/other]
- Urgency: [Low/Medium/High/Critical]
- Complexity: [Simple/Medium/Complex]
- Stakeholders: [who needs to be involved]
- Risks: [potential risks and mitigation]

PLAN:
# Task Plan: [Custom Title Based on Content]

## Executive Summary
[2-3 sentence summary of what this task is about and why it matters]

## Priority Level
[CRITICAL/HIGH/MEDIUM/LOW] - with justification

## Steps
1. [ ] [Specific action step] (Estimated: [time])
2. [ ] [Specific action step] (Estimated: [time])
3. [ ] [Specific action step] (Estimated: [time])
[Add more steps as needed - be comprehensive]

## Risks & Dependencies
- ⚠️ [Risk 1]: [mitigation strategy]
- 📋 [Dependency 1]: [what it depends on]

## Stakeholders
- [Role/Department]: [why they're involved]

## Estimated Timeline
- Total Estimated Time: [X hours/days]
- Deadline: [if mentioned in email, otherwise "None specified"]
- Recommended Completion: [your recommendation]

## Notes for Execution
[Any additional context, tips, or important information]

## IMPORTANT RULES

1. **Be Specific**: Reference actual details from the email (names, companies, dates, amounts)
2. **Be Realistic**: Estimate time accurately, don't underestimate
3. **Identify Risks Early**: Flag potential issues before they become problems
4. **Consider Business Impact**: Align with company goals and handbook rules
5. **Actionable Steps**: Each step should be clear and executable
6. **No Questions**: Don't ask for clarification - make reasonable assumptions and proceed

Generate your complete analysis and plan now:
"""

        try:
            print("    [AI] Calling Qwen Code for intelligent plan generation...")
            
            import shutil
            qwen_path = shutil.which('qwen')
            
            if not qwen_path:
                print("    [AI] ⚠️  Qwen Code not found - using template")
                return {'success': False, 'method': 'template'}
            
            # Call Qwen Code
            result = subprocess.run(
                [qwen_path],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=90,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                print("    [AI] ❌ Qwen Error:", result.stderr[:500] if result.stderr else "Unknown error")
                return {'success': False, 'method': 'template'}
            
            if result.returncode == 0 and result.stdout:
                ai_plan = result.stdout.strip()
                
                # Check if Qwen generated useful content (more flexible validation)
                if len(ai_plan) < 200:
                    print("    [AI] ⚠️  Qwen output too short - using template")
                    return {'success': False, 'method': 'template'}
                
                # Parse AI plan (more flexible - accepts various formats)
                analysis, plan_content = self._parse_ai_plan(ai_plan)
                
                # If we got any analysis, consider it successful
                if analysis or len(plan_content) > 300:
                    print("    [AI] ✅ AI-generated intelligent plan")
                    return {
                        'success': True,
                        'plan_content': plan_content,
                        'analysis': analysis,
                        'method': 'qwen_code_ai'
                    }
                else:
                    print("    [AI] ⚠️  Qwen output invalid - using template")
                    return {'success': False, 'method': 'template'}
            else:
                return {'success': False, 'method': 'template'}
                
        except subprocess.TimeoutExpired:
            print("    [AI] ⚠️  Qwen Code timeout - using template")
            return {'success': False, 'method': 'template'}
        except Exception as e:
            print(f"    [AI] ⚠️  Error: {e} - using template")
            return {'success': False, 'method': 'template'}
    
    def _parse_ai_plan(self, ai_output: str) -> tuple:
        """Parse AI output into analysis and plan content."""
        
        analysis = {}
        plan_content = ai_output
        
        # Try to extract ANALYSIS section
        if 'ANALYSIS:' in ai_output:
            parts = ai_output.split('ANALYSIS:')
            if len(parts) > 1:
                analysis_section = parts[1].split('PLAN:')[0] if 'PLAN:' in parts[1] else parts[1]
                
                # Parse analysis fields
                for line in analysis_section.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        analysis[key.strip().lower()] = value.strip()
        
        # Extract PLAN section
        if 'PLAN:' in ai_output:
            plan_content = ai_output.split('PLAN:')[1].strip()
        
        return analysis, plan_content
    
    def create_plan(self, task_file: Path, task_data: Dict[str, Any]) -> Path:
        """
        Create a plan for a task using AI (with template fallback).

        Args:
            task_file: Path to the task file
            task_data: Parsed task metadata

        Returns:
            Path to created plan file
        """
        task_type = task_data.get('type', 'default')
        content = task_file.read_text(encoding='utf-8')

        # Try AI-powered plan generation first
        if AI_AVAILABLE:
            print(f"  Creating AI-powered plan...")
            ai_result = self.generate_ai_plan(task_file, task_data, content)
            
            if ai_result.get('success'):
                # Use AI-generated plan
                plan_content = ai_result['plan_content']
                print(f"    [AI] Analysis: {ai_result.get('analysis', {}).get('urgency', 'Normal')} priority")
            else:
                # Fallback to template
                print(f"  Creating template plan...")
                template_func = self.plan_templates.get(task_type, self._default_plan_template)
                plan_content = template_func(task_file, task_data)
        else:
            # AI not available, use template
            print(f"  Creating template plan...")
            template_func = self.plan_templates.get(task_type, self._default_plan_template)
            plan_content = template_func(task_file, task_data)

        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plan_name = f"PLAN_{task_file.stem}_{timestamp}.md"
        plan_path = self.plans_folder / plan_name

        # Write plan
        plan_path.write_text(plan_content, encoding='utf-8')

        self._log_event('plan_created', {
            'task_file': task_file.name,
            'plan_file': plan_name,
            'task_type': task_type,
            'method': ai_result.get('method', 'template') if AI_AVAILABLE else 'template'
        })

        print(f"  Created plan: {plan_name}")
        return plan_path
    
    def update_plan(self, plan_path: Path, step_number: int, 
                    step_status: str, notes: str = "") -> None:
        """
        Update a plan with step completion status.
        
        Args:
            plan_path: Path to plan file
            step_number: Step number to update
            step_status: Status (completed, failed, skipped)
            notes: Optional notes
        """
        content = plan_path.read_text(encoding='utf-8')
        
        # Update step checkbox
        old_step = f"{step_number}. [ ]"
        new_step = f"{step_number}. [x]" if step_status == 'completed' else f"{step_number}. [-]"
        
        content = content.replace(old_step, new_step, 1)
        
        # Add note if provided
        if notes:
            notes_section = "\n## Execution Notes\n"
            if notes_section in content:
                content = content.replace(
                    notes_section,
                    f"{notes_section}\n- [{datetime.now().strftime('%H:%M:%S')}] {notes}\n"
                )
            else:
                content += f"\n## Execution Notes\n- [{notes}]\n"
        
        plan_path.write_text(content, encoding='utf-8')
    
    def complete_plan(self, plan_path: Path, summary: str = "") -> Path:
        """
        Mark a plan as complete and move to Done.
        
        Args:
            plan_path: Path to plan file
            summary: Completion summary
            
        Returns:
            Path to archived plan
        """
        content = plan_path.read_text(encoding='utf-8')
        
        # Add completion metadata
        completion_block = f"""
---
completed: {datetime.now().isoformat()}
status: completed
---

## Completion Summary

**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** ✓ Complete

{summary}

---
*AI Employee Plan Generator v0.1.0*
"""
        content += completion_block
        
        # Move to Done
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = plan_path.stem + '_completed_' + timestamp + plan_path.suffix
        dest_path = self.vault / 'Done' / new_name
        dest_path.write_text(content, encoding='utf-8')
        
        # Delete original
        plan_path.unlink()
        
        self._log_event('plan_completed', {
            'plan_file': plan_path.name,
            'destination': new_name
        })
        
        return dest_path
    
    def _email_plan_template(self, task_file: Path, task_data: Dict) -> str:
        """Email task plan template."""
        return f"""---
created: {datetime.now().isoformat()}
status: in_progress
task_file: {task_file.name}
task_type: email
objective: Process email and determine response
estimated_steps: 4
---

# Task Plan: Email Processing

## Objective
Process incoming email and determine appropriate response.

## Context
- **From:** {task_data.get('from', 'Unknown')}
- **Subject:** {task_data.get('subject', 'No Subject')}
- **Priority:** {task_data.get('priority', 'normal')}
- **Urgent:** {task_data.get('is_urgent', False)}

## Steps
1. [ ] Read full email content
2. [ ] Check Company Handbook for response rules
3. [ ] Determine if reply is needed
4. [ ] If reply needed:
    - Draft response
    - Create approval request
    - Send after approval
5. [ ] Archive email

## Execution Notes

## Completion Summary

"""
    
    def _email_reply_plan_template(self, task_file: Path, task_data: Dict) -> str:
        """Email reply plan template."""
        return f"""---
created: {datetime.now().isoformat()}
status: in_progress
task_file: {task_file.name}
task_type: email_reply
objective: Draft and send email reply
estimated_steps: 5
---

# Task Plan: Email Reply

## Objective
Draft and send reply to email.

## Context
- **To:** {task_data.get('to', 'Unknown')}
- **Subject:** {task_data.get('subject', 'No Subject')}
- **Requires Approval:** Yes

## Steps
1. [ ] Read original email
2. [ ] Check if sender is approved contact
3. [ ] Draft reply
4. [ ] Create approval request in /Pending_Approval/
5. [ ] Wait for human approval
6. [ ] Send email via Email Sender
7. [ ] Move to /Done/

## Execution Notes

## Completion Summary

"""
    
    def _payment_plan_template(self, task_file: Path, task_data: Dict) -> str:
        """Payment task plan template."""
        return f"""---
created: {datetime.now().isoformat()}
status: pending_approval
task_file: {task_file.name}
task_type: payment
objective: Process payment request
estimated_steps: 4
---

# Task Plan: Payment Processing

## Objective
Process payment request with human approval.

## Context
- **Amount:** {task_data.get('amount', 'Unknown')}
- **Recipient:** {task_data.get('recipient', 'Unknown')}
- **Requires Approval:** YES (Financial transaction)

## Steps
1. [ ] Verify payment details
2. [ ] Create approval request in /Pending_Approval/
3. [ ] Wait for human approval
4. [ ] Execute payment after approval
5. [ ] Log transaction
6. [ ] Move to /Done/

## Execution Notes

## Completion Summary

"""
    
    def _file_plan_template(self, task_file: Path, task_data: Dict) -> str:
        """File drop plan template."""
        return f"""---
created: {datetime.now().isoformat()}
status: in_progress
task_file: {task_file.name}
task_type: file_drop
objective: Process and categorize file
estimated_steps: 3
---

# Task Plan: File Processing

## Objective
Process dropped file and categorize appropriately.

## Context
- **Original File:** {task_data.get('original_name', 'Unknown')}
- **Size:** {task_data.get('size_human', 'Unknown')}
- **Extension:** {task_data.get('extension', 'Unknown')}

## Steps
1. [ ] Read file content
2. [ ] Categorize file (Finance, Legal, General, etc.)
3. [ ] Add categorization metadata
4. [ ] Move to appropriate folder
5. [ ] Update Dashboard

## Execution Notes

## Completion Summary

"""
    
    def _social_plan_template(self, task_file: Path, task_data: Dict) -> str:
        """Social media post plan template."""
        return f"""---
created: {datetime.now().isoformat()}
status: pending_approval
task_file: {task_file.name}
task_type: social_media
objective: Post to social media
estimated_steps: 4
---

# Task Plan: Social Media Post

## Objective
Post content to social media platform.

## Context
- **Platform:** {task_data.get('platform', 'Unknown')}
- **Type:** {task_data.get('post_type', 'Unknown')}
- **Requires Approval:** YES

## Steps
1. [ ] Review post content
2. [ ] Create approval request in /Pending_Approval/
3. [ ] Wait for human approval
4. [ ] Post via LinkedIn Poster
5. [ ] Capture confirmation screenshot
6. [ ] Move to /Done/

## Execution Notes

## Completion Summary

"""
    
    def _default_plan_template(self, task_file: Path, task_data: Dict) -> str:
        """Default plan template."""
        return f"""---
created: {datetime.now().isoformat()}
status: in_progress
task_file: {task_file.name}
task_type: {task_data.get('type', 'unknown')}
objective: Process task
estimated_steps: 3
---

# Task Plan

## Objective
Process this task according to Company Handbook rules.

## Context
- **Type:** {task_data.get('type', 'unknown')}
- **Priority:** {task_data.get('priority', 'normal')}
- **Created:** {task_data.get('created', 'unknown')}

## Steps
1. [ ] Read task content
2. [ ] Check Company Handbook for rules
3. [ ] Execute task or create approval request
4. [ ] Move to /Done/ when complete

## Execution Notes

## Completion Summary

"""
    
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


def main():
    """Run the plan generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Plan Generator')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--task', help='Task file to create plan for')
    
    args = parser.parse_args()
    
    generator = PlanGenerator(args.vault)
    
    if args.task:
        task_path = Path(args.vault) / 'Needs_Action' / args.task
        if task_path.exists():
            content = task_path.read_text()
            # Simple frontmatter parser
            task_data = {}
            in_frontmatter = False
            for line in content.split('\n'):
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    task_data[key.strip()] = value.strip().strip('"\'')
            
            plan_path = generator.create_plan(task_path, task_data)
            print(f"Plan created: {plan_path}")
        else:
            print(f"Task file not found: {task_path}")
    else:
        print("Plan Generator ready. Use --task to create a plan.")


if __name__ == '__main__':
    main()
