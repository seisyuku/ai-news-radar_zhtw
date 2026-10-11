# 私人雲端日報：C02 Astra 審查交接

日期：2026-10-09。最新狀態：C02 審查、C03～C06 本機模擬完成，停於 C07 前。
[正式決策、36項驗收案例與 C03 入口](DIGEST_CLOUD_CONTRACT.md)。
以下保留 C00 交接時的原始材料與當時狀態，不代表 C02 仍未開始。
使用者已核准架構 A 離線模擬，並要求遇下一高難度任務時停止，由其開啟 Astra。
本文件提供審查材料，不替代核准後的雲端資料契約。

## 本輪完成及未完成

- 起點 HEAD：`202cb9212022c118642f180b96c8bd449af8a9e9`；起點唯一差異為
  未追蹤的 `docs/DIGEST_CLOUD_DELIVERY_PROPOSAL.md`。
- 既有生成、私人交付、GitHub 驗證離線測試：62 passed in 0.63s。
- 項目：`tests/test_generate_digest.py`、`tests/test_deliver_digest.py`、
  `tests/test_validate_digest.py`。fetch 使用 mock/fixture，沒有 live API。
- tracked scripts/tests/workflows 在測試前後的 SHA-256 全部相同。
- C00 是模擬範圍核准與基線驗證，不代表平台、費用、通知及保存政策已裁決。
- 尚未建立雲端生成入口、storage adapter、校稿 API、私人網頁或 MCP。
- 沒有連網、讀寫雲端、取得憑證、改排程、傳送通知、修改私人日報或 commit/push。
- C01 線上帳號/手機工具能力驗證仍未執行；模擬不能替代它。

證據目錄：
`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C00-20261009-095013/`。
包含 START.json、COMMAND.json、BASELINE_TESTS.log、BASELINE_RESULT.json，
另於本輪結尾保存交接、文件快照與 diff。

## 為何在此停止

提案將 C02「manifest、固定期別、題目 ID、revision、狀態與 fixture」分為 High。
它決定雲端資料的永久身份、原稿與人工稿的關係，以及重試/併發是否會覆蓋校稿。
使用者要求在下一高難度任務停止，故不自行降級或先開始 C02 實作。
這是使用者指定的審查停點，不是技術阻塞或雲端模擬已完成。

## 既有程式能重用的部分

| 入口 | 已有行為 | 雲端注意事項 |
| --- | --- | --- |
| digest_window.window_for_date | 臺北 06～06 半開窗口 | 保留期別，不用重試當下日期覆蓋 |
| digest_document.build_digest_document | composer 與確定性身份 | identity 包含版本、設定及衍生內容，不只是 source commit |
| generate_digest.write_digest / verify_digest_pair | MD/meta 雜湊與身份核對 | 各檔原子替換不是雙檔或雲端交易 |
| deliver_digest.readiness | 達截止、非未來、核對時≤90分鐘 | 保存耗時可能令快照過期，須定義最後判定時點 |
| deliver_digest.deliver | 同 commit 讀取、staging、本機 flock、原稿/校稿保留 | flock 不能作不同 runner 的雲端互斥 |
| validate_digest.validate | 生成、核對、相同 bytes 重跑與安全摘要 | 暫存會自動刪除，不能直接當持久交付入口 |

既有 `deliver_digest.main` 強制輸出在 Downloads 下；新增雲端入口可重用純函式，
不得為雲端需求移除這項本機保護。生成 metadata candidates 有 `story_id`，
應在指定原稿 identity 內使用；不能預設跨新快照的聚合 ID 永遠不變。

## 請 Astra 審查的六個決策

### 1. 固定期別與請求身份

需區分原定時段、外部送出時間、run created_at、實際開始、補跑與人工指定日期。
若 cron-job.org 不能動態傳入日期，不可宣稱 run 建立日期等於原定日期。
候選：在能保存 request ID/期別的入口固定意圖；或明確限制當日時段並拒絕跨日。
請裁決可信時間來源、缺時間/日期時的拒絕規則，以及第三次補跑如何指向同一期。
測例：午夜跨日、run 排隊跨日、人工補驗舊日、重複 request、錯誤時區。

### 2. 原稿與校稿身份

候選：原稿用既有 document input_identity；校稿綁定原稿 identity，題目用
既有 story_id，顯示序號另存。跨新原稿不自動轉移人工稿或用序號套用修改。
請裁決版本選用與更新規則，不更改已生成 MD/meta 的既有身份契約。
測例：同輸入重跑、版本/設定改變、新快照題目合併、重新排序後的口述題號。

### 3. 交付的完整性與發布順序

候選：不可變原稿/metadata 上傳，讀回核對，再最後建立 ready manifest。
manifest-last 只能遮蔽未完成上傳，不能單獨解決併發、同 key 覆蓋與 reader 競態。
請定義 create-if-absent/條件寫入、缺檔/hash 不一致、半途上傳及舊成功稿保留。
測例：第二檔失敗、manifest 失敗、讀回損壞、兩個 runner 同期同/不同 identity。

### 4. 校稿 revision 的併發保護

候選：編輯提交帶 expected_revision 與 request ID，後端條件更新；衝突明確拒絕。
歷史版本不可變，不讓舊網頁/語音任務覆蓋新 revision；重送相同 request 不重複修改。
請裁決計數或內容 hash revision，以及本機假服務對 CAS 能力的明確契約。
測例：網頁/ChatGPT 同時修改、回應遺失後重送、還原、無變更保存、錯誤 base identity。

### 5. readiness 與準時性分開

現有 readiness 的 clock 是核對時點；雲端保存後才算交付，須處理上傳跨90分鐘門檻。
候選：既有原稿身份保持不變，時效與 deadline 存交付 manifest；ready、late 與
review-only 分開表示。09:00 後完成不改成準時；晚到可審閱但標明未準時。
測例：07:15 開始、09:01 完成；上傳跨90分鐘；合法新鮮空日；舊資料空日。

### 6. 模擬與正式安全邊界

本機 adapter 不承諾真實物件儲存 CAS、OAuth 或手機可用性。這些必須 C01/C09/C10 實測。
候選：status/read/edit/retry 為最小工具集合；原稿與交付寫入權限不暴露至手機。
請裁決必要且最小的 manifest/schema，控制公開診斷，不引入自動刪除或新來源。
測例：未知欄位、錯誤原稿 ID、公開摘要混入內容、未授權修改、模擬網路呼叫被禁止。

## C02 應交付什麼

1. 正式本機模擬契約文件，明確 schema/version、狀態及失敗行為。
2. 具體 fixture matrix：成功、空日、過舊、跨日、重跑、併發、半途保存與衝突。
3. C03～C05 的函式接口及 adapter 能力要求，不先綁定未核實的雲端供應商。
4. 審查結論：可實作的決策、未解決風險、模擬可證明與不能證明的事項。
5. 下一項精確入口、建議模型及思考強度；原始基線與歷史測試不改寫。

## 精確續行提示

```text
審查 docs/DIGEST_CLOUD_ASTRA_REVIEW.md 與已核准的架構 A 提案。
先處理 C02 六個契約決策與 fixture matrix，核對實際現有 API。
使用者授權離線本機模擬，沒有部署、外部排程、通知、清理或新 provider 授權。
本輪使用 Astra 審查。不要把本機成功當手機雲端能力驗證；不修改本機 Downloads 保護。
完成 C02 審查結論後提供 C03 實作入口與模型/思考建議。
先明確記錄審查結論與後續授權範圍，再接續程式實作。
```

下一階段：使用者指定的 Astra / High。理由：需要獨立審查身份、時間、
發布原子性與 revision 併發契約。此為使用者指定的切換，不宣稱已替其切換模型。

## 回復方式

本輪只有文件變更；不影響現行日報或網站。需要回復時保留 Downloads 證據，
僅移除本輪新增文件/段落；不得清掉原先未追蹤提案或其他使用者變更。
沒有 commit/push，故沒有新的結束 commit；以最終 diff 和文件雜湊作交接。
