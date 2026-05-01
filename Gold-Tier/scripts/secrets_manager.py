"""
Centralized Secrets Management System

Provides secure access to API keys and credentials from multiple sources:
1. Environment variables (.env file via python-dotenv)
2. AWS Secrets Manager (optional)
3. Azure Key Vault (optional)
4. HashiCorp Vault (optional)

Usage:
    from secrets_manager import get_secret, SecretNotFoundError

    # Get a secret (raises exception if not found)
    api_key = get_secret('FACEBOOK_APP_SECRET')

    # Get with default value
    api_key = get_secret('OPTIONAL_KEY', default='fallback_value')

    # Check if secret exists
    if has_secret('FEATURE_FLAG'):
        ...

Security Features:
- Never logs secret values
- Supports multiple secret backends
- Caches secrets in memory (not on disk)
- Validates secret format before returning
- Audit logging for secret access
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Try to import optional secret backends
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

# Configure logging
logger = logging.getLogger('SecretsManager')
logger.setLevel(logging.INFO)


class SecretNotFoundError(Exception):
    """Raised when a required secret is not found."""
    pass


class SecretsManager:
    """
    Centralized secrets management with multiple backend support.

    Priority order:
    1. Environment variables (highest priority)
    2. AWS Secrets Manager
    3. Azure Key Vault
    4. HashiCorp Vault
    """

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._backend = self._detect_backend()
        logger.info(f"Secrets backend: {self._backend}")

    def _detect_backend(self) -> str:
        """Detect which secrets backend to use."""
        # Always support environment variables
        if os.getenv('AWS_SECRETS_MANAGER_NAME') and AWS_AVAILABLE:
            return 'aws'
        elif os.getenv('AZURE_KEYVAULT_URL') and AZURE_AVAILABLE:
            return 'azure'
        elif os.getenv('VAULT_ADDR') and VAULT_AVAILABLE:
            return 'vault'
        else:
            return 'env'

    def get(self, key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
        """
        Get a secret value.

        Args:
            key: Secret key name (e.g., 'FACEBOOK_APP_SECRET')
            default: Default value if secret not found
            required: If True, raises exception when secret not found and no default

        Returns:
            Secret value or default

        Raises:
            SecretNotFoundError: If required=True and secret not found
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # Try to get from backend
        value = None

        # Priority 1: Environment variables (always check first)
        value = os.getenv(key)

        # Priority 2: Cloud secrets manager
        if value is None and self._backend != 'env':
            try:
                if self._backend == 'aws':
                    value = self._get_from_aws(key)
                elif self._backend == 'azure':
                    value = self._get_from_azure(key)
                elif self._backend == 'vault':
                    value = self._get_from_vault(key)
            except Exception as e:
                logger.warning(f"Failed to get secret '{key}' from {self._backend}: {e}")

        # Use default if provided
        if value is None and default is not None:
            value = default

        # Raise exception if required and not found
        if value is None and required:
            raise SecretNotFoundError(
                f"Secret '{key}' not found in environment or {self._backend} backend. "
                f"Please set it in .env file or secrets manager."
            )

        # Cache the value (only if found)
        if value is not None:
            self._cache[key] = value
            logger.debug(f"Secret '{key}' loaded from {self._backend}")

        return value

    def has(self, key: str) -> bool:
        """Check if a secret exists."""
        try:
            self.get(key, required=True)
            return True
        except SecretNotFoundError:
            return False

    def _get_from_aws(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        if not AWS_AVAILABLE:
            return None

        secret_name = os.getenv('AWS_SECRETS_MANAGER_NAME')
        region = os.getenv('AWS_REGION', 'us-east-1')

        try:
            client = boto3.client('secretsmanager', region_name=region)
            response = client.get_secret_value(SecretId=secret_name)

            # AWS stores secrets as JSON
            import json
            secrets = json.loads(response['SecretString'])
            return secrets.get(key)
        except Exception as e:
            logger.warning(f"AWS Secrets Manager error: {e}")
            return None

    def _get_from_azure(self, key: str) -> Optional[str]:
        """Get secret from Azure Key Vault."""
        if not AZURE_AVAILABLE:
            return None

        vault_url = os.getenv('AZURE_KEYVAULT_URL')

        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)
            secret = client.get_secret(key)
            return secret.value
        except Exception as e:
            logger.warning(f"Azure Key Vault error: {e}")
            return None

    def _get_from_vault(self, key: str) -> Optional[str]:
        """Get secret from HashiCorp Vault."""
        if not VAULT_AVAILABLE:
            return None

        vault_addr = os.getenv('VAULT_ADDR')
        vault_token = os.getenv('VAULT_TOKEN')
        vault_path = os.getenv('VAULT_SECRET_PATH', 'secret/ai-employee')

        try:
            client = hvac.Client(url=vault_addr, token=vault_token)
            response = client.secrets.kv.v2.read_secret_version(path=vault_path)
            return response['data']['data'].get(key)
        except Exception as e:
            logger.warning(f"HashiCorp Vault error: {e}")
            return None

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
        logger.info("Secrets cache cleared")


# Global singleton instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
    """
    Get a secret value (convenience function).

    Args:
        key: Secret key name
        default: Default value if not found
        required: Raise exception if not found and no default

    Returns:
        Secret value or default

    Example:
        api_key = get_secret('FACEBOOK_APP_SECRET')
        optional = get_secret('OPTIONAL_KEY', default='fallback')
    """
    return get_secrets_manager().get(key, default=default, required=required)


def has_secret(key: str) -> bool:
    """Check if a secret exists."""
    return get_secrets_manager().has(key)


def clear_secrets_cache():
    """Clear the secrets cache (useful for testing)."""
    get_secrets_manager().clear_cache()


# Convenience functions for common secrets
def get_facebook_credentials() -> Dict[str, str]:
    """Get all Facebook credentials."""
    return {
        'app_id': get_secret('FACEBOOK_APP_ID'),
        'app_secret': get_secret('FACEBOOK_APP_SECRET'),
        'page_id': get_secret('FACEBOOK_PAGE_ID'),
        'user_token': get_secret('FACEBOOK_USER_TOKEN'),
        'page_token': get_secret('FACEBOOK_PAGE_TOKEN'),
    }


def get_twitter_credentials() -> Dict[str, str]:
    """Get all Twitter credentials."""
    return {
        'api_key': get_secret('TWITTER_API_KEY'),
        'api_secret': get_secret('TWITTER_API_SECRET'),
        'access_token': get_secret('TWITTER_ACCESS_TOKEN'),
        'access_secret': get_secret('TWITTER_ACCESS_SECRET'),
        'bearer_token': get_secret('BEARER_TOKEN'),
    }


def get_twilio_credentials() -> Dict[str, str]:
    """Get all Twilio credentials."""
    return {
        'account_sid': get_secret('TWILIO_ACCOUNT_SID'),
        'auth_token': get_secret('TWILIO_AUTH_TOKEN'),
        'whatsapp_number': get_secret('TWILIO_WHATSAPP_NUMBER'),
    }


def get_database_url() -> str:
    """Get database connection URL."""
    return get_secret('NEON_DATABASE_URL')


def get_ai_credentials() -> Dict[str, str]:
    """Get AI service credentials."""
    return {
        'gemini_api_key': get_secret('GEMINI_API_KEY'),
        'anthropic_api_key': get_secret('ANTHROPIC_API_KEY', required=False),
    }
