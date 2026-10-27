# T04 Gemini 摘要備援候選（2026-10-25）

## 現行裁決

候選程式已接入，但排程固定 `GEMINI_SUMMARY_ENABLED=0`，因此沒有 Gemini
摘要 production call。Groq 仍是唯一正式摘要 provider；Gemini 讀者翻譯是獨立路徑。
本案沒有送出真實新聞到 Gemini；合成案例已透過 GitHub Actions Secrets
完成三個成功分離時段實測；10/26 晚間逾時／503 失敗也保留為限制證據。
沒有建立、讀取明文或更改任何 secret；兩個摘要測試用
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
- 獨立 `.github/workflows/t04-synthetic-eval.yml` 現在僅接受明確
  `workflow_dispatch`；已於 10/26 晚間移除分支 push 觸發，避免其他功能
  提交意外消耗測試額度。使用 Secrets 執行合成案例，不讀公開快照或真實 feed。
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

同一時段 16:54～16:57 的[流程複驗 attempt 1](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40178497098/attempts/1)
以修正後程式成功結束：Gemini 診斷通過、10/10 合格案例全綠；Groq 本次也
10/10，全程沒有 429、5xx。這是同時段的 runner 修正驗證，不冒充第二個
分離時段；首次 Groq 9/10 仍保留為模型輸出變動的比較證據。

## 第二個實測時段：2026-10-26 午後補跑

原訂臺北 09:00 的本地聊天自動化沒有產生執行回合；截至午後檢查，合成專用
workflow 也仍只有 10 月 25 日的兩個 run，各只執行一次。未觀察到今天早上
09:00 的模型測試、輸出或通知；目前無法從可讀紀錄確定本地排程漏觸發的原因。

依既有合成案例授權，於臺北 **13:01:14～13:04:26** 補跑
[Actions run 40178497098 的 attempt 2](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40178497098/attempts/2)
（[job 121406690403](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40178497098/job/121406690403)）。
Gemini diagnostic 通過，涵蓋 model discovery、plain 及 structured JSON；
11 例中 10 例生成並全數通過，title-only 依規則標記 `insufficient_context`。
Groq 同案也是 10/10，title-only 同樣跳過。安全日誌的案例錯誤碼均為空，
沒有 429、5xx、模型查找或結構化輸出錯誤。本次與第一時段相隔約 20 小時，
計為第二個分離時段；**不得記為 09:00 準時執行**。

## 第三時段的執行與通知稽核

2026-10-26 早上 09:00 的 Codex 本地排程未產生執行回合；使用者確認當時
電腦開機且 ChatGPT App 在前景。沒有足夠證據定位本地排程漏觸發原因，
不能把它歸因於電腦休眠或 App 未啟動。第三時段仍由 Codex 本地排程於
2026-10-27 臺北 09:00 啟動，09:30 為補位；同日只完成一次合成評估。

合成評估 workflow 現在把憑證檢查、Gemini 診斷、冷卻、語料載入、Gemini
案例、Groq 比較和終局狀態寫成不含模型原文／密鑰的 `t04-stage-events` artifact。
Actions 自身的 checkout、Python 設定、依賴安裝與評估步驟也有逐步結論。
獨立 `notify` job 在評估成功或失敗後執行，寄出結論、步驟狀態、階段摘要與
Actions 連結，並把 SMTP 接受結果保存在 `t04-email-receipt` artifact。
沿用先前已驗證的 `TW_SOURCE_EMAIL_SETTINGS`，不在倉庫放入收件地址或密碼。

預設分支另須保留同名 `t04-synthetic-eval.yml` 的手動 dispatch 註冊檔；
GitHub 只對預設分支存在的 workflow 接受 `workflow_dispatch`，實際評估仍
指定 T04 測試分支並使用該分支版本。另設預設分支上的
`t04-delivery-watchdog.yml`，於 10:17、10:47、11:17、
11:47（臺北時間）獨立檢查 T04 workflow_dispatch run 與 SMTP 接受收據。
若沒有 run、沒有可驗證的通知收據，或查核 API 失敗，就寄送逾期告警。
後續 tick 先檢查同日較早的成功 watchdog run，以免重複寄送。
**此排程只有在 watchdog workflow 與程式進入 GitHub 預設分支後才生效**；
T04 測試分支上的檔案本身不會註冊 GitHub schedule。

2026-10-26 已將 watchdog、預設分支 dispatch 註冊檔與站外心跳補位 job
推送至 `master`（`d9e4de3`、`36229b5`）。
[通知通道測試 run 40273783160](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40273783160)
執行成功，SMTP `DATA` 回應 250、狀態 `provider_accepted`；這只驗證
發信端接受。維護者隨後確認已在收件匣收到這封測試信。
[無 provider 派送測試 run 40273918526](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40273918526)
確認指定 T04 分支時執行該分支的 `probe` job，而摘要評估及通知 job 均被
略過；沒有消耗 Gemini／Groq 呼叫。第三時段的完整評估、階段 artifact 與
結果郵件已於 2026-10-27 驗證，實際紀錄見下節。
部署後第一個自然站外心跳
[run 40275006768](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40275006768)
於 2026-10-26 05:35 UTC 執行成功：`freshness-check` 中的 T04 步驟
正確判定尚未到截止時間並略過寄信；原有新聞更新 job 也成功。

通知保證的邊界：Actions 排程、runner、GitHub API、SMTP 與收件端都可能
故障；系統可記錄 SMTP 伺服器接受與否，無法保證郵件一定出現在收件匣。
GitHub schedule 也可能漏掉所有四個 watchdog tick。既有 cron-job.org
每 30 分鐘從 GitHub 外部觸發 `update-news.yml` 的 `source=heartbeat`；
在測試日 10:17～16:00 臺北時間，既有 `freshness-check` job 的追加步驟會
補 dispatch T04 watchdog，
不執行額外 provider 測試。這仍無法消除 GitHub 執行服務或 SMTP 同時故障，
因此不能宣稱收件匣投遞絕對保證。

## 2026-10-26 晚間意外觸發與失敗調查

臺北 21:05 的 `eca8881` 是 D+ 補充情報排序提交，原 `push` 觸發規則
卻同時啟動 [T04 run 40327620273](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40327620273)。
該次不是 10/27 早上排程：Gemini diagnostic 通過，但 `qwen-release`、
`security-incident`、`reported-acquisition` 三個案例為 `provider_error`，
其他七例生成通過，title-only 跳過；Groq 10/10。安全日誌當時只保留
HTTP status（這三例都是 null），捨棄了例外類型，無法回溯唯一定位根因。
失敗結論、階段 artifact 與結果郵件均正常完成，不得把此 run 記為驗收成功。

已移除 push 觸發，並在評估中增加逐案例開始／完成／失敗時間、實際呼叫
耗時、HTTP status 與列舉的安全例外類型。Gemini diagnostic 的子步驟也
保留同樣分類；郵件可直接顯示出錯案例與耗時，不記原始 exception message、
模型原文或憑證。相關測試 26 項及 actionlint 通過。

受控 [run 40337526478](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40337526478)
於臺北 22:12 啟動，在 `plain_generation` 即以
`transient_or_transport_failure` 中止，未進入摘要案例；通知成功。
這支持當晚生成服務／傳輸不穩的判斷，不是額度耗盡的證據。

保留子步驟分類後的 [run 40338077731](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40338077731)
於 22:16～22:23 再現具體故障：Gemini diagnostic 通過，`qwen-release`、
`commercial-adoption`、`conditional-service-end` 皆為 `ReadTimeout`，
實際耗時分別 30.040／30.032／30.031 秒；其他七例生成通過，耗時
13.351～23.776 秒，Groq 10/10。沒有收到 429 或 5xx。與原失敗案例
不完全相同，顯示現行 30 秒讀取上限會截斷部分慢請求；這項重現證據不能
回補原三例已被捨棄的 exception type。

已將 Gemini 候選的單次 timeout 獨立設為 60 秒，T04 diagnostic 同步採用；
Groq 保持 30 秒。摘要內容驗證、呼叫節奏及案例數維持，沒有加入自動重試。
60 秒設定會進入安全報告與郵件，避免新舊測試條件混淆。此變更仍屬停用中
的 Gemini 候選，不啟用正式摘要備援。變更後完整套件 2,363 項通過。

60 秒設定的 [run 40339463429](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40339463429)
於臺北 22:25:07～22:33:07 完成，仍判 failure：Gemini diagnostic 通過；
七例生成通過、`grok-release` 與 `conditional-service-end` 分別於
60.005／60.011 秒 `ReadTimeout`，`commercial-adoption` 收到 HTTP 503。
`untrusted-injection`、`unreleased-provider-claim` 分別花 36.205／32.123 秒
才成功，顯示 60 秒設定能容納部分慢請求，但沒有解決當晚的全部服務／傳輸
異常。Groq 10/10，title-only 跳過；沒有觀察到 429。結果郵件收到 SMTP
250 接受回應，階段與收據 artifacts 均保存。

Google 官方將 [503 分類為服務暫時不可用／容量不足](https://ai.google.dev/gemini-api/docs/generate-content/api-errors)。
本次回應可確認 Gemini endpoint 的服務不可用，不能據此宣稱全球事故。
原始及受控失敗都保留，不計入成功時段；維持正式摘要備援停用，依既定
10/27 時段再測，不在當晚繼續重跑或擴大等待上限。

## 第三個成功分離時段：2026-10-27 09:00 排程實測

本地 heartbeat 於臺北 08:58:50 喚醒，先核對當日 08:45 後沒有既存
workflow_dispatch run，等待 09:00 後才派送。實際
[run 40429943469](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40429943469)
於 **01:00:24 UTC／09:00:24 臺北** 建立，使用 T04 分支 `7736ceab745c`；
屬原訂 09:00 時段執行，沒有重跑舊 run 或同日重複呼叫。

- [synthetic-only job 121944895587](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40429943469/job/121944895587)：
  01:00:28～01:03:41 UTC（09:00:28～09:03:41 臺北），成功。
  腳本實際評估 01:00:47.137～01:03:37.627 UTC。
- Gemini configuration、model discovery、plain generation、structured JSON
  診斷均通過。11 例中 10 個可生成案例全數通過，title-only 標記
  `insufficient_context`；Groq 同案也是 10/10，title-only 同樣跳過。
- Gemini timeout 設定為 60 秒，實際 10 次生成耗時 **0.501～2.429 秒**；
  沒有逾時、429、5xx、模型查找或結構化輸出錯誤。
- [notify job 121946020246](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/40429943469/job/121946020246)：
  01:03:43～01:03:57 UTC（09:03:43～09:03:57 臺北），成功。
  01:03:54.429 UTC 的 SMTP `DATA` 回應為 250、`provider_accepted`。
  已逐一核對 `t04-stage-events` 與 `t04-email-receipt`，未宣稱收件匣送達。

這是第三個成功的分離時段；當晚失敗仍屬有效證據，不能由本次成功推論
Gemini 已具長期穩定性。測試全程僅使用既有合成案例，正式摘要備援仍停用。
本次一次性排程任務已完成，`t04-gemini` 本地自動化已移除，不再執行
09:30 補位。預設分支的獨立逾期查核仍可按原定時間核對本次通知收據。

## 正式 gate 狀態

1. Gemini 的提示注入及全套 11 例已在第一時段通過；Groq 同案已比較並
   保留一項未過結果。不可把單時段當作長窗穩定性結論。
2. 10/25、10/26 午後、10/27 09:00 三個成功分離時段均已完成 Gemini
   diagnostic/eval；各次均記錄 429、5xx、model discovery 與 structured
   output。10/26 晚間的逾時／503 失敗不計入成功時段，也不被刪除；
   後續正式接線裁決仍須考慮這項穩定性限制，不能把三次成功當成連續穩定證明。
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
[Gemini 診斷流程](guides/gemini-diagnostic-flow.md)；本案僅沿用上列 T04
合成實測與通知查核安排。
