---
name: linkedin-auto-posting
description: |
  Automatically post business updates to LinkedIn.
  Uses Playwright MCP for browser automation.
  Requires human approval before posting.
  Use for client wins, milestones, and business updates.
---

# LinkedIn Auto-Posting

Post business updates to LinkedIn automatically with human approval.

---

## When to Use

- New client win announcement
- Project milestone completed
- Weekly business update
- Product/service announcement
- Company achievement

---

## Prerequisites

1. **Playwright MCP Server** running (port 8808)
2. **LinkedIn account** credentials (stored securely)
3. **Human approval** for each post (per handbook)

---

## Skill 1: Create Post Draft

### Post Template

```markdown
---
type: social_media_post
platform: linkedin
created: 2026-02-28T10:00:00
status: pending_approval
post_type: milestone
---

# LinkedIn Post Draft

## Content
🎉 Excited to announce [achievement/milestone]!

[Brief description - 2-3 sentences]

[Optional: Call to action or link]

#hashtags #relevant #tags

## Posting Details
- **Platform:** LinkedIn
- **Type:** [milestone | announcement | update]
- **Visibility:** Public
- **Scheduled:** [immediate | specific time]

## Approval Required
Move this file to /Approved/ to publish.
Add edits as comments before approving.
```

### Example: Client Win

```markdown
---
type: social_media_post
platform: linkedin
created: 2026-02-28T10:00:00
status: pending_approval
post_type: client_win
client: ABC Corporation
---

# LinkedIn Post Draft

## Content
🎉 Excited to announce our partnership with ABC Corporation!

We'll be helping them transform their business with our AI-powered solutions. This marks a major milestone in our Q1 2026 growth journey.

Thank you to the entire team for making this possible!

#AI #BusinessTransformation #Partnership #Growth

## Posting Details
- **Platform:** LinkedIn
- **Type:** Client Win
- **Visibility:** Public
- **Character Count:** 287/3000

## Approval Required
Move this file to /Approved/ to publish.
```

---

## Skill 2: Execute LinkedIn Post (After Approval)

### Pre-flight Checks

```
1. Verify approval:
   - Check /Approved/ for this post
   - Confirm human reviewed content

2. Check Playwright MCP:
   - Server running on port 8808
   - Browser accessible

3. Validate post content:
   - Under 3000 characters
   - Hashtags included
   - No sensitive information
```

### Posting Workflow

```
┌─────────────────────────────────────────────────────────────┐
│           LINKEDIN POSTING WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

1. Start Playwright MCP Server
   │
2. Navigate to linkedin.com
   │
3. Login (if not already)
   │
4. Click "Start a post" button
   │
5. Type post content
   │
6. Add hashtags
   │
7. Click "Post" button
   │
8. Wait for confirmation
   │
9. Screenshot result
   │
10. Log post URL
   │
11. Stop MCP Server
   │
12. Move task to /Done/
```

---

## Skill 3: Playwright MCP Commands

### Navigate to LinkedIn

```bash
python3 scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_navigate \
  -p '{"url": "https://linkedin.com"}'
```

### Get Page Snapshot

```bash
python3 scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_snapshot \
  -p '{}'
```

### Click "Start Post" Button

```bash
python3 scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_click \
  -p '{"element": "Start a post", "ref": "e42"}'
```

### Type Post Content

```bash
python3 scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_type \
  -p '{"element": "Post text area", "ref": "e15", "text": "🎉 Excited to announce...\n\n#hashtags"}'
```

### Click Post Button

```bash
python3 scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_click \
  -p '{"element": "Post button", "ref": "e50"}'
```

### Take Screenshot

```bash
python3 scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_take_screenshot \
  -p '{"type": "png", "fullPage": false}'
```

---

## Skill 4: Post Execution Summary

### Summary Template

```markdown
---
type: social_media_post
platform: linkedin
created: 2026-02-28T10:00:00
posted: 2026-02-28T14:30:00
status: published
post_url: https://linkedin.com/posts/yourprofile_abc123
---

# Post Published

## Content
[Original post content]

## Publishing Details
- **Posted:** 2026-02-28 14:30:00
- **Platform:** LinkedIn
- **URL:** https://linkedin.com/posts/yourprofile_abc123
- **Status:** Published

## Execution Log
1. Playwright MCP started
2. Navigated to LinkedIn
3. Logged in successfully
4. Composed post
5. Published at 14:30:00
6. Screenshot captured
7. MCP server stopped

## Screenshot
![Post Confirmation](/Screenshots/linkedin_20260228_143000.png)

## Engagement Tracking
- Views: [check after 24 hours]
- Likes: [check after 24 hours]
- Comments: [check after 24 hours]
```

---

## Error Handling

| Error | Response |
|-------|----------|
| Login failed | Alert human, check credentials |
| Post button not found | Refresh page, retry once |
| Character limit exceeded | Truncate, alert human |
| Network timeout | Retry 3 times, then alert |
| Already posted | Log URL, move to Done |

---

## Best Practices

1. **Always get approval** before posting
2. **Review content** for typos before posting
3. **Include 3-5 relevant hashtags**
4. **Post during business hours** (9 AM - 5 PM)
5. **Screenshot confirmation** for audit
6. **Track engagement** after 24 hours

---

## Quick Reference

```
# Create post draft
Fill post template
Write to /Needs_Action/LINKEDIN_<topic>_<ts>.md

# After approval
Start Playwright MCP
Navigate to LinkedIn
Compose and post
Screenshot confirmation
Log URL
Move to /Done/
```

---

*AI Employee Skill v0.2.0 | Silver Tier*
