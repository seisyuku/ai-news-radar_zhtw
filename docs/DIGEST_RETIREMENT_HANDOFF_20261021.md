# 日報自動化退役交接（D00，2026-10-21）

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：D00已完成／退役交接歷史。** S03已完成外部停用及封存發布；本頁下方的部署前順序是當時交接，不是未執行任務。現況依[PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)及OPERATIONS，不恢復日報自動化。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

## 最新決策與執行狀態

使用者撤回每日自動產生、自動派送與排程目標。日報改為在Web Chat專案中，
由使用者發起要求收集題目／產生文檔，性質同過去「第一階段」收集題目。
不另建替代排程或自動文檔系統。保留過往選題研究，供明確人工要求時參考。

**2026-10-22 S03已完成外部停用與封存推送。** 兩份workflow均讀回disabled_manually、
無在途run，私人automation_enabled已false讀回；只改該欄且保留稿件／其他設定。
封存提交`7b2f8e1f256f`已推送master，移除自動觸發，手動dispatch也以false job
跳過，沒有生成／交付或secret引用。CI／Pages及一次性公開刷新／發布讀回成功，
停用後兩個日報workflow零新增run，D00驗收完成；證據見
[S03狀態](SOURCE_GOVERNANCE_S03_STATUS_20261022.md)。S01的夜間skipped為歷史紀錄。

上層順序：[來源治理計畫](SOURCE_GOVERNANCE_PLAN_20261021.md)。S02備妥最小差異，
D00優先獨立執行；S03啟用來源觀察前須完成退役驗收。S01／S02僅本機，S03依
使用者指令執行外部停用／設定及推送；沒有刪除歷史稿件或secret。

## 必須涵蓋的入口

| 位置 | 現有行為 | 退役動作／驗收 |
| --- | --- | --- |
| `.github/workflows/digest-generation.yml` | 監聽`Update AI News Snapshot`完成；上午符合條件時呼叫`digest_daily_job.py`並可保存Drive；另有手動生成／派送入口。 | 移除自動`workflow_run`觸發並停用專用workflow，避免未來刷新持續產生skipped紀錄。新日報以Web Chat要求為入口，GitHub手動生成不再是預設流程；既有手動入口保留封存或移除須在最小差異中明列。 |
| `.github/workflows/digest-validation.yml` | 臺北07:15／08:15兩個cron，執行測試及當期生成核對。 | 移除兩個cron並停用專用workflow；不得保留每日驗證來持續負擔已撤回的目標。 |
| Drive日報設定Doc | `automation_enabled`是日報job的執行開關；設定false仍不能防止上游觸發／runner前置作業。 | 讀回並改false，限此欄、保留其他資料、核對寫後值；真ID／URL只存私人交接。兩個workflow關閉也須獨立驗證。 |
| 已排隊／執行中的專用run | 關閉未來觸發不一定停止既有run。 | 列出實際狀態；必要時僅取消兩個專用workflow的run，再查有無部分保存。保留既有原稿、校稿及receipt，不重送或刪檔。 |
| `.github/workflows/digest-cloud-contract.yml` | 僅手動、合成驗收，沒有cron或真交付。 | 非每日負荷來源，先保留為歷史手動檢查；不擴大成新自動化。 |
| `offline-tests.yml`與既有digest測試 | 程式變更時的離線回歸，可涵蓋共用函式與舊資料契約。 | 保留必要測試，不把一般CI誤當每日交付排程全部刪除；依退役差異調整有關workflow斷言。 |
| `digest_daily_job.py`、生成／Drive／補讀模組 | 舊自動化及手動工具；部分依賴與公共生成共享。 | 首批以停止入口／執行為目標；先查引用再決定封存或後續刪碼，不為停用重寫整套系統。 |
| 日報專用secret／OAuth／私人設定 | 歷史部署使用`GOOGLE_DRIVE_OAUTH_CREDENTIALS`與`GOOGLE_DRIVE_DIGEST_TARGET`；本次未讀值。 | 停用後盤點是否仍有依賴，再提出專用憑證清理；不自動刪除帳號、Drive外掛授權或其他專案共用憑證。 |

## 執行順序與完成證據

1. 保存開始時HEAD、diff、兩個專用workflow／run狀態及私人設定的安全摘要。
2. 先準備移除自動觸發的本機差異與聚焦驗收，再依當次授權完成推送／外部停用。
   外部停用可先阻止下一次觸發；不能只改本機文件就稱線上已關閉。
3. 私人開關false、專用workflow停用、既有run處置分別讀回；若某項無法存取，
   列明缺項與已完成的防線，不阻擋可獨立完成的停用工作，也不冒稱全部成功。
4. 核對後續一次公開刷新正常、沒有新增日報自動接續執行；核對兩個驗證cron
   已由版本差異移除。必要時觀察原觸發時段，但不為驗收再觸發生成或派送。
5. 保存版本／API／run證據與未知事項，更新HANDOVER、OPERATIONS及ROADMAP。
   日報三日自動交付驗收取消，不繼續追求補齊成功次數。

## 受保護範圍

- 保留Radar的`update-news.yml`、`watchdog.yml`、外部heartbeat及Pages發布。
- 保留公開`data/daily-brief.json`、`brief_selection`、六類重點訊號、RSS摘要
  與公開翻譯；名稱含daily／brief不代表私人日報。
- 保留已產生的私人稿件、校稿、Drive資料夾及本機選題研究；退役不授權刪除。
- D00不修改來源七日觀察未部署草稿；S02另行修補觀察程式，Email仍是觀察報告。

## 後續人工工作

使用者在Web Chat專案提出當次需求後，依指定日期、範圍與輸出方式收集題目／
生成文檔。過去樣本只作參考，不能自動套用為永久權重、固定題數或每日工作。
S01未讀該Web Chat過去完整對話，不臆造「第一階段」的欄位與固定提示詞。
研究材料索引保留在[DIGEST_EDITORIAL_HANDOFF](DIGEST_EDITORIAL_HANDOFF_20261018.md)。

S02已完成本機差異與完整1495項回歸，詳見[S02審查](SOURCE_GOVERNANCE_S02_REVIEW_20261021.md)。
S03外部停用／私人開關／推送及公開刷新後讀回已完成，D00結案；不重做停用或重新
啟用。來源觀察啟用條件另見S03狀態。建議GPT-6.1 Sol／High。
