"""Loads and validates the static knowledge base (`content/*.yml`).

This is the only "static" part of the engine — brand truth, competitor notes,
the list of strategies/shapes, story seeds, tone rules, examples and banned
phrases. It contains *ingredients*, never finished tweets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict


# --------------------------------------------------------------------------- #
# pydantic models — one per YAML file
# --------------------------------------------------------------------------- #
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProductFact(_Strict):
    id: str
    fact: str


class Brand(_Strict):
    name: str
    website: str
    tagline: str
    positioning: str
    one_liner: str
    wedge: str
    product_role: str
    proof_level: str
    proof_rules: str
    approved_proof: list[str] = []


class AudienceSegment(_Strict):
    id: str
    label: str
    description: str
    pains: list[str]
    desired_outcomes: list[str]


class BrandContext(_Strict):
    brand: Brand
    product_facts: list[ProductFact]
    audience_segments: list[AudienceSegment]


class Competitor(_Strict):
    id: str
    name: str
    category: str
    positioning_summary: str
    chase_desk_contrast: str
    safe_contrast_angles: list[str]
    forbidden_attacks: list[str]


class CompetitorResearch(_Strict):
    competitors: list[Competitor]
    category_map: str


class Shape(_Strict):
    id: str
    description: str


class ExampleIds(_Strict):
    good: list[str] = []
    bad: list[str] = []


class Strategy(_Strict):
    id: str
    display_name: str
    purpose: str
    weight: float
    min_weight: float = 0.0
    allowed_shapes: list[str]
    cta_default: str
    allowed_cta_modes: list[str]
    hook_types: list[str]
    compatible_segments: list[str]
    human_review: bool = False
    prompt_notes: str
    example_ids: ExampleIds = ExampleIds()


class ContentStrategies(_Strict):
    shapes: list[Shape]
    strategies: list[Strategy]


class StorySeed(_Strict):
    id: str
    scene: str
    pain: str
    compatible_strategies: list[str]


class StorySeeds(_Strict):
    seeds: list[StorySeed]


class ToneRules(_Strict):
    voice: list[str]
    avoid: list[str]
    formatting: dict[str, Any]
    constraints: dict[str, Any]
    desired_reader_reaction: str
    undesired_reader_reaction: str


class Example(_Strict):
    id: str
    text: str
    strategy: str | None = None
    shape: str | None = None
    note: str | None = None
    rejection_reason: str | None = None


class _ExamplesFile(_Strict):
    examples: list[Example]


class BannedPhrases(_Strict):
    banned_phrases: list[str]
    competitor_attack_words: list[str]
    fake_metric_patterns: list[str]


# --------------------------------------------------------------------------- #
# knowledge base wrapper
# --------------------------------------------------------------------------- #
class KnowledgeBaseError(RuntimeError):
    pass


class KnowledgeBase:
    """Validated knowledge base with convenient lookups."""

    def __init__(
        self,
        *,
        brand_context: BrandContext,
        competitor_research: CompetitorResearch,
        content_strategies: ContentStrategies,
        story_seeds: StorySeeds,
        tone_rules: ToneRules,
        good_examples: list[Example],
        bad_examples: list[Example],
        banned: BannedPhrases,
    ) -> None:
        self.brand_context = brand_context
        self.competitor_research = competitor_research
        self.content_strategies = content_strategies
        self.story_seeds = story_seeds
        self.tone_rules = tone_rules
        self.good_examples = good_examples
        self.bad_examples = bad_examples
        self.banned = banned
        self.warnings: list[str] = []

        self._strategies = {s.id: s for s in content_strategies.strategies}
        self._shapes = {s.id: s for s in content_strategies.shapes}
        self._segments = {a.id: a for a in brand_context.audience_segments}
        self._seeds = {s.id: s for s in story_seeds.seeds}
        self._competitors = {c.id: c for c in competitor_research.competitors}
        self._examples = {e.id: e for e in (*good_examples, *bad_examples)}

        self._validate_references()
        self._normalize_weights()

    # -- lookups -----------------------------------------------------------
    def strategy(self, sid: str) -> Strategy:
        return self._strategies[sid]

    def shape(self, shid: str) -> Shape:
        return self._shapes[shid]

    def segment(self, aid: str) -> AudienceSegment:
        return self._segments[aid]

    def seed(self, sid: str) -> StorySeed:
        return self._seeds[sid]

    def competitor(self, cid: str) -> Competitor:
        return self._competitors[cid]

    def example(self, eid: str) -> Example | None:
        return self._examples.get(eid)

    @property
    def strategies(self) -> list[Strategy]:
        return list(self.content_strategies.strategies)

    @property
    def competitor_names(self) -> list[str]:
        return [c.name for c in self.competitor_research.competitors]

    def seeds_for_strategy(self, sid: str) -> list[StorySeed]:
        return [s for s in self.story_seeds.seeds if sid in s.compatible_strategies]

    # -- internal ----------------------------------------------------------
    def _validate_references(self) -> None:
        shape_ids = set(self._shapes)
        seg_ids = set(self._segments)
        strat_ids = set(self._strategies)
        ex_ids = set(self._examples)
        problems: list[str] = []

        for s in self.content_strategies.strategies:
            for sh in s.allowed_shapes:
                if sh not in shape_ids:
                    problems.append(f"strategy '{s.id}' references unknown shape '{sh}'")
            for seg in s.compatible_segments:
                if seg not in seg_ids:
                    problems.append(f"strategy '{s.id}' references unknown segment '{seg}'")
            if s.cta_default not in s.allowed_cta_modes:
                problems.append(f"strategy '{s.id}' cta_default '{s.cta_default}' not in allowed_cta_modes")
            for eid in (*s.example_ids.good, *s.example_ids.bad):
                if eid not in ex_ids:
                    problems.append(f"strategy '{s.id}' references unknown example '{eid}'")

        for seed in self.story_seeds.seeds:
            for sid in seed.compatible_strategies:
                if sid not in strat_ids:
                    problems.append(f"seed '{seed.id}' references unknown strategy '{sid}'")
            if not seed.compatible_strategies:
                problems.append(f"seed '{seed.id}' has no compatible strategies")

        for s in self.content_strategies.strategies:
            if not self.seeds_for_strategy(s.id):
                self.warnings.append(f"strategy '{s.id}' has no compatible story seeds")

        if problems:
            raise KnowledgeBaseError("knowledge base validation failed:\n  - " + "\n  - ".join(problems))

    def _normalize_weights(self) -> None:
        total = sum(s.weight for s in self.content_strategies.strategies)
        if total <= 0:
            raise KnowledgeBaseError("strategy weights sum to zero")
        if abs(total - 1.0) > 1e-6:
            self.warnings.append(f"strategy weights summed to {total:.4f}; normalized to 1.0")
            for s in self.content_strategies.strategies:
                s.weight = s.weight / total


# --------------------------------------------------------------------------- #
# loader
# --------------------------------------------------------------------------- #
def _read_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"missing content file: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_knowledge_base(content_dir: Path | str) -> KnowledgeBase:
    content_dir = Path(content_dir)
    return KnowledgeBase(
        brand_context=BrandContext.model_validate(_read_yaml(content_dir / "brand_context.yml")),
        competitor_research=CompetitorResearch.model_validate(_read_yaml(content_dir / "competitor_research.yml")),
        content_strategies=ContentStrategies.model_validate(_read_yaml(content_dir / "content_strategies.yml")),
        story_seeds=StorySeeds.model_validate(_read_yaml(content_dir / "story_seeds.yml")),
        tone_rules=ToneRules.model_validate(_read_yaml(content_dir / "tone_rules.yml")),
        good_examples=_ExamplesFile.model_validate(_read_yaml(content_dir / "good_examples.yml")).examples,
        bad_examples=_ExamplesFile.model_validate(_read_yaml(content_dir / "bad_examples.yml")).examples,
        banned=BannedPhrases.model_validate(_read_yaml(content_dir / "banned_phrases.yml")),
    )
