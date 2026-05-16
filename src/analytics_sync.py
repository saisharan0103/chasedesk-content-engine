"""Backfill `logs/metrics.csv` from the Typefully v2 analytics endpoint.

For every row in metrics.csv that has a `typefully_draft_id` but missing metrics
or missing `x_published_url`, look up the matching post in
`GET /v2/social-sets/{id}/analytics/x/posts` and fill in:

  - x_published_url
  - impressions, likes, replies, reposts, bookmarks, profile_clicks, url_clicks

Bookmarks / url_clicks map to Typefully's `saves` / `link_clicks` (may be null
upstream; we leave the cell blank when so).

Idempotent: never overwrites a cell that's already filled.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .config import Config
from .logging_utils import METRICS_FILE, METRICS_HEADER, _migrate_csv_header
from .typefully_client import TypefullyClient, TypefullyError


# Typefully analytics field name -> our metrics.csv column name
_METRIC_MAP = {
    "likes": "likes",
    "comments": "replies",      # X replies
    "shares": "reposts",        # X reposts
    "saves": "bookmarks",       # may be null upstream
    "profile_clicks": "profile_clicks",
    "link_clicks": "url_clicks",
}


def _to_str(value: Any) -> str:
    return "" if value is None else str(value)


def _is_blank(value: str | None) -> bool:
    return value is None or value == ""


def sync_metrics(config: Config | None = None, *, client: TypefullyClient | None = None) -> dict:
    """Walk metrics.csv, fetch analytics, write metrics back. Returns a summary dict."""
    from .config import load_config

    config = config or load_config()
    path = Path(config.logs_dir) / METRICS_FILE
    if not path.exists():
        raise FileNotFoundError(f"no metrics file at {path}")

    _migrate_csv_header(path, METRICS_HEADER)

    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        header = reader.fieldnames or METRICS_HEADER

    client = client or TypefullyClient(
        config.typefully_api_key,
        social_set_id=config.typefully_social_set_id or None,
    )

    by_draft_id: dict[str, dict] = {}
    by_post_url: dict[str, dict] = {}
    try:
        for post in client.iter_analytics_posts(platform="x"):
            did = _to_str(post.get("draft_id"))
            url = _to_str(post.get("url"))
            if did:
                by_draft_id[did] = post
            if url:
                by_post_url[url] = post
    except TypefullyError as exc:
        raise RuntimeError(f"failed to fetch analytics: {exc}") from exc

    updated = matched = 0
    for row in rows:
        draft_id = _to_str(row.get("typefully_draft_id"))
        url_already = _to_str(row.get("x_published_url"))
        post = by_draft_id.get(draft_id) or by_post_url.get(url_already)
        if not post:
            continue
        matched += 1
        changed = False
        if _is_blank(row.get("x_published_url")):
            new_url = _to_str(post.get("url"))
            if new_url:
                row["x_published_url"] = new_url
                changed = True
        metrics = post.get("metrics") or {}
        engagement = (metrics.get("engagement") or {}) if isinstance(metrics, dict) else {}
        impressions = metrics.get("impressions") if isinstance(metrics, dict) else None
        if _is_blank(row.get("impressions")) and impressions is not None:
            row["impressions"] = _to_str(impressions)
            changed = True
        for src_field, dest_col in _METRIC_MAP.items():
            if dest_col not in row or not _is_blank(row.get(dest_col)):
                continue
            value = engagement.get(src_field)
            if value is None:
                continue
            row[dest_col] = _to_str(value)
            changed = True
        if changed:
            updated += 1

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in header})

    return {
        "rows_total": len(rows),
        "rows_matched": matched,
        "rows_updated": updated,
        "metrics_path": str(path),
    }
