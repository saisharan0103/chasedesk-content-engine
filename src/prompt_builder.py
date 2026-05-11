"""Assemble the OpenAI prompt (system + user messages) and the JSON output schema
from a generation packet plus the knowledge base.
"""

from __future__ import annotations

from .content_loader import Example, KnowledgeBase
from .story_seed_builder import GenerationPacket

SYSTEM_PROMPT = (
    "You are ChaseDesk's social copywriter for X (Twitter). You write founder-led, "
    "specific, operational posts for people who run Xero bookkeeping firms. You never "
    "invent facts, customer stories, metrics, features, or competitor claims. You return "
    "only valid JSON matching the provided schema."
)

CANDIDATE_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tweet": {"type": "string"},
                    "shape": {"type": "string"},
                    "hook_type": {"type": "string"},
                    "character_count": {"type": "integer"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "risk_flags": {"type": "array", "items": {"type": "string"}},
                    "needs_human_review": {"type": "boolean"},
                },
                "required": [
                    "tweet",
                    "shape",
                    "hook_type",
                    "character_count",
                    "source_ids",
                    "risk_flags",
                    "needs_human_review",
                ],
            },
        }
    },
    "required": ["candidates"],
}

_CTA_INSTRUCTIONS = {
    "none": "Do not include a call to action. ChaseDesk may be mentioned only if it reads naturally.",
    "reply_question": "End with a genuine question that invites replies. No product pitch.",
    "soft_waitlist": (
        "You may end with ONE soft, calm CTA — e.g. 'we're opening access in batches to Xero firms "
        "still doing this by hand'. Never use urgency, scarcity, or hype."
    ),
}


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def _examples_block(kb: KnowledgeBase, ids: list[str], label: str) -> str:
    lines: list[str] = []
    for eid in ids:
        ex: Example | None = kb.example(eid)
        if ex is None:
            continue
        tail = f"  ({ex.note or ex.rejection_reason})" if (ex.note or ex.rejection_reason) else ""
        lines.append(f'{label}:\n"""{ex.text}"""{tail}')
    return "\n\n".join(lines)


def build_prompt(kb: KnowledgeBase, packet: GenerationPacket) -> tuple[list[dict], dict]:
    brand = kb.brand_context.brand
    strat = packet.strategy
    seg = packet.segment
    shape = packet.shape

    product_facts = "\n".join(f"- [{f.id}] {f.fact}" for f in kb.brand_context.product_facts)
    proof_line = (
        "Approved proof you may reference: " + "; ".join(brand.approved_proof)
        if brand.approved_proof
        else "No approved metrics exist — use no numbers, percentages, or results claims."
    )

    if packet.seed is not None:
        seed_block = f"Scene: {packet.seed.scene}\nUnderlying pain: {packet.seed.pain}"
    else:
        seed_block = "No fixed scene — write from the strategy and the audience's pains."

    if packet.competitor is not None:
        c = packet.competitor
        competitor_block = (
            f"You may reference {c.name} ({c.category}). Their positioning: {c.positioning_summary}\n"
            f"Use ONLY these contrast lines as your basis: {c.chase_desk_contrast}; "
            + "; ".join(c.safe_contrast_angles)
            + f"\nNEVER describe {c.name} with any of these words: {', '.join(c.forbidden_attacks)}.\n"
            "Contrast the workflow category, not the competitor's quality."
        )
    elif strat.id == "category_contrast":
        competitor_block = (
            "Do not name a specific competitor. Contrast the CATEGORY:\n"
            f"{kb.competitor_research.category_map}"
        )
    else:
        competitor_block = "Do not mention competitors."

    good_ids = strat.example_ids.good
    bad_ids = strat.example_ids.bad
    retry_block = ""
    if packet.retry_hints:
        retry_block = (
            "\n# Previous attempt(s) were rejected — fix every one of these:\n"
            + _bullets(packet.retry_hints)
            + "\n"
        )

    user = f"""# Objective
Generate {packet.n_candidates} candidate tweets. Campaign goal: {packet.campaign_goal}.
Each candidate must stand alone as a single X post.

# Audience
{seg.label} — {seg.description}
Their pains: {", ".join(seg.pains)}
What they want: {", ".join(seg.desired_outcomes)}

# Brand truth
{brand.one_liner}
Tagline: {brand.tagline}
Positioning: {brand.positioning}
The wedge: {brand.wedge}
Product role: {brand.product_role}

# Product facts (the ONLY product capabilities you may state)
{product_facts}

# Proof level
{brand.proof_rules}
{proof_line}

# Content strategy: {strat.display_name}
{strat.purpose}
{strat.prompt_notes}

# Tweet shape: {shape.id}
{shape.description}

# Story seed
{seed_block}

# Competitor handling
{competitor_block}

# Style
{_bullets(kb.tone_rules.voice)}
Avoid:
{_bullets(kb.tone_rules.avoid)}

# Hard constraints
- Platform: X. Maximum {packet.char_limit} characters per tweet — count characters and do not exceed.
- One idea per tweet. Strong opening line.
- No hashtags. No emojis.
- Never invent: {", ".join(kb.tone_rules.constraints.get("never_invent", []))}.
- {kb.tone_rules.constraints.get("competitor_rule", "")}
- If you state a product capability, it must map to a product fact id above; list those ids in source_ids.
- Do NOT reuse the wording of these recent posts:
{_bullets(packet.recent_posts) if packet.recent_posts else "- (none yet)"}
- Never use any of these banned phrases: {", ".join(kb.banned.banned_phrases)}

# CTA policy
CTA mode: {packet.cta_mode}. {_CTA_INSTRUCTIONS.get(packet.cta_mode, _CTA_INSTRUCTIONS["none"])}
{retry_block}
# Imitate the TONE of these (not the literal content)
{_examples_block(kb, good_ids, "GOOD") or "(no good examples configured)"}

# Never produce anything like these
{_examples_block(kb, bad_ids, "BAD") or "(no bad examples configured)"}

# Output
Return JSON only, matching the schema. `character_count` must equal the exact length of `tweet`.
`shape` should be "{shape.id}". `hook_type` should be one of: {", ".join(strat.hook_types)}.
Set `needs_human_review` true if the tweet names a competitor, includes any number/metric, or references a customer story.
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
    return messages, CANDIDATE_JSON_SCHEMA
