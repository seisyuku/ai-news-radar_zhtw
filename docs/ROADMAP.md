# AI News Radar Pulse Roadmap

本文件只記錄尚未完成或仍需追蹤的方向。已完成的設計事實、來源裁決與
歷史證據以 [`HANDOVER.md`](HANDOVER.md) 為準；操作程序以
[`OPERATIONS.md`](OPERATIONS.md) 為準。

## 現行產品邊界

- 公開預設是臺灣繁體中文的 AI 產業商業事件儀表板。
- 重點訊號固定採六類事件：財報營收、市佔格局、資安漏洞、價格方案、
  評測基準、模型發布。
- 一般列表保留較廣的 AI 產業資訊，但不擴張成開發教學、prompt 技巧或
  社群討論聚合器。
- 來源治理採「寧缺勿濫」；不為填滿版位而導入低訊噪比來源。

## P0：排程與來源可觀測性

- 持續用 `source-status.json` 與前端更新時間監看排程健康。
- 對可恢復的單一來源失敗保留明確狀態與診斷；不可讓來源靜默消失。
- 外部 heartbeat 使用的 fine-grained PAT 約於 **2026-10-17** 到期，
  到期前依 [`OPERATIONS.md`](OPERATIONS.md) 完成續期與驗證。

## P1：一般列表六類事件軸

- 在一般列表渲染現有六類事件徽章。
- 提供六類事件篩選軸，沿用現行事件判定結果，不另造第七類。
- 保持預設畫面簡單；篩選器不可遮蔽來源、時間與原文連結。
- 變更 `assets/` 時同步遞增 `index.html` 的 `?v=` 與
  `tests/asset_manifest.json`。

## P1：Model Release Radar

- v1 已加入低權重模型查漏與分析觀察源：LLM Stats `latestModels`、
  LLM Rumors RSS、RuntimeWire 聚焦 RSS。
- 補齊模型版本識別，避免 Qwen、GLM、Kimi 等不同版本錯誤聚合。
- 已統一「模型」分頁的 atomic 發布資料為 24 小時窗口，保留真實 release
  date，不把舊發布偽裝成新消息。
- 已完成：首頁事件式「LLM 發布雷達」，在 24 小時內出現新模型時才顯示；
  結構化價格／免費額度異動集中在市場區，兩者皆不改寫全域排序。
- 待辦：把 benchmark、價格/API、部署、商業採用與安全分析掛到同一
  canonical model key，形成完整七日模型生命週期。
- 待辦：完成至少 14 日來源健康與誤報回放後，再決定是否增加
  `model_significance`；未完成回放前不修改全域評分公式。

## P1：重點新聞內容摘要

- 已完成：RSS/Atom 發布者摘要清理與保留、Groq
  `qwen/qwen3.8-27b` 選用整合、內容雜湊快取、每輪呼叫上限與安全失敗。
- 已完成：前端以「AI 新聞摘要」取代分類徽章映射的固定「為什麼重要」
  字串；無可靠內容時直接省略，不製造模板式洞見。
- 待辦：累積實際排程樣本後觀察摘要可用率、失敗率、快取命中率與模型
  新聞細節保留情況，再決定是否調整 6 則上限或 prompt；不因此修改
  全域新聞評分公式。
- 已裁決（2026-09-06）：取消 Gemini 備選與多 provider fallback 路線；
  AI 摘要只使用 Groq `qwen/qwen3.8-27b`。Groq 失效時省略摘要，不新增
  替代 provider 的 acceptance 或接線待辦。

## P1：Market Sensor 與 usage-policy 速報

- 已完成：價格 JSON snapshot/diff、免費額度結構化 diff、兩個公開
  usage-monitor commit Atom Canary，以及獨立的市場區與速報區。
- 現行優先權拆為兩軸：長期影響 `價格 > 免費額度 > usage policy`；
  時效 `usage policy >> 免費額度 > 價格`。速報排序不改寫全域新聞評分。
- 待觀察：累積至少 14 天真實候選後，統計 Canary precision、官方確認
  延遲與漏報，再決定是否加入第三個 repo、release feed 或少數官方頁面。
- Promotion scraper、issues／PR ingestion 與 changedetection.io 仍延後；
  沒有實際漏報證據前不擴張。

## P2：成長型資料治理

- `title-zh-cache.json`：以新的明確唯讀任務收集可重現的多時點量測與適用的
  執行環境／儲存限制證據；不自動持續監測，也不啟動清理。
- 量測證據齊備後，再開一次零寫入決策訪談，定義容量、觀察窗與成長率的數值
  門檻，並在觀察開始前登記這些定義；目前尚無 prune 機制。
- `archive.json` 已回到 GitHub 50MB 軟上限以下，維持觀察即可；只有在
  積壓退場後仍持續成長時才重新升級為治理工作。
- 任何清理都必須保留可重現性、來源時間窗與現行頁面需要的資料。

## 維護準入條件

- 新預設來源：先做 overlap、訊噪比、時間戳與 Actions 可抓取性評估。
- 抓取器或輸出 schema：加入聚焦測試並更新 `SOURCE_COVERAGE.md`。
- 評分公式本體：依 repo 規則先取得同意並完成足量回測。
- 部署或 secret：只記錄名稱與程序，不把值寫入 repo。

## 已關閉或非目標

- 不恢復已因低訊噪比退場的廣域聚合來源。
- 不把舊版 Reader Skill、上游宣傳頁或舊站點當成本專案產品面。
- 不以大量新增來源解決重點訊號供給不足。
- 不在公開預設中依賴登入、cookies、私人信箱或不穩定社群 bridge。
