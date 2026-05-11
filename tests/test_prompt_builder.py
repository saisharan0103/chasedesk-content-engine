import random

from src.prompt_builder import CANDIDATE_JSON_SCHEMA, build_prompt
from src.story_seed_builder import build_packet


def _packet(kb, strategy_id, rng):
    return build_packet(
        kb,
        kb.strategy(strategy_id),
        rng=rng,
        n_candidates=4,
        char_limit=240,
        recent_posts=["a previous tweet about chasing receipts"],
    )


def test_build_prompt_structure(kb):
    packet = _packet(kb, "pain_led_story", random.Random(1))
    messages, schema = build_prompt(kb, packet)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    user = messages[1]["content"]
    assert "ChaseDesk" in user
    assert packet.strategy.display_name in user
    assert "Maximum 240 characters" in user
    assert "banned phrases" in user.lower()
    if packet.seed is not None:
        assert packet.seed.scene in user
    assert schema is CANDIDATE_JSON_SCHEMA


def test_schema_is_strict_friendly():
    s = CANDIDATE_JSON_SCHEMA
    assert s["additionalProperties"] is False
    item = s["properties"]["candidates"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == set(item["properties"].keys())


def test_category_contrast_prompt_mentions_competitor_rules(kb):
    # force a packet that names a competitor
    packet = build_packet(
        kb, kb.strategy("category_contrast"), rng=random.Random(2),
        n_candidates=3, char_limit=240, recent_posts=[], competitor_chance=1.0,
    )
    assert packet.competitor is not None
    _, _ = build_prompt(kb, packet)
    messages, _ = build_prompt(kb, packet)
    user = messages[1]["content"]
    assert packet.competitor.name in user
    assert "NEVER describe" in user


def test_retry_hints_appear_in_prompt(kb):
    packet = _packet(kb, "pain_led_story", random.Random(3)).with_retry_hints(["contains a hashtag"])
    messages, _ = build_prompt(kb, packet)
    assert "contains a hashtag" in messages[1]["content"]
