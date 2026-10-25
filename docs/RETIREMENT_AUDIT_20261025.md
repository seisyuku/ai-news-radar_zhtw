# 日報與七日來源實驗取消盤點（2026-10-25）

本頁記錄目前入口與移除相依功能的評估。現行產品範圍依 [README](../README.md)，來源政策依 [SOURCE_COVERAGE](SOURCE_COVERAGE.md)，任務狀態依 [TASK_LEDGER](TASK_LEDGER.md)。

## 取消狀態

| 項目 | 目前可驗狀態 | 結論 |
| --- | --- | --- |
| 私人日報自動生成與驗證 | `digest-generation.yml`、`digest-validation.yml` 在 GitHub 均為 `disabled_manually`；版控中的兩份檔案只剩手動入口與 `if: ${{ false }}`，沒有 cron、`workflow_run` 或 secret 引用。最後 run 分別建立於 10/21 16:09 UTC（skipped）及 10/21 04:42 UTC。私人設定 `automation_enabled=false` 的既有讀回證據見 [D00](DIGEST_RETIREMENT_HANDOFF_20261021.md)；本次未重新讀私人設定。 | 已取消自動化。 |
| 七日來源觀察與報告 | `tw-source-observation.yml`、`tw-source-report.yml` 在 GitHub 均為 `disabled_manually`；`config/tw-source-observation.json` 頂層 `enabled=false`。最後 run 都建立於 10/22 04:36 UTC，均 skipped。 | 已提前停止，不補 D7／D8 或結案信。 |
| 一次性來源 SMTP 驗證 | `tw-source-mail-check.yml` 為 `disabled_manually`，最後一次是 10/21 17:34 UTC 的手動 run。 | 無自動寄信入口。 |
| CyberQ／AlphaLab 七日回放 | `evaluate_tw_source_admission.py --replay` 是明確指定離線檔案才執行的評估模式；沒有 GitHub cron 或正式刷新入口。先前七日樣本只作來源評估。 | 無待取消排程；不列入接入驗收規格。 |
| Codex 本機自動化 | `/Users/lordmi/.codex/automations/` 沒有 `automation.toml`。 | 未找到相符的 Codex 排程。 |

以上 GitHub 狀態與最近 run 在 2026-10-25 查詢；只代表查詢時狀態，不以近期 run 清單替代 D00／A01 的停用證據。GitHub 仍保留五份停用 workflow 的歷史身分；目前不需要以刪除 workflow、歷史 artifact 或私人稿件才能達成取消。

## 相依功能移除評估

| 元件 | 現行相依與風險 | 裁決 |
| --- | --- | --- |
| 私人日報生成、Drive 派送、雲端校稿程式與其測試 | `scripts/digest_*`、`generate_digest*`、`validate_digest.py`、`deliver_digest.py` 沒有被正式刷新 `update_news.py` 或網站 JS 匯入；但彼此、手動合成契約 workflow 與離線測試相依，且仍是使用者臨時要求產文時可參考的研究／工具。整組移除對公開網站的執行路徑低風險，對人工工作能力及歷史驗證為實質功能損失。 | 不隨取消排程直接刪碼。若另案確定不再需要人工產文工具，應整組清理入口、測試、手動契約 workflow 與文件，跑完整 Python 回歸。 |
| 七日來源觀察、報告、SMTP adapter 與設定 | `observe_tw_sources.py`、`tw_source_*`、停用設定及 `docs/examples/tw-source-*` 自成一組，離線測試仍引用範例和七日結案契約。正式刷新不匯入此組。刪除對公開網站低風險，但會失去重驗舊 artifact 的工具與測試證據；單刪範例會讓測試失敗。 | 可在獨立清理變更中整組移除，先保存歷史證據及調整測試與文件引用；本次保留已停用狀態。 |
| `candidate_feed_admission.py` 與來源限定規則 | 正式 `update_news.py` 已匯入，供 CyberQ／AlphaLab RSS 收件；名稱含 admission，但已是現行生產依賴。 | 不可當七日回放殘留刪除。 |
| `evaluate_tw_source_admission.py --replay` | 手動離線診斷，不在排程；可用於來源變更查核，與 24 小時讀者窗口分離。 | 停止將七日回放列為接入驗收即可；沒有必要刪掉通用離線評估能力。 |
| 公開 `daily-brief.json`、每日刷新、Pages、watchdog | 正式網站使用，與私人日報自動交付不同。 | 保留；全站讀者可見時間維持滾動 24 小時。 |
| 七日模型生命週期與 14 日品質評估方向 | [ROADMAP](ROADMAP.md) 的 T02／T05 是不同議題，不是已撤回的七日來源觀察或 CyberQ／AlphaLab 回放。 | 本次不擴及這些方向。 |

## 文件處置

現行 [OPERATIONS](OPERATIONS.md) 已移除過時的私人日報排程、登入及派送操作段落；[DIGEST_USAGE](DIGEST_USAGE.md) 及舊 Drive／O01 文件已明示日常驗證與三日驗收退役。[TASK_LEDGER](TASK_LEDGER.md)、[SOURCE_COVERAGE](SOURCE_COVERAGE.md) 與[舊影子評估](TW_SOURCE_ADMISSION.md)已區分 A03 當時封存的 `shadow/cyberq` 和 2026-10-25 另行接入的 `tw_media/cyberq` 官方 RSS。舊階段文件、七日樣本與 artifact 保留作歷史證據；其中的「下一步」「待驗」不能重啟已取消的工作。此次沒有更動正式收件、排序、24 小時窗口或發布排程。
