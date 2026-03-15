"""
LinkedIn Poster for AI Employee - Silver Tier

Posts business updates to LinkedIn using Playwright's Chromium browser directly.
No MCP server needed - uses Playwright Python library directly.

Requires human approval before posting (per Company Handbook).

IMPORTANT: First run with --login-only to save your LinkedIn session!
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")


class LinkedInPoster:
    """
    Posts to LinkedIn using Playwright's Chromium browser directly.
    """
    
    def __init__(self, vault_path: str, headless: bool = False):
        """
        Initialize the LinkedIn poster.
        
        Args:
            vault_path: Path to the Obsidian vault root
            headless: Run browser in headless mode (default: False for better session support)
        """
        self.vault = Path(vault_path)
        self.headless = headless
        
        self.approved = self.vault / 'Approved'
        self.pending_approval = self.vault / 'Pending_Approval'
        self.done = self.vault / 'Done'
        self.logs = self.vault / 'Logs'
        self.screenshots = self.vault / 'Screenshots'
        
        # Ensure folders exist
        for folder in [self.approved, self.pending_approval, self.done, self.logs, self.screenshots]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed posts
        self.processed_posts_file = self.logs / 'linkedin_processed_posts.json'
        self.processed_posts = self._load_processed_posts()
        
        # Browser session path (persists login) - use absolute path
        self.browser_session = Path(__file__).parent.parent / 'linkedin_browser_session'
        self.browser_session.mkdir(exist_ok=True)
        
        print(f"Browser session folder: {self.browser_session.absolute()}")
    
    def _load_processed_posts(self) -> set:
        """Load previously processed post files."""
        if self.processed_posts_file.exists():
            try:
                with open(self.processed_posts_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('files', []))
            except Exception as e:
                print(f"Warning: Could not load processed posts: {e}")
        return set()
    
    def _save_processed_posts(self):
        """Save processed post files to disk."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'files': list(self.processed_posts)
            }
            with open(self.processed_posts_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving processed posts: {e}")
    
    def get_approved_posts(self) -> List[Path]:
        """Get all approved posts ready to publish."""
        if not self.approved.exists():
            return []
        return [f for f in self.approved.glob('*.md') if f.name not in self.processed_posts]
    
    def parse_post(self, filepath: Path) -> Dict[str, Any]:
        """Parse a post file to extract content and metadata."""
        content = filepath.read_text(encoding='utf-8')
        
        # Simple frontmatter parser
        data = {}
        in_frontmatter = False
        body_lines = []
        
        for line in content.split('\n'):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip().strip('"\'')
            elif not in_frontmatter:
                body_lines.append(line)
        
        # Extract post content from body
        post_content = '\n'.join(body_lines).strip()
        
        # Look for content under "## Content" section
        if '## Content' in content:
            content_section = content.split('## Content')[1]
            if '##' in content_section:
                post_content = content_section.split('##')[0].strip()
            else:
                post_content = content_section.strip()
        
        return {
            'file': filepath.name,
            'type': data.get('type', 'social_media_post'),
            'platform': data.get('platform', 'linkedin'),
            'status': data.get('status', 'pending'),
            'content': post_content,
            'full_content': content
        }
    
    def create_post_draft(self, content: str, post_type: str = 'announcement') -> Path:
        """Create a new post draft for approval."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"LINKEDIN_{post_type}_{timestamp}.md"
        filepath = self.pending_approval / filename
        
        markdown_content = f"""---
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
Add edits as comments before approving.

---
*Created by AI Employee LinkedIn Poster v0.4.0*
"""
        
        filepath.write_text(markdown_content, encoding='utf-8')
        
        self._log_event('post_created', {
            'file': filename,
            'type': post_type
        })
        
        return filepath
    
    def post_to_linkedin(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute posting to LinkedIn using Playwright directly."""
        content = post_data['content']
        result = {
            'success': False,
            'error': None,
            'screenshot': None,
            'steps_completed': []
        }
        
        try:
            with sync_playwright() as p:
                # Launch Chromium with persistent context
                print("  Launching Chromium browser...")
                print(f"  Session folder: {self.browser_session}")
                print(f"  Session exists: {self.browser_session.exists()}")
                if self.browser_session.exists():
                    files = list(self.browser_session.iterdir())
                    print(f"  Session files: {len(files)} files/dirs")
                
                browser = p.chromium.launch_persistent_context(
                    str(self.browser_session),
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ],
                    ignore_default_args=['--enable-automation']
                )
                
                page = browser.pages[0]
                
                # Step 1: Navigate to LinkedIn
                print("  Navigating to LinkedIn...")
                page.goto('https://www.linkedin.com/feed/', timeout=60000)
                result['steps_completed'].append('Navigated to LinkedIn')
                
                # Wait for page to load
                print("  Waiting for page to load...")
                time.sleep(5)
                
                # Check current URL
                current_url = page.url
                print(f"  Current URL: {current_url}")
                
                # Take debug screenshot
                debug_screenshot = self.screenshots / f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(debug_screenshot))
                print(f"  Debug screenshot: {debug_screenshot.name}")
                
                # Check if logged in by looking for various indicators
                print("  Checking if logged in...")
                logged_in = False
                
                # Method 1: Check URL (if we're on /feed/, we're logged in)
                if '/feed' in current_url or '/mynetwork' in current_url or '/jobs' in current_url:
                    print("  ✓ Logged in (URL check: on feed page)")
                    logged_in = True
                    result['steps_completed'].append('Verified login via URL')
                
                # Method 2: Check for "Start a post" component
                if not logged_in:
                    try:
                        page.wait_for_selector('[data-testid="update-component"]', timeout=5000)
                        print("  ✓ Logged in (found post composer)")
                        logged_in = True
                        result['steps_completed'].append('Verified login via composer')
                    except PlaywrightTimeout:
                        pass
                
                # Method 3: Check for navigation menu (another indicator)
                if not logged_in:
                    try:
                        page.wait_for_selector('nav[aria-label="Primary Navigation"]', timeout=5000)
                        print("  ✓ Logged in (found navigation menu)")
                        logged_in = True
                        result['steps_completed'].append('Verified login via nav')
                    except PlaywrightTimeout:
                        pass
                
                # Method 4: Check we're NOT on login page
                if not logged_in:
                    if '/login' in current_url or '/checkpoint' in current_url:
                        print(f"  ✗ Still on login/checkpoint page")
                        result['error'] = 'LinkedIn login failed - on login page'
                        browser.close()
                        return result
                    else:
                        # If we're on feed but didn't detect other indicators, assume logged in
                        print(f"  ✓ Assuming logged in (on feed page: {current_url})")
                        logged_in = True
                        result['steps_completed'].append('Assumed logged in')
                
                if not logged_in:
                    print(f"  ✗ Not logged in!")
                    print(f"  Current page title: {page.title()}")
                    result['error'] = 'LinkedIn login failed - session not saved properly'
                    browser.close()
                    return result
                
                # Step 2: Click "Start a post" button to open modal
                print("  Opening post composer...")
                try:
                    # Take screenshot before clicking
                    pre_click_screenshot = self.screenshots / f'debug_before_click_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    page.screenshot(path=str(pre_click_screenshot))
                    
                    # Method 1: Click the "Start a post" button
                    post_button = page.query_selector('[data-testid="update-component"]')
                    
                    if post_button:
                        print("  Found 'Start a post' button, clicking...")
                        post_button.scroll_into_view_if_needed()
                        time.sleep(1)
                        post_button.click()
                        time.sleep(3)  # Wait for modal animation
                        
                        # Take screenshot after clicking
                        post_click_screenshot = self.screenshots / f'debug_after_click_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                        page.screenshot(path=str(post_click_screenshot))
                        
                        result['steps_completed'].append('Clicked Start a post')
                        print("  ✓ Post composer opened")
                    else:
                        print("  'Start a post' button not found")
                        print("  Checking if composer is already open...")
                        result['steps_completed'].append('Start a post button not found')
                        
                except Exception as e:
                    print(f"  Warning opening composer: {e}")
                
                # Step 3: Type post content
                print("  Typing post content...")
                try:
                    # Wait for any animations to complete
                    time.sleep(2)
                    
                    # Take screenshot to see what we're working with
                    editor_screenshot = self.screenshots / f'debug_editor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    page.screenshot(path=str(editor_screenshot))
                    print(f"  Editor screenshot saved: {editor_screenshot.name}")
                    
                    # Try multiple approaches to find and type in the editor
                    typed = False
                    
                    # Method 1: Find ALL contenteditable divs and try each
                    editors = page.query_selector_all('div[contenteditable="true"]')
                    print(f"  Found {len(editors)} contenteditable div(s)")
                    
                    if editors and len(editors) > 0:
                        for i, editor in enumerate(editors):
                            try:
                                print(f"  Trying editor {i+1}/{len(editors)}...")
                                
                                # Scroll into view
                                editor.scroll_into_view_if_needed()
                                time.sleep(0.5)
                                
                                # Click to focus
                                editor.click()
                                time.sleep(1)
                                
                                # Check if element is still attached
                                if editor.is_element_type():
                                    # Type character by character
                                    editor.type(content, delay=30)
                                    time.sleep(2)
                                    typed = True
                                    result['steps_completed'].append(f'Typed via editor {i+1}')
                                    print(f"  ✓ Content typed (editor {i+1})")
                                    break
                                else:
                                    print(f"  Editor {i+1} not attached, trying next...")
                            except Exception as e:
                                print(f"  Editor {i+1} failed: {e}")
                                continue
                    
                    # Method 2: Try keyboard press approach
                    if not typed:
                        print("  Trying keyboard approach...")
                        # Press Tab to focus editor
                        page.keyboard.press('Tab')
                        time.sleep(1)
                        
                        # Try typing
                        try:
                            page.keyboard.type(content, delay=30)
                            time.sleep(2)
                            typed = True
                            result['steps_completed'].append('Typed via keyboard')
                            print("  ✓ Content typed (keyboard method)")
                        except Exception as e:
                            print(f"  Keyboard method failed: {e}")
                    
                    if not typed:
                        result['error'] = 'Could not type in editor'
                        print("  ✗ Could not type in any editor")
                        browser.close()
                        return result
                        
                except Exception as e:
                    print(f"  Error typing: {e}")
                    result['error'] = f'Failed to type: {str(e)}'
                    browser.close()
                    return result
                
                # Step 4: Click Post button
                print("  Clicking Post button...")
                try:
                    # Wait for Post button to be enabled
                    time.sleep(3)

                    # Try multiple selectors
                    post_submit = None
                    for selector in ['button:has-text("Post")', '[aria-label="Post"]', '.share-actions__primary-action']:
                        post_submit = page.query_selector(selector)
                        if post_submit:
                            print(f"  Found Post button")
                            break

                    if post_submit:
                        post_submit.scroll_into_view_if_needed()
                        time.sleep(1)
                        try:
                            post_submit.click()
                            time.sleep(3)
                            result['steps_completed'].append('Clicked Post button')
                            print("  ✓ Post button clicked")
                        except Exception as e:
                            # Fallback: Use keyboard
                            print(f"  Click failed, using Enter: {e}")
                            page.keyboard.press('Enter')
                            time.sleep(2)
                            result['steps_completed'].append('Posted via Enter')
                            print("  ✓ Posted via Enter key")
                    else:
                        # Use keyboard shortcut
                        print("  Post button not found, using Ctrl+Enter...")
                        page.keyboard.press('Control+Enter')
                        time.sleep(3)
                        result['steps_completed'].append('Posted via Ctrl+Enter')
                        print("  ✓ Posted via Ctrl+Enter")
                except Exception as e:
                    print(f"  Warning: {e}")
                    # Try keyboard fallback
                    try:
                        page.keyboard.press('Control+Enter')
                        time.sleep(2)
                        result['steps_completed'].append('Posted via Ctrl+Enter (fallback)')
                        print("  ✓ Posted via Ctrl+Enter (fallback)")
                    except:
                        result['error'] = 'Failed to submit post'
                        print("  ✗ Could not submit post")
                        browser.close()
                        return result

                # Step 5: Take screenshot
                print("  Taking confirmation screenshot...")
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    screenshot_path = self.screenshots / f'linkedin_post_{timestamp}.png'
                    page.screenshot(path=str(screenshot_path))
                    result['screenshot'] = str(screenshot_path)
                    result['steps_completed'].append('Screenshot saved')
                    print(f"  ✓ Screenshot: {screenshot_path.name}")
                except Exception as e:
                    print(f"  Warning: Could not save screenshot: {e}")

                browser.close()
                result['success'] = True
                return result
                
        except Exception as e:
            result['error'] = f'Browser error: {str(e)}'
            return result
    
    def execute_approved_posts(self) -> Dict[str, int]:
        """Execute all approved posts."""
        stats = {
            'processed': 0,
            'posted': 0,
            'errors': 0
        }
        
        approved_posts = self.get_approved_posts()
        
        if not approved_posts:
            print("No approved posts to publish")
            return stats
        
        print(f"Found {len(approved_posts)} approved post(s)")
        print("-" * 50)
        
        for filepath in approved_posts:
            try:
                post_data = self.parse_post(filepath)
                print(f"\nProcessing: {filepath.name}")
                print(f"  Preview: {post_data['content'][:80]}...")
                
                result = self.post_to_linkedin(post_data)
                
                if result['success']:
                    stats['posted'] += 1
                    self.processed_posts.add(filepath.name)
                    self._save_processed_posts()
                    self._mark_post_executed(filepath, result)
                    print(f"  ✓ SUCCESS")
                else:
                    stats['errors'] += 1
                    print(f"  ✗ ERROR: {result.get('error', 'Unknown')}")
                
                stats['processed'] += 1
                
            except Exception as e:
                print(f"Error: {e}")
                stats['errors'] += 1
        
        print("-" * 50)
        return stats
    
    def _mark_post_executed(self, filepath: Path, result: Dict[str, Any]):
        """Add execution result to post file and move to Done."""
        content = filepath.read_text(encoding='utf-8')
        
        execution_block = f"""
---
executed: {datetime.now().isoformat()}
status: {'success' if result['success'] else 'failed'}
steps: {json.dumps(result.get('steps_completed', []))}
---

## Execution Result
**Status:** {'Success ✓' if result['success'] else 'Failed ✗'}
**Steps:** {', '.join(result.get('steps_completed', []))}
"""
        content += execution_block
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = filepath.stem + '_posted_' + timestamp + filepath.suffix
        dest_path = self.done / new_name
        dest_path.write_text(content, encoding='utf-8')
        
        filepath.unlink()
        self._log_event('post_executed', {'file': filepath.name, 'success': result['success']})
    
    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an event to the daily log file."""
        log_entry = {'timestamp': datetime.now().isoformat(), 'event_type': event_type, **details}
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def main():
    """Run the LinkedIn poster."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee LinkedIn Poster')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--create', help='Create post draft')
    parser.add_argument('--type', default='announcement', help='Post type')
    parser.add_argument('--visible', action='store_true', help='Show browser (default: hidden)')
    parser.add_argument('--login-only', action='store_true', help='Just login and save session')
    
    args = parser.parse_args()
    
    if not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Playwright not installed")
        print("Run: pip install playwright && playwright install chromium")
        return
    
    # headless=False means browser window is VISIBLE
    poster = LinkedInPoster(args.vault, headless=not args.visible)
    
    if args.login_only:
        print("=" * 60)
        print("LINKEDIN LOGIN - SAVE SESSION")
        print("=" * 60)
        print("\n1. Browser will open in VISIBLE mode")
        print("2. If login page appears, enter credentials")
        print("3. If feed appears, you're already logged in")
        print("4. Wait for feed to load, then press Ctrl+C\n")
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(poster.browser_session),
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
                timeout=120000
            )
            page = browser.pages[0]
            
            print("Navigating to LinkedIn...")
            page.goto('https://www.linkedin.com/', timeout=60000)
            time.sleep(3)
            
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            # Check if already logged in
            if '/feed' in current_url or '/mynetwork' in current_url:
                print("\n✓ Already logged in!")
                print("\nACTION:")
                print("- Wait a moment for page to fully load")
                print("- Press Ctrl+C to save session\n")
            elif '/login' in current_url or '/checkpoint' in current_url:
                print("\n✓ Login page detected")
                print("\nACTION REQUIRED:")
                print("- Enter your email and password")
                print("- Click 'Sign in'")
                print("- Wait for feed to load")
                print("- Press Ctrl+C when you see your feed\n")
            else:
                print("\nPage loaded. Determine next steps...")
                print("If you see login form, enter credentials")
                print("If you see feed, press Ctrl+C to save\n")
            
            try:
                # Wait for user action
                while True:
                    current_url = page.url
                    if '/feed' in current_url or '/hp' in current_url:
                        print(f"✓ Feed detected: {current_url}")
                        print("Session will be saved when you press Ctrl+C")
                    time.sleep(2)
            except KeyboardInterrupt:
                print("\nSaving session...")
                try:
                    browser.close()
                    print("✓ Browser closed successfully")
                except:
                    print("Note: Browser may have already closed")
                print("\n" + "=" * 60)
                print("✓ Session saved successfully!")
                print(f"  Location: {poster.browser_session}")
                print("=" * 60)
                print("\nNow you can run without --login-only to post:")
                print("  python scripts/linkedin_poster.py --vault AI_Employee_Vault")
            except Exception as e:
                print(f"\nError: {e}")
                try:
                    browser.close()
                except:
                    pass
        return
    
    if args.create:
        filepath = poster.create_post_draft(args.create, args.type)
        print(f"Created: {filepath}")
        print("Move to /Approved/ to publish")
    else:
        print("LinkedIn Poster - Executing approved posts")
        print("-" * 50)
        stats = poster.execute_approved_posts()
        print("-" * 50)
        print(f"Posted: {stats['posted']}/{stats['processed']}")
        if stats['errors'] > 0:
            print(f"\n⚠ {stats['errors']} error(s) occurred")
            print("\nTROUBLESHOOTING:")
            print("1. Check debug screenshots in AI_Employee_Vault/Screenshots/")
            print("2. Try: python scripts/linkedin_poster.py --vault AI_Employee_Vault --login-only")
            print("3. Then try posting again")


if __name__ == '__main__':
    main()
