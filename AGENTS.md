# AI News Radar Agent Notes

## Scope

This repo powers the public AI News Radar static site and its maintainer Skill
source workflow.
Use it for high-signal AI/tech news aggregation, OPML-based custom feeds,
GitHub Actions refresh jobs, and GitHub Pages publishing.

## Working Rules

- T04 Gemini news-summary fallback is retired. Do not propose, recreate, or retest that design. Retained Gemini API/diagnostic/notification helpers are dormant and may be used only for a separately requested new purpose; existing reader translation remains maintained.
- Keep changes small and reviewable.
- Search the repo before changing source fetchers or output schemas.
- Do not commit private feeds, secrets, tokens, cookies, or `.env` values.
- Do not commit `feeds/follow.opml`; use `feeds/follow.example.opml` as the public template.
- Prefer stable public RSS/Atom/OPML sources before adding custom scrapers.
- Keep the reader-facing product simple: default to a curated AI-focused view, hide noisy or advanced source details behind existing filters/docs.
- A traceable original announcement or report is enough for the source requirement of general ranking. Use existing scope, source-use, and recency rules. Keep citations as references and leave factual verification to the social media editorial assistant. Routine refresh uses configured source material and does not follow citations to extend an article or its ranking eligibility.

## Release shorthand

- In this repository, the user's `commit push` request means commit the relevant
  changes, integrate them into the latest `master`, push `master`, and verify the
  public Pages site and its matching generated data. A feature-branch push alone
  does not complete this request.
- Preserve concurrent snapshot commits and unrelated local work. Integrate only
  the requested changes; do not force-push or publish unrelated draft branches.

## Conversation Output and Candidate Lists

- Keep task ledgers and handoff documents current, retaining only current
  status and items/history from the last ten days in Taipei time. Remove older
  entries rather than accumulating them in separate handoff archives.

- Default to complete, readable output directly in the conversation, using
  prose, tables, and inline images when useful. The user often reads on a phone;
  avoid requiring a new file, window, or tab to consume the result.
- Do not routinely create separate report files or open additional windows.
  Exceptions are handoff files, files explicitly requested or needed for local
  preservation, and outputs with a concrete, strong reason to be separate.
  Explain that reason and still show the essential result in the conversation.
- Updating an existing instruction file to preserve an explicitly requested
  workflow preference does not require creating a separate report.
- For news candidate lists, state the snapshot cutoff and time window in Taipei
  time, then use this fixed table format in the conversation:

  | 題目 | 內容 | 證據 | 判定理由／缺口 |
  |---|---|---|---|
  | Linked topic title | Full / Brief / Drop | Ready / Hold | Value rationale, original source link or access gap, and relevant limits |

- Content value (Full / Brief / Drop) and evidence readiness (Ready / Hold)
  are independent judgments. Full may be Hold; Brief does not imply weak
  evidence. Do not replace these axes with priority or backup labels.
- Ready means the original release or reporting for the item is accessible
  in a supported format. Cite it. For Hold, name the missing original source
  or access issue. The social media editorial assistant handles verification
  of factual claims before publication. Mark old events or out-of-window
  items separately.
- Before delivering a candidate list, check that every row has both judgments
  and a reason or evidence boundary. Put supporting source links in the table
  or directly below it so a separate file is not needed.

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
