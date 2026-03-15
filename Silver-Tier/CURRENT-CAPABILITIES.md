# AI Employee - Current Capabilities vs Roadmap

## ✅ Currently Working (Bronze Tier)

### Gmail Watcher
- ✅ Connects to Gmail API
- ✅ Detects new unread emails
- ✅ Creates action files in `/Needs_Action/`
- ✅ Detects urgent keywords (invoice, payment, asap)
- ✅ Avoids processing duplicates
- ✅ Saves authentication token

### File System Watcher
- ✅ Monitors folder for new files
- ✅ Creates action files for dropped files
- ✅ Moves files to Inbox
- ✅ Avoids duplicates

### Orchestrator
- ✅ Moves files: Needs_Action → In_Progress → Done
- ✅ Categorizes content (Finance, Schedule, Test, General, etc.)
- ✅ Updates Dashboard.md with stats
- ✅ Logs all actions to `/Logs/`

### LinkedIn Poster
- ⚠️ Partially working - can navigate to LinkedIn
- ⚠️ Can detect "Start a post" button
- ❌ Cannot find contenteditable div (needs debugging)

---

## ❌ NOT Yet Implemented (Silver Tier)

### Email Response System
- ❌ **Does NOT send automatic email replies**
- ❌ **Does NOT draft responses**
- ❌ **Does NOT check if sender is approved contact**

**What's needed:**
1. Email MCP server integration
2. Approved contacts list
3. Email draft generation
4. Send email after approval

### Approval Workflow
- ❌ **Does NOT create approval requests**
- ❌ **Does NOT check /Approved/ folder**
- ❌ **Does NOT execute approved actions**

**What's needed:**
1. Create approval request files for important emails
2. Human moves file to /Approved/ or /Rejected/
3. Execute approved actions automatically
4. Log approval decisions

### Plan.md Generation
- ❌ **Does NOT create detailed plans**
- ❌ **Does NOT track multi-step tasks**

**What's needed:**
1. Create Plan.md for complex tasks
2. Track step completion
3. Update plan with progress

---

## Current Flow (What Happens Now)

```
1. Gmail receives email
   ↓
2. Gmail Watcher creates action file in /Needs_Action/
   ↓
3. Orchestrator runs
   ↓
4. Reads email, categorizes it (Finance, General, etc.)
   ↓
5. Adds analysis summary
   ↓
6. Moves to /Done/
   ↓
7. NO email sent, NO approval requested
```

**Example:**
```
Email: "Invoice payment due"
↓
Action file created
↓
Categorized as "Finance"
↓
Moved to Done with summary
↓
❌ NO reply sent
❌ NO approval requested
```

---

## Desired Flow (Silver Tier)

```
1. Gmail receives email
   ↓
2. Gmail Watcher creates action file
   ↓
3. Orchestrator runs
   ↓
4. Reads email, checks Company Handbook
   ↓
5. DECISION:
   
   If reply needed AND sender is approved contact:
      → Draft reply
      → Create approval request
      → Wait for human approval
      → Send email via MCP
      → Move to Done
   
   If payment/invoice detected:
      → Create approval request
      → Wait for human approval
      → Execute payment
      → Move to Done
   
   If general email:
      → Categorize
      → Move to Done
```

---

## What Needs to Be Built

### Priority 1: Approval Workflow
**File:** `scripts/approval_handler.py`

```python
# Check for new approval requests
# If human approved → execute action
# If human rejected → archive with note
```

### Priority 2: Email Response
**File:** `scripts/email_sender.py`

```python
# Connect to email MCP server
# Send drafted emails after approval
# Log sent emails
```

### Priority 3: Plan Generation
**Update:** `scripts/orchestrator.py`

```python
# Create Plan.md for complex tasks
# Track progress
# Update plan with completion status
```

---

## How to Add Email Responses (Example)

### Step 1: Create Email Draft

When email needs reply:

```python
# In task_processor.py

def _create_email_draft(self, original_email, reply_content):
    draft = f"""
---
type: approval_request
action: email_reply
to: {original_email['from']}
subject: Re: {original_email['subject']}
---

# Email Reply Approval

## Draft Content
{reply_content}

## To Approve
Move to /Approved/ to send
"""
    return draft
```

### Step 2: Check Approved Actions

```python
# In approval_handler.py

def process_approved_emails():
    approved_files = list(approved_folder.glob("*.md"))
    
    for file in approved_files:
        # Parse email details
        # Send via email MCP
        # Move to Done
```

---

## Summary

| Feature | Status | Tier |
|---------|--------|------|
| Gmail Watcher | ✅ Working | Bronze |
| File Watcher | ✅ Working | Bronze |
| Categorization | ✅ Working | Bronze |
| Dashboard Updates | ✅ Working | Bronze |
| **Email Responses** | ❌ Not Implemented | Silver |
| **Approval Workflow** | ❌ Not Implemented | Silver |
| **Plan.md Generation** | ❌ Not Implemented | Silver |
| LinkedIn Posting | ⚠️ Partial | Silver |

**Current system is a Bronze Tier system** - it monitors, categorizes, and archives.

**To get Silver Tier**, we need to add:
1. Email sending via MCP
2. Approval workflow
3. Plan generation

Would you like me to implement these Silver Tier features?
