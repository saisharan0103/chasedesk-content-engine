def test_kb_loads_with_expected_shape(kb):
    assert len(kb.strategies) >= 8
    assert kb.brand_context.brand.name == "ChaseDesk"
    assert kb.competitor_research.competitors
    assert kb.story_seeds.seeds
    assert kb.good_examples and kb.bad_examples


def test_strategy_weights_normalized(kb):
    total = sum(s.weight for s in kb.strategies)
    assert abs(total - 1.0) < 1e-6


def test_every_strategy_has_compatible_seeds(kb):
    for s in kb.strategies:
        assert kb.seeds_for_strategy(s.id), f"{s.id} has no compatible seeds"


def test_strategy_references_resolve(kb):
    shape_ids = {sh.id for sh in kb.content_strategies.shapes}
    segment_ids = {a.id for a in kb.brand_context.audience_segments}
    example_ids = {e.id for e in (*kb.good_examples, *kb.bad_examples)}
    for s in kb.strategies:
        assert set(s.allowed_shapes) <= shape_ids
        assert set(s.compatible_segments) <= segment_ids
        assert s.cta_default in s.allowed_cta_modes
        assert set(s.example_ids.good) <= example_ids
        assert set(s.example_ids.bad) <= example_ids


def test_seed_strategy_references_resolve(kb):
    strat_ids = {s.id for s in kb.strategies}
    for seed in kb.story_seeds.seeds:
        assert set(seed.compatible_strategies) <= strat_ids
