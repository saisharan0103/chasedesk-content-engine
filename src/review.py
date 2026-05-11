"""Operator CLI: work the human-review queue, and re-tune strategy weights weekly.

Usage:
  python -m src.review list                       # show pending review items
  python -m src.review approve <date> <index>     # schedule a queued tweet to Typefully
  python -m src.review reject  <date> <index> "reason"
  python -m src.review retune                     # propose new strategy weights from metrics.csv
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from .config import load_config
from .content_loader import load_knowledge_base
from .logging_utils import METRICS_FILE, REVIEW_DIR
from .scheduler import to_utc_iso  # noqa: F401  (kept for parity / possible reuse)
from .typefully_client import TypefullyClient, TypefullyError


# --------------------------------------------------------------------------- #
# review queue
# --------------------------------------------------------------------------- #
def _queue_path(logs_dir: Path, day: str) -> Path:
    return Path(logs_dir) / REVIEW_DIR / f"{day}.json"


def _load_queue(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"no review queue file at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_queue(path: Path, items: list[dict]) -> None:
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_list(logs_dir: Path) -> int:
    review_dir = Path(logs_dir) / REVIEW_DIR
    if not review_dir.exists():
        print("no review queue directory yet — nothing pending.")
        return 0
    found = False
    for path in sorted(review_dir.glob("*.json")):
        items = json.loads(path.read_text(encoding="utf-8"))
        pending = [(i, it) for i, it in enumerate(items) if it.get("decision", "pending") == "pending"]
        if not pending:
            continue
        found = True
        day = path.stem
        print(f"\n=== {day} ({len(pending)} pending) ===")
        for i, it in pending:
            print(f"  [{i}] strategy={it['strategy']} posting_day={it['posted_for']} at {it['scheduled_local']}")
            print(f"      flags={', '.join(it.get('risk_flags') or []) or '-'} competitor={it.get('competitor_id') or '-'}")
            for line in (it.get("tweet_text") or "").splitlines():
                print(f"      | {line}")
    if not found:
        print("nothing pending.")
    return 0


def cmd_approve(logs_dir: Path, day: str, index: int) -> int:
    config = load_config()
    path = _queue_path(logs_dir, day)
    items = _load_queue(path)
    if index < 0 or index >= len(items):
        raise SystemExit(f"index {index} out of range (0..{len(items) - 1})")
    item = items[index]
    if item.get("decision") != "pending":
        raise SystemExit(f"item {index} already {item.get('decision')}")

    text = item["tweet_text"]
    schedule_utc = item["scheduled_utc"]
    tf = TypefullyClient(config.typefully_api_key, dry_run=config.dry_run)
    try:
        resp = tf.create_draft(text, schedule_date=schedule_utc)
    except TypefullyError as exc:
        raise SystemExit(f"Typefully error: {exc}")

    item["decision"] = "approved"
    item["typefully_draft_id"] = resp.get("id")
    item["typefully_share_url"] = resp.get("share_url")
    _save_queue(path, items)
    where = "DRY-RUN (not sent)" if config.dry_run else f"scheduled (id={resp.get('id')})"
    print(f"approved item {index} for {day} → {where} at {item['scheduled_local']}")
    return 0


def cmd_reject(logs_dir: Path, day: str, index: int, reason: str) -> int:
    path = _queue_path(logs_dir, day)
    items = _load_queue(path)
    if index < 0 or index >= len(items):
        raise SystemExit(f"index {index} out of range (0..{len(items) - 1})")
    item = items[index]
    if item.get("decision") != "pending":
        raise SystemExit(f"item {index} already {item.get('decision')}")
    item["decision"] = "rejected"
    item["rejection_reason"] = reason
    _save_queue(path, items)
    print(f"rejected item {index} for {day}: {reason}")
    print("Tip: if the same reason keeps appearing, add it to banned_phrases.yml or turn it into a quality check.")
    return 0


# --------------------------------------------------------------------------- #
# weekly re-tune
# --------------------------------------------------------------------------- #
_ENGAGEMENT_WEIGHTS = {
    "likes": 1.0,
    "replies": 3.0,
    "reposts": 3.0,
    "bookmarks": 2.0,
    "profile_clicks": 4.0,
    "url_clicks": 4.0,
    "followers_gained": 8.0,
    "waitlist_clicks": 10.0,
}


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def cmd_retune(logs_dir: Path, blend: float = 0.5) -> int:
    metrics_path = Path(logs_dir) / METRICS_FILE
    if not metrics_path.exists():
        raise SystemExit(f"no metrics file at {metrics_path} — run the engine first, then backfill metric columns.")
    kb = load_knowledge_base(load_config().content_dir)

    score_by_strategy: dict[str, float] = {s.id: 0.0 for s in kb.strategies}
    count_by_strategy: dict[str, int] = {s.id: 0 for s in kb.strategies}
    rows_with_metrics = 0
    with metrics_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sid = row.get("strategy")
            if sid not in score_by_strategy:
                continue
            impressions = _to_float(row.get("impressions", ""))
            engagement = sum(_ENGAGEMENT_WEIGHTS[k] * _to_float(row.get(k, "")) for k in _ENGAGEMENT_WEIGHTS)
            if impressions <= 0 and engagement <= 0:
                continue  # not yet backfilled
            rows_with_metrics += 1
            # engagement per 1k impressions if we have impressions, else raw engagement
            score = engagement / (impressions / 1000.0) if impressions > 0 else engagement
            score_by_strategy[sid] += score
            count_by_strategy[sid] += 1

    if rows_with_metrics == 0:
        raise SystemExit("metrics.csv has no backfilled engagement numbers yet — nothing to re-tune.")

    avg_score: dict[str, float] = {}
    for sid in score_by_strategy:
        c = count_by_strategy[sid]
        avg_score[sid] = (score_by_strategy[sid] / c) if c else 0.0

    total_score = sum(avg_score.values())
    perf_share = {
        sid: (avg_score[sid] / total_score if total_score > 0 else 1.0 / len(avg_score)) for sid in avg_score
    }

    new_weights: dict[str, float] = {}
    for s in kb.strategies:
        blended = blend * s.weight + (1.0 - blend) * perf_share[s.id]
        new_weights[s.id] = max(s.min_weight, min(0.40, blended))
    norm = sum(new_weights.values())
    new_weights = {sid: w / norm for sid, w in new_weights.items()}

    print(f"Re-tune based on {rows_with_metrics} post(s) with metrics (blend={blend:.2f}, current vs performance):\n")
    print(f"{'strategy':<24}{'current':>10}{'perf_share':>12}{'proposed':>12}{'posts':>8}")
    for s in kb.strategies:
        print(f"{s.id:<24}{s.weight:>10.3f}{perf_share[s.id]:>12.3f}{new_weights[s.id]:>12.3f}{count_by_strategy[s.id]:>8}")
    print("\nProposed `weight:` values for content/content_strategies.yml:")
    for s in kb.strategies:
        print(f"  {s.id}: {new_weights[s.id]:.3f}")
    print("\nReview these, then edit content/content_strategies.yml by hand. Don't auto-apply blindly — the sample is small.")
    return 0


# --------------------------------------------------------------------------- #
# entrypoint
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    argv = list(sys.argv[1:] if argv is None else argv)
    logs_dir = load_config().logs_dir
    if not argv:
        print(__doc__)
        return 1
    cmd, *rest = argv
    if cmd == "list":
        return cmd_list(logs_dir)
    if cmd == "approve":
        if len(rest) != 2:
            raise SystemExit("usage: python -m src.review approve <date> <index>")
        return cmd_approve(logs_dir, rest[0], int(rest[1]))
    if cmd == "reject":
        if len(rest) < 3:
            raise SystemExit('usage: python -m src.review reject <date> <index> "reason"')
        return cmd_reject(logs_dir, rest[0], int(rest[1]), " ".join(rest[2:]))
    if cmd == "retune":
        blend = float(rest[0]) if rest else 0.5
        return cmd_retune(logs_dir, blend=blend)
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
