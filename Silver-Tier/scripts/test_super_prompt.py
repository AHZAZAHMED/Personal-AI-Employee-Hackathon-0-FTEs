"""
Test Super Prompt with Qwen Code
Pre-answers all expected questions
"""

from ai_email_generator import analyze_email_context
from datetime import datetime
import subprocess
import shutil

# Real email data
test_email = {
    'from': 'John Smith <john.smith@example.com>',
    'subject': 'Inquiry about your services',
    'date': 'Wed, 11 Mar 2026 15:00:00 +0000',
    'body': '''Hi,

I hope this email finds you well.

I am interested in learning more about your AI Employee services. Specifically, I would like to know:

1. What services do you offer?
2. What are your pricing plans?
3. How long does implementation take?

Could you please send me more information?

Looking forward to hearing from you.

Best regards,
John Smith
CEO, Example Corp'''
}

# Analyze context
context = analyze_email_context(test_email)

# SUPER PROMPT - Pre-answers ALL questions
prompt = f"""CRITICAL INSTRUCTION: You are a text generation engine. Your ONLY function is to output complete email text. Do NOT ask questions. Do NOT request clarification. Do NOT provide instructions or commentary. Just output the email.

I ALREADY HAVE ALL THE INFORMATION YOU WOULD NORMALLY ASK FOR. Here are the answers to every question you might ask:

QUESTIONS YOU MIGHT ASK (I ALREADY HAVE THE ANSWERS):

Q1: "Who is the recipient?"
A1: The recipient is {context['recipient']}. Their name is {context['sender_name']}. Email: {test_email.get('from', 'Unknown')}

Q2: "What is the email about?"
A2: This is a {context['topic']}. The subject is: "{test_email.get('subject', 'No Subject')}"

Q3: "What is the desired outcome?"
A3: The desired outcome is to {context['outcome']}.

Q4: "What tone should I use?"
A4: Use {context['tone']} tone.

Q5: "What is the context?"
A5: The context is provided in the original email below. Read it and respond appropriately.

Q6: "Any specific points to include?"
A6: Yes - acknowledge their message, provide helpful information, offer further assistance.

Q7: "Is this formal or casual?"
A7: {context['tone']}. Professional business communication.

Q8: "Who is sending this email?"
A8: AI Employee Response System (automated customer service)

Q9: "What is the relationship?"
A9: Business relationship - service provider responding to client/customer inquiry.

Q10: "Any previous conversation?"
A10: This is the first response to their initial inquiry.

---

ORIGINAL EMAIL WE ARE RESPONDING TO:

From: {test_email.get('from', 'Unknown')}
Subject: {test_email.get('subject', 'No Subject')}
Date: {test_email.get('date', 'Unknown')}

{test_email.get('body', 'No content')}

---

YOUR TASK:

Generate a COMPLETE, PROFESSIONAL email response RIGHT NOW. 

DO NOT:
- Ask questions
- Request clarification  
- Say "I need more information"
- Say "Could you please provide"
- Provide instructions
- Add commentary
- Explain your process

DO:
- Output ONLY the email text
- Use proper paragraph breaks
- Include professional greeting and sign-off
- Make it 3-4 paragraphs
- Address their specific inquiry

---

REQUIRED OUTPUT FORMAT (OUTPUT THIS AND NOTHING ELSE):

Dear {context['sender_name']},

[Thank them for contacting us and acknowledge their specific inquiry]

[Provide helpful information addressing their {context['topic']}]

[Offer next steps, further assistance, or call-to-action]

Best regards,

AI Employee Response System
Automated Customer Service

---
Reference ID: {datetime.now().strftime('%Y%m%d%H%M%S')}
For urgent matters, reply with "URGENT" in subject line.

---

FINAL INSTRUCTION: Output ONLY the email text above. Fill in the bracketed sections with actual content. Do NOT output the brackets. Do NOT output any other text. Just the complete, ready-to-send email. BEGIN OUTPUT NOW:
"""

print("=" * 70)
print("TESTING SUPER PROMPT WITH QWEN CODE")
print("=" * 70)
print()
print("CONTEXT ANALYSIS:")
print(f"  Recipient: {context['recipient']}")
print(f"  Sender: {context['sender_name']}")
print(f"  Topic: {context['topic']}")
print(f"  Outcome: {context['outcome']}")
print(f"  Tone: {context['tone']}")
print()
print("=" * 70)
print("CALLING QWEN CODE...")
print("=" * 70)
print()

# Find Qwen
qwen_path = shutil.which('qwen')

if not qwen_path:
    print("Qwen Code not found!")
    exit(1)

# Call Qwen
result = subprocess.run(
    [qwen_path, '--prompt', prompt],
    capture_output=True,
    text=True,
    timeout=60
)

print("QWEN CODE RESPONSE:")
print("=" * 70)
print()
print(result.stdout)
print()
print("=" * 70)

# Check if response contains questions
response = result.stdout.lower()
if any(word in response for word in ['could you', 'please provide', 'i need', 'what is', 'can you']):
    print("⚠️  Qwen Code is ASKING QUESTIONS again!")
else:
    print("✅ Qwen Code GENERATED AN EMAIL!")
