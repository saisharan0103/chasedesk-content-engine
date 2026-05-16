"""Run logs, metrics CSV, the rolling recent-posts file, and the review queue.

All of these live under `logs/` and are committed by the GitHub Action so state
(anti-repetition history, metrics for the weekly re-tune) survives between runs.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

RECENT_POSTS_FILE = "recent_posts.json"
METRICS_FILE = "metrics.csv"
REVIEW_DIR = "review_queue"
MAX_RECENT_POSTS_KEPT = 250

METRIC_COLUMNS = [
    "impressions",
    "likes",
    "replies",
    "reposts",
    "bookmarks",
    "profile_clicks",
    "url_clicks",
    "followers_gained",
    "waitlist_clicks",
]

_BASE_COLUMNS = [
    "run_date",
    "posted_for",
    "slot",
    "scheduled_local",
    "scheduled_utc",
    "status",
    "strategy",
    "strategy_name",
    "shape",
    "segment",
    "seed_id",
    "competitor_id",
    "hook_type",
    "character_count",
    "quality_passed",
    "needs_human_review",
    "regen_count",
    "generator",
    "source_ids",
    "risk_flags",
    "typefully_draft_id",
    "typefully_share_url",
    "failure_reasons",
    "tweet_text",
]
METRICS_HEADER = _BASE_COLUMNS + METRIC_COLUMNS


@dataclass
class RunEntry:
    slot: int
    posted_for: str
    scheduled_local: str
    scheduled_utc: str
    status: str  # scheduled | review_queue | skipped
    strategy: str
    strategy_name: str
    shape: str
    segment: str
    seed_id: str | None
    competitor_id: str | None
    hook_type: str
    tweet_text: str | None
    character_count: int
    quality_passed: bool
    needs_human_review: bool
    regen_count: int
    generator: str
    source_ids: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)
    typefully_draft_id: str | None = None
    typefully_share_url: str | None = None


# --------------------------------------------------------------------------- #
# directory helpers
# --------------------------------------------------------------------------- #
def ensure_logs_dir(logs_dir: Path) -> Path:
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


# --------------------------------------------------------------------------- #
# recent posts (anti-repetition state)
# --------------------------------------------------------------------------- #
def load_recent_posts(logs_dir: Path, lookback: int | None = None) -> list[dict]:
    path = Path(logs_dir) / RECENT_POSTS_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data[-lookback:] if lookback else data


def save_recent_posts(logs_dir: Path, posts: list[dict]) -> None:
    ensure_logs_dir(logs_dir)
    path = Path(logs_dir) / RECENT_POSTS_FILE
    trimmed = posts[-MAX_RECENT_POSTS_KEPT:]
    path.write_text(json.dumps(trimmed, indent=2, ensure_ascii=False), encoding="utf-8")


def recent_seed_ids_within_cooldown(recent_posts: list[dict], target_day: date, cooldown_days: int) -> set[str]:
    if cooldown_days <= 0:
        return set()
    cutoff = target_day - timedelta(days=cooldown_days)
    out: set[str] = set()
    for entry in recent_posts:
        raw = entry.get("posted_for") or entry.get("date")
        if not raw:
            continue
        try:
            when = date.fromisoformat(str(raw)[:10])
        except ValueError:
            continue
        if when >= cutoff:
            sid = entry.get("seed_id")
            if sid:
                out.add(sid)
    return out


# --------------------------------------------------------------------------- #
# run log (markdown, human-readable)
# --------------------------------------------------------------------------- #
def write_run_log(logs_dir: Path, run_date: date, *, target_day: date, entries: list[RunEntry], notes: list[str]) -> Path:
    ensure_logs_dir(logs_dir)
    path = Path(logs_dir) / f"{run_date.isoformat()}.md"
    lines: list[str] = []
    lines.append(f"# ChaseDesk content run — {run_date.isoformat()}")
    lines.append("")
    lines.append(f"- Posting day: **{target_day.isoformat()}**")
    lines.append(f"- Slots: {len(entries)}")
    if notes:
        lines.append("- Notes:")
        for note in notes:
            lines.append(f"  - {note}")
    lines.append("")
    for entry in entries:
        lines.append(f"## Slot {entry.slot + 1} — {entry.scheduled_local} ({entry.status})")
        lines.append(f"- Strategy: `{entry.strategy}` ({entry.strategy_name})")
        lines.append(f"- Shape: `{entry.shape}` · Segment: `{entry.segment}` · Hook: `{entry.hook_type}`")
        lines.append(f"- Seed: `{entry.seed_id or '-'}` · Competitor: `{entry.competitor_id or '-'}` · Generator: `{entry.generator}`")
        lines.append(f"- Quality passed: {entry.quality_passed} · Regenerations: {entry.regen_count} · Needs review: {entry.needs_human_review}")
        if entry.risk_flags:
            lines.append(f"- Risk flags: {', '.join(entry.risk_flags)}")
        if entry.source_ids:
            lines.append(f"- Source facts: {', '.join(entry.source_ids)}")
        if entry.failure_reasons:
            lines.append(f"- Failure reasons: {', '.join(entry.failure_reasons)}")
        if entry.typefully_draft_id or entry.typefully_share_url:
            lines.append(f"- Typefully: id={entry.typefully_draft_id} url={entry.typefully_share_url}")
        lines.append("")
        if entry.tweet_text:
            lines.append("```")
            lines.append(entry.tweet_text)
            lines.append("```")
        else:
            lines.append("_(no tweet produced)_")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# metrics CSV (one row per slot; metric columns left blank for later backfill)
# --------------------------------------------------------------------------- #
def append_metrics(logs_dir: Path, run_date: date, entries: list[RunEntry]) -> Path:
    ensure_logs_dir(logs_dir)
    path = Path(logs_dir) / METRICS_FILE
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=METRICS_HEADER)
        if new_file:
            writer.writeheader()
        for entry in entries:
            row = {
                "run_date": run_date.isoformat(),
                "posted_for": entry.posted_for,
                "slot": entry.slot,
                "scheduled_local": entry.scheduled_local,
                "scheduled_utc": entry.scheduled_utc,
                "status": entry.status,
                "strategy": entry.strategy,
                "strategy_name": entry.strategy_name,
                "shape": entry.shape,
                "segment": entry.segment,
                "seed_id": entry.seed_id or "",
                "competitor_id": entry.competitor_id or "",
                "hook_type": entry.hook_type,
                "character_count": entry.character_count,
                "quality_passed": entry.quality_passed,
                "needs_human_review": entry.needs_human_review,
                "regen_count": entry.regen_count,
                "generator": entry.generator,
                "source_ids": ";".join(entry.source_ids),
                "risk_flags": ";".join(entry.risk_flags),
                "typefully_draft_id": entry.typefully_draft_id or "",
                "typefully_share_url": entry.typefully_share_url or "",
                "failure_reasons": " | ".join(entry.failure_reasons),
                "tweet_text": (entry.tweet_text or "").replace("\n", "\\n"),
            }
            for col in METRIC_COLUMNS:
                row[col] = ""
            writer.writerow(row)
    return path


# --------------------------------------------------------------------------- #
# review queue (json = source of truth for src/review.py; md = human-readable)
# --------------------------------------------------------------------------- #
def write_review_queue(logs_dir: Path, run_date: date, entries: list[RunEntry]) -> tuple[Path, Path]:
    review_dir = ensure_logs_dir(Path(logs_dir) / REVIEW_DIR)
    json_path = review_dir / f"{run_date.isoformat()}.json"
    md_path = review_dir / f"{run_date.isoformat()}.md"

    items = []
    for entry in entries:
        item = asdict(entry)
        item["decision"] = "pending"  # pending | approved | rejected
        item["rejection_reason"] = None
        items.append(item)
    json_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [f"# Review queue — {run_date.isoformat()}", "", "Approve/reject with `python -m src.review`.", ""]
    for i, entry in enumerate(entries):
        md_lines.append(f"## #{i} — `{entry.strategy}` → posting day {entry.posted_for} at {entry.scheduled_local}")
        md_lines.append(f"- Risk flags: {', '.join(entry.risk_flags) or '-'} · Competitor: `{entry.competitor_id or '-'}`")
        md_lines.append("")
        md_lines.append("```")
        md_lines.append(entry.tweet_text or "(no text)")
        md_lines.append("```")
        md_lines.append("")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    return json_path, md_path
