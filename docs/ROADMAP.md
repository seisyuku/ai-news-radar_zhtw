# AI 商業情報雷達 Roadmap

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
- v1 已在「模型」分頁加入七日 atomic 發布資料，保留真實 release date，
  不把舊發布偽裝成 24 小時新消息。
- 待辦：把 benchmark、價格/API、部署、商業採用與安全分析掛到同一
  canonical model key，形成完整七日模型生命週期。
- 待辦：完成至少 14 日來源健康與誤報回放後，再決定是否增加
  `model_significance`；未完成回放前不修改全域評分公式。

## P2：成長型資料治理

- 觀察 `title-zh-cache.json` 成長率；目前尚無 prune 機制。
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
