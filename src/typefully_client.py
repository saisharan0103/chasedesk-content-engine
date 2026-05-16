"""Thin Typefully API client.

Only what V1 needs: create a draft with a future schedule date.

Docs: https://api.typefully.com/  (auth header: X-API-KEY)
"""

from __future__ import annotations

from typing import Any

API_BASE = "https://api.typefully.com/v1"


class TypefullyError(RuntimeError):
    pass


class TypefullyClient:
    def __init__(self, api_key: str, *, session: Any = None, timeout: int = 30) -> None:
        if not api_key:
            raise TypefullyError("TYPEFULLY_API_KEY is not set")
        self.api_key = api_key
        self.timeout = timeout
        self._session = session

    def _http(self):
        if self._session is not None:
            return self._session
        import requests

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
