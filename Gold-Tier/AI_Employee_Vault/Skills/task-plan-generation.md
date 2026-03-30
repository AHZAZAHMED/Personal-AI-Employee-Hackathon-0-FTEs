---
name: task-plan-generation
description: |
  Generate detailed Plan.md files for complex tasks.
  Creates structured, executable plans with steps, context, and completion tracking.
  Use for multi-step tasks that require reasoning and tracking.
---

# Task Plan Generation

Create structured plans for executing complex tasks.

---

## When to Use

- Multi-step tasks (3+ actions required)
- Tasks involving external systems (email, social media, payments)
- Tasks that may need human approval
- Any task where tracking progress is important

---

## Plan File Location

```
/Plans/PLAN_<task-type>_<unique-id>_<timestamp>.md
```

---

## Plan Template

```markdown
---
created: 2026-02-28T10:00:00
status: in_progress
task_file: EMAIL_abc123_20260228_100000.md
objective: Reply to client inquiry about pricing
requires_approval: false
estimated_steps: 4
---

# Task Plan

## Objective
Clear one-sentence description of what this plan achieves.

## Context
- **From:** [source of task]
- **Type:** [task type from frontmatter]
- **Priority:** [high/normal/low]
- **Related Files:** [any related files]

## Steps
1. [ ] Step 1 - First action
2. [ ] Step 2 - Second action
3. [ ] Step 3 - Third action
4. [ ] Step 4 - Final action

## Execution Notes
*Add notes during execution*

## Completion Summary
*To be filled after all steps complete*
```

---

## Step-by-Step Process

### 1. Read Task File

```
Read file: /Needs_Action/<task_file>
Extract: type, priority, content, metadata
```

### 2. Check Company Handbook

```
Read: /Company_Handbook.md
Find: Rules for this task type
Determine: Auto-approve or requires approval?
```

### 3. Create Plan File

```
Generate filename: PLAN_<type>_<id>_<timestamp>.md
Fill template with:
  - Task metadata
  - Objective statement
  - Ordered steps
  - Approval requirement
Write to: /Plans/
```

### 4. Execute Steps

```
For each step in plan:
  - Mark as in_progress
  - Execute action
  - Mark as complete
  - Add note if needed
```

### 5. Update Completion Summary

```
Fill in:
  - Completion timestamp
  - Steps actually taken
  - Any deviations from plan
  - Outcome/result
```

### 6. Move to Done

```
Rename: Add _completed_<timestamp>
Move: /Plans/ → /Done/
Update: Original task file also to /Done/
```

---

## Example: Email Reply Plan

```markdown
---
created: 2026-02-28T10:30:00
status: completed
task_file: EMAIL_client_inquiry_20260228.md
objective: Reply to pricing inquiry from existing client
requires_approval: false
estimated_steps: 4
completed: 2026-02-28T10:45:00
---

# Task Plan

## Objective
Reply to client inquiry about pricing information

## Context
- **From:** existing.client@company.com
- **Subject:** Pricing Inquiry
- **Type:** email
- **Priority:** normal
- **Related Files:** /Inbox/pricing_sheet.pdf

## Steps
1. [x] Read full email content
2. [x] Check Company_Handbook.md - client is approved contact
3. [x] Draft response with standard pricing
4. [x] Send email via email MCP server
5. [x] Log action and update dashboard

## Execution Notes
- Client verified in approved contacts (Section 3.1)
- Used Q1 2026 pricing sheet
- Email sent successfully at 10:42 AM

## Completion Summary
**Completed:** 2026-02-28 10:45:00
**Status:** Success
**Actions:** Email drafted and sent with pricing information
**Follow-up:** Set reminder for 3-day follow-up if no response
```

---

## Example: Approval-Required Plan

```markdown
---
created: 2026-02-28T14:00:00
status: pending_approval
task_file: EMAIL_new_prospect_20260228.md
objective: Reply to pricing inquiry from NEW contact
requires_approval: true
estimated_steps: 3
---

# Task Plan

## Objective
Reply to new prospect inquiry (requires approval per handbook)

## Context
- **From:** newprospect@unknown-company.com
- **Subject:** Service Pricing Question
- **Type:** email
- **Priority:** normal
- **Approval Reason:** New contact (not in approved list)

## Steps
1. [ ] Create approval request in /Pending_Approval/
2. [ ] Wait for human approval
3. [ ] If approved: Draft and send email
4. [ ] If rejected: Archive with note

## Execution Notes
Per Company Handbook Section 3.1:
"Emails to new contacts require human review before sending"

## Completion Summary
*Pending approval*
```

---

## Quick Reference

```
# Create plan for task
Read /Needs_Action/<task>.md
Check /Company_Handbook.md for rules
Create /Plans/PLAN_<type>_<id>_<ts>.md
Execute steps, checking off each
Add completion summary
Move to /Done/ when complete
```

---

*AI Employee Skill v0.2.0 | Silver Tier*
