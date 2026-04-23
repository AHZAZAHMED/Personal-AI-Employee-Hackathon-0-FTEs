"""
Human Approval Service - Core Business Logic

Manages the human-in-the-loop approval workflow:
- Creates approval requests in Pending_Approval/
- Lists pending, approved, and rejected actions
- Processes approved actions (moves to Done/)
- Archives rejected actions
- Maintains audit trail via logs

No agent-related code — pure business logic only.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ApprovalService:
    """Core approval workflow service."""

    APPROVAL_RULES = {
        "email_reply": "Email replies to contacts require approval",
        "email_send": "Sending emails requires approval",
        "payment": "All payments require human approval",
        "social_post": "Social media posts require approval",
        "invoice": "Invoice-related actions require approval",
    }

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.pending_approval = self.vault / "Pending_Approval"
        self.approved = self.vault / "Approved"
        self.rejected = self.vault / "Rejected"
        self.done = self.vault / "Done"
        self.logs = self.vault / "Logs"

        for d in [self.pending_approval, self.approved, self.rejected,
                  self.done, self.logs]:
            d.mkdir(parents=True, exist_ok=True)

        self.processed_file = self.logs / "processed_approvals.json"
        self.processed_approvals = self._load_processed()

    def _load_processed(self) -> set:
        """Load previously processed approval files."""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, "r") as f:
                    data = json.load(f)
                    return set(data.get("files", []))
            except Exception:
                pass
        return set()

    def _save_processed(self):
        """Save processed approvals to disk."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "files": list(self.processed_approvals)
            }
            with open(self.processed_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed: {e}")

    def create_approval_request(
        self,
        action_type: str,
        details: Dict[str, Any],
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new approval request file.

        Args:
            action_type: Type of action (email_reply, payment, etc.)
            details: Dictionary with action details
            description: Human-readable description

        Returns:
            Dict with success status and filepath
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"APPROVAL_{action_type}_{timestamp}.md"
        filepath = self.pending_approval / filename

        # Build frontmatter
        frontmatter_lines = [
            "---",
            f"type: approval_request",
            f"action: {action_type}",
            f"created: {datetime.now().isoformat()}",
            f"status: pending",
            f"expires: {(datetime.now().replace(hour=23, minute=59)).isoformat()}",
            f"risk_level: {details.get('risk_level', 'medium')}",
        ]

        for key, value in details.items():
            if key != "risk_level":
                if isinstance(value, str):
                    if key == "draft_body" and "\n" in value:
                        frontmatter_lines.append(f"{key}: |")
                        for line in value.split("\n"):
                            frontmatter_lines.append(f"  {line}")
                    else:
                        value = value.replace("\n", " ").replace('"', "'")
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
{self.APPROVAL_RULES.get(action_type, "This action requires human review per Company Handbook.")}

## To Approve
**Move this file to `/Approved` folder.**

## To Reject
**Move this file to `/Rejected` folder with a note explaining why.**

## Deadline
Please respond within 24 hours.

---
*Created by AI Employee Approval Handler*
"""

        filepath.write_text(content, encoding="utf-8")
        self._log_event("approval_requested", {
            "file": filename,
            "action_type": action_type,
            "details": details
        })

        return {
            "success": True,
            "filepath": str(filepath),
            "filename": filename,
            "action_type": action_type
        }

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests."""
        if not self.pending_approval.exists():
            return []
        results = []
        for f in self.pending_approval.glob("*.md"):
            meta = self._parse_frontmatter(f.read_text(encoding="utf-8"))
            results.append({
                "filename": f.name,
                "action": meta.get("action", "unknown"),
                "created": meta.get("created", ""),
                "status": meta.get("status", "pending"),
                "risk_level": meta.get("risk_level", "medium")
            })
        return results

    def get_approved_actions(self) -> List[Dict[str, Any]]:
        """Get approved actions ready to execute."""
        if not self.approved.exists():
            return []
        results = []
        for f in self.approved.glob("*.md"):
            if f.name not in self.processed_approvals:
                meta = self._parse_frontmatter(f.read_text(encoding="utf-8"))
                results.append({
                    "filename": f.name,
                    "action": meta.get("action", "unknown"),
                    "filepath": str(f)
                })
        return results

    def get_rejected_actions(self) -> List[Dict[str, Any]]:
        """Get rejected actions to archive."""
        if not self.rejected.exists():
            return []
        results = []
        for f in self.rejected.glob("*.md"):
            if f.name not in self.processed_approvals:
                results.append({"filename": f.name, "filepath": str(f)})
        return results

    def mark_approved(self, filename: str) -> Dict[str, Any]:
        """Move a file from Pending_Approval to Approved."""
        src = self.pending_approval / filename
        if not src.exists():
            return {"success": False, "error": f"File not found: {filename}"}
        dst = self.approved / filename
        src.rename(dst)
        self._log_event("approved", {"file": filename})
        return {"success": True, "action": "moved_to_approved", "filepath": str(dst)}

    def mark_rejected(self, filename: str) -> Dict[str, Any]:
        """Move a file from Pending_Approval to Rejected."""
        src = self.pending_approval / filename
        if not src.exists():
            return {"success": False, "error": f"File not found: {filename}"}
        dst = self.rejected / filename
        src.rename(dst)
        self._log_event("rejected", {"file": filename})
        return {"success": True, "action": "moved_to_rejected", "filepath": str(dst)}

    def process_approved(self, filename: str) -> Dict[str, Any]:
        """
        Process an approved action — add execution metadata, move to Done/.
        """
        filepath = self.approved / filename
        if not filepath.exists():
            return {"success": False, "error": f"Approved file not found: {filename}"}

        content = filepath.read_text(encoding="utf-8")
        metadata = self._parse_frontmatter(content)
        action_type = metadata.get("action", "unknown")

        execution_block = f"""
---
executed: {datetime.now().isoformat()}
execution_status: success
executed_by: ApprovalHandler (Gold Tier)
action_type: {action_type}
---

## Execution Result

**Executed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** ✓ Success
**Action:** {action_type.replace('_', ' ').title()}

---
*AI Employee Approval Handler*
"""
        content += execution_block

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = filepath.stem + "_executed_" + timestamp + filepath.suffix
        dest_path = self.done / new_name
        dest_path.write_text(content, encoding="utf-8")
        filepath.unlink()

        self.processed_approvals.add(filename)
        self._save_processed()
        self._log_event("action_executed", {
            "file": filename,
            "action_type": action_type,
            "destination": new_name
        })

        return {"success": True, "action": "executed", "destination": new_name}

    def archive_rejected(self, filename: str) -> Dict[str, Any]:
        """Archive a rejected action — move to Done/."""
        filepath = self.rejected / filename
        if not filepath.exists():
            return {"success": False, "error": f"Rejected file not found: {filename}"}

        content = filepath.read_text(encoding="utf-8")
        rejection_block = f"""
---
rejected: {datetime.now().isoformat()}
status: rejected
---

*This action was rejected by human reviewer.*
"""
        content += rejection_block

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = filepath.stem + "_rejected_" + timestamp + filepath.suffix
        dest_path = self.done / new_name
        dest_path.write_text(content, encoding="utf-8")
        filepath.unlink()

        self.processed_approvals.add(filename)
        self._save_processed()
        self._log_event("action_rejected", {
            "file": filename,
            "destination": new_name
        })

        return {"success": True, "action": "archived", "destination": new_name}

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter (supports multi-line values)."""
        data = {}
        in_frontmatter = False
        current_key = None
        current_value = []
        in_multiline = False

        for line in content.split("\n"):
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    if current_key and current_value:
                        data[current_key] = "\n".join(current_value)
                    break

            if in_frontmatter:
                if ":" in line and not line.startswith("  ") and not line.startswith("    "):
                    if current_key and current_value:
                        data[current_key] = "\n".join(current_value)

                    key, value = line.split(":", 1)
                    current_key = key.strip()
                    value = value.strip().strip("\"'")

                    if value == "|":
                        in_multiline = True
                        current_value = []
                    else:
                        in_multiline = False
                        current_value = [value] if value else []
                elif in_multiline or (current_key and line.startswith("  ")):
                    current_value.append(line.rstrip())

        return data

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an event to the daily log file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **details
        }
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
