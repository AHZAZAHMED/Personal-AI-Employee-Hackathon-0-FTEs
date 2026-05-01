"""
Task Planning Skill - Agent Entry Point

Creates detailed action plans for complex tasks using AI (Qwen CLI)
with template fallback. Manages plan lifecycle: create, update, complete.
"""

from typing import Dict, Any
from .service import PlanningService


def create_task_plan(
    task_type: str,
    task_data: Dict[str, Any],
    task_content: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Create a detailed action plan for a complex task.

    Use this skill when:
    - A task requires multiple steps and needs structured breakdown
    - Before executing complex tasks to establish a clear plan
    - For emails, payments, social media posts, file processing

    The system tries AI generation first (Qwen Code), then falls back
    to a structured template if AI is unavailable.

    Args:
        task_type: Type of task (e.g., 'email', 'email_reply', 'payment',
                   'file_drop', 'social_media', 'default')
        task_data: Task metadata dict (from, subject, priority, is_urgent,
                   amount, recipient, platform, etc.)
        task_content: Full content of the task file (markdown with frontmatter)
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with keys:
        - success (bool): Whether plan was created
        - filepath (str): Path to the created plan file
        - plan_name (str): Name of the plan file
        - method (str): 'qwen_code_ai' or 'template'

    Example:
        result = create_task_plan(
            task_type="email_reply",
            task_data={"from": "client@example.com", "subject": "Inquiry", "priority": "high"},
            task_content="[full email content here]"
        )
    """
    try:
        service = PlanningService(vault_path=vault_path)
        return service.create_plan_file(task_type, task_data, task_content)
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_plan_step(
    plan_filepath: str,
    step_number: int,
    step_status: str = "completed",
    notes: str = ""
) -> Dict[str, Any]:
    """
    Update a plan step's completion status.

    Args:
        plan_filepath: Path to the plan file
        step_number: Step number to update (1-based)
        step_status: 'completed', 'failed', or 'skipped'
        notes: Optional execution notes

    Returns:
        Dict with success status
    """
    try:
        service = PlanningService()
        return service.update_plan(plan_filepath, step_number, step_status, notes)
    except Exception as e:
        return {"success": False, "error": str(e)}


def complete_plan(
    plan_filepath: str,
    summary: str = ""
) -> Dict[str, Any]:
    """
    Mark a plan as complete and archive to Done/.

    Args:
        plan_filepath: Path to the plan file
        summary: Completion summary

    Returns:
        Dict with success status and destination path
    """
    try:
        service = PlanningService()
        return service.complete_plan(plan_filepath, summary)
    except Exception as e:
        return {"success": False, "error": str(e)}
