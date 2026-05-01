"""
Test Claude AI Integration

Quick test script to verify Claude API is working correctly.
Run this after setting up your ANTHROPIC_API_KEY in .env
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from claude_ai_integration import (
    call_claude,
    call_ai_model,
    ai_generate_email_response,
    ai_generate_plan,
    ai_analyze_email
)


def test_basic_call():
    """Test basic Claude API call."""
    print("\n" + "="*60)
    print("TEST 1: Basic Claude API Call")
    print("="*60)

    response = call_claude("Say 'Hello from Claude!' and nothing else.")

    if response:
        print(f"✓ SUCCESS: {response}")
        return True
    else:
        print("✗ FAILED: No response from Claude")
        return False


def test_email_generation():
    """Test email response generation."""
    print("\n" + "="*60)
    print("TEST 2: Email Response Generation")
    print("="*60)

    response = ai_generate_email_response(
        from_email="client@example.com",
        subject="Partnership Inquiry",
        body="Hi, I'm interested in partnering with your company. Can we schedule a call?"
    )

    if response and len(response) > 50:
        print(f"✓ SUCCESS: Generated {len(response)} character email")
        print(f"\nPreview:\n{response[:200]}...")
        return True
    else:
        print("✗ FAILED: Email generation failed")
        return False


def test_plan_generation():
    """Test task plan generation."""
    print("\n" + "="*60)
    print("TEST 3: Task Plan Generation")
    print("="*60)

    response = ai_generate_plan(
        task_type="email",
        task_data={"subject": "Client Partnership Request", "from": "client@example.com"},
        task_content="Partnership inquiry from potential client"
    )

    if response and len(response) > 50:
        print(f"✓ SUCCESS: Generated {len(response)} character plan")
        print(f"\nPreview:\n{response[:200]}...")
        return True
    else:
        print("✗ FAILED: Plan generation failed")
        return False


def test_email_analysis():
    """Test email analysis."""
    print("\n" + "="*60)
    print("TEST 4: Email Analysis")
    print("="*60)

    result = ai_analyze_email(
        "Subject: URGENT - Server Down\n\nOur production server is down and customers can't access the site. Please help ASAP!"
    )

    if result and "intent" in result:
        print(f"✓ SUCCESS: Analysis completed")
        print(f"  Intent: {result.get('intent')}")
        print(f"  Urgency: {result.get('urgency')}")
        print(f"  Requires Reply: {result.get('requires_reply')}")
        print(f"  Sentiment: {result.get('sentiment')}")
        return True
    else:
        print("✗ FAILED: Email analysis failed")
        return False


def test_backward_compatibility():
    """Test backward compatibility with old function names."""
    print("\n" + "="*60)
    print("TEST 5: Backward Compatibility")
    print("="*60)

    # Test old model name mapping
    response = call_ai_model("Say 'Backward compatible!' and nothing else.", model="qwen3-coder:480b-cloud")

    if response:
        print(f"✓ SUCCESS: Old model name mapped correctly")
        print(f"  Response: {response}")
        return True
    else:
        print("✗ FAILED: Backward compatibility issue")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CLAUDE API INTEGRATION TEST SUITE")
    print("="*60)
    print("\nTesting Claude API integration...")
    print("Make sure ANTHROPIC_API_KEY is set in .env file")

    results = []

    try:
        results.append(("Basic Call", test_basic_call()))
        results.append(("Email Generation", test_email_generation()))
        results.append(("Plan Generation", test_plan_generation()))
        results.append(("Email Analysis", test_email_analysis()))
        results.append(("Backward Compatibility", test_backward_compatibility()))
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nCommon issues:")
        print("1. ANTHROPIC_API_KEY not set in .env")
        print("2. anthropic package not installed (run: pip install anthropic)")
        print("3. Invalid API key")
        return

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Claude API integration is working correctly.")
        print("\nYou can now use the AI Employee system with Claude API.")
    else:
        print("\n⚠ Some tests failed. Please check:")
        print("1. ANTHROPIC_API_KEY is correctly set in .env")
        print("2. API key is valid and active")
        print("3. You have sufficient API credits")


if __name__ == "__main__":
    main()
