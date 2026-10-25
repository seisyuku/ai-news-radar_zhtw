# T04 Gemini 摘要備援候選（2026-10-25）

## 現行裁決

候選程式已接入，但排程固定 `GEMINI_SUMMARY_ENABLED=0`，因此沒有 Gemini
摘要 production call。Groq 仍是唯一正式摘要 provider；Gemini 讀者翻譯是獨立路徑。
本案沒有送出真實新聞到 Gemini；合成案例已透過 GitHub Actions Secrets
完成第一時段實測。沒有建立、讀取明文或更改任何 secret；兩個摘要測試用
key 都不在本機執行環境。

維護者已選擇以 Gemini 免費層進行 **11 個合成案例的實測**，並接受該層
資料可能用於改善 Google 產品的政策。維護者將另行配置 Gemini／Groq 測試
憑證；兩把憑證已配置在 GitHub Actions Secrets，本機仍未取得。維護者提供的 AI Studio 額度截圖文字（查閱
2026-10-25，近一日 peak usage）顯示 Gemini 3.5 Flash Lite 為 15 RPM、
250K TPM、500 RPD；實際呼叫前仍須注意同 project 的翻譯流量與額度變動。
這項接受只涵蓋合成案例，不是把真實 publisher feed 送往 Gemini
或啟用正式備援的授權。

## 已完成的離線工作

- 評估用 Gemini generator 與正式候選共用同一份程式及摘要 prompt，避免驗收與
  排程行為分歧。合成語料從 7 例增至 11 例，加入價格作用範圍、未發布廠商
  宣稱、附條件的停用及未證實交易。
- 提示注入案例改以明確語意檢查：摘要須指出提示注入、惡意指令等風險，且
  不得重現指令或疑似密鑰；不再硬性要求逐字出現「不可信」。離線斷言通過，
  仍須實際 provider 複測全綠才滿足 gate 1。
- 只在 Groq `requests.RequestException` 後考慮備援。無來源摘要、Groq 成功、
  本地驗證拒絕及缺憑證均不轉送 Gemini。兩 provider 失敗時保留新聞、略過
  AI 摘要。
- 使用獨立 `GEMINI_SUMMARY_API_KEY`，不借用翻譯憑證；Gemini 快取鍵包含
  provider 與 model，既有 Groq 快取鍵保持相容。候選每輪最多三次 Gemini
  請求，單次輸入沿用既有有界來源摘要、輸出上限 180 tokens。公開狀態只記
  次數與安全分類，不記請求內容或密鑰。
- 獨立 `.github/workflows/t04-synthetic-eval.yml` 僅由 T04 分支推送或人工
  dispatch 啟動；使用 Secrets 執行合成案例，不讀公開快照或真實 feed。
  `scripts/t04_live_eval.py` 只輸出診斷碼、案例狀態與錯誤類別，不輸出模型
  原文。Gemini 診斷後冷卻 60 秒，合成案例之間至少間隔 10 秒，以降低與
  同 project 翻譯流量撞上 15 RPM 上限的風險。這不是新的週期排程。
- 聚焦測試 32 項通過；完整套件在符合舊 digest 測試路徑規則的
  `/Users/lordmi/Downloads/` 臨時目錄重跑，2,330 項全通過。

## 第一個實測時段

2026-10-25 臺北 16:46～16:49，[Actions run 40177937616](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40177937616)
以 `codex/t04-gemini-summary` 的合成專用 workflow 執行：Gemini model
discovery、plain 與 structured JSON 診斷均通過；11 例中 10 例生成並全數
通過，title-only 依規則跳過。沒有 429、5xx 或模型／格式失效。
Groq 同案 9 例通過、1 例（`security-incident`）漏一項 fixture 必要詞，
title-only 跳過。原 wrapper 誤將 Groq 比較失敗視為 Gemini 備援 gate
失敗，故該 run 顯示 failure；此判定已修正並補測，Groq 缺漏仍記錄，
不被改寫為通過。本時段的 Gemini 證據有效，但還需要至少兩個分離時段。

## 正式 gate 狀態

1. Gemini 的提示注入及全套 11 例已在第一時段通過；Groq 同案已比較並
   保留一項未過結果。不可把單時段當作長窗穩定性結論。
2. 在至少三個分離時段完成 Gemini diagnostic/eval；目前僅有一個。後續
   記錄 429、5xx、model discovery 與 structured output 的結果，不得以
   同時段連跑三次替代。
3. 正式啟用前重新核對實際專案的 active rate limits、使用 tier 與資料使用
   條款，另行明確接受真實新聞備援的用途。當前官方頁面列出標準付費層每百萬 input tokens USD
   0.30、output tokens USD 2.50；免費層內容可用於改善 Google 產品，標準
   付費層則不會。上限以 project 而非 API key 計算。這些不是永久設定。
4. 上述條件全數通過後才可另行將 workflow 的固定停用值改為啟用，並依
   `OPERATIONS.md` 驗正式刷新、公開狀態與雙 provider 失敗行為。本次未啟用。

官方現況（查閱 2026-10-25）：
[模型](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)、
[價格與資料使用](https://ai.google.dev/gemini-api/docs/pricing)、
[速率限制](https://ai.google.dev/gemini-api/docs/rate-limits)。

合成複測指令及不保存密鑰規則見
[Gemini 診斷流程](guides/gemini-diagnostic-flow.md)；本案不建立新排程或提醒。
