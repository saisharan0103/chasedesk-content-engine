"""End-to-end smoke test using the stub generator (no API keys, no network)."""

import dataclasses
import os
from datetime import date
from pathlib import Path

from src.config import Config
from src.logging_utils import METRICS_FILE, RECENT_POSTS_FILE
from src.orchestrator import run


def test_run_with_stub_generator(tmp_path, monkeypatch):
    # ensure no OpenAI key -> stub path -> forces dry-run
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = dataclasses.replace(
        Config(),
        openai_api_key="",
        typefully_api_key="",
        dry_run=True,
        posts_per_day=3,
        content_dir=Path("content"),
        logs_dir=tmp_path / "logs",
        schedule_random_seed=7,
    )
    entries = run(cfg, run_date=date(2026, 5, 11), target_day=date(2026, 5, 12))

    assert len(entries) == 3
    statuses = {e.status for e in entries}
    assert statuses <= {"dry_run", "review_queue", "skipped"}
    # at least something was produced
    assert any(e.tweet_text for e in entries)

    logs = cfg.logs_dir
    assert (logs / "2026-05-11.md").exists()
    assert (logs / METRICS_FILE).exists()
    assert (logs / RECENT_POSTS_FILE).exists()


def test_run_is_reproducible_with_seed(tmp_path):
    def _run(dirname):
        cfg = dataclasses.replace(
            Config(),
            openai_api_key="",
            typefully_api_key="",
            dry_run=True,
            content_dir=Path("content"),
            logs_dir=tmp_path / dirname,
            schedule_random_seed=42,
        )
        return [(e.strategy, e.scheduled_utc, e.tweet_text) for e in run(cfg, run_date=date(2026, 5, 11), target_day=date(2026, 5, 12))]

    assert _run("a") == _run("b")
