import sys
sys.path.insert(0, 'Gold-Tier/scripts')
sys.path.insert(0, 'Gold-Tier')

from skills.email_responder.service import EmailResponseService

# Test email responder functionality
try:
    print("Testing email responder with Qwen3-Coder:480b-cloud...")

    # Initialize email responder service
    email_service = EmailResponseService(vault_path="Gold-Tier/AI_Employee_Vault")

    # Test data
    from_email = "client@example.com"
    subject = "Project Inquiry"
    body = "Hello,\n\nI'm interested in your services for a new project. Can you provide more information?\n\nBest regards,\nClient"
    date = "2026-04-17"

    # Generate email response
    print("Generating email response...")
    response = email_service.generate_response(from_email, subject, body, date)

    print(f"Generated response: {response}")

    if response and response.get("success"):
        print("[SUCCESS] Email response generation successful!")
        print(f"Response content: {response.get('response')}")
        print(f"Method used: {response.get('method')}")
    else:
        print("[WARNING] Email response generation may have issues")

except Exception as e:
    print(f"Error testing email responder: {e}")
    import traceback
    traceback.print_exc()