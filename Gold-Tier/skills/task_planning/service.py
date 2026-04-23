"""
Task Planning Service - Core Business Logic

Generates detailed action plans for complex tasks.
Supports AI-powered generation (via Qwen CLI) with template fallback.

No agent-related code — pure business logic only.
"""

import json
import shutil
import subprocess
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add scripts/ to path for AI integration
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from claude_ai_integration import call_ai_model, call_claude, ai_generate_plan

logger = logging.getLogger(__name__)


class PlanningService:
    """Core planning service — generates plans, updates, archives."""

    PLAN_TEMPLATES = {
        "email": "_email_plan",
        "email_reply": "_email_reply_plan",
        "payment": "_payment_plan",
        "file_drop": "_file_plan",
        "social_media": "_social_plan",
        "default": "_default_plan",
    }

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.plans_folder = self.vault / "Plans"
        self.logs = self.vault / "Logs"
        for d in [self.plans_folder, self.logs]:
            d.mkdir(parents=True, exist_ok=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, subprocess.TimeoutExpired)),
        reraise=True
    )
    def generate_plan(self, task_type: str, task_data: Dict[str, Any],
                      task_content: str) -> Dict[str, Any]:
        """
        Generate a plan using Qwen AI with template fallback.

        Args:
            task_type: Type of task
            task_data: Task metadata dict
            task_content: Full task file content

        Returns:
            Dict with plan_content, method, analysis, success
        """
        # Try Claude AI first
        ai_result = ai_generate_plan(task_type, task_data, task_content)
        if ai_result:
            return {
                "success": True,
                "plan_content": ai_result,
                "method": "claude_ai",
                "analysis": {}
            }

        # Fallback to template
        plan_content = self._get_template(task_type, task_data)
        return {
            "success": True,
            "plan_content": plan_content,
            "method": "template",
            "analysis": {}
        }

    def create_plan_file(self, task_type: str, task_data: Dict[str, Any],
                         task_content: str, source_task_name: str = "") -> Dict[str, Any]:
        """
        Generate a plan and write it to Plans/ folder.

        Args:
            task_type: Task type
            task_data: Task metadata
            task_content: Full task content
            source_task_name: Name of source task file (for naming)

        Returns:
            Dict with success, filepath, plan_name, method
        """
        result = self.generate_plan(task_type, task_data, task_content)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_name = f"PLAN_{source_task_name}_{timestamp}.md" if source_task_name else f"PLAN_{task_type}_{timestamp}.md"
        plan_path = self.plans_folder / plan_name

        plan_path.write_text(result["plan_content"], encoding="utf-8")

        self._log_event("plan_created", {
            "task_file": source_task_name,
            "plan_file": plan_name,
            "task_type": task_type,
            "method": result.get("method", "template")
        })

        return {
            "success": True,
            "filepath": str(plan_path),
            "plan_name": plan_name,
            "method": result.get("method", "template")
        }

    def update_plan(self, plan_path_str: str, step_number: int,
                    step_status: str, notes: str = "") -> Dict[str, Any]:
        """Update a plan with step completion status."""
        plan_path = Path(plan_path_str)
        if not plan_path.exists():
            return {"success": False, "error": f"Plan not found: {plan_path_str}"}

        content = plan_path.read_text(encoding="utf-8")
        old_step = f"{step_number}. [ ]"
        new_step = f"{step_number}. [x]" if step_status == "completed" else f"{step_number}. [-]"
        content = content.replace(old_step, new_step, 1)

        if notes:
            notes_section = "\n## Execution Notes\n"
            if notes_section in content:
                content = content.replace(
                    notes_section,
                    f"{notes_section}\n- [{datetime.now().strftime('%H:%M:%S')}] {notes}\n"
                )
            else:
                content += f"\n## Execution Notes\n- [{datetime.now().strftime('%H:%M:%S')}] {notes}\n"

        plan_path.write_text(content, encoding="utf-8")
        return {"success": True, "action": "updated"}

    def complete_plan(self, plan_path_str: str, summary: str = "") -> Dict[str, Any]:
        """Mark a plan as complete and move to Done/."""
        plan_path = Path(plan_path_str)
        if not plan_path.exists():
            return {"success": False, "error": f"Plan not found: {plan_path_str}"}

        content = plan_path.read_text(encoding="utf-8")
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
*AI Employee Plan Generator*
"""
        content += completion_block

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = plan_path.stem + "_completed_" + timestamp + plan_path.suffix
        dest_path = self.vault / "Done" / new_name
        dest_path.write_text(content, encoding="utf-8")
        plan_path.unlink()

        self._log_event("plan_completed", {
            "plan_file": plan_path.name,
            "destination": new_name
        })

        return {"success": True, "action": "completed", "destination": str(dest_path)}

    # ─── AI Generation ────────────────────────────────────────────

    def _try_ai_generation(self, task_type: str, task_data: Dict,
                           content: str) -> Optional[Dict[str, Any]]:
        """Try Claude AI plan generation."""
        handbook = self._read_file(self.vault / "Company_Handbook.md", 2000)
        goals = self._read_file(self.vault / "Business_Goals.md", 1500)

        prompt = self._build_ai_prompt(task_type, task_data, content, handbook, goals)

        qwen_path = shutil.which("qwen")
        if not qwen_path:
            return None

        try:
            result = subprocess.run(
                [qwen_path],
                input=prompt,
                capture_output=True, text=True, timeout=90,
                encoding="utf-8", errors="replace"
            )
            if result.returncode == 0 and result.stdout and len(result.stdout.strip()) > 200:
                analysis, plan_content = self._parse_ai_plan(result.stdout.strip())
                if analysis or len(plan_content) > 300:
                    return {
                        "success": True,
                        "plan_content": plan_content,
                        "analysis": analysis,
                        "method": "qwen_code_ai"
                    }
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.warning(f"AI plan generation failed: {e}")

        return None

    def _build_ai_prompt(self, task_type: str, task_data: Dict, content: str,
                         handbook: str, goals: str) -> str:
        """Build AI prompt for plan generation."""
        return f"""You are an expert AI Employee project planner. Analyze a task and create a detailed plan.

## CONTEXT
### Company Handbook:
{handbook or "No handbook available"}

### Business Goals:
{goals or "No business goals available"}

## TASK TO ANALYZE
Type: {task_type}
Priority: {task_data.get('priority', 'normal')}
From: {task_data.get('from', 'Unknown')}
Subject: {task_data.get('subject', 'N/A')}

Full Content:
---
{content[:2000]}
---

## OUTPUT FORMAT

ANALYSIS:
- Intent: [detailed intent]
- Business Value: [revenue/partnership/support/other]
- Urgency: [Low/Medium/High/Critical]
- Complexity: [Simple/Medium/Complex]
- Stakeholders: [who needs to be involved]
- Risks: [potential risks and mitigation]

PLAN:
# Task Plan: [Custom Title]

## Executive Summary
[2-3 sentence summary]

## Priority Level
[CRITICAL/HIGH/MEDIUM/LOW]

## Steps
1. [ ] [Specific action step] (Estimated: [time])
2. [ ] [Specific action step] (Estimated: [time])
[Add more steps]

## Risks & Dependencies
- ⚠️ [Risk]: [mitigation]

## Stakeholders
- [Role]: [why involved]

## Estimated Timeline
- Total: [X hours/days]

## Notes for Execution
[Any context/tips]

Generate your complete analysis and plan now:
"""

    def _parse_ai_plan(self, ai_output: str) -> Tuple[Dict[str, str], str]:
        """Parse AI output into analysis and plan content."""
        analysis = {}
        plan_content = ai_output

        if "ANALYSIS:" in ai_output:
            parts = ai_output.split("ANALYSIS:")
            if len(parts) > 1:
                analysis_section = parts[1].split("PLAN:")[0] if "PLAN:" in parts[1] else parts[1]
                for line in analysis_section.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        analysis[key.strip().lower()] = value.strip()

        if "PLAN:" in ai_output:
            plan_content = ai_output.split("PLAN:")[1].strip()

        return analysis, plan_content

    # ─── Templates ────────────────────────────────────────────────

    def _get_template(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """Get the appropriate template for a task type."""
        template_name = self.PLAN_TEMPLATES.get(task_type, "_default_plan")
        template_func = getattr(self, template_name)
        return template_func(task_data)

    def _email_plan(self, td: Dict[str, Any]) -> str:
        ts = datetime.now().isoformat()
        return f"""---
created: {ts}
status: in_progress
task_type: email
objective: Process email and determine response
---

# Task Plan: Email Processing

## Objective
Process incoming email and determine appropriate response.

## Context
- **From:** {td.get('from', 'Unknown')}
- **Subject:** {td.get('subject', 'No Subject')}
- **Priority:** {td.get('priority', 'normal')}
- **Urgent:** {td.get('is_urgent', False)}

## Steps
1. [ ] Read full email content
2. [ ] Check Company Handbook for response rules
3. [ ] Determine if reply is needed
4. [ ] If reply needed: Draft response → Create approval → Send after approval
5. [ ] Archive email

---
*AI Employee Plan Generator*
"""

    def _email_reply_plan(self, td: Dict[str, Any]) -> str:
        ts = datetime.now().isoformat()
        return f"""---
created: {ts}
status: in_progress
task_type: email_reply
objective: Draft and send email reply
---

# Task Plan: Email Reply

## Objective
Draft and send reply to email.

## Context
- **To:** {td.get('to', 'Unknown')}
- **Subject:** {td.get('subject', 'No Subject')}
- **Requires Approval:** Yes

## Steps
1. [ ] Read original email
2. [ ] Check if sender is approved contact
3. [ ] Draft reply
4. [ ] Create approval request
5. [ ] Wait for human approval
6. [ ] Send email
7. [ ] Move to Done

---
*AI Employee Plan Generator*
"""

    def _payment_plan(self, td: Dict[str, Any]) -> str:
        ts = datetime.now().isoformat()
        return f"""---
created: {ts}
status: pending_approval
task_type: payment
objective: Process payment request
---

# Task Plan: Payment Processing

## Context
- **Amount:** {td.get('amount', 'Unknown')}
- **Recipient:** {td.get('recipient', 'Unknown')}
- **Requires Approval:** YES

## Steps
1. [ ] Verify payment details
2. [ ] Create approval request
3. [ ] Wait for human approval
4. [ ] Execute payment after approval
5. [ ] Log transaction
6. [ ] Move to Done

---
*AI Employee Plan Generator*
"""

    def _file_plan(self, td: Dict[str, Any]) -> str:
        ts = datetime.now().isoformat()
        return f"""---
created: {ts}
status: in_progress
task_type: file_drop
objective: Process and categorize file
---

# Task Plan: File Processing

## Context
- **Original File:** {td.get('original_name', 'Unknown')}
- **Extension:** {td.get('extension', 'Unknown')}

## Steps
1. [ ] Read file content
2. [ ] Categorize file
3. [ ] Add metadata
4. [ ] Move to appropriate folder
5. [ ] Update Dashboard

---
*AI Employee Plan Generator*
"""

    def _social_plan(self, td: Dict[str, Any]) -> str:
        ts = datetime.now().isoformat()
        return f"""---
created: {ts}
status: pending_approval
task_type: social_media
objective: Post to social media
---

# Task Plan: Social Media Post

## Context
- **Platform:** {td.get('platform', 'Unknown')}
- **Requires Approval:** YES

## Steps
1. [ ] Review post content
2. [ ] Create approval request
3. [ ] Wait for human approval
4. [ ] Post via platform API
5. [ ] Capture confirmation
6. [ ] Move to Done

---
*AI Employee Plan Generator*
"""

    def _default_plan(self, td: Dict[str, Any]) -> str:
        ts = datetime.now().isoformat()
        return f"""---
created: {ts}
status: in_progress
task_type: {td.get('type', 'unknown')}
objective: Process task
---

# Task Plan

## Context
- **Type:** {td.get('type', 'unknown')}
- **Priority:** {td.get('priority', 'normal')}

## Steps
1. [ ] Read task content
2. [ ] Check Company Handbook for rules
3. [ ] Execute task or create approval request
4. [ ] Move to Done when complete

---
*AI Employee Plan Generator*
"""

    # ─── Helpers ──────────────────────────────────────────────────

    def _read_file(self, path: Path, max_chars: int = 0) -> str:
        """Read a file with optional char limit."""
        try:
            content = path.read_text(encoding="utf-8")
            return content[:max_chars] if max_chars else content
        except Exception:
            return ""

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log event to daily log."""
        entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type, **details}
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
