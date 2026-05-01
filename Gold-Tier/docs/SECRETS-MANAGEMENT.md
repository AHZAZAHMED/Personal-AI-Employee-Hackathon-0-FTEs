# Secrets Management System

**Status:** ✅ IMPLEMENTED  
**Date:** 2026-04-25  
**Addresses:** AUDIT-1 BLOCKER #1 (Security)

---

## Overview

Centralized secrets management system that provides secure access to API keys and credentials from multiple sources with priority-based fallback.

**Priority Order:**
1. Environment variables (.env file) - Highest priority
2. AWS Secrets Manager
3. Azure Key Vault
4. HashiCorp Vault

---

## Quick Start

### Basic Usage

```python
from scripts.secrets_manager import get_secret, has_secret

# Get a required secret (raises exception if not found)
api_key = get_secret('FACEBOOK_APP_SECRET')

# Get with default value
optional_key = get_secret('OPTIONAL_KEY', default='fallback', required=False)

# Check if secret exists
if has_secret('FEATURE_FLAG'):
    enable_feature()
```

### Convenience Functions

```python
from scripts.secrets_manager import (
    get_facebook_credentials,
    get_twitter_credentials,
    get_twilio_credentials,
    get_ai_credentials,
    get_database_url,
)

# Get all Facebook credentials at once
fb_creds = get_facebook_credentials()
# Returns: {'app_id': '...', 'app_secret': '...', 'page_id': '...', ...}

# Get database URL
db_url = get_database_url()

# Get AI service credentials
ai_creds = get_ai_credentials()
# Returns: {'gemini_api_key': '...', 'anthropic_api_key': '...'}
```

---

## Configuration

### Environment Variables Only (Default)

No configuration needed. Secrets are loaded from `.env` file via `python-dotenv`.

```bash
# .env
FACEBOOK_APP_SECRET=your_secret_here
TWITTER_API_KEY=your_key_here
```

### AWS Secrets Manager

```bash
# .env
AWS_SECRETS_MANAGER_NAME=ai-employee/prod
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

**AWS Secrets Format (JSON):**
```json
{
  "FACEBOOK_APP_SECRET": "your_secret_here",
  "TWITTER_API_KEY": "your_key_here",
  "GEMINI_API_KEY": "your_key_here"
}
```

**Install AWS SDK:**
```bash
pip install boto3
```

### Azure Key Vault

```bash
# .env
AZURE_KEYVAULT_URL=https://your-vault.vault.azure.net/
```

**Install Azure SDK:**
```bash
pip install azure-keyvault-secrets azure-identity
```

### HashiCorp Vault

```bash
# .env
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=your_vault_token
VAULT_SECRET_PATH=secret/ai-employee
```

**Install Vault SDK:**
```bash
pip install hvac
```

---

## Security Features

### 1. Never Logs Secret Values

```python
# Logs show key names, not values
logger.info("Secret 'FACEBOOK_APP_SECRET' loaded from env")
# NOT: logger.info(f"Secret value: {secret_value}")
```

### 2. In-Memory Caching Only

Secrets are cached in memory for performance, never written to disk.

```python
# Clear cache when needed (e.g., after rotation)
from scripts.secrets_manager import clear_secrets_cache
clear_secrets_cache()
```

### 3. Multiple Backend Support

Automatically detects and uses the best available backend:
- Environment variables (always available)
- AWS Secrets Manager (if configured)
- Azure Key Vault (if configured)
- HashiCorp Vault (if configured)

### 4. Graceful Degradation

If cloud backend fails, falls back to environment variables.

```python
# Even if AWS Secrets Manager is down, env vars still work
api_key = get_secret('FACEBOOK_APP_SECRET')  # Gets from .env
```

---

## Migration Guide

### Step 1: Update Existing Code

**Before:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('FACEBOOK_APP_SECRET')
```

**After:**
```python
from scripts.secrets_manager import get_secret

api_key = get_secret('FACEBOOK_APP_SECRET')
```

### Step 2: Update All Skills

Run this script to update all skills:

```bash
# Find all os.getenv() calls
grep -r "os.getenv" skills/ --include="*.py"

# Replace with get_secret()
# Manual review recommended for each file
```

### Step 3: Test End-to-End

```bash
python tests/test_secrets_manager.py
python tests/test_all_skills.py
```

---

## API Reference

### `get_secret(key, default=None, required=True)`

Get a secret value.

**Parameters:**
- `key` (str): Secret key name (e.g., 'FACEBOOK_APP_SECRET')
- `default` (str, optional): Default value if secret not found
- `required` (bool): If True, raises exception when secret not found and no default

**Returns:**
- `str` or `None`: Secret value or default

**Raises:**
- `SecretNotFoundError`: If required=True and secret not found

**Examples:**
```python
# Required secret (raises exception if missing)
api_key = get_secret('FACEBOOK_APP_SECRET')

# Optional secret with default
timeout = get_secret('REQUEST_TIMEOUT', default='30', required=False)

# Optional secret without default (returns None if missing)
feature_flag = get_secret('BETA_FEATURE', required=False)
```

### `has_secret(key)`

Check if a secret exists.

**Parameters:**
- `key` (str): Secret key name

**Returns:**
- `bool`: True if secret exists, False otherwise

**Example:**
```python
if has_secret('PREMIUM_FEATURE_KEY'):
    enable_premium_features()
```

### `clear_secrets_cache()`

Clear the in-memory secrets cache.

**Use Cases:**
- After rotating API keys
- During testing
- When switching environments

**Example:**
```python
# Rotate keys
rotate_all_api_keys()

# Clear cache so new keys are loaded
clear_secrets_cache()

# Next call will fetch fresh values
api_key = get_secret('FACEBOOK_APP_SECRET')
```

### `get_facebook_credentials()`

Get all Facebook credentials as a dictionary.

**Returns:**
```python
{
    'app_id': str,
    'app_secret': str,
    'page_id': str,
    'user_token': str,
    'page_token': str,
}
```

### `get_twitter_credentials()`

Get all Twitter credentials as a dictionary.

**Returns:**
```python
{
    'api_key': str,
    'api_secret': str,
    'access_token': str,
    'access_secret': str,
    'bearer_token': str,
}
```

### `get_twilio_credentials()`

Get all Twilio credentials as a dictionary.

**Returns:**
```python
{
    'account_sid': str,
    'auth_token': str,
    'whatsapp_number': str,
}
```

### `get_ai_credentials()`

Get AI service credentials as a dictionary.

**Returns:**
```python
{
    'gemini_api_key': str,
    'anthropic_api_key': str or None,
}
```

### `get_database_url()`

Get database connection URL.

**Returns:**
- `str`: PostgreSQL connection URL

---

## Testing

### Run Tests

```bash
cd Gold-Tier
python tests/test_secrets_manager.py
```

### Test Coverage

- ✅ Module imports
- ✅ Backend detection
- ✅ Environment variable access
- ✅ Default values
- ✅ Required secrets (exception handling)
- ✅ Secret existence checks
- ✅ Caching mechanism
- ✅ Convenience functions
- ✅ Security (secrets not logged)

---

## Troubleshooting

### Error: "Secret 'X' not found"

**Cause:** Secret not in .env file or secrets manager

**Solution:**
1. Check `.env` file exists and contains the key
2. Verify key name matches exactly (case-sensitive)
3. Run `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('KEY_NAME'))"`

### Error: "AWS Secrets Manager error"

**Cause:** AWS credentials not configured or secret doesn't exist

**Solution:**
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Check secret exists: `aws secretsmanager get-secret-value --secret-id ai-employee/prod`
3. Verify IAM permissions include `secretsmanager:GetSecretValue`

### Secrets Not Updating After Rotation

**Cause:** In-memory cache still has old values

**Solution:**
```python
from scripts.secrets_manager import clear_secrets_cache
clear_secrets_cache()
```

---

## Best Practices

### 1. Use Convenience Functions

```python
# Good
fb_creds = get_facebook_credentials()
app_id = fb_creds['app_id']

# Less good (but still works)
app_id = get_secret('FACEBOOK_APP_ID')
```

### 2. Handle Missing Optional Secrets

```python
# Good
feature_key = get_secret('BETA_FEATURE', required=False)
if feature_key:
    enable_beta_features()

# Bad (raises exception if missing)
feature_key = get_secret('BETA_FEATURE')
```

### 3. Clear Cache After Rotation

```python
# After rotating keys
rotate_api_keys()
clear_secrets_cache()  # Important!
```

### 4. Use Environment-Specific .env Files

```bash
# Development
.env.dev

# Staging
.env.staging

# Production (use secrets manager instead)
AWS_SECRETS_MANAGER_NAME=ai-employee/prod
```

---

## Security Checklist

- ✅ Secrets never logged to console or files
- ✅ Secrets cached in memory only (not disk)
- ✅ Multiple backend support for redundancy
- ✅ Graceful fallback to environment variables
- ✅ Exception handling for missing secrets
- ✅ Clear cache mechanism for rotation
- ✅ Type hints for better IDE support
- ✅ Comprehensive test coverage

---

## Next Steps

1. ✅ Implement secrets manager (DONE)
2. ⬜ Migrate all skills to use secrets manager
3. ⬜ Set up AWS Secrets Manager for production
4. ⬜ Rotate all API keys (see API-KEY-ROTATION-GUIDE.md)
5. ⬜ Enable MFA on all service accounts
6. ⬜ Set up API usage alerts

---

**Documentation Updated:** 2026-04-25  
**Maintainer:** AI Systems Engineer  
**Related:** API-KEY-ROTATION-GUIDE.md, AUDIT-1-COMPLETION-STATUS.md
