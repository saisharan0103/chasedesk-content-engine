"""Thin Typefully API v2 client.

Endpoints used:
  GET  /v2/social-sets                                 discover available social sets
  POST /v2/social-sets/{social_set_id}/drafts          create + schedule a draft
  GET  /v2/social-sets/{id}/drafts/{draft_id}          fetch a draft (for x_published_url)
  GET  /v2/social-sets/{id}/analytics/x/posts          per-post X metrics

In dry-run mode all writes/reads are no-ops (the request body is echoed back).

Docs: https://typefully.com/docs/api  (auth header: X-API-KEY)
"""

from __future__ import annotations

from typing import Any, Iterable

API_BASE = "https://api.typefully.com/v2"


class TypefullyError(RuntimeError):
    pass


class TypefullyClient:
    def __init__(
        self,
        api_key: str,
        *,
        social_set_id: str | int | None = None,
        dry_run: bool = False,
        session: Any = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key
        self.social_set_id = str(social_set_id) if social_set_id else None
        self.dry_run = dry_run
        self.timeout = timeout
        self._session = session

    # -- http helpers ------------------------------------------------------
    def _http(self):
        if self._session is not None:
            return self._session
        import requests  # lazily imported so dry-run works without it

        self._session = requests.Session()
        return self._session

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise TypefullyError("TYPEFULLY_API_KEY is not set")
        return {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

    def _request(self, method: str, path: str, *, json_body: dict | None = None, params: dict | None = None) -> dict:
        url = f"{API_BASE}{path}"
        resp = self._http().request(
            method,
            url,
            json=json_body,
            params=params,
            headers=self._headers(),
            timeout=self.timeout,
        )
        if resp.status_code >= 300:
            raise TypefullyError(f"Typefully {method} {path} -> {resp.status_code}: {resp.text}")
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}

    # -- discovery ---------------------------------------------------------
    def list_social_sets(self) -> list[dict]:
        data = self._request("GET", "/social-sets")
        if isinstance(data, dict):
            return data.get("results") or data.get("social_sets") or []
        return data or []

    def ensure_social_set_id(self) -> str:
        if self.social_set_id:
            return self.social_set_id
        sets = self.list_social_sets()
        if not sets:
            raise TypefullyError(
                "no social sets found on this Typefully account. "
                "Run `python -m src.review whoami` to inspect."
            )
        first = sets[0]
        sid = str(first.get("id") or first.get("social_set_id") or "")
        if not sid:
            raise TypefullyError(f"could not determine social_set_id from response: {first}")
        self.social_set_id = sid
        return sid

    # -- draft creation ----------------------------------------------------
    def create_draft(
        self,
        content: str,
        *,
        schedule_date: str | None = None,
        share: bool = True,
        draft_title: str | None = None,
        # accepted for orchestrator parity; v2 expresses threads via the posts array
        threadify: bool = False,
    ) -> dict:
        body: dict[str, Any] = {
            "platforms": {
                "x": {
                    "enabled": True,
                    "posts": [{"text": content}],
                }
            },
            "share": share,
        }
        if schedule_date:
            body["publish_at"] = schedule_date  # ISO 8601, or "now" / "next-free-slot"
        if draft_title:
            body["draft_title"] = draft_title

        if self.dry_run:
            return {
                "dry_run": True,
                "request": body,
                "id": None,
                "share_url": None,
                "x_published_url": None,
                "status": "dry_run",
            }
        sid = self.ensure_social_set_id()
        return self._request("POST", f"/social-sets/{sid}/drafts", json_body=body)

    # -- fetch a draft (x_published_url is populated after the draft publishes)
    def get_draft(self, draft_id: int | str) -> dict:
        if self.dry_run:
            return {"dry_run": True, "id": draft_id}
        sid = self.ensure_social_set_id()
        return self._request("GET", f"/social-sets/{sid}/drafts/{draft_id}")

    # -- analytics ---------------------------------------------------------
    def analytics_posts(self, *, platform: str = "x", limit: int = 100, offset: int = 0) -> dict:
        if self.dry_run:
            return {"results": [], "count": 0}
        sid = self.ensure_social_set_id()
        return self._request(
            "GET",
            f"/social-sets/{sid}/analytics/{platform}/posts",
            params={"limit": limit, "offset": offset},
        )

    def iter_analytics_posts(self, *, platform: str = "x", page_size: int = 100) -> Iterable[dict]:
        offset = 0
        while True:
            page = self.analytics_posts(platform=platform, limit=page_size, offset=offset)
            results = page.get("results") or []
            for r in results:
                yield r
            if not results or len(results) < page_size:
                break
            offset += page_size
