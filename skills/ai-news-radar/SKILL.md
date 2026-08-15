---
name: ai-news-radar
description: "Use when maintaining seisyuku/ai-news-radar_zhtw: evaluating AI industry sources, adding RSS/Atom/OPML/public feeds, diagnosing source health, changing data generation or the web UI, and operating GitHub Actions or GitHub Pages."
---

# AI News Radar

## First Reads

When this skill triggers inside the repo, read the smallest relevant set in this
order:

1. `README.md` for the current product boundary.
2. `docs/HANDOVER.md` for current decisions, known facts, and open checkpoints.
3. `docs/SOURCE_COVERAGE.md` before adding, removing, or rerouting a source.
4. `docs/OPERATIONS.md` for Actions, Pages, heartbeat, and incident procedures.
5. `docs/ROADMAP.md` before changing product direction or priorities.
6. `scripts/update_news.py` before changing generation or fetch behavior.
7. `assets/app.js`, `assets/styles.css`, and `index.html` before UI changes.
8. `references/source-intake.md` for source intake and
   `references/v2-method.md` for product or architecture work.

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

1. Inspect current repo state, relevant docs, recent commits, and the smallest
   code surface.
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
- Before changing the AI relevance scoring formula, stop and follow the repo's
  backtest and approval rule.

## Source Intake

Use the highest stable option that meets the need:

1. Official RSS, Atom, or owner-published JSON.
2. Maintained public generated feeds with canonical URLs and timestamps.
3. Public newsletter archive or stable static page.
4. Private OPML for maintainer-specific sources.
5. Optional API adapter using user-owned secrets.
6. Reject sources that require login state, cookies, unstable bridges, or add
   mostly duplicate/noisy material.

Before promoting a candidate RSS/Atom source into the public default, run:

```bash
python scripts/evaluate_source_overlap.py \
  --source-url https://example.com/feed.xml \
  --source-name "Example Source" \
  --site-id example_candidate \
  --baseline data/archive.json \
  --lookback-days 7 \
  --output reports/source-intake/example-overlap.json
```

Treat the report as advisory. Check sample size, source quality, canonicality,
timeliness, unique coverage, and Actions compatibility before deciding. Details
and parser patterns are in `references/source-intake.md`.

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

Run the fastest relevant checks:

```bash
python -m py_compile scripts/update_news.py
python -m pytest -q
node --check assets/app.js
git diff --check
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/ai-news-radar
```

For source changes, generate into a temporary directory and inspect
`source-status.json` rather than overwriting tracked snapshots:

```bash
python scripts/update_news.py --output-dir /tmp/ai-news-radar-data \
  --window-hours 24 --rss-opml feeds/follow.opml
```

Confirm the source has an explicit success or failure status, item counts are
plausible, and the AI/business-event views are not flooded with off-topic items.

After an authorized push, use the current repository coordinates:

```bash
gh workflow run update-news.yml --repo seisyuku/ai-news-radar_zhtw --ref master
gh run list --repo seisyuku/ai-news-radar_zhtw --limit 5
```

Do not trigger workflows, push, or modify repository settings unless the user's
request authorizes that external state change.
