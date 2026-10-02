# 本機日報生成與人工校稿

此流程從已保存的 archive、既有譯文快取與健康快照產生 Markdown 草稿及 metadata。
不抓取新聞、不呼叫 LLM、不啟用排程或發布。資料窗口固定為臺北
`[前一天 06:00, 當天 06:00)`，資料時效以輸入快照自己的 as-of 為準。

## 生成

### 本機私人交付：固定遠端資料（O01）

使用者已選擇本機私人交付。新增手動入口，先唯讀解析遠端 master 一次，
再從同一 commit 下載三檔到 Downloads；不 pull、不修改專案 data、不呼叫來源／LLM。
需要專案 Python、系統 `curl` 與 GitHub 公開網路；不需 GitHub token。

```bash
.venv/bin/python scripts/deliver_digest.py --date 2026-10-03
```

期別必填，避免延遲或補跑默默換日。每次下載最多64MiB；連線10秒、傳輸45秒，
外層50秒硬逾時。archive必要；可選檔只有404可略過，其餘下載失敗不假裝缺檔成功。
生成重用現有 composer／pair核對，不改選題、摘要或新聞窗口。

- Exit 0／ready-for-review：archive as-of已達期別截止，非未來，且核對完成時距as-of≤90分鐘。
  即使零題仍可交付；不代表完整 coverage、事實查證或刊出合格。
- Exit 3／review-only：未知as-of、未達截止、過舊或未來，只留診斷草稿，不建立正常期別交付。
- Exit 1：下載／輸入／生成／核對／寫入失敗，或同期程序占用；保留舊成功版本。
- Exit 2：日期／參數錯誤。輸出根目錄必須是 Downloads 下的子目錄。

正常交付：`~/Downloads/ai-news-radar-digests/YYYY-MM-DD/<identity>/`，含MD/meta與
`delivery.json`。原始輸入、SHA、固定source commit、local HEAD與入口模組雜湊、
執行時間／狀態保存在 `.attempts/<attempt-id>/`；交付manifest不加入確定性identity。
入口模組雜湊不是整個依賴環境的可重現保證。目錄700、產物600，僅留本機；
不保證使用者其他備份／同步服務不會同步 Downloads。

同一期用程序鎖序列化；先完整驗證 staging配對，再將新版本目錄rename交付。
既有相同identity只核對，不替換MD/meta、manifest或人類稿；原配對被編輯則報失敗，
請保存人類稿並依核對說明處理，不自動修復覆蓋。不同identity另存版本，不自動替換校稿。
程序中斷可留下未完成attempt，沒有正常交付前不可使用；重新跑即可，鎖由OS釋放。
不提供斷電持久性保證。私人attempt包含原始輸入，不加入Git，也不公開上傳。

確認 exit 0 後，從該版本複製MD為 `review-YYYY-MM-DD.md` 再編輯；保留生成配對。
資料未ready時人工查既有遠端刷新，不自行dispatch可能付費的新聞更新。
目前沒有建立automation；07:15主／08:15備援、09:00檢查與11:30發布仍是下一階段時刻。

### 已保存輸入的離線生成

從專案根目錄使用專案 Python；系統 Python 3.9 不支援本專案的型別功能。

```bash
.venv/bin/python scripts/generate_digest.py \
  --date 2026-10-03 \
  --input-dir /Users/lordmi/Documents/ai-news-radar_zhtw/data \
  --output-dir /Users/lordmi/Downloads/ai-news-radar-digests
```

為了可重現，交付時優先指定已保存的三檔副本目錄。必要檔為 `archive.json`，
可選檔為 `title-zh-cache.json` 與 `source-status.json`；缺 archive 是失敗，合法空 archive
可生成空日。副本可能含私人來源，僅留本機，不加入 Git 或公開上傳。

省略 `--date` 使用臺北當天，即使在 06:00 前也不自動換期；省略 `--output-dir`
寫到 `~/Downloads/ai-news-radar-digests`。`--input-dir` 必填；輸出不能位於輸入目錄樹
或專案 `data/`、`item/`。選題預設 `--limit 20 --same-source-penalty 0.03`，不強湊題數。

## 核對、重跑與失敗

輸出為 `digest-YYYY-MM-DD.md`、`digest-YYYY-MM-DD.meta.json`；先核對再開始校稿。

```bash
.venv/bin/python -c 'from pathlib import Path; from scripts.generate_digest import verify_digest_pair; p=Path("/Users/lordmi/Downloads/ai-news-radar-digests"); d=verify_digest_pair(p/"digest-2026-10-03.md",p/"digest-2026-10-03.meta.json"); print(d["input_identity"])'
```

同三檔 bytes、期別、版本與設定重跑，輸出內容一致；新輸入或版本／設定會產生新版草稿
identity。每檔各自原子替換，兩檔不是交易：若第二檔寫入失敗，第一檔可能已更新。
核對拒絕缺檔、內容被編輯或配對不一致；重新執行完整生成命令，再核對恢復。

Exit 0：成功，包含空日／可選輸入降級；2：日期或參數錯誤；1：必要輸入、建構、
寫入或配對核對失敗。不要只看檔案存在便認定生成完成。

## 校稿與發布副本

保留生成的 MD/meta 配對。另存 `review-YYYY-MM-DD.md` 或其他發布副本後編輯；
人為編輯原 MD 會使 metadata hash 不符。發布副本由人確認，不聲稱仍通過生成配對核對。

校稿時核對期別與輸入 as-of，排除提示詞／教學／廣告等不符合新聞定位的題目；確認
模型版本、日期、金額及供應商歸因，開原文連結核對。來源 refs 可能是同 URL／同出版者
的不同 feed 記錄，數量不是獨立查證次數；Google News URL 可能先經新聞聚合跳轉。

第一版摘要僅來自出版者摘要或既有精確命中的快取譯文；有些摘要只是標題，缺摘要時
明示沒有可用摘要。譯文快取未版本化，並非本輪重新翻譯或查證。不能將來源摘錄／
不完整草稿當成完整採訪、完整正文或完整事實查證。

archive as-of 早於截止時間時，資料可能不完整；來源健康僅為单次觀測。過舊輸入產生
空日，不能據此宣稱當天沒有 AI 新聞。需要新資料時另行處理更新流程，不向窗口外借題。

完整整合驗收與當前進度見 [DIGEST_PLAN](DIGEST_PLAN.md)、[HANDOVER](HANDOVER.md)。
