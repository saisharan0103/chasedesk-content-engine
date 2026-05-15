"""Tests for analytics backfill into metrics.csv."""

from __future__ import annotations

import csv
import dataclasses
from datetime import date
from pathlib import Path

from src.analytics_sync import sync_metrics
from src.config import Config
from src.logging_utils import METRICS_HEADER, RunEntry, append_metrics


class FakeClient:
    """Stub TypefullyClient that just returns canned analytics rows."""

    def __init__(self, posts):
        self._posts = posts

    def iter_analytics_posts(self, *, platform="x", page_size=100):
        yield from self._posts


def _make_metrics_csv(tmp_path: Path, draft_id: str) -> Path:
    logs_dir = tmp_path / "logs"
    entries = [
        RunEntry(
            slot=0,
            posted_for="2026-05-12",
            scheduled_local="2026-05-12 10:00 IST",
            scheduled_utc="2026-05-12T04:30:00Z",
            status="scheduled",
            strategy="pain_led_story",
            strategy_name="Pain-led story",
            shape="two_part",
            segment="solo_bookkeeper",
            seed_id="monday_email_queue",
            competitor_id=None,
            hook_type="operational_pain",
            tweet_text="some text",
            character_count=9,
            quality_passed=True,
            needs_human_review=False,
            regen_count=0,
            generator="openai",
            typefully_draft_id=draft_id,
        )
    ]
    append_metrics(logs_dir, date(2026, 5, 11), entries)
    return logs_dir / "metrics.csv"


def _read_row(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return next(csv.DictReader(fh))


def test_sync_fills_url_and_metrics(tmp_path):
    csv_path = _make_metrics_csv(tmp_path, draft_id="100")
    posts = [
        {
            "post_id": "tw1",
            "draft_id": 100,
            "url": "https://x.com/me/status/123",
            "metrics": {
                "impressions": 1234,
                "engagement": {
                    "likes": 10, "comments": 2, "shares": 1, "quotes": 0,
                    "saves": 5, "profile_clicks": 7, "link_clicks": 3,
                },
            },
        }
    ]
    cfg = dataclasses.replace(Config(), logs_dir=tmp_path / "logs", typefully_api_key="k", typefully_social_set_id="42")
    summary = sync_metrics(cfg, client=FakeClient(posts))

    assert summary["rows_matched"] == 1
    assert summary["rows_updated"] == 1
    row = _read_row(csv_path)
    assert row["x_published_url"] == "https://x.com/me/status/123"
    assert row["impressions"] == "1234"
    assert row["likes"] == "10"
    assert row["replies"] == "2"      # comments -> replies
    assert row["reposts"] == "1"      # shares -> reposts
    assert row["bookmarks"] == "5"
    assert row["profile_clicks"] == "7"
    assert row["url_clicks"] == "3"


def test_sync_is_idempotent_does_not_overwrite(tmp_path):
    csv_path = _make_metrics_csv(tmp_path, draft_id="100")
    # First sync populates everything
    posts = [{
        "post_id": "tw1", "draft_id": 100, "url": "https://x.com/me/status/123",
        "metrics": {"impressions": 1234, "engagement": {"likes": 10}},
    }]
    cfg = dataclasses.replace(Config(), logs_dir=tmp_path / "logs", typefully_api_key="k", typefully_social_set_id="42")
    sync_metrics(cfg, client=FakeClient(posts))
    # Second sync with DIFFERENT numbers should not overwrite filled cells
    posts2 = [{
        "post_id": "tw1", "draft_id": 100, "url": "https://x.com/different/status/999",
        "metrics": {"impressions": 9999, "engagement": {"likes": 99}},
    }]
    sync_metrics(cfg, client=FakeClient(posts2))
    row = _read_row(csv_path)
    assert row["x_published_url"] == "https://x.com/me/status/123"
    assert row["impressions"] == "1234"
    assert row["likes"] == "10"


def test_sync_skips_unmatched_rows(tmp_path):
    csv_path = _make_metrics_csv(tmp_path, draft_id="100")
    posts = [{
        "post_id": "tw1", "draft_id": 999, "url": "https://x.com/me/status/123",
        "metrics": {"impressions": 1, "engagement": {"likes": 1}},
    }]
    cfg = dataclasses.replace(Config(), logs_dir=tmp_path / "logs", typefully_api_key="k", typefully_social_set_id="42")
    summary = sync_metrics(cfg, client=FakeClient(posts))
    assert summary["rows_matched"] == 0
    row = _read_row(csv_path)
    assert row["x_published_url"] == ""
    assert row["impressions"] == ""


def test_csv_header_migrates_when_columns_added(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    # Write a fake old CSV that's MISSING x_published_url
    old_header = [c for c in METRICS_HEADER if c != "x_published_url"]
    p = logs_dir / "metrics.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=old_header)
        writer.writeheader()
        writer.writerow({c: ("100" if c == "typefully_draft_id" else "") for c in old_header})
    # Now run sync — it should migrate the header and fill the URL
    posts = [{
        "post_id": "tw1", "draft_id": 100, "url": "https://x.com/me/status/123",
        "metrics": {"impressions": 5, "engagement": {"likes": 1}},
    }]
    cfg = dataclasses.replace(Config(), logs_dir=logs_dir, typefully_api_key="k", typefully_social_set_id="42")
    sync_metrics(cfg, client=FakeClient(posts))
    row = _read_row(p)
    assert "x_published_url" in row
    assert row["x_published_url"] == "https://x.com/me/status/123"
