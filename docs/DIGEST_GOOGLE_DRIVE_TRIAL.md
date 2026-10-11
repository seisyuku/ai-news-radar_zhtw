# C08-D：Google Drive 校稿與設定試用

## 2026-10-12 新app授權交付試驗

使用者完成專案自己的desktop OAuth/drive.file授權後，已經由本機程式實際刷新token並建立三份合成native Google Docs。不是使用ChatGPT connector代替GitHub授權：這次建立/複製/修改/讀回由新app憑證執行，connector另做三份讀取驗證。

新app可見的ChatGPT根資料夾與試用子資料夾由app建立；沒有猜既有資料夾IDs有權讀寫。原稿兩則合成標題，native copy後副本第一則改成「校稿保存成功」，原稿文字與revision保持。設定JSON讀回吻合：Asia/Taipei、06:00、github-actions、automation_enabled=false；此文件尚未由生成器消費。

三份文件及兩層目的資料夾permissions只有user/owner、metadata shared=false/owners.me=true。未要求profile/email scope，未列印owner信箱。這是owner-only metadata證據，不增加匿名/跨帳號測試；不將它等同C02原子提交/不可變正本。設定及校稿使用native TITLE；不增加PDF或語音轉寫測試。

現有ChatGPT Drive connector三份讀回成功，副本/原稿標題差異及設定JSON核對。使用者同日回報iPhone確認新校稿副本「校稿保存成功」，手機驗收完成，不重測歷史三份。私人file IDs/URLs/完整讀回存 `/Users/lordmi/Downloads/ai-news-radar-desktop-auth-20261012/`，不放repo。沒有正式日報、GitHub runner交付、secret、push或排程；External/Testing七天期限與正式接線仍待完成。

接正式交付前須裁決舊C02控制層與單人Drive路線的交付标准：建議私人保存/讀回、程序不覆寫原稿與人工校稿，不宣稱owner不可改及跨檔原子交易；未同意前不修改契約或自動增加服務。最新提案見HANDOVER頂部。

以下為2026-10-10 connector試用歷史紀錄，最新停點以上述新app試驗及HANDOVER為準。

更新：2026-10-10。使用者選擇先嘗試 Google Drive 校稿與設定。**現有 connector 的合成讀寫試用完成；GitHub 自動寫入與正式日報未接通。**

2026-10-11使用者已確認三份新連結在iPhone均可開啟且校稿正確，帳號為一般個人Google帳號。
下文手機／帳號待確認是歷史停點，最新入口為 [專案OAuth授權準備](DIGEST_GOOGLE_DRIVE_AUTH.md)。
使用者回報回應控制碼外露，往後使用正常文字連結；這項明確要求優先於技能output citation格式。

## 已實測

在現有 Google Drive 連線中建立私人 ChatGPT 資料夾及三份 native Google Docs：試用設定、合成原稿、由原稿複製的校稿副本。既有 C01 測試文件未修改；本輪精確名稱搜尋沒有找到它，不推定桌面與 iPhone 是同一 Google 帳號。

- 設定文件寫入固定臺北06～06窗口、GitHub生成位置及合成JSON，重新讀取後解析欄位正確。只改試用狀態，不改日報規則。
- 合成原稿包含兩則明確標示的虛構內容；native copy後，在校稿副本修改第一則標題與副本標記。副本讀回吻合，原稿內容及文件revision保持原值。
- 寫入帶Google Docs的`requiredRevisionId`。刻意用舊revision送第二筆合成寫入，API以400／INVALID_ARGUMENT拒絕；再次讀取沒有測試標記，也沒有改掉已保存的內容。
- 三份文件及資料夾的最終metadata均`shared=false`、permissions只列一個user/owner；沒有呼叫分享工具或改既有分享。這是權限metadata證據，未實測另一帳號或匿名讀取。
- 使用原生TITLE樣式；文字／位置／JSON／原稿保留／目的資料夾已核對。此輪沒有PDF版面驗收，手機開啟仍待使用者實測。

私人file ID、URL、revision與完整合成讀回只放Downloads檢查點，不寫入公開repo或Actions摘要。檢查點：`/Users/lordmi/Downloads/ai-news-radar-drive-trial-20261010/`。

## 設定與校稿的適用範圍

設定文件目前是**保存與讀回試用**，沒有程式消費它。JSON的`automation_enabled=false`不代表已建立排程控制器；變更此欄位不會啟用GitHub工作。

本次試用不新增來源、付費抓取、LLM生成、發布、保存清理或設定執行能力。正式設定只允許已同意的欄位；文件中的自由文字與新聞內容不能當作指令、API網址、憑證或權限授予。

保留原稿與修改副本證明流程分離，不代表擁有者不能手動改原稿，也不代表Drive已滿足C02完整不可變儲存／request receipt／原子交付契約。
Google Doc的revision guard能拒絕過時文件寫入，但不是專案的遞增校稿revision或idempotency receipt；不能直接把新Doc當成C05資料庫。
正式接入要維持原MD/meta核對，原稿／校稿／設定分開，核對寫入及讀回；native Doc用於閱讀／校稿，原始pair仍須保存為既有產物格式。不得為了方便改成公開artifact或把副本同步當成正式交易已完成。

## 下一段：GitHub如何寫入

現有connector成功只證明此對話的連線能讀寫。此輪沒有讀取或轉用connector的憑證，也沒有設定GitHub Google授權。

候選路線依帳號決定，尚未建立新的OAuth app、service account或shared drive：

| 帳號情況 | 待審閱的接入路線 |
| --- | --- |
| 一般個人Google帳號／My Drive | 專案自己的Google OAuth，透過官方頁面一次性授權offline access；runner用安全儲存的refresh token取得短期access token。優先評估drive.file範圍，不要求整個Drive管理權限 |
| 已有Google Workspace共享雲端硬碟 | 再評估GitHub OIDC／Workload Identity Federation與服務帳號，在指定shared drive工作；需用實際帳號確認能力及權限，不能假設已具備 |

`drive.file`只涵蓋該app建立或使用者向該app選定的檔案；另一個OAuth app不能因已知道這輪文件ID便推定有權讀寫。正式位置與設定文件須向該app授權或由它建立，然後再驗手機connector可讀。[Google Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)。

定時工作需offline授權才能在使用者不在場時刷新access token；這不等於Mac需要開機。
External／Testing的OAuth app，含Drive scope的refresh token會在7天到期，不能當作永久每日交付設定。
正式試用須先確認app狀態、撤銷／重新授權流程，不以排程已觸發當保存成功。
[Google offline access](https://developers.google.com/identity/protocols/oauth2/web-server#offline)、
[Refresh token有效條件](https://developers.google.com/identity/protocols/oauth2#expiration)。

服務帳號沒有個人Drive儲存額度且不能擁有檔案，不把「把資料夾分享給service account」視為個人My Drive可直接建立每日稿的已驗路線；需shared drive或代表人類的OAuth。
[Google Drive quota限制](https://developers.google.com/workspace/drive/api/guides/handle-errors#storageQuotaExceeded)。

## 目前停點與交接

先由使用者用iPhone開啟校稿副本，核對第一則含「校稿保存成功」，並回報使用一般Google帳號或Google Workspace。下一段再針對實際帳號準備具體GitHub寫入授權與受保護合成試驗。

本輪只有雲端合成文件與交接文件變更，沒有改生成程式／workflow、push、GitHub dispatch、Cloudflare或每日排程；不為文件試用重跑已通過的982項Python測試。這個數字是前階段歷史結果，不能拿來代表Drive端驗收。
本輪驗證是實際connector寫入／讀回／複製／過時寫入拒絕及權限核對，具體結果在`connector-evidence.json`。

下一階段例行授權接線可沿用GPT-6.1 Sol／High；若需修改私人交付交易契約或選新身份架構，先用Astra／High審查並呈現裁決。不新增正本／遠端SHA查驗。
