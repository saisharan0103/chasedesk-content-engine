"""Thin Typefully API client.

Only what V1 needs: create a draft with a future schedule date. In dry-run mode
nothing is sent — the call just echoes back what *would* have been scheduled.

Docs: https://api.typefully.com/  (auth header: X-API-KEY)
"""

from __future__ import annotations

from typing import Any

API_BASE = "https://api.typefully.com/v1"


class TypefullyError(RuntimeError):
    pass


class TypefullyClient:
    def __init__(self, api_key: str, *, dry_run: bool = False, session: Any = None, timeout: int = 30) -> None:
        self.api_key = api_key
        self.dry_run = dry_run
        self.timeout = timeout
        self._session = session

    def _http(self):
        if self._session is not None:
            return self._session
        import requests  # imported lazily so dry-run works without the dependency

        self._session = requests.Session()
        return self._session

    def create_draft(
        self,
        content: str,
        *,
        schedule_date: str | None = None,
        threadify: bool = False,
        share: bool = True,
    ) -> dict:
        if self.dry_run:
            return {
                "dry_run": True,
                "content": content,
                "schedule_date": schedule_date,
                "id": None,
                "share_url": None,
            }
        if not self.api_key:
            raise TypefullyError("TYPEFULLY_API_KEY is not set but dry_run is False")

        body: dict[str, Any] = {"content": content, "threadify": threadify, "share": share}
        if schedule_date:
            body["schedule-date"] = schedule_date

        resp = self._http().post(
            f"{API_BASE}/drafts/",
            json=body,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            timeout=self.timeout,
        )
        if resp.status_code >= 300:
            raise TypefullyError(f"Typefully API {resp.status_code}: {resp.text}")
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}
