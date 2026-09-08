# AI News Radar Agent Notes

## Scope

This repo powers the public AI News Radar static site and its maintainer Skill
source workflow.
Use it for high-signal AI/tech news aggregation, OPML-based custom feeds,
GitHub Actions refresh jobs, and GitHub Pages publishing.

## Working Rules

- Keep changes small and reviewable.
- Search the repo before changing source fetchers or output schemas.
- Do not commit private feeds, secrets, tokens, cookies, or `.env` values.
- Do not commit `feeds/follow.opml`; use `feeds/follow.example.opml` as the public template.
- Prefer stable public RSS/Atom/OPML sources before adding custom scrapers.
- Keep the reader-facing product simple: default to a curated AI-focused view, hide noisy or advanced source details behind existing filters/docs.

## Authority and Routing

- `README.md` defines the current public product boundary.
- `docs/HANDOVER.md` records current decisions and active checkpoints.
- `docs/SOURCE_COVERAGE.md` governs source status, acceptance, and replacement.
- `docs/OPERATIONS.md` governs Actions, Pages, scheduled refreshes, and incidents.
- `docs/ROADMAP.md` governs product direction and priorities.
- `skills/ai-news-radar/SKILL.md` routes maintainer workflows to the relevant code, documents, and references.

Read only the authority that governs the requested change.

## Source Strategy

Default source priority:

1. Official RSS/Atom feeds and OPML collections.
2. Stable public JSON APIs or static pages with timestamps.
3. Curated newsletters or changelogs with public feeds.
4. Manual/custom adapters only when the source is high-signal and stable.

Avoid account-bound timelines, broad personal social feeds, login-gated pages,
and fragile bridges unless the user explicitly accepts the maintenance cost.

## Validation by Change Type

```bash
# Environment setup, when needed
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Python fetch, generation, or schema changes
python -m py_compile scripts/update_news.py
python -m pytest -q <relevant-test-paths>

# JavaScript changes
node --check assets/app.js

# Repository hygiene
git diff --check
```

Run the full Python suite when shared generation, schema, scoring, or release behavior changes. For source work, generate into a temporary output directory and inspect `source-status.json`; do not overwrite tracked snapshots as a side effect of validation.
