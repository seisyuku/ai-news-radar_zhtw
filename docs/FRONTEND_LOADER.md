# Frontend loader contract

`assets/loader.js` exposes `AiRadarLoader` as a classic browser script and the
same API through CommonJS for direct Node tests. It has no DOM or app imports.
Load it with `defer` before `assets/app.js`; the loader, app, motion and stylesheet
references share one cache tag in `index.html`. No bundler or framework is needed.

## Interface and ownership

`createLoader({ state })` returns `fetchJson`, `loadNewsData`, `loadAllModeData`,
`loadSourceStatusData`, `loadDailyBriefData`, `loadStoriesData`,
`loadMarketSignalsData` and `loadLlmRadarData`. Each loader instance belongs to
its caller's state object; there is no shared module-level request cache.

Tests can inject `fetchImpl`, `now`, `setTimeoutFn`, `clearTimeoutFn` and
`AbortControllerClass`. The default implementations use browser globals.
`fetchJson(path, label, timeoutMs)` adds the existing `?t=<timestamp>` token,
rejects HTTP errors, parses JSON, and races the entire request plus body parsing
against one timeout. It aborts on timeout and clears the timer on every outcome.
It retains the existing error messages and performs no implicit retries.

| Method | Path | Timeout |
| --- | --- | --- |
| `loadNewsData` | `./data/latest-24h.json` | 12 seconds |
| `loadAllModeData` | `./` plus the current `state.allDataUrl` | 12 seconds |
| `loadStoriesData` | `./` plus the current `state.storiesDataUrl` | 8 seconds |
| `loadSourceStatusData` | `./data/source-status.json` | 8 seconds |
| `loadDailyBriefData` | `./data/daily-brief.json` | 8 seconds |
| `loadMarketSignalsData` | `./data/market-signals.json` | 8 seconds |
| `loadLlmRadarData` | `./data/llm-radar.json` | 8 seconds |

Ordinary methods return parsed payloads. All-mode keeps its existing state
contract: it reads `allDataLoaded`, `allDataPromise`, `allDataUrl` and `itemsAi`,
then writes `itemsAllRaw`, `itemsAll`, `totalRaw`, `totalAllMode` and
`allDataLoaded` on success. It retains the existing legacy field and count
fallbacks. Concurrent consumers share one underlying request. On failure or
timeout, `allDataPromise` becomes null, leaving the next explicit user click
free to retry. Already-loaded all-mode data causes no new request.
Its returned promise resolves after state updates, rather than returning a
payload; async callers need not receive the same promise object.

`app.js` still owns initialization, DOM rendering, filters and mode selection.
It waits for main news, renders once and emits `aiRadar:ready`, then starts five
independent auxiliary requests. Background responses retain the current query,
mode and expansion state. Source-status success or failure refreshes header
statistics. The app's all-mode request ID and current mode checks still prevent
late success or failure from repainting a newer user choice.

## Validation and future extraction

`tests/frontend_loader_module.test.cjs` directly imports the actual module for
path/timeouts, timer cleanup, abort, body stalls, explicit retry, request sharing,
legacy fallbacks and both export modes. `tests/frontend_loader_scenarios.cjs`
executes the complete loader and app scripts in a Node VM with DOM/rendering
stubs. It suppresses only the final automatic `init()` invocation so each
scenario can control startup; it no longer slices loader or event declarations.
`tests/test_frontend_loader.py` runs both harnesses in the existing pytest suite.
Real-browser smoke remains necessary for script order, startup and DOM behavior.

The offline workflow covers `assets/**` and runs loader syntax plus these tests.
The asset-version workflow covers the new loader explicitly. Current HTML must
reference all four versioned assets once; Git comparison can still read a
historical three-asset baseline. Local runs may exclude the Git-baseline check
when required by the task, while retaining reference/order checks.

Potential later extraction should begin with a bounded selection helper such
as `itemMatchesSection`, with focused contract tests before moving it.
`storyMatchesFilteredItems` currently reads app state and would need explicit
filter inputs before becoming a pure helper. DOM rendering, source categories,
scoring and featured-selection policies remain outside this loader boundary.
