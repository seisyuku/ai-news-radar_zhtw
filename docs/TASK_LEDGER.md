# 任務台帳

更新：2026-10-27。任務狀態、完成條件與續接入口集中於本頁；方向見[ROADMAP](ROADMAP.md)，歷史見[HANDOVER](HANDOVER.md)。產品、來源與操作規則仍分別以README、[SOURCE_COVERAGE](SOURCE_COVERAGE.md)及[OPERATIONS](OPERATIONS.md)為準。

舊文件的「下一步」「待驗」「尚未推送」描述其日期當時的狀態，不能直接當成現行任務。T編號沿用本次盤點，P1／P2沿用原Roadmap，不代表已排定順序或期限。

## 目前執行狀態

- D+重點選稿及情報列表簡化：I01～I04已正式發布與驗收完成，見[I04](SIGNAL_SELECTION_I04_RELEASE_20261024.md)與C07；本案結案，無下一個必跑階段。後續日常維護GPT-6.1 Sol／Medium，修程式High。
- PG、BR與方案A維持已結案；D+是新用途選稿案，不重開PG05補修或來源觀察。
- 私人日報自動化與七日來源觀察已取消；CyberQ／AlphaLab 的七日回放只是先前來源評估，沒有排程或實作驗收義務。退役入口與相依功能的盤點見[取消與移除評估](RETIREMENT_AUDIT_20261025.md)。公開刷新、daily-brief 與全站 24 小時規則照常運作。
- 2026-10-24文件整理已提交並推送；2026-10-25補正退役日報操作文件及舊影子來源／新 RSS 接入的時序。
- T03 Groq 摘要跨期回顧已完成，決定維持現有六則上限與 prompt，見[評估](GROQ_SUMMARY_T03_REVIEW_20261025.md)。T02 已依 14 日既有資料完成模型對齊及品質評估，暫不新增 `model_significance`，見[T02評估](MODEL_LIFECYCLE_T02_REVIEW_20261025.md)。T01 六類事件徽章與篩選已[正式發布並驗收](T01_EVENT_FILTER_IMPLEMENTATION_20261025.md)；T05 已依現行產品定位移除兩個 Canary 並結案；T04 已依維護者裁決刪除 Gemini 新聞摘要備援並結案；不再提出重測、接線或啟用建議。T06 狀態見下節。不建立 T05 排程、提醒或來源觀察。

## 尚待處理方向

| 編號 | 優先級 | 項目 | 狀態 | 下一個可交接動作 |
| --- | --- | --- | --- | --- |
| T06 | P2 | 翻譯快取成長治理 | 待量測／待決策 | 以明確唯讀任務建立量測及適用限制證據。 |


### T06：title-zh-cache成長治理

尚無prune機制，但未因此確認必須清理。先取得可重現多時點量測及適用環境／儲存限制；正式觀察前定義容量、成長率與觀察窗，不事後選有利期間宣稱觸發。

完成條件：依OPERATIONS形成可追溯量測與決策；未達門檻可維持現況。達標也只先提治理案，不預設prune、壓縮、分割或重建。archive容量已降級為例行觀察，不自動啟動清理。

## 已完成／已結案

| 編號 | 工作 | 結案依據 |
| --- | --- | --- |
| C01 | PG01～PG06：發布者與用途治理 | [PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)。採最後補修（四）定稿，不開補修（五）。 |
| C02 | BR01～BR06：brief同事件合併與24小時資格 | [BR06](BRIEF_EVENT_BR06_RELEASE_20261023.md)。 |
| C03 | 方案A／A01～A06與原S流程收尾 | [A06](SOURCE_GOVERNANCE_A06_RELEASE_20261022.md)。原S04長觀察由提前停止及集中評估取代。 |
| C04 | D00：日報自動化退役 | [退役交接](DIGEST_RETIREMENT_HANDOFF_20261021.md)及[S03實況](SOURCE_GOVERNANCE_S03_STATUS_20261022.md)。 |
| C05 | 三失效入口移除、INSIDE接入、RuntimeWire分流 | [來源工作歷史](RADAR_SOURCE_REVISION_20261018.md)及後續A06／PG06；不再等舊文件的下一次自然刷新。 |
| C06 | 舊外部heartbeat PAT替換 | 使用者2026-10-01已回報替換並驗HTTP 204；原10/17到期提醒取消，例行操作依OPERATIONS。 |
| C07 | I01～I04：D+重點選稿、模式入口及排序簡化 | [I04正式發布與驗收](SIGNAL_SELECTION_I04_RELEASE_20261024.md)。後端／正常資料／前端與CI、Pages、HTTP及Chrome均通過。 |
| C08 | T03：Groq 摘要品質與運作回顧 | [10/18～10/24既有快照評估](GROQ_SUMMARY_T03_REVIEW_20261025.md)。回顧可用率、失敗、快取及新聞細節；六則上限與 prompt 維持原樣。 |
| C09 | T02：模型生命週期與 `model_significance` 評估 | [10/11～10/24既有快照評估](MODEL_LIFECYCLE_T02_REVIEW_20261025.md)。定義模型對齊及長窗品質契約，檢查 14 日來源健康及明確誤報；暫不新增重要性分數，保留 24 小時讀者窗口。 |
| C10 | T01：一般列表六類事件徽章與篩選 | [正式發布與驗收](T01_EVENT_FILTER_IMPLEMENTATION_20261025.md)。沿用既有六類判定，資產共同版本、離線 CI、Pages、HTTP 與正式站 Chrome 均通過。 |
| C11 | T05：Usage policy Canary 退役 | 依現行產品定位移除兩個第三方 commit feed、候選卡片及相關程式；價格偵測保留。14 天品質研究與新增入口取消，舊文件僅作歷史紀錄。 |
| C13 | T04：Gemini 新聞摘要備援刪除 | [維護者退役裁決](T04_GEMINI_SUMMARY_RETIREMENT_20261027.md)。刪除設計與專用測試／排程；僅留通用串接供其他新用途，不再建議重測。 |

## 已撤回／提前停止／封存

| 編號 | 項目 | 有效狀態與邊界 |
| --- | --- | --- |
| R01 | 日報自動生成、派送、排程、三日交付及私人雲端自動交付 | 2026-10-21撤回，D00已退役。舊D／C／O未完成項不續跑；工具及研究保留。由使用者在Web Chat專案當次要求產文。 |
| R02 | 七日來源觀察、D7核查、D8停用及收尾Email | A01已提前結束，不等待原10/28～10/29、不重寄、不補成七日通過。CyberQ／AlphaLab 七日回放僅是先前離線來源評估，無持續執行或驗收義務；公開刷新、Pages及daily-brief維持。 |
| R03 | A03當時八個候選來源的裁決 | 當時資安人、CyberQ、網管人、DIGITIMES、Meet、Cloudflare、Modular、Zed為not_admitted_closed。CyberQ 後續於2026-10-25以新 `tw_media/cyberq` RSS 路線單獨准入一般池，舊 `shadow/cyberq` 裁決不變；其餘候選無再觀察或提醒義務。 |
| R04 | Free LLM APIs／market_free_tier | 自動分支已退役，無已驗等價替代為已接受損失；價格偵測保持。 |

## 已接受限制

以下不是自動續行任務：有界去重的漏併（如NVHBM）及21日記憶範圍；共享AI分類的基礎設施漏收及覆蓋不足；unknown／reported／unreviewed依政策保守處理；保護材料、既有污染及independent_precision=not_evaluable。PG改善部分教學／材料判斷，不等於全面分類品質已驗。不為解除限制而自動重開matcher、升級來源或解除隔離。

## 例行維護與可選整理

- 以既有source-status與更新時間處理排程及來源健康，不建立額外監控或提醒。
- M01：/Users/lordmi/Downloads/ai-news-radar-gemini是已合併、乾淨的舊translation worktree（2026-10-24盤點）。可另行指定清理，非未發布功能；本次不移動或刪除目錄及私人檔案。

## 狀態更新與交接

使用者指定T項目後，確認起始版本、最小範圍及既有證據，再更新執行狀態。結束時記錄實際完成條件、結果／限制及證據；完成者移至結案表。狀態整理不自動改優先級、排程或准入。

本次 T01 已正式發布並驗收；下一個功能任務需另行指定。模型建議不構成自動續行。
