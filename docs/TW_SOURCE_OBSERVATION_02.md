# 步驟 02：Actions 心跳、持久化與隔離接線（未部署）

使用者以「執行02」核准本機建置。工作仍留在本機與 docs 草稿；未推送、
未新增正式 workflow、未改外部心跳。正式 Radar／私人日報的收錄、排序與
發布程式、資料、設定及既有 workflow 均不修改。
後續已依「執行03」完成 [通知與結案](TW_SOURCE_OBSERVATION_03.md)；本篇保留
步驟02當時的交接範圍，當前狀態以步驟03與HANDOVER為準。歷史查詢已限有效
採樣／報告窗口，另保留手動延遲查核，避免全天心跳空run拖垮七日驗證。

## 已實作

- `scripts/tw_source_actions.py`：GET-only GitHub API adapter、完整分頁、run／
  workflow 指紋驗證、有限 ZIP 下載、archive digest／manifest／來源診斷驗證，
  還原主／補嘗試與供沿用的原始證據。
- `scripts/observe_tw_sources.py`：prepare、collect、reconcile 三個入口；
  固定程式 SHA、事件 metadata 正規化、先保存 intent 再抓取、部分來源沿用，
  以及不抓來源的獨立缺測監督。沒有 notify 或自停入口。
- 兩份 workflow 草稿已接到上述入口，仍在 `docs/examples/` 且 jobs 硬性 false。
  專用 concurrency 不取消執行中工作；採樣 job 僅 contents/read、actions/read，
  硬上限十分鐘。既有刷新完成事件只當 pulse，無須刷新成功。

## 主／補採樣路徑

1. 從當前 run API 核對自身 repo、master、workflow path/name、事件及 run_attempt=1；
   下載該 head SHA 的 workflow 檔核對核准指紋。原始事件不接受 inputs 改日期或 force。
2. 從主／補當日所有實驗 run 與 artifacts 還原歷史。API 失敗／分頁不全直接停止；
   名額曾上傳但 artifact 遺失、過期、重複、bundle 無 intent 都不能視為空名額。
   排在當前 run 後面的 queued run 尚未執行，不用它阻塞目前工作。
3. prepare 寫出 intent 與本機 state；upload-artifact 成功後才呼叫 collect。
4. collect 重新讀 API，驗證遠端已存在與本機完全相同的 intent，並重讀先前歷史。
   名額／歷史改變或 API 超時即停止；API 操作消耗時間也計入開始窗口。
   本機 exclusive create 再擋同一 job 第二次執行 collect。
5. 只向步驟 01 決策列出的來源呼叫既有隔離抓取器；不改原抓取器或正式來源。
   每站留原始診斷、實際 retrieved_at 及來源 hash；例外只記類型、不保存例外文字。
   已成功來源、終態限制與仍有效 baseline 沿用。來源例外或 baseline 比對失敗仍保存
   可用 capture，不能當作完整成功；補 slot 可只補 baseline。
6. bundle 保存該 slot 新抓的 capture、attempt、baseline 與影子 report、manifest；
   recovery report 可合併主資料，來源 capture 不偽造為補試時點。報告候選不是人工
   確認新增事件。上傳失敗／runner 中斷保留 intent，另一 slot 才能恢復，沒有第三 slot。

artifact 名稱固定 `twso-{experiment}-{臺北日期}-{primary|recovery}-{intent|bundle}`。
不使用 git／cache 當資料庫，不覆寫名額。每個 run 上傳的 artifact 不可變；
跨 run 仍靠固定 concurrency 與完整歷史檢查，不宣稱 HTTP exactly-once。

還原時不信任 JSON 的 verified=true：先核對 GitHub archive digest、來源 run、
核准 workflow 指紋、manifest 的 experiment/date/slot/kind/run/code SHA/plan hash，
再核對每檔 hash、來源診斷重算與 baseline/report metadata，才產生 verified snapshot。
ZIP 只讀記憶體，不解壓至路徑；拒絕路徑穿越、symlink、重複項、加密與過大資料。
API bearer token 不跟隨 artifact signed URL；下載限 HTTPS 的 GitHub/Azure artifact
host，無自動重導、無 ambient .netrc／proxy。signed URL、token 不進報告。

## 獨立監督

reconcile 由採樣完成事件、07:05 cron 或既有正式刷新 07:05～07:20 pulse 喚醒，
不呼叫來源抓取器、不取消採樣。期限已過但無證據標 missing，有部分證據標 unmet；
逾期仍執行中的採樣標 unmet，另保留 collection_state=in_progress，不取消它。
手動延遲查核最多回看固定 D1～D7，不延長採樣。
產出 `reconciliation.json` 獨立 artifact，Email／結案與自停交給步驟 03。
目前 mail_due=false、stop=false，不能從本步觸發通知或自停。

上游 REST run 使用 completed 事件當時、經 API 核對的 updated_at 作完成訊號時間，
沒有假設 REST 必定提供 completed_at；若上游已重跑而 metadata 改變則停止。

## SHA 與待核准部署設定

程式 checkout 固定 code_sha；baseline／啟用 plan 從 master 的另一 checkout 讀取。
這避免 plan 裡的 code_sha 指向包含自身 plan 的 commit，造成無法成立的自我引用。
report workflow 另外 sparse checkout config，不需私人日報或 Drive 設定。

部署前才填 experiment_id、start_date、code_sha，以及兩個實際部署 workflow
檔案的 workflow_sha256。workflow 內容有變必須重核指紋；plan 改變也不重置已用名額。
目前 plan.enabled=false、日期與 SHA／指紋皆空；GITHUB_OUTPUT 僅輸出受控欄位，
產物在 runner 的 Downloads，checkout 不寫入。

通知／結案草稿仍保留步驟 03 的接口，但尚無實作；全部 jobs 硬性 false。
尚未驗證真實 GitHub 排程準點、線上 artifact 傳遞或 Email 收件。

## 驗證與下一步

本機離線測試涵蓋端到端主成功、跨 runner 還原、部分來源補試、intent 未上傳、
重複 collect、遺失／過期／篡改 artifact、錯誤 workflow／run／scope、API 失敗、
分頁不全、來源診斷重算、簽名下載不帶 token、時間過窗、D7／缺測監督、CLI 接線。
workflow 草稿另以 actionlint 驗證。完整執行紀錄保存在 Downloads：
`ai-news-radar-tw-source-observation-02-20261021/ACCEPTANCE_REPORT.md`。

實際共 230 項通過（Actions 接線 61、協調器 113、既有來源准入 56），
三支程式 py_compile、兩份草稿 actionlint 及 diff 檢查均通過。這些是本機
離線測試，API／來源請求使用替身；不是線上 GitHub 或七日可靠度實測。

官方 API 依據：[Artifacts](https://docs.github.com/en/rest/actions/artifacts)、
[Workflow runs](https://docs.github.com/en/rest/actions/workflow-runs)、
[workflow_run 事件](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run)。

**下一步 03：每日 Email、通知去重、七日結案與自停。建議 GPT-6.1 Sol
（gpt-6.1-sol）／High。** 模型未自動切換。部署仍須使用者核准。
