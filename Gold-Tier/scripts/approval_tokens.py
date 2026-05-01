"""
Approval Token Manager for AI Employee - Gold Tier

Provides secure token-based approval enforcement for sensitive actions.
Prevents bypass of approval workflow by requiring valid tokens for execution.

Features:
- Cryptographically secure token generation
- Token expiration (24 hours default)
- Single-use tokens (consumed after use)
- Action-type validation
- File-based storage (upgradeable to Redis)

Usage:
    # Generate token (orchestrator)
    token = manager.generate_token("email_send", {"to": "user@example.com"})

    # Verify token (skill)
    if not manager.verify_token(token, "email_send"):
        raise ApprovalRequiredError()
"""

import json
import secrets
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class ApprovalTokenManager:
    """Manages approval tokens for secure action execution."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.tokens_file = self.vault / "Logs" / "approval_tokens.json"
        self.tokens_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing tokens
        self.tokens = self._load_tokens()

        # Clean expired tokens on init
        self._clean_expired_tokens()

    def _load_tokens(self) -> Dict[str, Dict[str, Any]]:
        """Load tokens from disk."""
        if self.tokens_file.exists():
            try:
                with open(self.tokens_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_tokens(self):
        """Save tokens to disk."""
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump(self.tokens, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save tokens: {e}")

    def _clean_expired_tokens(self):
        """Remove expired tokens."""
        now = datetime.now()
        expired = []

        for token, data in self.tokens.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if expires_at < now:
                expired.append(token)

        for token in expired:
            del self.tokens[token]

        if expired:
            self._save_tokens()

    def generate_token(
        self,
        action_type: str,
        metadata: Dict[str, Any],
        expires_hours: int = 24,
        single_use: bool = True
    ) -> str:
        """
        Generate a secure approval token.

        Args:
            action_type: Type of action (e.g., "email_send", "odoo_create_invoice")
            metadata: Action metadata (for audit trail)
            expires_hours: Token expiration in hours (default: 24)
            single_use: If True, token is consumed after first use

        Returns:
            Secure token string
        """
        # Generate cryptographically secure token
        token = secrets.token_urlsafe(32)

        # Store token with metadata
        self.tokens[token] = {
            "action_type": action_type,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
            "single_use": single_use,
            "used": False
        }

        self._save_tokens()
        return token

    def verify_token(
        self,
        token: Optional[str],
        action_type: str,
        consume: bool = True
    ) -> bool:
        """
        Verify an approval token.

        Args:
            token: Token to verify
            action_type: Expected action type
            consume: If True, mark token as used (for single-use tokens)

        Returns:
            True if token is valid, False otherwise
        """
        # No token provided
        if not token:
            return False

        # Token not found
        if token not in self.tokens:
            return False

        data = self.tokens[token]

        # Check if expired
        expires_at = datetime.fromisoformat(data["expires_at"])
        if expires_at < datetime.now():
            # Clean up expired token
            del self.tokens[token]
            self._save_tokens()
            return False

        # Check action type matches
        if data["action_type"] != action_type:
            return False

        # Check if already used (for single-use tokens)
        if data["single_use"] and data["used"]:
            return False

        # Mark as used if consuming
        if consume and data["single_use"]:
            self.tokens[token]["used"] = True
            self._save_tokens()

        return True

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (remove it).

        Args:
            token: Token to revoke

        Returns:
            True if token was revoked, False if not found
        """
        if token in self.tokens:
            del self.tokens[token]
            self._save_tokens()
            return True
        return False

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token (for debugging/audit).

        Args:
            token: Token to inspect

        Returns:
            Token metadata or None if not found
        """
        return self.tokens.get(token)

    def list_active_tokens(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active (non-expired, non-used) tokens.

        Returns:
            Dictionary of active tokens
        """
        self._clean_expired_tokens()

        active = {}
        for token, data in self.tokens.items():
            if not (data["single_use"] and data["used"]):
                active[token] = data

        return active


class ApprovalRequiredError(Exception):
    """Raised when an action requires approval but no valid token provided."""
    pass


# Singleton instance for easy access
_token_manager = None

def get_token_manager(vault_path: str = "AI_Employee_Vault") -> ApprovalTokenManager:
    """Get or create the global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = ApprovalTokenManager(vault_path)
    return _token_manager
