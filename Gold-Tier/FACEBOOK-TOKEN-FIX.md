# ⚠️  FACEBOOK TOKEN PERMISSION FIX NEEDED

## Error Message:
```
(#10) This endpoint requires the 'pages_read_engagement' permission
```

---

## 🔧 **QUICK FIX (5 minutes)**

### **Step 1: Go to Graph API Explorer**

Open: https://developers.facebook.com/tools/explorer/

---

### **Step 2: Select Your App**

- Dropdown at top → Select "AI Employee Social Media" (or your app name)

---

### **Step 3: Get New Token with Permissions**

1. Click **"Get Token"** → **"Get User Access Token"**

2. **Add these permissions:**
   - ✅ `pages_read_engagement`
   - ✅ `pages_read_user_content`
   - ✅ `pages_manage_posts`
   - ✅ `pages_manage_engagement`
   - ✅ `read_insights`

3. Click **"Generate Token"**

4. Login and **Approve** all permissions

---

### **Step 4: Copy New Token**

- Copy the new **User Access Token** (starts with `EAAB...`)

---

### **Step 5: Get New Page Token**

1. In Graph API Explorer, with your new User Token selected

2. In query box, enter: `me/accounts`

3. Click **"Submit"**

4. Copy the **`access_token`** for your "AI Employee" page

---

### **Step 6: Update .env File**

Edit `E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier\.env`

Replace:
```
FACEBOOK_USER_TOKEN=OLD_TOKEN_HERE
FACEBOOK_PAGE_TOKEN=OLD_PAGE_TOKEN_HERE
```

With new tokens:
```
FACEBOOK_USER_TOKEN=EAABw... (new long string)
FACEBOOK_PAGE_TOKEN=EAABw... (new long string)
```

---

### **Step 7: Test Again**

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

python scripts\test_facebook_credentials.py
```

---

## ✅ **EXPECTED RESULT**

```
✅ CREDENTIALS VALID!

Connected to Facebook Page:
  Name: AI Employee
  ID: 1012827638586192

Next steps:
  1. Facebook Watcher is ready to use
  2. Run: python scripts\facebook_watcher.py --vault AI_Employee_Vault
```

---

## 📚 **WHY THIS HAPPENS**

Facebook requires explicit permission for:
- Reading page engagement (comments, mentions)
- Reading page content
- Managing posts
- Managing engagement
- Reading insights (analytics)

**These permissions are NOT granted by default** - you must explicitly request them.

---

## 🆘 **STILL HAVING ISSUES?**

### **Problem: Can't add permissions**

**Solution:**
- Make sure you're an Admin of the Facebook Page
- Go to Page Settings → Page Access
- Ensure your user account has "Full Control"

### **Problem: Token expires immediately**

**Solution:**
- You're using a short-lived token
- Exchange for long-lived token:
  https://developers.facebook.com/tools/debug/access_token/

### **Problem: App in development mode**

**Solution:**
- This is OK for testing!
- Go to App Dashboard → App Review
- Toggle "Make public" (only for production)

---

**Once fixed, Facebook Watcher will work perfectly!** 🚀

*Facebook Token Fix Guide v1.0 | Gold Tier*
