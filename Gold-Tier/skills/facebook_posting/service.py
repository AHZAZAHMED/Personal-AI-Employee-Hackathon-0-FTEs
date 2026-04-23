"""
Facebook Posting Service - Core Business Logic

Monitors Facebook Page mentions, creates posts, and tracks engagement
via Facebook Graph API.

No agent-related code — pure business logic only.
"""

import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load credentials
for env_file in [Path(__file__).parent.parent.parent / ".env",
                Path(__file__).parent.parent.parent / ".facebook_credentials.env"]:
    if env_file.exists():
        load_dotenv(env_file)
        break

FACEBOOK_API_VERSION = "v18.0"
FACEBOOK_GRAPH_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"

logger = logging.getLogger(__name__)


class FacebookClient:
    """Facebook Graph API client."""

    def __init__(self):
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.page_token = os.getenv("FACEBOOK_PAGE_TOKEN")
        self.user_token = os.getenv("FACEBOOK_USER_TOKEN")

        if not all([self.app_id, self.app_secret, self.page_id, self.page_token]):
            raise ValueError("Missing Facebook credentials. Set FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_PAGE_ID, FACEBOOK_PAGE_TOKEN in .env")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
        reraise=True
    )
    def _request(self, endpoint: str, params: Dict = None, post: bool = False) -> Dict:
        url = f"{FACEBOOK_GRAPH_URL}/{endpoint}"
        params = params or {}
        params["access_token"] = self.page_token
        try:
            resp = requests.post(url, params=params, timeout=30) if post else requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Facebook API request failed: {e}")
            raise

    def get_page_info(self) -> Dict[str, Any]:
        return self._request(self.page_id, {"fields": "id,name,username,about,followers_count"})

    def get_mentions(self, since: Optional[datetime] = None, limit: int = 50) -> List[Dict[str, Any]]:
        params = {"fields": "id,message,from,created_time,permalink_url", "limit": limit}
        if since:
            params["since"] = since.strftime("%Y-%m-%dT%H:%M:%S+0000")
        result = self._request(f"{self.page_id}/feed", params)
        return result.get("data", [])

    def create_post(self, message: str, link: Optional[str] = None, photo_url: Optional[str] = None) -> Dict[str, Any]:
        params = {"message": message}
        if link:
            params["link"] = link
        if photo_url:
            params["url"] = photo_url
        result = self._request(f"{self.page_id}/feed", params, post=True)
        return {"success": True, "post_id": result.get("id"), "message": message}

    def get_insights(self, days: int = 7) -> Dict[str, Any]:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")
        params = {"metric": "page_impressions_unique,page_engaged_users,page_post_engagements,page_fans", "since": since, "until": until}
        result = self._request(f"{self.page_id}/insights", params)
        insights = {}
        for metric in result.get("data", []):
            insights[metric["name"]] = {"values": metric.get("values", []), "period": metric.get("period", "day")}
        return insights


class FacebookService:
    """Core Facebook service — mentions, posting, insights."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.needs_action = self.vault / "Needs_Action"
        self.logs = self.vault / "Logs"
        for d in [self.needs_action, self.logs]:
            d.mkdir(parents=True, exist_ok=True)

        self.processed_file = self.logs / "facebook_processed.json"
        self.processed_ids = self._load_processed()

        try:
            self.fb = FacebookClient()
            self.client_available = True
        except Exception:
            self.fb = None
            self.client_available = False

    def _load_processed(self) -> set:
        if self.processed_file.exists():
            try:
                with open(self.processed_file) as f:
                    return set(json.load(f).get("processed_ids", []))
            except Exception:
                pass
        return set()

    def _save_processed(self):
        try:
            with open(self.processed_file, "w") as f:
                json.dump({"processed_ids": list(self.processed_ids)[-1000:]}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed: {e}")

    def check_mentions(self, since_hours: int = 24) -> Dict[str, Any]:
        """Check for new Facebook mentions."""
        if not self.client_available:
            return {"success": False, "error": "Facebook client not available (missing credentials)"}

        try:
            since = datetime.now() - timedelta(hours=since_hours)
            mentions = self.fb.get_mentions(since=since)

            new_mentions = [m for m in mentions if m.get("id") not in self.processed_ids]

            for m in new_mentions:
                self.processed_ids.add(m.get("id"))
            self._save_processed()

            return {"success": True, "mentions": new_mentions, "count": len(new_mentions), "total_found": len(mentions)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_post(self, message: str, link: Optional[str] = None, photo_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a Facebook Page post."""
        if not self.client_available:
            return {"success": False, "error": "Facebook client not available"}
        try:
            return self.fb.create_post(message, link, photo_url)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get Facebook Page insights."""
        if not self.client_available:
            return {"success": False, "error": "Facebook client not available"}
        try:
            insights = self.fb.get_insights(days=days)
            return {"success": True, "insights": insights}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_action_files(self, mentions: List[Dict[str, Any]]) -> List[str]:
        """Create .md action files in Needs_Action/ for each mention."""
        created = []
        for item in mentions:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"FACEBOOK_mention_{ts}.md"
            filepath = self.needs_action / filename

            from_name = item.get("from", {}).get("name", "Unknown")
            message = item.get("message", "")
            created_time = item.get("created_time", "")
            permalink = item.get("permalink_url", "")

            content = f"""---
type: facebook_mention
from: {from_name}
received: {created_time}
priority: normal
status: pending
facebook_id: {item.get('id')}
permalink: {permalink}
---

# Facebook Mention

**From:** {from_name}
**Received:** {created_time}

## Content

{message}

## Link

[View on Facebook]({permalink})

## Suggested Actions

- [ ] Review mention
- [ ] Determine if response needed
- [ ] Draft response
- [ ] Post reply (requires approval)
- [ ] Archive after processing

---
*Detected by Facebook Watcher*
"""
            filepath.write_text(content, encoding="utf-8")
            created.append(str(filepath))
        return created

    def test_connection(self) -> Dict[str, Any]:
        """Test Facebook API connection."""
        if not self.client_available:
            return {"success": False, "error": "Facebook client not available"}
        try:
            info = self.fb.get_page_info()
            return {"success": True, "page_name": info.get("name"), "page_id": info.get("id")}
        except Exception as e:
            return {"success": False, "error": str(e)}
