---
name: mcp-email-integration
description: |
  Send emails via MCP server after human approval.
  Integrates with email MCP servers to send, draft, and manage emails.
  Use for replying to contacts, sending invoices, and email communication.
---

# MCP Email Integration

Send and manage emails via Model Context Protocol servers.

---

## When to Use

- Replying to approved contacts
- Sending invoices to clients
- Follow-up emails after meetings
- Automated responses (with approval)

---

## Prerequisites

1. **Email MCP Server** installed and configured
2. **Human approval** for new contacts (per approval workflow)
3. **Email credentials** securely stored (not in vault)

---

## MCP Server Configuration

### For Qwen Code

Configure in `~/.config/qwen-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "email",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-email"],
      "env": {
        "EMAIL_API_KEY": "<your-key>",
        "EMAIL_SERVICE": "gmail"
      }
    }
  ]
}
```

---

## Skill 1: Send Email (After Approval)

### Pre-flight Checks

```
1. Verify approval exists:
   - Check /Approved/ for email_send approval
   - OR verify recipient is in approved contacts list

2. Validate email content:
   - Has recipient
   - Has subject
   - Has body content
   - No sensitive data (passwords, etc.)

3. Log intent:
   - Write to /Logs/YYYY-MM-DD.jsonl
   - Include recipient, subject, timestamp
```

### Send Command

```bash
# Using MCP email send tool
mcp_call email_send \
  --to "client@example.com" \
  --cc "" \
  --bcc "" \
  --subject "Re: Pricing Inquiry" \
  --body "Email content here..." \
  --attachments ""
```

### Response Handling

```
If success:
  - Log: "Email sent to <recipient>"
  - Update task: Add sent timestamp
  - Move to /Done/

If failure:
  - Log error details
  - Create alert file
  - Notify human
```

---

## Skill 2: Draft Email (For Approval)

### When to Draft

- New contact (requires approval)
- Sensitive topic (legal, financial)
- First-time communication
- High-stakes conversation

### Draft Template

```markdown
---
type: email_draft
to: newcontact@example.com
subject: Re: Service Inquiry
created: 2026-02-28T10:30:00
status: pending_approval
---

# Email Draft

## Recipient
- **To:** newcontact@example.com
- **Name:** [Contact Name]
- **Company:** [Company Name]

## Subject
Re: Service Inquiry

## Body

Dear [Name],

[Email content here]

Best regards,
[Your Name]

## Approval Required
Move this file to /Approved/ to send.
Add edits as comments before approving.
```

---

## Skill 3: Reply to Existing Contact

### Contact Verification

```
Read /Company_Handbook.md
Find: Approved contacts list
Check: Is recipient in list?

If YES: Auto-approve, send directly
If NO: Create approval request
```

### Reply Template

```markdown
---
type: email_reply
to: existing.client@company.com
subject: Re: Project Update
sent: 2026-02-28T14:30:00
status: sent
---

# Email Sent

## Details
- **To:** existing.client@company.com
- **Subject:** Re: Project Update
- **Sent:** 2026-02-28 14:30:00
- **Status:** Approved contact (Section 3.1)

## Content

Hi [Name],

Thanks for the update. [Reply content]

Best,
[Your Name]

## Log Entry
Action logged to /Logs/2026-02-28.jsonl
```

---

## Skill 4: Send Invoice Email

### Invoice Email Template

```markdown
---
type: invoice_email
to: client@company.com
subject: Invoice #INV-2026-001 - Due 2026-03-15
amount: 5000.00
sent: 2026-02-28T09:00:00
status: sent
---

# Invoice Sent

## Details
- **To:** client@company.com
- **Invoice:** #INV-2026-001
- **Amount:** $5,000.00
- **Due Date:** 2026-03-15
- **Sent:** 2026-02-28 09:00:00

## Email Content

Dear [Client],

Please find attached invoice #INV-2026-001 for services rendered.

**Amount Due:** $5,000.00
**Due Date:** March 15, 2026

Payment methods:
- Bank transfer (details on invoice)
- Credit card (link on invoice)

Thank you for your business!

Best regards,
[Your Name]

## Attachment
- /Invoices/INV-2026-001.pdf

## Follow-up
Schedule reminder for 2026-03-10 if unpaid
```

---

## Email MCP Tools Reference

| Tool | Purpose | Parameters |
|------|---------|------------|
| `email_send` | Send email | to, subject, body, cc, bcc, attachments |
| `email_draft` | Create draft | to, subject, body |
| `email_search` | Search emails | query, limit, folder |
| `email_read` | Read email | message_id |

---

## Error Handling

| Error | Response |
|-------|----------|
| Invalid recipient | Log error, notify human |
| SMTP failure | Retry 3 times, then alert |
| Rate limit | Wait 1 hour, retry |
| Attachment missing | Skip attachment, send text only |

---

## Security Best Practices

1. **Never log** email passwords or API keys
2. **Always verify** recipient before sending
3. **Use BCC** for bulk emails
4. **Encrypt** sensitive attachments
5. **Log** all sent emails for audit

---

## Quick Reference

```
# Send email to approved contact
Verify contact in approved list
mcp_call email_send --to <email> --subject <subject> --body <body>
Log to /Logs/

# Send email to new contact
Create approval request in /Pending_Approval/
Wait for human to move to /Approved/
Execute email_send
Move to /Done/
```

---

*AI Employee Skill v0.2.0 | Silver Tier*
