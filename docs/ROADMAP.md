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
- 變更 `assets/` 時同步遞增 `index.html` 的共用 `?v=`；由 Git baseline
  測試驗證資產變更與版號更新成對出現。

## P1：維護者日報與持久交接（2026-10-02 設計已確認）

- 收錄台北時間前一天 06:00 至當天 06:00，半開區間；無擴散等待或跨窗口例外。
- 先做唯讀既有資料、確定性候選與繁中 Markdown，上午人工校稿，約 11:30
  人工發布為目標。D01～D11與本機私人手動交付已完成，排程尚未啟用。
  既有公開網站、新聞排序與來源邊界維持原設計。
- 依 [DIGEST_PLAN](DIGEST_PLAN.md) 的 D01～D11 小任務推進；每項起點即保存
  Downloads 檢查點，完成後更新台帳、HANDOVER 與下一階段模型／思考建議。
- 2026-10-03後續驗證改在GitHub：兩個上午時刻觀察生成／時效，僅安全摘要；
  私人交付仍在本機，三日schedule驗收待完成。可選LLM與自動發文不包含在驗證排程。
- 2026-10-09 已核准 [私人雲端日報架構 A](DIGEST_CLOUD_DELIVERY_PROPOSAL.md)
  的本機離線模擬；目的為 Mac 關機也可交付、iPhone 語音校稿。C00 準備與
  62 項既有離線測試完成；C02 六項設計審查已完成，
  [正式契約與36項驗收案例](DIGEST_CLOUD_CONTRACT.md)，C03～C06 本機生成、保存、
  校稿版本與[合成私人網頁預覽](DIGEST_CLOUD_PREVIEW.md)已完成，
  [C07 接入審查與C07a](DIGEST_CLOUD_C07_REVIEW.md)、[C07b/C07c本機接入](DIGEST_CLOUD_RUNTIME.md)及[C08本機工作協調](DIGEST_CLOUD_JOBS.md)已完成，完整966項測試通過。
  2026-10-10使用者校正順序：先做 [C08-G GitHub日報生成](DIGEST_GITHUB_GENERATION.md)，
  新增手動直接讀checkout的生成與核對工作；私人保存去向待決定，還沒有完成每日交付。
  後續使用者選擇先嘗試 [Google Drive校稿與設定](DIGEST_GOOGLE_DRIVE_TRIAL.md)，實際合成保存、
  副本校稿/原稿保留、設定讀回與權限核對通過；手機新連結及GitHub專案OAuth授權仍待確認。
  2026-10-11手機三份新文件已由使用者確認，帳號為一般Google；[手機OAuth helper準備](DIGEST_GOOGLE_DRIVE_AUTH.md)
  及25項合成測試完成，完整1007項通過。需選定Google Cloud專案才進真client/授權；不使用裸露控制碼交付。
  使用者隨後已選日報專用專案，建立表單已提交；控制台載入錯誤使結果未知，需 [手機確認實際專案](DIGEST_GOOGLE_PROJECT_SETUP.md)，再進client與授權。
  [C09部署前置](DIGEST_CLOUD_DEPLOYMENT_GATE.md)延後至正式私人服務接入，不能阻擋生成驗證。
  真雲端保存/部署與手機遠端校稿尚未實作，
  現行交付仍在本機；C01 已用現成 Google Drive 外掛完成 iPhone 帳號能力代理驗證，
  C01b 專案自建工具的實機驗收移至核准後 C10a 合成環境；真日報與三日驗收仍待完成。
- 已知 bug B01～B03 已於提交前複查修正；Social snapshot／Threads、model aliases 與
  新來源屬條件後續，不綁入第一份可用日報。不建立 velocity 或 social history。

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
- 已裁決：Gemini `gemini-3.5-flash-lite` 為
  `qualified backup candidate, disabled by default`；Groq 保持 primary，
  尚未授權 production fallback 或真實 publisher feed 呼叫。
- 待辦（Gemini acceptance）：裁決提示注入語意／精確詞 gate、完成三個
  分離時段 live diagnostic/eval、擴充合成案例並與 Groq 同案比較。
- 待辦（fallback implementation）：建立 Groq failure trigger matrix、
  防雙重呼叫、獨立 secret、provider+model cache identity、單輪成本上限、
  公開安全狀態與雙 provider 失敗行為測試。
- 待辦（operator decision）：啟用前重新核對 Gemini active rate limits、
  定價及 free/paid tier 資料使用條款，取得 maintainer 明確接受後才可接線。
  完整 gate 以 `docs/OPERATIONS.md` 為準。

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
