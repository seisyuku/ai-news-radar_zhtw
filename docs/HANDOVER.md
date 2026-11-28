# AI News Radar 交接摘要

更新：2026-11-28（臺北）。本頁保留目前有效狀態與 2026-11-19 起的交接紀錄。任務清單以 [TASK_LEDGER](TASK_LEDGER.md) 為準，產品、來源與操作細節分別依 README、SOURCE_COVERAGE 與 OPERATIONS。

## 11/28 全系統狀態機重構 R12 正式發布驗收

`6914f48cc0e2` 後端、`aca6e13bab42` 正常刷新、`a2b936eaf015` 前端依序發布。臺北 11:05:31 快照共 95 篇一般 AI 新聞、108 篇全量新聞、0 則重點、0 則模型雷達。治理為 ready，14 個來源成功，失敗及降級各 0／0，OPML 失敗 0。24 個正式 HTTP 檔與部署提交逐位元相符，包含首頁、共同資產、公開資料及三篇舊文章的雙格式永久連結。Chrome 1440×1000 與 390×844 通過一般／全量切換、去重、來源篩選、清除與同代治理。正式驗收已完成。[後端離線 CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/46101020209)、[後端 Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/46101019558)、[正常刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/46101142952)、[資料 Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/46101277612)、[前端離線 CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/46101403543)、[資產版本](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/46101403526)、[前端 Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/46101402847)均成功。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r12-20261128/HANDOFF.md`。例行讀回建議 GPT-6.2 Sol／Medium。

## 11/28 全系統狀態機重構 R11 已驗收

在本機依序提交後端、生成快照、換版前端。後端搭配舊前端通過 2,403 項測試，完整候選版通過 2,422 項。R01 兩輪回放共 32,836 檔逐檔相符。新舊前端皆可讀相容資料，混代時保留一般新聞。來源探測與觀察、SMTP、私人校稿及獨立工具均以模擬服務驗證。

注入 daily 寫入故障後，發布分支保有最後成功快照。先退前端再退生成器，沿用並行發布保護及較新資料。重新生成後保有 8,205 個文章 ID、407 篇文章的修訂歷史、3,627 個事件的階段與時鐘，兩種永久連結共 16,410 檔一致。模擬價格依序從 2 到 1.25，再從 1.25 到 0.75。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r11-20261128/HANDOFF.md`。分段候選與回退演練供日後維護參考。[實作計畫](STATE_MACHINE_REFACTOR_PLAN.md)

## 11/28 全系統狀態機重構 R10 已驗收

以同一計時入口更新 2／6 小時橫幅及事件、模型到期。分頁恢復立即重算，畫面重建取消舊動效。全量三次切換共用一次請求。1440×1000 及 390×844 Chrome 驗收、完整 2,422 項測試均通過，兩輪回放與 R01 共 32,836 檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r10-20261128/HANDOFF.md`。

## 11/28 全系統狀態機重構 R09 已驗收

主快照與輔助檔到達時更新治理狀態。正常、降級及修訂衝突三種情境各驗 24 種順序，重點與雷達讀取相同結果。159 項聚焦、2,415 項完整測試通過；額度中斷後重跑全套與相容性比對亦通過。兩輪回放與 R01 共 32,836 檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r09-20261128/HANDOFF.md`。

## 11/28 全系統狀態機重構 R08 已驗收

重播正式 heartbeat 成功但更新 job 跳過的案例。現以 Git 發布分支的快照時間判定 25 分鐘門檻。Watchdog 仍依排程觸發時間判定，整分鐘商大於 90 時代觸發。聚焦 46 項、完整 2,411 項通過，兩輪回放與 R01 逐檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r08-20261128/HANDOFF.md`。

## 11/28 全系統狀態機重構 R07 已驗收

本機雙 clone 重現並修復舊快照覆蓋較新 archive 的競態。20 項 Git 發布案例及完整 2,385 項測試通過，兩輪與 R01 逐檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r07-20261128/HANDOFF.md`。

## 11/28 全系統狀態機重構 R06 已驗收

事件歷史寫入結果決定各公開檔的治理版本。故障輪仍能讀一般新聞和價格，下一輪可恢復重點與雷達。完整 2,370 項通過，兩輪輸出與 R01 逐檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r06-20261128/HANDOFF.md`。

## 11/28 全系統狀態機重構 R05 已驗收

封存紀錄與時間取自同次讀取，事件歷史區分續用、重建及不可用。完整 2,368 項通過，兩輪輸出與 R01 逐檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r05-20261128/HANDOFF.md`。

## 11/27 全系統狀態機重構 R04 已驗收

價格基線遇讀取失敗、損壞或目錄縮水時保留原檔。既有價格訊號照常到期，恢復後沿用最後有效基線計算價差。完整 2,366 項測試通過，兩輪 16,434／16,402 檔與 R01、R03 逐檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r04-20261127/HANDOFF.md`。

## 11/27 全系統狀態機重構 R03 已驗收

翻譯與 Groq 的未來拒絕時間視為無效，翻譯 429 重試受剩餘時間及請求額度限制，導言在同輪每個網址只嘗試一次。完整 2,358 項測試通過，兩輪 16,434／16,402 檔與 R01、R02 均逐檔一致。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r03-20261127/HANDOFF.md`。

## 11/27 全系統狀態機重構 R02 已驗收

翻譯與 Groq 快取的壞版本、壞紀錄及異常來源連敗值已在本機隔離。生成入口測試確認有效的相鄰紀錄可續用，壞 archive 仍會中止並保護既有輸出。完整 2,346 項測試通過，兩輪回放與 R01 比較 16,434／16,402 檔，均零差異。

交接位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r02-20261127/HANDOFF.md`。

## 11/27 全系統狀態機重構 R01 已驗收

R01 以 11/20 的三份連續正式快照固定種子和兩輪時鐘。兩組離線回放每輪均走生成入口，16,434／16,402 個輸出逐檔一致。重點 1 → 0 與當時正式選集相符。收件與供應商使用固定條件；公開資料與模擬差異見證據目錄的 comparison.json。11/27 21:35:35 正式快照的首頁、健康檔和 daily brief 與 GitHub 提交一致。

交接及比較命令位於 `/Users/lordmi/Downloads/ai-news-radar-refactor-r01-20261127/HANDOFF.md`。[交接模板](TASK_HANDOFF_TEMPLATE.md)

## 11/20 Anthropic News 列表修復（已發布並驗收）

已修復官方新聞列表解析及置頂卡片掩蓋列表故障的健康誤報，並納入官網 Newsroom 列出的 Claude 模型發布頁。依裁決，Claude Desktop 更新頻道不收錄。程式 `f51deb13cf18` 已推送 master，臺北 11/20 11:09:30 快照 `f90593a6f071` 收到 Anthropic News 18 篇、Claude Product Updates 12 篇。正式站 17 檔與生成提交相同，四篇指標公告封存、讀者資料及來源健康驗證完成。 [來源覆蓋](SOURCE_COVERAGE.md#2026-11-20-anthropic-news-列表修復與模型公告收錄)

## 人工查漏參考

阿梨 AI 早晚報保留為人工找線索的參考，原始文字與來源仍逐則回查。評估依據見[來源覆蓋](SOURCE_COVERAGE.md)。

## 下次接手

先讀任務台帳的目前待辦，再核對實際Git、工作目錄及來源健康。公開新聞維持24小時窗口與現行來源／用途資格；實作新的來源、評分或產品能力時，依相關權威文件另行處理。

更新本頁時以臺北日期計算十天窗口，只保留目前有效狀態、近期完成結果與必要入口，刪除超期項目和被取代的接續步驟。當前規則依權威文件維護，不藉由保留整串舊歷程傳遞。
