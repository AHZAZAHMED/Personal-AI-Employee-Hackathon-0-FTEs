"""
Facebook Posting Skill - Agent Entry Point

Check Facebook Page mentions, create posts, and get insights.
"""

from typing import Dict, Any, Optional
from .service import FacebookService


def facebook_check_mentions(
    since_hours: int = 24,
    vault_path: str = "AI_Employee_Vault",
    create_action_files: bool = True
) -> Dict[str, Any]:
    """
    Check Facebook Page for new mentions.

    Use this skill when:
    - Monitoring your Facebook Page for mentions or activity
    - Checking if anyone mentioned your business page
    - Creating tasks from Facebook engagement

    Args:
        since_hours: Check mentions from the last N hours (default: 24)
        vault_path: Path to AI Employee Vault
        create_action_files: Whether to create .md files in Needs_Action/

    Returns:
        Dict with keys:
        - success (bool)
        - mentions (list): New mention dicts
        - count (int): Number of new mentions
        - action_files (list): Paths of created action files
        - error (str|None)
    """
    try:
        service = FacebookService(vault_path=vault_path)
        result = service.check_mentions(since_hours=since_hours)

        action_files = []
        if result.get("success") and create_action_files and result.get("mentions"):
            action_files = service.create_action_files(result["mentions"])

        result["action_files"] = action_files
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def facebook_create_post(
    message: str,
    link: Optional[str] = None,
    photo_url: Optional[str] = None,
    vault_path: str = "AI_Employee_Vault",
    approval_token: Optional[str] = None,
    correlation_id: str = "",
    approver: str = "",
    approval_time: str = ""
) -> Dict[str, Any]:
    """
    Create a post on Facebook Page.

    **REQUIRES APPROVAL TOKEN** - This is a sensitive action that requires
    human approval. The approval_token parameter must be provided and valid.

    Use this skill when:
    - Publishing a business update to Facebook
    - Sharing content with your Facebook audience

    Args:
        message: Post message/content
        link: Optional link to share
        photo_url: Optional photo URL
        vault_path: Path to AI Employee Vault
        approval_token: Required approval token from human approval workflow
        correlation_id: Correlation ID for audit trail (optional)
        approver: Who approved this action (optional)
        approval_time: When it was approved (optional)

    Returns:
        Dict with success status and post_id

    Example:
        # This will FAIL without approval token:
        result = facebook_create_post(
            message="Check out our latest update!"
        )
        # Returns: {"success": False, "error": "APPROVAL_REQUIRED"}
    """
    # SECURITY: Verify approval token before executing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from approval_tokens import get_token_manager

    token_manager = get_token_manager(vault_path)

    if not token_manager.verify_token(approval_token, "social_post"):
        return {
            "success": False,
            "error": "APPROVAL_REQUIRED",
            "message": "This action requires human approval. Facebook post was NOT published."
        }

    # Token verified - proceed with execution
    try:
        service = FacebookService(vault_path=vault_path)
        return service.create_post(message, link, photo_url)
    except Exception as e:
        return {"success": False, "error": str(e)}


def facebook_get_insights(
    days: int = 7,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """Get Facebook Page insights/analytics."""
    try:
        service = FacebookService(vault_path=vault_path)
        return service.get_insights(days=days)
    except Exception as e:
        return {"success": False, "error": str(e)}


def facebook_test_connection(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """Test Facebook API connection."""
    try:
        service = FacebookService(vault_path=vault_path)
        return service.test_connection()
    except Exception as e:
        return {"success": False, "error": str(e)}
