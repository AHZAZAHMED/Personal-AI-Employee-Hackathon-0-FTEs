import sys
import os

# Add current directory to Python path
sys.path.insert(0, 'Gold-Tier/scripts')
sys.path.insert(0, 'Gold-Tier')

# Test skill registry functionality
try:
    from skill_registry import SkillRegistry
    print("SkillRegistry imported successfully")

    # Initialize skill registry
    registry = SkillRegistry(skills_dir="Gold-Tier/skills")
    count = registry.discover()
    print(f"Discovered {count} skills")

    # List available skills
    skills = registry.list_skills()
    print("Available skills:")
    for skill in skills:
        print(f"  - {skill}")

    # Test dispatching a skill
    print("\nTesting skill dispatch...")
    result = registry.dispatch("email_generate_response",
                              from_email="test@example.com",
                              subject="Test Email",
                              body="This is a test email for skill testing.",
                              vault_path="Gold-Tier/AI_Employee_Vault")
    print(f"Skill dispatch result: {result}")

except Exception as e:
    print(f"Error testing skill registry: {e}")
    import traceback
    traceback.print_exc()