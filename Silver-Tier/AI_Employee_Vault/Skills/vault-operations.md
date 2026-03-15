---
name: ai-employee-vault-operations
description: |
  AI Employee Vault Operations - Core skills for managing the Obsidian vault,
  processing tasks, and maintaining the AI Employee system.
---

# AI Employee Vault Operations

Core skills for Qwen Code to manage the Personal AI Employee system.

## Overview

This skill set enables Qwen Code to:
- Read and write to the Obsidian vault
- Process tasks from `/Needs_Action` folder
- Create plans and execute auto-approved actions
- Request human approval for sensitive operations
- Update the Dashboard with current status
- Maintain audit logs

---

## Skill 1: Read Vault Structure

**Purpose:** Understand the current state of the vault.

**When to use:** At the start of each processing cycle.

**Actions:**
1. List files in `/Needs_Action` to find pending tasks
2. List files in `/Pending_Approval` to check for approved items
3. Read `Dashboard.md` for current status
4. Read `Company_Handbook.md` for rules and boundaries

**Example:**
```
Read all .md files in /Needs_Action folder
Read Company_Handbook.md to understand permission rules
Read Dashboard.md to see current system status
```

---

## Skill 2: Process Task File

**Purpose:** Process a single task file from `/Needs_Action`.

**When to use:** When a new task file is detected.

**Actions:**
1. Read the task file content
2. Extract metadata (type, priority, suggested actions)
3. Determine if action requires approval (per Company Handbook)
4. If approval needed → move to `/Pending_Approval`
5. If auto-approved → create plan and execute

**Decision Tree:**
```
Task Type → Action Required
─────────────────────────────────
file_drop → Review content, categorize, archive
email_draft → Check recipient, if new → approval needed
payment_request → ALWAYS requires approval
data_analysis → Auto-approve if within vault
external_api → Requires approval
```

---

## Skill 3: Create Task Plan

**Purpose:** Create a structured plan for executing a task.

**When to use:** Before executing any auto-approved task.

**Template:**
```markdown
---
created: <timestamp>
status: in_progress
task_file: <original_task_filename>
objective: <clear objective statement>
---

# Task Plan

## Objective
<objective description>

## Steps
1. [ ] <step 1>
2. [ ] <step 2>
3. [ ] <step 3>

## Execution Notes
<notes during execution>

## Completion Summary
<summary after completion>
```

---

## Skill 4: Update Dashboard

**Purpose:** Keep Dashboard.md current with system status.

**When to use:** After processing tasks, before exiting.

**Actions:**
1. Count files in each folder:
   - `/Needs_Action` → Pending count
   - `/In_Progress/qwen_agent` → In progress count
   - `/Pending_Approval` → Awaiting approval count
   - `/Done` (today) → Completed today count
2. Update the stats table in Dashboard.md
3. Add recent activity entries
4. Update last_updated timestamp

**Stats Table Format:**
```markdown
| Metric | Value |
|--------|-------|
| Pending Tasks | <count> |
| In Progress | <count> |
| Awaiting Approval | <count> |
| Completed Today | <count> |
| Completed This Week | <count> |
```

---

## Skill 5: Request Human Approval

**Purpose:** Request human decision for sensitive actions.

**When to use:** When task requires human review per Company Handbook.

**Template for Approval Request:**
```markdown
---
type: approval_request
action: <action_type>
created: <timestamp>
status: pending
expires: <timestamp + 24 hours>
---

# Approval Required

## Action Details
- **Action:** <what action is needed>
- **Reason:** <why this action is needed>
- **Risk Level:** <low/medium/high>

## Details
<full details of what will be done>

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.

## Deadline
Please respond within 24 hours.
```

---

## Skill 6: Log Activity

**Purpose:** Maintain audit trail of all actions.

**When to use:** After every significant action.

**Log Entry Format (JSONL):**
```json
{
  "timestamp": "2026-02-26T10:30:00",
  "event_type": "task_processed",
  "task_file": "FILE_document_20260226_103000.md",
  "action_taken": "created_plan",
  "plan_file": "PLAN_document_20260226_103000.md",
  "status": "success"
}
```

**Log File:** `/Logs/YYYY-MM-DD.jsonl`

---

## Skill 7: Move Task to Done

**Purpose:** Archive completed tasks.

**When to use:** After task is fully completed.

**Actions:**
1. Add completion summary to task file
2. Rename file with completion timestamp
3. Move to `/Done` folder
4. Update Dashboard recent activity

**Completion Summary Template:**
```markdown
---
completed: <timestamp>
completion_status: success
---

## Completion Summary

**Completed:** <timestamp>
**Status:** Success

**Actions Taken:**
- <action 1>
- <action 2>

**Notes:**
<any relevant notes>
```

---

## Skill 8: Generate Daily Summary

**Purpose:** Create end-of-day summary report.

**When to use:** End of each day or on request.

**Output Location:** `/Briefings/YYYY-MM-DD_Daily_Summary.md`

**Template:**
```markdown
---
generated: <timestamp>
period: <date>
---

# Daily Summary - <date>

## Tasks Completed
- <task 1>
- <task 2>

## Pending Approvals
- <approval 1>
- <approval 2>

## Errors/Issues
- <issue 1 or "None">

## Suggestions
- <suggestion 1>
```

---

## Complete Processing Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING CYCLE                          │
└─────────────────────────────────────────────────────────────┘

1. READ PHASE
   ├── List /Needs_Action/*.md
   ├── Read Company_Handbook.md
   └── Read Dashboard.md

2. PROCESS PHASE
   ├── For each task file:
   │   ├── Read content
   │   ├── Check handbook rules
   │   ├── Determine: approve or request approval?
   │   ├── If approve: create plan, execute, move to Done
   │   └── If approval: move to Pending_Approval
   │
   └── Check /Approved for newly approved items

3. WRITE PHASE
   ├── Update Dashboard.md stats
   ├── Write log entries
   └── Generate summary if needed

4. EXIT
   └── Report: tasks processed, errors, pending approvals
```

---

## Error Handling

| Error Type | Response |
|------------|----------|
| File not found | Log error, skip, continue |
| Invalid format | Flag for human review |
| Permission denied | Log, alert, skip |
| Qwen Code error | Log full error, create alert file |

---

## Best Practices

1. **Always read handbook first** - Rules may have changed
2. **Log everything** - Audit trail is critical
3. **When in doubt, ask** - Better to request approval than make mistake
4. **Update dashboard last** - Ensure all counts are accurate
5. **Preserve original files** - Move, don't delete
6. **Use timestamps** - All files should have creation/modification times

---

## Quick Reference Commands

```
# Process all pending tasks
Read /Needs_Action/*.md → Process each → Update Dashboard

# Check for approvals
Read /Approved/*.md → Execute approved actions → Move to Done

# Generate status report
Count folders → Read logs → Write summary to Dashboard
```

---

*AI Employee Skill Set v0.1.0 | Bronze Tier*
