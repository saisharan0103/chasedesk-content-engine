import random

from src.strategy_selector import effective_weights, select_strategies


def test_select_returns_n_distinct(kb):
    chosen = select_strategies(kb, 3, rng=random.Random(0))
    assert len(chosen) == 3
    assert len({s.id for s in chosen}) == 3


def test_select_caps_at_pool_size(kb):
    chosen = select_strategies(kb, 999, rng=random.Random(0))
    assert len(chosen) == len(kb.strategies)


def test_select_is_deterministic_with_seed(kb):
    a = [s.id for s in select_strategies(kb, 3, rng=random.Random(42))]
    b = [s.id for s in select_strategies(kb, 3, rng=random.Random(42))]
    assert a == b


def test_min_weight_floor_applied(kb):
    weights = effective_weights(kb, overrides={s.id: 0.0 for s in kb.strategies})
    for s in kb.strategies:
        assert weights[s.id] >= s.min_weight > 0
