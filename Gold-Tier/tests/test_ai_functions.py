import sys
sys.path.insert(0, 'scripts')
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

# Test the AI integration functions directly
from scripts.qwen_ai_integration import ai_select_skill, ai_generate_email_response, ai_generate_plan, ai_analyze_email

# Mock data for testing
available_skills = [
    {"name": "email_responder", "description": "Handles email responses"},
    {"name": "task_planning", "description": "Creates task plans"},
    {"name": "payment_processor", "description": "Processes payments"}
]

task_content = """---
type: email
from: client@example.com
subject: Project Inquiry
---

## Email Content
Hi, I'm interested in your services for a new project. Can you provide more information?

Best regards,
Client
"""

email_content = """From: client@example.com
Subject: Project Inquiry
Date: 2026-04-17

Hi, I'm interested in your services for a new project. Can you provide more information?

Best regards,
Client
"""

print("Testing AI functions with mock data...")

# Test skill selection
print("\n1. Testing skill selection:")
selected_skill = ai_select_skill(task_content, available_skills)
print(f"Selected skill: {selected_skill}")

# Test email response generation
print("\n2. Testing email response generation:")
email_response = ai_generate_email_response(
    "client@example.com",
    "Project Inquiry",
    "Hi, I'm interested in your services for a new project. Can you provide more information?"
)
print(f"Email response: {email_response}")

# Test plan generation
print("\n3. Testing plan generation:")
task_data = {"subject": "Project Inquiry", "from": "client@example.com"}
plan = ai_generate_plan("email", task_data, task_content)
print(f"Generated plan: {plan}")

# Test email analysis
print("\n4. Testing email analysis:")
analysis = ai_analyze_email(email_content)
print(f"Email analysis: {analysis}")

print("\nAll tests completed!")