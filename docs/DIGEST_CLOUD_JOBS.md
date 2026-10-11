# C08 本機意圖、生成前 guard 與有界補跑

2026-10-10最新路由：先完成 [C08-G GitHub生成驗證](DIGEST_GITHUB_GENERATION.md)，不依賴Cloudflare。
下文memory coordinator是正式私人交付的模擬證據，不要求生成job先部署它；跨job持久去重及每日觸發仍待接通。

更新：2026-10-10。**本機流程與合成合約 workflow 完成；正式外部觸發／交付 job 未接通。**

## 已實作

- `MemoryJobCoordinator.issue_slot` 由服務端時鐘推導臺北日期及07:15/08:15/08:45 slot，
  發行窗口15分鐘；同一期同slot重送沿用已保存的意圖與request ID。不能由runner猜日期。
- `claim` 在下載／生成前排他保留execution、固定source commit；最多3次execution。
  同execution重送不新增，活躍租約內第二runner回in_progress；每次租約最多10分鐘。
  恢復沿用第一次固定commit，第四次在loader前拒絕。跨日不換issue_date。
- 定時slot若已存在完整合格交付，直接略過；已結算request回原receipt，不再生成。
  當期人工retry需owner policy的digest:retry，最多3個logical attempt；歷史補驗需明確指定
  historical，不能算當日成功。人工重試可保留既有基底並新增候選，不自動覆寫校稿。
- `run_job` 重用C03/C04；提交交易在讀取服務端時鐘後再檢查claim，逾期或過時execution
  不能提交。部分上傳／生成失敗只回固定原因，不回exception原文或私人產物。
- 合格交付和09:00未達標可產生去重的安全通知**計畫**；沒有發送通知，渠道仍待定。
- `public_job_summary` 重建公開紀錄白名單，只保留合法期別、狀態、原因、commit、時效及核對欄位，不輸出原稿、物件位置或例外原文。提交成功後協調紀錄失敗仍回已提交，重送由權威交付 receipt 恢復，不重新生成。
- 新增手動 [合成合約workflow](../.github/workflows/digest-cloud-contract.yml)：contents:read、
  timeout10分鐘、只跑合成測試。沒有schedule或正式交付步驟。
- 三份驗證 workflow 的 pytest 暫存改到 runner 的 Downloads，符合既有準備入口的路徑約束；既有 schedule 與觸發條件保持原值。新變更尚未推送或在 GitHub 實跑。

## 修正兩項恢復問題

1. C04原先把第一次可恢復I/O失敗標failed，又允許下一execution改回running。
   現改為：有剩餘execution的暫時錯誤仍running並保留reason；額度耗盡、永久錯誤、
   明確CAS條件衝突／跨日才終態。failed/missed_issue不能重新開始，舊execution的失敗
   不得改寫較新execution。這使有界恢復與C02終態規則一致。
2. C04去重payload原含每次重新生成的started_at，同輸入重跑也會衝突。
   現去重只用固定請求、意圖、commit、原稿與輸入hash；第一次started_at仍保留作觀測，
   重新prepared的時間只作核對觀測，不改請求意義。已成功重送仍回原時間與receipt。

記憶體coordinator與delivery control共用同一個鎖，避免claim讀控制層與commit查claim
出現相反鎖順序。這不是分散式鎖證據；正式控制層須在同一期持久交易中整合
intent、claim、execution fence、delivery receipt及校稿指標。

## 真實與模擬邊界

- memory store不抗服務重啟；issuer是內部注入的模擬來源，沒有網路登入或Actions身份驗證。
  不把issue_slot方法直接暴露給匿名MCP／HTTP。
- loader為注入的固定commit來源；本輪沒有從GitHub下載正式輸入、發行線上意圖或dispatch。
  正式loader與I/O重試需在選定平台後接入，保持每I/O最多3次、1/2秒間隔與工作期限。
- 正式私人job/交付的線上原子狀態、OAuth/服務身份與secret名在保存方案定案後接通。
  GitHub純生成工作可先完成，不依賴C09；此文件的合成workflow不代表每日生成已啟用。
- 沒有發布MCP的retry工具；須等可信意圖/guard正式接通後才提供。

## 驗證與交接

- 新增13項job測試，涵蓋slot去重、跨日、未知request、ready略過、固定commit恢復、
  租約與第四次guard、上傳途中到期、manual/historical、並發claim、偽造claim、通知去重、公開摘要及已提交後紀錄失敗恢復。
- 第一次相關46項中1項失敗：明確CAS衝突應保持永久終態。修正可恢復判斷後46項通過；
  階段完整 **964 passed in 3.47s**。之後MCP增加原始JSON重複鍵／NaN檢查及上述恢復／摘要案例，最終完整 **966 passed in 5.19s**。
- 檢查點：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C08-local/`，含C08修改前
  源碼、測試log與最終快照。回復時只比對本輪文件，不做全庫reset。
- 最新下一入口 [C08-G GitHub生成](DIGEST_GITHUB_GENERATION.md)及私人保存方式裁決；C09只在正式私人接入階段啟動。
