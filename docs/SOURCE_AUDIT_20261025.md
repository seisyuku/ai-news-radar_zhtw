# 2026-10-25 專案與消息來源盤點

## 範圍與資料時間

以 GitHub `master` 上同代生成的 `data/source-status.json`、`data/latest-24h.json`、`data/latest-24h-all.json`、`data/daily-brief.json`、`data/stories-merged.json` 為現況基準，生成時間均為 **2026-10-25 03:57:57 UTC／臺北 11:57:57**。另從本機 Git 既有 `source-status.json` 歷史抽取 10/22～10/24 約每兩小時一筆、共 36 筆快照，僅作近期穩定性旁證。這不是重啟已取消的七日來源觀察或回放，也不改全站 24 小時讀者規則。

盤點包含已接入來源、讀者顯示身分、准入政策、公開輸出、現存任務與本機變更。沒有新增來源、抓取或排程，沒有改來源等級、全域評分、選稿、計票鍵、官方資料快照或私人日報退役狀態。

## 現況

| 面向 | 盤點結果 |
| --- | --- |
| 新聞入口 | 41 個正式新聞入口：33 個群組子來源與 8 個獨立來源；另有橘鴉控制對照、私人 OPML 池及價格／兩個 Canary，不能混作新增新聞入口。 |
| 最新刷新健康 | `source-status` 的 16 個頂層站點均成功，沒有失敗、降級或持續故障；33 個群組子來源也均成功。子來源 `item_count: 0` 表示當輪無合格新稿，不等於抓取失敗。 |
| 近期旁證 | 36 筆既有快照中，大部分來源 36／36 成功；TechNews 34／36、若干 Google News 橋接 35／36，均未出現持續故障。此樣本早於 CyberQ／AlphaLab 正式接入，不能證明兩站長期穩定。 |
| 公開資料一致性 | 五份資料的 `generated_at` 一致；公開新聞及 brief 的 `window_hours` 均為 24，發布者治理為 `ready`。當輪 48 篇一般全量、43 篇 AI 列表、46 個合併故事、3 則 daily 重點。 |
| 准入分布 | 全量 48 篇中，29 篇來自 `limited` 範圍、19 篇為 `unreviewed`；這是文章數，不是來源數。3 則 daily 重點均來自既有 `limited` 媒體。 |
| 來源顯示身分 | 全量 48 篇有 37 篇 `identified`、4 篇 `reported`、7 篇 `unknown`。`reported` 均是 Google News RSS 提供的第三方名稱，不等於本站認證或品質准入。 |

公開 24 小時 AI 列表中 TechNews 9／43、36Kr 5／43、The Decoder 5／43；這是單輪分布，不能單獨作為升降級依據。36Kr 本來就是未審來源；DeepSeek／xAI 主題查詢返回的是不同第三方媒體，也保持未審。`openai_skills`、`thinking_machines_lab`、MCP Blog、ARC Prize 在近期抽樣中常見零件數，但抓取健康；稀疏公告來源不因零新稿自動降級。

逐項看當輪 43 篇 AI 標題，雜訊集中在**個別稿型**而非可證的整站故障：36Kr 的提示詞評論、xAI 查詢返回的 Tesla 配件商稿、Reuters 的音樂觀點稿，都需要逐篇判斷新聞價值。三則 daily 重點中，The Decoder 的新語音模型較符合具體事件；TechCrunch 的「AI graveyard」持續更新清單和 CNBC 的投資組合評論，從標題看不如具體新事件明確，列為下一次選稿品質複核的候選案例。這裡只做標題層級初判，未逐篇核對全文，不能宣稱它們違反現行規則或據此降整站等級。

## 升降級裁決

**本次不調整任何來源等級或准入權限。** 已核對的失敗沒有形成持續故障；24 小時篇數、單篇內容與短期健康不足以支持整站升降。CyberQ／AlphaLab 仍為 `unreviewed`、watchlist rank 6，只可進一般池並逐篇競爭下方精選；不取得上方重點、daily 主文、雷達或獨立佐證票。Google News 主題查詢與私人 OPML 未審來源亦不因顯示名稱改善而升級。

若將來要重審來源，應分開看來源可靠性、AI 產業消息的有效比例、同事件重複量、獨有的重要消息、標題／摘要與原文的一致性；從現有快照做明確抽樣即可，不自動恢復舊的七日觀察工作流。單輪 `item_count` 是抓取／預篩數，不能當有效新聞數或品質分數。

## 媒體名稱缺口與本機修正

最新全量的 7 則 `unknown`：AlphaLab 2 則、CyberQ 1 則，另外 4 則來自私人 OPML（InfoQ CN 3、Simon Willison 1）。前兩站的公開 RSS 入口、文章 host 與政策 scope 能相互核對，但舊前端仍一律顯示「來源待辨識」；OPML 的私有訂閱標籤則不能直接當作已核實的發布者身分。Google News 查詢若缺少可信 RSS 來源資訊，仍可能真正無法判明媒體。

本機前端現改為：`unknown` 的**已配置公開 RSS** 同時符合入口 `source_id`、未審 scope、入口名稱和文章／feed 同 host 時，顯示該入口名稱；其他 `unknown` 且有經後端驗證的文章 host 時，僅顯示 host；Google News 不明發布者與 `conflict` 繼續顯示待辨識／衝突。這只改善讀者標示，保留原 `publisher.status`、來源等級、用途權限及佐證計票，不將私人 OPML 標籤升格為媒體身分。既有公開快照本身不變；前端發布後才會見到新標示。

本機以 `node --check assets/app.js`、相關前端來源／政策／徽章與資產版本測試 28 項及舊本機快照實際欄位驗證通過：CyberQ／AlphaLab 顯示入口名稱，InfoQ／Simon Willison 顯示網域，未審層級仍為 `other`。`index.html` 六個資產共同版本已升至 `20261025-source-name`；尚未提交或推送，正式網站仍是原版本。

## 其他專案狀態

T03 摘要回顧已結案，維持 Groq 每輪六則上限與 prompt。任務台帳尚留 T01、T02、T04、T05、T06；本次盤點沒有把它們啟動。私人日報自動化與七日來源觀察／回放維持取消，公開刷新、Pages、daily-brief 與 24 小時窗口照常。先前尚未提交的文件改動仍在本機工作樹，本次沒有將它們重置或混作已發布成果。
