---
name: ai-news-radar
description: "Maintain AI News Radar sources, data generation, reader UI, and GitHub operations. Use for work in seisyuku/ai-news-radar_zhtw involving feeds or OPML, source health, the web app, Actions, or Pages."
---

# AI News Radar

## Reference Routing

Read only the routes that govern the requested change:

- Product scope or reader-layer changes: `README.md`; add `docs/ROADMAP.md` when priorities or direction change.
- Resuming an active work stream or relying on a prior decision: `docs/HANDOVER.md`.
- Adding, removing, evaluating, or rerouting sources: `docs/SOURCE_COVERAGE.md` and `references/source-intake.md`.
- Actions, Pages, schedules, deployment, or incidents: `docs/OPERATIONS.md`.
- Generation or fetch behavior: the relevant parts of `scripts/update_news.py` and its tests.
- Reader UI: the affected parts of `assets/app.js`, `assets/styles.css`, or `index.html` and their tests.
- Product or architecture method: `references/v2-method.md`.

Do not use deleted upstream handoffs, marketing pages, Reader Skill assets, or
the upstream site as current project authority.

## Product Direction

Maintain a two-layer product:

- **Reader layer**: a simple Taiwan Traditional Chinese dashboard focused on
  six types of material AI-industry business events.
- **Maintainer layer**: source health, source governance, OPML customization,
  GitHub Actions, deployment controls, and optional secret-backed adapters.

The general list can carry broader AI-industry reporting, but the public product
is not a programming-tutorial, prompt-tip, personal-social-feed, or general-news
aggregator. Prefer fewer defensible signals over filling a quota with noisy
sources.

## Working Loop

For non-trivial work:

1. Inspect current repo state, the routed authority, and the smallest affected code surface.
2. State the user-visible problem and the evidence that would count as fixed.
3. For source work, classify the source as official feed, public generated feed,
   static page, OPML-only customization, secret-backed adapter, or reject.
4. Search for existing fetcher, schema, status, UI, and test patterns before
   editing.
5. Make a small reviewable diff and add tests for behavior changes.
6. Run proportional validation and inspect `source-status.json` for source work.
7. Update `HANDOVER.md`, `SOURCE_COVERAGE.md`, or `OPERATIONS.md` only when the
   change affects their current authority.

## Safety Rules

- Never commit `feeds/follow.opml`, secrets, API keys, tokens, cookies, browser
  exports, inbox identifiers, private email content, or `.env` values.
- Keep the public repo runnable without credentials.
- Prefer official RSS, Atom, OPML, or stable public JSON over custom scraping.
- Avoid account-bound social timelines, browser automation, and fragile bridges
  as public defaults.
- Optional X API, email, or other private integrations must skip cleanly when
  their credentials are absent.
- Do not publish `data/email-digest.json` unless the maintainer explicitly opts
  into publication and accepts the privacy implications.
- Do not hand-edit scheduled `data/*.json` unless the task explicitly requires
  a snapshot refresh.
- For changes to AI relevance scoring or its `0.65` floor, follow the 14-day backtest requirement in `docs/HANDOVER.md`. A user request to change the scoring behavior authorizes local implementation and validation; request a product decision only when the requested outcome leaves the threshold or tradeoff unresolved.

## Source Intake

Follow `references/source-intake.md` for source classes, evaluation commands,
parser patterns, and promotion criteria. Record the resulting source status in
`docs/SOURCE_COVERAGE.md` when the accepted default set changes.

## Personal OPML

Use the ignored local file for private customization:

```bash
cp feeds/follow.example.opml feeds/follow.opml
python scripts/update_news.py --output-dir /tmp/ai-news-radar-data \
  --window-hours 24 --rss-opml feeds/follow.opml
```

In GitHub Actions, store the base64-encoded private OPML in the
`FOLLOW_OPML_B64` secret. When absent, the public example OPML remains the safe
fallback. Never commit the real file.

## Validation

Choose checks by the affected surface:

```bash
# Markdown or metadata
git diff --check

# Python fetch or generation code
python -m py_compile scripts/update_news.py

# Python tests: start with affected files; use the full suite for shared
# generation, schema, scoring, or release behavior
python -m pytest -q <relevant-test-paths>

# Reader JavaScript
node --check assets/app.js

# Skill structure
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/ai-news-radar
```

For source changes, also run the overlap evaluation from
`references/source-intake.md`, generate into a temporary directory, and inspect
`source-status.json` rather than overwriting tracked snapshots:

```bash
python scripts/update_news.py --output-dir /tmp/ai-news-radar-data \
  --window-hours 24 --rss-opml feeds/follow.opml
```

Confirm the source has an explicit success or failure status, item counts are
plausible, and the AI/business-event views are not flooded with off-topic items.

For AI relevance scoring changes, run the 14-day comparison with
`scripts/backtest_scoring.py` and review inclusion/exclusion flips before treating
the change as validated.

After an authorized push, use the current repository coordinates:

```bash
gh workflow run update-news.yml --repo seisyuku/ai-news-radar_zhtw --ref master
gh run list --repo seisyuku/ai-news-radar_zhtw --limit 5
```

Do not trigger workflows, push, or modify repository settings unless the user's
request authorizes that external state change.
