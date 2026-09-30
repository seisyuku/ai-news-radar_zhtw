# Source health contract

`scripts/source_health.py` owns health history, group diagnostics and persistent
failure reporting. It imports only the Python standard library. Source adapters,
their registries, paid-source interval gates and public payload sanitization
remain in `scripts/update_news.py`. Source acceptance and product boundaries
remain governed by [SOURCE_COVERAGE.md](SOURCE_COVERAGE.md).

## Module API

| Function | Input and result | Effects |
| --- | --- | --- |
| `load_source_status(path)` | Existing JSON object, or `{}` for missing, unreadable, invalid JSON or non-object input | Reads one file; does not rewrite it |
| `fetch_subsource_with_status(source_id, fetch)` | A callback returning a list of items; returns `(items, child_status)` | Executes the callback; catches ordinary exceptions and exposes only safe error codes |
| `summarize_subsources(subsources)` | Current child observations; returns group `ok`, `degraded`, reason, error and the same child list | Does not copy or change child rows |
| `apply_source_health_history(statuses, previous_status, now_iso, *, threshold=3)` | Fresh current site observations, previous snapshot and caller-supplied UTC ISO timestamp; returns persistent failures | Mutates current sites and children in place; leaves previous snapshot untouched; no clock reads or file writes |
| `apply_subsource_health_history(status, previous, now_iso, threshold, persistent_failures)` | One current group and the previous row for that **same site**; returns whether children are present | Updates children and appends their alerts; normally called by the site-level function |
| `report_persistent_source_failures(failures)` | Persistent failures for actual attempts | Prints Actions warnings and appends a table to `GITHUB_STEP_SUMMARY` when set; no output for an empty list |

The existing `update_news.apply_source_health_history` entrypoint still accepts
`datetime` and delegates after applying the generator's `iso(now)` conversion.
The loader, child history helper and private group helpers retain
their existing `update_news` import names through aliases. Both package and
direct-script entrypoints are supported. The `update_news` reporter retains its
existing signature through a wrapper that sanitizes a copy before publication.

## Data and state transitions

Minimal `TypedDict` contracts describe known fields, without introducing runtime
schema enforcement or removing extension fields. `SiteStatus` requires `site_id`;
`SubsourceStatus` requires `source_id`; `PersistentFailure` requires `site_id`
and `consecutive_failures`. `HealthHistory` describes optional history fields.
Fields are optional to support observations before calculation and older
snapshots. The lenient loader does not validate nested field types.

History is scoped by `site_id` and then by the exact `source_id`. A new or renamed
child starts fresh; a removed child is absent from an attempted group's current
rows. An old group snapshot without children cannot supply a child's streak.
An older skipped snapshot's retained failure count or success timestamp may
recover its last real result; lost history cannot be reconstructed.

| Observation | Failure streak and timestamps | Persistent alert |
| --- | --- | --- |
| Actual success, including a valid empty result | Clears the streak and first failure; updates last success; retains last failure | None |
| Actual failure | Continues only the same identity's last failed attempt; updates last failure; retains last success | At and above `max(1, threshold)` |
| Scheduled skip | Preserves last real result, streak and timestamps; does not count as success or failure | None, even when the retained streak is persistent |

A skipped group with an empty child list retains known children as explicitly
skipped observations. Child `ok` becomes `null`, `item_count` becomes zero,
`error` becomes `null`, and `attempted` is false. A retained failure also marks
the skipped observation degraded. Site `ok`, `attempted` and interval metadata
remain the caller's responsibility; the history calculation does not recast a
site skip as an actual fetch.

Whole-group history stays separate from child history. A single child recovery
never resets a peer's streak. An all-failed group can retain its own persistent
state, but emits child alerts without a duplicate group alert. Supply fresh
current observations on every run; this API is a state transition, not an
idempotent recalculation of already-enriched rows.

## Public diagnostics and extension requirements

A valid feed/page with no recent matching items is successful. Malformed or
unusable source content must raise `ValueError`, yielding `invalid_source`;
other ordinary fetch errors yield `fetch_failed`. Exception messages, feed URLs
and private credentials are not placed in these child diagnostics.

Some children succeeding keeps usable articles and sets
`degraded_reason: partial_subsource_failure`; all children failing sets group
`ok: false` and `error: all_subsources_failed`. Warning and summary identities
are `site_id/source_id` for children and `site_id` for sites. The reporter keeps
existing workflow escaping (`%`, CR, LF) and Markdown error-cell escaping
(`|`, LF). The standalone `source_health` reporter formats caller-supplied
errors; callers using that module directly must supply safe diagnostic values.
The generator's `update_news.report_persistent_source_failures` wrapper applies
the existing public secret/email redaction policy before publishing warnings
and summaries, matching `main()`'s sanitized `source-status.json` payload.
Redaction leaves the caller's original health history and error observations
untouched. The module remains independent of the generator and its sanitizer.

When adding a child, use a unique, stable, public ID within its site; never derive
it from a private URL or credential. Return a current observation for each
attempted child, validate source content separately from relevance filtering,
retain successful peers' items, and route history through the site-level API.
Test partial/all failure, valid empty results, failure→skip→failure, recovery,
renamed IDs, same IDs in different sites, and the configured alert threshold.

This module does not define reader source categories. The reader's header and
`successful_sites` remain group-level `ok` counts; child degradation and history
remain maintainer diagnostics. A reader-facing child warning would need a
separate product decision and frontend task.
