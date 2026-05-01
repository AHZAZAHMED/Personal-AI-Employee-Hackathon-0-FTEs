"""
Human Approval Skill - Agent Entry Point

Manages human-in-the-loop approval workflow for sensitive AI actions.
"""

from typing import Dict, Any, Optional
from .service import ApprovalService


def create_approval_request(
    action_type: str,
    details: Dict[str, Any],
    description: str = "",
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Create a human-in-the-loop approval request.

    Use this skill when:
    - A sensitive AI action requires human review before execution
    - Sending emails, making payments, or posting to social media
    - Any action marked as requiring approval per Company Handbook

    Args:
        action_type: Type of action (e.g., 'email_reply', 'email_send',
                     'payment', 'social_post', 'invoice')
        details: Dictionary with action details (to, subject, draft_body,
                 amount, recipient, platform, risk_level, etc.)
        description: Human-readable description of why approval is needed
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with keys:
        - success (bool): Whether the request was created
        - filepath (str): Path to the created approval file
        - filename (str): Name of the approval file
        - action_type (str): The action type
        - error (str|None): Error message if failed

    Example:
        result = create_approval_request(
            action_type="email_send",
            details={
                "to": "client@example.com",
                "subject": "Re: Inquiry",
                "draft_body": "Dear Client,\\n\\nThank you...",
                "risk_level": "medium"
            }
        )
    """
    try:
        service = ApprovalService(vault_path=vault_path)
        return service.create_approval_request(action_type, details, description)
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_pending_approvals(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    List all pending approval requests awaiting human review.

    Use this skill when:
    - Checking what actions are waiting for approval
    - Displaying a dashboard of pending items

    Args:
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with keys:
        - success (bool)
        - pending (list): List of pending approval dicts
        - count (int): Number of pending approvals
    """
    try:
        service = ApprovalService(vault_path=vault_path)
        pending = service.get_pending_approvals()
        return {"success": True, "pending": pending, "count": len(pending)}
    except Exception as e:
        return {"success": False, "error": str(e), "pending": [], "count": 0}


def list_approved_actions(
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    List all approved actions ready for execution.

    Args:
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status and list of approved actions
    """
    try:
        service = ApprovalService(vault_path=vault_path)
        approved = service.get_approved_actions()
        return {"success": True, "approved": approved, "count": len(approved)}
    except Exception as e:
        return {"success": False, "error": str(e), "approved": [], "count": 0}


def approve_action(
    filename: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Move an approval request from Pending to Approved.

    Args:
        filename: Name of the approval file to approve
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status
    """
    try:
        service = ApprovalService(vault_path=vault_path)
        return service.mark_approved(filename)
    except Exception as e:
        return {"success": False, "error": str(e)}


def reject_action(
    filename: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Move an approval request from Pending to Rejected.

    Args:
        filename: Name of the approval file to reject
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status
    """
    try:
        service = ApprovalService(vault_path=vault_path)
        return service.mark_rejected(filename)
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_approved_action(
    filename: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Process an approved action — execute it and move to Done/.

    Args:
        filename: Name of the approved file to process
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status and destination
    """
    try:
        service = ApprovalService(vault_path=vault_path)
        return service.process_approved(filename)
    except Exception as e:
        return {"success": False, "error": str(e)}


def archive_rejected_action(
    filename: str,
    vault_path: str = "AI_Employee_Vault"
) -> Dict[str, Any]:
    """
    Archive a rejected action to Done/.

    Args:
        filename: Name of the rejected file to archive
        vault_path: Path to AI Employee Vault

    Returns:
        Dict with success status and destination
    """
    try:
        service = ApprovalService(vault_path=vault_path)
        return service.archive_rejected(filename)
    except Exception as e:
        return {"success": False, "error": str(e)}
