# LinkedIn Poster - Playwright Chromium Setup

## Quick Setup (5 minutes)

### Step 1: Install Playwright

```bash
# Install Playwright Python library
pip install playwright

# Install Chromium browser (this downloads ~100MB)
playwright install chromium

# (Optional) Install system dependencies on Linux
# playwright install-deps
```

### Step 2: First-Time LinkedIn Login

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs

# Open LinkedIn in visible browser for login
python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only
```

**What happens:**
- Browser window opens
- Navigate to LinkedIn
- Log in with your credentials
- Session is saved to `linkedin_browser_session/` folder
- Press `Ctrl+C` to close after logging in

### Step 3: Test Posting (Headless Mode)

```bash
# Create a test post
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "Testing automated LinkedIn posting! #Test #Automation" ^
  --type announcement

# Approve the post (move from Pending_Approval to Approved)
move AI_Employee_Vault\Pending_Approval\LINKEDIN_*.md AI_Employee_Vault\Approved\

# Execute the post (headless - no browser window shown)
python scripts\linkedin_poster.py --vault AI_Employee_Vault
```

---

## Usage Examples

### Create and Post in One Flow

```bash
# 1. Create post draft
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "🎉 Excited to announce our Q1 2026 growth! #business #milestone" ^
  --type milestone

# 2. Review the draft
type AI_Employee_Vault\Pending_Approval\LINKEDIN_*.md

# 3. Approve (move to Approved folder)
move AI_Employee_Vault\Pending_Approval\LINKEDIN_*.md AI_Employee_Vault\Approved\

# 4. Post (headless mode - invisible)
python scripts\linkedin_poster.py --vault AI_Employee_Vault

# OR post with visible browser window
python scripts\linkedin_poster.py --vault AI_Employee_Vault --visible
```

### Post Types

```bash
# Milestone post
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "Reached 1000 followers! Thank you all! #milestone" ^
  --type milestone

# Client win post
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "Welcome ABC Corp as our newest client! #clientwin" ^
  --type client_win

# Business update
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "New AI Employee features released! Check them out. #update" ^
  --type update

# General announcement
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "Exciting news coming soon! Stay tuned. #announcement" ^
  --type announcement
```

---

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--vault` | Path to Obsidian vault | `--vault AI_Employee_Vault` |
| `--create "text"` | Create post draft with content | `--create "Hello world"` |
| `--type` | Post type | `--type milestone` |
| `--visible` | Show browser window | `--visible` |
| `--login-only` | Just open LinkedIn for login | `--login-only` |

**Post Types:**
- `announcement` (default)
- `milestone`
- `update`
- `client_win`

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│        LINKEDIN POSTING - PLAYWRIGHT DIRECT                  │
└─────────────────────────────────────────────────────────────┘

1. python scripts\linkedin_poster.py
   │
2. Load approved posts from /Approved/
   │
3. For each post:
   │   ├── Launch Chromium with saved session
   │   ├── Navigate to LinkedIn (auto-login)
   │   ├── Click "Start a post"
   │   ├── Type content
   │   ├── Click "Post" button
   │   ├── Take screenshot
   │   └── Close browser
   │
4. Save execution result to /Done/
   │
5. Log to /Logs/YYYY-MM-DD.jsonl
```

---

## Browser Session Management

### Where Sessions Are Stored

```
E:\Personal-AI-Employee-Hackathon-0-FTEs\linkedin_browser_session\
```

This folder contains:
- Cookies (including LinkedIn login)
- Local storage
- Browser preferences

### Backup Session

```bash
# Backup session
xcopy /E /I linkedin_browser_session linkedin_browser_session_backup
```

### Clear Session (Force Re-login)

```bash
# Delete session and re-login
rmdir /S /Q linkedin_browser_session
mkdir linkedin_browser_session

# Then login again
python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only
```

---

## Troubleshooting

### Problem: "Playwright not installed"

```bash
# Install Playwright
pip install playwright
playwright install chromium
```

### Problem: "Browser doesn't close" or "Hangs"

```bash
# Kill any stuck Python processes
taskkill /F /IM python.exe
```

### Problem: "Not logged in" or "Login page appears"

```bash
# Re-login to LinkedIn
python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only

# Log in manually in the browser window
# Wait for feed to load
# Press Ctrl+C to save session
```

### Problem: "Post button not found"

LinkedIn's UI may have changed. Try:
1. Update the selectors in `linkedin_poster.py`
2. Or run with `--visible` to see what's happening

```bash
python scripts\linkedin_poster.py --vault AI_Employee_Vault --visible
```

### Problem: "Content not typed correctly"

Some special characters may not work. Try:
- Remove emojis
- Use simple ASCII text
- Keep posts under 1000 characters

---

## Headless vs Visible Mode

### Headless Mode (Default)
```bash
# No browser window shown - runs in background
python scripts\linkedin_poster.py --vault AI_Employee_Vault
```

**Use for:**
- Production posting
- Scheduled tasks
- When you trust the automation

### Visible Mode
```bash
# Browser window shown - you can see what's happening
python scripts\linkedin_poster.py --vault AI_Employee_Vault --visible
```

**Use for:**
- Debugging
- First-time testing
- When you want to monitor the process

---

## Best Practices

1. **Login once, save session** - Use `--login-only` first time
2. **Test with visible mode** - Before running headless
3. **Review before approving** - Always check content in Approved folder
4. **Post during business hours** - 9 AM - 5 PM for best engagement
5. **Keep sessions secure** - Don't share `linkedin_browser_session/` folder
6. **Check screenshots** - Verify posts in `/Screenshots/`

---

## Quick Reference

```bash
# Setup (first time only)
pip install playwright
playwright install chromium
python scripts\linkedin_poster.py --vault AI_Employee_Vault --login-only

# Create post
python scripts\linkedin_poster.py --vault AI_Employee_Vault ^
  --create "Your post content here" --type announcement

# Approve post
move AI_Employee_Vault\Pending_Approval\*.md AI_Employee_Vault\Approved\

# Execute post
python scripts\linkedin_poster.py --vault AI_Employee_Vault

# View results
dir AI_Employee_Vault\Done\
dir AI_Employee_Vault\Screenshots\
```

---

*AI Employee LinkedIn Poster v0.3.0 | Playwright Direct | Silver Tier*
