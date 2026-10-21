# 步驟 01：觸發與補試協調器（本機實作，未部署）

使用者以「執行01」核准本步建置。七天自動觀察的部署仍待另外核准。
後續已依「執行02」建置 [Actions adapter](TW_SOURCE_OBSERVATION_02.md)；
下列介面責任是步驟01完成時的交接，當前進度以[步驟03](TW_SOURCE_OBSERVATION_03.md)與HANDOVER為準。
本步提供 `scripts/tw_source_observation.py`，純標準函式庫、無網路存取，
不匯入正式生成器、私人日報或來源抓取器。不建立正式 workflow、不寄 Email。

## 已實作的判定

- 臺北 06:00 ≤ 主開工 < 06:30；06:30 ≤ 補開工 < 06:50。
  排程、手動與既有刷新完成 pulse 均檢查實際開工時間，過窗不追抓。
- 自開始日期固定七個日曆日；D8 禁止採樣。事件建立日期、上游完成日期及
  執行日期一致，不接受跨日重跑。延遲的主排程不能自動變成補排程。
- 只接受自身 repo／master；pulse 上游必須是 `Update AI News Snapshot`，
  原事件為 schedule 或 workflow_dispatch。上游失敗亦可喚醒，不能當新 baseline。
- 主已完成就跳過；主仍執行就等待後續序列化重查；主僅剩 intent 可用補 slot
  恢復，但同 slot 不可重取名額。沒有第三個採樣 slot 或 force／日期回填入口。
- 合格部分結果與原 retrieved_at 沿用，只重試暫時錯誤／缺少的來源。
  robots、403、付費牆、無原生 feed、跨 host 轉址等終態不當日重試。
- 缺少／過舊 baseline 可單獨補讀，不必重抓來源。完整結果按完成當時的
  baseline 年齡判定；恢復部分結果時，baseline 須在補試時仍不超過兩小時。
- 成功需要五站診斷完整、至少一站成功解析、其他為成功或已知終態限制，
  且 baseline 合格。有效空 feed 算成功；全部失效、缺測與部分完成不算成功。
- 歷史不可讀、作用域不符、驗證失敗、重複 slot、並發重疊、異常時間／來源
  證據均 blocked，不能冒充空歷史重新採樣。

## 介面與下一步接線責任

`decide(plan, context, history, now)` 回傳 `skip`、`blocked` 或
`prepare_attempt`。後者只是決策，不會抓來源；`claim_required=true` 表示
呼叫端仍須先確認 durable intent 成功保存。`assess` 合併主補證據，保留原來源
時間與 slot，回傳 complete／partial／missing／in_progress／unmet。
期限缺測通知與每日回報由步驟 02／03 的獨立監督器處理。

`context` 是未來 adapter 從當前 Actions run API 與原事件正規化的 metadata，
不可從 workflow_dispatch inputs 任意覆寫。包含 repository、branch、run_id、
created_at、event_name、schedule；pulse 額外含 action、workflow_run 的 id、
name、repository、branch、event、conclusion、created_at、completed_at。

`history` 必須包含 available、experiment_id、date、plan_hash、attempts。
attempts 每 slot 至多一筆，state 為 intent／running／finished；finished 證據
包含 started_at、finished_at、verified、sources 及 baseline_at。
sources 只記該 slot 新抓到的診斷，不重複嵌入沿用來源；來源具 status、
retrieved_at、evidence_sha256，解析成功另有 item_count（0～50）。

**verified 是已完成驗證的介面契約，不是檔案簽章。** 步驟 02 必須從同實驗的
不可變 artifact 驗證來源 run／SHA、manifest、實際檔案 hash 與 schema，
確認當前執行狀態，再提供此 snapshot；不能只信任下載 JSON 自稱 verified。
plan_hash 鎖定同一計畫；設定漂移必須停止，不能重置每日名額。

`LocalIntentStore` 是本機原子 claim 參考實作，以 exclusive create、fsync
保存名額；I/O 失敗不授權抓取，遺留未知 marker 不覆寫。它不能跨 GitHub runner
提供持久性。步驟 02 仍須串行化、重讀歷史、上傳 intent artifact 確認成功後
才接抓取器。沒有宣稱 HTTP exactly-once；主抓完但未保存時，補 slot 可能重抓。

## 離線執行

CLI 只接受明確 `--simulate`，讀取含 plan／context／history／now 的 scenario，
將決策輸出至 stdout；blocked 回傳 exit 2。沒有 collect、deploy、寄信指令。
完整 scenario 與真實執行紀錄放在 Downloads 的本步驗收目錄：
`ai-news-radar-tw-source-observation-01-20261021/`。

```bash
.venv/bin/python scripts/tw_source_observation.py --simulate \
  --scenario /Users/lordmi/Downloads/ai-news-radar-tw-source-observation-01-20261021/scenarios/primary.json
.venv/bin/python -m pytest -q tests/test_tw_source_observation.py tests/test_tw_source_admission.py
```

本步實際驗收 166 項離線測試通過（新協調器 110、既有來源准入 56），另執行
9 組 CLI 情境。py_compile、diff 檢查通過，7470 個既有正式檔案 hash 未變。
完整執行紀錄見上述 Downloads 目錄的 `ACCEPTANCE_REPORT.md`。

本步不等於 GitHub artifact 持久化、線上補觸發、Email 投遞或七日觀察驗收。
目前兩份 workflow 草稿仍位於 docs、jobs 硬性 false；計畫 disabled、日期與 SHA
留空。本機測試用啟用計畫僅存在測試與 Downloads scenario。

**步驟 01 完成後，下一步 02 建議：GPT-6.1 Sol（gpt-6.1-sol）／High。**
下一步接既有 pulse、Actions artifact 歷史及獨立採樣／監督架構，仍先本機驗收，
不因本步通過就部署。模型名稱是建議，沒有自動切換模型或建立其他 agent。
