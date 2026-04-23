"""
LinkedIn Posting Service - Core Business Logic

Creates LinkedIn post drafts, posts to LinkedIn via Playwright,
and manages post lifecycle (draft → approved → posted → done).

No agent-related code — pure business logic only.
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


class LinkedInService:
    """Core LinkedIn posting service."""

    def __init__(self, vault_path: str = "AI_Employee_Vault", headless: bool = True):
        self.vault = Path(vault_path)
        self.headless = headless
        self.pending_approval = self.vault / "Pending_Approval"
        self.approved = self.vault / "Approved"
        self.done = self.vault / "Done"
        self.logs = self.vault / "Logs"
        self.screenshots = self.vault / "Screenshots"
        for d in [self.pending_approval, self.approved, self.done, self.logs, self.screenshots]:
            d.mkdir(parents=True, exist_ok=True)

        self.processed_file = self.logs / "linkedin_processed_posts.json"
        self.processed = self._load_processed()
        self.browser_session = Path(__file__).parent.parent.parent / "linkedin_browser_session"
        self.browser_session.mkdir(parents=True, exist_ok=True)

    def _load_processed(self) -> set:
        if self.processed_file.exists():
            try:
                with open(self.processed_file) as f:
                    return set(json.load(f).get("files", []))
            except Exception:
                pass
        return set()

    def _save_processed(self):
        try:
            with open(self.processed_file, "w") as f:
                json.dump({"last_updated": datetime.now().isoformat(), "files": list(self.processed)}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed: {e}")

    def create_post_draft(self, content: str, post_type: str = "announcement") -> Dict[str, Any]:
        """Create a LinkedIn post draft for human approval."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LINKEDIN_{post_type}_{timestamp}.md"
        filepath = self.pending_approval / filename

        markdown = f"""---
type: social_media_post
platform: linkedin
created: {datetime.now().isoformat()}
status: pending_approval
post_type: {post_type}
---

# LinkedIn Post Draft

## Content
{content}

## Posting Details
- **Platform:** LinkedIn
- **Type:** {post_type}
- **Visibility:** Public

## Approval Required
Move this file to `/Approved` folder to publish.

---
*Created by AI Employee LinkedIn Poster*
"""
        filepath.write_text(markdown, encoding="utf-8")
        self._log_event("post_created", {"file": filename, "type": post_type})

        return {"success": True, "filepath": str(filepath), "filename": filename, "post_type": post_type}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True
    )
    def publish_post(self, post_content: str) -> Dict[str, Any]:
        """
        Publish a post to LinkedIn via Playwright.

        Args:
            post_content: The post text to publish

        Returns:
            Dict with success status, screenshot path, and steps completed
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {"success": False, "error": "Playwright not installed. Run: pip install playwright && playwright install chromium"}

        result = {"success": False, "error": None, "screenshot": None, "steps_completed": []}

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    str(self.browser_session),
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage", "--no-sandbox"],
                    ignore_default_args=["--enable-automation"]
                )
                page = browser.pages[0]

                # Navigate
                page.goto("https://www.linkedin.com/feed/", timeout=60000)
                time.sleep(5)
                result["steps_completed"].append("Navigated to LinkedIn")

                # Check logged in
                url = page.url
                if "/login" in url or "/checkpoint" in url:
                    result["error"] = "Not logged in"
                    browser.close()
                    return result

                # Open composer
                try:
                    post_button = page.query_selector('[data-testid="update-component"]')
                    if post_button:
                        post_button.scroll_into_view_if_needed()
                        time.sleep(1)
                        post_button.click()
                        time.sleep(3)
                        result["steps_completed"].append("Opened composer")
                except Exception as e:
                    logger.warning(f"Composer open warning: {e}")

                # Type content
                typed = False
                editors = page.query_selector_all('div[contenteditable="true"]')
                for editor in editors:
                    try:
                        editor.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        editor.click()
                        time.sleep(1)
                        if editor.is_element_type():
                            editor.type(post_content, delay=30)
                            time.sleep(2)
                            typed = True
                            result["steps_completed"].append("Typed content")
                            break
                    except Exception:
                        continue

                if not typed:
                    page.keyboard.press("Tab")
                    time.sleep(1)
                    try:
                        page.keyboard.type(post_content, delay=30)
                        time.sleep(2)
                        typed = True
                        result["steps_completed"].append("Typed content (keyboard)")
                    except Exception as e:
                        result["error"] = f"Could not type: {e}"
                        browser.close()
                        return result

                # Click Post
                time.sleep(3)
                submitted = False
                for selector in ['button:has-text("Post")', '[aria-label="Post"]']:
                    btn = page.query_selector(selector)
                    if btn:
                        btn.scroll_into_view_if_needed()
                        time.sleep(1)
                        try:
                            btn.click()
                            submitted = True
                        except Exception:
                            page.keyboard.press("Enter")
                            submitted = True
                        break

                if not submitted:
                    page.keyboard.press("Control+Enter")
                    submitted = True

                time.sleep(3)
                result["steps_completed"].append("Submitted post")

                # Screenshot
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                ss_path = self.screenshots / f"linkedin_post_{ts}.png"
                try:
                    page.screenshot(path=str(ss_path))
                    result["screenshot"] = str(ss_path)
                except Exception:
                    pass

                browser.close()
                result["success"] = True
                return result

        except Exception as e:
            result["error"] = f"Browser error: {e}"
            return result

    def get_pending_posts(self) -> List[Dict[str, Any]]:
        """List pending post drafts."""
        if not self.pending_approval.exists():
            return []
        return [{"filename": f.name} for f in self.pending_approval.glob("*.md") if f.name not in self.processed]

    def get_approved_posts(self) -> List[Dict[str, Any]]:
        """List approved posts ready to publish."""
        if not self.approved.exists():
            return []
        return [{"filename": f.name, "filepath": str(f)} for f in self.approved.glob("*.md") if f.name not in self.processed]

    def mark_post_published(self, filename: str) -> Dict[str, Any]:
        """Move an approved post to Done with published metadata."""
        src = self.approved / filename
        if not src.exists():
            return {"success": False, "error": f"Not found: {filename}"}

        content = src.read_text(encoding="utf-8")
        content += f"\n---\nexecuted: {datetime.now().isoformat()}\nstatus: success\n---\n"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.done / f"{src.stem}_posted_{ts}{src.suffix}"
        dest.write_text(content, encoding="utf-8")
        src.unlink()
        self.processed.add(filename)
        self._save_processed()
        self._log_event("post_published", {"file": filename})
        return {"success": True, "destination": str(dest)}

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type, **details}
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
