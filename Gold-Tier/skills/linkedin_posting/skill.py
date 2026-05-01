"""
LinkedIn Posting Skill - Agent Entry Point

Creates LinkedIn post drafts for human approval and publishes
approved posts via Playwright browser automation.
"""

from typing import Dict, Any
from .service import LinkedInService


def linkedin_create_post_draft(
    content: str,
    post_type: str = "announcement",
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Create a LinkedIn post draft for human review and approval.

    Use this skill when:
    - You need to post a business update to LinkedIn
    - Creating an announcement or company update
    - The post requires human review before publishing

    The draft is saved to Pending_Approval/ for human review.
    Move it to Approved/ to trigger publishing.

    Args:
        content: The LinkedIn post content/text
        post_type: Type of post ('announcement', 'update', 'article', 'default')
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with keys:
        - success (bool): Whether draft was created
        - filepath (str): Path to the draft file
        - filename (str): Name of the draft file
        - post_type (str): The post type
        - error (str|None): Error message if failed

    Example:
        result = linkedin_create_post_draft(
            content="Excited to announce our new product launch!"
        )
    """
    try:
        service = LinkedInService(vault_path=vault_path)
        return service.create_post_draft(content, post_type)
    except Exception as e:
        return {"success": False, "error": str(e)}


def linkedin_publish_post(
    post_content: str,
    vault_path: str = "AI_Employee_Vault",
    approval_token: str = None,
    correlation_id: str = "",
    approver: str = "",
    approval_time: str = ""
) -> Dict[str, Any]:
    """
    Publish a post directly to LinkedIn via Playwright.

    **REQUIRES APPROVAL TOKEN** - This is a sensitive action that requires
    human approval. The approval_token parameter must be provided and valid.

    Use this skill when:
    - You have an approved post ready to publish
    - Automating social media posting

    Note: LinkedIn may flag automated posting. Use with caution.

    Args:
        post_content: The post text to publish
        vault_path: Path to AI Employee Vault
        approval_token: Required approval token from human approval workflow
        correlation_id: Correlation ID for audit trail (optional)
        approver: Who approved this action (optional)
        approval_time: When it was approved (optional)

    Returns:
        Dict with keys:
        - success (bool): Whether post was published
        - screenshot (str|None): Path to confirmation screenshot
        - steps_completed (list): List of completed steps
        - error (str|None): Error message if failed

    Example:
        # This will FAIL without approval token:
        result = linkedin_publish_post(
            post_content="Excited to announce our new product!"
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
            "message": "This action requires human approval. LinkedIn post was NOT published."
        }

    # Token verified - proceed with execution
    try:
        service = LinkedInService(vault_path=vault_path)
        return service.publish_post(post_content)
    except Exception as e:
        return {"success": False, "error": str(e)}


def linkedin_list_pending(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """List pending LinkedIn post drafts awaiting approval."""
    try:
        service = LinkedInService(vault_path=vault_path)
        pending = service.get_pending_posts()
        return {"success": True, "pending": pending, "count": len(pending)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def linkedin_list_approved(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """List approved LinkedIn posts ready to publish."""
    try:
        service = LinkedInService(vault_path=vault_path)
        approved = service.get_approved_posts()
        return {"success": True, "approved": approved, "count": len(approved)}
    except Exception as e:
        return {"success": False, "error": str(e)}
