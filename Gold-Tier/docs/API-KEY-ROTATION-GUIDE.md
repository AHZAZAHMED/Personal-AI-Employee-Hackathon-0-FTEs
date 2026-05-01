# API KEY ROTATION GUIDE - CRITICAL SECURITY

**Status:** 🔴 URGENT - MUST COMPLETE IMMEDIATELY  
**Date:** 2026-04-25  
**Reason:** Live API keys exposed in .env file (AUDIT-1 BLOCKER #1)

---

## ⚠️ IMMEDIATE ACTION REQUIRED

Your `.env` file contains **LIVE API KEYS IN PLAIN TEXT**. These must be rotated immediately to prevent unauthorized access.

**Estimated Time:** 2-3 hours  
**Priority:** 🔴 CRITICAL - Do this before any other work

---

## 📋 ROTATION CHECKLIST

### Phase 1: Facebook/Meta (30 minutes)

**Services Affected:** facebook_posting, facebook_watcher, instagram_posting, instagram_watcher

1. **Rotate Facebook App Secret**
   - Go to: https://developers.facebook.com/apps/
   - Select your app (ID: 1269171781225024)
   - Navigate to: Settings > Basic
   - Click "Reset App Secret"
   - Copy new secret to temporary secure location
   - Update `.env`: `FACEBOOK_APP_SECRET=<new_secret>`

2. **Regenerate Facebook Access Tokens**
   - Go to: https://developers.facebook.com/tools/explorer/
   - Select your app
   - Click "Generate Access Token"
   - Select permissions: `pages_manage_posts`, `pages_read_engagement`
   - Copy new tokens
   - Update `.env`:
     - `FACEBOOK_USER_TOKEN=<new_token>`
     - `FACEBOOK_PAGE_TOKEN=<new_token>`

3. **Regenerate Instagram Access Token**
   - Same process as Facebook (Instagram uses Facebook Graph API)
   - Update `.env`: `INSTAGRAM_USER_TOKEN=<new_token>`

4. **Test Facebook/Instagram Skills**
   ```bash
   python skills/facebook_posting/test_skill.py
   python skills/instagram_posting/test_skill.py
   ```

---

### Phase 2: Twitter/X (20 minutes)

**Services Affected:** twitter_posting

1. **Regenerate Twitter API Keys**
   - Go to: https://developer.twitter.com/en/portal/dashboard
   - Select your app
   - Navigate to: Keys and tokens
   - Click "Regenerate" for:
     - API Key and Secret
     - Access Token and Secret
     - Bearer Token
   - Copy all new credentials

2. **Update .env**
   ```bash
   TWITTER_API_KEY=<new_key>
   TWITTER_API_SECRET=<new_secret>
   TWITTER_ACCESS_TOKEN=<new_token>
   TWITTER_ACCESS_SECRET=<new_secret>
   BEARER_TOKEN=<new_bearer>
   CLIENT_ID=<new_client_id>
   CLIENT_SECRET=<new_client_secret>
   SECRET_KEY=<new_secret_key>
   ```

3. **Test Twitter Skill**
   ```bash
   python skills/twitter_posting/test_skill.py
   ```

---

### Phase 3: Twilio (15 minutes)

**Services Affected:** whatsapp, whatsapp_watcher

1. **Rotate Twilio Auth Token**
   - Go to: https://console.twilio.com/
   - Navigate to: Account > API keys & tokens
   - Click "Create new Auth Token"
   - Copy new token
   - **IMPORTANT:** Old token will be invalidated immediately
   - Update `.env`: `TWILIO_AUTH_TOKEN=<new_token>`

2. **Test WhatsApp Skill**
   ```bash
   python skills/whatsapp/test_skill.py
   ```

---

### Phase 4: Neon Database (20 minutes)

**Services Affected:** whatsapp_watcher (message storage)

1. **Reset Neon Database Password**
   - Go to: https://console.neon.tech/
   - Select your project
   - Navigate to: Settings > Reset password
   - Copy new password
   - Update connection string in `.env`:
     ```
     NEON_DATABASE_URL=postgresql://user:<new_password>@host.neon.tech/dbname?sslmode=require
     ```

2. **Test Database Connection**
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); import psycopg2; conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL')); print('✅ Database connection successful'); conn.close()"
   ```

---

### Phase 5: Google Gemini (10 minutes)

**Services Affected:** AI response generation (primary)

1. **Regenerate Gemini API Key**
   - Go to: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy new key
   - **Delete old key** from the console
   - Update `.env`: `GEMINI_API_KEY=<new_key>`

2. **Test Gemini Integration**
   ```bash
   python scripts/claude_ai_integration.py --test-gemini
   ```

---

### Phase 6: Anthropic Claude (10 minutes)

**Services Affected:** AI response generation (fallback)

1. **Regenerate Claude API Key**
   - Go to: https://console.anthropic.com/settings/keys
   - Click "Create Key"
   - Copy new key
   - **Delete old key** from the console
   - Update `.env`: `ANTHROPIC_API_KEY=<new_key>`

2. **Test Claude Integration**
   ```bash
   python scripts/claude_ai_integration.py --test-claude
   ```

---

### Phase 7: Gmail API (15 minutes)

**Services Affected:** gmail_watcher, email_responder

1. **Revoke and Regenerate OAuth Token**
   ```bash
   # Delete existing token
   rm AI_Employee_Vault/.gmail_token.json
   
   # Re-authenticate (will open browser)
   python scripts/authenticate-gmail.py
   ```

2. **Test Gmail Connection**
   ```bash
   python skills/gmail_watcher/test_skill.py
   ```

---

### Phase 8: LinkedIn (10 minutes)

**Services Affected:** linkedin_posting

1. **Change LinkedIn Password**
   - Go to: https://www.linkedin.com/mypreferences/d/change-password
   - Change password
   - Update `.env`: `LINKEDIN_PASSWORD=<new_password>`

2. **Test LinkedIn Skill**
   ```bash
   python skills/linkedin_posting/test_skill.py
   ```

---

## 🔒 POST-ROTATION SECURITY CHECKLIST

After rotating all keys, complete these steps:

### 1. Verify .env is Gitignored
```bash
git check-ignore .env
# Should output: .env
```

### 2. Check Git History for Leaked Secrets
```bash
git log --all --full-history -- .env
# Should be empty (no commits)
```

### 3. Set Restrictive File Permissions
```bash
chmod 600 .env
# Only owner can read/write
```

### 4. Test All Skills End-to-End
```bash
python tests/test_all_skills.py
```

### 5. Update Secrets Manager (if using)
If you're using AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault:
```bash
# Example for AWS Secrets Manager
aws secretsmanager update-secret --secret-id ai-employee/prod --secret-string file://.env
```

### 6. Document Rotation in Audit Log
```bash
echo "$(date): All API keys rotated - AUDIT-1 BLOCKER #1 addressed" >> AI_Employee_Vault/Logs/security_audit.log
```

---

## 🚨 IF KEYS WERE ALREADY COMMITTED TO GIT

If you accidentally committed `.env` with real secrets to git history:

### Option 1: BFG Repo-Cleaner (Recommended)
```bash
# Install BFG
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Remove .env from history
java -jar bfg.jar --delete-files .env

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: Destructive)
git push --force --all
```

### Option 2: Git Filter-Branch
```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch Gold-Tier/.env" \
  --prune-empty --tag-name-filter cat -- --all

git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force --all
```

### After Cleaning Git History
1. ✅ Rotate ALL keys immediately (they're compromised)
2. ✅ Notify team members to re-clone the repository
3. ✅ Check GitHub/GitLab for cached versions
4. ✅ Monitor API usage for unauthorized access

---

## 📊 ROTATION VERIFICATION

After completing all rotations, verify:

| Service | Old Key Deleted? | New Key Working? | Skill Tested? |
|---------|------------------|------------------|---------------|
| Facebook | ⬜ | ⬜ | ⬜ |
| Instagram | ⬜ | ⬜ | ⬜ |
| Twitter | ⬜ | ⬜ | ⬜ |
| Twilio | ⬜ | ⬜ | ⬜ |
| Neon DB | ⬜ | ⬜ | ⬜ |
| Gemini | ⬜ | ⬜ | ⬜ |
| Claude | ⬜ | ⬜ | ⬜ |
| Gmail | ⬜ | ⬜ | ⬜ |
| LinkedIn | ⬜ | ⬜ | ⬜ |

---

## 🎯 NEXT STEPS AFTER ROTATION

Once all keys are rotated:

1. ✅ Implement secrets manager (Task #21)
2. ✅ Set up secret scanning in CI/CD
3. ✅ Enable MFA on all service accounts
4. ✅ Set up API usage alerts
5. ✅ Schedule quarterly key rotation

---

## 📞 EMERGENCY CONTACTS

If you suspect unauthorized API usage:

- **Facebook:** https://developers.facebook.com/support/
- **Twitter:** https://help.twitter.com/en/forms/platform
- **Twilio:** https://www.twilio.com/help/contact
- **Neon:** https://neon.tech/docs/introduction/support
- **Google:** https://support.google.com/
- **Anthropic:** support@anthropic.com

---

**Rotation Started:** ___________  
**Rotation Completed:** ___________  
**Verified By:** ___________  
**Next Rotation Due:** ___________ (recommended: 90 days)
