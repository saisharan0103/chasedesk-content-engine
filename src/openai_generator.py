"""Call OpenAI (real time) to generate tweet candidates with Structured Outputs."""

from __future__ import annotations

import json

from .config import Config


class GeneratorError(RuntimeError):
    pass


def generate_candidates(
    config: Config,
    messages: list[dict],
    schema: dict,
    *,
    temperature: float = 0.9,
) -> list[dict]:
    if not config.openai_api_key:
        raise GeneratorError("OPENAI_API_KEY is not set")

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise GeneratorError("the `openai` package is not installed") from exc

    client = OpenAI(api_key=config.openai_api_key)
    try:
        resp = client.chat.completions.create(
            model=config.openai_model,
            messages=messages,
            temperature=temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "tweet_candidates", "schema": schema, "strict": True},
            },
        )
    except Exception as exc:  # network / API errors
        raise GeneratorError(f"OpenAI request failed: {exc}") from exc

    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise GeneratorError("OpenAI returned an empty response")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise GeneratorError(f"OpenAI returned invalid JSON: {exc}") from exc

    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise GeneratorError("OpenAI response had no candidates")
    return candidates
