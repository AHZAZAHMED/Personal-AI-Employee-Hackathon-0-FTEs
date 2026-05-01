"""
Instagram Posting Skill - Agent Entry Point

Check Instagram comments/mentions, post images, and get insights.
"""

from typing import Dict, Any, Optional
from .service import InstagramService


def instagram_check_comments(
    recent_posts_limit: int = 5,
    vault_path: str = "AI_Employee_Vault",
    create_action_files: bool = True
) -> Dict[str, Any]:
    """
    Check Instagram Business Account for new comments on recent posts.

    Use this skill when:
    - Monitoring your Instagram account for new comments
    - Checking engagement on recent posts
    - Creating tasks from Instagram activity

    Args:
        recent_posts_limit: Number of recent posts to check (default: 5)
        vault_path: Path to AI Employee Vault
        create_action_files: Whether to create .md files in Needs_Action/

    Returns:
        Dict with success, comments list, count, action_files
    """
    try:
        service = InstagramService(vault_path=vault_path)
        result = service.check_comments(recent_posts_limit=recent_posts_limit)

        action_files = []
        if result.get("success") and create_action_files and result.get("comments"):
            action_files = service.create_action_files(result["comments"], "comment")

        result["action_files"] = action_files
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def instagram_check_mentions(
    vault_path: str = "AI_Employee_Vault",
    create_action_files: bool = True
) -> Dict[str, Any]:
    """Check Instagram for mentions (tagged media)."""
    try:
        service = InstagramService(vault_path=vault_path)
        result = service.check_mentions()

        action_files = []
        if result.get("success") and create_action_files and result.get("mentions"):
            action_files = service.create_action_files(result["mentions"], "mention")

        result["action_files"] = action_files
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def instagram_post_image(
    image_url: str,
    caption: str,
    vault_path: str = "AI_Employee_Vault",
    approval_token: Optional[str] = None,
    correlation_id: str = "",
    approver: str = "",
    approval_time: str = ""
) -> Dict[str, Any]:
    """
    Post an image to Instagram.

    **REQUIRES APPROVAL TOKEN** - This is a sensitive action that requires
    human approval. The approval_token parameter must be provided and valid.

    Use this skill when:
    - Publishing a photo to your Instagram Business Account
    - Sharing visual content with your audience

    Args:
        image_url: URL of the image to post (must be publicly accessible)
        caption: Caption text for the post
        vault_path: Path to AI Employee Vault
        approval_token: Required approval token from human approval workflow
        correlation_id: Correlation ID for audit trail (optional)
        approver: Who approved this action (optional)
        approval_time: When it was approved (optional)

    Returns:
        Dict with success status and post_id

    Example:
        # This will FAIL without approval token:
        result = instagram_post_image(
            image_url="https://example.com/image.jpg",
            caption="Check out our new product!"
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
            "message": "This action requires human approval. Instagram post was NOT published."
        }

    # Token verified - proceed with execution
    try:
        service = InstagramService(vault_path=vault_path)
        return service.post_image(image_url, caption)
    except Exception as e:
        return {"success": False, "error": str(e)}


def instagram_get_insights(
    metric: str = "impressions",
    days: int = 7,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """Get Instagram insights/analytics."""
    try:
        service = InstagramService(vault_path=vault_path)
        return service.get_insights(metric=metric, days=days)
    except Exception as e:
        return {"success": False, "error": str(e)}


def instagram_test_connection(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """Test Instagram API connection."""
    try:
        service = InstagramService(vault_path=vault_path)
        return service.test_connection()
    except Exception as e:
        return {"success": False, "error": str(e)}
