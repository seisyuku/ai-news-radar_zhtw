# O01 日報生成與上午交付提案

狀態：**使用者已選本機私人交付；手動入口已實作，排程尚未啟用**。
日期：2026-10-03，所有交付時刻使用 Asia/Taipei。

後續決定：使用者回覆「本機私人交付」。本輪依核准實作
`scripts/deliver_digest.py`，固定遠端三檔、私人staging／版本交付、時效門檻、
程序鎖與安全失敗紀錄；用法與驗收見 [DIGEST_USAGE](DIGEST_USAGE.md)、
[HANDOVER](HANDOVER.md)。以下CI方案保留為提案歷史，不代表已採用或需發布程式。
本機方案不需commit/push或公開artifact；手動驗收之後的automation另行啟用。

## 現況與原因

本機 HEAD／cached origin/master 都為 `541e493957e01168434dd8eb22de414f11045096`，
本機 archive/health 時間停在臺北10/1 23:11:39。D11 因此交付10/2不完整草稿與10/3空日。
唯讀 GitHub 查詢確認遠端 master 已到 `c32d582705a7ea54ca241cfe50afb914753cbdb8`，
該 commit 的 archive/health 同為 `2026-10-02T22:05:32.441492Z`（臺北10/3 06:05:32），
archive 8399筆；最新觀察到的刷新 run 成功。這次空日是本機副本落後，非遠端停止抓取。
[已觀察的成功 run](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/37070548098)。

遠端仍有既有刷新流程；本機 workflow 設定名義每小時4個錯開分鐘的 tick、update job
15分鐘 timeout、既有 watchdog／外部 heartbeat 接管。最近8個 run 有 success，也有
可能只做 freshness-check 的 dispatch；不能只看 run success 推論有新資料，應讀資料 as-of。
不改既有刷新頻率、provider、付費來源或公開 Pages 發布。

日報 CLI 及配套目前仍為本機未提交檔案，固定遠端 commit 的
`scripts/generate_digest.py` 回傳404。CI方案需先取得公開程式碼發布授權；不能假設遠端已有。
本輪沒有 fetch/pull、資料刷新、workflow_dispatch、workflow修改、commit/push、automation或部署。

## 建議方案：雲端生成，人工下載校稿

維持現有新聞更新，新增**獨立唯讀日報 workflow**，只從已發布的資料生成草稿。
雲端不依賴 Mac 是否開機；本機在上午下載 artifact 到 Downloads，再另存校稿副本。
不把生成 MD/meta 提交回 repo，不新增抓取／翻譯／LLM，不借其他期新聞補題。

| 臺北時刻 | UTC | 動作／完成標準 |
| --- | --- | --- |
| 06:00 | 前日22:00 | 固定本期內容截止，沒有額外擴散等待窗口 |
| 07:15 | 前日23:15 | 主生成嘗試；固定遠端資料 commit、核對 as-of、生成並驗 MD/meta |
| 08:15 | 當日00:15 | 備援嘗試；已有驗證通過且資料達標的本期產物則跳過，否則取得新快照重試 |
| 09:00 | 當日01:00 | 人工檢查 artifact／Actions 摘要；缺產物或過舊資料走失敗處理，不靜默當空日成功交付 |
| 09:00～10:45 | — | 下載校稿，刪教學／噪音、收斂同 URL refs、核對原文及金額／版本／歸因 |
| 11:30 | 當日03:30 | 人工發布目標；未校稿或資料不完整可延後／停刊，不自動發布 |

這些是生成／審閱時刻，新聞收錄仍只用 `[D-1 06:00,D 06:00)`。09:00是人工檢查點，
沒有新增第三個自動 job 或對外通知承諾。Actions schedule 不保證準時，可能延遲或丟棄；
兩個嘗試也可能同時受影響，不能視為嚴格SLA。
[GitHub schedule 限制](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

## 輸入、身份與交付狀態

1. 明確傳入臺北期別 D；觸發時間不決定新聞窗口。延遲 job若已跨臺北日期，不默默換期，
   記 missed/deferred，使用者手動指定 D 恢復。
2. 解析一次遠端 master SHA；同一 SHA 取 archive/cache/health 三檔，保存 bytes SHA與
   source_commit。code_version/commit另記執行 manifest；不混不同 branch HEAD 的三檔。
   不在 dirty worktree pull/rebase，也不改本機正式 data/。
3. 使用 D09 composer/CLI，保持 generator 身份算法；額外 source_commit、取得／執行時間
   留交付 manifest，不塞入確定性日報 identity。產物需核對 identity/hash，不以 run success 代替。
4. 新操作層狀態建議如下，**不改既有 CLI 空日exit0／optional health降級契約**：

| 狀態 | 條件 | 交付／重試 |
| --- | --- | --- |
| ready-for-review | archive as-of已到本期截止，且執行時距 as-of≤90分鐘，配對通過 | 可交人工校稿；健康partial/missing/mismatched另提示，不冒稱完整覆蓋或完成查證 |
| review-only | archive as-of未知、未達截止、過舊或未來時間 | 只保存帶限制的診斷草稿；重試，不宣告正常當期交付 |
| failed | 必要輸入、生成、序列化、寫入、pair核對失敗 | 不發布新正常產物；保留之前成功版本及安全錯誤 |

90分鐘是提議的**交付資料時效門檻**，不是收錄條件、擴窗或消息擴散時間。
as-of是producer觀測時間，即使達標仍不保證窗口完整。真的新快照／同一期無題可以
ready-for-review空日；過舊快照無題必須review-only，不宣稱當天沒有新聞。

## 儲存、權限與失敗處理

- 建議 artifact 名稱包含期別與 run ID，保存7天；只上傳 MD/meta、安全交付 manifest。
  原始 archive/cache/health、OPML、credentials、私密 feeds與原 exception 不上傳。
  workflow僅需contents讀取與既有artifact讀取，沒有repo寫入、source/API/LLM secrets。
- 目前repo公開。artifact不是私人保險箱，具repo讀取權限的登入者可下載；若不接受
  未校稿草稿被下載，改採下面本機方案，不在此repo上傳草稿。
  [Artifact 存取與保存](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)。
- 本機下載先到新 staging目錄，核對完整配對後才交付至
  `/Users/lordmi/Downloads/ai-news-radar-digests/YYYY-MM-DD/<identity>/`；runner內只有工作目錄，
  不聲稱會直接寫入Mac Downloads。校稿版另存review.md；重試不能覆蓋人類已編輯版本。
- 同一期並行執行需串行／互斥；備援先查**實際已核對產物**而非只看成功run。
  若改了資料而重新生成，保存新 identity 版本；第一份ready產物交付後不自動替換校稿版。
- 失敗或資料不達標在Actions摘要明示期別/as-of/source SHA/安全原因；08:15重試。
  使用者訂閱該 workflow 失敗通知後才有GitHub通知；本提案沒有設定email/Slack/外部通知。
  若需要09:00定時主動提醒，另核准通知渠道／自動化，不默認有硬時限通知。
- 09:00仍未ready時，人工查既有刷新是否最新，取固定新commit手動重跑。
  不自動dispatch新聞刷新，因既有刷新可能呼叫付費provider；不當作無成本日報重試。
  配對中斷用完整生成＋核對恢復，不提供跨檔交易或斷電保證。

## 備選：本機生成與私人交付

適合不接受artifact草稿可見性、Mac上午通常可用者。先以read-only API下載固定遠端
commit三檔到Downloads隔離目錄，再執行目前本機CLI；不pull覆蓋未提交程式碼，不在repo
保存原始輸入。可先人工執行同樣07:15/08:15流程；若需Codex recurring automation，
另核准後使用app原生automation工具，不能假設Mac睡眠／離線時會準時交付。
本輪兩方案都沒有建立排程或automation。

## 核准後的實作／啟用驗收

此部分是待辦，尚未動工：

1. 選擇CI artifact可見性或本機私人交付；接受上述時刻／時效／失敗安排。
2. 若選CI，審閱並選擇性提交／發布日報程式、測試及必要文件到已設定repo，不把
   其他差異、私人feeds或舊資料快照整批提交。此repo已在公開Pages運作，程式發布需明確授權。
3. 先實作manual-only日報workflow及資料固定／交付guard，離線測邊界與故障；
   使用已發布資料做一次手動驗證，不新增provider key或抓取。
4. 手動驗收MD/meta、artifact內容／可見性、下載路徑、重跑與過舊／未達截止／未來as-of/
   必要資料錯誤、真正空日／並行／中斷，確認不改公開data或人類稿。
5. 手動驗收通過後再依核准內容啟用日報觸發；按 OPERATIONS核對實際schedule開始執行，
   連續3天記錄主／備援起止、時效、ready狀態及人工下載時間。沒有實際run前不標啟用成功。
6. 發布仍由人操作；LLM、資料源品質／去重修改不由此核准默認包含。

O01進度：提案與診斷完成，已採用本機方案；手動入口已實作，排程／3日驗收仍待下一階段。
下一階段建議GPT-6.1 Sol／Medium，重點為本機automation時刻、執行權限與實際交付觀察。
詳見 [OPERATIONS](OPERATIONS.md)、[DIGEST_USAGE](DIGEST_USAGE.md)、[HANDOVER](HANDOVER.md)。
