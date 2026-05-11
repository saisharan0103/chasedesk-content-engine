# ChaseDesk Content Engine

A research-backed AI content generation and scheduling system for ChaseDesk.

This project is designed to generate high-quality Twitter/X content for ChaseDesk using OpenAI, structured competitor research, ChaseDesk positioning, storytelling frameworks, content themes, quality filters, and Typefully scheduling.

The goal is **not** to hardcode tweets.

The goal is to build a system that can consistently generate fresh, useful, founder-led, buyer-relevant content using a static knowledge base and carefully designed prompts.

---

## 1. What is ChaseDesk?

**ChaseDesk** is a SaaS product for Xero bookkeeping firms.

Core positioning:

> **We chase. You close.**

ChaseDesk helps bookkeeping firms automatically chase clients for missing receipts and documents.

It connects to Xero, detects missing receipts, follows up with clients by email/SMS, gives clients a no-login upload link, OCRs/extracts the documents, and helps post clean entries back to Xero.

In simple terms:

> Bookkeepers waste hours every month asking clients for missing receipts.  
> ChaseDesk automates that annoying follow-up loop.

---

## 2. Why this project exists

ChaseDesk needs distribution.

The product is narrow and specific, so the content also needs to be narrow and specific.

Generic AI content like:

> “AI will transform accounting.”

is useless for us.

The target audience is:

- Xero bookkeeping firm owners
- Solo bookkeepers
- Small accounting teams
- Practice operations people
- Accounting firms that serve SMB clients
- Firms tired of manually chasing missing receipts before month-end close

This system exists to help ChaseDesk publish consistent, sharp, founder-led content around the exact pain it solves:

> Missing receipt chasing.

---

## 3. Current strategy

The content strategy is based on four major conclusions.

### 3.1 Do not research every day

Daily web research is not required because the market is narrow and the core competitor landscape does not change every day.

Instead, the system should use a **static knowledge base** containing:

- ChaseDesk positioning
- ICP details
- competitor research
- product facts
- buyer pain points
- content themes
- storytelling frameworks
- good/bad examples
- banned phrases
- tone rules

This knowledge base can be manually refreshed every 2–4 weeks, or whenever a major competitor/product/platform change happens.

### 3.2 Do not hardcode tweets

The system should not store 100 ready-made tweets and publish them.

Hardcoded tweets become stale and repetitive.

Instead, the system should store **structured context** and generate fresh tweets through OpenAI.

Good input:

```text
ICP + situation + pain + story angle + product role + tone rules
```

Bad input:

```text
Write 3 tweets for ChaseDesk.
```

### 3.3 Build multiple content strategies

Instead of one generic generator, the system should support multiple content-generation strategies/themes.

Examples:

- Pain-led storytelling
- Before/after workflow
- Hidden cost of manual chasing
- Competitor/category contrast
- No-login upload link
- Founder observation
- Customer discovery questions
- Soft waitlist CTA

The system will run these themes for 2–3 weeks, track performance, then double down on the themes that work.

### 3.4 Storytelling matters

The best ChaseDesk tweets should not just describe features.

They should tell mini-stories about real workflow pain.

Example story direction:

```text
A bookkeeper opens Xero on Monday.
There are 34 uncategorized transactions.
The accounting is not hard.
The receipts are missing.
Now the team has to chase clients manually.
```

That kind of situation gives OpenAI a scene to write from.

The system should generate posts that feel like:

> “This founder understands my workflow.”

not:

> “This SaaS account is posting AI-generated marketing.”

---

## 4. What we researched

We researched direct and adjacent competitors in the bookkeeping, accounting automation, receipt capture, document collection, and client portal space.

### 4.1 Direct competitors

These competitors focus on receipt/document capture, OCR, bookkeeping automation, or accounting workflows:

- Dext
- Hubdoc
- AutoEntry
- Datamolino
- Apron
- EzzyBills

### 4.2 Adjacent competitors

These competitors solve related problems around client tasks, document collection, portals, workflow, and practice management:

- Client Hub
- Financial Cents
- TaxDome
- Karbon

### 4.3 Competitor positioning summary

| Competitor | Main positioning | ChaseDesk insight |
|---|---|---|
| Dext | Receipt capture and bookkeeping automation | Dext helps after receipts arrive. ChaseDesk helps get the receipt to arrive. |
| Hubdoc | Source document storage and extraction | Hubdoc manages documents. ChaseDesk chases missing ones before close. |
| AutoEntry | Automated data entry for invoices/receipts | Automation is useful after documents are available; ChaseDesk handles the earlier bottleneck. |
| Datamolino | Invoice/bill/receipt OCR and Xero sync | “Never type an invoice again” is strong; ChaseDesk version is “never chase a receipt again.” |
| Apron | Payments, approvals, receipts, accountant workflow | Modern brand and community-led distribution are worth studying. |
| EzzyBills | Bill/receipt capture and Xero marketplace distribution | Xero marketplace is an important channel later. |
| Client Hub | Client portal and client responsiveness | Broad client communication; ChaseDesk should be narrower and sharper. |
| Financial Cents | Stop chasing clients for docs | Very close pain messaging; ChaseDesk should specialize in Xero missing receipts. |
| TaxDome | Client portal, documents, tasks, reminders | ChaseDesk should contrast against heavy portals with no-login upload links. |
| Karbon | Practice management, workflow, AI reports | Strong thought leadership and premium B2B SaaS positioning. |

---

## 5. Core market insight

Most tools talk about:

```text
Capture receipts.
Extract data.
Automate bookkeeping.
Manage documents.
Improve workflows.
```

ChaseDesk should talk about:

```text
The receipt never arrived.
The client ignored the request.
The bookkeeper is stuck chasing.
Month-end close is delayed.
```

The wedge:

> **Most tools help after the receipt arrives. ChaseDesk helps get the receipt to arrive.**

This should be one of the strongest ideas in the system.

---

## 6. System overview

High-level flow:

```text
Static Knowledge Base
        ↓
Content Strategy Selector
        ↓
Story Seed Builder
        ↓
OpenAI Tweet Generator
        ↓
Quality Filter
        ↓
Typefully Scheduler
        ↓
Daily Log
        ↓
Performance Review
        ↓
Theme Weight Updates
```

The system should generate and schedule tweets without needing daily research.

---

## 7. Main components

### 7.1 Static Knowledge Base

The knowledge base stores all stable context.

Recommended files:

```text
content/
  brand_context.yml
  competitor_research.yml
  content_strategies.yml
  story_seeds.yml
  tone_rules.yml
  good_examples.yml
  bad_examples.yml
  banned_phrases.yml
```

This is the brain of the system.

It should be updated manually when strategy changes.

---

### 7.2 Brand context

This tells OpenAI what ChaseDesk is.

Must include:

```yaml
brand:
  name: "ChaseDesk"
  tagline: "We chase. You close."
  positioning: "Receipt-chasing autopilot for Xero bookkeeping firms"
  audience:
    - "Xero bookkeepers"
    - "small bookkeeping firms"
    - "accounting practice owners"
  promise: "Automatically detect missing receipts, follow up with clients, collect documents, extract data, and help post clean entries to Xero."
```

The brand context should be included in every OpenAI request.

---

### 7.3 Competitor research

Competitor research should not be used to copy competitors.

It should be used to understand:

- what they talk about
- what they do well
- what content formats they use
- what buyer pain they educate around
- where ChaseDesk is different

Recommended structure:

```yaml
competitors:
  - id: "dext"
    name: "Dext"
    category: "receipt capture / bookkeeping automation"
    market_message: "Automate receipt and invoice processing"
    marketing_methods:
      - "SEO pages"
      - "webinars"
      - "case studies"
      - "accountant resources"
    chase_desk_counter_position: "Dext helps after receipts arrive. ChaseDesk helps get receipts to arrive."
    safe_contrast_angles:
      - "Most receipt tools start too late."
      - "OCR is not the bottleneck; client responsiveness is."
    forbidden_attacks:
      - "outdated"
      - "useless"
      - "inferior"
```

Important rule:

> Mention competitors only occasionally.  
> Do not make the account look obsessed with competitors.

Recommended ratio:

```text
70% pain-led content
20% category/competitor contrast
10% CTA/product/waitlist
```

---

### 7.4 Content strategy selector

Every day, the system should select 2–3 content strategies.

Example strategies:

```text
pain_led_storytelling
before_after_workflow
hidden_cost
category_contrast
no_login_upload_link
founder_observation
customer_discovery_question
soft_waitlist_cta
```

The selected strategy controls what OpenAI generates.

---

### 7.5 Story seed builder

This is the key part.

Instead of giving OpenAI a topic, give it a story seed.

Bad:

```text
Write a tweet about missing receipts.
```

Good:

```text
A small bookkeeping firm is closing books for 40 clients.
The accounting work is mostly done.
But missing receipts are blocking final review.
The team spends Monday sending reminder emails and checking replies.
```

OpenAI should receive scenes and situations, not vague topics.

---

### 7.6 OpenAI generator

OpenAI receives:

```text
Brand truth
+ ICP profile
+ selected content strategy
+ story seed
+ product role
+ competitor insight if relevant
+ tone rules
+ banned phrases
+ output schema
```

The model generates candidate tweets.

It should return structured JSON, not free-form text.

Example response shape:

```json
{
  "candidates": [
    {
      "tweet": "Month-end doesn't always get delayed by accounting.\n\nSometimes it's 27 missing receipts sitting between your team and a clean close.",
      "strategy": "pain_led_storytelling",
      "hook_type": "operational_pain",
      "character_count": 148,
      "risk_flags": [],
      "needs_human_review": false
    }
  ]
}
```

---

### 7.7 Quality filter

The quality filter blocks bad tweets.

Reject if:

- above character limit
- contains hashtags
- uses fake metrics
- sounds generic
- contains unsupported claims
- attacks competitors directly
- uses too many emojis
- uses banned phrases
- sounds like corporate SaaS fluff
- repeats recent posts too closely

Banned phrases should include:

```text
game-changer
revolutionize accounting
10x your bookkeeping overnight
AI-powered transformation
future of accounting
set it and forget it forever
```

The filter should be strict.

If a tweet fails, regenerate up to 2–3 times.

If it still fails, log it and skip or send to manual review.

---

### 7.8 Typefully scheduler

After tweets pass the quality filter, they should be sent to Typefully.

Recommended posting schedule:

```text
10:00 AM IST
3:00 PM IST
8:00 PM IST
```

Start with:

```text
3 tweets/day
21 tweets/week
63 tweets over 3 weeks
```

Do not overpost in the beginning.

---

### 7.9 Daily logs

Every run should produce a log.

The log should include:

```text
Date
Selected strategies
Story seed
Competitor insight used, if any
Generated tweet
Quality result
Scheduled time
Typefully status
```

Logs are important because they help us understand what the system did.

---

## 8. What exactly should be sent to OpenAI?

This is the most important design decision.

The system should send a **generation packet**.

### 8.1 Generation packet structure

```json
{
  "campaign_goal": "awareness",
  "audience_segment": "firm_owner_2_20_staff",
  "content_strategy": "pain_led_storytelling",
  "story_angle": "before_after",
  "brand_context": {},
  "product_facts": [],
  "competitor_context": {},
  "story_seed": {},
  "tone_rules": {},
  "banned_phrases": [],
  "recent_posts": [],
  "output_requirements": {}
}
```

This packet becomes the input to OpenAI.

---

### 8.2 Brand truth

Always send:

```text
ChaseDesk helps Xero bookkeeping firms automatically chase clients for missing receipts.

It detects missing receipts, sends follow-ups, gives clients a no-login upload link, OCRs documents, and helps post clean entries back to Xero.

Core line: We chase. You close.
```

---

### 8.3 ICP profile

Example:

```text
ICP: Small Xero bookkeeping firm owner.

They manage 20–80 SMB clients.
They lose time every month chasing clients for missing receipts.
They care about faster month-end close, less admin, and more capacity without hiring.
```

---

### 8.4 Story situation

Example:

```text
A bookkeeper opens Xero on Monday morning.
There are dozens of uncategorized transactions.
Most are not hard accounting problems.
They are missing receipt problems.
The team now has to email clients one by one.
```

This gives OpenAI the emotional and operational context.

---

### 8.5 Product role

Important:

ChaseDesk should not be framed as the hero.

The bookkeeper is the hero.

ChaseDesk is the quiet assistant.

Input rule:

```text
Do not make ChaseDesk sound magical.
Show it as the quiet assistant that handles the chase so the bookkeeper can close books faster.
```

---

### 8.6 Proof level

Because ChaseDesk is early, do not invent metrics.

Input:

```text
No real customer data available yet.
Do not invent numbers.
Use qualitative stories only.
If mentioning time saved, say "less time" or "hours back", not exact claims.
```

Later, when real beta data exists, add approved proof:

```text
Approved proof:
Beta firm saved 9 hours/month chasing receipts.
Use this number only when relevant.
```

---

## 9. Prompt structure

Recommended prompt:

```text
# Identity
You are ChaseDesk's social copywriter for X.

# Objective
Generate {n_candidates} candidate tweets for {campaign_goal}.

# Audience
{audience_segment}

# Brand truth
ChaseDesk is a receipt-chasing autopilot for Xero bookkeeping firms.
It detects missing receipts, follows up with clients, gives clients a no-login upload link, extracts documents, and helps post clean entries back to Xero.
Tagline: We chase. You close.

# Content strategy
{content_strategy}

# Story seed
{situation}
{pain}
{workflow_context}

# Product role
Show ChaseDesk as a quiet assistant, not a magical replacement for bookkeepers.

# Competitor context
{competitor_context_if_relevant}

# Style
- Plain English
- Founder-led
- Specific
- Operational
- Slightly witty if natural
- No hashtags
- No emojis unless requested
- No fake metrics
- No generic AI hype
- No overpromising
- No aggressive competitor attacks

# Constraints
- Platform: X
- Max characters: 240
- One idea per tweet
- Avoid repeating recent posts
- Never invent customer stories, numbers, features, or competitor claims

# Output
Return valid JSON only.
```

---

## 10. Content generation strategies

The system should support multiple strategies.

Each strategy has a purpose and a different prompt style.

---

### 10.1 Pain-led storytelling

Purpose:

Make bookkeepers feel understood.

Input style:

```text
Theme: Pain-led storytelling
ICP: Xero bookkeeping firm owner
Situation: Month-end is blocked because clients have not sent receipts
Goal: Make the reader feel the operational pain
```

Example output style:

```text
Bookkeepers don't lose Sunday nights because accounting is hard.

They lose them because clients still haven't sent the receipts.
```

Use this often.

Recommended share:

```text
30%
```

---

### 10.2 Before/after workflow

Purpose:

Explain the product through workflow contrast.

Input style:

```text
Theme: Before/after workflow
Before: manually checking Xero, emailing clients, following up, checking inbox
After: ChaseDesk detects missing receipts and follows up automatically
```

Example output style:

```text
Before ChaseDesk:

Open Xero.
Find missing receipts.
Email clients.
Follow up again.
Check inbox.
Repeat.

After ChaseDesk:

Open one dashboard.
See what's still blocking close.
```

Recommended share:

```text
20%
```

---

### 10.3 Hidden cost of manual chasing

Purpose:

Show business impact.

Input style:

```text
Theme: Hidden cost
Angle: Receipt chasing is not small admin work; it blocks close, wastes team time, and limits capacity.
```

Example output style:

```text
Receipt chasing looks like admin work.

But it quietly delays close, eats team capacity, and turns bookkeepers into client follow-up machines.
```

Recommended share:

```text
15%
```

---

### 10.4 Competitor/category contrast

Purpose:

Explain ChaseDesk's position in the market.

Input style:

```text
Theme: Category contrast
Insight: Most tools help after receipts arrive. ChaseDesk helps get the receipt to arrive first.
```

Example output style:

```text
Most receipt tools start too late.

They help after the client sends the receipt.

Bookkeepers know the painful part is getting it sent in the first place.
```

Recommended share:

```text
10-20%
```

Do not overuse this.

---

### 10.5 No-login upload link

Purpose:

Show client-side simplicity.

Input style:

```text
Theme: No-login upload
Angle: SMB clients do not want another portal. They need one simple upload link.
```

Example output style:

```text
Your SMB client does not want another portal.

They want one link.

Click.
Upload.
Done.
```

Recommended share:

```text
10%
```

---

### 10.6 Founder observation

Purpose:

Build founder-led credibility.

Input style:

```text
Theme: Founder POV
Angle: The real bookkeeping bottleneck is not OCR. It is client responsiveness.
```

Example output style:

```text
The more we study bookkeeping workflows, the more obvious it gets:

the pain is not accounting.

The pain is coordination.
```

Recommended share:

```text
10%
```

---

### 10.7 Customer discovery questions

Purpose:

Get replies and learn from the market.

Input style:

```text
Theme: Customer question
Question: What takes longer — categorizing transactions or chasing clients for receipts?
```

Example output style:

```text
Xero bookkeepers:

What takes longer every month?

1. Categorizing transactions
2. Chasing clients for receipts
3. Reviewing uploads
4. Explaining delays
```

Recommended share:

```text
10%
```

---

### 10.8 Soft waitlist CTA

Purpose:

Convert interested readers without sounding desperate.

Input style:

```text
Theme: Soft CTA
Angle: We are opening ChaseDesk to Xero firms that still chase receipts manually.
```

Example output style:

```text
We're opening ChaseDesk to a small group of Xero bookkeeping firms.

If missing receipts are still slowing your close, we'd love to learn your workflow.
```

Recommended share:

```text
5-10%
```

---

## 11. Recommended 3-week experiment

Initial test period:

```text
3 weeks
3 tweets/day
21 tweets/week
63 tweets total
```

Recommended theme split:

| Strategy | Share |
|---|---:|
| Pain-led storytelling | 30% |
| Before/after workflow | 20% |
| Hidden cost | 15% |
| No-login upload link | 10% |
| Founder observation | 10% |
| Customer questions | 10% |
| Soft CTA | 5% |
| Competitor/category contrast | Include inside 10–20%, not daily |

Alternative simple ratio:

```text
70% pain/problem
20% category/competitor contrast
10% CTA/product
```

---

## 12. Metrics to track

Every generated/scheduled tweet should be tracked with metadata.

Track:

```text
tweet_id
date
time
content_strategy
story_angle
ICP
competitor_used
tweet_text
character_count
quality_passed
typefully_status
impressions
likes
replies
reposts
bookmarks
profile_clicks
url_clicks
followers_gained
waitlist_clicks
```

---

## 13. How to decide winners

After 2–3 weeks:

### High replies

Means the content is good for conversation.

Likely winners:

- customer discovery questions
- founder POV
- controversial pain observations

### High bookmarks

Means the post felt insightful or useful.

Likely winners:

- workflow breakdowns
- hidden cost posts
- category education

### High profile clicks

Means the reader became curious about ChaseDesk.

Likely winners:

- pain-led storytelling
- before/after workflow
- no-login link posts

### High waitlist clicks

Means the post converts.

Likely winners:

- product explainer
- soft CTA
- specific pain + solution posts

### Low engagement

Check if:

- too generic
- too salesy
- too vague
- no clear pain
- no specific ICP detail
- too much competitor talk

---

## 14. Weekly feedback loop

Every week:

1. Pull performance data from Typefully/X.
2. Sort posts by strategy.
3. Identify top 5 posts.
4. Identify bottom 5 posts.
5. Add winners as good examples.
6. Add bad patterns as rejected examples.
7. Increase weight of winning strategies.
8. Reduce weight of weak strategies.
9. Update banned phrases if needed.
10. Refresh research only if necessary.

Important:

> The system should learn from performance, not from daily web scraping.

---

## 15. Human review rules

Not every tweet needs manual approval.

Suggested approval matrix:

| Post type | Review needed? | Reason |
|---|---|---|
| Pain-led evergreen | No, if quality checks pass | Low factual risk |
| Before/after workflow | No, if based on approved product facts | Low/medium risk |
| No-login upload link | No, if feature is approved | Low risk |
| Founder POV | Optional | Brand voice risk |
| Customer discovery question | No | Low risk |
| Soft CTA | Optional | Conversion tone |
| Competitor contrast | Yes | Tone/legal/positioning risk |
| Posts with numbers | Yes | Proof risk |
| Customer stories | Yes | Must be real and approved |
| News/trend posts | Yes | Freshness risk |

---

## 16. What this system should avoid

### Avoid generic AI content

Bad:

```text
AI is revolutionizing bookkeeping workflows for modern firms.
```

Why bad:

- generic
- no ICP pain
- no specific workflow
- sounds like everyone else

### Avoid fake metrics

Bad:

```text
ChaseDesk saves 90% of your time instantly.
```

Why bad:

- unsupported
- risky
- not credible

### Avoid aggressive competitor attacks

Bad:

```text
Dext is outdated and useless.
```

Why bad:

- insecure
- unprofessional
- unnecessary

### Avoid spammy growth content

Bad:

```text
🚀 Transform your bookkeeping today!!! #AI #Accounting #Automation
```

Why bad:

- spammy
- generic
- not founder-led

---

## 17. What good ChaseDesk content should feel like

Good ChaseDesk content should feel:

```text
specific
operational
calm
slightly sharp
bookkeeper-aware
founder-led
not corporate
not hype-driven
```

The reader should feel:

```text
“They understand my month-end workflow.”
```

not:

```text
“They are trying to sell me AI.”
```

---

## 18. Example generation inputs

These are not hardcoded tweets.

They are examples of the kind of input the system should send to OpenAI.

### 18.1 Pain-led storytelling input

```json
{
  "campaign_goal": "awareness",
  "audience_segment": "firm_owner_2_20_staff",
  "content_strategy": "pain_led_storytelling",
  "story_angle": "month_end_blocked",
  "situation": "A small bookkeeping firm is closing books for 40 clients. The accounting work is mostly done, but missing receipts are blocking final review. The team spends Monday sending reminder emails and checking replies.",
  "product_role": "ChaseDesk detects missing receipts and follows up with clients automatically using no-login upload links.",
  "proof_level": "No exact numbers. Do not invent time saved.",
  "cta_mode": "none"
}
```

### 18.2 Before/after input

```json
{
  "campaign_goal": "product_clarity",
  "audience_segment": "solo_bookkeeper",
  "content_strategy": "before_after_workflow",
  "before": "Open Xero, find missing receipts, email clients, wait, follow up, check inbox, repeat.",
  "after": "ChaseDesk detects missing receipts, sends follow-ups, collects uploads, and shows what is still blocking close.",
  "product_role": "Quiet assistant that removes manual chasing.",
  "cta_mode": "none"
}
```

### 18.3 Category contrast input

```json
{
  "campaign_goal": "positioning",
  "audience_segment": "xero_bookkeeper",
  "content_strategy": "category_contrast",
  "competitor_context": "Most receipt/document tools are strongest after a receipt has already arrived. ChaseDesk focuses on getting missing receipts to arrive in the first place.",
  "rules": "Contrast workflow categories. Do not insult competitors. Do not claim superiority without proof.",
  "cta_mode": "none"
}
```

### 18.4 Soft waitlist input

```json
{
  "campaign_goal": "waitlist",
  "audience_segment": "xero_firm_owner",
  "content_strategy": "soft_waitlist_cta",
  "situation": "A firm still manually follows up with clients for receipts before month-end.",
  "product_role": "ChaseDesk automates the follow-up loop.",
  "allowed_cta": "If this is your workflow, we're opening access in batches.",
  "cta_mode": "soft_waitlist"
}
```

---

## 19. Output examples

These are example outputs to guide tone.

They are **not** meant to be hardcoded.

```text
Month-end doesn't always get delayed by accounting.

Sometimes it's missing receipts sitting between your team and a clean close.
```

```text
The receipt is usually easy to process.

The hard part is getting the client to send it.

That's the boring workflow ChaseDesk is built around.
```

```text
Most receipt tools start too late.

They help after the client sends the receipt.

Bookkeepers know the painful part is getting it sent in the first place.
```

```text
Your client does not need another portal.

They need one link.

Click.
Upload.
Done.
```

```text
No one became a bookkeeper to send the same reminder email five times.

That loop should be automated.
```

---

## 20. Suggested project structure

```text
chasedesk-content-engine/
  README.md
  requirements.txt
  .env.example

  content/
    brand_context.yml
    competitor_research.yml
    content_strategies.yml
    story_seeds.yml
    good_examples.yml
    bad_examples.yml
    banned_phrases.yml

  src/
    config.py
    content_loader.py
    strategy_selector.py
    story_seed_builder.py
    openai_generator.py
    quality_filter.py
    scheduler.py
    typefully_client.py
    logging_utils.py
    orchestrator.py

  tests/
    test_content_loader.py
    test_strategy_selector.py
    test_quality_filter.py
    test_scheduler.py
    test_prompt_builder.py

  logs/
    YYYY-MM-DD.md

  .github/
    workflows/
      post-chasedesk.yml
```

---

## 21. Environment variables

Required:

```text
OPENAI_API_KEY=
TYPEFULLY_API_KEY=
```

Optional:

```text
POSTS_PER_DAY=3
TIMEZONE=Asia/Kolkata
DRY_RUN=true
CHAR_LIMIT=240
HUMAN_REVIEW_COMPETITOR_POSTS=true
```

---

## 22. Dry run mode

Dry run mode should:

- generate tweets
- run quality checks
- create logs
- skip Typefully publishing

This is useful for testing.

Recommended first run:

```text
DRY_RUN=true
```

Only switch to publishing after reviewing generated posts.

---

## 23. Build order

Recommended implementation order:

1. Create content YAML files.
2. Build content loader.
3. Build strategy selector.
4. Build prompt/generation packet builder.
5. Build OpenAI generator.
6. Build quality filter.
7. Build scheduler.
8. Add Typefully client.
9. Add daily logs.
10. Add GitHub Actions.
11. Run dry mode for 3–5 days.
12. Enable real scheduling.

---

## 24. MVP scope

Version 1 should include:

```text
3 tweets/day
Static knowledge base
OpenAI generation
Quality filter
Typefully scheduling
Daily logs
GitHub Actions cron
Dry run mode
```

Do not add in V1:

```text
database
dashboard
daily web research
reply automation
auto-engagement
complex analytics engine
multi-platform optimization
```

Keep V1 boring and stable.

---

## 25. Future improvements

After 2–3 weeks:

### Add performance tracking

Pull metrics from Typefully/X:

- impressions
- likes
- replies
- bookmarks
- reposts
- clicks
- profile visits

### Add weighted strategy selection

If `pain_led_storytelling` performs best, increase its weight.

Example:

```yaml
strategy_weights:
  pain_led_storytelling: 0.40
  before_after_workflow: 0.20
  hidden_cost: 0.15
  no_login_upload_link: 0.10
  founder_observation: 0.10
  soft_waitlist_cta: 0.05
```

### Add recent post similarity check

Avoid repeating the same wording.

### Add LinkedIn support

Reuse same strategy system, but change:

- post length
- formatting
- CTA style
- story depth

### Add monthly research refresh

Only refresh competitor research when:

- a competitor launches a major feature
- pricing changes
- Xero platform rules change
- a new accounting automation trend appears
- ChaseDesk positioning changes

---

## 26. Important decisions made so far

### Decision 1: Static research, not daily research

The market is narrow. Daily research adds noise.

### Decision 2: No hardcoded tweets

Tweets should be generated fresh from structured context.

### Decision 3: Storytelling over feature posting

Content should show why the product matters through business workflow stories.

### Decision 4: Multiple themes, then double down

Run multiple strategies for 2–3 weeks, measure what performs, then increase weight on winning themes.

### Decision 5: ChaseDesk is not generic AI accounting automation

The sharp positioning is:

> Receipt-chasing autopilot for Xero bookkeeping firms.

### Decision 6: Product is not the hero

The bookkeeper is the hero. ChaseDesk is the quiet assistant.

### Decision 7: Competitor contrast should be careful

Do not attack competitors. Contrast workflow categories.

### Decision 8: Quality filter is mandatory

Without quality checks, output will drift into generic AI content.

---

## 27. The core philosophy

This project is not just a tweet bot.

It is a small content operating system.

It uses:

```text
research
positioning
storytelling
structured prompting
quality control
scheduling
feedback loops
```

to create better social content over time.

The desired outcome:

> ChaseDesk becomes known as the product that understands and solves missing receipt chasing for Xero bookkeeping firms.

---

## 28. One-line summary

ChaseDesk Content Engine uses structured market research, ICP pain, storytelling themes, OpenAI generation, strict quality filters, and Typefully scheduling to produce fresh, founder-led tweets that help Xero bookkeeping firms understand why automated receipt chasing matters.

---

## 29. Current status

Research and strategy are mostly complete.

Done:

- ChaseDesk positioning clarified
- ICP identified
- competitor landscape mapped
- competitor marketing patterns studied
- content themes defined
- OpenAI input strategy designed
- no-hardcoded-tweets decision made
- no-daily-research decision made
- 2–3 week experimentation plan created
- Typefully/OpenAI architecture selected

Left to build:

- content YAML files
- OpenAI generation system
- quality filter
- Typefully scheduling
- logs
- GitHub Actions workflow
- dry-run testing
- performance tracking after initial posting period

---

## 30. Final note

The system should always optimize for specificity.

Bad content sounds like:

> AI automation for modern accounting firms.

Good content sounds like:

> Month-end is blocked because clients still have not sent the receipts.

That difference is the whole game.
