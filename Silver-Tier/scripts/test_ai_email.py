"""
Test AI Email Generator with Real Email Data
"""

from ai_email_generator import generate_ai_response

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

print("=" * 60)
print("TESTING AI EMAIL GENERATION WITH REAL EMAIL")
print("=" * 60)
print()

result = generate_ai_response(test_email)

print()
print("=" * 60)
print("AI-GENERATED RESPONSE:")
print("=" * 60)
print()
print(result.get('response', 'No response generated'))
print()
print(f"Method: {result.get('method', 'unknown')}")
print(f"Success: {result.get('success', False)}")
