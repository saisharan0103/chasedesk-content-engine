"""Deterministic quality checks for generated tweet candidates.

A candidate must pass ALL checks to be eligible. Passing candidates may still be
routed to human review (competitor mention, numbers, customer story, or a
strategy that always requires review).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import Config
from .content_loader import KnowledgeBase
from .content_loader import Strategy

_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # symbols & pictographs, supplemental, etc.
    "\U00002600-\U000027BF"  # misc symbols + dingbats
    "\U0001F1E6-\U0001F1FF"  # regional indicators
    "\U00002B00-\U00002BFF"
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U00002190-\U000021FF"  # arrows
    "]",
    flags=re.UNICODE,
)

_GENERIC_MARKERS = (
    "streamline",
    "optimize your",
    "optimise your",
    "boost your",
    "elevate your",
    "in today's",
    "leverage",
    "synergy",
    "robust solution",
    "cutting-edge",
    "empower",
    "seamless",
    "effortless",
    "take your business to the next level",
)
_SPECIFIC_MARKERS = (
    "receipt",
    "xero",
    "bookkeep",
    "month-end",
    "month end",
    "close the books",
    "close",
    "client",
    "upload",
    "invoice",
    "reconcile",
    "uncategorized",
    "uncategorised",
)

_WORD_RE = re.compile(r"[a-z0-9']+")


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def text_similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def max_similarity(text: str, others: list[str]) -> tuple[float, str | None]:
    best, worst = 0.0, None
    for other in others:
        sim = text_similarity(text, other)
        if sim > best:
            best, worst = sim, other
    return best, worst


def emoji_count(text: str) -> int:
    return len(_EMOJI_RE.findall(text))


def looks_generic(text: str) -> bool:
    low = text.lower()
    generic_hits = sum(1 for m in _GENERIC_MARKERS if m in low)
    specific_hits = sum(1 for m in _SPECIFIC_MARKERS if m in low)
    return generic_hits >= 2 and specific_hits == 0


@dataclass
class FilterResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    needs_human_review: bool = False


def check_candidate(
    candidate: dict,
    *,
    kb: KnowledgeBase,
    config: Config,
    strategy: Strategy,
    recent_posts: list[str],
) -> FilterResult:
    text = (candidate.get("tweet") or "").strip()
    reasons: list[str] = []
    flags: list[str] = list(candidate.get("risk_flags") or [])
    low = text.lower()

    if not text:
        return FilterResult(passed=False, reasons=["empty tweet"], risk_flags=flags)

    # length
    if len(text) > config.char_limit:
        reasons.append(f"over char limit ({len(text)} > {config.char_limit})")

    # hashtags
    if "#" in text:
        reasons.append("contains a hashtag")

    # emojis
    max_emojis = int(kb.tone_rules.formatting.get("max_emojis", 0))
    if emoji_count(text) > max_emojis:
        reasons.append("contains an emoji")

    # banned phrases
    for phrase in kb.banned.banned_phrases:
        if phrase.lower() in low:
            reasons.append(f"banned phrase: '{phrase}'")

    # fabricated metric (only when no approved proof exists)
    if not kb.brand_context.brand.approved_proof:
        for pattern in kb.banned.fake_metric_patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    reasons.append(f"possible fabricated metric (matched /{pattern}/)")
                    break
            except re.error:
                continue

    # competitor mention + attack words
    mentioned = [name for name in kb.competitor_names if name.lower() in low]
    if mentioned:
        flags.append("competitor_mentioned")
        for word in kb.banned.competitor_attack_words:
            if re.search(rf"\b{re.escape(word.lower())}\b", low):
                reasons.append(f"competitor attack word: '{word}'")

    # similarity to recent posts
    if recent_posts:
        sim, _ = max_similarity(text, recent_posts)
        if sim >= config.similarity_threshold:
            reasons.append(f"too similar to a recent post (similarity {sim:.2f})")

    # unknown source ids
    known_fact_ids = {f.id for f in kb.brand_context.product_facts}
    for sid in candidate.get("source_ids") or []:
        if sid not in known_fact_ids:
            reasons.append(f"unknown source_id: '{sid}'")

    # generic / low-specificity heuristic (lenient — just triggers regeneration)
    if looks_generic(text):
        reasons.append("sounds generic / low specificity")

    passed = not reasons

    needs_review = (
        bool(candidate.get("needs_human_review"))
        or strategy.human_review
        or ("competitor_mentioned" in flags and config.human_review_competitor_posts)
    )
    return FilterResult(passed=passed, reasons=reasons, risk_flags=flags, needs_human_review=needs_review)
