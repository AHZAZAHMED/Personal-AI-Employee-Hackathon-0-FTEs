# Task Plan: TechCorp Partnership Inquiry Response & Validation

## Executive Summary
Sarah Johnson from TechCorp has reached out regarding a partnership opportunity. The email content suggests this may be a test of the AI Employee system, but requires professional follow-up to confirm intent and preserve potential business value. This task involves validating the inquiry, engaging appropriately, and escalating if genuine.

## Priority Level
**HIGH** - Marked as urgent with "Partnership Opportunity" in subject. Even if a test, demonstrates system capability; if genuine, could impact Q1/Q2 revenue targets ($22,500 Q1 / $45,000 Q2).

## Steps
1. [ ] **Verify sender authenticity** - Check if sarah.johnson@techcorp.com exists in contacts, search domain reputation, verify against known phishing patterns (Estimated: 10 minutes)
2. [ ] **Search vault for TechCorp history** - Check `/Inbox`, `/Done`, `/Accounting` for any previous interactions with TechCorp or Sarah Johnson (Estimated: 5 minutes)
3. [ ] **Draft professional response** - Create reply acknowledging the inquiry, requesting more details about the partnership opportunity, and offering a call/meeting (Estimated: 15 minutes)
4. [ ] **Move to Pending_Approval** - Per Company Handbook, "Sending emails to new contacts" requires human approval. Create approval file in `/Pending_Approval/` (Estimated: 5 minutes)
5. [ ] **Update Dashboard.md** - Log this inquiry under "Outstanding Items" or "Partnership Pipeline" section (Estimated: 5 minutes)
6. [ ] **Create log entry** - Add entry to `/Logs/2026-03-15.json` documenting receipt, analysis, and actions taken (Estimated: 5 minutes)
7. [ ] **Await human approval** - Monitor `/Approved/` for approval to send response (Estimated: Variable)
8. [ ] **Send response upon approval** - Execute email send via MCP Gmail server once approved (Estimated: 2 minutes)
9. [ ] **Move to Done** - Transfer processed email file to `/Done/` with completion timestamp (Estimated: 2 minutes)

## Risks & Dependencies
- ⚠️ **Risk**: Sender may be phishing attempt | **Mitigation**: Verify domain, don't share sensitive info in first response
- ⚠️ **Risk**: Real opportunity delayed if treated as test | **Mitigation**: Professional response either way, escalate if follow-up confirms genuine
- 📋 **Dependency 1**: Human approval required before sending (Company Handbook: "Sending emails to new contacts" requires approval)
- 📋 **Dependency 2**: MCP Gmail server must be configured and running

## Stakeholders
- **System Operator/Human Approver**: Must approve outbound email to new contact per HITL rules
- **CEO/Sales Lead** (if genuine): Should be notified if this becomes a real partnership opportunity
- **AI Employee (Email Agent)**: Responsible for processing, drafting, and executing

## Estimated Timeline
- **Total Estimated Time**: 44 minutes (excluding approval wait time)
- **Deadline**: None specified (but marked "Urgent" - recommend same-day response)
- **Recommended Completion**: **Today (2026-03-15)** - Aligns with "Client response time < 24 hours" metric in Business Goals

## Notes for Execution
- **Company Handbook Compliance**: This workflow follows the "Require Approval" rule for "Sending emails to new contacts"
- **Business Goals Alignment**: Supports "New clients acquired: 5/month" target if genuine opportunity
- **Test Scenario**: If this IS a system test, successful completion demonstrates Silver-tier capability (watcher → plan generation → HITL workflow → MCP action)
- **Follow-up**: If no response from Sarah within 3 business days, create follow-up task
- **Template**: Consider creating a "Partnership Inquiry Response" template for future similar emails