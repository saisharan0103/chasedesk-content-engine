"""Randomized posting times.

Each day we draw `n` times inside [window_start, window_end] (local to the
configured timezone) such that every consecutive pair is at least
`min_gap_minutes` apart, but the exact minute is otherwise random.

Algorithm: the window has `span` minutes; `(n-1) * min_gap` minutes are reserved
for the mandatory gaps; the remaining `slack` minutes are split into `n+1`
random non-negative chunks (one lead chunk before each post, plus a trailing
chunk after the last post — that trailing chunk is what keeps the final post
from always landing exactly at window_end).
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def _split_int(total: int, parts: int, rng: random.Random) -> list[int]:
    if parts <= 1:
        return [total]
    if total <= 0:
        return [0] * parts
    cuts = sorted(rng.randint(0, total) for _ in range(parts - 1))
    out: list[int] = []
    prev = 0
    for cut in cuts:
        out.append(cut - prev)
        prev = cut
    out.append(total - prev)
    return out


def random_post_times(
    day: date,
    *,
    n: int,
    window_start: time,
    window_end: time,
    min_gap_minutes: int,
    tz: str,
    rng: random.Random | None = None,
) -> list[datetime]:
    """Return `n` timezone-aware datetimes on `day`, sorted, gaps >= min_gap_minutes."""
    if n < 1:
        return []
    rng = rng or random.Random()
    zone = ZoneInfo(tz)
    start_dt = datetime.combine(day, window_start, tzinfo=zone)
    end_dt = datetime.combine(day, window_end, tzinfo=zone)
    span = int((end_dt - start_dt).total_seconds() // 60)
    if span <= 0:
        raise ValueError(f"posting window is empty or inverted: {window_start}–{window_end}")

    reserved = (n - 1) * min_gap_minutes
    if reserved > span:
        raise ValueError(
            f"cannot fit {n} posts with {min_gap_minutes}-minute gaps inside a {span}-minute window"
        )
    slack = span - reserved
    chunks = _split_int(slack, n + 1, rng)

    times: list[datetime] = []
    current = start_dt + timedelta(minutes=chunks[0])
    times.append(current)
    for i in range(1, n):
        current = current + timedelta(minutes=min_gap_minutes + chunks[i])
        times.append(current)
    return times


def to_utc_iso(dt: datetime) -> str:
    """ISO-8601 UTC string with a trailing Z, e.g. 2026-05-12T04:23:00Z (Typefully format)."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_in_tz(tz: str) -> datetime:
    return datetime.now(ZoneInfo(tz))


def resolve_target_day(
    *,
    tz: str,
    window_start: time,
    buffer_minutes: int = 15,
    reference: datetime | None = None,
) -> date:
    """Pick which day to schedule for: today if there's enough runway before the
    posting window opens, otherwise tomorrow.
    """
    ref = reference or now_in_tz(tz)
    today = ref.date()
    cutoff = datetime.combine(today, window_start, tzinfo=ZoneInfo(tz)) - timedelta(minutes=buffer_minutes)
    return today if ref < cutoff else today + timedelta(days=1)
