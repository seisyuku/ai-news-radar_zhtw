# 私人雲端接入：本機實作與 runtime 證據

更新：2026-10-10。依使用者授權自動續行，遇 High 不再要求重新下令。

最新使用者校正：本文件的Cloudflare runtime試驗保留作候選證據；生成在GitHub，
目前優先 [C08-G GitHub生成驗證](DIGEST_GITHUB_GENERATION.md)。正式接入前不需要Cloudflare帳號，
本機相容性試驗不再阻擋生成／測試。

## 目前狀態

| 任務 | 狀態與證據 |
| --- | --- |
| C07a | 完成。單一 Python 校稿規則、交易結果與身份/儲存 ports；SQLite 重開重送已驗。共用 JSON/bytes 核對抽取後全套938項通過 |
| C07b | 本機相容性完成。實際 Wrangler/workerd 中執行 Python EditorialService、SQLite-backed DO、R2；拒絕、保存、並發CAS、程序重開、舊成功重送與原稿條件寫入通過 |
| C07c | 本機 resource-server/MCP 介面完成。RS256驗證、owner/scopes、官方SDK的實際ASGI HTTP授權/工具讀寫與讀回已驗；另完成 TypeScript edge/Python core 的真 workerd 合成試驗 |
| C01b/C07線上 | 未完成。沒有真實身份服務登入、部署網址、自建外掛手機驗收或真雲端持久性證據 |
| C08 | 本機完成：[可信期別意圖、生成前guard、固定commit與有界execution補跑](DIGEST_CLOUD_JOBS.md)，最終全套966項通過；正式issuer與交付job仍未接通 |
| C09～C12 | [C09部署前置](DIGEST_CLOUD_DEPLOYMENT_GATE.md)已整理，待真帳號、預算及身份設定；正式部署與三日驗收尚未完成 |

## C07b 固定工具與實驗邊界

- uv 0.12.24、workers-py 1.17.7、workers-runtime-sdk 1.9.3、Wrangler 4.149.0、
  workerd 1.20261006.1、Node v24.19.0、tzdata 2026.5。
- pywrangler 依 runtime compatibility 另下載 CPython 3.14.8／Pyodide 3.14.2；
  compat date 固定2026-10-06。初次用臺北當日2026-10-10被runtime判為future，已更正；
  runtime日期是相容版本設定，不是日報期別或時區。
- 工具、cache、Python版本、模擬器資料與合成輸出全部保存在 Downloads 隔離目錄。
  本機只聽127.0.0.1；實驗配置 workers_dev=false；所有Cloudflare bindings均為local。
- `/r2` 證明條件寫入阻擋不同bytes，讀回仍通過同一`verify_digest_bytes`。
  `/edit` 證明拒絕receipt不回滾，重開後仍回拒絕；原r1成功重送回applied=1/current=3。
- 初次工具PATH缺uv亦已修正。故障與最終runtime log／request vectors均保留。
- 合成實驗來源、鎖檔、runtime log及前後結果：
  `/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07b-local-probe/`。
  這是本機workerd證據，不代表真雲端一致性、額度、延遲或登入已通過。

## C07c 身份與 HTTP

- `JWTVerifier` 僅接受RS256；配置固定issuer/resource與owner subject，key resolver只收kid，
  不從token的URL取得金鑰。PyJWT檢查簽章、issuer、audience、期限與必要claims；
  服務再檢查owner與scope。測試金鑰為測試時隨機生成的合成RSA金鑰，不是正式憑證。
- 正式provider的JWKS來源、金鑰輪換／撤銷、OAuth discovery/PKCE/callback仍待C09及C01b；
  此程式不建立登入頁或簽發token。部署時必須由真身份服務提供key resolver與設定。
- MCP SDK2.3.0標準wire codec會移除非標準頂層`securitySchemes`。JSON HTTP adapter在SDK
  處理身份/RPC後補上同一工具的OpenAI描述欄位，並保留`_meta.securitySchemes`鏡像。
  HTTP測試確認兩者相同、Content-Length正確、401 discovery challenge及scope拒絕成立。
- `build_mcp_app`使用官方SDK的無狀態Streamable HTTP；未認證的記憶體/stdio直接呼叫也被
  handler拒絕。沒有發布retry工具，直到C08可信意圖與guard正式接通。
- HTTP 在 SDK 解析前拒絕重複 JSON 鍵、NaN 與超過1MiB的內容；這避免正規化掩蓋非法參數。SDK仍負責未授權 challenge。
- 保存後按applied revision重算hash核對；已提交但讀回失敗會明確回committed=true、
  verified=false，不換新request ID重做。大型read可按story IDs分段，完整性標記不靜默截斷。
- MCP/認證依賴列在requirements-cloud.txt，requirements-dev.txt包含它，CI完整測試會安裝。
  實際 Python Workers 打包試驗在 cryptography RSA 匯入時發生 Rust/Pyodide fatal error，服務無法啟動。
  隨後實測 TypeScript MCP/JWT 外層經私人 service binding 呼叫同一 Python 核心，完成401/權限拒絕、保存讀回及程序重開。
  這條替代只驗證合成 fixture，尚未提供正式 adapter/issuer；來源、版本、結果與限制見 [C09 準備報告](DIGEST_CLOUD_DEPLOYMENT_GATE.md)。

官方參考：[Python Workers套件](https://developers.cloudflare.com/workers/languages/python/packages/)、
[MCP Python SDK授權](https://py.sdk.modelcontextprotocol.io/run/authorization/)、
[OpenAI工具欄位](https://developers.openai.com/plugins/reference#_meta-fields-on-tool-descriptor)。

## 交接與驗證

- C07a：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07a-20261010-023104/`。
- C07c：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07c-local/`。
  首次14通過／1失敗（頂層授權欄位被SDK移除），第二次同失敗，補入JSON描述欄位adapter後
  階段最終15項通過；完整 **953 passed in 3.55s**。C08整合後最終 **966 passed in 5.19s**。
- 本輪雲端尚無真實設定，正式日報與自動排程仍未接通。
