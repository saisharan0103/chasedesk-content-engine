"""End-to-end run: pick strategies -> build prompts -> generate (real time) ->
quality-filter -> schedule in Typefully -> log.

Run it with:  python -m src.orchestrator

There is no dry-run mode. If both keys are present, generated+passing tweets are
sent to Typefully. Tweets that fail the quality filter are skipped; tweets that
need human review go to the review queue and can be approved with
`python -m src.review approve`.
"""

from __future__ import annotations

import random
import sys
from datetime import date, datetime

from .config import Config, load_config
from .content_loader import KnowledgeBase, load_knowledge_base
from .logging_utils import (
    RunEntry,
    append_metrics,
    ensure_logs_dir,
    load_recent_posts,
    recent_seed_ids_within_cooldown,
    save_recent_posts,
    write_review_queue,
    write_run_log,
)
from .openai_generator import GeneratorError, generate_candidates
from .prompt_builder import build_prompt
from .quality_filter import FilterResult, check_candidate
from .scheduler import random_post_times, resolve_target_day, to_utc_iso
from .story_seed_builder import build_packet
from .strategy_selector import select_strategies
from .typefully_client import TypefullyClient, TypefullyError


def _today(tz: str) -> date:
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo(tz)).date()


def run(
    config: Config | None = None,
    *,
    run_date: date | None = None,
    target_day: date | None = None,
    rng: random.Random | None = None,
    weight_overrides: dict[str, float] | None = None,
) -> list[RunEntry]:
    config = config or load_config()
    notes: list[str] = []

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    if not config.typefully_api_key:
        raise RuntimeError("TYPEFULLY_API_KEY is not set")

    kb = load_knowledge_base(config.content_dir)
    for warning in kb.warnings:
        notes.append(f"KB: {warning}")
        print(f"[i] KB: {warning}")

    rng = rng or random.Random(config.schedule_random_seed)
    run_date = run_date or _today(config.timezone)
    target_day = target_day or resolve_target_day(tz=config.timezone, window_start=config.post_window_start)
    notes.append(f"posting day = {target_day.isoformat()} (run on {run_date.isoformat()})")

    ensure_logs_dir(config.logs_dir)
    recent_posts = load_recent_posts(config.logs_dir)
    recent_texts = [p["text"] for p in recent_posts if p.get("text")][-config.recent_posts_lookback:]
    cooldown_seed_ids = recent_seed_ids_within_cooldown(recent_posts, target_day, config.seed_cooldown_days)

    n = config.posts_per_day
    strategies = select_strategies(kb, n, rng=rng, weight_overrides=weight_overrides)
    post_times = random_post_times(
        target_day,
        n=len(strategies),
        window_start=config.post_window_start,
        window_end=config.post_window_end,
        min_gap_minutes=config.min_gap_minutes,
        tz=config.timezone,
        rng=rng,
    )

    tf = TypefullyClient(config.typefully_api_key)
    entries: list[RunEntry] = []
    used_seed_ids: set[str] = set(cooldown_seed_ids)

    for slot, (strategy, when) in enumerate(zip(strategies, post_times)):
        packet = build_packet(
            kb,
            strategy,
            rng=rng,
            n_candidates=config.candidates_per_slot,
            char_limit=config.char_limit,
            recent_posts=recent_texts,
            exclude_seed_ids=used_seed_ids,
        )

        chosen: tuple[dict, FilterResult] | None = None
        last_reasons: list[str] = []
        regen_count = 0

        for attempt in range(max(1, config.max_regen_attempts)):
            try:
                messages, schema = build_prompt(kb, packet)
                candidates = generate_candidates(config, messages, schema)
            except GeneratorError as exc:
                last_reasons = [f"generation error: {exc}"]
                regen_count = attempt + 1
                continue

            evaluated = [
                (c, check_candidate(c, kb=kb, config=config, strategy=strategy, recent_posts=recent_texts))
                for c in candidates
            ]
            passing = [(c, r) for c, r in evaluated if r.passed]
            if passing:
                passing.sort(key=lambda cr: (cr[1].needs_human_review, len(cr[0].get("tweet", ""))))
                chosen = passing[0]
                regen_count = attempt
                break

            last_reasons = evaluated[0][1].reasons if evaluated else ["no candidates returned"]
            regen_count = attempt + 1
            packet = packet.with_retry_hints(last_reasons)

        scheduled_local = when.strftime("%Y-%m-%d %H:%M %Z")
        scheduled_utc = to_utc_iso(when)
        seed_id = packet.seed.id if packet.seed else None
        competitor_id = packet.competitor.id if packet.competitor else None

        if chosen is None:
            entries.append(
                RunEntry(
                    slot=slot,
                    posted_for=target_day.isoformat(),
                    scheduled_local=scheduled_local,
                    scheduled_utc=scheduled_utc,
                    status="skipped",
                    strategy=strategy.id,
                    strategy_name=strategy.display_name,
                    shape=packet.shape.id,
                    segment=packet.segment.id,
                    seed_id=seed_id,
                    competitor_id=competitor_id,
                    hook_type="-",
                    tweet_text=None,
                    character_count=0,
                    quality_passed=False,
                    needs_human_review=False,
                    regen_count=regen_count,
                    generator="openai",
                    failure_reasons=last_reasons,
                )
            )
            print(f"[x] slot {slot + 1}: skipped after {regen_count} attempt(s) - {'; '.join(last_reasons)}")
            continue

        candidate, result = chosen
        text = candidate["tweet"].strip()
        if seed_id:
            used_seed_ids.add(seed_id)

        if result.needs_human_review:
            status = "review_queue"
            draft_id = share_url = None
        else:
            try:
                resp = tf.create_draft(text, schedule_date=scheduled_utc)
                draft_id = resp.get("id")
                share_url = resp.get("share_url")
                status = "scheduled"
            except TypefullyError as exc:
                status = "skipped"
                draft_id = share_url = None
                result.reasons.append(f"typefully error: {exc}")
                print(f"[x] slot {slot + 1}: Typefully error - {exc}")

        entry = RunEntry(
            slot=slot,
            posted_for=target_day.isoformat(),
            scheduled_local=scheduled_local,
            scheduled_utc=scheduled_utc,
            status=status,
            strategy=strategy.id,
            strategy_name=strategy.display_name,
            shape=packet.shape.id,
            segment=packet.segment.id,
            seed_id=seed_id,
            competitor_id=competitor_id,
            hook_type=candidate.get("hook_type", "-"),
            tweet_text=text,
            character_count=len(text),
            quality_passed=True,
            needs_human_review=result.needs_human_review,
            regen_count=regen_count,
            generator="openai",
            source_ids=list(candidate.get("source_ids") or []),
            risk_flags=list(result.risk_flags),
            failure_reasons=[r for r in result.reasons] if status == "skipped" else [],
            typefully_draft_id=draft_id,
            typefully_share_url=share_url,
        )
        entries.append(entry)

        if status == "scheduled":
            recent_posts.append(
                {
                    "date": run_date.isoformat(),
                    "posted_for": target_day.isoformat(),
                    "text": text,
                    "seed_id": seed_id,
                    "strategy_id": strategy.id,
                }
            )
            recent_texts.append(text)

        marker = {"scheduled": "[ok]", "review_queue": "[rev]", "skipped": "[x]"}.get(status, "[?]")
        print(f"{marker}  slot {slot + 1} [{strategy.id}] {status} @ {scheduled_local}  ({len(text)} chars)")

    write_run_log(config.logs_dir, run_date, target_day=target_day, entries=entries, notes=notes)
    append_metrics(config.logs_dir, run_date, entries)
    save_recent_posts(config.logs_dir, recent_posts)

    review_entries = [e for e in entries if e.status == "review_queue"]
    if review_entries:
        json_path, _ = write_review_queue(config.logs_dir, run_date, review_entries)
        print(f"[rev] {len(review_entries)} tweet(s) waiting for review: {json_path}")

    scheduled = sum(1 for e in entries if e.status == "scheduled")
    review = len(review_entries)
    skipped = sum(1 for e in entries if e.status == "skipped")
    print(f"\nDone. scheduled={scheduled} review={review} skipped={skipped}")
    return entries


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        run()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
