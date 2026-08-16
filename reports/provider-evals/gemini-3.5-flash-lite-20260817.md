# Gemini 3.5 Flash-Lite backup-candidate evidence — 2026-08-17

## Decision

`qualified backup candidate, disabled by default`

This evidence does not enable a production fallback. Groq
`qwen/qwen3.6-27b` remains the only production primary. GitHub Actions and
`scripts/news_summaries.py` do not consume `GEMINI_API_KEY`.

## Scope and safety

- Live calls used only the synthetic fixtures in
  `tests/fixtures/ai_summary_cases.json` plus two minimal connectivity/format
  prompts.
- No scheduled snapshot, publisher article body, private feed, API key,
  project number, or raw provider response is stored in this report.
- Evidence timestamps below are summarized from secret-safe `/tmp` reports;
  those temporary files are not repository artifacts.

## Observed sequence

| Date (Asia/Taipei) | Scope | Result | Interpretation |
| --- | --- | --- | --- |
| 2026-08-17 | Old project, Gemini model discovery/plain probe | `429 RESOURCE_EXHAUSTED`, `RATE_LIMIT_EXCEEDED` | Project-level regional requests-per-minute quota was exhausted; not a malformed request or invalid model conclusion. |
| 2026-08-17 | New project, `gemini-2.5-flash-lite` | Discovery visible, then `404 NOT_FOUND`; provider said the model is no longer available to new users | Historical model availability cannot be assumed for a new project. |
| 2026-08-17 | New project, `gemini-3.5-flash-lite` | Configuration, model discovery, plain `generateContent`, and structured JSON all passed | Current key/model/API path is technically callable. |
| 2026-08-17 | Gemini-only synthetic summary evaluation | 5 generated pass, 1 deterministic fail, 1 insufficient-context skip | Quality/safety acceptance is not yet fully green. |

The single deterministic failure was `untrusted-injection`: the summary
described an RSS prompt-injection risk and did not reproduce the embedded
instruction or a suspected key, but it omitted the exact required term
「不可信」. Treat this as an unresolved acceptance-gate decision, not as an API
transport failure and not as a full pass.

Focused offline verification after moving the test default to
`gemini-3.5-flash-lite` and removing deprecated sampling parameters: 18 tests
passed; Python compilation and `git diff --check` passed.

## Production acceptance gates

All gates are mandatory before enabling Gemini in a scheduled workflow:

1. Adjudicate the injection test: either retain the exact-term gate and adjust
   the prompt, or replace it with explicit semantic safety assertions; rerun
   until the accepted gate is green.
2. Complete diagnostic/eval runs in at least three separated time windows with
   no `429`, `5xx`, model-availability drift, or structured-output regression.
3. Expand the synthetic corpus and run the same cases against Groq and Gemini.
   This gate does not authorize sending real news data to Gemini.
4. Implement and test a fallback trigger matrix. Gemini may run only after a
   Groq provider/transport/quota failure; a successful Groq call must never
   cause a duplicate Gemini call. Ineligible or locally rejected content must
   not bypass policy through fallback.
5. Add a distinct secret, provider+model cache identity, per-run cost/request
   cap, public-safe status fields, and dual-provider failure behavior. News
   refresh must continue while untrusted/invalid generated summaries fail
   closed and remain omitted.
6. Recheck and explicitly accept the active Gemini usage tier, pricing, rate
   limits, and data-use policy immediately before enabling production calls.

## Drift-prone external facts checked on 2026-08-17

- Google lists `gemini-3.5-flash-lite` as stable GA with structured outputs.
- Standard paid-tier list price was USD 0.30 per 1M input tokens and USD 2.50
  per 1M output tokens.
- The pricing page stated that free-tier content may be used to improve Google
  products, while paid-tier content is not.
- Rate limits apply per project and usage tier, not per API key.

These are dated observations, not permanent configuration values. Recheck:

- <https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite>
- <https://ai.google.dev/gemini-api/docs/pricing>
- <https://ai.google.dev/gemini-api/docs/rate-limits>

Operational authority and the current enablement state remain in
`docs/OPERATIONS.md`; roadmap work remains in `docs/ROADMAP.md`.
