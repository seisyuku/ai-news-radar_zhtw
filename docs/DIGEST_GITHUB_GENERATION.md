# C08-G：GitHub 靜態日報生成驗證

2026-10-12最新：使用者批准單人Drive交付標準，手動workflow新增預設false的deliver_drive輸入。可在生成與既有pair/rerun核對後選擇私人保存；詳見 [Drive交付操作](DIGEST_GOOGLE_DRIVE_DELIVERY.md)。以下delivery_verified固定false、保存未選定與不含憑證為歷史生成階段；目前未選deliver_drive時仍是純生成。新排程沒有啟用，真GitHub驗收以HANDOVER最新紀錄為準。

更新：2026-10-10。最新使用者確認：日報在 GitHub Actions 生成；Cloudflare 延後到正式私人保存／手機接入，不能阻擋生成工作。專案正本僅本機與 GitHub，不新增正本、遠端或程式檔案 SHA 清冊／比較。

後續使用者選擇先嘗試 [Google Drive校稿與設定](DIGEST_GOOGLE_DRIVE_TRIAL.md)，connector的合成讀寫已通過。
GitHub自動寫入授權尚未配置，以下生成workflow仍只作生成驗證；不因Drive文件建立成功就啟用保存或schedule。

## 本輪完成範圍

- 新增 `scripts/generate_digest_job.py`，只讀已簽出的 `data/` 三檔，不呼叫 GitHub API、新聞刷新、provider、Cloudflare 或 MCP。三檔讀取一次後，以捕獲的 bytes 做獨立重建。
- 新增 `.github/workflows/digest-generation.yml`，名稱 **Daily digest generation check**。僅手動啟動，明確提供期別，不依開始時間猜日期；工作最多10分鐘，序列執行，不取消正在生成的工作。
- 每次生成 `digest-YYYY-MM-DD.md` 與 `.meta.json`，沿用原選題、06:00～06:00窗口、pair核對與相同bytes重跑。保留既有內容完整性核對，不新增版本一致性查驗或追蹤清冊。
- 新入口輸出至 Downloads 下的新私人目錄。拒絕沿用已有目錄、寫入輸入目錄、改寫先前原稿／校稿；中間輸入與重跑稿完成後清除，只留下核對成功的 pair。
- GitHub runner 在 `always()` 步驟清除這次私人產物。此階段沒有選定持久保存位置，不上傳公開 artifact、不 commit 稿件、不發布 Pages。強制終止時仍依 runner 回收，不能保證 cleanup step 一定執行。
- workflow 只裝生成與測試依賴，沒有雲端 SDK 或憑證。既有 news refresh、Pages、驗證 schedule 保持原設定；新workflow檔的push/PR變更納入既有Offline tests路徑。

## 狀態與驗收界線

| 回應 | 意義 |
| --- | --- |
| generated / exit 0 | 當期期別、快照時效、生成、配對及相同bytes重跑通過；只算生成完成 |
| review-only / exit 3 | 已產稿及核對，但快照不足，或明確歷史補驗；不能算當日成功 |
| missed_issue / exit 3 | 開始或核對結束已跨指定期別，不換日期，沒有保存 pair |
| failed / exit 1 | 必要輸入／寫入／配對／重跑失敗；不輸出例外原文 |

`delivery_verified` 固定 false。`generation_timeliness` 是生成核對當下的09:00準時性，**不是私人交付時間**；手動歷史稿標 historical。原90分鐘快照時效規則保持，沒有新增擴散緩衝。

公開 log/Step Summary 只留期別、固定狀態/原因、時效、題數、pair/rerun結果及交付未接通標記，不包含稿件全文、路徑、題目、完整網址或原始exception。來源版本直接由 GitHub 執行畫面的 checkout 版本可追溯，不再另查遠端 SHA。

## 操作與後續

這批變更目前在本機，尚未推送或執行真正 GitHub run。
發布此 workflow 後，可在 Actions → Daily digest generation check → Run workflow，指定臺北期別；補驗舊日期須勾 historical。只能看到安全核對摘要，沒有手機可開的稿件下載連結。

本機可用以下入口檢查；output-dir 必須是 Downloads 下尚不存在的新目錄：

```bash
python scripts/generate_digest_job.py --date YYYY-MM-DD --input-dir data \
  --output-dir "$HOME/Downloads/ai-news-radar-generation/example-run"
```

**目前先試用Google Drive；正式自動保存仍需帳號與寫入授權定案。** 生成能力、雲端持久保存、iPhone登入／校稿分開驗收；不得以生成通過冒充完整雲端日報。

| 待決定項目 | 為何此時需要 |
| --- | --- |
| 保存到哪個私人位置 | 原稿／校稿不能放公開 repo/artifact；要讓 runner 結束後稿件仍存在並可由手機閱讀 |
| 外部觸發的期別證據 | 手動期別已明確；每日自動化須確定排程來源可提供日期／時段，或另選可信發行方式；不因 Cloudflare 尚未選定就假設需要新服務 |
| 正式私人服務／登入 | 只在接通保存及手機操作時處理，不是本輪生成的前置條件 |

不自動新增帳號、私人 repo、Google Drive 檔案、外部排程、通知、付費服務或清理。現成 Google Drive 手機代理驗證只證明手機可使用該文件服務，不代表 GitHub Actions 已有寫入授權或版本控制。

## 本輪交接

- 測試涵蓋真非空產稿、06～06窗口、合法空日、四種時效不足、開始／完成跨日、歷史標記、生成遲到、原稿與輸入保護、有效但不同重跑、損壞配對、例外遮蔽及 CLI／workflow 邊界。
- 直接 CLI 使用 import fence 證明不能匯入 MCP、JWT、crypto 或任何 digest_cloud 模組仍可生成。另一測例拒絕網路及 Git 子程序。
- 新增16項驗收；初輪相關75項通過，完整 **982 passed in 5.40s**。Python編譯、workflow shell/YAML、diff檢查通過。
- 真本機checkout產稿的pair與重跑均通過，但archive as-of為 `2026-10-02T23:35:46.191951Z`，10/10期別資料不足，明確historical／review-only及零題。這不是有效今日稿或GitHub真run證據；本輪不呼叫來源刷新／遠端同步。
- 過程證據：`/Users/lordmi/Downloads/ai-news-radar-github-generation-20261010/`。保留改前文件、改後程式／workflow／文件、測試及交接，不新增SHA清冊。不要做全庫reset。
- 下一階段為保存方式裁決；例行 GitHub 接線沿用 GPT-6.1 Sol／High，身份或保存交易需要另作設計審查時再用 Astra／High。模型建議是任務複雜度分工，不宣稱最新模型排名。
