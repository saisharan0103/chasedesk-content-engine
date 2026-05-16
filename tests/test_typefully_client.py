"""Unit tests for the v2 Typefully client."""

from __future__ import annotations

import json

import pytest

from src.typefully_client import API_BASE, TypefullyClient, TypefullyError


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or (json.dumps(payload) if payload is not None else "")

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    def __init__(self):
        self.calls = []
        self._responses: list[FakeResponse] = []

    def enqueue(self, status=200, payload=None, text=""):
        self._responses.append(FakeResponse(status, payload, text))

    def request(self, method, url, json=None, params=None, headers=None, timeout=None):
        self.calls.append(
            {"method": method, "url": url, "json": json, "params": params, "headers": headers}
        )
        return self._responses.pop(0) if self._responses else FakeResponse(200, {})


def test_uses_bearer_auth_not_x_api_key():
    sess = FakeSession()
    sess.enqueue(201, {"id": 1, "share_url": None, "x_published_url": None})
    tf = TypefullyClient("my-key", social_set_id="42", session=sess)
    tf.create_draft("hi")
    call = sess.calls[-1]
    assert call["headers"]["Authorization"] == "Bearer my-key"
    assert "X-API-KEY" not in call["headers"]


def test_create_draft_uses_v2_path_and_platforms_body():
    sess = FakeSession()
    sess.enqueue(201, {"id": 99, "share_url": "https://t.fy/abc", "x_published_url": None})
    tf = TypefullyClient("k", social_set_id="42", session=sess)
    resp = tf.create_draft("hello world", schedule_date="2026-05-17T04:30:00Z")
    assert resp["id"] == 99
    call = sess.calls[-1]
    assert call["method"] == "POST"
    assert call["url"] == f"{API_BASE}/social-sets/42/drafts"
    assert call["json"]["platforms"]["x"]["enabled"] is True
    assert call["json"]["platforms"]["x"]["posts"] == [{"text": "hello world"}]
    assert call["json"]["publish_at"] == "2026-05-17T04:30:00Z"


def test_auto_discovers_social_set_id_when_missing():
    sess = FakeSession()
    sess.enqueue(200, {"results": [{"id": 7, "name": "primary"}, {"id": 8}]})
    sess.enqueue(201, {"id": 1, "share_url": None, "x_published_url": None})
    tf = TypefullyClient("k", session=sess)
    tf.create_draft("x")
    assert sess.calls[0]["url"] == f"{API_BASE}/social-sets"
    assert sess.calls[1]["url"] == f"{API_BASE}/social-sets/7/drafts"


def test_raises_on_http_error():
    sess = FakeSession()
    sess.enqueue(401, payload=None, text="Unauthorized")
    tf = TypefullyClient("k", social_set_id="42", session=sess)
    with pytest.raises(TypefullyError):
        tf.create_draft("x")


def test_iter_analytics_posts_paginates_and_stops():
    sess = FakeSession()
    sess.enqueue(200, {"results": [{"post_id": "1"}, {"post_id": "2"}]})
    sess.enqueue(200, {"results": [{"post_id": "3"}]})
    tf = TypefullyClient("k", social_set_id="42", session=sess)
    got = list(tf.iter_analytics_posts(page_size=2))
    assert [p["post_id"] for p in got] == ["1", "2", "3"]
    assert all("/analytics/x/posts" in c["url"] for c in sess.calls)


def test_missing_api_key_errors_at_construction():
    with pytest.raises(TypefullyError):
        TypefullyClient("", social_set_id="42")
