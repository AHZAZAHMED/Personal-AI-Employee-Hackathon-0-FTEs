import sys
sys.path.insert(0, 'scripts')
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from scripts.qwen_ai_integration import call_qwen_coder

prompt = """You are a professional AI Employee assistant. Generate a complete email response NOW.

CONTEXT:
- Recipient: client
- Sender: Client
- Topic: general inquiry
- Desired Outcome: provide information and offer assistance
- Tone: professional and friendly

ORIGINAL EMAIL:
---
From: client@example.com
Subject: Project timeline update needed
Date: 

Hi, we need the updated timeline for the project by next week. Please share the current status and any blockers. Thanks!
---

Write a COMPLETE, PROFESSIONAL email response. Do NOT ask questions. Do NOT provide instructions.
Use greeting "Dear Client", 3-4 paragraphs, and sign off with "Best regards, AI Employee Response System".
Reference ID: 20260413000000

Generate ONLY the email text and wrap it strictly inside <email></email> tags. Do not output anything outside of these tags.
"""

print("Calling Qwen3-Coder:480b-cloud with strict prompt...")
response = call_qwen_coder(prompt, vault_path="AI_Employee_Vault", timeout=30)
print(f"\n=== Response (length: {len(response) if response else 0}) ===")
print(response)
