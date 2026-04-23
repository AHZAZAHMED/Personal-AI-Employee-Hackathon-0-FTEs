"""
CEO Briefing Service - Core Business Logic

Generates weekly business briefings analyzing completed tasks,
revenue, bottlenecks, and providing proactive suggestions.

No agent-related code — pure business logic only.
"""

import json
import re
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Try Odoo
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
try:
    from odoo_mcp_server import OdooAccountingMCP
    ODOO_AVAILABLE = True
except Exception:
    ODOO_AVAILABLE = False

logger = logging.getLogger(__name__)


class CEOBriefingService:
    """Core CEO briefing generation service."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.output_path = self.vault / "Briefings"
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.done_folder = self.vault / "Done"
        self.plans_folder = self.vault / "Plans"
        self.logs_folder = self.vault / "Logs"
        self.in_progress = self.vault / "In_Progress" / "qwen_agent"

        # Odoo connection
        self.odoo = None
        if ODOO_AVAILABLE:
            try:
                self.odoo = OdooAccountingMCP({
                    "url": "http://localhost:8069",
                    "db": "odoo",
                    "username": "admin123@example.com",
                    "password": "admin"
                })
                self.odoo.client.authenticate()
            except Exception:
                self.odoo = None

    def generate_briefing(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate a CEO briefing.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with briefing markdown content and analysis data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        completed_tasks = self._analyze_completed_tasks(start_date, end_date)
        revenue_data = self._analyze_revenue(start_date, end_date)
        bottlenecks = self._identify_bottlenecks()
        suggestions = self._generate_suggestions(completed_tasks, revenue_data)

        briefing_md = self._create_briefing_content(
            start_date, end_date, completed_tasks, revenue_data,
            bottlenecks, suggestions
        )

        return {
            "success": True,
            "content": briefing_md,
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "completed_tasks": completed_tasks,
            "revenue": revenue_data,
            "bottlenecks": bottlenecks,
            "suggestions": suggestions
        }

    def save_briefing(self, briefing_content: str) -> Dict[str, Any]:
        """
        Save briefing to Briefings/ folder.

        Args:
            briefing_content: Markdown content

        Returns:
            Dict with filepath and success status
        """
        filename = f"{datetime.now().strftime('%Y-%m-%d')}_CEO_Briefing.md"
        filepath = self.output_path / filename
        filepath.write_text(briefing_content, encoding="utf-8")
        return {"success": True, "filepath": str(filepath), "filename": filename}

    # ─── Analysis Methods ─────────────────────────────────────────

    def _analyze_completed_tasks(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Analyze completed tasks in date range."""
        tasks = {"total": 0, "emails": 0, "invoices": 0, "payments": 0, "other": 0, "files": []}
        if not self.done_folder.exists():
            return tasks

        for file in self.done_folder.glob("*.md"):
            try:
                file_date = datetime.fromtimestamp(file.stat().st_mtime)
                if start <= file_date <= end:
                    tasks["total"] += 1
                    tasks["files"].append({"name": file.name, "date": file_date.strftime("%Y-%m-%d"), "path": str(file)})
                    content = file.read_text(encoding="utf-8").lower()
                    if "email" in content:
                        tasks["emails"] += 1
                    if "invoice" in content:
                        tasks["invoices"] += 1
                    if "payment" in content:
                        tasks["payments"] += 1
                    if "email" not in content and "invoice" not in content and "payment" not in content:
                        tasks["other"] += 1
            except Exception:
                continue
        return tasks

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def _analyze_revenue(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Analyze revenue in date range."""
        revenue = {"total": 0.0, "invoices": 0, "payments": 0, "this_week": 0.0, "mtd": 0.0}

        # Try Odoo first
        if self.odoo:
            try:
                result = self.odoo.list_transactions(days=7, limit=100)
                if result.get("success"):
                    for txn in result.get("transactions", []):
                        amount = txn.get("amount", 0)
                        if amount > 0:
                            revenue["total"] += amount
                            revenue["invoices"] += 1
            except Exception as e:
                logger.warning(f"Odoo revenue analysis failed: {e}")

        # Fallback: scan Done folder for dollar amounts
        if revenue["total"] == 0 and self.done_folder.exists():
            for file in self.done_folder.glob("*.md"):
                try:
                    content = file.read_text(encoding="utf-8")
                    if "invoice" in content.lower():
                        amounts = re.findall(r"\$(\d+(?:\.\d+)?)", content)
                        for amount in amounts:
                            revenue["total"] += float(amount)
                            revenue["invoices"] += 1
                except Exception:
                    continue

        # MTD
        today = datetime.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start <= month_start <= end:
            revenue["mtd"] = revenue["total"]
        elif self.done_folder.exists():
            for file in self.done_folder.glob("*.md"):
                file_date = datetime.fromtimestamp(file.stat().st_mtime)
                if file_date >= month_start:
                    try:
                        amounts = re.findall(r"\$(\d+(?:\.\d+)?)", file.read_text(encoding="utf-8"))
                        for amount in amounts:
                            revenue["mtd"] += float(amount)
                    except Exception:
                        continue

        revenue["this_week"] = revenue["total"]
        return revenue

    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify bottlenecks and delays."""
        bottlenecks = []

        # Overdue plans
        if self.plans_folder.exists():
            for file in self.plans_folder.glob("*.md"):
                try:
                    content = file.read_text(encoding="utf-8")
                    if "deadline" in content.lower() or "overdue" in content.lower():
                        bottlenecks.append({"task": file.name, "issue": "Potential deadline concern", "severity": "medium"})
                except Exception:
                    continue

        # Stuck tasks
        if self.in_progress.exists():
            stuck_count = len(list(self.in_progress.glob("*.md")))
            if stuck_count > 10:
                bottlenecks.append({"task": "Multiple tasks in progress", "issue": f"{stuck_count} tasks stuck", "severity": "high"})

        return bottlenecks

    def _generate_suggestions(self, tasks: Dict[str, Any], revenue: Dict[str, Any]) -> List[str]:
        """Generate proactive suggestions."""
        suggestions = []

        if revenue["total"] == 0:
            suggestions.append("💰 **Revenue Alert**: No invoices recorded this week. Consider following up on pending proposals.")
        elif revenue["total"] < 1000:
            suggestions.append("📈 **Growth Opportunity**: Revenue is below $1,000 this week. Focus on closing pending deals.")

        if tasks["total"] == 0:
            suggestions.append("⚠️ **Productivity Alert**: No tasks completed this week. Review workload and priorities.")

        if tasks["emails"] > 10:
            suggestions.append("📧 **Email Volume**: High email activity. Consider email templates for common responses.")

        suggestions.append("📅 **Weekly Review**: Schedule time to review pending approvals and clear inbox.")
        return suggestions

    def _create_briefing_content(self, start: datetime, end: datetime,
                                  tasks: Dict[str, Any], revenue: Dict[str, Any],
                                  bottlenecks: List[Dict[str, Any]],
                                  suggestions: List[str]) -> str:
        """Create briefing markdown."""
        if revenue["total"] > 0 and tasks["total"] > 0:
            summary = "Strong week with revenue generation and task completion."
        elif revenue["total"] > 0:
            summary = "Revenue generated this week. Task completion needs improvement."
        elif tasks["total"] > 0:
            summary = "Good task completion. Focus on revenue generation next week."
        else:
            summary = "Quiet week. Review pipeline and priorities for improvement."

        if bottlenecks:
            summary += f" {len(bottlenecks)} bottleneck(s) identified."

        bottlenecks_table = ""
        if bottlenecks:
            bottlenecks_table = "| Task | Issue | Severity |\n|------|-------|----------|\n"
            for b in bottlenecks:
                bottlenecks_table += f"| {b.get('task', 'Unknown')} | {b.get('issue', 'Unknown')} | {b.get('severity', 'medium')} |\n"
        else:
            bottlenecks_table = "*No bottlenecks identified this week.* ✅"

        suggestions_md = "\n".join(f"{s}\n" for s in suggestions)

        return f"""---
generated: {datetime.now().isoformat()}
period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}
type: weekly_ceo_briefing
---

# Monday Morning CEO Briefing

## Executive Summary
{summary}

---

## 📊 Revenue

| Metric | Amount |
|--------|--------|
| **This Week** | ${revenue['this_week']:,.2f} |
| **MTD (Month to Date)** | ${revenue['mtd']:,.2f} |
| **Total Invoices** | {revenue['invoices']} |

---

## ✅ Completed Tasks

**Total:** {tasks['total']} tasks completed

| Category | Count |
|----------|-------|
| Emails Processed | {tasks['emails']} |
| Invoices Created | {tasks['invoices']} |
| Payments Recorded | {tasks['payments']} |
| Other Tasks | {tasks['other']} |

---

## ⚠️ Bottlenecks

{bottlenecks_table}
---

## 💡 Proactive Suggestions

{suggestions_md}
---

## 📅 Upcoming Deadlines

*Review calendar for upcoming deadlines and schedule accordingly.*

---

## 📈 Weekly Trend

| Week | Revenue | Tasks |
|------|---------|-------|
| This Week | ${revenue['this_week']:,.2f} | {tasks['total']} |
| Last Week | - | - |

---

*Generated by AI Employee | Gold Tier | {datetime.now().strftime('%Y-%m-%d')}*
"""
