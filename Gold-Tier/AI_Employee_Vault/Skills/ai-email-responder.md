---
name: ai-email-responder
description: |
  AI-powered email response generator.
  Reads email content and generates professional, context-aware replies.
  Use for all email response generation in AI Employee system.
---

# AI Email Responder Skill

Generates professional email responses using AI reasoning.

---

## When to Use

- New email detected in `/Needs_Action/`
- Email requires reply
- Human has approved the response
- Need professional, context-aware content

---

## AI Prompt Template

```
You are a professional AI Employee assistant. Read the following email and generate a professional response.

ORIGINAL EMAIL:
---
From: {from_email}
Subject: {subject}
Date: {date}

{email_body}
---

INSTRUCTIONS:
1. Analyze the email content and intent
2. Generate a professional, courteous response
3. Use proper email formatting with clear paragraphs
4. Keep it concise but helpful
5. Include appropriate greeting and sign-off

GENERATE RESPONSE IN THIS FORMAT:

Dear {Sender Name or "Valued Contact"},

[Opening paragraph - acknowledge their message]

[Main paragraph - address their inquiry]

[Closing paragraph - next steps or offer further assistance]

Best regards,

AI Employee Response System
Automated Customer Service

---
Reference ID: {timestamp}
```

---

## Usage Example

```python
# Call Qwen Code to generate response
prompt = f"""
You are a professional AI Employee assistant.

ORIGINAL EMAIL:
From: client@company.com
Subject: Inquiry about services

Hi,

I'm interested in learning more about your services. 
Can you send me information?

Thanks,
John Smith

INSTRUCTIONS:
Generate a professional response with proper formatting.
"""

# Qwen Code generates AI response
ai_response = qwen_code.generate(prompt)
```

---

## Expected AI Output

```
Dear John,

Thank you for your interest in our services.

We would be happy to provide you with more information. Our team offers comprehensive solutions tailored to your business needs.

Could you please let us know which specific services you're interested in? This will help us send you the most relevant information.

We look forward to assisting you.

Best regards,

AI Employee Response System
Automated Customer Service

---
Reference ID: 20260310123456
```

---

## Integration Points

| Component | AI Integration |
|-----------|----------------|
| Gmail Watcher | Detects email → Creates action file |
| **Orchestrator** | **Calls Qwen Code → Generates AI response** |
| Approval Handler | Human reviews AI-generated response |
| Email Sender | Sends AI-generated email |

---

## Benefits of AI Integration

✅ **Context-Aware** - Understands email content and intent
✅ **Professional Tone** - Consistent, courteous responses
✅ **Proper Formatting** - AI generates proper paragraphs
✅ **Personalized** - Addresses sender by name when available
✅ **Silver Tier Compliant** - Uses AI reasoning as required

---

*AI Employee Email Responder Skill v1.0*
