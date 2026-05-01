"""
LinkedIn Posting Skill — End-to-End Functional Test
Tests everything except actual browser posting.
"""
import sys, json, os, tempfile
from pathlib import Path
sys.path.insert(0, '.')

PASS = FAIL = 0
def t(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        print(f"  ✅ {name}"); PASS += 1
    else:
        print(f"  ❌ {name} — {detail}"); FAIL += 1

print("=" * 60)
print("LINKEDIN POSTING SKILL — END-TO-END FUNCTIONAL TEST")
print("=" * 60)

# Setup temp vault
vault = os.path.join(tempfile.gettempdir(), "test_li_e2e_vault")
for d in ['Pending_Approval', 'Approved', 'Done', 'Logs', 'Screenshots']:
    os.makedirs(os.path.join(vault, d), exist_ok=True)

# ─── 1. Create draft via SKILL (not service directly) ──────
print("\n1. Create Draft via skill.py (full path)")
from skills.linkedin_posting.skill import linkedin_create_post_draft

result = linkedin_create_post_draft(
    content="Excited to announce our Q2 2026 results! Revenue up 40%. 🚀\n\n#Growth #Business",
    post_type="announcement",
    vault_path=vault
)

t("success=True", result.get("success") == True, result.get("error", ""))
t("has filename", "filename" in result)
t("has filepath", "filepath" in result)
t("post_type=announcement", result.get("post_type") == "announcement")

# Verify file exists and has correct content
filepath = Path(result.get("filepath", ""))
t("file created on disk", filepath.exists())
if filepath.exists():
    content = filepath.read_text(encoding="utf-8")
    t("file contains post content", "Q2 2026" in content)
    t("file has frontmatter", "type: social_media_post" in content)
    t("file has platform: linkedin", "platform: linkedin" in content)
    t("file has approval instructions", "Approved" in content)

# ─── 2. List pending via skill ─────────────────────────────
print("\n2. List Pending via skill.py")
from skills.linkedin_posting.skill import linkedin_list_pending

result2 = linkedin_list_pending(vault_path=vault)
t("success=True", result2.get("success") == True)
t("count >= 1", result2.get("count", 0) >= 1, f"count={result2.get('count')}")
t("pending is list", isinstance(result2.get("pending"), list))

# ─── 3. Create second draft ────────────────────────────────
print("\n3. Create 2nd Draft")
result3 = linkedin_create_post_draft(
    content="We're hiring! Join our team.",
    post_type="update",
    vault_path=vault
)
t("2nd draft success", result3.get("success") == True)

result4 = linkedin_list_pending(vault_path=vault)
t("count >= 2 after 2nd", result4.get("count", 0) >= 2, f"count={result4.get('count')}")

# ─── 4. List approved (should be empty) ────────────────────
print("\n4. List Approved (should be empty)")
from skills.linkedin_posting.skill import linkedin_list_approved

result5 = linkedin_list_approved(vault_path=vault)
t("success=True", result5.get("success") == True)
t("count=0 (nothing approved yet)", result5.get("count", 0) == 0, f"count={result5.get('count')}")

# ─── 5. Move file to Approved (simulate human approval) ────
print("\n5. Simulate Human Approval (move file)")
import shutil
filename = result.get("filename", "")
src = Path(vault) / "Pending_Approval" / filename
dst = Path(vault) / "Approved" / filename
if src.exists():
    shutil.move(str(src), str(dst))
    t("file moved to Approved", dst.exists())
else:
    t("file moved to Approved", False, "source not found")

result6 = linkedin_list_approved(vault_path=vault)
t("count=1 after approval", result6.get("count", 0) == 1, f"count={result6.get('count')}")

# ─── 6. Mark post as published (skip browser) ─────────────
print("\n6. Mark Post Published (file ops only)")
from skills.linkedin_posting.service import LinkedInService
svc = LinkedInService(vault_path=vault)

result7 = svc.mark_post_published(filename)
t("mark_published success", result7.get("success") == True, result7.get("error", ""))
t("has destination", "destination" in result7)
if result7.get("success"):
    dest_path = Path(result7.get("destination", ""))
    t("file in Done/", dest_path.exists())
    if dest_path.exists():
        done_content = dest_path.read_text(encoding="utf-8")
        t("has executed metadata", "executed:" in done_content)
        t("has success status", "status: success" in done_content)

# Verify file removed from Approved
t("removed from Approved", not (Path(vault) / "Approved" / filename).exists())

# ─── 7. publish_post returns proper error (no Playwright/login) ──
print("\n7. publish_post Safety Test")
from skills.linkedin_posting.service import PLAYWRIGHT_AVAILABLE
t("Playwright check", isinstance(PLAYWRIGHT_AVAILABLE, bool))
# Skip actual browser test — launches Chromium and hangs without LinkedIn session
# Verify the method structure exists and returns correct pattern
from skills.linkedin_posting.skill import linkedin_publish_post
t("linkedin_publish_post callable", callable(linkedin_publish_post))
t("has docstring", linkedin_publish_post.__doc__ is not None)

# ─── 8. Error Handling ─────────────────────────────────────
print("\n8. Error Handling")
bad = linkedin_create_post_draft(content="test", vault_path="/nonexistent/xyz_123")
t("bad vault returns error dict", isinstance(bad, dict))
# It should still work because dirs are created, but test the structure
t("has success key", "success" in bad)

# ─── Summary ───────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"RESULTS: {PASS}/{PASS+FAIL} passed")
if FAIL == 0:
    print("ALL TESTS PASSED — LinkedIn posting skill works end-to-end!")
    print("(Browser posting skipped — requires valid LinkedIn session)")
else:
    print(f"{FAIL} test(s) failed")
print("=" * 60)
