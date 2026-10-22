# BR06：正式發布與結案

狀態：**BR01～BR06 完成，brief 事件修正已推送並正式驗收。** 使用者離機前已授權自動執行至無可執行階段；本案無下一個必跑步驟，沒有新增觀察、提醒或排程。

## 正式行為

所有 brief 入口採同一後端事件投影，同事件只佔一個位置；重發、換標題與已辨識的跨語言重述不延長 24 小時資格。具體進展更新同一事件卡；完整模型版本、平台及不同動作保留。引用、原始文章、一般新聞、歷史連結與來源規則維持。

投影無效時不從舊 stories 補回重複稿；本頁有效 cache 到期即撤下，一般新聞仍可閱讀。讀者看到的時間區分報導、進展與系統初見，只有日期時不冒充精確時刻。

## 發布與真刷新

- 先完整整合遠端 13 筆 bot 提交，3,391 個差異路徑全部屬 data／item；沒有用 capped compare 代替完整核對。
- 後端提交 `f5c9409122f142d70d4c3ef90b48c23de0ba89e3`；既有 19:05 UTC 刷新 run **39836992052**（head 為該提交），產生資料提交 `980a259212b5d50d4464b78d978bb9e395cb21bc`。初始狀態標示 recovered，175 根，HTTP state／投影／daily 同代且 hash 正確。
- 確認後端 HTTP 後才推前端提交 `643b3ce9aa34f627d548fc0d2939bbb13d2e2ce1`，五資產共同版本 `20261023-br04`。離線 CI **39837484829**、資產版本 **39837484833** 及 Pages **39837481834** 成功。
- 既有 watchdog 另觸發正常刷新 **39837505116**（head 為前端提交），資料提交 `f00e958c3e3e0df90ffc6686e4853cf75d42bb44`，Pages **39837692503** 成功。沒有由本助理額外 dispatch 刷新或更改排程。
- 第二次 state 為 ready／recovery_mode=none；原 175 根全部保留或以 alias 延續，176 個既有 phase 的時間沒有延後。PHP 六篇披露共一根，實際攻擊觀察仍為 `2026-10-22T02:24:17Z`，沒有因重發續命。

第一次 HTTP 讀取發生於新 data 的 Pages 尚在建置時，state 暫為 404；等待該 run 成功後重驗通過，未以舊資料或空 state 假裝成功。

## 正式驗收

正式 HTTP 快照為 **2026-10-23 03:09:00 臺北時間**（UTC `2026-10-22T19:09:00.111985Z`）：198 篇 AI、183 原故事、178 事件根、177 有效根、9 個內部 brief。這些是不同層級的數量；首頁依原選稿與排序仍可顯示熱點 10／時間線 20，不把內部 brief 差額當事件損失。

投影世代 `bg1_f3adbb494ab3c89dbdc55dfb`；state 178 根、169,869 bytes，revision `dd6c9776c3c11245f5641169025d191c9125cd1499840130cc4f71b3013bc3bf`。state 校驗、投影內容 hash、daily 入選 ID 與內容、來源當期 phase 票數及 24 小時期限一致。五項正式前端資產的 bytes SHA256 與已驗候選一致。

真 Chrome 155 的 1440／390 寬度均驗：熱點 10、時間線 20、展開後實際卡片 ID 唯一、無過期事件、發布者標示正確、來源／多方篩選、PHP 查詢只一張卡，以及一般全量模式（262 原始、231 顯示）正常；無 JS 錯誤、HTTP 錯誤或水平溢出。數量只是當次快照，後續正常刷新會變動。

來源健康無失敗；價格、Usage4Claude 與 Claude Usage Monitor 兩個 canary 正常，free-tier 自動分支仍不存在。五個退役的觀察／報告、日報及 SMTP 驗收 workflow 均維持 disabled_manually；觀察設定 enabled=false，既有公開刷新／watchdog／Pages 保持。未新增寄信、日報生成或額外常駐服務。

本機完整 **1,621 項回歸**與發布 CI 通過；十四日離線、固定五窗口、舊 JSON／混代／延遲／少於名額／本頁自動到期，以及 110 項副本回復驗證見 [BR04](BRIEF_EVENT_BR04_VALIDATION_20261023.md)／[BR05](BRIEF_EVENT_BR05_REVIEW_20261023.md)。

## 限制與交接

這是有界事件身份修正，不是通用語意去重。未涵蓋主題仍可能漏併，已知 NVHBM 的一組同事件報導仍分開；未使用驗證群調參追逐此例。替代樣本僅 3 群 6 篇，一般 precision 保持 not_evaluable，且 BR05 為同一助理複核，沒有另一模型獨立審查。21 日 last-mentioned 記憶及 archive 不足時，也不能承諾識別久遠重發。

回復依 BR05：先保留有效 state，可只回前端並升新共同版本；後端故障則接受 v1 並輸出 unavailable，一般新聞維持。不可刪記憶、回放舊快照或重啟退役工作流。

完整證據位於 Downloads `ai-news-radar-brief-event-br06-20261023/`：REMOTE_INTEGRATION、RELEASE_PROGRESS、CI_ACCEPTANCE、HTTP_BACKEND／HTTP_FINAL、WARM_ACCEPTANCE、BROWSER_LIVE、WORKFLOWS_BEFORE／AFTER、RETIRED_WORKFLOWS，以及 CHECKPOINT／HANDOFF／MANIFEST。sealed HTTP 僅供機械查核，勿批次展開受保護正文。

**本案無下一必跑階段。** 日常維護建議 GPT-6.1 Sol／Medium；需要修程式時 High。來源封存、不相關擱置議程與通用語意擴充不在本案自動執行範圍。
