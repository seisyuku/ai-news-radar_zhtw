# C07 雲端接入審查與實作交接

日期：2026-10-09。使用者已切換模型並要求開始審查。
2026-10-10 使用者另授權自動續行至無可執行任務；下文歷史停止點不再要求每項重新下令。
狀態：**C07 設計審查完成；有條件可行，實作與真實雲端驗收未完成。**
本輪只修改文件、查閱官方資料、重跑既有合成測試。

## 1. 審查裁決

1. 保留架構 A：Actions 生成；私人雲端服務保存與校稿；ChatGPT 優先、私人網頁備援。
2. C01 分成兩層：**C01a 現成外掛代理查核已完成**；**C01b 專案自建工具實機查核待完成**。
   Google Drive 不自動成為正式校稿資料庫，也不將一般文件編輯直接同步回 revision。
3. C07 不能當成單純接線。先將 C05 規則從記憶體儲存拆出，再加入持久儲存及真實身份。
4. 優先評估 Cloudflare Workers + SQLite-backed Durable Objects + 私人 R2；
   這是技術候選排序，並非服務開通、付費、部署或正式選型核准。
5. 使用者能少量觸控；口述指令加點選批准即可。朗讀、逐字聽寫、完全免觸控不列阻塞條件。

## 2. 重要發現

| 等級 | 證據與問題 | 決策與完成條件 |
| --- | --- | --- |
| P1 接入缺口 | C01 只用現成 Google Drive；尚無本專案的遠端 MCP URL、登入、工具清單或手機實測 | C01a 不冒充 C01b。正式工具先用合成稿驗證建立連線、讀寫、讀回及拒絕未授權身份 |
| P1 接入缺口 | `MockEditorialService.__init__` 限定 `MockDeliveryService`；多處直接讀寫 `control._issues`、`_lock`、`_clock` | 抽出與儲存無關的規則和交易介面；網頁/MCP 共用一套規則，不各存一份稿 |
| P1 交易移植 | `_remember_error`、`apply_edit.reject` 在記憶體更新後拋錯；真交易若拋錯會回滾，可能連拒絕 receipt 一起消失 | 交易 callback 回傳成功或拒絕的結構化結果，先提交 receipt，離開交易後才轉成 API/MCP 錯誤；基礎設施異常才回滾 |
| P1 身份缺口 | C06 在建構時固定 `SimulatedPrincipal(owner, True)`；頁面含預覽 token；這是 loopback 模擬 | 正式請求逐次驗證憑證及 owner，由服務端注入 principal；不得把 C06 token 當登入或把布林 owner 欄位暴露給模型 |
| P1 任務相依 | 原 C07 要真工具驗收，C09 又以前者為前置，而部署排到 C10，形成驗收次序矛盾 | C07 分本機完成和線上驗收；C09 可用本機完成作準備前置，C10a 合成部署補 C01b/C07 實機證據，再進真日報 |
| P2 執行環境 | `_verify` 寫 Downloads 暫存；mock 使用 `threading.RLock`。Python Workers 不提供可用 threading，磁碟也不是持久儲存 | 保留本機路徑保護；正式雲端另用 bytes 驗證介面及平台交易，先做相容性試驗，不直接部署 preview |
| P2 操作語意 | 只有題號無法識別是哪次排序；衝突後若自動換成新 revision 並重解題號，仍可能改錯新聞 | 每次修改攜帶使用者指涉的期別/base/revision/題號映射；衝突讀回後呈現差異，不自動重送新意思 |

以上屬正式雲端接入的缺口；本輪未確認需要立即修改現有本機模擬的程式 bug。
相關位置：[C05 服務](../scripts/digest_cloud_editorial.py)、
[C04 記憶體服務](../scripts/digest_cloud_mock.py)、[C06 預覽](../scripts/digest_cloud_preview.py)。
Cloudflare 明定 `transactionSync` 的 callback 拋錯會回滾，且不能在其中 await 外部 I/O。
來源：[Durable Objects 交易](https://developers.cloudflare.com/durable-objects/api/sqlite-storage-api/#transactionsync)。

## 3. 建議接入形態

```text
iPhone 一般 Chat／Work → 專案私人 MCP ┐
iPhone 私人網頁 → 同源 API          ├→ 驗證身份/權限 → 同一校稿規則
                                  ┘                  ↓
                                           每期一個交易控制單元
                                           revisions + receipts + head
                                                    ↕
Actions → 受限交付入口 → 核對原稿 bytes → 私人不可變原稿儲存
```

### 平台與程式重用

- 優先候選用一個 Durable Object 管理 `(owner, issue_date)` 的控制狀態，
  以 SQLite 交易保存版本、指標及 receipt；原稿 bytes 放私人 R2。
  R2 上傳／讀回先做，控制交易再檢查版本和服務端時間，交易內不放遠端物件 I/O。
- Python 生成仍在 Actions。校稿規則維持單一 Python 實作，優先做 Python Workers
  相容性試驗；需要 TypeScript MCP/登入外層時只負責傳輸與已驗證身份，不複製校稿規則。
  Python Workers/FFI 不通過時再提出 Python 服務替代部署，不能默默重寫整套規則。
- 正式 bytes 驗證須和既有 `verify_digest_pair` 共用規則、跑相同測例；
  不刪除或放寬現行 Downloads 保護來迎合雲端環境。
- Cloudflare 文件證實 Python 執行支援，但標準庫有環境限制；平台支援不是本專案可直接執行的證據。
  [Python Workers](https://developers.cloudflare.com/workers/languages/python/)、
  [標準庫限制](https://developers.cloudflare.com/workers/languages/python/stdlib/)。
- R2 的條件寫入與強一致讀回可用於候選原稿 adapter；仍需測試不存在才寫、
  已存在不同 bytes 拒絕，以及受限入口無法任意覆寫。
  [R2 API](https://developers.cloudflare.com/r2/api/workers/workers-api-reference/)。
- SQLite-backed Durable Objects 有免費方案；超出免費限制會失敗。
  Workers 付費方案有基本訂閱與用量費，不能將基本費當整體費用上限。
  本輪沒有帳號、CPU/儲存量實測與完整登入服務報價，不承諾零成本。
  [DO 定價](https://developers.cloudflare.com/durable-objects/platform/pricing/)、
  [Workers 定價](https://developers.cloudflare.com/workers/platform/pricing/)。

### 身份與工具權限

- 自建 MCP 使用 HTTPS、Streamable HTTP、OAuth；私人網頁另用登入 session，
  兩者映射到同一內部 owner。以已驗證的 issuer/subject 映射，不讓工具參數指定 actor。
- 逐次驗證簽章、issuer、audience/resource、有效期及 scope；owner 白名單與 scope 都必須通過。
  登入後仍須拒絕別的帳號。期限、撤銷及重新連線行為在測試環境實測。
- 建議 scope 分 `digest:read`、`digest:edit`、`digest:retry`；交付及排程身份另設。
  MCP 不拿儲存管理憑證或 GitHub PAT。模型工具參數不得攜帶 owner_authorized 或任意儲存 URL。
- 優先使用成熟身份服務及維護中的 OAuth library。Cloudflare Access/外部 IdP 為候選，
  要核對 discovery、PKCE S256、resource/audience、callback 與 ChatGPT 實際連線。
  單純在 MCP 前方放網頁登入頁不算 OAuth 接入完成。
- 官方文件支持在 ChatGPT 網頁建立並安裝自訂 MCP 外掛；一般手機外掛可用，
  但本帳號的自建外掛可見性和實際登入仍須 C01b 驗證。
  工具批准設定是使用者介面行為，不代替服務端授權。
  [OpenAI 自訂 MCP](https://developers.openai.com/api/docs/guides/custom-mcp-server)、
  [OpenAI 認證規格](https://developers.openai.com/plugins/build/auth)、
  [外掛支援介面](https://learn.chatgpt.com/docs/plugins)、
  [Cloudflare MCP 授權候選](https://developers.cloudflare.com/agents/model-context-protocol/protocol/authorization/)。
- 若採 Cloudflare MCP SDK，先固定相容版本；目前官方指南建議新無狀態入口用
  `createMcpHandler`，並警告部分快速模板仍走已棄用路徑，不直接照抄模板部署。
  [Cloudflare Remote MCP](https://developers.cloudflare.com/agents/model-context-protocol/guides/remote-mcp-server/)。

### 最小工具與保存語意

| 工具 | 內容與限制 |
| --- | --- |
| `get_digest_status` | 期別、交付品質／時效、選用 base、最新 attempt；不得有匿名私人狀態 |
| `read_digest` | 明確期別、base、revision，回題號映射、內容與 hash；大型內容分段並標明未讀完，不靜默截斷 |
| `apply_digest_edit` | C05 patch/restore，只收穩定 story ID、expected_revision、request_id；整批成功或拒絕 |
| `select_digest_base` | 維護者明確選版，帶 expected_control_version；不遷移舊校稿 |
| `retry_current_digest` | C08 有界 guard 與可信意圖完成後才提供；未接通時不發布此工具 |

工具層由已讀快照建立修改內容；對話缺少映射時先讀取。需要防止跨對話混用時，
可以加服務端簽發的 read-context，綁 owner/issue/base/revision/映射；它只輔助定位，
不代替 OAuth，也不改 C05 的持久 request identity。不要為新介面改原稿 identity。

保存後按 `applied_revision` 讀回並重算 content hash，再查目前 head。
receipt 已成功但讀回失敗時顯示「已提交，讀回尚未核對」；保留原 request_id 查詢／恢復，
不能直接顯示未保存並換新 ID 重做。若讀到後續版本，分別呈現已套用版本與目前版本。
canonical JSON 沿用 `digest_document.canonical_json`；跨語言邊界不得用一般 JSON.stringify
代替 identity/hash 規則。新聞內容是資料，不作登入、工具指令或發布授權。

## 4. 驗收矩陣（本輪只制定，尚未實作這些雲端測試）

| ID | 驗收情境 | 必須結果 |
| --- | --- | --- |
| G01 | 匿名、別的 owner、過期／錯 issuer/audience／偽造 token | 拒絕且不回私人稿、不建立版本或 receipt；合法公開 discovery 不含私人資料 |
| G02 | 只有 read scope 嘗試 edit/retry，或工具參數自述 owner | 拒絕；真正 principal 只來自驗證過的 request context |
| G03 | MCP/網頁同時改同 base/revision | 僅一筆成功，另一衝突；共用同一 head |
| G04 | 保存成功、回應丟失、服務重啟後重送 | 回原 applied_revision；另一新版本不被舊重送覆蓋 |
| G05 | 永久拒絕後重啟；同 ID 同/異 payload | 拒絕 receipt 持久；重送原結果／idempotency_conflict，不能因 throw 回滾丟失 |
| G06 | 換 base 或重排後仍指涉舊題號 | 使用原映射／舊版本被拒絕；不偷偷按新順序改錯題 |
| G07 | 原稿缺檔、bytes 改動、revision hash 不符 | integrity_error，不交出未驗證內容 |
| G08 | receipt 成功但 readback 失敗、或已有更晚 head | 區分提交與核對；原 ID 可恢復，applied/current 不混淆 |
| G09 | 中斷上傳、交易失敗、同時提交／選版 | 沿用 F17～F24；舊合格稿保留，沒有半筆控制狀態 |
| G10 | Python Workers 真實相容性及 Unicode/hash | 實際 runtime 可讀寫平台交易；相同 fixture 的 bytes/hash/結果與本機一致 |
| G11 | MCP OAuth 重連／權限撤銷與私人網頁登入 | 只 owner 可存取；MCP 與網頁映射同一 owner，錯帳號無法讀寫 |
| G12 | 核准後的自建外掛，在 Mac 離線的 iPhone 操作合成稿 | 可見工具、讀取、編輯、另次讀回和私有權限核對；允許少量點選 |

G10 的本機模擬器通過不冒充真實平台持久性；G11/G12 必須記錄線上實測。
C02 的服務端提交時效與09:00要求不在本輪放寬；正式 adapter 須說明平台提交／確認時間
可提供什麼證據，遇到跨截止持久寫入的模糊情境不得靠客戶端事前時間宣稱準時。

## 5. 下一步小任務與停止點

| 任務 | 可交接產物 | 建議模型／強度 |
| --- | --- | --- |
| **C07a** | 抽離儲存與身份邊界，保留 mock 相容；規則回傳可提交的成功/拒絕結果；保持 bytes/hash 與 C05 語意 | **GPT-6.1 Sol／High**；共享交易邊界需完整回歸，已無須重新做平台探索 |
| C07b | 候選平台本機相容性小試驗：Python 規則、DO 交易、R2 bytes；固定版本和失敗證據 | GPT-6.1 Sol／High；若 Python/FFI 無法保持契約，停下交 Astra／High 裁決 |
| C07c | 最小 MCP/API 傳輸層與身份介面；先合成測試 G01～G09，不把測試 token 當正式登入 | GPT-6.1 Sol／High |
| C08 | 原定日報 workflow／可信期別／有界重試的離線實作 | GPT-6.1 Sol／High；另按 C08 範圍交接 |
| C09 | C07 本機部分與 C08 完成後，整合帳號、區域、實際報價、權限、部署／回復計畫供核准 | Astra／High 審查具體部署設定 |
| C10a | 核准後只部署受保護合成環境，完成 C01b 與 G10～G12 | GPT-6.1 Sol／High；首次 OAuth/持久交易問題再升 Astra |
| C10b/C11 | 合成門檻通過後依核准範圍做單次真日報，再另啟排程與三日驗收 | 沿用原任務分級 |

C07-R（本審查）完成不等於 C07 整體完成。C09 的準備入口可用 C07a～c 本機產物，
正式日報則必須等 C10a 完成實機門檻。若私人自建外掛無法在本帳號安裝／使用，
明確記錄原因並採使用者已接受的私人網頁備援；網頁仍要登入、持久版本與讀回。

**精確續行指令：** `run C07a`。先讀本文件、最新 HANDOVER、C02 契約與現有差異。
僅抽出 service/transaction ports 與 pure transition，保留 PreviewApp 和 mock 的原有行為。
最少覆蓋拒絕 receipt 的「提交後才拋錯」邊界及回應遺失重送；共用生成/schema受影響時
依 AGENTS 跑全套。過程產物放 Downloads，保存起點與最終差異；不安裝真外掛、不部署。
完成後停於下一 High 任務 C07b 前並提供模型建議。

## 6. 本輪驗證與恢復

- C03～C06 相關合成測試：**65 passed in 0.57s**；首輪即通過。
- 本輪不變更 scripts/tests/private_preview；沒有為文件審查重跑全套928項並聲稱新證據。
- 檢查點：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07-review-185036/`。
  含起點 commit/status/diff、修改前文件、原始碼雜湊、測試命令及 log、最終文件與交接。
- 回復本輪只需按 checkpoint 的 before 文件逐份比對回復並移除本輪新增審查文件；
  工作區已有 C02～C06 未提交改動，不得用整庫 reset/checkout 丟棄。
- 正式平台／身份服務、費用上限、通知與清理政策仍需具體設定後裁決；
  本輪沒有取得憑證、修改 Google Drive 文件、部署、啟用排程或 commit/push。

## 2026-10-10 C07a 實作交接

- `EditorialService` 透過 OriginalReadPort、IssueControlPort、OwnerPolicy 工作；MockEditorialService 僅提供既有模擬身份的相容包裝。正式登入仍待接入，不能由工具輸入建構可信身份。
- 純規則回傳 IssueDecision；控制層提交 state 後，服務再處理 error_code。永久拒絕可保存 receipt，未知異常仍中止交易。先讀 receipt 的快速路徑與交易內二次去重均保留。
- 抽出 digest_json/digest_integrity，共用 identity 和配對核對。原 generator 的檔案驗證呼叫同一 bytes 核對；沒有放寬 Downloads 邊界。
- SQLite 關閉重開後拒絕仍有 receipt；成功回應重送仍回 applied_revision/current_revision。資料庫測試 adapter 不屬正式雲端 adapter。
- 最終完整回歸 **938 passed in 3.51s**；checkpoint 見 HANDOVER。繼續 C07b，模型建議 GPT-6.1 Sol／High；本輪依使用者新授權不在此停止。
