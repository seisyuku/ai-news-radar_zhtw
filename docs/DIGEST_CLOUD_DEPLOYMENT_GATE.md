# C09 準備交接：正式平台、身份與部署入口

**2026-10-10最新決策：本階段延後。** 先完成 [C08-G GitHub生成驗證](DIGEST_GITHUB_GENERATION.md)
及私人保存方式裁決。下文帳號、預算與身份條件只阻擋正式私人服務接入，不阻擋Actions產稿。
先前將這些設定當成所有工作的下一個阻塞點，是執行順序偏差，已在最新HANDOVER撤回。

日期：2026-10-10。狀態：**已完成可獨立執行的本機準備；C09完整檢查未完成。**
使用者的自動續行授權有效；目前需補的是帳號及成本/身份設定，沒有因High分級自行停止。

## 已有證據與候選

- C07a純規則/ports、C07b Python規則+DO/R2 runtime、C07c CPython MCP resource-server
  與C08本機意圖/補跑已完成。沒有真OAuth登入或正式日報交付。
- 直接把mcp2.3.0/PyJWT2.15.1/cryptography50.0.2打進Python Workers，在RSA匯入時發生
  Rust/Pyodide fatal error，runtime無法開始；不能部署這條候選路徑。
- 已實測替代：**TypeScript MCP/JWT外層 → 私人service binding → Python校稿核心+DO/R2**。
  MCP server2.3.1、jose6.2.12、Wrangler4.149.0在本機可完成匿名/錯帳號/過期拒絕、
  read scope拒絕編輯、owner保存、Python讀回與重開後讀回。
  TypeScript只作身份及傳輸，沒有複製校稿/revision規則。
- 這是合成prototype：固定fixture與單一期別，不是真production控制服務。
  正式核心仍需按實際帳號配置實作持久原稿adapter、期別/claim控制及交付入口；
  不能將Downloads內的合成worker直接部署為正式私人服務。

## 目前缺少的外部條件

| 項目 | 目前證據 | 下一動作 |
| --- | --- | --- |
| Cloudflare帳號/登入 | 本機未見Cloudflare相關環境設定或Wrangler登入配置；未讀任何憑證值 | 使用者選定自己的帳號並完成官方登入，不需貼token到對話 |
| 月費上限與方案 | 先前尚未定案 | 使用者指定可接受上限；實際帳號啟用、CPU/儲存額度與費用再查核 |
| 真身份服務 | 現有試驗是隨機合成RSA key與example.invalid issuer | 優先評估Cloudflare Access/既有Google登入；要實測MCP OAuth discovery、resource/audience、PKCE、callback与owner subject，不把網頁SSO當作MCP登入已完成 |
| 外部日報issuer | 只有MemoryJobCoordinator內部模擬意圖 | 受保護發行端持久寫intent再dispatch；Actions身份只允許指定repo/workflow/環境 |
| 正式交付workflow | 只有手動合約檢查入口 | 在確定API/身份後新增只接受request ID的交付job，固定source commit及有界執行；部署前檢查公開log白名單 |
| 通知渠道 | 僅安全通知計畫，未指定渠道或收件人 | 在C11啟用前選定；目前不傳送消息 |

## 可審閱的部署形態

```text
外部心跳 → 受保護的intent issuer → 日報專用Actions → 受限交付入口
                                              → 私人R2原稿 + 每期DO控制/版本
iPhone Chat／Work → OAuth → TypeScript MCP edge → 私人Python核心
iPhone私人網頁    → 登入 → 同一private API       → 同一版本/receipt
```

- 公開只留edge的OAuth discovery與受保護入口；core無公開route/workers.dev，R2非公開。
- 外部觸發、runner交付、讀取、校稿/選版、retry分權限。UI/手機不持有GitHub PAT或R2管理權限。
- 真實owner由已驗證issuer/subject綁定；不從模型參數、文中指令、名稱或未驗證email推定。
- production配置以 [非secret範本](../deploy/private-digest.example.json) 為起點。
  null欄位尚未確定；正式secret只放供應商/GitHub的secret介面，不放JSON或交接。
- 先完成配置與持久adapter/issuer實作，再於受保護合成環境做C10a/C01b。
  合成門檻通過才做單次真日報C10b；另啟C11排程，累積三個完整臺北日的證據。
- 當前沒有可核准的完整production部署包；此文件是準備方案，不是部署已通過。

## 費用查核（2026-10-10）

Workers的付費定價包含每月基本訂閱及用量費；官方範例的基本訂閱為US$5。
這不是本方案總月費或保證上限。[Workers定價](https://developers.cloudflare.com/workers/platform/pricing/)。
SQLite-backed DO有Free方案，超限會失敗；R2 Standard有10GB-month等免費額度，超限另計。
本輪尚無實際帳號或CPU/用量測量，不承諾免費可穩定交付。
[DO定價](https://developers.cloudflare.com/durable-objects/platform/pricing/)、
[R2定價](https://developers.cloudflare.com/r2/pricing/)。

沒有新增LLM API生成呼叫；生成沿用既有Python。Cloudflare/身份服務/通知的費用與
GitHub既有帳號額度，必須在實際配置後一起核對，不只看Workers基本費。

## 現在可續行的入口與模型

當使用者選定正式私人服務且確定需要Cloudflare後，才執行 **C09配置與provider定案審查，Astra／High**：
先唯讀確認官方登入與帳號權限，取得實際issuer/discovery/audience/回呼設定與計價，
裁決採split Workers或其他Python服務，再產生production adapter、受保護合成部署包及
明確回復方案供最終檢查。定案後的例行接線可用GPT-6.1 Sol／High。

不得把合成token、固定fixture、memory coordinator或本機binding標記為正式身份/持久性。
C10a～C12依賴這些真實設定與三日證據，目前不能完成驗收。

## 實驗與恢復

- 失敗路徑：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07c-workers-probe/runtime.log`。
- 成功替代：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07c-edge-probe/`及
  `C07c-split-core/`；有套件鎖檔、合成來源、HTTP結果及重開結果。臨時合成token已移除，
  所有本機服務已停止。
- 全部程式與交接仍在既有canonical repo；過程產物在Downloads。
  本機測試不變更Google Drive合成文件或既有私人日報；本輪沒有正式部署或排程啟用。
