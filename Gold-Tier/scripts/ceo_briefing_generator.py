"""
CEO Briefing Generator for AI Employee - Gold Tier

Generates weekly business briefings every Monday at 8 AM.
Analyzes tasks, revenue, and bottlenecks to provide executive summary.

Features:
- Revenue tracking from Odoo invoices
- Task completion analysis
- Bottleneck identification
- Proactive suggestions
- Cost optimization recommendations
- Upcoming deadlines

Usage:
    python scripts/ceo_briefing_generator.py --vault AI_Employee_Vault --output Briefings
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import Odoo MCP server
try:
    from odoo_mcp_server import OdooAccountingMCP
    ODOO_AVAILABLE = True
except:
    ODOO_AVAILABLE = False
    print("⚠️  Odoo MCP not available - will use vault data only")


class CEOBriefingGenerator:
    """Generates weekly CEO briefings."""
    
    def __init__(self, vault_path: str, output_path: str = None):
        """
        Initialize briefing generator.
        
        Args:
            vault_path: Path to Obsidian vault
            output_path: Path to store briefings (default: vault/Briefings)
        """
        self.vault = Path(vault_path)
        self.output_path = Path(output_path) if output_path else self.vault / 'Briefings'
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Folders
        self.done_folder = self.vault / 'Done'
        self.plans_folder = self.vault / 'Plans'
        self.logs_folder = self.vault / 'Logs'
        
        # Initialize Odoo if available
        if ODOO_AVAILABLE:
            try:
                self.odoo = OdooAccountingMCP({
                    'url': 'http://localhost:8069',
                    'db': 'odoo',
                    'username': 'admin123@example.com',
                    'password': 'admin'
                })
                self.odoo.client.authenticate()
                print("✅ Odoo connected for revenue tracking")
            except:
                self.odoo = None
                print("⚠️  Odoo not connected - revenue data from vault only")
        else:
            self.odoo = None
    
    def generate_briefing(self, days: int = 7) -> str:
        """
        Generate weekly CEO briefing.
        
        Args:
            days: Number of days to analyze (default: 7 for weekly)
            
        Returns:
            Briefing markdown content
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Gather data
        completed_tasks = self._analyze_completed_tasks(start_date, end_date)
        revenue_data = self._analyze_revenue(start_date, end_date)
        bottlenecks = self._identify_bottlenecks(start_date, end_date)
        suggestions = self._generate_suggestions(completed_tasks, revenue_data)
        
        # Generate briefing
        briefing = self._create_briefing_content(
            start_date=start_date,
            end_date=end_date,
            completed_tasks=completed_tasks,
            revenue_data=revenue_data,
            bottlenecks=bottlenecks,
            suggestions=suggestions
        )
        
        return briefing
    
    def _analyze_completed_tasks(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze completed tasks in date range."""
        tasks = {
            'total': 0,
            'emails': 0,
            'invoices': 0,
            'payments': 0,
            'other': 0,
            'files': []
        }
        
        if not self.done_folder.exists():
            return tasks
        
        # Scan Done folder for completed tasks
        for file in self.done_folder.glob('*.md'):
            try:
                # Check file date
                file_date = datetime.fromtimestamp(file.stat().st_mtime)
                if start_date <= file_date <= end_date:
                    tasks['total'] += 1
                    tasks['files'].append({
                        'name': file.name,
                        'date': file_date.strftime('%Y-%m-%d'),
                        'path': str(file)
                    })
                    
                    # Categorize by type
                    content = file.read_text(encoding='utf-8').lower()
                    if 'email' in content:
                        tasks['emails'] += 1
                    if 'invoice' in content:
                        tasks['invoices'] += 1
                    if 'payment' in content:
                        tasks['payments'] += 1
                    if 'email' not in content and 'invoice' not in content and 'payment' not in content:
                        tasks['other'] += 1
            except Exception as e:
                continue
        
        return tasks
    
    def _analyze_revenue(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze revenue in date range."""
        revenue = {
            'total': 0.0,
            'invoices': 0,
            'payments': 0,
            'this_week': 0.0,
            'mtd': 0.0
        }
        
        # Try Odoo first
        if self.odoo:
            try:
                # Get transactions from Odoo
                result = self.odoo.list_transactions(
                    days=days,
                    limit=100
                )
                
                if result.get('success'):
                    for txn in result.get('transactions', []):
                        amount = txn.get('amount', 0)
                        if amount > 0:  # Income
                            revenue['total'] += amount
                            revenue['invoices'] += 1
            except Exception as e:
                print(f"⚠️  Odoo revenue analysis failed: {e}")
        
        # Fallback: Scan vault for invoice data
        if revenue['total'] == 0 and self.done_folder.exists():
            for file in self.done_folder.glob('*.md'):
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    # Look for dollar amounts in invoice-related files
                    if 'invoice' in content.lower():
                        # Simple extraction of dollar amounts
                        import re
                        amounts = re.findall(r'\$(\d+(?:\.\d+)?)', content)
                        for amount in amounts:
                            revenue['total'] += float(amount)
                            revenue['invoices'] += 1
                except:
                    continue
        
        # Calculate MTD (Month to Date)
        today = datetime.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if start_date <= month_start <= end_date:
            revenue['mtd'] = revenue['total']
        else:
            # Scan current month files
            for file in self.done_folder.glob('*.md'):
                file_date = datetime.fromtimestamp(file.stat().st_mtime)
                if file_date >= month_start:
                    try:
                        content = file.read_text(encoding='utf-8')
                        import re
                        amounts = re.findall(r'\$(\d+(?:\.\d+)?)', content)
                        for amount in amounts:
                            revenue['mtd'] += float(amount)
                    except:
                        continue
        
        # This week's revenue
        revenue['this_week'] = revenue['total']
        
        return revenue
    
    def _identify_bottlenecks(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Identify bottlenecks and delays."""
        bottlenecks = []
        
        # Scan Plans folder for overdue tasks
        if self.plans_folder.exists():
            for file in self.plans_folder.glob('*.md'):
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    # Look for deadline indicators
                    if 'deadline' in content.lower() or 'overdue' in content.lower():
                        bottlenecks.append({
                            'task': file.name,
                            'issue': 'Potential deadline concern',
                            'severity': 'medium'
                        })
                except:
                    continue
        
        # Check for tasks stuck in In_Progress
        in_progress_folder = self.vault / 'In_Progress' / 'qwen_agent'
        if in_progress_folder.exists():
            stuck_count = len(list(in_progress_folder.glob('*.md')))
            if stuck_count > 10:
                bottlenecks.append({
                    'task': 'Multiple tasks in progress',
                    'issue': f'{stuck_count} tasks stuck in progress',
                    'severity': 'high'
                })
        
        return bottlenecks
    
    def _generate_suggestions(
        self,
        completed_tasks: Dict[str, Any],
        revenue_data: Dict[str, Any]
    ) -> List[str]:
        """Generate proactive suggestions."""
        suggestions = []
        
        # Revenue-based suggestions
        if revenue_data['total'] == 0:
            suggestions.append("💰 **Revenue Alert**: No invoices recorded this week. Consider following up on pending proposals.")
        elif revenue_data['total'] < 1000:
            suggestions.append("📈 **Growth Opportunity**: Revenue is below $1,000 this week. Focus on closing pending deals.")
        
        # Task-based suggestions
        if completed_tasks['total'] == 0:
            suggestions.append("⚠️ **Productivity Alert**: No tasks completed this week. Review workload and priorities.")
        
        if completed_tasks['emails'] > 10:
            suggestions.append("📧 **Email Volume**: High email activity detected. Consider email templates for common responses.")
        
        # Generic suggestions
        suggestions.append("📅 **Weekly Review**: Schedule time to review pending approvals and clear inbox.")
        
        return suggestions
    
    def _create_briefing_content(
        self,
        start_date: datetime,
        end_date: datetime,
        completed_tasks: Dict[str, Any],
        revenue_data: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        suggestions: List[str]
    ) -> str:
        """Create briefing markdown content."""
        # Generate executive summary
        if revenue_data['total'] > 0 and completed_tasks['total'] > 0:
            summary = "Strong week with revenue generation and task completion."
        elif revenue_data['total'] > 0:
            summary = "Revenue generated this week. Task completion needs improvement."
        elif completed_tasks['total'] > 0:
            summary = "Good task completion. Focus on revenue generation next week."
        else:
            summary = "Quiet week. Review pipeline and priorities for improvement."
        
        # Add bottleneck warning if any
        if bottlenecks:
            summary += f" {len(bottlenecks)} bottleneck(s) identified."
        
        briefing = f"""---
generated: {datetime.now().isoformat()}
period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
type: weekly_ceo_briefing
---

# Monday Morning CEO Briefing

## Executive Summary
{summary}

---

## 📊 Revenue

| Metric | Amount |
|--------|--------|
| **This Week** | ${revenue_data['this_week']:,.2f} |
| **MTD (Month to Date)** | ${revenue_data['mtd']:,.2f} |
| **Total Invoices** | {revenue_data['invoices']} |

---

## ✅ Completed Tasks

**Total:** {completed_tasks['total']} tasks completed

| Category | Count |
|----------|-------|
| Emails Processed | {completed_tasks['emails']} |
| Invoices Created | {completed_tasks['invoices']} |
| Payments Recorded | {completed_tasks['payments']} |
| Other Tasks | {completed_tasks['other']} |

---

## ⚠️ Bottlenecks

"""
        
        if bottlenecks:
            briefing += "| Task | Issue | Severity |\n"
            briefing += "|------|-------|----------|\n"
            for bottleneck in bottlenecks:
                briefing += f"| {bottleneck.get('task', 'Unknown')} | {bottleneck.get('issue', 'Unknown')} | {bottleneck.get('severity', 'medium')} |\n"
        else:
            briefing += "*No bottlenecks identified this week.* ✅\n"
        
        briefing += f"""
---

## 💡 Proactive Suggestions

"""
        
        for suggestion in suggestions:
            briefing += f"{suggestion}\n\n"
        
        briefing += f"""---

## 📅 Upcoming Deadlines

*Review calendar for upcoming deadlines and schedule accordingly.*

---

## 📈 Weekly Trend

| Week | Revenue | Tasks |
|------|---------|-------|
| This Week | ${revenue_data['this_week']:,.2f} | {completed_tasks['total']} |
| Last Week | - | - |

---

*Generated by AI Employee v1.0 | Gold Tier | {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        return briefing
    
    def save_briefing(self, briefing: str) -> Path:
        """
        Save briefing to file.
        
        Args:
            briefing: Briefing markdown content
            
        Returns:
            Path to saved file
        """
        # Generate filename with date
        filename = f"{datetime.now().strftime('%Y-%m-%d')}_CEO_Briefing.md"
        filepath = self.output_path / filename
        
        # Save file
        filepath.write_text(briefing, encoding='utf-8')
        
        print(f"✅ Briefing saved to: {filepath}")
        
        return filepath


def main():
    """Generate CEO briefing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CEO Briefing Generator')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--output', help='Output folder for briefings')
    parser.add_argument('--days', type=int, default=7, help='Days to analyze (default: 7)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CEO BRIEFING GENERATOR")
    print("=" * 60)
    print()
    
    # Initialize generator
    generator = CEOBriefingGenerator(args.vault, args.output)
    
    # Generate briefing
    print(f"Generating briefing for last {args.days} days...")
    briefing = generator.generate_briefing(days=args.days)
    
    # Save briefing
    filepath = generator.save_briefing(briefing)
    
    print()
    print("=" * 60)
    print("BRIEFING GENERATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"File: {filepath}")
    print()
    print("Next steps:")
    print("1. Review the briefing in Obsidian")
    print("2. Share with stakeholders")
    print("3. Take action on suggestions")
    print()


if __name__ == '__main__':
    main()
