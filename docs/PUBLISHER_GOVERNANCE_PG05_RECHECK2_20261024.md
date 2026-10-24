# PG05 補修二複驗（2026-10-24）

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：階段歷史／已結案。** PG01～PG06已正式發布，最後補修（四）定稿；本頁的下一步、未通過、待推送只描述當時，不再開補修（五）。技術契約與限制保留，對照[PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)及SOURCE_COVERAGE使用。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

本次複驗完成，**發布驗收未通過，不進 PG06**。既有反例都已修好，但新的合成案例仍確認兩類材料誤判。下一階段：**PG05 補修（三），GPT-6.1 Sol／High**；補修後由 **GPT-6 Astra／High** 複驗。

## 起點與範圍

canonical 為 `/Users/lordmi/Documents/ai-news-radar_zhtw`，master，HEAD `8deab0c1b61a7560c2f552c5366b3776bc82dd51`。先核補修二 MANIFEST 的 261 個證據檔及 39 個累積 dirty 檔，全部相符；既有候選完整保留。

本次只更新本說明、HANDOVER、SOURCE_COVERAGE、ROADMAP。沒有修改 runtime、測試、來源 registry、事件去重、state／phase／時間、資料快照或工作流；沒有提交、推送、dispatch、部署或啟動下一階段。

證據：`/Users/lordmi/Downloads/ai-news-radar-pg05-recheck2-20261024/`。先核 `SEAL.sha256`／`MANIFEST.json`，再讀 `HANDOFF.md`、`VALIDATION.json`、`FINDINGS.json`。原各階段封存保持唯讀。

## 阻擋發布的兩項發現

全部案例都是合成材料；官方 URL 僅用作 fixture，並非指稱官方真的發布過這些內容。案例先定預期，再經實際 business_event_score、AI relevance、材料資格、事件 producer 及 radar，不注入入選分數。

### R2-01：未命中否定詞不等於交易已確認

`scripts/publisher_material.py` 的 `transaction_state` 第 217～229 行，在未命中兩組否定／意向詞時直接回傳 affirmed。後續只要動作前後有具名主體便可支持交易。因此以下六種材料都被標 supported，並各自取得一個首頁重點：

- `OpenAI is expected to acquire Cedar Labs`，摘要明說尚未簽約。
- `Will OpenAI acquire Cedar Labs?`，摘要明說尚未宣布交易。
- `If OpenAI acquires Cedar Labs, the AI market will change`，摘要明說是假設。
- `OpenAI is unlikely to acquire Cedar Labs`。
- `OpenAI declines to acquire Cedar Labs`，摘要明說提案已拒絕。
- `OpenAI是否收購Cedar Labs？`，摘要明說是假設且未宣布交易。

這與 D05 要求的明確交易動作不符。Chrome 桌機／手機已對疑問及拒絕交易兩例重現錯誤卡片；已簽協議但待監管核准的正例仍可入選。

補修需辨識有界交易命題的肯定狀態與動作歸屬；疑問、條件、拒絕及未定案不能因「沒命中黑名單」而直接支持。不應只繼續追加本次六句字串，也不能要求所有交易都已完成交割。保留明確宣布／簽約、待核准、未來生效及補修二既有正例。

### R2-02：有限後綴排除仍把附屬出版物當成模型

`scripts/publisher_material.py` 第 93～101 行的 `model_is_release_object` 只排除固定修飾詞與文件名詞組合。未命中即接受，再由 `publisher_governance.py` 第 78～84 行的 release→模型名稱橋接取得發布資格。

新五個文件案例均誤取得首頁資格：`Photon Nova AI model updated documentation`、`Photon Nova AI model API reference`、`Photon Nova AI model training tutorial`、`GPT-6.1 Sol updated documentation`，以及 `OpenAI發布Photon Nova模型新版使用手冊`。其中四個未知型號案例還進入實際模型雷達；已知型號那例只誤進首頁。

Chrome 桌機／手機已對英文 updated documentation 及中文新版使用手冊重現首頁／雷達誤收。「發布模型並附更新文件」的正例仍可正常入選。

補修需確認完整發布受詞為模型本體，處理修飾語／所有格／中英文文件名稱；不能因模型名位於 release 後便認定本體發布，也不能將任何含文件、API 或教學字樣的真正模型發布一律排除。保持已知與未列名模型的同一判斷邏輯。

## 通過與未通過的證據

| 驗證 | 結果 |
|---|---|
| 完整 Python／JS bridge 回歸 | 1,983 passed，10.10 秒 |
| 原七個反例、前次 22 個正反例 | 全部通過 |
| 容量 | 七項通過；含縮小上限驗配置路徑，非 100k 文章效能測試 |
| 本次新 24 個合成案例 | 13 通過、11 失敗；交易 6／8 失敗、文件 5／8 失敗、財務主體 8／8 通過 |
| 正常 Chrome 驗證 | 50 contexts 通過，包括固定讀者、混版、到期、CNBC 一枚徽章、回復、14 日選集及前次三反例 |
| 新 Chrome 案例 | 12 contexts 符合 producer 實際輸出；重現四個負例與兩個正例，**不是產品驗收通過** |
| 固定 14 日重新產出 | 56 個 candidate 檔與補修二逐位元組一致；14 份 input 相同 |
| 回放規模與選集 | 1,914 事件窗口，daily 2 事件次數、一般 1,976 列次；state、raw、材料與選集均未變 |
| 固定讀者資料 | 18 檔一致；194 一般篇、183 raw 根、0 featured／daily、1 媒體雷達 |

固定回放使用同一封存輸入、previous state 及 asof；PG03 baseline 沿用已核封存，未重新生成。這是保留 archive 的離線重建，不是當時線上觀測。無新增進退出選集，因此未重讀任何真實新聞正文。正式資料 hash 亦與既有錨點一致。

兩張代表手機全頁截圖已目視確認疑問收購卡片及文件稿首頁／雷達誤收。外部請求被離線封鎖，圖片未載入不列為本案缺陷。

## 隔離與交接

強隔離閉包維持 1,039 IDs，包含原 72 protected、448 reserved、既有污染稿、完整／裸 Claude 版本及六 CN 家族。此次沒有新保護材料曝光；不抹除先前已記錄的污染。新合成案例與所有已讀開發資料不得當成獨立留出；`independent_precision=not_evaluable`。

補修（三）以此兩項為最小範圍。財務主體新八例及補修二正例應保留，沒有證據要求再改其實作。優先修關係判定，沿用門檻、matcher、來源准入／計票鍵及既有排序，禁止為過測而加入文章 ID／URL 特例。

接手時先核本次與補修二封存；把 `fresh_adversarial_probes.py` 的預期轉為正式回歸，保留原七例／22例／79例正反對照。新 Chrome 腳本目前用於**重現錯誤輸出**，修後必須改為驗收負例零首頁／零雷達、一般列表仍可讀；不能直接沿用誤收為 1 的斷言宣稱修復。

修後依規範重跑完整 suite、固定回放、隔離後的影響檢查及 Chrome；如果選集改變，先檢查整組 Boundary.allowed 才輸出材料。交付下一次複驗前綁定最終程式／輸入 hash，使用新的 Downloads 目錄，不覆寫前階段證據。複驗通過才進 PG06。
