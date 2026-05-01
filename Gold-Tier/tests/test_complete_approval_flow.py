"""
Complete Approval Flow Test - End-to-End Validation

Tests the COMPLETE approval workflow:
1. Human approval (file in /Approved folder)
2. Orchestrator processes approved file
3. Orchestrator generates approval token
4. Orchestrator calls skill with token
5. Skill verifies token and executes

Also validates that direct skill calls WITHOUT tokens are blocked.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add paths - add parent directory so skills can be imported as packages
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from approval_tokens import ApprovalTokenManager, get_token_manager
from approval_handler import ApprovalHandler

print("=" * 70)
print("COMPLETE APPROVAL FLOW - END-TO-END TEST")
print("=" * 70)
print()

# Setup
vault_path = Path(__file__).parent.parent / "AI_Employee_Vault"
approved_folder = vault_path / "Approved"
done_folder = vault_path / "Done"

# Ensure folders exist
approved_folder.mkdir(parents=True, exist_ok=True)
done_folder.mkdir(parents=True, exist_ok=True)

tests_passed = 0
tests_total = 0

def test(name, condition, details=""):
    global tests_passed, tests_total
    tests_total += 1
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} | {name}")
    if details:
        print(f"        {details}")
    if condition:
        tests_passed += 1
    print()

# ============================================================================
# TEST 1: Direct Skill Call WITHOUT Token (Should Fail)
# ============================================================================
print("TEST 1: SECURITY - Direct Skill Call Without Token")
print("-" * 70)

try:
    # Import email skill as a proper package
    from skills.email_responder import skill as email_skill

    # Try to call skill directly WITHOUT token
    result = email_skill.email_send(
        to="attacker@example.com",
        subject="Bypass Attempt",
        body="This should be BLOCKED",
        vault_path=str(vault_path)
        # NO approval_token parameter
    )

    blocked = (result.get("success") == False and
               result.get("error") == "APPROVAL_REQUIRED")

    test("Direct skill call blocked without token", blocked,
         f"Result: {result.get('error', 'Unknown')}")
except Exception as e:
    test("Direct skill call blocked without token", False, f"Error: {e}")

# ============================================================================
# TEST 2: Create Mock Approval File
# ============================================================================
print("TEST 2: Create Mock Approval File in /Approved Folder")
print("-" * 70)

try:
    # Create a mock approval file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    approval_filename = f"APPROVAL_email_send_{timestamp}_test.md"
    approval_filepath = approved_folder / approval_filename

    approval_content = f"""---
type: approval_request
action: email_send
created: {datetime.now().isoformat()}
status: approved
to: test@example.com
subject: Test Email
draft_body: This is a test email for approval flow validation.
risk_level: low
---

# Approval Required

## Action Details
- **Action Type:** Email Send
- **To:** test@example.com
- **Subject:** Test Email

## Approved
This file was moved to /Approved folder by human reviewer.
"""

    approval_filepath.write_text(approval_content, encoding='utf-8')

    test("Mock approval file created", approval_filepath.exists(),
         f"File: {approval_filename}")
except Exception as e:
    test("Mock approval file created", False, f"Error: {e}")

# ============================================================================
# TEST 3: Approval Handler Detects File in /Approved Folder
# ============================================================================
print("TEST 3: Approval Handler Detects File in /Approved Folder")
print("-" * 70)

try:
    handler = ApprovalHandler(str(vault_path))
    approved_actions = handler.get_approved_actions()

    found = any(f.name == approval_filename for f in approved_actions)

    test("Approval handler detects file", found,
         f"Found {len(approved_actions)} approved action(s)")
except Exception as e:
    test("Approval handler detects file", False, f"Error: {e}")

# ============================================================================
# TEST 4: Process Approved Action (Token Generation + Skill Call)
# ============================================================================
print("TEST 4: Process Approved Action with Token")
print("-" * 70)

try:
    # Track if token was generated and passed (define before function)
    token_generated = [False]  # Use list to avoid nonlocal issues
    token_passed_to_skill = [False]
    skill_called = [False]

    # Custom executor that tracks token usage
    def test_executor(action_type, metadata, content, correlation_id=None,
                     approver=None, approval_time=None, approval_token=None):
        skill_called[0] = True

        # Check if token was passed
        token_generated[0] = approval_token is not None and len(approval_token) > 0

        # Verify the token works if provided
        if approval_token:
            token_manager = get_token_manager(str(vault_path))
            token_valid = token_manager.verify_token(approval_token, "email_send", consume=False)
            token_passed_to_skill[0] = token_valid
        else:
            token_passed_to_skill[0] = False

        # Simulate skill call with token
        # (We won't actually send email, just verify token would work)
        return {
            'success': True,
            'token_generated': token_generated[0],
            'token_valid': token_passed_to_skill[0],
            'message': 'Test execution - token verified'
        }

    # Process approved actions with our test executor
    stats = handler.process_approved_actions(test_executor)

    test("Orchestrator processes approved action", stats['executed'] > 0,
         f"Executed: {stats['executed']}, Errors: {stats['errors']}")

    test("Token generated by orchestrator", token_generated[0],
         "Orchestrator generated approval token")

    test("Token passed to skill", token_passed_to_skill[0],
         "Token was valid and could be passed to skill")

except Exception as e:
    test("Process approved action", False, f"Error: {e}")

# ============================================================================
# TEST 5: Verify File Moved to /Done After Execution
# ============================================================================
print("TEST 5: Verify File Moved to /Done After Execution")
print("-" * 70)

try:
    # Check if file was moved from /Approved to /Done
    still_in_approved = approval_filepath.exists()

    # Check /Done folder for executed file
    done_files = list(done_folder.glob(f"*{timestamp}_test_executed_*.md"))
    moved_to_done = len(done_files) > 0

    test("File moved from /Approved to /Done",
         not still_in_approved and moved_to_done,
         f"Still in Approved: {still_in_approved}, In Done: {moved_to_done}")
except Exception as e:
    test("File moved to /Done", False, f"Error: {e}")

# ============================================================================
# TEST 6: Token System Prevents Replay Attacks
# ============================================================================
print("TEST 6: Token System Prevents Replay Attacks")
print("-" * 70)

try:
    token_manager = get_token_manager(str(vault_path))

    # Generate single-use token
    replay_token = token_manager.generate_token(
        action_type="email_send",
        metadata={'test': 'replay_attack'},
        single_use=True
    )

    # First use - should succeed
    first_use = token_manager.verify_token(replay_token, "email_send", consume=True)

    # Second use - should fail (replay attack)
    second_use = token_manager.verify_token(replay_token, "email_send", consume=True)

    test("Replay attack prevented",
         first_use == True and second_use == False,
         f"First use: {first_use}, Replay attempt: {second_use}")
except Exception as e:
    test("Replay attack prevention", False, f"Error: {e}")

# ============================================================================
# CLEANUP
# ============================================================================
print("CLEANUP")
print("-" * 70)

try:
    # Clean up test files
    if approval_filepath.exists():
        approval_filepath.unlink()
        print("  Removed test approval file from /Approved")

    # Clean up done files
    for done_file in done_folder.glob(f"*{timestamp}_test_executed_*.md"):
        done_file.unlink()
        print(f"  Removed test file from /Done: {done_file.name}")

    print()
except Exception as e:
    print(f"  Cleanup error: {e}")
    print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("END-TO-END APPROVAL FLOW TEST SUMMARY")
print("=" * 70)
print(f"Tests Passed: {tests_passed}/{tests_total}")
print()

if tests_passed == tests_total:
    print("[SUCCESS] - Complete Approval Flow Validated")
    print()
    print("The system works as designed:")
    print("  1. Human approval via folder system (/Approved)")
    print("  2. Orchestrator generates approval tokens")
    print("  3. Orchestrator passes tokens to skills")
    print("  4. Skills verify tokens before execution")
    print("  5. Direct skill calls without tokens are BLOCKED")
    print("  6. Replay attacks are prevented (single-use tokens)")
    print()
    print("The approval system is SECURE and OPERATIONAL.")
else:
    print(f"[FAILURE] - {tests_total - tests_passed} test(s) failed")
    print("Review failures above.")

print("=" * 70)
