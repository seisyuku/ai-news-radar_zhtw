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
目前沒有本機automation。使用者已將後續驗證移至GitHub：07:15與08:15跑
獨立生成／時效驗證；見 [GitHub驗證說明](DIGEST_GITHUB_VALIDATION.md)。
GitHub只留安全狀態，不傳草稿到Mac；本機交付／09:00檢查／11:30人工發布仍由人操作。

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
或專案 `data/`、`item/`。第二版選題預設最多10則、`--same-source-penalty 0.03`，不強湊題數。

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

### 第二版自動快訊（2026-10-12）

#### 當期同新聞去重與談論點辨識（2026-10-13）

私人第二版啟用 `current-event-v2`：保存的出版者原文／`publisher_links`若明確連結到本期另一篇
報導，且標題主體與談論點符合，同新聞只占一個選題名額，保留既有選題排名較高的一則
（優先級、分數、同分時固定ID順序），不強制保留被引用原報導。
被移除稿的標題、URL與來源材料保留於私人metadata的`event_group.related_reports`，
不增加代表稿的來源數或分數；`source_count`本來就是來源引用數，不代表獨立查證數。
同公司／產品／事件而談論點不同（如收購與增資選項、軟體與整體科技職缺、
發布與降價／回應），仍各自保留；不建立跨日追蹤或增加讀頁／LLM呼叫。

沒有保存的引用鏈不推定成立：只有出版者名稱、相似主題或不確定材料不觸發引用合併。
另可辨識同出版者重複稿：兩個原文標題須共享引號中的具體產品名、談論點相同，且至少80字元的
原摘要具有至少30種共同相鄰字元組合，覆蓋較短摘要的45%以上。中文產品名可省略AI前綴，
出版者英文文章尾註不參與比對；缺乏材料或不同進展／版本仍保留。此規則不等於通用語意辨識。
去除重複後依既有排序補入下一則，仍最多10則；不新增讀頁、LLM或跨日資料。
既有RSS抓取在同一次HTML解析中保留最多24個文字連結，不增加請求；新快照才能
帶入這個可選字段，歷史純文字快照不補抓網頁。
可於離線CLI提供`--event-citations <私人JSON>`重播使用者已確認的同新聞引用，格式為：

```json
[{"citing_url":"https://example.invalid/derived", "cited_url":"https://example.invalid/original", "basis":"user-confirmed-same-news"}]
```

這是可選的當期證據，不是必需的人工候選池或永久配對規則；兩篇均須是本期
符合選題條件的候選。過期／窗口外URL不補進候選。證據原值入metadata以供離線重建，
私人JSON不提交Git。正常每日入口不需這個檔案，也不會自動載入歷史裁決。
`event_analysis`分別記原符合条件報導數、去重後的選題單位、`cited_duplicates`與`content_duplicates`移除數；
選題單位數不能當作獨立事件數。

預設以 `daily-news-v2` 在固定06～06窗口內自動選最多10則。產業事件與有
具體成本、能力、部署、流程或風險資訊的實用報導共同排序；傳聞／廠商自測
可入選，保留原材料措辭。明顯宣傳、泛泛評論、一般教學與多事件日報索引排除。
不以舊0.72／兩來源門檻擋掉整批候選，不設最低篇數，不輸出人工候選池。

正文只列編號標題、可用摘要與來源連結。沒有摘要就省略，不新增模型寫作或
模板式論點。內部匹配理由與 `selection_diagnostics` 留在私人metadata，
Full表示當期入選，不等於已查證或完整長文。

GitHub日報入口在選題後補讀入選科技新報的原文首段、快取並捕捉摘錄。
重新組裝與核對共用同一捕捉值；失敗時保留標題／連結。
離線CLI只讀既有快照，不會補讀；重播摘錄時可指定
`--article-excerpts <captured-excerpts.json>`。舊政策回放可指定
`--policy existing_daily_brief`，不影響正式第二版預設。

pipeline/render為 `daily-digest-v2`／`markdown-v4`，新政策／摘錄會產生新的
文件identity。舊metadata、原稿與校稿仍可讀取；已保存的期別不自動重寫。

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
