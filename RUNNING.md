# Running the ChaseDesk Content Engine

`Readme.md` is the design spec. This file is the operator's guide — how to run it,
what each piece does, and how the weekly loop works.

## What it does (in one paragraph)

Every run it picks 2–3 **content strategies** (weighted-random, see
`content/content_strategies.yml`), pairs each with an **audience segment**, a
**story seed** (a concrete scene), a **shape**, and a **CTA mode**, builds a prompt
on the fly, calls **OpenAI in real time** for candidate tweets, runs them through a
strict **quality filter**, and **schedules** the survivors in **Typefully** at
randomized times inside a daily window (strict ≥3h gaps). Competitor / risky tweets
go to a **review queue** instead. Everything is logged. Nothing is a pre-written
tweet — the only static thing is the `content/*.yml` knowledge base of ingredients.

## Quick start (local)

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in OPENAI_API_KEY and TYPEFULLY_API_KEY
python -m src.orchestrator
```

Both keys are required. The orchestrator generates tweets, runs them through
the quality filter, and schedules passing ones in Typefully. Look in `logs/`:

- `logs/YYYY-MM-DD.md` — human-readable run log
- `logs/metrics.csv` — one row per slot (metric columns blank, for later backfill)
- `logs/recent_posts.json` — rolling anti-repetition state
- `logs/review_queue/YYYY-MM-DD.json` / `.md` — tweets waiting for human approval

## Tests

```bash
python -m pytest
```

## The knowledge base — `content/*.yml`

| File | What's in it |
|---|---|
| `brand_context.yml` | Brand truth, the wedge, product facts (the only product claims allowed), audience segments |
| `competitor_research.yml` | Competitor notes + safe contrast angles + forbidden attack words + the category map |
| `content_strategies.yml` | **The 10 strategy "templates"** (id, purpose, weight, allowed shapes, CTA policy, prompt notes, human-review flag) + the shape definitions |
| `story_seeds.yml` | ~20 concrete scenes, each tagged with which strategies it fits |
| `tone_rules.yml` | Voice, formatting rules, hard constraints |
| `good_examples.yml` / `bad_examples.yml` | Few-shot steering — imitate the *tone*, never the literal content |
| `banned_phrases.yml` | Banned phrases, competitor-attack words, fabricated-metric regexes |

Edit these by hand whenever positioning, product, or strategy changes. They're the brain.

## The review queue

`HUMAN_REVIEW_COMPETITOR_POSTS=true` (default) means any tweet that names a
competitor — or comes from a strategy flagged `human_review` (`category_contrast`,
`soft_waitlist_cta`) — is parked in `logs/review_queue/<date>.json` instead of being
scheduled. Work it with:

```bash
python -m src.review list
python -m src.review approve 2026-05-12 0           # schedule item #0 to Typefully
python -m src.review reject  2026-05-12 1 "too salesy"
```

## The weekly loop ("double down on what works")

1. After each posting day, the GitHub Action commits `logs/`. Once posts have run,
   backfill the metric columns in `logs/metrics.csv` (impressions, likes, replies,
   reposts, bookmarks, profile_clicks, url_clicks, followers_gained, waitlist_clicks)
   from Typefully / X.
2. Run `python -m src.review retune`. It scores each **strategy** by engagement,
   blends 50/50 with the current weight, clamps to `[min_weight, 0.40]`, renormalizes,
   and prints proposed new `weight:` values.
3. Eyeball them, then edit `content/content_strategies.yml` by hand. Don't auto-apply
   — ~3 weeks at 3/day is ~6 posts per strategy, which is *directional*, not conclusive.
4. Add the best real tweets to `content/good_examples.yml`; add recurring failures to
   `bad_examples.yml` or `banned_phrases.yml`. If the same human-rejection reason shows
   up 3+ times, turn it into an automatic check in `src/quality_filter.py`.

## GitHub Actions

`.github/workflows/post-chasedesk.yml` runs daily at 03:00 UTC (≈ 08:30 IST):
checkout → install → `python -m src.orchestrator` → commit `logs/`.

- The cron is just a **trigger**. The precise (randomized) posting times are handled
  by **Typefully**, which the orchestrator schedules into via the API. So cron delay
  doesn't matter.
- It schedules for **today** if there's runway before the posting window opens,
  otherwise for **tomorrow**.
- Set repo secrets: `OPENAI_API_KEY`, `TYPEFULLY_API_KEY` (Settings → Secrets and
  variables → Actions). Optional repo *variables*: `OPENAI_MODEL`, `TIMEZONE`,
  `POSTS_PER_DAY`, `POST_WINDOW_START`, `POST_WINDOW_END`, `MIN_GAP_MINUTES`,
  `CHAR_LIMIT`, `HUMAN_REVIEW_COMPETITOR_POSTS`.
- To test on demand: Actions tab → "ChaseDesk daily content" → "Run workflow".
- `logs/recent_posts.json` and `logs/metrics.csv` are committed by the workflow on
  purpose — that's how anti-repetition state and metrics history survive between runs.

## Module map (`src/`)

| Module | Role |
|---|---|
| `config.py` | env-backed configuration |
| `content_loader.py` | load + validate `content/*.yml` into a `KnowledgeBase` |
| `strategy_selector.py` | weighted-random pick of N distinct strategies/run |
| `story_seed_builder.py` | build a `GenerationPacket` (strategy + shape + segment + seed + cta + competitor) |
| `prompt_builder.py` | assemble the OpenAI messages + JSON output schema |
| `openai_generator.py` | real-time OpenAI call with Structured Outputs |
| `quality_filter.py` | deterministic checks + human-review routing |
| `scheduler.py` | randomized posting times (strict ≥ gap), UTC conversion, target-day logic |
| `typefully_client.py` | create/schedule a draft via the Typefully API |
| `logging_utils.py` | run log, metrics CSV, recent-posts state, review queue |
| `orchestrator.py` | ties it all together — `python -m src.orchestrator` |
| `review.py` | review-queue CLI + weekly `retune` |
