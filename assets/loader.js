// Shipped as a classic browser script; directly require()able in Node tests.
// No DOM or app imports: the caller owns state and rendering.
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.AiRadarLoader = api;
})(globalThis, function () {
  "use strict";

  const AUXILIARY_FETCH_TIMEOUT_MS = 8000;
  const PRIMARY_FETCH_TIMEOUT_MS = 12000;

  function createLoader({
    state,
    fetchImpl = (...args) => globalThis.fetch(...args),
    now = () => Date.now(),
    setTimeoutFn = (...args) => globalThis.setTimeout(...args),
    clearTimeoutFn = (id) => globalThis.clearTimeout(id),
    AbortControllerClass = globalThis.AbortController,
  }) {
    async function fetchJson(path, label, timeoutMs = AUXILIARY_FETCH_TIMEOUT_MS) {
      const controller = new AbortControllerClass();
      let timeoutId;
      const timeout = new Promise((_, reject) => {
        timeoutId = setTimeoutFn(() => {
          reject(new Error(`載入 ${label} 逾時`));
          controller.abort();
        }, timeoutMs);
      });
      try {
        return await Promise.race([
          fetchImpl(`${path}?t=${now()}`, { signal: controller.signal }).then((res) => {
            if (!res.ok) throw new Error(`載入 ${label} 失敗: ${res.status}`);
            return res.json();
          }),
          timeout,
        ]);
      } catch (error) {
        if (error?.message === `載入 ${label} 逾時`) throw error;
        throw new Error(`暫時無法載入${label}，請稍後重試。`);
      } finally {
        clearTimeoutFn(timeoutId);
      }
    }

    function loadMarketSignalsData() {
      return fetchJson("./data/market-signals.json", "價格變更");
    }

    function loadLlmRadarData() {
      return fetchJson("./data/llm-radar.json", "LLM 發布雷達");
    }

    function loadNewsData() {
      return fetchJson("./data/latest-24h.json", "AI 新聞", PRIMARY_FETCH_TIMEOUT_MS);
    }

    async function loadAllModeData() {
      if (state.allDataLoaded) return;
      if (!state.allDataPromise) {
        state.allDataPromise = fetchJson(`./${state.allDataUrl}`, "全部收錄內容", PRIMARY_FETCH_TIMEOUT_MS)
          .then((payload) => {
            state.itemsAllRaw = payload.items_all_raw || payload.items_all || state.itemsAi;
            state.itemsAll = payload.items_all || state.itemsAi;
            state.totalRaw = payload.total_items_raw || state.itemsAllRaw.length;
            state.totalAllMode = payload.total_items_all_mode || state.itemsAll.length;
            state.allGovernanceMeta = payload.publisher_governance_meta || null;
            state.allDataLoaded = true;
          })
          .catch((err) => {
            state.allDataPromise = null;
            throw err;
          });
      }
      return state.allDataPromise;
    }

    function loadSourceStatusData() {
      return fetchJson("./data/source-status.json", "來源狀態");
    }

    function loadDailyBriefData() {
      return fetchJson("./data/daily-brief.json", "重點訊號");
    }

    function loadStoriesData() {
      return fetchJson(`./${state.storiesDataUrl}`, "重點訊號整理資料");
    }

    return {
      fetchJson, loadNewsData, loadAllModeData, loadSourceStatusData,
      loadDailyBriefData, loadStoriesData, loadMarketSignalsData, loadLlmRadarData,
    };
  }

  return { createLoader, AUXILIARY_FETCH_TIMEOUT_MS, PRIMARY_FETCH_TIMEOUT_MS };
});
