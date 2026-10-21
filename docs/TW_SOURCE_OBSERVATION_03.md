# 步驟 03：每日 Email、七日結案與自停條件（本機完成，未部署）

> 2026-10-22：原觀察工具已於整體S03提交／推送，尚未啟用實驗；SMTP與停止責任
> 尚缺。最新外部狀態見[S03狀態](SOURCE_GOVERNANCE_S03_STATUS_20261022.md)。

> 本文件記錄原觀察工具03建置；後續S02整體審查與修補見
> [S02結論](SOURCE_GOVERNANCE_S02_REVIEW_20261021.md)。最新回歸1495項通過，
> 下一步為整體計畫S03。日報另案退役；實驗自停失敗須按新契約人工處置，不無限延長。

使用者「執行03」授權本步建置；部署仍須另行核准。沒有設定或讀取真實寄信
憑證、寄送 Email、改外部心跳、推送或啟動 workflow。正式 Radar／私人日報
的來源、收錄、排序、資料與發布流程不改。

## 已建置的工作順序

`tw_source_reporting.py` 負責通知 ledger、報告凍結、七日結案與自停閘門；
`tw_source_email.py` 提供單一收件人的 TLS SMTP adapter。
`observe_tw_sources.py` 新增 notify、audit-stop；reconcile 同時準備報告與通知。
兩份 workflow 仍在 docs，全部 jobs 硬性 false；plan disabled、日期／SHA／
workflow 指紋留空，沒有註冊排程。

1. reconcile 驗證觀察證據與獨立通知歷史。主失敗先等補試；主成功、補試終態，
   或 07:05 期限到才備妥每日回報。觀察證據壞掉標 unavailable，不假稱缺測或成功。
2. 先保存每日報告 artifact；第七天還須保存結案包，再上傳 notification intent。
3. notify 重新讀 GitHub，確認報告、結案引用與 intent 已真正保存，且與本機完全
   相符，才取用寄信 secret。單 job 重跑也用本機 durable marker 擋第二次送信。
4. 保存服務接受／確定未接受／結果不明的 receipt。自停審查再次下載遠端證據，
   不能把上一步綠燈、stdout 或本機 receipt 當成已持久化。
5. 只在結案包與其對應的結案 Email 接受紀錄均驗證成功時，audit-stop 輸出 stop=true。
   獨立 actions:write job 只停用兩個固定實驗 workflow，不 checkout 程式、不接觸私人
   secret，也沒有 contents:write、正式刷新 dispatch 或 Pages 發布權限。

audit-stop 本身唯讀；真正停用由仍硬性停用的 workflow job 執行。停用 API 失敗
會保留 Actions 失敗狀態，後續合格 report 觸發可重試，不重寄已接受的結案信。
日期閘門照常禁止 D8 再採樣，Email／自停故障不會延長到湊滿七次成功。

## 每日回報與去重

- 主旨：`[TW來源觀察][D3/7][成功／補試成功／未達標／缺測／證據無法驗證] 日期`。
  本文含五站狀態／篇數、真實主補時點、baseline、限制、待人工核對篇數與 Actions
  報告連結。沒有全文、私人日報／Drive、OPML、收寄地址或憑證進入公開 artifact。
- 正常每天一封；D7 將當日回報與結案合併。中斷後補報明列原日期並標「延遲補報」，
  可以一封涵蓋多個尚未通知的日期，不補抓過去新聞。
- 鍵固定為 experiment＋日期＋daily-final，payload 與報告 hash 凍結。重複 pulse、
  rerun、上游失敗、通知失敗都不能讓來源重新採樣。
- 確定未接受且屬暫時錯誤，最多三個投遞嘗試，由後續合格觸發接續；不在同一
  SMTP 交易內盲目重寄。三次上限、永久拒收或設定錯誤會標 notification_failed。
- DATA 期間斷線、只剩 intent 沒有 receipt、接受後 receipt 遺失：delivery_unknown，
  不自動重寄。先前日期結果不明不會被當成沒寄過而塞入隔天補報。
- 結果不明／通知失敗會使 CLI 與 Actions 呈失敗；通知 ledger 讀取或驗證失敗也
  禁止送信並保存診斷。SMTP 本身不能投遞時，不能靠同一 SMTP 保證告知其故障。
- 若 D7 逾期但採樣仍執行，先寄未達標通報且不結案；執行終止後，才用明確的
  `final-correction-1` 寄一次結案更正。這是異常情況下的第二封，沒有悄悄改寄舊報告。

通知 ledger 沿用來源 run／workflow 指紋、archive digest、manifest 與檔案 hash 驗證；
額外核對 message hash、covered_dates、receipt 與報告／結案 hash。任意每日接受紀錄
不能授權結案自停，SMTP 250/data 的接受紀錄也不代表已進收件匣。
觀察期間須保留 run/artifacts：單一 artifact 遺失可偵測並停止；整個 run 被刪除後，
同一 GitHub 歷史無法再證明它曾存在，不宣稱能對抗管理者刪除完整歷史。
歷史 API 查詢限有效採樣／報告窗口，另查手動延遲 run；不逐筆下載全天空心跳
run，也避免七天累積觸及每個查詢的 1,000 run 上限。分頁仍須完整，沒有截斷當成功。

## 七日結案包

- `FINAL_REPORT.md`：完整日數、缺測／限制、候選數與裁決界線。
- `SOURCE_DAILY.csv`：固定五站 × 七日期，共 35 列；含真實 retrieved_at、來源 slot、
  當日比較 baseline／來源 slot baseline、原 run/artifact ID。
- `EVENT_REVIEW.csv`：只列待核候選，按來源＋URL 跨日去重；保留首次／末次出現、
  每日比較、事後 baseline 聯集 URL 可見性與空白人工裁決欄。文字匯出防公式注入。
- `observations.json`：七個固定日期與診斷，新增事件／新證據確認值皆為 null。
- 各日 slot 的 capture／baseline／report／attempt，以及 `checksums.json` 與 manifest。

事後 URL 可見性與每日比對分開，不用未來 baseline 偽裝當日覆蓋，也不把候選篇數
當新增事件。缺測或 API 無法驗證同樣留在七日矩陣，不延長觀察、不自動准入來源。
結案檔案上限 140 MB 展開／110 MB ZIP、150 個平面檔，拒絕超限與不安全 ZIP；
保留期 30 天，沒有將測試報告提交回 Git 或發布到正式網站。

## 寄信設定與部署前仍需完成的事項

僅支援單一收件人 SMTP：465/SSL 或 587/STARTTLS，驗證服務端憑證與 hostname，
不支援明文 SMTP 或關閉 TLS 驗證。設定格式見
[假值範例](examples/tw-source-email.settings.json.example)。真值只放 GitHub secret
`TW_SOURCE_EMAIL_SETTINGS`；不得填入 repo 範例、commit、artifact 或聊天紀錄。
SMTP secret 只進 notify step，採樣、監督驗證與自停 job 都沒有它。

目前尚未指定服務、收寄地址或憑證，所以沒有實寄／實收驗收。上線前需一次確認：
寄信服務與 SMTP 授權、secret 設定、成功與失敗觀察範例各一封的實際收件；
然後核准開始日期、程式 SHA／workflow 指紋與部署。CLI 正式入口要求啟用 Email，
不允許開啟採樣卻把每日通知關掉。
一次性實寄驗收可先使用獨立 SMTP adapter 與信件預覽，不需啟用每日排程。

## 本機驗收與下一步

測試涵蓋 TLS、拒收與斷線、receipt 遺失、最多三次投遞、通知去重、缺測與
API 失敗、35 列七日矩陣、候選跨日去重、結案綁定、固定停用目標及停用 API 失敗。
另執行七個邏輯日期的端到端模擬：七封 SMTP 替身接受、35 次來源替身呼叫，
只有 D7 且結案 receipt 保存後才產生 stop=true。這不是七天實際經過或實際寄信。

完整驗收紀錄在 Downloads
`ai-news-radar-tw-source-observation-03-20261021/ACCEPTANCE_REPORT.md`。
實際 290 項離線測試通過（本步 60＋Actions 61＋協調器 113＋來源准入 56），
五支程式 py_compile、兩份 workflow 草稿 actionlint、diff 檢查通過；7470 個正式
程式／設定／資料／既有 workflow hash 未變。真實 GitHub／來源 HTTP／SMTP 連線、
實寄 Email 與 workflow 停用 API 均為 0，沒有部署或推送。
官方行為依據：[Python SMTP](https://docs.python.org/3/library/smtplib.html)、
[GitHub artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data)。

**下一步：部署前隔離與故障審查，建議 GPT-6 Astra（gpt-6-astra）／High。**
這是建議，沒有自動換模型或啟動 agent；審查與真實收件驗證完成後仍等使用者核准部署。
