"""End-to-end smoke test with the OpenAI and Typefully calls mocked out."""

import dataclasses
from datetime import date
from pathlib import Path

from src.config import Config
from src.logging_utils import METRICS_FILE, RECENT_POSTS_FILE
from src.orchestrator import run


def _patch(monkeypatch):
    """Stub the real network-touching calls so the orchestrator can run offline."""

    def fake_generate(config, messages, schema, temperature=0.9):
        return [
            {
                "tweet": "Bookkeepers don't lose evenings because accounting is hard. They lose them chasing receipts that never arrived.",
                "shape": "two_part",
                "hook_type": "operational_pain",
                "character_count": 110,
                "source_ids": [],
                "risk_flags": [],
                "needs_human_review": False,
            }
        ]

    monkeypatch.setattr("src.orchestrator.generate_candidates", fake_generate)

    def fake_create_draft(self, content, *, schedule_date=None, threadify=False, share=True):
        return {"id": "draft_xyz", "share_url": "https://typefully.com/share/xyz"}

    monkeypatch.setattr("src.typefully_client.TypefullyClient.create_draft", fake_create_draft)


def test_run_end_to_end(tmp_path, monkeypatch):
    _patch(monkeypatch)
    cfg = dataclasses.replace(
        Config(),
        openai_api_key="sk-test",
        typefully_api_key="tf-test",
        posts_per_day=3,
        content_dir=Path("content"),
        logs_dir=tmp_path / "logs",
        schedule_random_seed=7,
    )
    entries = run(cfg, run_date=date(2026, 5, 11), target_day=date(2026, 5, 12))

    assert len(entries) == 3
    # only valid statuses now: scheduled | review_queue | skipped
    assert {e.status for e in entries} <= {"scheduled", "review_queue", "skipped"}
    assert any(e.tweet_text for e in entries)

    logs = cfg.logs_dir
    assert (logs / "2026-05-11.md").exists()
    assert (logs / METRICS_FILE).exists()
    assert (logs / RECENT_POSTS_FILE).exists()


def test_run_is_reproducible_with_seed(tmp_path, monkeypatch):
    _patch(monkeypatch)

    def _run(dirname):
        cfg = dataclasses.replace(
            Config(),
            openai_api_key="sk-test",
            typefully_api_key="tf-test",
            content_dir=Path("content"),
            logs_dir=tmp_path / dirname,
            schedule_random_seed=42,
        )
        return [(e.strategy, e.scheduled_utc, e.tweet_text) for e in run(cfg, run_date=date(2026, 5, 11), target_day=date(2026, 5, 12))]

    assert _run("a") == _run("b")


def test_missing_openai_key_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = dataclasses.replace(
        Config(),
        openai_api_key="",
        typefully_api_key="tf-test",
        content_dir=Path("content"),
        logs_dir=tmp_path / "logs",
    )
    import pytest

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        run(cfg, run_date=date(2026, 5, 11), target_day=date(2026, 5, 12))


def test_missing_typefully_key_fails(tmp_path, monkeypatch):
    cfg = dataclasses.replace(
        Config(),
        openai_api_key="sk-test",
        typefully_api_key="",
        content_dir=Path("content"),
        logs_dir=tmp_path / "logs",
    )
    import pytest

    with pytest.raises(RuntimeError, match="TYPEFULLY_API_KEY"):
        run(cfg, run_date=date(2026, 5, 11), target_day=date(2026, 5, 12))
