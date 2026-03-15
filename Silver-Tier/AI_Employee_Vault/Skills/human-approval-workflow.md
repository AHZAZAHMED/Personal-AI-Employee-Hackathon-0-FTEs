---
name: human-approval-workflow
description: |
  Manage human-in-the-loop approval workflow.
  Create approval requests, process approved/rejected actions,
  and maintain audit trail of all human decisions.
  Use for sensitive actions requiring human review.
---

# Human Approval Workflow

Request and process human approval for sensitive actions.

---

## When to Use

**Always require approval for:**
- Emails to new contacts (not in approved list)
- Any payment or financial transaction
- Social media posts (LinkedIn, Twitter, etc.)
- External API calls with side effects
- Actions costing >$0
- Irreversible operations

**Auto-approve (no approval needed):**
- File categorization within vault
- Data analysis without external calls
- Replies to approved contacts
- Internal documentation updates

---

## Approval Folder Structure

```
Vault/
├── Pending_Approval/    # Awaiting human decision
├── Approved/            # Approved, ready to execute
├── Rejected/            # Rejected by human
└── Done/                # Executed or archived
```

---

## Skill 1: Create Approval Request

### Template

```markdown
---
type: approval_request
action: <action_type>
created: 2026-02-28T10:30:00
status: pending
expires: 2026-03-01T10:30:00
risk_level: <low|medium|high>
---

# Approval Required

## Action Details
- **Action:** <what will be done>
- **Reason:** <why this action is needed>
- **Risk Level:** <low|medium|high>

## Details
<full details of what will be done>
<include previews, amounts, recipients, etc.>

## Why Approval is Required
Per Company Handbook Section X.X:
"<relevant rule from handbook>"

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with a note explaining why.

## Deadline
Please respond within 24 hours.
```

### Example: Email to New Contact

```markdown
---
type: approval_request
action: email_send
created: 2026-02-28T10:30:00
status: pending
expires: 2026-03-01T10:30:00
risk_level: medium
---

# Approval Required

## Action Details
- **Action:** Send Email
- **To:** newcontact@example.com (NEW CONTACT)
- **Subject:** Re: Pricing Inquiry
- **Risk Level:** Medium (new recipient)

## Email Preview
```
Dear [Name],

Thank you for your interest in our services.
[Full draft content here]

Best regards,
[Your Name]
```

## Why Approval is Required
Per Company Handbook Section 3.1:
"Emails to new contacts require human review before sending"

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with a note.

## Deadline
Please respond within 24 hours.
```

### Example: Payment Request

```markdown
---
type: approval_request
action: payment
created: 2026-02-28T14:00:00
status: pending
expires: 2026-03-01T14:00:00
risk_level: high
---

# Approval Required

## Action Details
- **Action:** Make Payment
- **Amount:** $500.00
- **Recipient:** Vendor ABC Corp
- **Account:** ****1234
- **Risk Level:** High (financial transaction)

## Payment Details
- **Invoice:** #INV-2026-001
- **Due Date:** 2026-03-05
- **Service:** Monthly software subscription
- **Category:** Operating Expense

## Why Approval is Required
Per Company Handbook Section 4.2:
"All payments require human approval"

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with explanation.

## Deadline
Please respond within 24 hours (before due date).
```

---

## Skill 2: Check for Approved Actions

### Process

```
1. List files in /Approved/
2. For each file not yet processed:
   - Parse action type and details
   - Execute via appropriate MCP server
   - Add execution result to file
   - Move to /Done/
3. Update Dashboard stats
```

### Check Command

```
List /Approved/*.md
For each file:
  Read frontmatter to get action type
  If action == "email_send":
    Execute via email MCP
  If action == "payment":
    Execute via payment MCP
  If action == "social_post":
    Execute via browser MCP (LinkedIn)
  Add execution summary
  Move to /Done/
```

---

## Skill 3: Process Rejected Actions

### Process

```
1. List files in /Rejected/
2. For each file not yet archived:
   - Add rejection timestamp
   - Add any human notes
   - Move to /Done/ with _rejected suffix
3. Log rejection for audit
```

### Rejection Handling

```
Read /Rejected/<file>.md
Add:
---
rejected: <timestamp>
rejected_by: <human name>
reason: <if provided>
---
Move to: /Done/<file>_rejected_<timestamp>.md
Log: Event to /Logs/YYYY-MM-DD.jsonl
```

---

## Skill 4: Approval Status Tracking

### Status Values

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `pending` | Awaiting human decision | Wait |
| `approved` | Human approved | Execute action |
| `rejected` | Human rejected | Archive |
| `executed` | Action completed | Move to Done |

### Status Check

```
Read file frontmatter
Get status field
Case:
  pending → Wait or send reminder
  approved → Execute immediately
  rejected → Archive with note
  executed → Already done
```

---

## Approval Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│           HUMAN APPROVAL WORKFLOW                            │
└─────────────────────────────────────────────────────────────┘

Task Requires Approval?
         │
    ┌────┴────┐
    │         │
   NO        YES
    │         │
    │    ┌────┴────────────────────────────┐
    │    │ Create /Pending_Approval/       │
    │    │ Request with full details       │
    │    └────────────┬────────────────────┘
    │                 │
    │          ┌──────┴──────┐
    │          │ Human Review│
    │          └──────┬──────┘
    │                 │
    │         ┌───────┴───────┐
    │         │               │
    │    Moved to          Moved to
    │    /Approved/        /Rejected/
    │         │               │
    │    Execute          Archive
    │    via MCP          with note
    │         │               │
    │    ┌────┴────┐      ┌───┴───┐
    │    │         │      │       │
    │    v         v      v       v
    └──► Done ◄───────────────────┘
```

---

## Quick Reference

```
# Create approval request
Parse task to get action details
Fill approval template
Write to /Pending_Approval/<ACTION>_<desc>_<ts>.md

# Check for approvals
List /Approved/*.md
Execute each via appropriate MCP
Move to /Done/

# Check for rejections
List /Rejected/*.md
Archive with timestamp
Move to /Done/
```

---

## Company Handbook Integration

**Always check handbook before creating approval:**

```
Read /Company_Handbook.md
Find section on: <action_type>
Quote relevant rule in "Why Approval Required"
```

**Common approval rules:**
- Section 3.1: Emails to new contacts
- Section 4.2: All payments
- Section 5.1: Social media posts
- Section 6.3: External API calls

---

*AI Employee Skill v0.2.0 | Silver Tier*
