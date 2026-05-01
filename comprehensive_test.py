import sys
sys.path.insert(0, 'Gold-Tier/scripts')
sys.path.insert(0, 'Gold-Tier')

from scripts.qwen_ai_integration import call_ai_model, ai_select_skill, ai_generate_email_response, ai_generate_plan, ai_analyze_email
from skill_registry import SkillRegistry

print("=== Comprehensive Test of Refactored Functionalities ===")

# Test 1: Direct AI model calling
print("\n1. Testing direct AI model calling...")
prompt = "Write a short professional greeting."
response = call_ai_model(prompt, model="qwen3-coder:480b-cloud", timeout=30)
print(f"Direct AI response: {response[:100]}..." if response else "No response")

# Test 2: Skill selection
print("\n2. Testing skill selection...")
available_skills = [
    {"name": "email_responder", "description": "Handles email responses"},
    {"name": "task_planning", "description": "Creates task plans"}
]
task_content = "I need help with responding to an email from a client."
selected_skill = ai_select_skill(task_content, available_skills)
print(f"Selected skill: {selected_skill}")

# Test 3: Email response generation
print("\n3. Testing email response generation...")
email_response = ai_generate_email_response(
    "client@example.com",
    "Project Inquiry",
    "Hi, I'm interested in your services."
)
print(f"Email response generated: {bool(email_response)}")

# Test 4: Plan generation
print("\n4. Testing plan generation...")
plan = ai_generate_plan(
    "email",
    {"subject": "Project Inquiry", "from": "client@example.com"},
    "Client wants information about our services."
)
print(f"Plan generated: {bool(plan)}")

# Test 5: Email analysis
print("\n5. Testing email analysis...")
email_content = """From: client@example.com
Subject: Project Inquiry

Hi, I'm interested in your services for a new project. Can you provide more information?

Best regards,
Client"""

analysis = ai_analyze_email(email_content)
print(f"Email analysis completed: {bool(analysis)}")
print(f"Analysis result: {analysis}")

# Test 6: Skill registry
print("\n6. Testing skill registry...")
try:
    registry = SkillRegistry(skills_dir="Gold-Tier/skills")
    registry.discover()
    skill_result = registry.dispatch("email_generate_response",
                                   from_email="test@example.com",
                                   subject="Test",
                                   body="This is a test.",
                                   vault_path="Gold-Tier/AI_Employee_Vault")
    print(f"Skill registry test: {'SUCCESS' if skill_result.get('success') else 'FAILED'}")
except Exception as e:
    print(f"Skill registry test failed: {e}")

print("\n=== All tests completed ===")