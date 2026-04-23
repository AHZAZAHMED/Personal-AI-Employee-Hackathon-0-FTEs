"""
Instagram Posting Service - Core Business Logic

Monitors Instagram Business Account comments/mentions, posts images,
and tracks engagement via Facebook Graph API (same endpoint as Facebook).

No agent-related code — pure business logic only.
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

for env_file in [Path(__file__).parent.parent.parent / ".env",
                Path(__file__).parent.parent.parent / ".facebook_credentials.env"]:
    if env_file.exists():
        load_dotenv(env_file)
        break

GRAPH_API_URL = "https://graph.facebook.com/v18.0"
logger = logging.getLogger(__name__)


class InstagramClient:
    """Instagram Graph API client (uses Facebook credentials)."""

    def __init__(self):
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.page_token = os.getenv("FACEBOOK_PAGE_TOKEN")
        self.instagram_business_account_id = None

        if not all([self.page_id, self.page_token]):
            raise ValueError("Missing FACEBOOK_PAGE_ID or FACEBOOK_PAGE_TOKEN in .env")

        self._get_instagram_account()

    def _get_instagram_account(self):
        """Get Instagram Business Account ID linked to Facebook Page."""
        try:
            resp = requests.get(f"{GRAPH_API_URL}/{self.page_id}",
                                params={"fields": "instagram_business_account", "access_token": self.page_token},
                                timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "instagram_business_account" in data:
                self.instagram_business_account_id = data["instagram_business_account"]["id"]
        except Exception as e:
            logger.warning(f"Failed to get Instagram account: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout)),
        reraise=True
    )
    def _request(self, endpoint: str, method: str = "GET", params: Dict = None) -> Dict:
        url = f"{GRAPH_API_URL}/{endpoint}"
        params = params or {}
        params["access_token"] = self.page_token
        try:
            resp = requests.get(url, params=params, timeout=30) if method == "GET" else requests.post(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            # Try to get detailed error from Instagram API response
            error_detail = str(e)
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_json = e.response.json()
                    if 'error' in error_json:
                        error_detail = f"{error_json['error'].get('message', str(e))} (code: {error_json['error'].get('code', 'unknown')})"
            except:
                pass
            logger.error(f"Instagram API request failed: {error_detail}")
            raise Exception(error_detail)

    def get_account_info(self) -> Dict[str, Any]:
        if not self.instagram_business_account_id:
            return {"error": "Instagram Business Account not linked"}
        return self._request(self.instagram_business_account_id,
                             params={"fields": "username,biography,website,followers_count,follows_count,media_count"})

    def get_recent_media(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.instagram_business_account_id:
            return []
        result = self._request(f"{self.instagram_business_account_id}/media",
                               params={"fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count", "limit": limit})
        return result.get("data", [])

    def get_comments(self, media_id: str) -> List[Dict[str, Any]]:
        result = self._request(f"{media_id}/comments", params={"fields": "id,from,username,text,timestamp,like_count"})
        return result.get("data", [])

    def get_mentions(self) -> List[Dict[str, Any]]:
        if not self.instagram_business_account_id:
            return []
        result = self._request(f"{self.instagram_business_account_id}/mentioned_media",
                               params={"fields": "id,caption,media_type,media_url,permalink,timestamp,owner", "limit": 50})
        return result.get("data", [])

    def post_image(self, image_url: str, caption: str) -> Dict[str, Any]:
        """Post an image to Instagram (container + publish)."""
        if not self.instagram_business_account_id:
            return {"success": False, "error": "Instagram Business Account not linked"}
        try:
            # Step 1: Create container (don't include media_type for images)
            container = self._request(f"{self.instagram_business_account_id}/media", method="POST",
                                      params={"image_url": image_url, "caption": caption})
            container_id = container.get("id")
            time.sleep(2)
            # Step 2: Publish (don't include media_type here either)
            publish = self._request(f"{self.instagram_business_account_id}/media_publish", method="POST",
                                    params={"creation_id": container_id})
            return {"success": True, "post_id": publish.get("id")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_insights(self, metric: str = "impressions", days: int = 7) -> Dict[str, Any]:
        if not self.instagram_business_account_id:
            return {"error": "Instagram Business Account not linked"}
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")
        result = self._request(f"{self.instagram_business_account_id}/insights",
                               params={"metric": metric, "period": "day", "since": since, "until": until})
        return {"success": True, "insights": result.get("data", [])}


class InstagramService:
    """Core Instagram service — comments, posting, insights."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.needs_action = self.vault / "Needs_Action"
        self.logs = self.vault / "Logs"
        for d in [self.needs_action, self.logs]:
            d.mkdir(parents=True, exist_ok=True)

        self.processed_file = self.logs / "instagram_processed.json"
        self.processed_ids = self._load_processed()

        try:
            self.ig = InstagramClient()
            self.client_available = bool(self.ig.instagram_business_account_id)
        except Exception:
            self.ig = None
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

    def check_comments(self, recent_posts_limit: int = 5) -> Dict[str, Any]:
        """Check recent posts for new comments."""
        if not self.client_available:
            return {"success": False, "error": "Instagram client not available (no linked Business Account)"}
        try:
            media_list = self.ig.get_recent_media(limit=recent_posts_limit)
            all_comments = []
            for media in media_list:
                comments = self.ig.get_comments(media["id"])
                for c in comments:
                    if c.get("id") not in self.processed_ids:
                        all_comments.append({**c, "media_id": media["id"], "media_caption": media.get("caption", "")})
                        self.processed_ids.add(c["id"])
            self._save_processed()
            return {"success": True, "comments": all_comments, "count": len(all_comments)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_mentions(self) -> Dict[str, Any]:
        """Check for Instagram mentions."""
        if not self.client_available:
            return {"success": False, "error": "Instagram client not available"}
        try:
            mentions = self.ig.get_mentions()
            new_mentions = [m for m in mentions if m.get("id") not in self.processed_ids]
            for m in new_mentions:
                self.processed_ids.add(m["id"])
            self._save_processed()
            return {"success": True, "mentions": new_mentions, "count": len(new_mentions)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_image(self, image_url: str, caption: str) -> Dict[str, Any]:
        """Post an image to Instagram."""
        if not self.client_available:
            return {"success": False, "error": "Instagram client not available"}
        try:
            return self.ig.post_image(image_url, caption)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_insights(self, metric: str = "impressions", days: int = 7) -> Dict[str, Any]:
        """Get Instagram insights."""
        if not self.client_available:
            return {"success": False, "error": "Instagram client not available"}
        try:
            return self.ig.get_insights(metric=metric, days=days)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_action_files(self, items: List[Dict[str, Any]], item_type: str = "comment") -> List[str]:
        """Create .md action files in Needs_Action/."""
        created = []
        for item in items:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"INSTAGRAM_{item_type}_{ts}.md"
            filepath = self.needs_action / filename
            username = item.get("username", item.get("from", {}).get("username", "Unknown"))
            text = item.get("text", item.get("caption", ""))
            created_time = item.get("timestamp", "")
            permalink = item.get("permalink", "")

            content = f"""---
type: instagram_{item_type}
instagram_id: {item.get('id')}
username: {username}
received: {created_time}
priority: normal
status: pending
permalink: {permalink}
---

# Instagram {item_type.title()}

**Username:** @{username}
**Received:** {created_time}

## Content

{text}

## Link

[View on Instagram]({permalink})

## Suggested Actions

- [ ] Review {item_type}
- [ ] Determine if response needed
- [ ] Draft response
- [ ] Post reply (requires approval)
- [ ] Archive after processing

---
*Detected by Instagram Watcher*
"""
            filepath.write_text(content, encoding="utf-8")
            created.append(str(filepath))
        return created

    def test_connection(self) -> Dict[str, Any]:
        """Test Instagram API connection."""
        if not self.client_available:
            return {"success": False, "error": "Instagram client not available"}
        try:
            info = self.ig.get_account_info()
            if "error" in info:
                return {"success": False, "error": info["error"]}
            return {"success": True, "username": info.get("username"), "followers": info.get("followers_count")}
        except Exception as e:
            return {"success": False, "error": str(e)}
