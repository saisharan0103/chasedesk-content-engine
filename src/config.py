"""Environment-backed configuration. Mirrors `.env.example`."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path

try:  # optional, only needed for local `.env` loading
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience, not a requirement
    pass


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw not in (None, "") else default


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw not in (None, "") else default


def _opt_int(name: str) -> int | None:
    raw = os.getenv(name)
    return int(raw) if raw not in (None, "") else None


def _time(name: str, default: str) -> time:
    raw = (os.getenv(name) or default).strip()
    hh, mm = raw.split(":")
    return time(int(hh), int(mm))


@dataclass(frozen=True)
class Config:
    # OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip())
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o").strip())

    # Typefully (v2 API; social_set_id auto-discovers if blank)
    typefully_api_key: str = field(default_factory=lambda: os.getenv("TYPEFULLY_API_KEY", "").strip())
    typefully_social_set_id: str = field(default_factory=lambda: os.getenv("TYPEFULLY_SOCIAL_SET_ID", "").strip())

    # behaviour
    posts_per_day: int = field(default_factory=lambda: _int("POSTS_PER_DAY", 3))
    char_limit: int = field(default_factory=lambda: _int("CHAR_LIMIT", 240))
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Kolkata").strip())

    # randomized posting window
    post_window_start: time = field(default_factory=lambda: _time("POST_WINDOW_START", "09:00"))
    post_window_end: time = field(default_factory=lambda: _time("POST_WINDOW_END", "21:00"))
    min_gap_minutes: int = field(default_factory=lambda: _int("MIN_GAP_MINUTES", 180))
    schedule_random_seed: int | None = field(default_factory=lambda: _opt_int("SCHEDULE_RANDOM_SEED"))

    # generation / quality
    candidates_per_slot: int = field(default_factory=lambda: _int("CANDIDATES_PER_SLOT", 4))
    max_regen_attempts: int = field(default_factory=lambda: _int("MAX_REGEN_ATTEMPTS", 3))
    recent_posts_lookback: int = field(default_factory=lambda: _int("RECENT_POSTS_LOOKBACK", 30))
    similarity_threshold: float = field(default_factory=lambda: _float("SIMILARITY_THRESHOLD", 0.6))
    seed_cooldown_days: int = field(default_factory=lambda: _int("SEED_COOLDOWN_DAYS", 10))

    # review routing
    human_review_competitor_posts: bool = field(
        default_factory=lambda: _bool("HUMAN_REVIEW_COMPETITOR_POSTS", True)
    )

    # paths
    content_dir: Path = field(default_factory=lambda: Path(os.getenv("CONTENT_DIR", "content")))
    logs_dir: Path = field(default_factory=lambda: Path(os.getenv("LOGS_DIR", "logs")))


def load_config() -> Config:
    return Config()
