"""Pick which content strategies to generate for a given run.

Weighted-random, distinct within a day (so we never post three pain-led tweets
in one day). Weights come from `content_strategies.yml`, optionally overridden
by a re-tuned weights map (see `src/review.py retune`).
"""

from __future__ import annotations

import random

from .content_loader import KnowledgeBase, Strategy


def effective_weights(kb: KnowledgeBase, overrides: dict[str, float] | None = None) -> dict[str, float]:
    overrides = overrides or {}
    out: dict[str, float] = {}
    for s in kb.strategies:
        w = overrides.get(s.id, s.weight)
        out[s.id] = max(s.min_weight, float(w))
    return out


def select_strategies(
    kb: KnowledgeBase,
    n: int,
    *,
    rng: random.Random | None = None,
    weight_overrides: dict[str, float] | None = None,
) -> list[Strategy]:
    rng = rng or random.Random()
    pool = effective_weights(kb, weight_overrides)
    n = max(0, min(n, len(pool)))
    chosen: list[Strategy] = []
    for _ in range(n):
        ids = list(pool.keys())
        weights = [pool[i] for i in ids]
        pick = rng.choices(ids, weights=weights, k=1)[0]
        chosen.append(kb.strategy(pick))
        del pool[pick]  # distinct within the run
    return chosen
