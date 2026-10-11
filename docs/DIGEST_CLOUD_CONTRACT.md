# 私人雲端日報 C02：離線模擬契約 v1

## 2026-10-12 已批准：GitHub + 私人Drive單人交付標準

使用者明確許可簡化本路線的C02控制層要求。以下單人Drive標準優先於本文件歷史v1的不可變儲存／原子交易／request receipt／服務端revision控制要求；既有mock與候選runtime保留為歷史試驗，不能再作Drive接線前置。

- GitHub生成，私人Drive保存原始MD/meta bytes、native可讀原稿與獨立校稿副本。沿用既有pair完整性與生成重跑，不新增code/remote SHA核對。
- 程序只建立或讀取既有檔案，不更新已保存原稿或人工校稿。相同mode/issue/base重送沿用檔案；同一期不同base停止為existing_issue_conflict，不自動換稿。歷史與當期保存位置分開。
- 原始pair保存讀回及native原稿/新副本內容核對成功後標delivery_verified；既有人工副本不要求等同原稿。目的地及文件metadata須owner-only。保存中途可能留下部分文件，不宣稱跨檔原子交易，失敗不能標完成，也不自動刪檔。
- owner仍能手動修改Drive原稿；程式不覆寫不等於儲存層不可變。既有原稿讀回不符停止；GitHub concurrency僅序列化本workflow，不宣稱全域分散式互斥或完整編輯revision交易。
- 臺北06～06、明確期別、跨日拒絕、既有90分鐘快照時效、生成與保存時效分開保持。保存完成時間是runner觀測，不宣稱交易服務可信提交時鐘。historical不算每日成功。
- 設定僅已同意欄位；自由文字不當指令、網址或憑證。這輪只接手動workflow，deliver_drive預設false；不启每日排程/通知/發布/清理，也不改既有新聞刷新與公開站。

使用者已確認新app校稿副本在iPhone正常。2026-10-12 OAuth已為External／In production並重新授權，GitHub新憑證歷史交付通過；每日觸發與本路線期別發行簡化仍待[提案裁決](DIGEST_DAILY_TRIGGER_PROPOSAL.md)，下文持久intent issuer沒有被默默取消。

## 2026-10-10 最新適用範圍

使用者確認：生成在GitHub Actions；Cloudflare僅正式私人保存／手機入口候選，不是生成前置。
目前優先入口為 [C08-G GitHub生成驗證](DIGEST_GITHUB_GENERATION.md)。手動明確期別、直接讀checkout、
產生MD/meta及核對，沒有正式交付與外部每日排程。下文持久intent issuer、原子delivery/revision、
OAuth及雲端adapter要求仍適用於**正式自動私人交付**，不要求手動生成驗證先建立這些服務。
生成回`delivery_verified=false`；不能用此階段放寬正式三日交付標準或宣稱手機可用。
不新增正本／遠端SHA核對或程式雜湊清冊；原有稿件identity、pair完整性及重跑規則保留。

後續 [C08-D Google Drive校稿／設定合成試用](DIGEST_GOOGLE_DRIVE_TRIAL.md)完成connector讀寫與副本保存。
它不是C02控制層：Google Docs revision guard不替代專案request receipt、不可變原稿及原子交付。
設定文件只作合成保存，不直接執行；正式GitHub授權與是否需調整交付adapter仍須具體確認。

更新：2026-10-10。狀態：六項設計審查及 C03～C08 本機模擬／接入試驗完成；
持久交易已在本機 runtime 驗證，仍無正式雲端服務、真手機登入或遠端驗收。
本契約優先於提案內關於日期、manifest、狀態的候選文字；不改既有本機或 GitHub 驗證流程。
授權：本機實作、設計審查與自動續行。C01a 現成外掛的手機代理查核及 C07 設計審查已完成，
正式私人接入階段再處理 [C09 帳號、預算與身份配置](DIGEST_CLOUD_DEPLOYMENT_GATE.md)；C01b 自建工具與 C07 線上驗收仍待完成。
接入邊界、任務細分及實機驗收次序以 [C07 審查](DIGEST_CLOUD_C07_REVIEW.md) 為準，
本文件的原稿身份、版本、去重、固定期別及交付契約繼續適用。
平台、正式部署、排程、通知、清理均另案。

## 1. 固定期別、請求與嘗試

- `issue_date` 必填，合法 YYYY-MM-DD；唯一時區 Asia/Taipei，窗口由
  `window_for_date(issue_date)` 推導，固定 [前日06:00, 當日06:00)。不得由 runner 開始時間補日期。
- 定時請求必須來自受信任的期別發行端，包含 `scheduled_for`、`issued_at`、`request_id`；
  `scheduled_for` 必須是該期臺北07:15、08:15或08:45，`issued_at` 在該時段起15分鐘內。
  這些時間是發行端的證據，不接受匿名或一般編輯客戶端自行宣稱。
- 發行端先持久化意圖再觸發 Actions。傳輸重送沿用完整意圖；工作只按 request_id 取可信意圖。
  GitHub created_at、外部 HTTP 接受與工作 started_at 都只是觀測，不能代替 scheduled_for。
- **靜態 cron 直接 dispatch、沒有可信日期意圖的路徑不符合本契約。** C01/C08 須證明
  排程服務能提供可信日期，或設計有持久意圖的發行端；不能默默依接收日期猜測。
  若因此需要新服務或費用，列出具體方案再裁決；C03 僅注入模擬意圖。
- 自動工作開始與最終交付時，服務端臺北日期都必須等於 issue_date；跨日記
  `missed_issue`，不自動改期，也不讓失敗清掉已成功稿。
- 人工補驗歷史日必須 `mode=manual_historical`、明確日期及維護者授權；標為歷史審閱，
  不計每日準時驗收。當期人工重試 `mode=manual_current`，同樣不新增新聞刷新。
- 三個定時 slot 每期各最多一個邏輯 attempt。相同 request 重送不新增 attempt；新 slot
  可以選新來源 commit。每個 attempt 一旦固定 source commit，恢復時不得换 commit。
  C03/C08 每個 attempt 最多3次執行、每次工作上限10分鐘；每項 I/O 最多3次、
  重試間隔1/2秒，且受工作期限限制。當期人工重試另限最多3個邏輯 attempt。
- 定時 guard 若已有合格交付只核對並回傳；已有校稿不自動更新基底。
- 2026-10-10 C08澄清：有剩餘execution的暫時I/O錯誤仍是running，保留reason作恢復；
  只有額度耗盡／永久拒絕／跨日才寫終態。終態不能改回running。volatile生成開始時間
  不作去重payload的一部分；固定意圖/commit/bytes仍必須相同。提交時檢查當前execution租約。

## 2. 原稿身份與題號

- `base_identity` 原樣使用既有 `document_identity`／`input_identity`（64位小寫十六進位）。
  它涵蓋版本、設定、輸入描述和生成內容；source commit 單獨記錄，不能取代身份。
- 原稿 MD/meta 保留既有 bytes 與 identity 規則；時間、雲端 key、人工修改不塞入原稿 metadata。
- 同 identity 的 MD/meta 若 bytes 不同，一律 `immutable_conflict`，不得覆寫或偷偷換身份。
- 題目身份為 `(base_identity, story_id)`。story_id 是原稿內非空且唯一的字串，
  不要求 hex，不拿原始 story_id 拼儲存路徑；不同 base 不自動配對或移轉校稿。
- revision 0 含原稿全部題目與順序；人工稿保存完整 ordered story_id、每題 included、
  title_override/summary_override（null代表沿用原稿，空字串代表明確清空）。
  不允許改來源 URL、原始證據或原稿 verification；本階段不新增題目。
- 顯示回應附 `base_identity`、`revision`、1起算題號→story_id映射。
  語音選題須以使用者正在指涉的映射轉成 IDs；重排後舊題號不能套用新映射。
  無映射或指涉不清時要求澄清；伺服端只收 IDs 和 expected_revision。
- 不同 base 可保存為獨立候選；`selected_base` 一旦有值只准維護者明確 CAS 選版。
  選版不複製舊編輯；每個 base 的完整 revision 歷史保留。

## 3. 不可變物件與原子交付

決策：分成不可變物件層與具交易能力的控制層。單純「最後上傳 manifest」不足以通過。

1. 原稿兩檔各 `put_if_absent`；已存在時比較長度和SHA256，不同即拒絕。
2. 從儲存讀回兩檔，再呼叫既有 `verify_digest_pair`；第二次獨立生成須 bytes 完全相同。
3. 控制層在同一原子交易中核對 issue/CAS、服務端提交時鐘及時效，寫 delivery receipt、
   attempt terminal result、request receipt；必要時建立 revision 0 和首次 selected_base。
4. 交易提交是交付成立點。只有交易已提交且物件核對完整的版本能供讀取；讀取若發現
   缺檔或損壞，回 `integrity_error`，不回草稿或宣稱 ready，不覆寫歷史交付證據。

控制層必須提供線性一致讀取與條件交易；若供應商只有單 key CAS，需把同 issue 的
原子狀態放同一控制紀錄，或另提供交易儲存。不能用本機 flock 冒充分散式互斥。
物件不可被同權限外部程序覆寫；意外刪除仍以讀取時完整性檢查發現。

併發同 base：共用不可變物件、每個 request 有自己的結果，不重建 revision 0。
併發不同 base：第一筆合格交易可首次選版；後者僅登記候選，不能覆蓋 selected_base。
review-only 版本可私人讀取及編輯，但不搶首次合格交付的預設選版；明確指定 base 才操作。
第二檔、讀回或控制交易失敗：沒有成功 receipt；已上傳物件保留供有界恢復，不自動清理。
交易已成功但回應遺失：重送先查 request receipt，回原結果；不重新判定或重建版本。

## 4. revision 與編輯交易

- revision 採非負整數（0起），另存 content_sha256。hash 是內容核對，不作順序或鎖。
- 編輯請求包含 request_id、issue_date、base_identity、expected_revision、operation。
  operation 僅 `patch` 或 `restore`；patch 可改排序、included、標題、摘要；restore 指定
  同 base 的既有 revision。整批修改全成或全敗，不做部分成功。
- 原子交易順序：驗證身份/權限 → 查 idempotency receipt → 核對 base與expected_revision
  → 驗證所有題目與完整新內容 → 同時寫不可變新revision、current pointer、request receipt。
- 去重範圍為 `(principal, operation_family, issue_date, request_id)`；payload 用 canonical_json
  算hash。同ID同payload回原結果（即使之後又有新版本）；同ID不同payload拒絕
  `idempotency_conflict`。尚在處理回 `in_progress`，不再次執行。
- revision 不符回 `revision_conflict` 及目前版本，不自動合併。客戶端讀回後以新的
  request_id、expected_revision重新送出；不得改寫舊request內容。
- 無變更保存成功但不增revision，仍原子記錄receipt。restore產生新的遞增revision，
  不把current倒退；若還原內容已相同則視為無變更。
- 永久 validation/conflict結果記receipt；基礎設施失敗而交易未提交可以重試。
  receipt與版本保留至另行核准清理；無TTL導致遲到重送重複生效。
- 回應含 applied_revision、current_revision、content_sha256、replayed；客戶端按 applied_revision
  讀回核對，再另讀current，避免把舊成功回應誤稱為目前內容。

## 5. 時效、完整性與準時分開

attempt狀態：pending → running → committed / failed / missed_issue；terminal不可倒退。
交付 `quality`：ready-for-review / review-only。
交付 `timeliness`：on_time / late / historical。
讀取 `integrity`：verified / integrity_error（屬當次讀取結果，不改歷史receipt）。

提交時以控制層可信時鐘 `committed_at` 調用既有 readiness(as_of, window, now)：
as_of未知、未來、早於06:00截止、或age>90分鐘均review-only；恰90分鐘合格。
`now` 必须在交易成立點取得；上傳前的checked_at只作診斷。服務若不能提供這種
原子時效裁決，不符合adapter契約，不可用客戶端寫入前的時鐘冒充。

`deadline_at` 為該期臺北09:00；committed_at <= deadline 才on_time，超過即late。
每日驗收必須同時 quality=ready-for-review、timeliness=on_time、完整性通過。
review-only即使準時保存也不算成功。歷史人工稿一律historical。
日後閱讀不因經過90分鐘把已合格日報變成失敗；保留「交付當時」判定與資料時間。
最新attempt失敗不掩蓋先前合格交付；查詢同時回當期可用稿、最新attempt與是否達標。
零題沿用既有健康/coverage診斷；新鮮零題可以合格，僅說「本次選題零則」，不推論沒有新聞。
09:00沒有合格交付時查詢顯示未達標；通知另待核准，不要求此時有人操作。

## 6. 最小資料格式與安全邊界

新增紀錄 `schema_version=1`；嚴格拒絕未知欄位、未知enum、NaN、重複JSON keys、
錯型別（bool不當整數）、超限內容。舊原稿metadata依原契約驗證，不用新白名單刪欄位。
時戳線上格式UTC RFC3339 `Z`，最多6位小數；日期嚴格驗證。外來時戳與服務端時間分開。
request_id採UUID；source_commit為40位小寫hex；SHA256為64位小寫hex。

| 紀錄 | v1 必要欄位（除注明nullable皆必填） |
| --- | --- |
| Intent | schema_version, request_id, issue_date, mode, scheduled_for(nullable僅manual), issued_at, issuer_id；C03模擬可信來源另附owner_authorized布林，正式服務由身分驗證產生，不收客戶端自述 |
| Attempt | schema_version, attempt_id(UUID), request_id, issue_date, state, execution_count, source_commit(nullable直到固定), started_at(nullable), finished_at(nullable), reason_code(nullable) |
| Delivery receipt | schema_version, delivery_id(UUID), attempt_id, request_id, issue_date, base_identity, source_commit, input_sha256(固定三個檔名→hash或null), objects(md/meta各key/sha256/size), archive_as_of(nullable), pair_verified(true), rerun_identical(true), checked_at, committed_at, deadline_at, quality, reason_code, timeliness |
| Issue control | schema_version, issue_date, control_version(遞增), selected_base(nullable), delivery_ids, attempt_ids, review_heads(base→revision) |
| Review revision | schema_version, issue_date, base_identity, revision, parent_revision(nullable僅0), content_sha256, content(ordered_story_ids, entries: story_id→included/title_override/summary_override), actor_id, created_at, request_id(nullable僅初始化) |
| Request receipt | schema_version, principal, operation_family, issue_date, request_id, payload_sha256, result_code, result, committed_at |

input_sha256的null只代表原有可選檔缺失；archive缺失必失敗。壞的可選檔沿用既有降級診斷，
仍記實際bytes hash。三檔必來自同一固定commit；本機fixture commit僅為宣告，無法證明GitHub來源。
objects.key只准服務端生成，客戶端不能傳路徑或URL。內容hash使用既有canonical_json。
Review的content_sha256只涵蓋ordered_story_ids和entries；ID集合必與原稿候選一致，排序不得重複。
最多20題（沿用預設生成limit）；每標題4096字元、摘要32768字元、request UTF-8上限1MiB。
超限回 `payload_limit`，不截斷原稿或人工內容；C03生成超限原稿時明確失敗，不悄悄刪題。

reason_code封閉集合：既有readiness五種archive代碼，加 invalid_request、unauthorized、
missed_issue、immutable_conflict、integrity_error、revision_conflict、idempotency_conflict、
unknown_story、base_mismatch、payload_limit、generation_failed、storage_failed、attempt_limit、
in_progress、already_delivered、applied、no_change。內部例外不原樣公開。
attempt failed與API拒絕是不同結果；未接受intent的拒絕不建立attempt。

只提供 status/read/edit/retry；校稿角色不能寫原稿、改排程、執行shell或新增provider呼叫。
所有讀寫先驗證owner與物件歸屬；mock以注入principal驗證授權流程，不宣稱完成OAuth。
公開摘要白名單僅issue_date、固定狀態/原因、commit、as_of、count、pair/rerun布林；
用白名單重新建立回應，不序列化private exceptions、任意payload、路徑、網址或稿件內容。
模擬測試禁止所有非loopback socket連線與網路子程序，資料限合成fixture；不讀私人既有稿。

## C03～C05 接口責任

- C03 `prepare_generation(intent, pinned_inputs, clock, workspace) -> PreparedPair`：
  檢驗意圖/期別、三檔manifest與hash、build/write/verify、獨立重跑比對，回不可變bytes及來源證據。
  pinned_inputs提供commit與固定三檔bytes/null；不fetch。workspace只在指定Downloads測試目錄。
  `PreparedPair`不是交付成功；沒有storage就不能回ready。保留deliver_digest.main的Downloads保護。
- C04 `store.put_if_absent/get`；`MockDeliveryService.commit_delivery(prepared, request, expected_control_version)`：
  原子裁決clock/readiness/去重/選版/receipt。mock以可控clock、故障點及併發屏障證明行為。
  `get_issue`、`read_base`每次檢驗引用；不暴露孤立物件為成功稿。
- C05 `apply_edit(principal, request)`、`read_review(base, revision=None)`、
  `select_base(expected_control_version, base)`、`export_review(base, revision)`。
  匯出指定不可變revision，附base/revision/hash；還原透過apply_edit，所有狀態修改需request_id。
- C03不提前實作真provider、API登入、排程或C04交易引擎。C04 adapter須先通過下列故障矩陣，
  才能用於C05；真雲端必須重跑能力驗證，mock鎖不能當作雲端證據。

## 驗收 fixture matrix（C03～C05 適用子集已有本機測試）

共通：D=2026-10-09、時區Taipei；窗口UTC [10/7 22:00Z,10/8 22:00Z)，deadline=10/9 01:00Z。
基準archive_as_of=10/9 00:30Z，commit時刻00:45Z；合成兩題story_id="story/a"、"legacy-2"。
下列時間未注明日期者皆D的UTC。每例須斷言回應與持久狀態，不能只檢查exception。

| ID / 階段 | 輸入或故障 | 必須結果 |
| --- | --- | --- |
| F01 C03 | D固定日期 | 精確上述半開窗口；start收錄、end不收錄 |
| F02 C03 | 缺日期/naive時間/錯時區/未知欄位 | invalid_request；零輸出 |
| F03 C03 | 07:15 slot對應前日23:15Z，合法意圖；run晚建 | 仍為D，不依run建立改期 |
| F04 C03/C04 | 開始或提交已達D+1臺北00:00 | missed_issue；舊稿/選版不變 |
| F05 C03 | 未授權historical；合法owner歷史D | 前者拒絕；後者明確historical、不計準時 |
| F06 C03 | 靜態dispatch無可信意圖、偽造issuer | 拒絕，不補當日日期 |
| F07 C03 | 同輸入與設定生成兩次 | MD/meta完全同bytes、identity相同 |
| F08 C03 | 改設定或版本 | 新identity，原稿bytes不变 |
| F09 C03 | archive缺失、hash不符、混commit | 失敗；無PreparedPair成功值 |
| F10 C03 | 可選檔缺失/壞JSON | 沿用降級診斷、記null/真hash，不冒充完整coverage |
| F11 C04 | 正常提交兩題；合法新鮮零題 | 合格交付，0亦明確保留coverage限制 |
| F12 C04 | 上傳前age89分，提交age90分+1微秒 | review-only/archive_stale；不計成功 |
| F13 C04 | 提交恰age90分；再加1微秒 | 前者ready，後者review-only |
| F14 C04 | as_of未來/未知/早於窗口截止 | 對應既有reason，review-only，不報沒新聞 |
| F15 C04 | 提交01:00Z / 01:00:00.000001Z，仍新鮮 | 分別on_time / late |
| F16 C04 | 07:15開始09:01完成、已過舊 | review-only且late，兩軸均呈現 |
| F17 C04 | 第二物件寫入失敗 | 無delivery receipt；恢復可沿用首檔 |
| F18 C04 | pair讀回hash錯、manifest交易失敗 | 不可讀為ready，舊selected保留 |
| F19 C04 | 已存在key bytes不同 | immutable_conflict，不覆寫 |
| F20 C04 | 兩runner同base併發 | 一份revision0；成功去重，無丟失receipt |
| F21 C04 | 兩runner不同base併發 | 僅首次選版；第二候選不改人工稿 |
| F22 C04 | 提交成功後斷線重送 | 回原receipt與原committed_at，不重算時效 |
| F23 C04 | 已ready，次slot或失敗attempt | 保留首次稿與準時證據，不重建revision |
| F24 C04 | 讀取時物件缺失/損壞 | integrity_error，不交出殘缺內容 |
| F25 C04 | 三slot之外第四自動attempt或第4 execution | attempt_limit，不再生成 |
| F26 C05 | 網頁/語音同expected_revision不同request | 僅一筆成功，另一revision_conflict |
| F27 C05 | 同ID同payload重送；同ID換payload | 回原結果；後者idempotency_conflict |
| F28 C05 | r1成功回應遺失，其後r2，再重送r1 | applied_revision=1/current_revision=2，不回退 |
| F29 C05 | 修改一題有效另一題未知 | 整批unknown_story，版本與內容不變 |
| F30 C05 | reorder後使用舊題號映射 | 舊expected_revision拒絕，不修改錯題 |
| F31 C05 | 更換base，story_id巧合同名 | base_mismatch或操作明確舊base，不跨base套用 |
| F32 C05 | restore r0；無變更保存 | 新revision含r0內容；無變更不增revision且有receipt |
| F33 C05 | 排除/恢復/選另一base/匯出 | 原稿與各base歷史不變，匯出指定版本可核對 |
| F34 C03～05 | 未授權、越權、未知欄位、重複keys、超限 | 拒絕且無狀態副作用；不漏內容 |
| F35 C03～05 | 例外包含假token/新聞全文/私人路徑 | 公開摘要無注入內容；只白名單欄位 |
| F36 C03～05 | 執行路徑試圖網路或curl/provider | 測試硬失敗，不以無網路碰巧失敗算通過 |

## 審查結論與續行

六項決策已可進行離線實作；新增重要平台條件是可信期別發行與原子控制層。
原先「直接靜態cron→Actions→物件manifest」不足以符合所有需求，正式架構可行性
仍取決於C01/C08/C09；不在離線階段宣稱候選供應商已滿足。
現有本機函式按其原用途未發現本輪必須修正的bug，缺口屬新雲端邊界。
本段記錄 C02 審查時的結論；C03 完成狀態見下方交接。36例尚未全部測試，手機雲端能力未驗證。

下一項 **C03，建議 Astra / High**：先用相同審查脈絡落實日期、身份與重跑的接口，
避免跨模組共享生成行為退化。此為任務複雜度建議，非即時模型評測。

續行指令：依本契約只實作C03離線prepare_generation與F01～F10、F34～F36相關測試。
先讀最新HANDOVER與工作差異，沿用既有composer及Downloads保護；測試使用合成輸入，
過程產物存Downloads。跑相關測試；涉及共享generation/schema時依AGENTS跑完整Python套件。
完成後保存差異、測試與未完成矩陣，停止在C04前並提供模型/思考建議。

## 2026-10-09 C03 執行交接

- C03 已新增 `scripts/digest_cloud_prepare.py` 與 `tests/test_digest_cloud_prepare.py`，
  只接收注入的模擬可信意圖及固定三檔bytes/hash/commit，生成、配對核對並獨立重跑。
  輸出 `PreparedPair` 含不可變 bytes 與來源證據；不含 ready/late 或交付 receipt。
- 入口檢查排程 slot、固定日期、跨日、人工歷史授權宣告、同commit、輸入hash、
  既有原稿identity及長度上限。所有暫存寫在指定Downloads子目錄，用後自動移除。
- 已覆蓋 F01～F10 及 F34～F36 中 C03 適用的行為；其中 F08 的「改版本/設定」
  使用既有 `test_generate_digest.py` 測試，本輪新增測試驗證輸入改變。F04 提交跨日屬 C04。
- C03 模擬中的 `issuer_id` 與 `owner_authorized` 只代表測試注入的可信意圖，
  **不證明**網路來源身分、憑證、GitHub commit 來源或真實手機授權。
- 測試首次失敗：時間戳正則漏日期；修後一次仍發現既有 `window_for_date(None)`
  會套用今天，故新入口明確拒絕缺少日期。最終結果與checkpoint見HANDOVER。
- 精確 C04 入口：依第3/5/6節實作 `store.put_if_absent/get` 與
  `control.commit_delivery` 的本機假服務；使用 PreparedPair，不重算日期。
  先做F11～F25與F34～F36，特別驗證同/不同base併發、交易成功後回應遺失、
  保存時點90分鐘界線、選版與人工稿保護。不得以本機鎖聲稱真provider具CAS。
- 下一項建議 **GPT-6.1 Sol／High** 以節省額度；只有遇跨交易一致性問題再升Astra／High。

## 2026-10-09 C04 執行交接

- C04 已新增 `scripts/digest_cloud_mock.py` 與 `tests/test_digest_cloud_mock.py`。
  `MemoryObjectStore` 對每個原稿bytes採不存在才寫入、既有bytes不同則拒絕；
  `MockDeliveryService` 上傳後讀回並用既有pair verifier核對；`MemoryControl` 在同一
  程序鎖內採copy-on-write提交整筆issue控制紀錄。這些都是本機記憶體假服務，
  不承諾重啟後持久保存或真雲端的CAS/權限/網路一致性。
- 每個 request 的attempt在上傳前先記為running，固定source commit與payload；
  失敗變failed並保留舊交付。交易提交時才取可信模擬時鐘決定時效與09:00截止，
  原子寫入delivery receipt、request receipt、attempt終態與首次revision 0。
  相同request重送回原結果；不同payload或attempt ID拒絕；帶舊control版本的請求拒絕。
- F11～F25 的 C04 適用行為均有合成測試，另含 F34～F36 的部分邊界。
  F23的「下個slot已有ready先跳過生成」屬C08流程guard；C04已驗證後續失敗
  不清除舊ready或人工版，並保留第二個合格來源版本作候選以支援異稿併發。
  F25工作execution_count>3及同slot新request已拒絕；避免在生成前浪費第四次工作
  仍須C08在進入C03前執行guard。
- 本機控制儲存目前公開的是內部Python函式，沒有真實登入、網路API或手機入口；
  C05才做校稿寫入/還原/匯出與角色授權邊界。讀取時若物件損壞，回integrity_error，
  不把歷史receipt改寫成成功的目前讀取。
- 驗證：最終完整套件使用桌面附帶Node.js為 **903 passed in 3.06s**。
  首次全套執行因PATH沒有node，39個前端測試失敗、862通過；補上Node路徑
  並完成末次修改後全套通過。首輪39項為環境錯誤。
- 精確 C05 入口：在 `MemoryControl` 每issue copy-on-write交易上加入
  `apply_edit(principal, request)`、`read_review(base, revision=None)`、
  `select_base(expected_control_version, base)`、`export_review(base, revision)`。
  先實作 F26～F33：以同base story_id、expected_revision與request_id做整批原子修改，
  確認語音/網頁同時寫入、回應遺失後重送、還原及匯出不覆蓋原稿或其他base。
  模擬owner身份僅注入，不能宣稱手機OAuth驗證。
- 下一項建議 **GPT-6.1 Sol／High**；遇revision交易無法保持原子性再用Astra／High。

## 2026-10-09 C05 執行交接

- C05 新增 `scripts/digest_cloud_editorial.py` 與 `tests/test_digest_cloud_editorial.py`。
  `MockEditorialService` 共用C04每期copy-on-write控制紀錄，提供owner注入身份的
  `read_review`、`apply_edit`、`select_base`、`export_review`。只模擬權限，
  沒有登入系統或雲端HTTP API。
- 編輯request綁定issue_date、base_identity、expected_revision與request_id；按原稿內
  story_id整批修改included、標題、摘要和順序。原稿metadata/source refs不可編輯。
  舊revision拒絕並回安全代碼；相同request重送回原結果，另外呈現當前revision，
  防止成功回應遺失後重送而覆蓋較新的人工稿。
- restore從指定歷史revision建立新的遞增版本，沒有內容變化時只保存request receipt。
  選版必須owner+control_version+request_id；校稿不跨base移轉。匯出指定不可變
  revision為JSON，包含身份、內容雜湊、可閱讀題目/來源及檔案SHA256。
- F26～F33、F34～F36 的C05適用部分已有合成測試，包含併發、回應遺失、未知題目
  全批拒絕、重排後舊題號、同story ID不同base、還原、匯出、越權、重複JSON key、
  NaN/超限與內部例外去敏。語意衝突結果會留request receipt；格式錯誤在取得可信
  request身份前直接拒絕，不留receipt。
- 驗證：完整離線套件 **923 passed in 3.35s**，Python編譯通過；快照見HANDOVER。
  模擬仍限單程序記憶體，不能代替持久雲端
  交易、手機語音、OAuth或登入測試；C01/C09/C10保持待實測。
- 精確 C06 入口：以這套校稿方法做**本機私人網頁預覽**，預設只載合成稿；
  顯示日期、狀態、base、revision、來源與明確題號→story_id映射。提供大按鈕、
  可存取標籤、保留/排除、標題/摘要聽寫欄位、儲存、讀回、還原、選版、匯出。
  寫入一律帶expected_revision與request_id，衝突須顯示目前版本及重新讀取入口；
  不以只送出表單表示保存成功。不得把模擬網頁稱為已在iPhone實測或可離線同步。
  C06不部署、不要求真帳號憑證、不連外部服務。
- 下一項建議 **GPT-6.1 Sol／Medium**；介面若出現複雜同步衝突，再提高至High。

## 2026-10-09 C06 執行交接

- 新增 `scripts/digest_cloud_preview.py`、`private_preview/` 與
  `tests/test_digest_cloud_preview.py`，以只綁 `127.0.0.1` 的 WSGI 預覽頁呼叫
  **同一套 C05 校稿服務**；預設僅建立兩則合成資料、單程序記憶體保存。
  [操作與限制](DIGEST_CLOUD_PREVIEW.md)。
- 頁面顯示期別、狀態、selected/working base、revision、來源與題號→story ID；
  大按鈕及可存取標籤支援保留/排除、排序、標題/摘要欄位、儲存、讀回、
  還原、明確選版、指定revision匯出。欄位可用作業系統聽寫，尚未在 iPhone 實測。
- 校稿及還原送 `expected_revision`、`request_id`；選版送
  `expected_control_version`、`request_id`。成功後讀回 `applied_revision` 並核對
  `content_sha256`；衝突顯示目前版本、重新讀取入口並保留未套用輸入。
  本機邊界限制 Host/Origin、token、請求長度與快取，不能視為正式登入。
- C06 五項合成 API 測試通過；本機瀏覽器已操作保存讀回、還原及兩頁並發衝突，
  並以手機寬度檢查排版。最終完整離線套件 **928 passed in 3.37s**；Python 編譯、
  JavaScript 語法檢查及 `git diff --check` 通過。
- 第一輪新測試因 fixture 未傳入 token 而有四個 setup error；修正後
  第二輪因兩份合成稿使用同一排程 slot 有一個 `attempt_limit`，改用第二 slot 後
  五項通過。此為測試配置問題，正式離線回歸無失敗。
- **精確 C07 入口**：先完成 C01 的實際平台/帳號與 iPhone 讀寫／語音可行性查核；
  以該結果裁決接入雲端工具或採私人網頁降級方案。接入時沿用 C05 的
  issue/base/story ID/revision/request receipt 契約，補真實身份驗證與持久原子控制。
  不能以 C06 的本機 mock 或手機寬度模擬代替 C01/C07 驗收；不在本階段部署。
- 停於 **C07 High**。審查建議 **Astra／High**；若 C01 已證實平台能力且
  只需按既定介面接線，可用 **GPT-6.1 Sol／High** 節省額度。

### 2026-10-09 C01 手機代理查核補記

使用者已在 iPhone 一般 Chat／Work 用現成 `@Google Drive` 外掛完成合成文件的
搜尋、建立、編輯、跨對話讀回與僅本人分享權限查核；建立需點選批准。
Mac 離線時，使用者回報手機仍可處理該文件。可少量觸控、避免大量編輯即可；
朗讀與零觸碰不是驗收條件。詳見
`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C01-mobile-validation/HANDOFF.md`。
這是手機帳號能力的代理證據，不證明 AI News Radar 自建工具、候選供應商
登入／權限範圍、持久原子控制或正式日報已可用。C07 先審查平台和身份邊界，
仍停在 **High**；建議 **Astra／High**。
