"""
Skill Registry - Dynamic Skill Discovery & Dispatch

Scans the skills/ directory, reads schema.json files, builds a registry
of callable skill functions, and dispatches tasks by matching task types
to skill names.

This replaces hardcoded imports in orchestrator.py with dynamic discovery.

Usage:
    from skill_registry import SkillRegistry

    registry = SkillRegistry(skills_dir="skills/")
    registry.discover()              # Scan skills/ folder
    registry.list_skills()           # Show available skills
    result = registry.dispatch("email_generate_response", **kwargs)
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Add Gold-Tier root to sys.path so 'skills' package is importable
_golod_tier_root = Path(__file__).parent.parent
if str(_golod_tier_root) not in sys.path:
    sys.path.insert(0, str(_golod_tier_root))

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Dynamic skill registry — discovers and dispatches agent skills.

    Architecture:
        skills/
        ├── whatsapp/
        │   ├── schema.json   ← name, description, parameters
        │   └── skill.py      ← callable functions
        ├── gmail_watcher/
        └── ...

    The registry:
    1. Scans skills/ for folders containing schema.json + skill.py
    2. Reads schema.json to get skill metadata
    3. Imports skill.py and extracts callable functions
    4. Maps task types → skill functions for dispatch
    """

    # Mapping from task types (from .md task files) to skill function names
    TASK_TYPE_MAP = {
        "email": "email_generate_response",
        "email_send": "email_send",
        "email_reply": "email_send",
        "whatsapp": "whatsapp_send_message",
        "whatsapp_reply": "whatsapp_send_message",
        "gmail_check": "gmail_check_unread",
        "gmail": "gmail_check_unread",
        "approval": "create_approval_request",
        "approval_request": "create_approval_request",
        "payment": "create_approval_request",
        "social_post": "create_approval_request",
        "invoice": "create_approval_request",
        "planning": "create_task_plan",
        "plan": "create_task_plan",
        "social_media": "linkedin_create_post_draft",
        "linkedin": "linkedin_create_post_draft",
        "linkedin_post": "linkedin_create_post_draft",
        "ceo_briefing": "generate_ceo_briefing",
        "weekly_briefing": "generate_ceo_briefing",
        "business_report": "generate_ceo_briefing",
        "error": "classify_error",
        "error_classification": "classify_error",
        "health_check": "get_health_status",
        "facebook": "facebook_check_mentions",
        "facebook_mention": "facebook_check_mentions",
        "facebook_post": "facebook_create_post",
        "instagram": "instagram_check_comments",
        "instagram_comment": "instagram_check_comments",
        "instagram_mention": "instagram_check_mentions",
        "instagram_post": "instagram_post_image",
        "invoice": "odoo_create_invoice",
        "payment": "odoo_record_payment",
        "accounting": "odoo_get_account_balance",
        "odoo": "odoo_create_invoice",
        "financial_report": "odoo_generate_financial_report",
        "file_drop": "scan_watch_folder",
        "file_scan": "scan_watch_folder",
        "file_watcher": "scan_watch_folder",
        "sync_neon": "sync_neon_to_vault",
        "sync_vault": "sync_neon_to_vault",
        "db_sync": "sync_neon_to_vault",
        "email_to_invoice": "process_email_to_invoice",
        "create_invoice_from_email": "process_email_to_invoice",
        "invoice_email": "process_email_to_invoice",
        "currency_update": "update_currency_rates",
        "currency_rates": "update_currency_rates",
        "exchange_rates": "update_currency_rates",
    }

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Dict[str, Any]] = {}  # name → {schema, functions, module}

    def discover(self) -> int:
        """
        Scan skills/ directory and register all valid skills.

        Returns:
            Number of skills discovered
        """
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return 0

        count = 0
        for skill_folder in sorted(self.skills_dir.iterdir()):
            if not skill_folder.is_dir():
                continue
            if skill_folder.name.startswith("_") or skill_folder.name.startswith("."):
                continue

            schema_file = skill_folder / "schema.json"
            skill_py = skill_folder / "skill.py"

            if not schema_file.exists():
                logger.debug(f"Skipping {skill_folder.name}: no schema.json")
                continue
            if not skill_py.exists():
                logger.debug(f"Skipping {skill_folder.name}: no skill.py")
                continue

            try:
                skill_info = self._register_skill(skill_folder, schema_file, skill_py)
                if skill_info:
                    self.skills[skill_info["name"]] = skill_info
                    count += 1
                    logger.info(f"Registered skill: {skill_info['name']}")
            except Exception as e:
                logger.error(f"Failed to register skill {skill_folder.name}: {e}")

        return count

    def _register_skill(self, folder: Path, schema_file: Path,
                        skill_py: Path) -> Optional[Dict[str, Any]]:
        """Register a single skill."""
        # Read schema
        with open(schema_file) as f:
            schema = json.load(f)

        # Import skill module
        module_name = f"{self.skills_dir.name}.{folder.name}.skill"
        skill_module = importlib.import_module(module_name)

        # Extract all public callable functions (not starting with _)
        functions = {}
        for attr_name in dir(skill_module):
            if attr_name.startswith("_"):
                continue
            attr = getattr(skill_module, attr_name)
            if callable(attr):
                functions[attr_name] = attr

        return {
            "name": schema.get("name", folder.name),
            "schema": schema,
            "functions": functions,
            "module": skill_module,
            "folder": str(folder)
        }

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a skill by name."""
        return self.skills.get(name)

    def list_skills(self) -> List[Dict[str, str]]:
        """
        List all registered skills with their descriptions.

        Returns:
            List of dicts with name and description.
        """
        result = []
        for name, info in self.skills.items():
            result.append({
                "name": name,
                "description": info["schema"].get("description", ""),
                "functions": list(info["functions"].keys()),
                "parameters": info["schema"].get("parameters", {}).get("properties", {})
            })
        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all skills as agent tool definitions (for LLM tool calling).

        Returns:
            List of tool definitions compatible with agent frameworks.
        """
        tools = []
        for name, info in self.skills.items():
            schema = info["schema"]
            tools.append({
                "name": schema["name"],
                "description": schema.get("description", ""),
                "parameters": schema.get("parameters", {})
            })
        return tools

    def dispatch(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        Dispatch to a skill function by skill name.

        Uses the skill's primary function (same name as the skill).

        Args:
            skill_name: Name of the skill (e.g., "email_generate_response")
            **kwargs: Arguments to pass to the skill function

        Returns:
            Result dict from the skill function

        Example:
            result = registry.dispatch(
                "email_generate_response",
                from_email="client@example.com",
                subject="Inquiry",
                body="Hello"
            )
        """
        skill = self.skills.get(skill_name)
        if not skill:
            return {
                "success": False,
                "error": f"Skill not found: {skill_name}. Available: {list(self.skills.keys())}"
            }

        func = skill["functions"].get(skill_name)
        if not func:
            # Try to find the first public function
            if skill["functions"]:
                func = next(iter(skill["functions"].values()))
            else:
                return {
                    "success": False,
                    "error": f"No callable functions found in skill: {skill_name}"
                }

        try:
            return func(**kwargs)
        except TypeError as e:
            # Try with only the kwargs that the function accepts
            import inspect
            sig = inspect.signature(func)
            valid_params = set(sig.parameters.keys())
            filtered = {k: v for k, v in kwargs.items() if k in valid_params}
            logger.debug(f"Filtering kwargs for {skill_name}: {filtered}")
            return func(**filtered)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def dispatch_by_task_type(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        Dispatch to a skill based on a task type string.

        Maps task types (from .md task files) to skill function names
        using the TASK_TYPE_MAP.

        Args:
            task_type: Task type string (e.g., "email", "whatsapp_reply")
            **kwargs: Arguments to pass to the skill

        Returns:
            Result dict from the skill function

        Example:
            result = registry.dispatch_by_task_type("email", from_email="...", subject="...")
        """
        # Try exact match first
        if task_type in self.skills:
            return self.dispatch(task_type, **kwargs)

        # Try mapped match
        skill_func_name = self.TASK_TYPE_MAP.get(task_type)
        if skill_func_name:
            # Find which skill this function belongs to
            for skill_name, skill_info in self.skills.items():
                if skill_func_name in skill_info["functions"]:
                    func = skill_info["functions"][skill_func_name]
                    try:
                        return func(**kwargs)
                    except TypeError:
                        import inspect
                        sig = inspect.signature(func)
                        valid_params = set(sig.parameters.keys())
                        filtered = {k: v for k, v in kwargs.items() if k in valid_params}
                        return func(**filtered)
                    except Exception as e:
                        return {"success": False, "error": str(e)}

            return {
                "success": False,
                "error": f"Function '{skill_func_name}' not found in any registered skill"
            }

        return {
            "success": False,
            "error": f"No skill registered for task type: {task_type}. Available: {list(self.skills.keys())}"
        }

    def has_skill(self, name: str) -> bool:
        """Check if a skill is registered."""
        return name in self.skills

    def get_task_type_mapping(self) -> Dict[str, str]:
        """
        Get current task type → skill function mapping.

        Returns:
            Dict mapping task types to skill function names.
        """
        return dict(self.TASK_TYPE_MAP)

    def register_task_type(self, task_type: str, skill_function_name: str) -> bool:
        """
        Register a new task type mapping.

        Args:
            task_type: Task type string from .md files
            skill_function_name: Name of the skill function to call

        Returns:
            True if the skill function exists in any registered skill
        """
        # Check if this function exists
        for skill_info in self.skills.values():
            if skill_function_name in skill_info["functions"]:
                self.TASK_TYPE_MAP[task_type] = skill_function_name
                return True

        logger.warning(f"Function '{skill_function_name}' not found in any skill")
        return False


# ─── Convenience: global registry instance ─────────────────────────

_registry: Optional[SkillRegistry] = None


def get_registry(skills_dir: str = "skills") -> SkillRegistry:
    """Get or create the global registry instance."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry(skills_dir=skills_dir)
        _registry.discover()
    return _registry


def dispatch(skill_name: str, **kwargs) -> Dict[str, Any]:
    """Dispatch to a skill using the global registry."""
    return get_registry().dispatch(skill_name, **kwargs)


def dispatch_by_task_type(task_type: str, **kwargs) -> Dict[str, Any]:
    """Dispatch by task type using the global registry."""
    return get_registry().dispatch_by_task_type(task_type, **kwargs)
