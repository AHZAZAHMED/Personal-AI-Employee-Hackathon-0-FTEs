"""
CEO Briefing Skill - Agent Entry Point

Generates weekly business briefings with executive summary,
revenue analysis, bottleneck identification, and proactive suggestions.
"""

from typing import Dict, Any
from .service import CEOBriefingService


def generate_ceo_briefing(
    days: int = 7,
    vault_path: str = "AI_Employee_Vault",
    save_to_file: bool = True
) -> Dict[str, Any]:
    """
    Generate a weekly CEO briefing.

    Use this skill when:
    - Creating a weekly executive summary
    - Reviewing business performance
    - Identifying bottlenecks and productivity issues
    - Generating revenue analysis reports

    Analyzes completed tasks from Done/ folder, revenue data
    (from Odoo if available, otherwise from vault), and provides
    proactive suggestions.

    Args:
        days: Number of days to analyze (default: 7 for weekly)
        vault_path: Path to AI Employee Vault
        save_to_file: Whether to save to Briefings/ folder

    Returns:
        Dict with keys:
        - success (bool): Whether briefing was generated
        - content (str): Markdown briefing content
        - period (dict): Date range analyzed
        - completed_tasks (dict): Task analysis
        - revenue (dict): Revenue analysis
        - bottlenecks (list): Identified issues
        - suggestions (list): Proactive suggestions
        - filepath (str|None): Saved file path (if save_to_file=True)
        - error (str|None): Error message if failed

    Example:
        result = generate_ceo_briefing(days=7)
        print(result["content"][:500])
    """
    try:
        service = CEOBriefingService(vault_path=vault_path)
        briefing = service.generate_briefing(days=days)

        filepath = None
        if save_to_file:
            save_result = service.save_briefing(briefing["content"])
            if save_result.get("success"):
                filepath = save_result["filepath"]

        briefing["filepath"] = filepath
        return briefing
    except Exception as e:
        return {"success": False, "error": str(e)}
