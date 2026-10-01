// Run the complete shipped app with mocked DOM/rendering and the real loader.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../assets/app.js"), "utf8");
const selectionSource = fs.readFileSync(path.join(__dirname, "../assets/selection.js"), "utf8");
const loaderSource = fs.readFileSync(path.join(__dirname, "../assets/loader.js"), "utf8");
// Suppress only automatic startup so each scenario controls when init runs.
// Functions, state, loader wiring and registered handlers execute unchanged.
assert.match(source, /\ninit\(\);\s*$/);
const app = source.replace(/\ninit\(\);\s*$/, "\n");
const news = { items_ai: [{ id: "one" }], generated_at: "2026-09-26T00:00:00Z" };
const defaults = {
  "./data/latest-24h.json": news,
  "./data/source-status.json": { sites: [] },
  "./data/daily-brief.json": { items: [] },
  "./data/stories-merged.json": { stories: [] },
  "./data/market-signals.json": { signals: [] },
  "./data/llm-radar.json": { events: [] },
  "./data/latest-24h-all.json": { items_all: [{ id: "all" }], items_all_raw: [{ id: "all" }] },
};
const flush = () => new Promise((resolve) => setImmediate(resolve));

function environment({ pending = [], failures = [], sequence = {} } = {}) {
  const gates = {};
  const events = [];
  const calls = [];
  const observed = { list: 0, brief: [], stale: 0, health: [], coverage: [], stats: [] };
  const elements = {};
  const element = (id) => elements[id] ||= {
    innerHTML: "", textContent: "載入中...", value: "",
    appendChild() {},
    addEventListener(type, handler) { this[type] = handler; },
    getAttribute() { return ""; },
  };
  const newsListEl = element("newsList");
  const updatedAtEl = element("updatedAt");
  const modeAllBtnEl = element("modeAllBtn");
  const fetch = (url, options = {}) => {
    const key = url.split("?")[0];
    calls.push({ key, signal: options.signal });
    const values = sequence[key];
    if (values && values.length) {
      const value = values.shift();
      if (value instanceof Error) return Promise.reject(value);
      return Promise.resolve({ ok: true, json: async () => value });
    }
    if (failures.includes(key)) return Promise.reject(new Error(`${key} failed`));
    if (pending.includes(key)) return new Promise((resolve, reject) => { gates[key] = { resolve, reject }; });
    return Promise.resolve({ ok: true, json: async () => defaults[key] });
  };
  const context = {
    fetch, AbortController, setTimeout, clearTimeout, Date,
    document: {
      currentScript: null,
      getElementById: element,
      dispatchEvent(event) { events.push(event.type); },
      createElement() { return { className: "", textContent: "" }; },
    },
    CustomEvent: function CustomEvent(type) { this.type = type; },
    fmtTime: (value) => value,
  };
  vm.createContext(context);
  vm.runInContext(loaderSource, context, { filename: "assets/loader.js" });
  vm.runInContext(selectionSource, context, { filename: "assets/selection.js" });
  vm.runInContext(app, context, { filename: "assets/app.js" });
  const state = vm.runInContext("state", context);
  context.fetchJson = vm.runInContext("AiRadarLoader.createLoader({ state }).fetchJson", context);
  context.fmtTime = (value) => value;
  context.renderList = () => { observed.list += 1; };
  context.renderBriefPicks = (options) => { observed.brief.push(options || {}); };
  context.renderStaleBanner = () => { observed.stale += 1; };
  context.renderSourceHealth = (error) => { observed.health.push(error || ""); };
  context.renderCoverageStrip = (error) => { observed.coverage.push(error || ""); };
  context.setStats = () => { observed.stats.push({ status: state.sourceStatus, error: state.sourceStatusError }); };
  for (const name of ["renderMarketSignals", "renderLlmRadar", "renderSectionTabs", "renderModeSwitch", "renderListSortTools", "renderSiteFilters"]) context[name] = () => {};
  return { context, state, observed, events, calls, gates, updatedAtEl, newsListEl, modeAllBtnEl,
    release(key, payload = defaults[key]) { gates[key].resolve({ ok: true, json: async () => payload }); },
  };
}

async function main() {
  const scenario = process.argv[2];
  if (scenario === "section-filters") {
    const env = environment();
    const items = [
      { id: "qwen", title: "Qwen model released", site_id: "official_ai", source: "OpenAI", url: "https://openai.com/a", ai_score: 0.99 },
      { id: "media", title: "Qwen model reviewed", site_id: "curated_media", source: "Reuters", url: "https://reuters.com/a", ai_score: 0.99 },
      { id: "funding", title: "Company IPO", site_id: "official_ai", source: "OpenAI", url: "https://openai.com/b", ai_score: 0.99 },
    ];
    env.state.itemsAi = items;
    env.state.itemsAll = [...items, { id: "raw", title: "Qwen model", site_id: "official_ai", source: "OpenAI", ai_score: 0.99 }];
    env.state.itemsAllRaw = env.state.itemsAll;
    env.state.allDataLoaded = true;
    env.state.modelReleases24h = [];
    env.state.activeSection = "models";
    env.state.query = "qwen";
    env.state.siteFilter = "original";
    env.state.mode = "ai";
    assert.deepEqual(Array.from(env.context.getFilteredItems(), (i) => i.id), ["qwen"]);
    env.state.mode = "all";
    assert.deepEqual(Array.from(env.context.getFilteredItems(), (i) => i.id), ["qwen", "raw"]);
    env.state.mode = "ai";
    env.state.siteFilter = "";
    assert.deepEqual(Array.from(env.context.getFilteredItems(), (i) => i.id), ["qwen", "media"]);
    env.state.query = "absent";
    assert.equal(env.context.getFilteredItems().length, 0);
  } else if (scenario === "aux-pending") {
    const key = process.argv[3];
    const env = environment({ pending: [key] });
    const started = env.context.init();
    await flush();
    await flush();
    assert.equal(env.observed.list, 1, `${key} blocked the main list`);
    assert.equal(env.updatedAtEl.textContent, news.generated_at);
    assert.equal(env.observed.stale, 1);
    assert.deepEqual(env.events, ["aiRadar:ready"]);
    env.state.query = "user search";
    env.state.mode = key.includes("stories") ? "all" : "ai";
    env.release(key);
    await started;
    await flush();
    assert.equal(env.observed.list, 1, "late auxiliary data reset the list");
    assert.equal(env.state.query, "user search");
    assert.equal(env.state.mode, key.includes("stories") ? "all" : "ai");
    assert.equal(env.events.filter((event) => event === "aiRadar:ready").length, 1);
    if (key.includes("brief") || key.includes("stories")) {
      assert.ok(env.observed.brief.length >= 2);
      assert.ok(env.observed.brief.slice(1).every((options) => options.animate === false));
    }
    if (key.includes("source-status")) {
      assert.ok(env.observed.stats.some((snapshot) => snapshot.status?.sites), "source arrival did not refresh header stats");
    }
  } else if (scenario === "aux-reject") {
    const key = process.argv[3];
    const env = environment({ failures: [key] });
    await env.context.init();
    await flush();
    assert.equal(env.observed.list, 1);
    assert.equal(env.updatedAtEl.textContent, news.generated_at);
    assert.equal(env.events.filter((event) => event === "aiRadar:ready").length, 1);
    if (key.includes("source-status")) {
      assert.ok(env.observed.health.some(Boolean));
      assert.match(env.state.sourceStatusError || "", /source-status\.json/);
      assert.ok(env.observed.stats.some((snapshot) => snapshot.error), "source failure did not refresh header stats");
    }
  } else if (scenario === "main-fail") {
    const env = environment({ failures: ["./data/latest-24h.json"], pending: ["./data/stories-merged.json"] });
    const started = env.context.init();
    await flush();
    await flush();
    assert.equal(env.updatedAtEl.textContent, "新聞資料載入失敗");
    assert.match(env.newsListEl.innerHTML, /latest-24h\.json/);
    assert.equal(env.observed.list, 0);
    assert.deepEqual(env.events, ["aiRadar:ready"]);
    if (env.gates["./data/stories-merged.json"]) env.release("./data/stories-merged.json");
    await started;
  } else if (scenario === "all-race") {
    const key = "./data/latest-24h-all.json";
    const env = environment({ pending: [key] });
    const started = env.modeAllBtnEl.click();
    await flush();
    env.state.mode = "selected";
    env.release(key);
    await started;
    assert.equal(env.observed.list, 0, "late all-mode response rerendered a newer user choice");
    assert.equal(env.state.mode, "selected");
  } else if (scenario === "all-error-race") {
    const key = "./data/latest-24h-all.json";
    const env = environment({ pending: [key] });
    const started = env.modeAllBtnEl.click();
    await flush();
    env.state.mode = "selected";
    env.gates[key].reject(new Error("late all-mode failure"));
    await started;
    assert.equal(env.observed.list, 0);
    assert.equal(env.state.mode, "selected");
    assert.doesNotMatch(env.newsListEl.innerHTML, /late all-mode failure/);
  } else if (scenario === "all-retry") {
    const key = "./data/latest-24h-all.json";
    const env = environment({ sequence: { [key]: [new Error("first failed"), defaults[key]] } });
    env.state.briefExpanded = true;
    env.state.siteGroupsExpanded = true;
    await env.modeAllBtnEl.click();
    assert.equal(env.state.allDataPromise, null);
    await env.modeAllBtnEl.click();
    assert.equal(env.state.allDataLoaded, true);
    assert.equal(env.observed.list, 1);
    assert.equal(env.state.briefExpanded, true);
    assert.equal(env.state.siteGroupsExpanded, true);
  } else if (scenario === "timeout-abort") {
    const key = "./data/latest-24h.json";
    const env = environment({ pending: [key] });
    await assert.rejects(env.context.fetchJson(key, "latest-24h.json", 10), /逾時/);
    assert.equal(env.calls[0].signal.aborted, true);
  } else if (scenario === "timeout-json") {
    const env = environment();
    let signal;
    env.context.fetch = (_url, options) => {
      signal = options.signal;
      return Promise.resolve({ ok: true, json: () => new Promise(() => {}) });
    };
    await assert.rejects(env.context.fetchJson("./data/latest-24h.json", "latest-24h.json", 10), /逾時/);
    assert.equal(signal.aborted, true);
  } else if (scenario === "stories-url") {
    const key = "./data/alternate-stories.json";
    const env = environment({ sequence: {
      "./data/latest-24h.json": [{ ...news, stories_data_url: "data/alternate-stories.json" }],
      [key]: [{ stories: [] }],
    } });
    await env.context.init();
    await flush();
    assert.equal(env.calls.filter((call) => call.key === key).length, 1);
    assert.equal(env.calls.filter((call) => call.key === "./data/stories-merged.json").length, 0);
  } else {
    throw new Error(`unknown scenario: ${scenario}`);
  }
  console.log(JSON.stringify({ scenario, ok: true }));
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
