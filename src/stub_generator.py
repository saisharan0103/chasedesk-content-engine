"""Offline placeholder generator.

Used only when OPENAI_API_KEY is not set, so `python -m src.orchestrator` runs
end to end with no keys. It produces plausible-but-placeholder candidates so the
rest of the pipeline (quality filter, scheduling, logging) can be exercised.
Never used when an API key is present, and it forces dry-run.
"""

from __future__ import annotations

from .story_seed_builder import GenerationPacket


def stub_candidates(packet: GenerationPacket) -> list[dict]:
    strat = packet.strategy
    seed = packet.seed
    drafts: list[str] = []

    if seed is not None:
        drafts.append(
            f"{seed.scene}\n\nThat loop is the boring part ChaseDesk is built around."
        )
        drafts.append(f"{seed.pain}\n\nMost receipt tools help after the receipt arrives. ChaseDesk helps get it to arrive.")
    drafts.append("Bookkeepers don't lose evenings because accounting is hard. They lose them chasing receipts that never arrived.")
    drafts.append("Your client doesn't want another portal. They want one link. Click. Upload. Done.")

    cands: list[dict] = []
    for text in drafts[: max(1, packet.n_candidates)]:
        if len(text) > packet.char_limit:
            text = text[: packet.char_limit].rstrip()
        cands.append(
            {
                "tweet": text,
                "shape": packet.shape.id,
                "hook_type": strat.hook_types[0] if strat.hook_types else "operational_pain",
                "character_count": len(text),
                "source_ids": [],
                "risk_flags": [],
                "needs_human_review": False,
            }
        )
    return cands
