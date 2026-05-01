import sys
sys.path.insert(0, 'Gold-Tier/scripts')
sys.path.insert(0, 'Gold-Tier')

from skills.task_planning.service import PlanningService

# Test plan generation functionality
try:
    print("Testing plan generation with Qwen3-Coder:480b-cloud...")

    # Initialize planning service
    planner = PlanningService(vault_path="Gold-Tier/AI_Employee_Vault")

    # Test data
    task_type = "email"
    task_data = {
        "subject": "Project Inquiry",
        "from": "client@example.com",
        "priority": "normal"
    }
    task_content = """---
type: email
from: client@example.com
subject: Project Inquiry
priority: normal
---

## Email Content
Hello,

I'm interested in your services for a new project. Can you provide more information?

Best regards,
Client
"""

    # Generate plan
    print("Generating plan...")
    plan = planner.generate_plan(task_type, task_data, task_content)

    print(f"Generated plan: {plan}")

    if plan and isinstance(plan, dict) and "plan_content" in plan:
        print("[SUCCESS] Plan generation successful!")
        print(f"Plan content: {plan['plan_content']}")
    else:
        print("[WARNING] Plan generation may have issues")

except Exception as e:
    print(f"Error testing plan generation: {e}")
    import traceback
    traceback.print_exc()