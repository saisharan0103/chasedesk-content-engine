import dataclasses

from src.config import Config
from src.quality_filter import check_candidate, looks_generic, text_similarity


def _cfg(**over):
    return dataclasses.replace(Config(), **over)


def _cand(text, **extra):
    base = {
        "tweet": text,
        "shape": "two_part",
        "hook_type": "operational_pain",
        "character_count": len(text),
        "source_ids": [],
        "risk_flags": [],
        "needs_human_review": False,
    }
    base.update(extra)
    return base


def test_clean_tweet_passes(kb):
    strat = kb.strategy("pain_led_story")
    text = "Bookkeepers don't lose Sunday nights because accounting is hard.\n\nThey lose them chasing receipts that never arrived."
    res = check_candidate(_cand(text), kb=kb, config=_cfg(char_limit=240), strategy=strat, recent_posts=[])
    assert res.passed, res.reasons
    assert res.needs_human_review is False


def test_over_char_limit_fails(kb):
    strat = kb.strategy("pain_led_story")
    text = "x" * 300
    res = check_candidate(_cand(text), kb=kb, config=_cfg(char_limit=240), strategy=strat, recent_posts=[])
    assert not res.passed
    assert any("char limit" in r for r in res.reasons)


def test_hashtag_fails(kb):
    strat = kb.strategy("pain_led_story")
    res = check_candidate(_cand("Stop chasing receipts #bookkeeping"), kb=kb, config=_cfg(), strategy=strat, recent_posts=[])
    assert not res.passed
    assert any("hashtag" in r for r in res.reasons)


def test_banned_phrase_fails(kb):
    strat = kb.strategy("pain_led_story")
    res = check_candidate(_cand("ChaseDesk is a real game-changer for bookkeeping receipts"), kb=kb, config=_cfg(), strategy=strat, recent_posts=[])
    assert not res.passed
    assert any("banned phrase" in r for r in res.reasons)


def test_fake_metric_fails_when_no_approved_proof(kb):
    strat = kb.strategy("pain_led_story")
    res = check_candidate(_cand("ChaseDesk saves bookkeepers 90% of their time"), kb=kb, config=_cfg(), strategy=strat, recent_posts=[])
    assert not res.passed
    assert any("metric" in r for r in res.reasons)


def test_competitor_attack_fails(kb):
    strat = kb.strategy("category_contrast")
    res = check_candidate(_cand("Dext is outdated compared to chasing receipts properly"), kb=kb, config=_cfg(), strategy=strat, recent_posts=[])
    assert not res.passed
    assert any("attack word" in r for r in res.reasons)


def test_competitor_mention_routes_to_review(kb):
    strat = kb.strategy("category_contrast")
    text = "Dext helps after the receipt arrives. The painful part is getting the client to send it."
    res = check_candidate(_cand(text), kb=kb, config=_cfg(human_review_competitor_posts=True), strategy=strat, recent_posts=[])
    assert res.passed, res.reasons
    assert res.needs_human_review is True
    assert "competitor_mentioned" in res.risk_flags


def test_similarity_catches_near_duplicate(kb):
    strat = kb.strategy("pain_led_story")
    prev = "Bookkeepers lose evenings chasing receipts that clients never sent."
    near = "Bookkeepers lose evenings chasing receipts clients never sent in."
    assert text_similarity(prev, near) >= 0.6
    res = check_candidate(_cand(near), kb=kb, config=_cfg(similarity_threshold=0.6), strategy=strat, recent_posts=[prev])
    assert not res.passed
    assert any("similar" in r for r in res.reasons)


def test_looks_generic_heuristic():
    assert looks_generic("Leverage cutting-edge synergy to empower your seamless workflow")
    assert not looks_generic("Chasing missing receipts in Xero before month-end close")
