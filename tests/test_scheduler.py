import random
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from src.scheduler import random_post_times, resolve_target_day, to_utc_iso

TZ = "Asia/Kolkata"
WS = time(9, 0)
WE = time(21, 0)


def test_returns_n_times_in_window_with_min_gap():
    for seed in range(25):
        times = random_post_times(date(2026, 5, 12), n=3, window_start=WS, window_end=WE, min_gap_minutes=180, tz=TZ, rng=random.Random(seed))
        assert len(times) == 3
        assert times == sorted(times)
        for t in times:
            assert t.tzinfo is not None
            assert time(9, 0) <= t.time() <= time(21, 0)
        for a, b in zip(times, times[1:]):
            assert (b - a).total_seconds() >= 180 * 60


def test_last_post_not_pinned_to_window_end_across_seeds():
    last_times = set()
    for seed in range(50):
        ts = random_post_times(date(2026, 5, 12), n=3, window_start=WS, window_end=WE, min_gap_minutes=180, tz=TZ, rng=random.Random(seed))
        last_times.add(ts[-1].time())
    assert len(last_times) > 5  # genuinely varies


def test_deterministic_with_seed():
    a = random_post_times(date(2026, 5, 12), n=3, window_start=WS, window_end=WE, min_gap_minutes=180, tz=TZ, rng=random.Random(99))
    b = random_post_times(date(2026, 5, 12), n=3, window_start=WS, window_end=WE, min_gap_minutes=180, tz=TZ, rng=random.Random(99))
    assert a == b


def test_raises_when_impossible():
    with pytest.raises(ValueError):
        random_post_times(date(2026, 5, 12), n=10, window_start=WS, window_end=WE, min_gap_minutes=180, tz=TZ)


def test_to_utc_iso_format():
    dt = datetime(2026, 5, 12, 9, 30, tzinfo=ZoneInfo(TZ))
    s = to_utc_iso(dt)
    assert s.endswith("Z")
    assert s == "2026-05-12T04:00:00Z"


def test_resolve_target_day_runway():
    early = datetime(2026, 5, 11, 8, 0, tzinfo=ZoneInfo(TZ))
    late = datetime(2026, 5, 11, 9, 30, tzinfo=ZoneInfo(TZ))
    assert resolve_target_day(tz=TZ, window_start=WS, reference=early) == date(2026, 5, 11)
    assert resolve_target_day(tz=TZ, window_start=WS, reference=late) == date(2026, 5, 12)
