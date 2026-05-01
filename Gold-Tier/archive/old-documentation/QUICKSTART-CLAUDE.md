# QUICK START: Claude API Migration

## 🚀 3-Minute Setup

### Step 1: Install Package (30 seconds)
```bash
pip install anthropic
```

### Step 2: Get API Key (2 minutes)
1. Visit: https://console.anthropic.com/
2. Sign up/login
3. Click "API Keys"
4. Create new key
5. Copy it (starts with `sk-ant-`)

### Step 3: Update .env (30 seconds)
Open `Gold-Tier/.env` and replace:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

With your actual key:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### Step 4: Test It (30 seconds)
```bash
cd Gold-Tier
python test_claude_integration.py
```

Expected: All 5 tests pass ✓

### Step 5: Run System
```bash
python scripts/orchestrator.py --vault AI_Employee_Vault --once
```

## ✅ What Changed?

**Before (Qwen/Ollama):**
- ❌ Weekly usage limits
- ❌ Required local Ollama server
- ❌ Session limits blocking AI features

**After (Claude API):**
- ✅ No usage limits (scales with plan)
- ✅ Cloud-based (works anywhere)
- ✅ Better quality responses
- ✅ Faster and more reliable

## 💰 Cost

Typical usage:
- Email response: ~$0.006
- 1,000 emails/month: ~$6
- 10,000 emails/month: ~$60

Much cheaper than Ollama cloud upgrade!

## 📊 Monitor Usage

Dashboard: https://console.anthropic.com/
- View API calls
- Track costs
- Set billing alerts

## 🔧 Troubleshooting

**"ANTHROPIC_API_KEY not found"**
→ Add key to `.env` file

**"No module named 'anthropic'"**
→ Run: `pip install anthropic`

**"Authentication failed"**
→ Check key is correct at console.anthropic.com

**"Rate limit exceeded"**
→ Upgrade plan or add delays

## 📚 Full Documentation

- `CLAUDE-MIGRATION.md` - Complete migration guide
- `output2.txt` - Full issue resolution report
- `test_claude_integration.py` - Test suite

## 🎯 What Works Now

✅ Email response generation (Claude AI)
✅ Task planning (Claude AI)
✅ Email analysis (Claude AI)
✅ WhatsApp messaging (fixed)
✅ Orchestrator (all features)
⚠️ Instagram (needs token refresh - see output2.txt)

## 🚦 Quick Test Commands

```bash
# Test Claude API directly
python -c "from scripts.claude_ai_integration import call_claude; print(call_claude('Hello!'))"

# Test email generation
python -c "from skills.email_responder.service import EmailResponseService; s = EmailResponseService(); print(s.generate_response('test@example.com', 'Test', 'Hello'))"

# Test orchestrator
python scripts/orchestrator.py --vault AI_Employee_Vault --once
```

## ⚡ Automated Setup (Optional)

**Windows:**
```bash
setup_claude.bat
```

**Linux/Mac:**
```bash
chmod +x setup_claude.sh
./setup_claude.sh
```

## 🎉 You're Done!

The system now uses Claude API instead of Qwen/Ollama.

Just add your API key and start using it!

---

**Need help?** Check `CLAUDE-MIGRATION.md` for detailed docs.
