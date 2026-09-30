// Directly import the shipped loader; no app.js declaration extraction or DOM.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");
const loader = require("../assets/loader.js");

function fixture(fetchImpl) {
  const state = { itemsAi: [{ id: "ai" }], allDataLoaded: false,
    allDataPromise: null, allDataUrl: "data/latest-24h-all.json",
    storiesDataUrl: "data/stories-merged.json" };
  const timers = [];
  const cleared = [];
  const api = loader.createLoader({ state, fetchImpl, now: () => 123,
    setTimeoutFn(callback, delay) { timers.push({ callback, delay }); return timers.length; },
    clearTimeoutFn(id) { cleared.push(id); } });
  return { api, state, timers, cleared };
}

test("CommonJS import needs no document and classic browser export needs no module", () => {
  assert.equal(typeof document, "undefined");
  assert.equal(typeof loader.createLoader, "function");
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../assets/loader.js"), "utf8"), context);
  assert.equal(typeof context.AiRadarLoader.createLoader, "function");
  assert.equal(context.AiRadarLoader.AUXILIARY_FETCH_TIMEOUT_MS, 8000);
  assert.equal(context.AiRadarLoader.PRIMARY_FETCH_TIMEOUT_MS, 12000);
});

test("each JSON method uses its existing path, cache token and timeout", async () => {
  const calls = [];
  const env = fixture(async (url, options) => {
    calls.push({ url, signal: options.signal });
    return { ok: true, json: async () => ({ sites: [] }) };
  });
  for (const [method, file, timeout] of [
    ["loadNewsData", "latest-24h.json", 12000],
    ["loadSourceStatusData", "source-status.json", 8000],
    ["loadDailyBriefData", "daily-brief.json", 8000],
    ["loadStoriesData", "stories-merged.json", 8000],
    ["loadMarketSignalsData", "market-signals.json", 8000],
    ["loadLlmRadarData", "llm-radar.json", 8000],
  ]) {
    await env.api[method]();
    assert.equal(calls.at(-1).url, `./data/${file}?t=123`);
    assert.equal(env.timers.at(-1).delay, timeout);
    assert.equal(calls.at(-1).signal.aborted, false);
  }
  assert.equal(env.cleared.length, calls.length);
});

test("stories and all-mode paths are read from current state at call time", async () => {
  const urls = [];
  const env = fixture(async (url) => {
    urls.push(url);
    return { ok: true, json: async () => ({ items_all: [] }) };
  });
  env.state.storiesDataUrl = "data/custom-stories.json";
  env.state.allDataUrl = "data/custom-all.json";
  await env.api.loadStoriesData();
  await env.api.loadAllModeData();
  assert.deepEqual(urls, ["./data/custom-stories.json?t=123", "./data/custom-all.json?t=123"]);
  assert.equal(env.timers.at(-1).delay, 12000);
});

test("fetch and body parsing are covered by the same timeout and abort", async () => {
  for (const stalledBody of [false, true]) {
    let signal;
    const env = fixture((_url, options) => {
      signal = options.signal;
      return stalledBody ? Promise.resolve({ ok: true, json: () => new Promise(() => {}) })
        : new Promise(() => {});
    });
    const pending = env.api.loadNewsData();
    await Promise.resolve();
    env.timers[0].callback();
    await assert.rejects(pending, /載入 latest-24h\.json 逾時/);
    assert.equal(signal.aborted, true);
    assert.deepEqual(env.cleared, [1]);
  }
});

test("HTTP, network and parse errors reject and clear their timer", async () => {
  for (const kind of ["http", "network", "parse"]) {
    const env = fixture(async () => {
      if (kind === "network") throw new Error("network offline");
      return { ok: kind !== "http", status: 503, json: async () => { throw new Error("bad JSON"); } };
    });
    await assert.rejects(env.api.loadSourceStatusData(), kind === "http" ? /失敗: 503/ : kind === "network" ? /network offline/ : /bad JSON/);
    assert.deepEqual(env.cleared, [1]);
  }
});

test("concurrent all-mode consumers share one fetch; loaded data stays cached", async () => {
  let release;
  let requests = 0;
  const env = fixture(() => { requests += 1; return new Promise((resolve) => { release = resolve; }); });
  const first = env.api.loadAllModeData();
  const second = env.api.loadAllModeData();
  const rows = [{ id: "all" }];
  release({ ok: true, json: async () => ({ items_all: rows, total_items_all_mode: 1 }) });
  await Promise.all([first, second]);
  assert.equal(requests, 1);
  assert.equal(env.state.itemsAll, rows);
  assert.equal(env.state.itemsAllRaw, rows);
  assert.equal(env.state.allDataLoaded, true);
  await env.api.loadAllModeData();
  assert.equal(requests, 1);
});

test("failed or timed-out all-mode requests clear the promise and allow explicit retry", async () => {
  for (const kind of ["http", "timeout"]) {
    let requests = 0;
    const env = fixture(async () => {
      requests += 1;
      if (requests === 1) return kind === "http" ? { ok: false, status: 503 } : new Promise(() => {});
      return { ok: true, json: async () => ({ items_all: [{ id: "retry" }] }) };
    });
    const failed = env.api.loadAllModeData();
    if (kind === "timeout") env.timers[0].callback();
    await assert.rejects(failed);
    assert.equal(env.state.allDataPromise, null);
    assert.equal(env.state.allDataLoaded, false);
    await env.api.loadAllModeData();
    assert.equal(requests, 2);
    assert.equal(env.state.itemsAll[0].id, "retry");
  }
});

test("legacy all-mode fallback preserves AI items and existing count semantics", async () => {
  const env = fixture(async () => ({ ok: true, json: async () => ({}) }));
  await env.api.loadAllModeData();
  assert.equal(env.state.itemsAll, env.state.itemsAi);
  assert.equal(env.state.itemsAllRaw, env.state.itemsAi);
  assert.equal(env.state.totalRaw, 1);
  assert.equal(env.state.totalAllMode, 1);
});
