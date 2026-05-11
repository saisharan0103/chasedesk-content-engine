"""Turn a chosen strategy into a full generation packet.

A packet bundles everything the prompt builder needs for one tweet slot:
strategy + shape + audience segment + story seed + cta mode + optional
competitor context. None of this is a tweet — it's the input to OpenAI.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .content_loader import AudienceSegment, Competitor, KnowledgeBase, Shape, Strategy, StorySeed

_GOAL_BY_CTA = {
    "none": "awareness",
    "reply_question": "replies",
    "soft_waitlist": "waitlist",
}


@dataclass
class GenerationPacket:
    strategy: Strategy
    shape: Shape
    segment: AudienceSegment
    seed: StorySeed | None
    cta_mode: str
    competitor: Competitor | None
    campaign_goal: str
    n_candidates: int
    char_limit: int
    recent_posts: list[str] = field(default_factory=list)
    retry_hints: list[str] = field(default_factory=list)

    def with_retry_hints(self, hints: list[str]) -> "GenerationPacket":
        return GenerationPacket(
            strategy=self.strategy,
            shape=self.shape,
            segment=self.segment,
            seed=self.seed,
            cta_mode=self.cta_mode,
            competitor=self.competitor,
            campaign_goal=self.campaign_goal,
            n_candidates=self.n_candidates,
            char_limit=self.char_limit,
            recent_posts=self.recent_posts,
            retry_hints=list(hints),
        )


def pick_story_seed(
    kb: KnowledgeBase,
    strategy: Strategy,
    *,
    rng: random.Random,
    exclude_seed_ids: set[str] | None = None,
) -> StorySeed | None:
    exclude = exclude_seed_ids or set()
    compatible = kb.seeds_for_strategy(strategy.id)
    if not compatible:
        return None
    fresh = [s for s in compatible if s.id not in exclude]
    return rng.choice(fresh if fresh else compatible)


def build_packet(
    kb: KnowledgeBase,
    strategy: Strategy,
    *,
    rng: random.Random,
    n_candidates: int,
    char_limit: int,
    recent_posts: list[str] | None = None,
    exclude_seed_ids: set[str] | None = None,
    competitor_chance: float = 0.5,
) -> GenerationPacket:
    seed = pick_story_seed(kb, strategy, rng=rng, exclude_seed_ids=exclude_seed_ids)
    segment = kb.segment(rng.choice(strategy.compatible_segments))
    shape = kb.shape(rng.choice(strategy.allowed_shapes))
    cta_mode = strategy.cta_default

    competitor: Competitor | None = None
    if strategy.id == "category_contrast" and kb.competitor_research.competitors:
        if rng.random() < competitor_chance:
            competitor = rng.choice(kb.competitor_research.competitors)

    return GenerationPacket(
        strategy=strategy,
        shape=shape,
        segment=segment,
        seed=seed,
        cta_mode=cta_mode,
        competitor=competitor,
        campaign_goal=_GOAL_BY_CTA.get(cta_mode, "awareness"),
        n_candidates=n_candidates,
        char_limit=char_limit,
        recent_posts=list(recent_posts or []),
    )
