# Instagram Integration Setup Guide

**Complete guide to set up Instagram Business Account**

---

## 📋 **GOOD NEWS: SAME FACEBOOK CREDENTIALS!**

Instagram uses the **same Facebook credentials** you already configured! No new API keys needed!

---

## ✅ **PREREQUISITES**

| Item | Status | Details |
|------|--------|---------|
| Facebook App | ✅ Already configured | From Facebook integration |
| Facebook Page | ✅ Already configured | "AI Employee" Page |
| Facebook Credentials | ✅ Already in .env | Same credentials |
| Instagram Account | ⏳ Need Business Account | Free conversion |
| Instagram Linked to FB | ⏳ Need to link | 5 minute setup |

---

## 📱 **STEP 1: CONVERT TO BUSINESS ACCOUNT** (2 minutes)

### **On Instagram Mobile App:**

1. **Open Instagram app** on your phone
2. **Go to your profile**
3. **Tap Menu** (☰ three lines, top right)
4. **Tap "Settings and privacy"**
5. **Scroll down** → Tap "Account type and tools"
6. **Tap "Switch to professional account"**
7. **Tap "Continue"** through the prompts
8. **Select "Business"** (not Creator)
9. **Tap "Done"**

**✅ Done! Your account is now a Business Account!**

---

## 🔗 **STEP 2: LINK INSTAGRAM TO FACEBOOK PAGE** (5 minutes)

### **Option A: Link from Instagram App (Easiest)**

1. **Instagram Settings** → **"Linked Accounts"**
2. **Tap "Facebook"**
3. **Login to Facebook** (if prompted)
4. **Select your "AI Employee" Facebook Page**
5. **Tap "Done"**

### **Option B: Link from Facebook Page**

1. **Go to your Facebook Page:** https://www.facebook.com/
2. **Click "Settings"** (top right)
3. **Click "Linked Accounts"** (left menu)
4. **Click "Instagram"**
5. **Click "Connect Account"**
6. **Login to Instagram** (if prompted)
7. **Confirm connection**

---

## 🧪 **STEP 3: TEST CONNECTION**

### **Run Test Script:**

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

python scripts\test_instagram_credentials.py
```

### **Expected Output:**

```
============================================================
INSTAGRAM CREDENTIALS TEST
============================================================

Step 1: Connecting to Instagram...
✅ Connected!

Step 2: Getting Instagram account information...
============================================================
✅ INSTAGRAM CONNECTED SUCCESSFULLY!
============================================================

Instagram Business Account:
  Username: @YourUsername
  Followers: XXX
  Following: XXX
  Posts: XXX
  Bio: Your bio text
  Website: your-website.com

Next steps:
  1. Instagram Watcher is ready to use
  2. Run: python scripts\instagram_watcher.py --vault AI_Employee_Vault
  3. Test posting: python scripts\test_instagram_post.py
```

---

## 📸 **STEP 4: TEST POSTING**

### **Post Test Image:**

```bash
python scripts\test_instagram_post.py
```

### **Expected Output:**

```
============================================================
INSTAGRAM POSTING TEST
============================================================

Step 1: Connecting to Instagram...
✅ Connected to @YourUsername

Step 2: Creating test post...

Image URL: https://images.unsplash.com/...
Caption: 🤖 AI Employee Test Post...

Posting to Instagram...
(This may take 10-20 seconds)

✅ IMAGE POSTED SUCCESSFULLY!

Post ID: 1234567890123456789
Caption: 🤖 AI Employee Test Post...

View your post:
https://www.instagram.com/YourUsername/

Note: It may take a few minutes for the post to appear on your profile.
```

---

## 🆘 **TROUBLESHOOTING**

### **Problem: "Instagram Business Account not linked"**

**Solution:**
1. Make sure you converted to Business Account (Step 1)
2. Make sure Instagram is linked to Facebook Page (Step 2)
3. Wait 5 minutes after linking, then try again

### **Problem: "No Instagram Business Account linked to this Facebook Page"**

**Solution:**
1. Go to Facebook Page Settings
2. Click "Linked Accounts" → "Instagram"
3. Click "Connect Account"
4. Login to Instagram and confirm

### **Problem: "Post failed - Image URL must be publicly accessible"**

**Solution:**
- Image URL must be on public server (not localhost)
- Use Unsplash, Imgur, or your own website
- Image must be JPG or PNG format

### **Problem: "Insufficient permissions"**

**Solution:**
1. Go to Facebook Developer Portal
2. Select your app
3. Add "instagram_content_publish" permission
4. Regenerate Page Access Token
5. Update .env file

---

## 📊 **INSTAGRAM API LIMITS**

| Action | Limit | Your Usage |
|--------|-------|------------|
| **Posts per day** | 25 | ~5-10 |
| **Comments per day** | 500 | ~50 |
| **API calls per hour** | 200 | ~60 |

**Free tier is MORE than enough for hackathon!**

---

## 📋 **SETUP CHECKLIST**

- [ ] Instagram account exists
- [ ] Converted to Business Account (Step 1)
- [ ] Linked to Facebook Page (Step 2)
- [ ] Test credentials script passes
- [ ] Test post script works
- [ ] Instagram Watcher runs successfully

---

## 🎯 **WHAT INSTAGRAM INTEGRATION DOES**

### **Monitoring:**
- ✅ Track comments on your posts
- ✅ Monitor mentions (tagged media)
- ✅ Create action files for responses
- ✅ Track engagement metrics

### **Posting:**
- ✅ Post images with captions
- ✅ Post carousel (multiple images)
- ✅ Auto-publish (with approval workflow)
- ✅ Track post performance

### **Analytics:**
- ✅ Impressions (how many saw your post)
- ✅ Reach (unique viewers)
- ✅ Engagement (likes, comments, saves)
- ✅ Follower growth

---

## 🚀 **NEXT STEPS**

Once Instagram is set up:

1. ✅ Run Instagram Watcher
2. ✅ Monitor comments and mentions
3. ✅ Post images automatically
4. ✅ Track engagement metrics
5. ✅ Generate Instagram reports

---

## 📚 **INSTAGRAM VS FACEBOOK**

| Feature | Facebook | Instagram |
|---------|----------|-----------|
| **Credentials** | Same | Same ✅ |
| **API** | Graph API | Graph API ✅ |
| **Posting** | Text + Images | Images only |
| **Monitoring** | Posts, Comments | Comments, Mentions |
| **Setup Time** | 20 min | 7 min (after FB) |

---

**Instagram integration uses the SAME Facebook credentials - no new API setup needed!** 🎉

*Instagram Integration Setup Guide v1.0 | Gold Tier | AI Employee Hackathon 0*
