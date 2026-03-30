# Facebook Integration Setup Guide

**Complete guide to get Facebook API credentials**

---

## 📋 **PREREQUISITES**

| Item | Status | Details |
|------|--------|---------|
| Facebook Account | ✅ Required | Your personal account |
| Facebook Page | ✅ Required | Business page for posting |
| Email | ✅ Required | For Facebook Developer account |
| Phone | ✅ Required | For 2FA (optional but recommended) |

---

## 🔑 **STEP 1: CREATE FACEBOOK DEVELOPER ACCOUNT**

### **1.1 Go to Facebook Developers**

1. Open: https://developers.facebook.com/
2. Click **"Get Started"** or **"Log In"**
3. Login with your Facebook account
4. Accept Developer Terms

### **1.2 Verify Your Account**

Facebook may ask for:
- ✅ Phone number verification
- ✅ Email verification

**This is normal security procedure.**

---

## 📱 **STEP 2: CREATE FACEBOOK PAGE (If You Don't Have One)**

### **2.1 Create New Page**

1. Go to: https://www.facebook.com/pages/creation
2. Fill in:
   - **Page Name:** Your Business Name
   - **Category:** Business/Company
   - **Description:** Brief description
3. Click **"Create Page"**

### **2.2 Add Page Details**

- Profile picture (optional)
- Cover photo (optional)
- Business info (optional)

**Time:** 5 minutes

---

## 🔧 **STEP 3: CREATE FACEBOOK APP**

### **3.1 Create App**

1. Go to: https://developers.facebook.com/apps/
2. Click **"Create App"**
3. Select use case: **"Other"** → **"Next"**
4. Select app type: **"Business"** → **"Next"**
5. Fill in:
   - **App Name:** AI Employee Social Media
   - **App Contact Email:** your-email@gmail.com
   - **Business Account:** Select or create
6. Click **"Create App"**

### **3.2 Add Facebook Login Product**

1. In your app dashboard, find **"Add Product"**
2. Find **"Facebook Login"**
3. Click **"Set Up"**
4. Select **"Web"**
5. Set:
   - **Site URL:** http://localhost:8080 (for testing)
   - **OAuth Redirect URI:** http://localhost:8080/fb-callback
6. Click **"Save"**

### **3.3 Add Pages Management Product**

1. Click **"Add Product"** again
2. Find **"Pages"**
3. Click **"Set Up"**
4. This enables Page posting

---

## 🔑 **STEP 4: GET APP CREDENTIALS**

### **4.1 Get App ID and App Secret**

1. Go to your app dashboard
2. Click **"Settings"** → **"Basic"**
3. You'll see:
   - **App ID:** `1234567890123456` (yours will be different)
   - **App Secret:** `abcdef1234567890abcdef1234567890` (click "Show")

**⚠️ COPY THESE SECURELY!**

### **4.2 Store Credentials**

Create file: `E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier\.facebook_credentials.env`

```
# Facebook App Credentials
# KEEP THIS FILE SECRET - NEVER COMMIT TO GIT

FACEBOOK_APP_ID=1234567890123456
FACEBOOK_APP_SECRET=abcdef1234567890abcdef1234567890
FACEBOOK_PAGE_ID=987654321098765
```

**⚠️ This file is already in .gitignore - don't share it!**

---

## 🔐 **STEP 5: GET ACCESS TOKENS**

### **5.1 Get User Access Token**

1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app from dropdown
3. Click **"Get Token"** → **"Get User Access Token"**
4. Select permissions:
   - ✅ `pages_read_engagement`
   - ✅ `pages_read_user_content`
   - ✅ `pages_manage_posts`
   - ✅ `pages_manage_engagement`
5. Click **"Generate Token"**
6. Login and approve permissions
7. **Copy the generated token**

### **5.2 Get Page Access Token**

1. In Graph API Explorer, with your User Token selected
2. In query box, enter: `me/accounts`
3. Click **"Submit"**
4. You'll see your pages with tokens
5. **Copy the `access_token` for your page**

### **5.3 Store Tokens**

Add to `.facebook_credentials.env`:

```
# Access Tokens
FACEBOOK_USER_TOKEN=EAAB... (long string)
FACEBOOK_PAGE_TOKEN=EAAB... (long string)
```

---

## ⚙️ **STEP 6: TEST CREDENTIALS**

### **6.1 Run Test Script**

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

python scripts\test_facebook_credentials.py
```

**Expected Output:**
```
✅ App ID: Valid
✅ App Secret: Valid
✅ User Token: Valid
✅ Page Token: Valid
✅ Page Name: Your Business Page
```

---

## 🔒 **SECURITY BEST PRACTICES**

### **Do's:**
- ✅ Store credentials in `.env` file
- ✅ Add `.env` to `.gitignore`
- ✅ Use separate tokens for development/production
- ✅ Rotate tokens every 90 days

### **Don'ts:**
- ❌ Never commit `.env` to Git
- ❌ Never share App Secret publicly
- ❌ Never hardcode tokens in code
- ❌ Never use production tokens in development

---

## 📊 **TOKEN EXPIRY**

| Token Type | Expires | Refresh |
|------------|---------|---------|
| **User Token** | 60 days | Re-generate via Graph Explorer |
| **Page Token** | Never* | *If User Token is valid |
| **App Secret** | Never | Only if compromised |

**Recommendation:** Set calendar reminder to refresh tokens every 45 days.

---

## 🆘 **TROUBLESHOOTING**

### **Problem: Can't create Facebook Developer account**

**Solution:**
- Use a different Facebook account
- Complete all profile verification steps
- Wait 24 hours and try again

### **Problem: Can't create Facebook Page**

**Solution:**
- Personal accounts can create Pages
- Use business name even for testing
- Minimum: Just page name, no other details required

### **Problem: App review required**

**Solution:**
- For development/testing: Use "Development Mode"
- For production: Submit app for review (takes 3-7 days)
- For hackathon: Development mode is sufficient

### **Problem: Token expired**

**Solution:**
1. Go to Graph API Explorer
2. Generate new token
3. Update `.facebook_credentials.env`
4. Restart your script

---

## 📋 **CHECKLIST**

Before proceeding with Facebook integration:

- [ ] Facebook Developer account created
- [ ] Facebook Page created (or test page)
- [ ] Facebook App created
- [ ] App ID copied to `.facebook_credentials.env`
- [ ] App Secret copied to `.facebook_credentials.env`
- [ ] User Access Token generated
- [ ] Page Access Token generated
- [ ] Tokens saved to `.facebook_credentials.env`
- [ ] Test script runs successfully

---

## 🎯 **NEXT STEPS**

Once you have all credentials:

1. ✅ Run test script to verify
2. ✅ Facebook Watcher will monitor mentions
3. ✅ Facebook Poster will auto-post updates
4. ✅ Facebook Summary will generate reports

---

**Need help with any step? Let me know which step you're on!**

*Facebook Integration Setup Guide v1.0 | Gold Tier | AI Employee Hackathon 0*
