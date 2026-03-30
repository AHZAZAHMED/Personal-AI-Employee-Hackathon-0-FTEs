# Twitter/X Integration Setup Guide

**Complete guide to get Twitter API credentials**

---

## 📋 **PREREQUISITES**

| Item | Status | Details |
|------|--------|---------|
| Twitter Account | ✅ Required | Personal or business account |
| Phone Number | ✅ Required | For verification |
| Email | ✅ Required | Verified email |

---

## 🔑 **STEP 1: CREATE TWITTER DEVELOPER ACCOUNT**

### **1.1 Go to Twitter Developer Portal**

1. Open: https://developer.twitter.com/
2. Click **"Sign In"** (top right)
3. Login with your Twitter account
4. Click **"Apply for a developer account"**

### **1.2 Choose Account Type**

Select: **"Hobbyist"** (free, perfect for testing)

- ✅ Free
- ✅ No credit card required
- ✅ Enough for hackathon

### **1.3 Fill Application**

**Use case description:**
```
I'm building an AI Employee system for a hackathon project. 
I need Twitter API to:
1. Monitor mentions of my business
2. Post business updates automatically
3. Track engagement and analytics

This is for educational/personal project use.
```

**Country:** Select your country  
**Agree to terms:** Check the box  
**Submit:** Click "Submit"

### **1.4 Verify Your Account**

Twitter will send:
- ✅ SMS verification code (to your phone)
- ✅ Email verification (confirm your email)

**Enter codes and verify.**

---

## 🔧 **STEP 2: CREATE TWITTER APP**

### **2.1 Create Project**

1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Click **"Create Project"**
3. Fill in:
   - **Project name:** AI Employee Social Media
   - **Description:** AI-powered employee automation system
   - **Use case:** Select "Posting tweets" and "Reading tweets"
4. Click **"Next"**

### **2.2 Create App**

1. Click **"Create App"**
2. App name: AI Employee Bot
3. Click **"Next"**

### **2.3 Get Credentials**

You'll see your credentials:

| Credential | Copy This | Save To |
|------------|-----------|---------|
| **API Key** | Click "Copy" | `.env` file |
| **API Secret** | Click "Copy" | `.env` file |
| **Bearer Token** | Click "Copy" | Not needed |
| **Access Token** | Click "Generate" | `.env` file |
| **Access Secret** | Click "Generate" | `.env` file |

**⚠️ SAVE THESE SECURELY!**

---

## 📱 **STEP 3: GET ACCESS TOKENS**

### **3.1 Generate Access Token**

1. In your app dashboard
2. Go to **"Keys and tokens"**
3. Under "Authentication Tokens":
   - Click **"Generate"** for Access Token
   - Click **"Generate"** for Access Token Secret

### **3.2 Copy All Credentials**

You need 4 values:
```
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
```

---

## ⚙️ **STEP 4: CONFIGURE APP PERMISSIONS**

### **4.1 Set Permissions**

1. Go to **"Keys and tokens"**
2. Under "Permissions":
   - Select **"Read and Write"**
   - Click **"Save"**

### **4.2 Enable Additional Features**

1. Go to **"Additional permissions"**
2. Enable:
   - ✅ **Tweet** (post tweets)
   - ✅ **Tweet.read** (read tweets)
   - ✅ **Users.read** (read user info)
   - ✅ **Follows.read** (read followers)
   - ✅ **Offline.access** (refresh tokens)

---

## 🔐 **STEP 5: STORE CREDENTIALS**

### **5.1 Create .env Entry**

Edit file: `E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier\.env`

Add:
```
# Twitter API Credentials
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
```

### **5.2 Security**

- ✅ `.env` is in `.gitignore` (never committed)
- ✅ Keep credentials private
- ✅ Don't share screenshots with credentials

---

## 🧪 **STEP 6: TEST CREDENTIALS**

### **6.1 Run Test Script**

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

python scripts\test_twitter_credentials.py
```

### **6.2 Expected Output**

```
============================================================
TWITTER CREDENTIALS TEST
============================================================

✅ API Key: Valid
✅ API Secret: Valid
✅ Access Token: Valid
✅ Access Secret: Valid

✅ CREDENTIALS VALID!

Connected to Twitter:
  Username: @YourUsername
  User ID: 123456789
  Followers: XXX

Next steps:
  1. Twitter Watcher is ready to use
  2. Run: python scripts\twitter_watcher.py --vault AI_Employee_Vault
```

---

## 🚀 **STEP 7: TEST TWEET POSTING**

### **7.1 Post Test Tweet**

```bash
python scripts\test_twitter_post.py
```

### **7.2 Expected Output**

```
✅ TWEET POSTED SUCCESSFULLY!

Tweet ID: 1234567890123456789
Text: 🤖 AI Employee Test Tweet...

View your tweet:
https://twitter.com/YourUsername/status/1234567890123456789
```

---

## 📊 **TWITTER API LIMITS (Free Tier)**

| Action | Limit | Your Usage |
|--------|-------|------------|
| **Tweets per day** | 2,400 | ~10-50 |
| **Read tweets** | 500/hour | ~60/hour |
| **Follows** | 400/day | ~10/day |
| **Likes** | 1,000/day | ~20/day |

**Free tier is MORE than enough for hackathon!**

---

## 🆘 **TROUBLESHOOTING**

### **Problem: Developer account rejected**

**Solution:**
- Use personal account (not business)
- Fill use case description clearly
- Mention it's for education/hackathon
- Wait 24 hours and reapply

### **Problem: Can't create app**

**Solution:**
- Complete developer profile first
- Verify phone number
- Verify email address
- Wait for account approval

### **Problem: 401 Unauthorized**

**Solution:**
- Check all 4 credentials are correct
- No extra spaces in .env file
- Regenerate tokens if needed

### **Problem: Rate limit exceeded**

**Solution:**
- Free tier has limits
- Wait 15 minutes
- Reduce check frequency

---

## 📋 **CHECKLIST**

Before proceeding:

- [ ] Twitter account created
- [ ] Developer account approved
- [ ] Project created
- [ ] App created
- [ ] API Key copied to .env
- [ ] API Secret copied to .env
- [ ] Access Token copied to .env
- [ ] Access Secret copied to .env
- [ ] Permissions set to "Read and Write"
- [ ] Test script runs successfully

---

## 🎯 **NEXT STEPS**

Once credentials are ready:

1. ✅ Run test script to verify
2. ✅ Twitter Watcher will monitor mentions
3. ✅ Twitter Poster will auto-post updates
4. ✅ Twitter Summary will generate reports

---

**Need help with any step? Let me know!**

*Twitter Integration Setup Guide v1.0 | Gold Tier | AI Employee Hackathon 0*
