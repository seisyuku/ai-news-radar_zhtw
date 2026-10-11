# AI News Radar Pulse — 交接摘要（截至 2026-10-12）

## 2026-10-12 新正式憑證GitHub交付已驗；每日觸發待選

- 使用者要求繼續執行。當時臺北約02:00、10/12窗口尚未06:00截止，故明確以10/11歷史模式實跑新正式憑證，不保存未完成的10/12當期稿。[38162146429](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/38162146429)success，3則；pair/rerun/delivery_verified均true，storage_saved_at為2026-10-11T18:03:11.303087+00:00。仍是manual_historical／review-only，不算今天或每日準時達標；本輪新token已由runner消費。
- 既有外部心跳近期:05／:35有成功工作；[38160263615](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/38160263615)guard真SOURCE heartbeat、30分鐘間隔並接管更新，確認可沿用。沒有登入或修改cron-job.org、PAT、刷新schedule與設定Doc。
- 完成 [每日觸發具體提案](DIGEST_DAILY_TRIGGER_PROPOSAL.md)：A沿用既有刷新完成事件，通常07:35主嘗試／08:35補試；B專用外部07:15／08:15觸發。兩者都需明確接受GitHub觀測建立時間固定臺北期別，取代本路線歷史C02獨立持久intent issuer要求；未默默取消契約或直接啟排程。
- 規劃當期已保存稿核對後跳過、第一次完成時間私人紀錄、人工校稿保留與部分保存停止；不新增交易服務、通知、來源刷新、LLM或私人稿公開發布。等待觸發選項與期別簡化方式裁決，尚未改產品程式或workflow。只做文件差異，diff check通過，不重跑本機完整套件或SHA核驗。
- ROADMAP的舊PAT約10/17到期提醒與既有10/01使用者替換紀錄矛盾，已更正為使用者回報無到期日，沒有重建PAT或改續期政策。
- 私人檢查點Downloads `ai-news-radar-daily-trigger-20261012/` 保存安全report、已觀測原稿／校稿真URL與交接；真URL／IDs不入repo。下一階段例行Sol／High，選A或B且接受期別方式後接線；每日尚未啟用。

## 2026-10-12 正式OAuth與GitHub憑證更新完成

- 使用者在最後動作當下回覆「確認執行」。於既有私人Chrome無痕工作階段、ai-news-radar-daily專案確認發布；Google Audience顯示「實際運作中」及「返回測試應用程式」，External保持。沒有新增scope、帳號、付費服務或審查申請。
- 以同一Desktop client／PKCE／loopback新授權，Google已有存取權清單僅一項特定Drive檔案權限。一次Google同意頁500，正常刷新一次即恢復；不是權限不足或程式錯誤，未為此改程式或繞過安全提示。CLI exit0、authorized／credentials_saved；新憑證另存Downloads私人檔案，舊憑證保留，未輸出授權code/token。
- 新授權JSON的drive.file-only／Bearer／必要refresh欄位、無access token保存及0600／0700核對通過。以新refresh token取得短期token，既有私人目的資料夾／設定文件metadata及固定設定唯讀成功；Drive文件與分享不變。
- 以compact JSON經標準輸入成功更新既有GOOGLE_DRIVE_OAUTH_CREDENTIALS Secret；目標Secret與其他Secrets不變。本輪沒有重跑歷史交付，故不宣稱新token已由GitHub runner實際消費；先前runner交付成功證據仍見下方。
- Testing固定七天到期前提已解除；正式refresh token仍受Google一般撤銷／到期規則約束，不能稱永久有效。[Google token條件](https://developers.google.com/identity/protocols/oauth2#expiration)。
- 本階段只處理授權／憑證與同步交接，未改產品程式、重跑完整套件或新增SHA查驗；diff check通過。每日私人生成排程、外部觸發、有效當期驗收與人工發布仍未啟用。下一段先定每日觸發時間／來源及失敗補觸發方式，不擅自新增服務或排程。例行接線Sol／High；若新增服務或權限邊界再裁決。
- 私人檢查點Downloads `ai-news-radar-google-production-20261012/` 的STATUS.json、authorization-result.json與HANDOFF.md；真憑證／私人IDs不入repo。以下待確認段落為先前歷史紀錄，以本節為準。

## 2026-10-12 三份OAuth公開說明頁已批准

- 使用者已同意三份工具說明／隱私權說明／使用說明發布於既有GitHub Pages，並用於Google OAuth品牌設定。此許可接續先前Testing→In production授權；不新增主機、付費服務或私人稿件公開分享。
- 將已準備的三份HTML加入網站根目錄，移除草稿標記、保留手機可讀排版與相互導覽。公開新聞首頁、來源、生成窗口與既有排程保持原設定。
- 三頁已正常push並由既有Pages發布；實際HTTP讀回均200、名稱正確且沒有草稿標記。Pages工作38160634053 success。推送前整合既有新聞排程更新，未force或另做SHA比對。
- 已於私人Chrome無痕工作階段補上三個公開URL及seisyuku.github.io授權網域，Google回報「已儲存品牌宣傳變更！」。Audience仍Testing，但「發布應用程式」按鈕已啟用；無網域驗證阻塞畫面，未送額外審查。
- 下一步為Google正式發布的最後確認，再以新私人檔名重新桌面授權及更新既有GitHub Secret。瀏覽器工具要求擴大安全敏感存取須在動作當下確認，即使先前批准；不是再次裁決架構或公開三頁。尚未切正式、產生新憑證或更動GitHub Secret。
- 每日私人日報排程仍是後續階段；不重做手機驗收、歷史交付或完整程式測試。只改公開說明與交接，diff check通過；下一階段例行Sol／High。私人過程只存Downloads檢查點。

## 2026-10-12 正式OAuth已授權；Google品牌設定擋住發布

- 使用者已同意Testing改In production並授權自動執行，不重問這項許可。唯讀查看可用瀏覽器後，以先前本人授權用的Mac Chrome無痕視窗開Console；確認個人帳號與ai-news-radar-daily，不沿用IAB商業帳號。
- 真Audience頁仍Testing，發布應用程式按鈕disabled，畫面明確要求在Branding完成設定。Branding已有名稱/支援信箱/聯絡資訊，首頁/隱私政策/條款連結與授權網域空白；未填假URL或嘗試绕過disabled UI。
- [Google品牌說明](https://support.google.com/cloud/answer/15549049)列外部正式app的連結要求；[個人自用免OAuth審查](https://support.google.com/cloud/answer/13464323)不等同此專案UI已可發布。沒有額外要求買網域或申請審查，也未假定免除目前品牌設定。
- 已將工具說明/隱私權說明/使用說明三份可閱HTML草稿與具體方案存Downloads `ai-news-radar-google-production-20261012/`；不含私人email、Docs IDs/URLs或憑證。另合併成一份私人native Google Doc供iPhone審閱，內容讀回及owner-only核對通過，真URL僅存該目錄draft-drive-evidence.json。建議用既有GitHub Pages的三個獨立資訊頁補OAuth品牌，不改新聞首頁產品規則、不新增hosting/付費服務。
- 待使用者裁決的是新增公開說明頁範圍，不是再授權In production。尚未把草稿放repo或公開網站、填品牌URL、提交審查、改正式狀態或產生新token；GitHub現有手動交付仍可短期使用Testing token。新排程未啟。
- 下一步讀該Downloads/HANDOFF.md；得到公開資訊頁範圍許可後再發布/填品牌/切正式OAuth/重新授權及更新既有Secret。既有手機與歷史交付不重跑，無SHA查驗。例行Sol／High；新公開定位或資料用途裁決再Astra／High。

## 2026-10-12 單人Drive契約已批准；手動GitHub交付接線

- 使用者已許可簡化C02，現行單人路線以 [Drive交付操作](DIGEST_GOOGLE_DRIVE_DELIVERY.md) 及C02頂部2026-10-12決策為準。舊不可變/交易控制mock保留歷史，不新增服務、不拿舊要求阻塞此路線。
- 新增 `digest_drive_delivery.py`，手動生成入口/workflow可選deliver_drive（預設false）。保存原始MD/meta並下載讀回，native原稿/獨立校稿副本，owner-only目的地及設定字段核對。同mode/issue/base重送讀取既有文件、不改人工副本；不同base停止，不自動换稿。部分保存失敗不宣稱成功，不清除或覆寫。
- 新增12項必要接線測試，相關28通過，完整 **1042 passed in 5.72s**，編譯及diff check通過。未新增SHA清冊/遠端比對或重測手機語音。本機真API歷史審閱保存成功，原始pair/可讀原稿/副本讀回驗證；本機快照為10/03，對10/12資料不足、選題零則，不宣稱今日有效日報。
- GitHub登入/儲存庫擁有者seisyuku及push權限確認；已用標準輸入設定GOOGLE_DRIVE_OAUTH_CREDENTIALS及GOOGLE_DRIVE_DIGEST_TARGET Secrets，未輸出值或寫repo。兩個名稱原先不存在，未改其他Secrets。
- 推送完成：先前已授權的合成基礎/依賴與本輪接線分兩個提交；首次push因遠端較新拒絕，正常pull --rebase後重推，未force或做額外SHA核驗。GitHub [手動歷史交付38157491285](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/38157491285) **success**，delivery_verified/pair_verified/rerun_identical均true，historical/review-only、零題；as-of在本期06:00前，不算今日達標。原MD/meta与可讀原稿/校稿由runner保存，實際私人入口只存Downloads。既有 [Offline tests38157457066](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/38157457066) success。
- 多行credentials Secret的單獨JSON括號被GitHub自動遮罩，污染安全摘要JSON；已將同內容改compact單行保存，沒有變更token/scope或重跑成功交付。既有設定Doc僅更新驗證狀態及已供手動流程讀取的說明，requiredRevisionId写入并讀回；automation false，未改窗口/分享/原稿/校稿。
- 下一停點：OAuth仍External/Testing，需使用者許可將app publishing status改In production並重新授權，解除固定7天測試期限。正式狀態允許其他Google帳號提出自己資料的授權，不會自動分享本人的Drive；不加scope、不啟排程。沒有新schedule、分享、發布稿件、Cloudflare部署或改來源刷新。下一階段授權例行Sol／High。
- 本輪檢查點 `/Users/lordmi/Downloads/ai-news-radar-drive-delivery-20261012/`。下一階段例行Sol／High；新的身份/交易範圍裁決再Astra／High。

## 2026-10-12 iPhone新app校稿驗收與交付契約裁決（已批准，見頂部）

- 使用者已確認iPhone新校稿副本顯示「校稿保存成功」。新app的API保存/內容/owner-only、connector可讀及手機開啟驗收完成，不重測既有連結或語音。
- 自動續行檢查 [C02契約](DIGEST_CLOUD_CONTRACT.md)：它明確保留不可變MD/meta物件、交易式delivery/attempt/request receipts及revision控制為正式自動交付要求；目前Drive三份文件試用不具備這層控制。不能在未裁決下假定舊契約已取消，或擅自加交易服務。
- 建議單人GitHub+Drive路線採簡化交付標準：私人保存原始MD/meta、native原稿及獨立校稿副本；程序不覆寫既有原稿/人工校稿，沿用pair核對，保存與讀回核對後標私人保存成功。清楚保留owner可手動修改Drive原稿及無跨檔原子交易的界線；生成/快照時效分開，不新增SHA查驗或保守驗證程序。本建議尚未批准，沒有修改C02條款或實作workflow。
- 具體提案及交接存Downloads `ai-news-radar-desktop-auth-20261012/NEXT-DESIGN.md` / HANDOFF.md。需使用者決定簡化本路線的C02控制層要求，或保留原要求另行設計；決策前不新增服務、scope、GitHub secret、push、OAuth正式狀態或schedule。
- 設計裁決建議Astra／High；確定後例行接線Sol／High。Google External/Testing七天期限仍是正式運作前需處理的外部設定。

## 2026-10-12 新app私人合成Drive/Docs交付驗證完成

- 使用者授權在已同意範圍內自動續行；不加SHA核驗，不因保守寫法擴大驗證。以已授權的desktop client刷新token，在私人Downloads的一次性probe建立三份合成native Docs：原稿、native copy校稿副本、合成設定。未更改既有試用文件或分享。
- 新app只要求drive.file；app可見的ChatGPT根資料夾與私人試用子資料夾由app建立，不假設既有connector資料夾已向此app授權。三份新文件讀回內容吻合；副本第一則「校稿保存成功」，原稿文字/revision保持。設定是保存試用，06～06/GitHub生成/automation false，尚未由生成程式消費。
- 三份文件與目的資料夾metadata/permissions只有user owner、shared=false、owners.me=true。此證據未擴大為匿名/其他帳號拒絕測試，也未宣稱Drive滿足C02完整不可變/原子交易契約。
- 現有ChatGPT Drive connector已讀回三份文件，內容/標題/設定吻合。使用者後續確認新校稿連結在iPhone開啟，最新停點見本文件頂部；不把歷史舊連結驗收冒充本次證據。
- 私人IDs/URLs/完整讀回只存Downloads `drive-live-evidence.json`、`connector-readback.json` 及HANDOFF。沒有新增產品程式/workflow、重跑測試、SHA查驗、GitHub secret、push、排程、Cloudflare或公開分享。先前1030項為桌面helper歷史測試結果，本輪證據是真API建立/複製/修改/讀回/權限與connector讀取。
- 正式長期自動化仍待處理External/Testing七天refresh token期限、GitHub私人交付及MD/meta保存；本機API成功不是GitHub runner已驗。下一階段例行Sol／High，C02交易/身份契約有新裁決再用Astra／High。

## 2026-10-12 桌面Google Drive授權準備

- 使用者已回報專案ID/編號、Drive/Docs APIs、External/Testing自己為test user及僅`drive.file`範圍完成。商業與私人帳號須隔離；使用專用profile或新無痕工作階段，先確認帳號和專案。以上控制台狀態為使用者回報。
- 使用者指定Downloads桌面client JSON；僅核對installed格式、專案ID及必要欄位，未輸出密鑰。改用 [桌面授權入口](DIGEST_GOOGLE_DRIVE_AUTH.md)，修正先前device flow適用性判斷。新增PKCE/state、127.0.0.1暫時listener、15分鐘超時、錯Host/state拒絕及私密保存；不自動開瀏覽器。
- 23項新桌面合成測試與25項歷史測試共48通過；配置現有bundled Node至本次PATH後全套 **1030 passed in 5.57s**，py_compile與diff check通過。先前測試因Downloads父目錄缺少而出現4項setup errors；第一輪全套因PATH沒有node出現39項前端測試失敗，配置既有runtime後完整重跑通過，未為環境問題改產品程式。
- 真Google登入同意已完成：使用者回報「Response received」，本輪CLI正常exit 0、回報authorized/credentials_saved。私人檔案讀回核對有refresh token及client欄位、scope僅drive.file、Bearer、未保存access token，檔案0600/目錄0700。授權流程不要求profile/email，故未藉token獨立辨認帳號信箱；帳號由使用者在隔離瀏覽器選取。
- 下一步為使用新app建立合成原稿/校稿/設定，保存讀回與owner-only ACL、iPhone/Chat connector可讀驗收；不能直接假設既有connector試用文件對此app已授權。沒有Drive寫入、GitHub secret、push、啟排程或新增SHA比對。External/Testing為短期授權驗證，正式自動化前須處理7天refresh token期限。
- 私人交接目錄：`/Users/lordmi/Downloads/ai-news-radar-desktop-auth-20261012/`。下一阶段例行授權接線建議Sol／High；新的身份/交易裁決用Astra／High。

## 2026-10-11 已選日報專用Google專案；建立結果待手機核對

- 使用者選擇「建立日報專用專案」，選型已定，不再詢問是否沿用舊專案。已在登入中的Google Cloud控制台填入 `AI News Radar Daily` 並提交；表單曾顯示候選ID，跳到creatingProject頁，但沒有可驗證的成功結果。
- 控制台的近期專案、通知、資源選擇器及目標專案核對頁持續顯示載入錯誤；核對頁按「重試」一次後仍無法載入。**專案是否建立成功未知**，不得將候選ID當成正式配置、重複建立或在未知專案啟API/client。
- [Google專案建立交接](DIGEST_GOOGLE_PROJECT_SETUP.md)。下一動作由使用者在iPhone控制台搜尋 `AI News Radar Daily`，回報是否出現及實際專案ID；不重做已完成的Drive文件手機測試。
- 未連結帳單、啟Drive/Docs API、建立OAuth client、簽發憑證、改workflow、push或啟排程。程式沒有改動，本輪不重跑歷史1007項測試，亦不新增SHA查驗。
- 檢查點 `/Users/lordmi/Downloads/ai-news-radar-google-project-20261011/` 保存狀態、錯誤畫面及交接。例行接線Sol／High；新的身份／交易裁決再用Astra／High。

## 2026-10-11 iPhone確認與個人Google授權準備完成

- 使用者確認三份Google文件均可於iPhone開啟，校稿內容吻合，使用一般Google帳號。新連結手機驗收完成，不再要求重做；不擴大為跨帳號／匿名拒絕已驗。
- 使用者回報citation控制碼外露，後續改普通Markdown文字連結；[正式交付顯示規則與授權入口](DIGEST_GOOGLE_DRIVE_AUTH.md)。已把手機確認、帳號類型及顯示偏好寫回設定文件並讀回；不改原稿或校稿、不變分享。
- 新增Google Drive-file-only手機device authorization helper及25項合成測試；全套 **1007 passed in 5.84s**。沒有呼叫真Google授權、建立OAuth app、讀取真憑證、設GitHubsecret或改workflow。手機登入短碼只在有專案client後才產生，不製造預先可用的授權連結。
- 下一個需要使用者決定的項目是 **Google Cloud專案：使用現有專案或新建日報專用專案**。決定後再準備API/client與手機授權。生成仍在GitHub、Cloudflare延後、沒有啟每日保存或排程；沒有新增SHA查驗。
- 完整交接：`/Users/lordmi/Downloads/ai-news-radar-drive-auth-prep-20261011/HANDOFF.md`。例行授權接線Sol／High；若需新身份或交易裁決，Astra／High。

## 2026-10-10 C08-D Google Drive校稿與設定試用完成

- 使用者選擇先嘗試Google Drive，已以現有connector完成 [校稿與設定實測](DIGEST_GOOGLE_DRIVE_TRIAL.md)。建立設定、合成原稿及native校稿副本；修改副本讀回正確，原稿內容/revision未改。舊revision寫入被400拒絕，讀回沒有副作用。
- 設定的合成JSON已讀回解析；只是設定保存試用，尚未供生成程式消費。三份文件及目的資料夾的權限metadata只列owner／shared=false；未變更分享，匿名/另一帳號拒絕與iPhone開啟仍待驗。
- 本輪精確搜尋未找到舊C01文件，不推定手機與桌面Google帳號相同。請手機開校稿副本核對「校稿保存成功」，並確認一般Google帳號或Workspace，才能決定下一段GitHub寫入授權。
- GitHub生成位置與06～06窗口保持。connector不是GitHub的已配置憑證；正式寫入需要專案自己的Google授權，Cloudflare繼續延後。
- 私人file IDs/URLs/revisions及讀回只保存在 `/Users/lordmi/Downloads/ai-news-radar-drive-trial-20261010/connector-evidence.json`，公開repo不含它們。沒有改生成程式/workflow、push、啟排程、發通知或上傳真日報；本輪不用歷史982測試冒充Drive驗收。
- 下一入口為手機連結/帳號類型確認，再準備Google授權方案。例行接線Sol／High；若保存交易/身份需新裁決，Astra／High。完整交接在同檢查點HANDOFF.md。

## 2026-10-10 最新範圍校正：先完成 GitHub 生成，Cloudflare 接入延後

- 使用者確認架構 A 的生成在 GitHub；Cloudflare 是正式私人保存／手機入口的候選，不能當作生成前置。先前將帳號、預算視為下一步阻塞的安排已撤回。下方 C09 停點是歷史紀錄，以本節為目前入口。
- [C08-G GitHub 生成與驗證](DIGEST_GITHUB_GENERATION.md)：新增直接讀 checkout 的生成入口與手動 workflow，產生 MD/meta、配對核對及確定性重跑；不呼叫遠端查 SHA 或建立程式雜湊清冊。保留既有稿件完整性核對。
- 生成、私人持久保存、手機閱讀／校稿分開驗收。新工作回 `delivery_verified=false`；runner 收尾清除私人稿，只留安全摘要。每日外部觸發、跨工作去重、保存與手機交付仍未接通。
- 原 C07～C08 模擬及 Cloudflare 本機試驗保留為後續參考，不把它們當成本階段前置。既有來源刷新／Pages／驗證 schedule 未改。
- 本輪初次相關75項通過；最終全套 **982 passed in 5.40s**，Python編譯、workflow shell／YAML與差異檢查通過。新增workflow變更納入原Offline tests的push/PR路徑範圍；既有schedule未改。
- 本機真checkout產稿已完成MD/meta核對及相同bytes重跑；本機快照as-of為 `2026-10-02T23:35:46.191951Z`，對10/10期別只可review-only，選題零則不代表當日無新聞。試跑明確標historical且delivery_verified=false，私人產物保留在本輪Downloads檢查點。沒有為此刷新來源或同步遠端。
- 尚未 push、GitHub run、部署或啟用新排程；GitHub真run與有效當期日報不能用本機舊快照試跑代替。
- 此階段的保存位置待決已由後續Google Drive合成試用續接；目前尚未正式接通GitHub保存。交接在 `/Users/lordmi/Downloads/ai-news-radar-github-generation-20261010/HANDOFF.md`，以頂部C08-D為最新入口。

## 2026-10-10 自動工作重新核對：C08 本機完成，C09 待外部設定

- 最終完整 **966 passed in 5.19s**；Python 編譯、JavaScript 語法、workflow 結構與差異檢查通過。重啟後沿既有檢查點核對，沒有清除先前工作。
- [C08 本機工作協調](DIGEST_CLOUD_JOBS.md) 已完成可信模擬意圖、生成前排他 guard、固定 commit、租約與最多三次 execution、通知去重計畫及公開摘要白名單。修正暫時失敗被標為終態、重新生成時間污染去重，以及提交成功後協調紀錄失敗的恢復問題。
- Python MCP/crypto 直接打包至 Workers 的實際試驗失敗；改用 TypeScript 身份/MCP 外層經私人 binding 呼叫同一 Python 核心，本機已驗證授權、保存讀回與重開持久性。詳見 [runtime 證據](DIGEST_CLOUD_RUNTIME.md)，這仍是合成試驗。
- 新增手動合成合約 workflow；修正既有兩份驗證 workflow 的測試暫存目錄，使其符合 Downloads 路徑規則。既有觸發時刻未改，尚未於 GitHub 執行這批新變更。
- [C09 部署前置與設定範本](DIGEST_CLOUD_DEPLOYMENT_GATE.md) 可審閱；本機未有可用 Cloudflare 登入設定，月費上限及真 OAuth 尚未指定。正式持久控制／intent issuer／交付 workflow、C01b 手機自建工具、C10a～C12 驗收仍未完成。沒有部署、啟用新排程或發送通知。
- 完整自動工作交接：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/AUTO-C07-C09-20261010/HANDOFF.md`。下一步 **C09 配置與 provider 定案審查，Astra／High**；定案後例行接線用 GPT-6.1 Sol／High。

## 2026-10-10 C07b／C07c 本機接入完成

- [Runtime、身份與MCP證據](DIGEST_CLOUD_RUNTIME.md)。C07b實際workerd本機試驗通過DO交易、R2條件寫入、程序重開與版本重送；C07c resource-server使用官方SDK及RS256 owner/scope驗證，HTTP讀寫／讀回與未授權拒絕通過。
- 此階段新增15項C07c測試；階段完整 **953 passed in 3.55s**。真OAuth登入、JWKS／撤銷與C01b手機自建外掛仍待驗；後續套件打包失敗及替代試驗見頂部最新交接，不能將本機成功稱為正式接通。
- C07b過程在Downloads/C07b-local-probe，C07c log與快照在Downloads/C07c-local（完整絕對路徑見runtime文件）。依使用者新授權自動繼續C08；模型建議仍為GPT-6.1 Sol／High。

## 2026-10-10 自動續行與 C07a 完成

- 使用者授權自動執行至無可執行任務，並要求換模型後從此階段起點重新核對；這取代先前每到 High 就停止的續行限制。平台帳號、實際預算、登入與實機證據仍須具體確認，不能假設存在。
- C07a 已抽出 [純校稿交易規則](../scripts/digest_cloud_editorial_rules.py)、[儲存與身份介面](../scripts/digest_cloud_ports.py)，服務透過交易回傳的結果保存成功／永久拒絕 receipt，再在交易外回報錯誤。既有 mock 與預覽相容。
- [共用 JSON/identity](../scripts/digest_json.py) 與 [bytes 配對核對](../scripts/digest_integrity.py) 避免雲端校稿服務匯入新聞生成器；`digest_document` 與檔案核對入口保留原 API 與既有核對規則。
- [SQLite 交易邊界測試](../tests/test_digest_cloud_ports.py) 驗證拒絕紀錄、重開後重送、後續版本不被舊回應覆蓋，以及授權失敗先於儲存操作；SQLite adapter 僅為測試 fixture。另驗證檔案/bytes 邊界均拒絕竄改及錯誤編碼。
- 模型重啟後首輪相關 69 項通過、首輪全套 932 項通過；完成共用 bytes 抽取後最終 **938 passed in 3.51s**。下一步 C07b 候選平台本機 runtime 試驗，已準備隔離工具與合成資料，尚未宣稱平台驗收。
- C07a 檢查點：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07a-20261010-023104/`。本輪尚無正式雲端服務、真登入或排程啟用。

## 2026-10-09 C07 雲端接入審查完成

- [C07 審查、裁決與下一步](DIGEST_CLOUD_C07_REVIEW.md)：架構 A 有條件可行，C07 實作與線上驗收仍未完成。C01a 現成外掛代理驗證完成；C01b 自建工具的手機登入與讀寫保留待驗。
- C05 與記憶體私有欄位直接耦合，不能只換儲存設定。特別是記下永久拒絕後拋錯的做法，移入真正資料庫交易會回滾 receipt；先拆出規則與交易邊界，再接平台。
- 優先評估 Workers + SQLite-backed Durable Objects + 私人 R2；Python 執行相容性、身份服務、帳號及費用尚待驗證／定案。Google Drive 不自動成為正式校稿資料庫。
- 解開驗收次序：C07a～c 做本機接入準備，C09 準備具體部署設定，核准後 C10a 用受保護合成環境完成 C01b/C07 實機門檻，再進真日報；不以 mock 通過冒充雲端驗收。
- 本輪 **65 項相關合成測試通過**，只改文件；沒有改程式或正式稿、部署、啟排程或 commit/push。檢查點：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C07-review-185036/`。
- 下一步 **`run C07a`，GPT-6.1 Sol／High**：抽出儲存與身份介面，保留單一校稿規則、相容 mock 與拒絕 receipt 語意。停於下一 High 任務前。

## 2026-10-09 C01 iPhone 雲端能力代理驗證

- 使用者在 iPhone 一般 Chat／Work 以 `@Google Drive` 實際搜尋、建立、編輯並跨對話讀回私人合成文件；內文「藍色貓咪七號」由手機畫面核對。建立時需點選批准，編輯時未再次要求批准；分享設定查得僅本人可存取。
- Mac 離線時，使用者回報 iPhone 一般 Chat 仍可處理該 Google Drive 文件。這證明此帳號的現成外掛路徑不依賴已配對的 Mac；未記錄離線時執行的精確讀寫動作。
- 使用者可少量觸控，目標是避免大量手機編輯；持續語音朗讀與逐字聽寫不是驗收條件。外掛曾正確列出內容但未發聲。
- 此為**現成 Google Drive 外掛的代理驗證**，不代表專案自建 MCP/API、候選儲存服務、OAuth 權限範圍、持久交易或跨帳號拒絕已驗收。C07 仍須先審查真實平台與身份邊界；停在 C07 High，建議 **Astra／High**。
- C01 詳細交接：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C01-mobile-validation/HANDOFF.md`。本輪未改程式、部署或啟用排程。

## 2026-10-09 C06 合成私人網頁本機預覽完成

- 新增 [C06 本機預覽服務](../scripts/digest_cloud_preview.py)、
  [手機尺寸介面](../private_preview/index.html)、
  [操作與限制](DIGEST_CLOUD_PREVIEW.md)、
  [五項驗收測試](../tests/test_digest_cloud_preview.py)。頁面直接使用 C05 的
  原稿、校稿 revision 與選版 API，不另造一套編輯狀態。
- 顯示期別、狀態、原稿、revision、來源及題號→story ID；可保留/排除、
  重排、聽寫欄位校稿、儲存讀回、還原、明確選版與匯出。寫入帶
  request ID 與 expected revision；衝突顯示目前版本及重新讀取入口，
  不把單次 HTTP 成功當成保存完成。
- 本機瀏覽器實際操作標題校稿與讀回、還原，以及兩頁並發導致的
  revision 衝突；手機寬度排版可讀。這**不是** iPhone 實機、語音控制、
  真正私人遠端網頁、持久保存或 Mac 關機驗收。
- 首次新測試有四個 fixture token 設定錯誤；第二輪有一個合成 slot 重複
  而被正確拒絕。修正測試配置後五項通過；最終完整離線套件
  **928 passed in 3.37s**，Python 編譯、JS 語法與差異檢查通過。
- [C06 完整交接與 C07 精確入口](DIGEST_CLOUD_CONTRACT.md)。停於 C07 High，
  C01 現成外掛的手機能力代理查核已完成，真實專案工具仍待驗證。建議 **Astra／High** 審查路線，
  若只按已驗證平台接線可改 **GPT-6.1 Sol／High**。
  未部署、連外、啟用排程、取得憑證、修改真實私人稿或 commit/push。
- C06 交接證據：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C06-handoff/`。

## 2026-10-09 C05 校稿版本與匯出模擬完成

- 新增 [C05校稿服務](../scripts/digest_cloud_editorial.py) 與
  [驗收測試](../tests/test_digest_cloud_editorial.py)。同base的修改以revision條件交易，
  語音/網頁並發只有一方成功；request去重保留首次結果及目前版本，不靜默覆蓋。
- 可按story ID保留、排除、改標題/摘要、重排；restore建立新revision，
  無變更仍記receipt；owner明確選base後可匯出指定版本的可讀JSON。
  原稿、來源欄位及其他base校稿不會被修改。
- 有效但衝突的request留安全結果，格式不合法在建立request身份前拒絕；
  匿名/錯owner拒絕。owner身份仍為**模擬注入**，不是手機登入或OAuth驗證。
- F26～F33及C05適用的F34～F36合成測試通過；最終完整離線套件
  **923 passed in 3.35s**，程式編譯通過。首次一項測試預期錯誤已修正，
  命令/差異/文件檢查記於C05 checkpoint。
- [C05完整交接與C06精確入口](DIGEST_CLOUD_CONTRACT.md)。停於C06前；
  建議 **GPT-6.1 Sol／Medium**。未連網、部署、啟用排程、修改私人稿或commit/push。
- C05交接證據：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C05-handoff/`。


## 2026-10-09 C04 本機保存與原子控制模擬完成

- 新增 [C04本機假服務](../scripts/digest_cloud_mock.py) 與
  [故障/併發測試](../tests/test_digest_cloud_mock.py)。上傳不可變原稿、讀回核對後，
  以每期copy-on-write控制紀錄原子提交交付、request去重、嘗試終態與revision 0。
- 真實時效只在模擬交易提交時取clock；09:00準時、90分鐘來源時效分開。
  上傳半途失敗、manifest失敗、資料損壞或補跑失敗都不清除先前成功稿。
- C04 F11～F25 適用案例及C03回歸已通過。此服務只在單程序記憶體運作，
  真provider的持久性、CAS及手機登入仍待C01/C09/C10驗證。
- 首次完整測試因PATH缺Node.js導致39個前端用例無法啟動、862通過；使用桌面
  附帶Node後最終完整 **903 passed in 3.06s**；此前相關 **101 passed in 0.74s**。
  編譯及文件/差異檢查結果、版本與快照在C04 checkpoint。
- [完整契約、C04範圍及C05精確入口](DIGEST_CLOUD_CONTRACT.md)。停於C05前；
  建議 **GPT-6.1 Sol／High**，若revision交易一致性有難題再用Astra／High。
- 未連網、部署、啟用排程、取得憑證、修改私人稿或commit/push。
- C04交接證據：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C04-handoff/`。


## 2026-10-09 C03 離線生成入口完成

- 新增 [C03離線準備入口](../scripts/digest_cloud_prepare.py) 與
  [合成測試](../tests/test_digest_cloud_prepare.py)，重用既有composer、原稿配對驗證與獨立重跑；
  只回傳可交給C04的不可變bytes和來源證據，不標ready或已交付。
- 檢查固定期別、可信模擬issuer、slot及手動歷史期別、三檔同commit/hash、
  跨日拒絕及Downloads暫存邊界。歷史稿只標mode；真雲端來源/手機授權未驗證。
- C03子集與原有生成/交付/驗證離線測試通過；首次失敗及修正保存在C03檢查點。
  [C02契約末尾](DIGEST_CLOUD_CONTRACT.md)載明C04精確入口與未完成案例。
- 停於C04前。建議 **GPT-6.1 Sol／High**；遇交易一致性疑難再用Astra／High。
  本輪未連網、部署、啟用排程、取得憑證、修改私人稿或commit/push。
- C03交接證據：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C03-handoff/`。


## 2026-10-09 C02 六項契約審查完成

- 使用者標註續行指令，完成 C02 設計審查；[正式契約與36項驗收案例](DIGEST_CLOUD_CONTRACT.md)。
- 固定可信期別意圖、原稿 identity、題號與 story_id 分離、原子交付、revision 交易去重、
  提交當下時效與準時性分開。review-only 不冒充正常交付，舊成功與人工稿保持可追溯。
- 重要修正：靜態 cron 直接 dispatch 無法證明期別；物件最後寫 manifest 不足以保證交易。
  正式供應商須另驗可信意圖發行及原子控制層，可能需要配套服務；C01/C08/C09 待驗。
- 本輪只改文件，36項是待實作驗收規格，沒有宣稱新測試通過；C00 的62項為歷史基線。
- 停於下一 High 關卡 C03；建議 **Astra / High**。精確入口在契約末尾。
  未連網、部署、啟用排程、改私人稿、改正式程式或 commit/push。
- C02 交接證據：`/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C02-review/`。


## 2026-10-09 私人雲端日報架構 A 模擬核准與 Astra 停點

- 使用者核准架構 A 本機模擬，授權自動續行至下一高難度任務時停止，
  由使用者開啟 Astra 審查；未授權正式部署、外部排程啟用、通知或雲端清理。
- 本輪 C00 範圍登記/環境核對完成；既有生成、私人交付、GitHub 驗證
  三組離線測試 **62 passed in 0.63s**。scripts/tests/workflows 雜湊前後相同。
- 依既定分級，離線路徑首個 High 為 C02 資料契約，已在開始前停止。
  尚未建立新雲端入口/storage adapter/revision API/網頁/MCP，不宣稱模擬實作完成。
- [核准範圍與提案](DIGEST_CLOUD_DELIVERY_PROPOSAL.md)、
  [C02 Astra 六項審查決策與續行提示](DIGEST_CLOUD_ASTRA_REVIEW.md)。
- 檢查點 `/Users/lordmi/Downloads/ai-news-radar-cloud-20261009/C00-20261009-095013/`，
  含起點、命令、測試、結果、最終交接與差異；下一階段 **Astra / High**。
- C01 帳號/手機雲端語音讀寫仍待復線實測。平台、費用、通知渠道與清理政策未定。
  原 O01 尚未達上午準時驗收，新外部觸發驗收須明確改版，不能改寫舊失敗。
- 本輪沒有連網、改正式程式/排程、觸發刷新、取得憑證、修改私人稿、commit/push。

## 2026-10-03 O01 後續驗證移至GitHub

- 使用者明確要求「o01之後步驟改為在GitHub上面繼續驗證」，後續路徑改為
  Daily digest validation；先前本機automation建議被本項覆蓋，私人交付仍在本機。
- 新workflow每天臺北07:15／08:15（UTC23:15／00:15）兩次獨立觀察，先跑離線故障測試，
  再唯讀固定遠端commit、生成／配對核對、相同bytes重跑。只有安全摘要，不上傳MD/meta／輸入。
- scripts/validate_digest.py使用runner讀取token，不傳provider憑證；暫存用完清除。
  schedule以run created_at固定臺北期別，跨日標missed_issue；舊資料review-only不當正常空日。
- 相關52 passed、完整863 passed，workflow actionlint／YAML、語法與diff格式通過；
  run created_at API使用相同raw media header也已唯讀驗證。
- O01為github_observing，三個完整臺北日的event=schedule／時效／09:00前完成與
  artifact零值待實際驗收；手動成功不算三日驗收，未啟用本機automation。
- 首次[真實GitHub手動驗證](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/37079245894)
  已成功，程式commit 9d42a0419a5a7f021e475290c1d74eaf23f1c9ca；完整Offline tests同樣成功。
- [GitHub操作與驗收](DIGEST_GITHUB_VALIDATION.md)。發布／真實手動run／測試證據落於
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261003/O01-GITHUB-20261003-073958/`。
  run ID／commit／結果以該目錄RELEASE.md為準；下一階段GPT-6.1 Sol／Medium。


## 2026-10-03 全專案複查與提交前修正

- 使用者授權全專案複查並朝commit/push完成，只有範圍擴充才需裁決；本輪無此類擴充。
- 審閱所有待提交日報模組／測試與共享archive入口、公開產品／來源治理、Actions／前端契約。
- B01修正：OPML採既有group feed驗證，非feed HTML／malformed／全缺欄位標失敗，
  合法空feed與成功peer保留；不增加新來源或調整AI評分。
- B02修正：新creator_metrics缺失／非法值為null，明確0仍0；UI／scoring無數值消費者，
  不改既有archive的0、不遷移資料。B03修正：搜尋10頁硬上限／100 raw觀測停止下一請求，
  整頁可超過閾值，保留早先成功頁；保留數估算不再冒稱帳單上限。
- 修正交付失敗仍留ready staging manifest的狀態矛盾；來源治理、ROADMAP與台帳已同步。
- 最終完整850 passed；24份Python模組、4份JavaScript語法與4份workflow YAML結構通過。
  暫存生成健康檔已檢查；憑證樣式掃描唯一命中既有FakeSession測試字串，私人feed／日報不入版控。
- 遠端只新增data/item自動快照；整合時保留遠端資料，不以本機舊快照覆蓋。
- 原始與最終驗證／差異／提交推送結果保存至
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261003/PREPUSH-20261003-072022/`。
- 日報私人產物不入Git；本機排程尚未啟用，O01下一步仍為本機排程／3日觀察，
  建議GPT-6.1 Sol／Medium。提交SHA／推送結果以該目錄RELEASE.md為準。


## 2026-10-03 O01 本機私人交付實作與手動驗收

- 使用者選擇「本機私人交付」，新增 `scripts/deliver_digest.py` 及21項測試；
  不需發布程式或CI artifact。O01為local_manual_ready，尚未建立排程／3日觀察。
- 手動交付2026-10-03成功：19題，窗口固定10/2 06:00～10/3 06:00；固定遠端
  `27156f411f326aa2cfdeea491e05771486420400`，archive as-of臺北10/3 07:04:40，
  MD/meta配對與來源三檔SHA已核對；ready表示時效達標，不保證選題或事實查證完成。
  生成版本／校稿副本在
  `/Users/lordmi/Downloads/ai-news-radar-digests/2026-10-03/4c34f92f7488560da54090a1d497c191e101bde78116e218e99de8b67975dfc3/`。
- 私人attempt保存原始輸入／manifest，目錄700、檔案600；同一期flock、先驗 staging
  再rename新版本，既有配對／人工稿不覆蓋。archive未知／早於截止／過舊／未來
  exit3 review-only，失敗exit1，ready含真空日exit0，不改既有generator契約。
- 初次urllib下載卡住已終止；curl硬逾時版第一次raw主機下載仍失敗，沒有正常交付。
  改官方contents API raw media、固定ref，真實交付成功；不是忽略錯誤或放寬資料門檻。
  下載10秒連線／45秒傳輸／50秒外層逾時、64MiB上限；無credentials或新抓取。
- 最終相關67 passed，完整830 passed，語法與格式通過。交接、失敗／成功logs、
  起點、增量patch與固定副本重跑證據在
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261003/O01-LOCAL-20261003-065944/`。
- [操作說明](DIGEST_USAGE.md) 已補入口／狀態／復原。真實草稿第1題職涯技能、第3題模型
  使用指南、第6題月度回顧須人工判斷；同publisher/URL refs不當獨立查證，不改選題算法。
  沒有pull、正式data變更、來源刷新、provider／LLM、workflow／automation、commit/push或部署。
- 下一階段O01本機排程／3日交付觀察，建議 **GPT-6.1 Sol／Medium**：手動入口已驗證，
  重點為07:15／08:15時刻、執行權限與Mac睡眠／離線限制。依提案在手動審閱後再啟用，
  不把本輪選擇渠道宣稱成已啟用。B01～B03與新聞品質缺口仍另案。

## 2026-10-03 O01 資料時效與上午交付提案

- **O01提案完成，實作／正式啟用待核准**；臺帳proposal_ready，沒有將整項O01標done。
- `run o01` 唯讀診斷：本機HEAD/cached origin停541e493、data臺北10/1 23:11；
  真遠端master已c32d582705a7ea54ca241cfe50afb914753cbdb8，固定commit archive/health
  同為臺北10/3 06:05:32，最新刷新run成功。本次過舊空日是本機落後，不是遠端停抓。
  該遠端commit沒有generate_digest.py，本機日報程式未提交／發布，CI方案需額外核准。
- [O01完整提案](DIGEST_OPERATIONS_PROPOSAL.md)：07:15主生成、08:15備援、09:00人工檢查、
  11:30人工發布；固定同commit輸入，MD/meta核對，時效交付guard不改06～06新聞窗口。
  建議唯讀CI artifact7天，公開repo草稿可見性需接受；備選本機私人交付。
- 初次沙盒gh網路失敗後，升權僅做GitHub GET；8筆run與固定commit資料時間、
  CLI404保存在remote-facts/read-commands。成功run可能僅freshness-check，不能替代as-of。
  官方schedule/artifact限制已核對，提案有原始連結；不承諾準時／私人artifact／已開通知。
- 證據、文件快照與提案交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261003/O01-20261003-062352/`。
  只改四份文件；未pull/刷新來源/dispatch/workflow/automation/commit/push/deploy。
- 下一階段仍為O01實作／啟用驗收，**GPT-6.1 Sol／High**：需跨commit下載／固定身份、
  交付guard、artifact邊界、互斥與故障驗收。先待使用者核准CI或本機渠道、時間與發布前提，
  然後新checkpoint；不可把run o01提案當作啟用排程授權。B01～B03與選題品質缺口仍未修。

## 2026-10-03 D11 本機日報與人工校稿交付

- **D11 已完成交付**：三組 MD/meta 核對與 byte-identical 重跑通過，交接已落檔。D01～D11 離線主線完成；人工校稿尚待使用者。
- 使用者 `run d11`；客戶日期10/3，沿 D10 先交10/2真實草稿，另交10/3當期空日與
  明確分開的合成空日。固定三輸入副本、生成 MD/meta、manifest／命令／logs、校稿說明：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261003/D11-20261003-061422/`。
- archive/health as-of 臺北 **10/1 23:11:39**，早於兩期截止；10/2有8題（89候選），
  10/3無窗內題目，均提示 input_before_cutoff。這是現有過舊快照的結果，不代表當日無新聞。
  新增 [DIGEST_USAGE](DIGEST_USAGE.md)，說明生成、核對、重跑與校稿副本。
- 10/2第6題是提示詞教學，建議校稿移除；第4～8題的多筆refs各自同publisher/URL，
  不當獨立查證。摘要可能只是標題或缺失；cache譯文 unversioned。已列 REVIEW_NOTES，
  本輪不改 score／gate／去重，保留生成配對與独立校稿副本；不是全部8題刊出合格的保證。
- 初次固定副本步驟使用系統Python3.9 import失敗，起點已保存且未讀三輸入；改專案
  .venv恢复。程序碼不變，沿用 D10 809 passed，不冒稱本輪全套再驗。
  正式data/feeds/workflow未改，未抓取/provider/commit/push/deploy。
- **建議下一項 O01：資料時效、上午生成與人工交付提案**，先核對現有更新來源與本機
  快照流程，再提出時間／儲存／失敗與通知安排，實際啟用須另核准；仍 conditional。
  **GPT-6.1 Sol／Medium**：需對齊資料更新與人工校稿流程，尚無部署改動。
  本輪沒有建立 automation 或启用新排程；不自動推進 LLM/其他optional來源。B01～B03未修。

## 2026-10-02 D10 整合與公開相容性驗收

- **D10 已完成**：日報聚焦 281 passed，完整 Python 809 passed，交接已落檔。
- 使用者 `run d10`。新增真實 CLI／composer／pair 核對的離線整合測試；
  [D10 實作／驗收](DIGEST_PLAN.md#d10-已實作與整合驗收2026-10-02) 記範圍與限制。
- F01～F19 對照保存於 ACCEPTANCE_MATRIX.md；晚發現新聞同日改稿、窗口證據、空日／
  非 AI、健康失效／不同輪、單次預設日期、record reorder、fake/no key 封鎖外部函式、
  程序兩檔之間 exit 73 與 stream.write 故障均有端到端證據。缺失／不一致配對拒絕交付，
  重跑恢復；失敗不報成功、不暴露原錯誤。
- 初次新測例 **2 failed** 證實顯示缺口；已修臺北日期／本地窗口、出版者摘要／既有快取
  譯文標示與段落。renderer 核對固定期別窗口、拒絕非法日或無支持的摘要 kind。
  render_version=markdown-v3；schema/pipeline 不改。D08 舊 fixture 窗口錯一日已校正，
  原歷史驗收保留。本輪最終聚焦 **281 passed**、完整 **809 passed**。
- 原生成器／所有日報模組語法、差異格式通過；full suite 使用 bundled Node PATH。
  起點、每次命令／環境／失敗及成功 logs、矩陣、六檔增量 patch／文件快照／交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D10-20261002-233733/`。
  原二十三份差異保留；十八份本輪未碰的既有差異保持起點 bytes。
- 正式 JSON／來源／workflow／公開生成器未改，未 commit、push、部署或呼叫 provider。
  不把離線全套成功宣稱 live API 可用、歷史整日 coverage、斷電／多 writer 交易或人工校稿完成。
- **下一階段 D11：本機真實日報與人工交付**。先新 checkpoint，僅核對 archive/cache/health
  時效與指定期別（未另指定可先評估 2026-10-02），保存可重现的輸入副本到 Downloads，
  用 D09 CLI 生成 MD/meta，核對 identity/hash，保留成功配對；人工校稿另存發布副本。
  同時交空日合成樣本、實際命令／重跑說明／未啟用功能與資料限制。若輸入過舊或當期為空，
  如實呈現，不能借其他期新聞填當期或把合成資料當真實日報，不自行抓新資料。
  **建議 GPT-6.1 Sol／Medium**：流程已验證，重點是期別／時效、新聞證據與可操作交付。
  B01～B03 未修；D11 不自動推進 LLM、排程、部署或 optional 來源。

## 2026-10-02 D09 離線 CLI 與双檔核對

- **D09 已完成**：聚焦 209 passed，語法／格式通過，交接已落檔。
- 使用者 `run d09`。新增 digest_document composer、generate_digest CLI 與測試；
  [D09 實際接口](DIGEST_PLAN.md#d09-已實作接口與驗收2026-10-02) 記參數、identity 與恢復界線。
- CLI `--input-dir` 必填，date 預設臺北當天，output 預設 Downloads/ai-news-radar-digests；
  日期／參數錯誤 exit 2，生成失敗 exit 1，成功含空日 exit 0。明確 output 可指定新目錄，
  不能寫 input 樹或專案 data/item。全程離線，固定輸入／日期／設定重跑完全一致。
- Markdown comment 與 meta sidecar 共享 identity；meta 記 Markdown SHA-256，核對重算
  metadata identity。先完整建構再用既有 atomic writer 寫兩檔，各自原子；第二檔失敗可能
  留下不一致配對，回報失敗／核對拒絕，重跑恢復。輸入／render 失敗保留舊成功配對。
- 同期快照或設定／版本改變會改 identity；不借 Git HEAD／路徑／mtime／clock。衍生內容
  亦納入身份；未提供多 writer 鎖。校稿編輯會使 SHA 不符，發布副本與生成配對分開保存。
- 修正已證實 D08 bug：URL 括號 percent-encode、文字換行 collapse、HTML escaping、URL host
  檢查，新增回歸；原 D08 交接反映當時結果，本次版本 render=markdown-v2。
- 聚焦 **209 passed**；composer/CLI/renderer/原生成器 py_compile、diff check 通過。
  未跑完整 suite，D10 待整合複核；正式 data／來源／workflow 未改，原二十份差異保留，
  未 commit／push／部署。起點、命令／環境／logs、增量 patch 與交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D09-20261002-232821/`。
- **下一階段 D10：整合驗收**，先新 checkpoint，核對 D01 fixture matrix 與實際 D09
  API；跨窗口證據、晚發現重跑、optional health、全失效仍有 archive、空日／非 AI、
  終端 CLI、寫入中斷、同輪身份與 Markdown 證據連結逐項查缺。按改動範圍驗共享相容性，
  必要時使用 bundled Node PATH 跑完整 suite，保留首次失敗 log。
  **建議 GPT-6.1 Sol／High**：多階段證據／identity／原子寫入與相容性需獨立審查。
  D11 人工交付仍待執行，B01～B03 未修；不啟用排程或 provider。

## 2026-10-02 D08 繁中 Markdown renderer

- **D08 已完成**：聚焦 115 passed，語法／格式通過，交接已落檔。
- 使用者 `run D08`。新增 `scripts/digest_render.py` 與 renderer 測試；
  [DIGEST_PLAN 的 D08 接口](DIGEST_PLAN.md#d08-已實作接口與驗收2026-10-02) 記實際欄位與限制。
- `render_digest(document) -> str` 是純格式化接口：窗口、候選、health notices、diagnostics
  由呼叫端提供；不抓取、不翻譯、不排序、不呼叫模型。空候選合法，候選缺標題安全失敗。
- 標題／摘要／來源文字做 Markdown escaping；連結只接受 http(s)，保留合法證據 URL，拒絕
  javascript 等 scheme。缺摘要、缺來源與未知日期如實標示。health 只映射固定 notice code，
  不輸出原始錯誤、ID、path 或未知 code。輸入不變、輸出 deterministic。
- 聚焦 **115 passed**（D08＋D07＋D06＋D05）；`py_compile`、`git diff --check` 通過。
  新增隔離 renderer，未重跑完整 suite；正式資料／來源／workflow 未改，未 commit、push、
  部署或呼叫 provider。原十六份差異保留。
- 起點、命令／結果、增量 patch、文件快照及交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D08-20261002-225500/`。
- **下一階段 D09：CLI 與原子寫入**。先建立新 checkpoint，讀 D01 contract 及 D08 實際
  renderer，再定義 `generate_digest.py` 的 date／input／output 參數、input identity、
  重跑與 fatal 行為。產生 Markdown 與 meta sidecar，先建構／驗證再原子替換；兩檔不保證
  交易，人工交付前核對 identity。測 exit 0/1/2、空日、缺 archive、health mismatch、
  已存在成功檔與寫入失敗。**建議 GPT-6.1 Sol／Medium**：跨輸入、renderer、identity、
  原子檔案與錯誤碼的整合需要較強介面審查；不自動切模型。B01～B03 未修，D09 不啟用
  排程、provider 或公開部署。

## 2026-10-02 D07 來源健康與資料時效摘要

- **D07 已完成**：聚焦 77 passed，語法／格式通過，交接已落檔。
- 使用者 `run d07`。新增 `scripts/digest_health.py` 與測試；
  [DIGEST_PLAN 的 D07 接口](DIGEST_PLAN.md#d07-已實作接口與驗收2026-10-02) 記實際欄位與文案界線。
- summarize_digest_health(snapshot, window) 產生 DigestHealth 與可選 RoundHealth。
  取 D03 descriptor as-of 解析／比較；matched 且 loaded 才附同輪統計；不同輪／未知
  保留時間但不借健康數字。input_before_cutoff 是提示，不更改 06:00～06:00 窗口。
- site_counts 與 child_counts 分開，provider availability 另列固定四鍵；不重複加總。
  成功、健康零則、失敗、部分失敗、skip、disabled、未知互斥；skip/disabled/未嘗試的父列
  不把舊子列算成功。不重播 history，不輸出輸入的 ID、名稱、錯誤或 reason/path。
- notices 是受控代碼；始終明示健康不是歷史日 coverage、留存新聞不是本輪新採集。
  不推算 fetched_raw_items 或獨立文章總數；D03 未保留該頂層指標。
- **77 passed**（D07＋D03 input＋既有 source_health）；語法及格式通過。
  新隔離接口未改共享程式，未重跑 full suite。正式資料／來源／workflow 未改；
  原十六份未提交差異保留，未 commit、push、部署或呼叫 provider。
- 起點、每次命令／環境／結果、增量 patch、文件快照及交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D07-20261002-224029/`。
- **下一階段 D08：繁中 Markdown renderer**。先建立新 checkpoint，讀 D01 contract、
  D05 candidates、D06 selection、D07 health 的實際接口，再決定最小 document 組合入口。
  以 render_digest(document)->str 輸出窗口、入選新聞、publisher 摘要與原文證據；
  受控 health 文案，缺摘要／缺譯文如實保留，空日合法，測 Markdown escaping/連結。
  **建議 GPT-6 Luna／Medium**：接口與內容來源已確定，工作集中在格式與邊界測例。
  若 renderer 組合接口出現跨模組矛盾再評估 Sol／Medium；不自動切模型。
  B01～B03 未修；CLI／整合／人工交付待 D09～D11，D08 不启用排程或 provider。

## 2026-10-02 D06 選題與來源證據

- **D06 已完成**：聚焦 107 passed，語法／格式通過，交接已落檔。
- 使用者 `runmd06` 依前文續接 D06。新增 `scripts/digest_selection.py` 與選題測試；
  介面與限制見 [DIGEST_PLAN 的 D06 接口](DIGEST_PLAN.md#d06-已實作接口與驗收2026-10-02)。
- 對原 story 重用 brief gate／來源降權／同事件抑制；預設 limit 20、penalty 0.03、
  gate 0.72 或多來源。快取譯文不影響排序；同分同標題依 ID 固定順序。
  唯一且集合一致的 story/candidate ID 對回完整證據，deep-copy，不補分、不強湊題數。
- 回傳 DigestSelection 的 candidates/counts/settings/階段 diagnostics；D08 可取 candidates，
  D09 需將 settings 納入 identity。沒有摘要如實保留；缺漏／重複 ID 不偷偷替補。
- 聚焦 **107 passed**，含既有 brief／quality 與 D04/D05；語法／格式通過。
  隔離新模組，未重跑完整 suite；不把 D04 的 642 當本階段完整驗收。
  正式資料、來源、workflow 未改；原十四份未提交差異保留，未 commit、push 或部署。
- 起點、精確命令／環境／結果、增量 patch、文件快照與交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D06-20261002-213319/`。
- **下一階段 D07：來源健康／資料時效摘要**。先保存新 checkpoint，讀 D01 health contract、
  D03 allowlist 與既有 source_health 狀態規則；區分 leaf/group、成功零則、失敗、partial、
  skip/disabled。只有 as-of matched 可描述同輪計數，不宣稱歷史整日 coverage。
  archive 有窗內新聞不等於本輪全新採集；input_before_cutoff 提示不改窗口／不加等待。
  對未知／缺欄位保持未知，用受控文案，避免輸出原始錯誤／私密字串。
  **建議 GPT-6.1 Sol／Medium**：既有快照接口已齊，重點是健康分類、時間對齊與薄 metadata。
  若實際狀態契約互相矛盾再評估 High；B01～B03 未修，renderer／CLI 尚未實作。

## 2026-10-02 D05 候選 adapter

- **D05 已完成**：最終聚焦 63 passed，語法／格式通過，交接已落檔。

- 使用者要求 `run d05`。新增 `scripts/digest_candidates.py` 與 31 項候選測試；
  介面與欄位來源見 [DIGEST_PLAN 的 D05 接口](DIGEST_PLAN.md#d05-已實作接口與驗收2026-10-02)。
- adapt_story/adapt_stories 保留排序／ID；schema v1，缺 optional 欄位 nullable，
  verification null。主來源依 primary ID 唯一回查，日期不取 latest_at、摘要不借其他來源。
  每題與每個來源保留 publisher 原文、URL、日期、精確 cache 譯文及 unversioned provenance。
- summary_kind 區分 publisher/publisher_translation/none；不搬 AI summary、未對證據的
  summary_zh 或不明 raw payload。缺主來源保留 metadata origin，不假裝查證；source_count
  僅 refs 長度。legacy ID 原樣保留，無 provider／翻譯／選題／重排。
- 最終聚焦 **63 passed**（D05 31＋D04 32）；語法／格式通過。無共享程式修改，
  未重跑 full suite，不把 D04 的 642 當 D05 全套驗收。正式資料、來源、workflow 未改。
- 起點、精確命令與結果、任務增量 patch／交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D05-20261002-211348/`。原十二份差異保留；未 commit、push 或部署。
- **下一階段 D06：日報選題與來源證據整理**。先建新 checkpoint，讀 D06 卡與現有
  select_diverse_stories／story_passes_brief_gate 及 D04/D05 接口；對原 story 做既有選擇，
  再按 story ID 對回 candidate，保留證據與摘要來源，不補分／強湊題數／添加新來源配額。
  **建議 GPT-6.1 Sol／Medium**：來源與候選已齊，重點是選題參數、對應與確定性測例。
  D07 亦可開始；預設先 D06，B01～B03 未修；renderer／CLI 尚未實作。

## 2026-10-02 D04 窗口篩選與故事重用

- **D04 已完成**：聚焦 50 passed／完整 642 passed，交接已落檔。

- 使用者要求 `run d04`。新增 `scripts/digest_pipeline.py` 與 32 項日報 pipeline 測試；
  實際 stage API 與限制見 [DIGEST_PLAN 的 D04 接口](DIGEST_PLAN.md#d04-已實作接口與驗收2026-10-02)。
- `build_digest_stories(snapshot, window)` 先排 alias／嚴格發布窗口／無 title 或 link，
  再 deep-copy、重用現有繁中顯示、相關性、分級、去重、來源上限與 merge。
  merge 固定 end_utc/24h，同時刻以 item ID 固定順序；現有公開 ID 算法與 scoring 不改。
- 回傳 DigestStories 的 stories/items/diagnostics；items 是去重後實際 merge 證據，
  diagnostics 僅此 stage，另有 D03 input diagnostics。尚無候選adapter、選題、renderer 或 CLI。
  不翻譯／呼叫 provider；缺出版者「未標示來源」，不猜 host；窗口外證據不混入。
- 最終聚焦 **50 passed**、完整 suite **642 passed**，語法與差異檢查通過。
  首次兩個 fixture假設不符現有 source relevance/title門檻，已修fixture，失敗 log保留；
  未改既有生成器或其他 H00～D03 程式。無正式資料、來源、workflow、commit、push、部署。
- 起始 checkpoint、最小查碼、每次命令／環境／結果、本任務增量 patch 與交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D04-20261002-194958/`。原十份未提交差異保留。
- **下一階段 D05：story → EditorialCandidate 薄 adapter**。先保存新起點，再讀 D01
  candidate contract、D04 stage API；逐 sources／primary ID 回查日期與 publisher evidence，
  接 exact title/summary cache，schema version/nullable verification 明確，不借用 AI cache。
  **建議 GPT-6.1 Sol／Medium**：stage 輸出與欄位來源已明確，重點是 nullable mapping、
  cache 命中與單／多源測例。保留 story ID 限制，勿把 sources 數量說成獨立查證次數。
  D06 尚需 D05；D07 也可做，預設先 D05；B01～B03 仍未修。

## 2026-10-02 D03 唯讀輸入快照

- **D03 已完成**：最終完整測試 610 passed，交接已落檔。

- 使用者要求 `run d03`。新增 `scripts/digest_input.py` 與輸入測試；既有
  archive loader 的結構驗證抽成 `archive_from_payload()`，原 path API 行為保留。
  介面與限制見 [DIGEST_PLAN 的 D03 接口](DIGEST_PLAN.md#d03-已實作接口與驗收2026-10-02)。
- 三檔各讀一次；raw bytes immutable、每檔 SHA-256、目錄無關 fingerprint；
  缺 archive fatal、cache/health 降級、strict as-of/UTC 對齊。不抓取／翻譯／呼叫模型，
  不寫輸入、不套用 AI 摘要快取、不修改公開 ID 或 scoring。
- 原始 bytes 不可直接匯出；health 已限縮到狀態、subsources、disabled/skip metadata，
  不帶原始 error、credential presence、URL/path 欄位。health 不同輪／未知仍保留證據，
  D07 不能將其計數說成同輪或整日 coverage；input_before_cutoff 亦留 D07 判斷。
- 最終完整 Python suite **610 passed**；語法與差異檢查通過。
  首次完整 suite 39 項缺 node 失敗，bundled Node PATH 修正後通過，原失敗 log 保留。
  沒有正式資料、來源、workflow、commit、push 或部署。
- 起始 checkpoint、確切命令／環境 override、逐命令 logs 與 task-only patch：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D03-20261002-193322/`。H00～D02 原差異保留。
- **下一階段 D04：先按發布窗口篩原始新聞，再重用 story 生成**。
  先建立新檢查點，讀 D01/D02/D03 實際接口與必要預處理／merge symbols；
  用 window.end_utc 固定排序時間，無 first_seen fallback、無窗外證據、固定 ID tie-break。
  **建議 GPT-6.1 Sol／High**：涉及時間篩選、去重／ID 與現有排序重用的相容性；
  不重寫 scoring 或來源系統。D07 也可開始，預設先依序做 D04；B01～B03 仍未修。

## 2026-10-02 D02 日期窗口與發布時間解析

- **D02 已完成**：49 項聚焦測試與語法／格式檢查通過，交接已落檔。

- 使用者要求 `run d02`。新增獨立 `scripts/digest_window.py` 與
  `tests/test_digest_window.py`；時間契約、實際 signature 與 wire 格式見
  [DIGEST_PLAN 的 D02 接口](DIGEST_PLAN.md#d02-已實作接口與驗收2026-10-02)。
- 窗口仍為臺北 `[前一天 06:00, 當天 06:00)`。`window_for_date()` 回傳 frozen
  DigestWindow 與 UTC aware 邊界；預設日期只捕捉一次 clock，06:00 前不換期。
  `parse_published_at()` 拒絕缺值／date-only／naive／非法格式，輸出安全診斷 code；
  不接 first_seen，不更改既有 `parse_iso()`／`event_time()`。
- 聚焦 49 項測試通過；新模組與既有生成器語法檢查、差異格式檢查通過。
  已驗證無生成器／requests／bs4／dateutil 依賴；不是新日報整合驗收。
  原四份未提交文件保留；無正式資料、feed、workflow、commit、push 或部署。
- 起點檢查點、命令與環境 override、逐命令 log、task-only patch 與交接保存在
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D02-20261002-192502/`。
- **下一階段 D03：唯讀 archive／cache／health 輸入快照**。先建立 D03 起始檢查點，
  讀 D01 三檔 contract 與 archive I/O 權威，重用 validated loader 與 D02 strict parser；
  不抓取／翻譯／呼叫模型。D04 尚需 D03 完成，B01～B03 仍未修。
  **建議 GPT-6.1 Sol／Medium**：現有 loader 可重用，主要處理缺檔、optional cache
  降級、as-of 對齊與 captured bytes；若共用 decode 邊界需要改公開 loader 語意，
  先找兼容做法，實際產生相容性矛盾再升 High。

## 2026-10-02 D01 輸入契約與 fixture 清單

- **D01 已完成**：契約／fixture 清單與文件驗收通過，交接已落檔；新日報行為尚未實作。

- 使用者要求 `run d01`。契約與 19 組 fixture 情境已記於
  [DIGEST_PLAN.md 的 D01 已定契約](DIGEST_PLAN.md#d01-已定契約2026-10-02)。
  本輪只補文件，尚未新增 generator、fixture 或測試，也未修 B01～B03。
- 必要輸入 `archive.json`；可選 `title-zh-cache.json`、`source-status.json`。
  缺 archive 是 fatal，合法空 items 才是空日；legacy keyed archive 沿用既有 loader。
  日期仍為 `[前一天 06:00, 當天 06:00)`，只用帶時區 published_at，不用 first_seen。
- archive／health 各自保存 producer as-of；相異或未知時不聲稱同輪健康。
  翻譯快取沒有生成時間，標 unversioned。只指紋三個指定輸入，無 repo 掃描。
  多檔讀取與多檔輸出都不是交易；同一輸入／日期／設定／版本才保證確定性。
- 第一期 publisher 摘要／既有譯文，無摘要保留標題與證據；不套用依賴
  title/context/model/prompt 的 AI 快取，也不觸發現有 translator 或摘要 provider。
- 輸入／候選／文件 schema、CLI 與 exit codes、缺檔／壞檔／早於截止提示、
  19 組測例責任及候選檔案位置已定；全部是後續待實作契約，並非現成 CLI。
- 起始檢查點、唯讀查碼、D01 文件增量與驗收證據保存在
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D01-20261002-191535/`。
  延續 H00 四份未提交文件，不覆蓋原差異；HEAD 仍為
  `541e493957e01168434dd8eb22de414f11045096`。無產品程式／正式資料變更、commit、push 或部署。
- **下一階段 D02：06:00 日期窗口純函式與邊界測試**。先建立新檢查點，
  讀 D01 時間 contract，新增 `scripts/digest_window.py` 與聚焦測試。
  **建議 GPT-6.1 Sol／Medium**：接口已明確，主要是時區、半開邊界及嚴格解析；
  不需讀整個生成器或提高至 High。D03 依賴亦已滿足，但預設先依序做 D02。

## 2026-10-02 日報設計確認與小任務交接機制

- 使用者同意日報採台北時間 `[前一天 06:00, 當天 06:00)`；無 8h 擴散等待、
  跨窗口補充證據或其他新時間規則。06:00 截止後生成，上午人工校稿、
  約 11:30 人工發布為工作目標，尚無日報生成排程或自動發布。
- 已建立 [DIGEST_PLAN.md](DIGEST_PLAN.md)：28 項小任務，H00 完成；
  D01～D11 主線為無新 LLM 的本機日報；LLM、排程、bug、社群與模型／來源
  後續各有獨立卡片與條件。本輪僅文件，不修改程式、正式快照、feed 或 workflow。
- 日期與輸入契約要先處理：現有 stories／brief 是滾動 24h，需先從指定 archive
  snapshot 篩選發布時間再重用生成。固定 snapshot 才能確定性重跑；story ID
  不宣稱跨輪永久固定。缺日期不臆造，當下健康也不等同歷史日 coverage。
- 已在本聊天完成無網路 main() fixture：RSS 全失效仍可用非 RSS 5 筆形成
  4 stories；全失效空 archive 合法為空，近期 archive 仍可供新聞。
  10 個相關既有測試檔 112 passed；不是完整 suite 或新日報驗收。
  先前暫存已清除，這些數值來自工具結果；不得假稱已有原始 log 檔。
- 三項既有缺口已離線重現，尚未修：OPML 非 feed HTML → healthy zero、
  TikHub metrics 缺值 → 0、SocialData search 缺明確分頁上限。詳見 B01～B03。
  social snapshot 不包含 velocity；既有新聞／健康／付費間隔 state 不能因此刪除。
- [TASK_HANDOFF_TEMPLATE.md](TASK_HANDOFF_TEMPLATE.md) 要求任務起點先落檔、
  小步後更新、長命令前記 pending action；證據與檢查點放 Downloads。
  硬中斷後先查實際 diff／結果，不 reset 或盲目重跑有費用的呼叫。
- 本輪文件驗收與初始檢查點：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/H00/`。
  Repo 基線 `master`／`541e493957e01168434dd8eb22de414f11045096`，起始乾淨；
  文件保留本機差異，未 commit、push 或部署。
- 已完成 H00。**下一階段 D01：日報輸入契約與 fixture 清單**；首個動作為
  讀 DIGEST_PLAN 的 D01 卡與必要的 archive／時間／story symbols，落 D01
  起始 CHECKPOINT，補定最低工程語意與實際檔案／測試方案，不重做全 repo 盤點。
  **建議 GPT-6.1 Sol／Medium**：有明確產品窗口，主要處理跨輸入與缺值語意；
  若發現 producer 相容性矛盾再提高至 High。建議不會自動更換模型。

## 2026-10-01 本地健康檢查後續完成

- 生成器新增 monotonic phase wall 耗時及群組 child 當輪耗時；OPML feed
  加總與 phase wall 分開，跳過 child 為 0 且不重置故障歷史。
- 狀態檔在其他輸出成功後、resolver 清理前發布；輸出耗時不包含其自身
  發布與清理，單檔 replace 仍不是跨檔交易。規則見 OPERATIONS。
- 欄目純選擇函式抽至 `assets/selection.js`，分類／搜尋／模式／DOM
  行為不變；五項資產共用 `selection-module-1001a`，module defer 在 app 前。
- 8/22 免費額度假異動的格式缺口已補：字串 models、非字串模型、重複
  provider ID 與已知退休說明文字會拒絕整輪；既有 80% 縮水保護延伸至
  每個 retained provider 的模型數，保留前次 baseline，不產生本輪假異動。
  此為型別／已知說明文字／數量崩落保護，不宣稱涵蓋同數量的大幅替換
  或任意自然語言。真實大量退場亦可能需人工核對。
- 本輪修正已於 2026-10-01 提交至 master。本輪遠端驗收須以對應提交的
  Offline tests、Asset version、Pages 及部署頁面實測為準；既有 DELIVERY
  的通過記錄屬於先前版本。各階段結果與交接留在 Downloads。

## 2026-09-24 GitHub 健康與讀者翻譯複核（最新）

- GitHub 9/24 00:29（台北時間）的最新實際資料更新為 17/17 來源任務成功，
  無失敗、降級或持續故障；Mistral 6、MCP Blog 1、ARC Prize 1 均健康。
  00:35 的後續 heartbeat 成功但未重新生成資料，不能當成新一次抓取。
- 該輪 Gemini 翻譯 4 個新候選全部成功；前四輪曾有 timeout／HTTP 錯誤，
  45 筆暫時性 provider 拒絕仍套用原六小時等待。線上 24h AI 列表
  22 個英文標題無繁中顯示值，其中 20 個對上此類拒絕；19 個未翻譯
  英文 RSS 摘要也全部對上。其餘兩個標題是 `llm` 工具版本名稱。
- 本機將暫時性 provider 故障的重試等待縮至 30 分鐘；無效譯文維持
  六小時，429 限流仍不寫拒絕快取。完整測試 372 項通過，Python 編譯、
  Node 語法及差異格式檢查通過。線上回補須由推送後的新資料更新驗證。
- 已完成 GitHub 健康與未翻譯原因複核；下一階段是觀察推送後的
  GitHub 翻譯回補，建議 GPT-6 Sol／Low。

## 2026-09-23 本機差異審閱與來源健康觀察（最新）

- 已審閱本輪本機差異，確認三站只接入既有 RSS/Atom 路徑，ARC Prize
  維持第三方評測身分；五個人工查漏站、其餘五個暫緩 feed、公開資料契約
  與 24h 讀者窗口均未擴張。這些變更仍只在本機，尚未 push 或部署。
- 修正新 feed 的健康判斷：有效但沒有近期合格文章維持健康零則；若整個
  feed 缺少具日期的第一方文章，明確回報失敗，避免欄位失效被當成低頻。
- 9/23 暫存生成的三站健康基線仍為 Mistral 6、MCP 1、ARC Prize 1，
  16/16 任務成功；新增欄位失效回歸後完整測試 371 項通過，編譯、
  Node 語法及差異格式檢查通過。
- 使用者已取消本地 Codex 每日 09:00（Asia/Taipei）來源健康觀察；
  後續改在推送後手動執行 GitHub 驗證並檢查 Actions log。
- 已完成本機差異審閱與本地定時任務取消；下一階段是提交推送後核對
  GitHub 上的來源健康紀錄，建議 GPT-6 Sol／Low。

## 2026-09-23 准入來源最小接入與暫存驗證

- 依已完成的准入判斷，沿用 RSS/Atom 抓取路徑接入 Mistral 官方公告、
  MCP 官方協定公告與 ARC Prize 第三方評測；三站有獨立健康任務及每輪上限。
  明確客戶案例／教學、一般協定說明、政策及募款文章在來源處排除。
- ARC Prize 使用獨立評測來源身分及讀者標示，不冒用模型廠商官方公告；
  ARC-AGI 原始結果可命中既有「評測基準」事件。前端只補必要來源標示，
  資產版本已更新；六類事件與 24h 窗口未放寬。
- 9/23 完整暫存生成寫入 `/private/tmp/ai-news-radar-admitted-20260923/`：
  16/16 來源／任務健康，Mistral 6、MCP 1、ARC Prize 1 則進入 archive。
  三站目前均無 24h 文章，網站新聞列表暫無新卡片屬預期。
  五個原始人工查漏站及另五個暫緩直接 feed 仍未接入。
- 暫存生成的精簡健康與收錄證據已歸檔於
  `/Users/lordmi/Downloads/ai-news-radar-source-review-20260923/IMPLEMENTATION_VALIDATION.md`
  及同目錄 `integration-validation.json`。
- 完整測試 369 項通過，Python 編譯、Node 語法、差異格式檢查通過；
  測試與生成未使用付費來源、翻譯或摘要憑證。保留既有本機修改，
  未 commit、push 或部署。
- 已完成准入來源最小接入與暫存驗證；下一階段是使用者審閱本機差異及
  持續觀察來源健康，建議 GPT-6 Sol／Medium。

## 2026-09-23 八站來源准入與最終複核（優先於下方歷史紀錄）

- 八個 YunNEWS 公開出處候選的原始 feed 欄位、最近 45 日 51 則內容與
  9/21 線上 8,723 筆 archive 已對照；直接網址零重複不代表事件零重複。
- Mistral、MCP Blog 准入一手公告範圍；ARC Prize 有條件准入第三方評測，
  接入前須保留正確評測身分並排除非評測文章。LM Studio、Cloudflare、
  Modular、Zed、Google Antigravity 暫不准入，理由見 `SOURCE_COVERAGE.md`。
- 完整欄位、原始 XML、准入限制及重疊例子存於
  `/Users/lordmi/Downloads/ai-news-radar-source-review-20260923/`。
  五個原始聚合／日報站仍只是人工查漏候選；本階段沒有啟用新來源。
- 最終差異複核清除了通用資安回歸測試中已撤回的 TheAI 來源名稱，
  不改測試的資安新聞／教學判定意義。先前保留的摘要歸因限制維持。
- 使用本機 Node 路徑重跑完整測試 364 項通過；Python 編譯、Node 語法與
  `git diff --check` 通過。既有工作區修改均保留，未 commit、push 或部署。
- 已完成逐站欄位整理、來源准入判斷與最後複核；下一階段才是對准入來源
  做最小接入及暫存輸出驗證，建議 GPT-6 Sol／High。

## 2026-09-22 恢復與決策更新（優先於下方歷史試行紀錄）

- 中斷完整性檢查：本機差異符合暫停點，18 份前次 JSON 全部可解析，
  整合評估所引用四份原始紀錄皆存在。暫停前尚未開始撤回或新一輪抓取。
- 使用者否決 YunNEWS 排版／維護收益與 TheAI 文章落差；五站統一改為
  未來人工檢查內容缺漏的候選參考，不是自動查漏、編輯或寫作流程。
- 撤回 YunNEWS／TheAI 抓取器、任務、分級、限量與專用佐證規則；
  `scripts/update_news.py` 恢復至 HEAD，專用六項測試已先歸檔再移除。
  既有摘要 prompt v2 與資安新聞回歸測試保留。
- 先前驗證、撤回前 patch／文件／專用測試及校驗碼歸檔至
  `/Users/lordmi/Downloads/ai-news-radar-source-review-20260922/`。
- 已完成 YunNEWS 全部公開期別盤點：60 期、2,486 則，原始與佐證 URL
  整理為 195 個出處網域。93 個 feed 兩次可解析；4 個只是 Google News
  轉接；4 個有解析警告；85 個本輪未找到標準 feed；8 個社群／橋接依
  產品邊界排除；Anthropic 1 個沿用既有靜態解析器驗證成功。
  這是公開刊出內容的出處盤點，不代表私有完整訂閱設定；技術可讀也不等於
  官方一手或准入。共享平台需逐 repo／組織驗證，本輪不新增上游站點。
- 官方直接 feed 優先候選：Mistral、LM Studio、MCP Blog、Cloudflare、
  Modular、Zed、ARC Prize、Google Antigravity。日期完整但部分更新低頻；
  尚待內容與覆蓋增益驗收。Claude／Cursor／Cognition 靜態頁僅為備選。
- 完整 pytest 364 項通過，Python 編譯、Node 語法、diff hygiene 通過。
  撤回後暫存生成 108 則 AI、13/13 健康任務成功，兩站任務與文章皆不存在。
  未修改正式 data、feeds、前端或 Actions，未 commit、push、部署。
- 完整證據見上述歸檔的 REPORT.md、sources-verified.csv、completion.json，
  含撤回前／後快照、逐站請求與雜湊。舊本機預覽仍是 9/21 試行快照，
  不代表目前 repo；本輪最新可檢視資料在歸檔 generation/data/。
- 已完成中斷完整性複核、五站撤回歸檔及上游一輪驗證；下一階段為優先官方
  feed 的內容／重疊驗收，再決定最小接入。建議 GPT-5.6 Sol／High。


## 2026-09-21 複核：清除跨專案污染

- 外部 `AI_NEWS_RADAR_PULSE_CODEX_HANDOFF.md` 混入另一個 GPT 專案的
  編輯流程。使用者要求以 README 為界；不引入選題分流、查證狀態、
  競品採用研究或寫作交接，也不更改現有六類事件與一般列表的收錄範圍。
- 污染清理階段先只把五站保留在 `SOURCE_COVERAGE.md` 的待評估清單，
  移除外部編輯角色設定；來源註冊延後到文章層級驗收完成後。
- 撤回本輪提前新增的 TheAI 專用閘門、公開 `article_categories` 欄位、
  七處 feed 傳遞與對應測試。摘要中的兩段操作步驟不足以判斷整篇是教學：
  合成資安新聞附補救步驟時會被誤殺。原有教學過濾及資料契約維持。
- 程式只保留既有短摘要的歸因、供應商與版本忠實性限制，prompt 使用 v2
  快取鍵；模型、呼叫上限及輸出結構未變。不增加外部查證，也不宣稱
  prompt 更新等於模型語義驗證通過。回復 v1 可使用舊鍵，無須刪快取。
- 污染清理階段的前一輪 374 項通過包含已撤回功能的 11 項合成測試，
  不是來源准入或功能範圍正確的證明。本次另加 1 項誤判回歸（資安新聞
  保留、明確教學仍排除），完整 `.venv/bin/python -m pytest -q` 在補上本機 Node 路徑後
  364 項通過；Python 編譯及 `git diff --check` 通過，測試暫存放 Downloads。
  當次未呼叫摘要模型或探測五站；抓取器與相關性程式已核對與 HEAD 一致。
- 本輪維持本機修改，未 commit、push 或部署，未改受追蹤資料快照。

### 五站技術探測完成（2026-09-21）

- 以唯讀 HTTP 實測首頁、robots、sitemap、RSS autodiscovery、常見 feed
  路徑及實際 feed 項目；中間 JSON 報告存於 Downloads，沒有寫入 repo
  或變更正式資料快照。
- YunNEWS RSS 當次有未關閉 CDATA，恢復解析會產生亂碼；Look AI 與
  Array 的 RSS 有效，但內容單位是日報／多事件合輯，Array 還混入 glossary。
- AIReiter 只有英文 RSS；繁中頁存在但需 HTML 清單解析或路徑改寫，不符合本輪
  RSS 優先的最小維護方向。TheAI RSS 有日期、摘要、文章 tag 與離散 URL，
  技術結構最可用。
- 本階段沒有新增、刪除或啟用來源，也沒有修改抓取器。

### 五站文章品質、成本與重疊評估完成（2026-09-21）

- 額度中斷後先更新中繼資料：17 份既有 JSON 均可解析，90 個抽樣文章頁
  均為 HTTP 200；四站抽樣仍吻合目前 feed。線上 archive 更新為 8,723 筆，
  14 日對照窗口為 3,574 筆。整合報告存於 Downloads 的
  `ai-news-radar-source-evaluation-20260921.json`。
- YunNEWS 除破損 RSS 外有免金鑰公開 REST API；最新 20 則仍有 10 則原始
  URL 已存在 archive，且 16 則為 `reported`、2 則 `unverified`。採用成本低，
  只適合低量 watchlist；排除 `unverified`，連回原始發布者，且不增加獨立
  佐證票數。
- AIReiter 英文 RSS 的引用透明度尚可，但 20 篇只有約 5 篇是明確近期新聞，
  其餘多為價格、評測、比較、教學或 SEO 題材。繁中 `/tw/blog` 清單可一頁
  取得文章卡片，但 20 個同 slug 頁面有 2 篇仍是英文；成本與新聞增益不相稱，
  本輪不接入。
- Look AI 的內容與外部引用品質佳，但一頁含 6–8 個事件，RSS 只有整期日報；
  先作缺漏對照而不接入。Array 最新 20 篇混有 6 篇 glossary，新聞日報又
  缺少逐則原始新聞連結，判定不接入。
- TheAI 的 60 篇 feed 中只有 6 篇 `/blog/`，其中 4 篇精確標為 `AI 時事`、
  2 篇為 `時事評論`。實作只取 `/blog/` 且精確 `AI 時事`，不傳遞 tag 到
  公開 schema，不納入評論、工具、評比、教學或企業軟文。
- 已完成五站文章品質、接入成本與重疊評估，下一階段是最小來源實作：
  YunNEWS API 低量觀察源與 TheAI 精確新聞閘門；建議使用
  GPT-5.6 Sol／Medium。其他三站不加入。

### 最小來源實作完成（2026-09-21）

- 新增 YunNEWS 公開 JSON API 任務；只接受 `confirmed`／`reported`、三日內、
  有效外部原始 URL 的項目，單輪及讀者窗口最多 5 則。讀者來源固定標為
  YunNEWS，避免把 AI 聚合摘要誤認為原發布者文字；上游來源與信心只作
  解析期私有資訊，不擴張公開 schema。YunNEWS 為 watchlist rank 6，合併
  故事時不增加獨立佐證票數。
- 新增 TheAI 獨立健康任務，但資料沿用 `tw_media` 讀者分組；只接受七日內、
  `/blog/` 且 tag 精確為 `AI 時事` 的文章，單輪及讀者窗口最多 4 則。
  TheAI 發布者級 tier 為 watchlist rank 6；評論、工具、評比、教學、企業
  應用與其他 tag 均不進入。
- 有效來源若暫時沒有符合條件的文章會回報健康的零項結果；介面或解析失敗
  才累計來源故障。AIReiter、Look AI、Array 未加入任何抓取任務。
- 完整暫存抓取寫入 `/private/tmp/ai-news-radar-validation-final`：TheAI 4 則、
  YunNEWS 5 則，兩個健康任務皆成功；24 小時結果經既有時間窗、相關性與
  去重後保留 YunNEWS 2 則，TheAI 4 則因較舊只進 archive。公開輸出沒有
  `tags`、`article_categories`、內部信心或上游來源欄位。
- 已完成最小來源實作與暫存輸出驗證，下一階段是最終範圍與回歸複核；
  建議使用 GPT-6 Astra／High。

### 最終範圍與回歸複核完成（2026-09-21）

- 最終程式範圍只有兩個來源局部解析器、各自健康任務、低量上限、watchlist
  tier 與 YunNEWS 非獨立佐證規則。AIReiter、Look AI、Array 沒有來源常數、
  任務或解析器；沒有新增編輯／寫作流程。
- 未修改 `data/`、`feeds/`、`.github/`、前端或既有公開資料 schema；完整抓取
  只寫入 `/private/tmp`。先前保留的摘要 prompt v2 與資安新聞誤判回歸仍是
  本輪其餘兩項程式修改。
- 完整測試 370 項通過；Python 編譯、`node --check assets/app.js` 與
  `git diff --check` 通過。未 commit、push 或部署。
- 已完成最終範圍與回歸複核，下一階段是使用者審閱本機差異；本次原先
  同意的最終複核建議為 GPT-6 Astra／High，現已完成。

## 2026-09-12 來源品質分級、同源去重與時間閘門

- 以 2026-09-12 線上 21 天 archive 重算來源品質。iThome（133 筆、
  48.1% 商業事件、0 同源重複）改用 publisher-level
  `professional_media` rank 1；The Decoder（144 筆、19.4% 商業事件、
  0.7% 同源重複）改用 `ai_vertical` rank 1。兩者仍保留原本共用的
  `tw_media`／`curated_media` 抓取與健康狀態 ID。
- 數位時代 Google News 路由在同一窗口有 26.4% 同源重複、5.0% 商業
  事件率，改用 `advanced` rank 4。其 Google News publisher suffix 變體在
  進入翻譯與讀者資料前依同一發布者標題去重。
- 36Kr 維持 `watchlist`：它仍補中國市場邊際覆蓋，但 21 天 1,479 筆中
  約 49.1% 是同源重複。單輪抓取與 24 小時 reader output 均限制最多 5
  筆，並先折疊 `36 Kr`／`36kr.com`／`m-ai.36kr.com` 等標題尾碼變體。
- RuntimeWire 的 21 天樣本為 43 筆，100% 通過 AI gate、32.6% 命中商業
  事件、0 同源重複，跨來源估算 90.7% unique；由 watchlist 有限升至
  `advanced` rank 4／「次級AI媒體」。LLM Rumors、LLM Stats、橘鴉維持
  watchlist。AIBASE 維持既有 backend tier 與前端聚合呈現。
- Reader 24 小時窗口新增發布時間上限：只接受
  `published_at <= generated_at + 6h`，容許小幅來源時鐘／時區偏差，拒絕
  提前數日的來源日期。Archive 與 resolver 仍保留原始發布時間，不竄改
  上游資料。

## 2026-09-08 AIBASE 繁中優先與一般列表來源分級

- AIBASE 讀取 `https://news.aibase.com/tw/news` 與
  `https://news.aibase.com/news` 的公開 Nuxt 新聞列表資料，各取首頁相同
  範圍；繁中欄位優先，英文補缺欄位與缺文章。不讀介紹頁或文章全文。
- 原生繁中標題、摘要與連結直接使用；英文補入文字沿用既有翻譯。
  以列表 `createTime` 作發布時間（無時區值按 UTC+8），雙語均無可確認
  日期者保留 archive，但不以首次發現時間進入讀者 24 小時窗口。
- 跨語言依 AIBASE 上游文章 ID 沿用既有 Radar ID；已取得繁中欄位不因
  暫時英文回退而降級。歷史同文重複 ID 保留 resolver，但以
  `duplicate_of` 排除重複展示；次要紀錄不刷新 last_seen，依原 21 天
  規則自然退場。全站 `make_item_id()` 演算法未變更。
- 一般列表改為「原始來源／專業媒體／聚合／二次整理／其他與觀察來源」
  四個區塊（聚合／二次整理是同一區），內層依發布者分組，同級沿用既有
  排序。AIBASE 在聚合區，台灣專業媒體在媒體區；機構自有研究發布在
  原始來源區。RSS/OPML 依發布者辨識，未知來源與觀察名單置後。
- 這是獨立的前端呈現分類；AIBASE 的共用資料身分仍為
  `curated_media` / `AIBASE`。今日重點訊號位置、選取、來源多樣性、
  全域評分及獨立雷達未改。已合併同事件沿用既有官方主來源優先規則，
  不新增外部搜尋。
- `source-status.json` 的 AIBASE 任務附 `language_status`、
  `language_mode`、`english_supplemented_count`、`undated_count` 及
  `degraded`。兩版皆失敗仍由既有任務錯誤處理回報。


## 2026-09-07 News-ID resolver contract

- Radar 前端既有「複製新聞 ID」維持複製普通 news item 的 40-char SHA-1
  `id`；`make_item_id()` 演算法沒有變更。
- 每次 `scripts/update_news.py` 產生快照時，會在 GitHub Pages 靜態資料下
  輸出 `data/items/<item.id>.json`。公開 lookup URL 為
  `https://seisyuku.github.io/ai-news-radar_zhtw/data/items/<item.id>.json`。
- 每個 resolver 檔直接沿用 `archive.json` 的公開 item record schema，至少有
  `id`、`title`、`source`、`published_at`、來源 `summary`（若來源有提供）與
  原始新聞 `url`；原文連結固定讀 `url`，不是 `source_url`。沒有 API、
  database、authentication 或 LLM 層。
- resolver 在 archive prune 後寫入，與 archive 相同採 `last_seen_at` 的
  21-day retention（workflow 的 `--archive-days 21`）。archive 已不存在的
  40-char resolver 檔會在同輪刪除；過期 ID 回傳不存在是預期行為。
- 每次快照也會以同一筆 archive record 寫入靜態 HTML adapter：
  `item/<item.id>/index.html`，公開 lookup URL 為
  `https://seisyuku.github.io/ai-news-radar_zhtw/item/<item.id>/`。頁面沒有
  JavaScript，直接呈現 Radar ID、title、source、published_at、summary（若有）
  與可點擊的原始 `url`；所有文字與 URL attribute 都經 HTML escaping。
- JSON contract (`/data/items/<id>.json`) 維持 machine-readable integration
  data；HTML contract (`/item/<id>/`) 是 LLM/browser-friendly resolver adapter。
  ChatGPT Social Editor 應優先開啟 HTML URL、確認頁面的 Radar ID 與輸入相符，
  再讀取 Original URL。兩種 resolver 都隨相同 21-day archive retention 清理。

## 2026-09-03 Groq 摘要模型遷移

- Groq 通知 `qwen/qwen3.6-27b` 即將停用，production primary 改為
  `qwen/qwen3.8-27b`。既有 Chat Completions、JSON object mode、
  `reasoning_effort="none"`、180-token 上限與本地輸出驗證規則維持不變。
- `GROQ_SUMMARY_MODEL` 沒有設定 GitHub Variable 時，workflow fallback 與
  Python 預設會一致使用新模型；模型名稱已包含在摘要快取鍵中，因此保留舊
  cache、不做全量重生，切換後只會依既有每輪最多 6 則的限制補新摘要。
- 沒有新增自動 fallback。若 Groq 暫時失敗，新聞快照依舊 fail-open，僅省略
  摘要；不得回退到即將停用的 3.6。

## 2026-08-21 維運與讀者層校正

- **36Kr AI**：一般 RSS 長期回傳 WAF HTML，排程改以 Google News
  `site:36kr.com` 為正式 watchlist 路由；不再每輪先打不可用的直接 feed
  再把可用結果標示為 degraded。直接 feed 僅保留給低頻維運探測。
- **LLM Stats**：已解析的 `latestModels` payload 若沒有近期 allowlisted
  模型，記為健康的零筆結果 (`empty_reason=no_recent_allowlisted_models`)，
  不再累積 persistent failure；HTTP、payload 缺失與 schema 失敗仍是故障。
- **AI 摘要**：保留繁中、數字、版本名與提示注入驗證；相同
  content/model/prompt 鍵的 `insufficient_context`、`validation_length`
  拒絕會負面快取 6 小時，避免無產出的重複 Groq 呼叫。
- **AIBASE**：讀者資料改歸入 `curated_media` 的 `精選媒體` 群組，子來源
  顯示固定為 `AIBASE`。它不再是「AI網站」或社群類，也不再套用舊的
  default-source 100 分地板／AI 垂直源權重；仍與中國聚合來源共用
  corroboration ecosystem，不能藉轉載提高多源熱度。舊 archive 記錄在
  下次排程載入時會一併正規化，避免保留窗內重新產生獨立群組。
- **重點訊號卡**：移除所有固定理由與 RSS 摘要回退文案。只有產生且通過
  驗證的 `news_summary` 才建立「AI 新聞摘要」區塊；沒有摘要即完全不渲染
  其標題、留白或固定字串。

## 專案身份
- Fork：seisyuku/ai-news-radar_zhtw（上游 LearnPrompt/ai-news-radar，MIT）
- 線上：https://seisyuku.github.io/ai-news-radar_zhtw/
- 架構：GitHub Actions 排程 + watchdog + 外部心跳三層（見下方「排程
  健康」）+ Pages 靜態頁，零伺服器零月費
- 目標：六類商業事件情報（財報/市佔/資安漏洞/價格/benchmark/模型發布），
  排除程式技巧與社群意見；全站繁中（zh-TW）

## 協作協議
- Chat = 規劃/決策/驗收裁決；Claude Code（Sonnet 5:high）= 執行
- 一次一步，執行後回報再進下一步
- Git：GitHub Flow 極簡版，feature branch 短命速合，文件類變動經
  明示授權可直接 commit master；data/*.json 為機器產物不手改，衝突
  取遠端；shallow clone 屬預期

## 已落地的關鍵改造
1. 信息源置換：砍 11 個社群熱榜源；接入廠商一手、財經（GNews 查詢式）、
   benchmark 第三方、台灣繁中媒體、36Kr、橘鴉日報（對照源）
2. 繁中化：UI 全繁中 + 全管線 `to_zh_hant()`（含冪等性防護）+
   `SITE_NAME_ALIASES` 出口正規化
3. 商業事件加權：`BUSINESS_EVENT_KEYWORDS` 六類雙語規則 → 前端排序
   + 徽章；第六類「模型發布」為主體×發布詞×語境詞三重防護，規則
   詳見程式碼
4. 噪音閘門：HN 轉發過濾（聚合器後門）+ V2EX 網域級排除
   （`AGGREGATOR_BACKDOOR_EXCLUDED_DOMAINS`，同聚合器後門機制形狀但
   鍵值為網域非來源標籤，掛在 `score_ai_relevance()`，只影響收錄層
   `items_ai`，`items_all` 透明度視圖不變）+ 關鍵字誤判修正（merger/
   hackathon/遊戲排行榜/eval 語境防護，規則詳見程式碼）
5. 生態群組去重：`SOURCE_ECOSYSTEM_GROUPS`（中國聚合器群），
   story_heat 同群多源只計一次
6. 基礎設施：前端資產 `?v=` 版號由 `tests/test_asset_versions.py`
   強制；規則見 `docs/OPERATIONS.md`
7. 教學文收錄過濾：標題模式硬性排除（英文句首錨定 + 中文複合詞，
   規則詳見程式碼）；已知殘差 2 條無徽章教學文，已測試釘住接受
8. 官方源接入：Thinking Machines Lab（thinkingmachines.ai/index.xml，
   Hugo 標準 RSS，非常見 /feed 路徑）
9. 翻譯正典名稱表（`CANONICAL_NAMES`，取代舊 BRAND_GLOSSARY，四階段
   全案已結案）：三層防線——遮罩回填（翻譯前，主防線）/ 出口修正
   （exit-fix，命中 Table A/B 回寫 cache）/ 反向修正（Table C，只修
   顯示不回寫）。Claude 五子系詞另有兩條擴充通道：非相鄰共現（同標題
   有 Claude/Anthropic 即保護）、與第四階段「無 Claude 共現也保護」
   （大寫詞形 + 緊鄰版號 + 同標題任一 CANONICAL_NAMES 實體共現，
   排除微軟/Google/蘋果/亞馬遜/三星/騰訊等綜合巨頭，防遊戲/消費品
   誤中）。範圍刻意維持 Claude 五子系封閉集，不泛化到 Gemini/GPT 等
   其他家族尾綴詞——那些是語意開放的常見英文字，Claude 子系則有大量
   實測誤譯證據支撐。機制全文、匹配規則、日常維護方式見
   `docs/OPERATIONS.md`「翻譯管線」章節；專屬 pytest 約 37 案例。翻譯 provider
   已改為固定的 Gemini `gemini-3.5-flash-lite`；缺少 credential 或 provider
   故障只保留英文，不得阻塞快照更新。`source-status.json.translations` 與
   `translation-state.json` 分別提供無敏感資訊的狀態與六小時拒絕快取。
10. 資料時效警示帶：前端讀 `generated_at` 與瀏覽當下比較，2 小時內
    不顯示、2-6 小時低調樣式、6 小時以上明顯樣式，門檻常數化
    （`STALE_DATA_WARN_HOURS`/`STALE_DATA_BAD_HOURS`）
11. 重點訊號區資格閘門：`featuredCandidatesGate()` 前置過濾（不重排，
    既有徽章優先四級排序 `briefStorySortCompare` 不動）——徽章
    （`business_events` 非空）直接入選；無徽章僅在非
    `COMMUNITY_SOURCE_TYPES`（AIBASE）來源時才能補位，寧缺勿濫不硬湊。**未做**地板值
    排除：後端分數已被 `max(score, 0.65)` 覆寫，前端 JSON 無欄位能
    可靠區分真實分與地板值，判斷不可行後只做源類型排除（已回報此
    限制，非遺漏）。掛在 story-pool 與 no-story-data fallback 兩條
    候選池入口
12. 前端死代碼清理：`HN熱議` 分頁/計數器整組移除（背後 hackernews/
    zeli 抓取器已於 07-14 源置換移除，此為孤兒 UI，非過濾結果）；
    07-21 補一批同型殘留——`sourceSignal()`/`sourcePriority()`/
    `clusterBriefEvents()` 內的 `HN熱議`/`GitHub趨勢` 判斷分支同理
    清除（`clusterBriefEvents` 家族經 `renderBriefPicks()` →
    `rankedFallbackRows()` 仍有存活呼叫路徑，故只清殘留字串，不構成
    整組退役）
13. **7/21 四源審判裁決**：`iris`（Info Flow）、`techurls` 退出預設
    來源；2026-08-26 已將其與其他退役來源的擷取器、來源權重及前端殘留
    一併刪除，不保留 rollback 程式碼。`36Kr AI`、xAI/Grok 查詢詞
    （curated_media 內）維持不動。`AGGREGATOR_BACKDOOR_EXCLUDED_DOMAINS`
    （v2ex.com）保留為非來源專屬的 URL 網域防護。裁決依據見
    `docs/SOURCE_COVERAGE.md`「2026-07-21 Four-Source Trial」章節。
14. 內測回報管道文案上線：頁尾新增引導至 GitHub Issues 的說明文字
    （`.app-footer-note`），沿用既有頁尾樣式
15. **7/21 重點訊號區來源多樣性上限（N=2,僅退化層生效）**：診斷
    （`.claude-reports/2026-07-21-aibase-signal-area-diagnosis.md`）
    定位 aibase 佔重點訊號區 39.5%（近期 66%）之成因——非品質問題，
    而是絕大多數合格候選為單源（`storyHotScore=0`），
    `briefStorySortCompare` 前兩層（徽章、熱度）恆平手，勝負落在
    `storyScore` 的 22% `source_tier` 分量，使 aibase（`ai_vertical`,
    0.78）系統性擊敗供貨量更大但 tier 較低的來源。裁決：不動
    `source_tier`、不動 `storyScore` 權重（aibase 品質乾淨，壓 tier
    是錯誤懲罰；動權重逼近紅線）；改在選卡層加來源多樣性上限——新增
    `applyFeaturedSourceDiversityCap()`（`assets/app.js`），套用於
    `storyRowsForPool()` 產出的已排序 rows、切片為預設可見 5 席
    （Top3+展開2）之前。上限**只在「純靠 source_tier 決勝」的退化
    情形生效**：某來源已佔 2 席時，若其下一條與「下一個不同來源
    候選」在前兩層（徽章、熱度）平手才讓出席位；`hotScore` 有真實
    優勢者，或無不同來源候選可比較者，不受上限約束，仍保留席位
    （寧缺勿濫優先於多樣性，但不因多樣性規則反而剔除合格內容）。
    讓出的席位只由排序中「原本就在候選池」的其他合格候選（有
    `business_events` 徽章）自然遞補，不引入候選池外的內容。回測
    （復用診斷 40 次快照）：aibase 佔比 39.5% → 26.5%（近 10 次快照
    66.0% → 40.0%），40 次快照中無一次因上限造成 <5 席（既有資料
    供給充足，寧缺勿濫分支未被觸發，`applyFeaturedSourceDiversityCap`
    亦從不減少候選總數，只重排順序）；26 個因上限讓出而變更的席位
    100% 由有徽章候選遞補、0 例降級納入無徽章/社群類條目；40 次快照
    樣本中無 aibase 真實熱度豁免案例（該窗口 aibase `duplicate_count`
    100%=1，單源為主下豁免路徑未被觸發，符合診斷 D1 既有發現），
    豁免邏輯正確性改由合成案例的單元測試
    （`tests/test_featured_source_diversity_cap.py`）驗證。細節與
    上限前後完整對照表見
    `.claude-reports/2026-07-21-featured-diversity-cap.md`。
    **範圍追認**：工單原文以「熱點」（`hot`）檢視為診斷對象，實作時
    一併套用到「時間線」（`timeline`／`latestStories()`）路徑——該
    路徑底層同樣呼叫 `briefStorySortCompare`，存在完全相同的單源
    平手退化風險，若不一併套用，使用者切換檢視即可繞過上限、
    aibase 集中問題原封不動重現。此擴大已於驗收時追認為正確範圍，
    非後續才發現的遺漏。

16. **8/16 Model Release Radar v1**：新增三個獨立、可觀測且維持
    `watchlist` tier 的來源：LLM Stats `latestModels` 只負責近期主要實驗室
    模型的 atomic 查漏；LLM Rumors RSS 補長篇策略分析；RuntimeWire RSS
    以嚴格標題篩選補模型、推理、價格與 benchmark 後續，未啟用其高量
    Head-to-Head feed。同步修正模型發布分類器把版本小數點誤當句號的
    bug（Qwen3.8/Grok 4.6/Gemini 3.7 先前因此漏徽章），並擴充
    Qwen/GLM/Kimi 的模型版本識別，避免跨版本錯誤聚合；「模型」分頁
    額外合併 24 小時內的 atomic 發布資料並以發布事件優先，不污染其他分頁的
    24 小時窗口。未修改全域評分公式；後續分析聚合與
    `model_significance` 仍列 Roadmap 待辦。
17. **8/17 Groq 新聞短摘要 v1**：RSS/Atom fetcher 開始保留並清理來源
    `summary`/`description`；排程在設定 `GROQ_API_KEY` 時，以
    `qwen/qwen3.6-27b` 對有內容依據的高優先 story 產生 30–120 字繁中
    摘要，單輪最多新增 6 則，並以 `data/ai-summary-cache.json` 內容雜湊
    快取避免重複呼叫。標題-only 不送出；provider 或輸出驗證失敗不阻斷
    更新。前端「為什麼重要」固定模板已移除，改顯示「AI 新聞摘要」；
    沒有合格摘要時整塊隱藏。未修改全域評分公式。
18. **8/17 Gemini 摘要備選候選裁決（未啟用）**：`gemini-3.5-flash-lite`
    在新 project 已通過 model discovery、plain `generateContent` 與
    structured JSON；七個合成案例為 5 generated pass、1
    `insufficient_context`、1 因缺少精確詞「不可信」未過 deterministic
    gate，但未重現提示注入指令或疑似 key。歷程另確認舊 project 的
    `429 RATE_LIMIT_EXCEEDED` 與 `gemini-2.5-flash-lite` 對新使用者的
    `404 NOT_FOUND` 是不同失敗原因。裁決為
    `qualified backup candidate, disabled by default`：Groq 仍是 primary，
    摘要 workflow/production 未做 Gemini fallback、未授權真實 feed 內容送往
    Gemini 產生摘要。這不影響 2026-09-07 已採用的讀者翻譯路徑。摘要 fallback
    啟用前必須完成三時段穩定性、同案比較、
    trigger matrix、防雙重計費、provider+model cache、成本/狀態護欄與
    tier 資料政策裁決；完整準入條件見 `docs/OPERATIONS.md`，sanitized
    證據見 `reports/provider-evals/gemini-3.5-flash-lite-20260817.md`。
19. **8/17 LLM 翻譯與 Simon Willison 徽章修正**：`LLM`／`LLMs` 納入
    `CANONICAL_NAMES` 遮罩，翻譯 provider 不再把 AI 縮寫譯為「法學
    碩士」；既有快取也會依原始英文標題定點修復並回寫。Simon Willison
    是公開示範 OPML 的既有 builder feed，不是臨時來源；其 Qwen 3.8
    文章的錯誤「財報」來自量化格式 `Q4_K_M` 被誤認為季度 `Q4`。ASCII
    關鍵字邊界已將底線視為 token 一部分，該篇保留有內容依據的「評測」
    徽章，不變更全域排序或擴大摘要資料取得範圍。
20. **8/17 Top10 摘要可見性與失敗可觀測性**：Top3 後的故事卡現在在
    `news_summary` 存在時顯示兩行內的「AI 摘要」，避免已生成內容只因
    精簡卡版型而隱藏。title-only 條目仍不會生成摘要；這是來源內容不足
    的安全邊界，不是前端缺漏。`source-status.json.ai_summaries` 保留原有
    `last_error_type`，並新增不含原文與 provider 回覆的
    `last_error_detail` allowlist，供診斷 Groq 輸出被本地 gate 拒絕的原因。
21. **8/17 Top10 來源多樣性與摘要繁體化**：來源多樣性上限現在對熱點完整
    Top10 生效，而非只在預設可見的前五格生效；同源單源平手內容會讓位給
    同層的其他來源，真實多源熱度仍保留，沒有調整 AI relevance 或重要性
    權重。Groq 摘要在生成及快取讀取時都以 OpenCC `s2t` 統一為繁體，修復
    `将`／`并购` 類模型輸出殘留，且不另送內容到翻譯服務。
22. **8/17 摘要候選不中斷與英文 RSS 顯示界線**：`GROQ_SUMMARY_MAX_NEW`
    的上限只計成功新增摘要；驗證失敗不再耗盡額度而讓後段、已在讀者畫面
    的有 RSS 內容故事永遠無法嘗試。候選嘗試仍受既有 20 條上限保護。Top
    卡一旦有合格繁中 AI 摘要，就隱藏原始 RSS 摘要，避免英文原文與繁中摘要
    同時呈現；無合格摘要時仍顯示來源原文，且不為 title-only 項目新增抓取。
23. **8/17 RSS 摘要顯示翻譯**：既有英文 RSS `summary`／`description`
    現在沿用 title 的翻譯管線、正典名稱遮罩及繁體轉換，輸出
    `summary_zh` 供前端優先顯示；原始 `summary` 保留作 Groq 事實依據。
    原生繁體 RSS 摘要只正規化、絕不送翻譯；沒有 RSS 簡介的條目不新增
    抓取或推測。翻譯快取以 `summary::` 前綴與既有 title 快取共存。

24. **9/07 Gemini 讀者翻譯遷移**：讀者層英文標題與 RSS 摘要的顯示翻譯，
    從 Google Cloud Translation／DeepL 路徑改為固定使用 Gemini Developer API
    `gemini-3.5-flash-lite`。請求走 Interactions API 的 JSON schema 回應，將來源
    文字視為不可信內容，要求原始項目 ID 一一對應，並驗證 placeholder 與 URL
    沒有被遺失。每輪維持串行、最多 6 請求；429 僅在 `Retry-After` 可落入剩餘
    45 秒預算時重試，否則 fail-open 且不寫入六小時拒絕快取。這是 public reader
    translation 的單一 provider，不改動 Groq 摘要或私人產稿器；Actions 必須設定
    `GEMINI_API_KEY`，免費層只可傳送公開新聞內容。

25. **9/11 Gemini 翻譯修復**：線上 Actions 仍有翻譯候選且 secret 已注入，
    但 10 秒 transport timeout 被共用 feed session 的 POST retry 暗中重跑三次，最終
    包裝成 `ConnectionError` 並吃完整輪 45 秒預算，`translated_count` 因而連續
    為 0。翻譯已改走同模型完整支援的單輪 `generateContent` endpoint；Gemini
    prefix 使用 no-retry adapter，單次／整輪邊界調整為 45／120 秒。原有 JSON
    schema、項目 ID、placeholder／URL 驗證與 fail-open 邊界保留；翻譯狀態版本
    提升至 4，部署後會捨棄故障期間的拒絕快取並立即重試。

## 部署

實測 `gh api repos/{owner}/{repo}/pages`（2026-07-28）：

```json
{
  "status": "built",
  "cname": null,
  "custom_404": false,
  "html_url": "https://seisyuku.github.io/ai-news-radar_zhtw/",
  "build_type": "legacy",
  "source": { "branch": "master", "path": "/" },
  "public": true,
  "https_enforced": true
}
```

- **發佈來源**：`master` 分支根目錄（`path: "/"`），非 `gh-pages` 或
  其他分支
- **build type**：`legacy`——GitHub Pages 直接監看分支內容並發佈靜態
  檔案，無 Jekyll 或其他建置步驟
- **自訂網域**：無（`cname: null`），使用預設 `github.io` 網域
- **HTTPS**：已強制啟用（`https_enforced: true`）
- **`.github/workflows/` 內無 Pages 部署 step，發佈由 GitHub Pages
  直接監看 `master` 分支完成**——`update-news.yml` 的 `update` job
  推送新的 `data/*.json` 後即由 Pages 自動反映，不需額外部署動作

## 已知設計事實（避免重複調查）
- 收錄門檻 = ai_relevance ≥ 0.65；六類只主宰重點區排序，非收錄條件
- ai_relevance 有 has_ai 地板值 max(score, 0.65)——上游設計，
  動它需 14 天回測（治理規則），未動；聚合器條目多靠地板值過關，且
  此覆寫使前端無法回推真實分（見「重點訊號區資格閘門」的地板值排除
  限制）
- BRIEF_SCORE_GATE/daily-brief 原始排序不影響使用者所見
  （調查結論在 story_passes_brief_gate() docstring）
- `renderBriefBrief()` 是死代碼；另發現同批未被呼叫的死代碼：
  `pickBriefItems()`、`clusterBriefEvents()` 的獨立呼叫路徑、
  `renderStoryViewPanel()`——皆僅定義未被任何即時渲染路徑呼叫，
  未清除（非本輪範圍），供未來清理參考
- 重點卡片減噪：下排內容分類標籤列與「優先順序 A/B/C」chip 已移除
  （importance_label 後端欄位與排序引用不動），上排業務事件徽章與
  內容標籤統一去重、近義詞讓位（model_release 抑制「模型釋出」
  內容標籤）
- `to_zh_hant()` 詞彙保護層裁決與已知限制（2026-07-21，
  `ZH_HANT_PROTECTED_TERMS`/`ZH_HANT_BARE_TERM_CONTEXT`，見
  `scripts/update_news.py` 常數上方註解）：`参数` 無條件保護為
  `參數`，前提是本站產品定位排除程式技巧/開發者社群內容（若未來
  納入此類內容，需重新評估）；已知限制是 CLI 引數（argument）語境
  的 `参数` 也會被誤改為 `參數` 而非技術正確的 `引數`——2026-07-21
  全量回溯（`archive.json` 90,826 筆唯一標題）基準：131 筆 diff／
  128 筆修正／3 筆接受誤傷（0.0033%，皆出自已移除的 Show HN／開發者
  社群來源）；曾評估改為 AI/模型語境共現閘門（比照裸詞「字節」）但
  已否決，因為會讓規格參數類標題（手機/鏡頭/晶片/Kubernetes 設定）
  退回錯誤的「引數」，得不償失——**不得未來善意重新引入此共現閘門**
- `to_zh_hant()` s2twp context-collision 定點保護（5 詞，2026-07-21，
  `fix/zh-hant-context-collision-0721`，見
  `.claude-reports/2026-07-21-zh-hant-context-collision.md`）裁決記錄：
  1. **保護內容**：`循环`/`回调`/`图像` 併入 `ZH_HANT_PROTECTED_TERMS`
     無條件保護（`循環`/`回調`/`圖像`，理由與「参数」同一產品範疇
     排除假設）；`ZH_HANT_BARE_TERM_CONTEXT["字节"]` 共現詞集擴充
     「BAT」與公司行為動詞「发现/推出/发布/宣布」；新建
     `ZH_HANT_REVERSE_BARE_TERM_CONTEXT["对象"]`（storage 語境共現詞集：
     存储/存儲/数据库/資料庫/database/storage/S3/OSS/bucket）——**方向
     與「字節」閘門相反**：預設攔回「對象」，僅 storage 語境共現時才
     放行 s2twp 原生輸出的「物件」。全量回溯 `archive.json` 85,926 筆
     唯一標題：249 筆 diff／182 筆預期修正／59 筆共現閘門判定／
     **8 筆已裁決接受的誤傷**
  2. **已接受的 8 筆誤傷**：7 筆為真程式語境（loop/callback 語境被
     `循環`/`回調` 誤保護，範疇外，比照「参数」CLI 引數先例）、1 筆
     為物件儲存罕見措辭（`对象标签读写`，未含 storage 詞集任一關鍵字）
  3. **對象 storage 共現詞集的已知缺口**：以非清單詞（例：`云`、
     `localStorage`、`标签`）描述物件儲存語境的標題，會被反向閘門
     預設攔回「對象」而非 s2twp 原生的「物件」。**明列為未來「第七類」
     工單前置**——第七類上線、物件儲存成為讀者核心內容時，須以該
     類別實際的 `items_ai` 可見樣本重新調校此共現詞集，不在本輪
     （2026-07-21）硬調，避免無實際樣本支撐的臆測性擴詞
- Python `re` 模組在 Unicode 模式下 `\w`/`\b` 會匹配 CJK 表意文字，
  因此 `(?<!\w)term(?!\w)` 形式的 Latin 詞界錨定，在中英混排標題
  （本站最常見的標題形態）下對緊鄰 CJK 字元的英文詞恆為匹配失敗。
  Latin 詞界必須改用 ASCII-only 邊界
  `(?<![A-Za-z0-9])...(?![A-Za-z0-9])`。此類 bug 的特徵是**單元測試
  全綠但實際場景全滅**（純英文測試字串不會觸發，只有真實中英混排
  語料才會曝露），不會自行浮現，日後任何用到 `\w`/`\b` 做 Latin 詞
  境判斷的程式碼都要留意此陷阱（實際案例見
  `_zh_hant_bare_term_context_ok()` 的開發過程，
  `.claude-reports/2026-07-21-zh-hant-term-protection.md`）
- `.site`／`.source`／`.category` 三個徽章的隱藏邏輯彼此獨立，互不
  依賴（2026-07-21，`CATEGORY_REDUNDANT_WITH_SOURCE` 整組退役後）：
  `.site`／`.source` 的隱藏各自由 `renderItemNode()` 內兩個獨立的
  `context.source === item.source` 判斷式負責，在 `buildSourceGroupNode()`
  的巢狀分組渲染情境下對幾乎所有卡片恆為真（該來源子分組內所有項目
  的 `item.source` 本就等於分組鍵本身）；`.category` 現為一般分組
  列表中**唯一**的來源識別徽章，無條件依 `SOURCE_KINDS` 渲染，與
  `.source`/`.site` 是否隱藏完全無關。已刪除的
  `CATEGORY_REDUNDANT_WITH_SOURCE` 常數原意是「避免 `.category` 與
  `.source` 重複顯示同一段文字」，但這個前提在現行渲染架構下從未
  成立——`.source` 早被前述獨立機制恆常隱藏，該常數的實際效果只是
  把碩果僅存的 `.category` 也一併關掉，讓 `official_ai`／
  `curated_media`／`opmlrss`／`aibase` 四個 site_id 的卡片完全沒有
  來源識別文字，並非「去重」。重點訊號區（`buildTopStoryCard()`／
  `buildStoryCard()`）完全不使用 `renderItemNode()`，沒有 `.category`／
  `.source` 元素，此常數的設計前提在該區塊亦無從復活
- `SOURCE_KINDS` 的 AIBASE 顯示名稱維持原文 `AIBASE`，並作為「精選媒體」
  的子來源，不形成獨立來源類別。
- `SOURCE_KINDS` 的 `opmlrss` label「OPML」對一般讀者是技術縮寫，
  可理解性存疑（2026-07-21 隨上一項一併檢視時發現，**本輪不改**）：
  `opmlrss` 目前屬進階層 site_id，實際曝光範圍（是否觸及一般讀者
  可見的預設層卡片）未經證實，貿然改字可能是無的放矢，也可能改壞
  已熟悉「OPML」一詞的進階使用者的預期用語，留待獨立工單評估曝光
  範圍後再裁決是否修改
- 測試基線：267 pytest（2026-07-21 重點訊號區來源多樣性上限工單，
  新增 `tests/test_featured_source_diversity_cap.py` 5 案例，由 262
  → 267；此前基線 240 已隨中間工單的測試增補過時，此處一併更新為
  當下實測值，避免下次比對誤判)
- 排程健康 = 三層架構，已將停擺風險吸收掉（完整事故時間軸與診斷
  記錄見 `docs/OPERATIONS.md`「Schedule (cron) health」/「External
  heartbeat」章節）。**2026-07-21 全期（7/17-7/21）唯讀複測驗證通過**：
  - **內部 cron**（4 tick/hr）：全期 59 筆成功 schedule run，平均間隔
    99.5 分鐘、中位數 81.0 分鐘、最大 293.7 分鐘，44.8%（26/58）間隔
    超過 90 分鐘——不可靠層特性依舊，符合既有基線判讀，靠下兩層兜底
    吸收，非本輪需修復項
  - **watchdog**（90 分鐘門檻代觸發）：**確認留**（原「傾向留」升級
    為確定裁決）。全期完整代觸發記錄（非僅先前對話內看到的 2 筆）
    共 **8 次**，**7 次成功、1 次失敗（87.5%）**；唯一失敗即
    `-R` 旗標缺漏事件本身（07-18 03:21Z，缺口 138 分鐘），修復
    （commit `387d27c`）之後同期內連續 **7/7** 成功，逐次對應主排程
    缺口：118／153／114／109／197／160／158 分鐘
  - **外部心跳**（cron-job.org，`:05`/`:35` + 25 分鐘 freshness
    guard，2026-07-19 上線）：脫離 GitHub schedule 機制的結構性解
    法。GitHub 側可見全期 80 筆 `:05`/`:35` 節奏 dispatch，early-exit
    （內部排程健康）59 筆（73.75%）、接管全量執行 21 筆
    （26.25%）——接管比例偏高，反映內部 cron 中位間隔（81 分鐘）
    本就常態性超過心跳 25 分鐘門檻，心跳已是事實上的共同主排程而非
    罕見備援；發現 1 起 GitHub API 側 503 瞬斷（07-20 00:35Z）導致
    單次 freshness-check 失敗，非 cron-job.org 端問題。**已知限制**：
    cron-job.org 自身執行紀錄（含任何從未送達 GitHub 的
    401/超時案例）不在 GitHub 側可見範圍，完整驗證仍需使用者親自
    登入 cron-job.org 後台確認
  - **前端警示帶銜接**：全期 0 次觸發 6 小時明顯樣式；2-6 小時低調
    樣式觸發 6 次（累計約 5.0 小時），**全數集中於心跳上線（07-19）
    之前**，07-19 之後至 07-21 零次觸發，與心跳上線時間點完全吻合
  - **內部 cron 頻率裁決（2026-07-21）**：維持 4 tick/hr，不降回
    上游預設的 30 分鐘一次。理由：降頻不解決病灶（病灶型態是排程
    「歸零」個案而非「過密」，降低密度對此無效）；且 4 tick/hr
    目前仍對資料新鮮度上限有實質貢獻，降頻會在心跳 25 分鐘 guard
    疊加下犧牲現有新鮮度餘裕，省下的 Actions 用量不足以抵銷代價
  - **定調**：停擺已由三層架構吸收，且本輪唯讀複測未發現新的
    未結案異常；若之後又看到前端 2 小時警示帶浮現，代表連心跳層都
    失效了，排查入口 = `docs/OPERATIONS.md`「External heartbeat」
    章節「失效排查順序」
- **分析 `data/*.json` 前必須先同步遠端**（2026-07-27）：`data/*.json`
  由排程每 30 分鐘更新並推送。本機工作目錄極易落後數百個 commit，
  直接讀取會分析到歷史切片。任何以 `data/*.json` 為輸入的評估、
  掃描、統計工單，執行前必須先 `git fetch` 並確認落後筆數；需要
  最新資料者須 `git pull --ff-only`。2026-07-27 曾因本機落後 207
  個 commit，誤判「排程停擺 3.5 天」，實際排程全程正常（每 30
  分鐘一筆快照、GitHub Actions 連續 success）。判斷排程健康須以
  `origin/master` 或 `gh run list` 為準，`stat` 的 mtime 與本機
  `git log` 皆為本機視角，不可作為依據
- **archive.json 容量現況與縮小成因**（2026-07-27）：實測 29 MB、
  70,439 筆，`published_at` 範圍 2015-12-11 ～ 2026-07-27。相較
  07-21 的 52.5 MB 大幅縮小，已退回 GitHub 50 MB 軟上限之下。成因
  查證：07-23 至 07-27 退場 20,358 筆唯一 URL，其中 94% 集中於
  TopHub（9,348）／Buzzing（5,091）／Info Flow（2,279）／
  TechURLs（799）／NewsNow（479）等**已於先前來源整頓移除、不在
  現行 6 個啟用 fetch 任務內**的來源。屬已移除來源歷史積壓的一次性
  退場，非穩態衰減，證實 07-21「淨縮小疑為初始積壓退場」之假設。
  原訂 ~2026-08-04 之容量複測降級為「確認積壓退完後檔案是否止跌
  回穩」，不再視為風險項目
- **已移除來源的歷史積壓污染語料分析**（2026-07-27）：archive.json
  保留已移除來源的歷史條目直至其自然退場。2026-07 期間語料中約 2
  萬筆來自已停用來源，任何以 archive.json 為基礎的規則校準或噪音
  分析，若未過濾來源，會對**再也不會出現的噪音**進行最佳化。後續
  同類分析工單須明列來源過濾條件
  - **六類上線規則之污染影響：已診斷結案（2026-07-27），不做任何
    規則修改。** 依 `.claude-reports/2026-07-27-six-category-corpus-audit.md`
    與 `.claude-reports/2026-07-27-benchmark-gate-output-audit.md`：
    - 六類規則主體（五類共 169 個關鍵字，commit `bf2d47a`）為人工
      編訂，無語料依據，無暴露面
    - 後續三次語料驅動調整（`ab1e088`／`595bb13`／`1b08987`）之用途
      為「發現失效案例」而非「擬合參數」，與 infrastructure 第七類
      的統計擬合性質不同，過擬合風險不可類比
    - 輸出端實測：四條排除規則／共現閘門在現行 6 源 3,004 筆樣本上
      合計僅作用 4 次（0.13%），其中 3 次攔阻正確、1 次為 market
      軸誤殺但已由 earnings 接住。作用面過小，不足以承載有意義的
      偏誤
    - 結論：污染事實成立，但對六類的實質影響為可忽略，**不重新
      校準、不修改規則**
  - **休眠規則登記（0 觸發，保留不移除）**：
    `BUSINESS_EVENT_EXCLUDE_KEYWORDS["security"]`（駭客馬拉松等 5
    詞）與 `BUSINESS_EVENT_EXCLUDE_KEYWORDS["benchmark"]`（遊戲等 4
    詞）在現行來源上觸發次數為 0。判定為休眠而非失效——詞條語意
    自足，未來新增來源若產出該類內容即刻生效。保留成本趨近於零，
    不移除
- **21 天保留窗口對現役來源的實際行為（2026-07-27 實測）**：保留邏輯
  以 `last_seen_at` 而非 `published_at` 為準。現役來源若在其索引頁／RSS
  持續列出舊文，該條目的 `last_seen_at` 會反覆刷新，使條目留存時間
  遠超過 21 天。實測現行 6 源共 3,015 筆中，`published_at` 超過 21 天
  者 385 筆（12.77%），集中於 official_ai（324 筆），最舊者發佈於
  2026-04-06。判定為**已知行為，不修正**：留存量上限由來源索引頁
  大小決定，非無限膨脹；`archive.json` 為去重與歷史存底，展示層另走
  `data/latest-24h.json`，舊條目不會外洩至使用者可見範圍。對比：
  已移除來源因 `last_seen_at` 凍結，會準時於 21 天後整批退場（見下方
  「archive.json 容量現況」條目）
- **無人值守失效模式（2026-07-27 盤點）**：
  - 通知機制為零——無 status badge、無自動開 issue、無 webhook。
    workflow 內的 `::warning::`／`::error::` annotation 僅顯示於該次
    run 的日誌頁，不會主動推送
  - 單一來源抓取失敗為靜默跳過（`scripts/update_news.py`
    `collect_all()` 的 per-source `try/except`），不會導致 job 失敗。
    來源健康須主動查 `data/source-status.json` 或前端進階層
  - `watchdog.yml` 每小時觸發，可涵蓋排程掉線，但無法涵蓋
    「job 成功但資料劣化」
  - GitHub 對無活動 repo 會靜默停用排程 workflow（60 天）。本 repo
    的快照 commit 由 `github-actions[bot]` 每 30 分鐘推上 default
    branch，推定可持續重置計時器，但未經實證。**失效徵狀為網站資料
    停在某一天不再更新；恢復方式為 `gh workflow enable` 後推任一
    commit。**
- **`primary_item.site_id` 欄位遺漏修復（2026-07-27）**：
  `build_story_record()` 的 `primary_item` 輸出字典原未列入 `site_id`
  鍵（同函式內 `story_reasons()`／`story_category()` 皆能正常讀取
  `primary.get("site_id")`，證實為純欄位遺漏而非資料不可得）。
  - 影響範圍：`assets/app.js` 的 `storyCandidateSiteId()` 恆讀到
    `null`，導致兩項機制在故事池路徑上自始未生效——
    (a) `featuredCandidatesGate()` 的社群來源補位排除；
    (b) `applyFeaturedSourceDiversityCap()` 的來源多樣性上限 N=2
    （2026-07-23 合併，**自合併起即為無效狀態**）
  - 修復前實測（2026-07-27 快照）：重點訊號區前 10 名中前 4 席
    皆為 aibase，預設 Top 3 全數同源
  - 修復後模擬：故事集合不變（0 新增、0 移除），僅排序調整，
    前 5 席內 aibase 由 4 席收斂至 2 席，符合 N=2 設計目標
  - **預期附帶效果（非回歸）**：徽章故事少於 10 則的日子，aibase
    無徽章故事將被排除於補位之外，重點訊號區可能較先前為短。
    此為設計預期，依北極星原則不得以「條數不足」為由回調。
- **infrastructure 第七類規則：整條退場（2026-07-27 裁決，非待辦、
  非未結項目）**。V5/V6/V7 三輪校準與驗證歷史見下方三項退場依據：
  1. **樣本可行性**：全量命中率僅 0.43%，新資料累積速率約 0.4
     筆／日，欲湊足 60 筆獨立留出樣本需 120 天以上；既有語料的
     獨立樣本池已被前四輪抽樣（calib100／holdout98／C1／C2）抽乾，
     此後任何驗證設計都無足夠新樣本可用，非可透過調整方法論解決
  2. **精準度逐輪惡化**：V6 holdout 67.35% → V7 C1（擴張型時間
     留出）51.67%／C2（收縮型專屬池）46.88%，且 C1 44.8% 的誤判
     可溯源至 V6 上一輪修正動作本身（英文動作動詞＋裸詞主體擴大
     後的副作用），判定為**過擬合**而非單輪實作瑕疵，換人重做或
     換方法論皆無法迴避同一結構性問題
  3. **產品價值不成立**：日均約 0.4 則的類別規模，不足以支撐獨立
     徽章與獨立篩選軸這類使用者可感知的呈現層投資
  - V5/V6/V7 全部評估報告（`.claude-reports/2026-07-21-infrastructure-*`
    與 `.claude-reports/2026-07-27-infrastructure-v7-structural.md`
    等）保留作為歷史紀錄，不進版控、不再更新
  - 前一輪「須在同步後語料上重做」之裁決，**就第七類而言隨本次
    退場裁決一併取消**——不再有下一輪重做

## 通用評估規範

適用於未來任何規則驗證，不限 infrastructure 第七類：

- **精準度門檻一律 85%。** 門檻調整僅得在無待決候選規則的時點提出，
  且理由須獨立於任何特定規則；不得於某規則未達標後向下調整
- **評估樣本分母限定「評估執行當下啟用中的來源」**，名冊須於執行
  時凍結並記錄於報告。評估期間若有來源退場，樣本重算，不得事後
  剔除。反向舉證中但尚未裁決的來源納入分母，但須在報告中分層
  列出其貢獻筆數
- **來源盤點須以「fetch 函式實際產出的 entry」為準，不得只列舉
  設定檔 tuple。** 已知 tuple 之外仍有來源路徑：`official_ai` 除
  `OFFICIAL_AI_FEEDS` tuple 外，`fetch_official_ai_updates()` 另
  硬編爬取 `anthropic.com/news`（`parse_anthropic_news_items()`）
  與 `developers.openai.com/codex/changelog`；另有 `--rss-opml`
  CLI 參數指向的外部使用者 OPML 檔案（不進版控，內容無法從
  repo 檢查）。僅讀 tuple 定義會漏算這些來源，盤點/去重/缺口
  判斷前須先確認涵蓋範圍

## 待辦檢查點
- **容量觀測更新（2026-10-01，本地 O06）**：archive.json 為
  5,679,506 bytes／8,639 筆，title-zh-cache.json 為
  7,352,921 bytes／37,441 筆。以下 29MB、4.4MB 與退場日期是歷史
  觀測，不代表目前容量；現有跨日期樣本不足以確定穩態成長速率，
  尚不啟動 prune 或調整容量門檻。
- archive.json 容量治理【已降級，非最高優先】：現況已降至 29MB
  （2026-07-27 實測，見「已知設計事實」章節「archive.json 容量現況
  與縮小成因」），退回 GitHub 50MB 軟上限之下。原 52-53MB、逼近軟
  上限的風險已隨已移除來源（TopHub／Buzzing／Info Flow／TechURLs／
  NewsNow 等）的歷史積壓一次性退場而解除，證實 07-21「淨縮小疑為
  初始積壓退場」之假設為真、非穩態衰減。**原訂 ~2026-08-04 之複測
  範圍縮小為「確認積壓退完後檔案是否止跌回穩」，不再視為風險項目
  或治理行動項**；若複測發現止跌後仍持續成長，才需重新升級處理。
  title-zh-cache.json 為第二個成長型檔案（無 prune 機制，目前約
  4.4MB，成長速率低但零治理，長期仍列待辦）。已移除來源（12 源）
  將分兩批整批自然退場：10 源（tophub／buzzing／aihot／newsnow／
  zeli／aibreakfast／aihubtoday／followbuilders／bestblogs／
  hackernews）**2026-08-04**、iris／techurls **2026-08-11**，屆時
  全庫由 69,446 筆降至約 3,000 筆量級，容量問題自我解決，本項
  降級為觀察
- **PAT 替換完成（2026-10-01，使用者回報）**：外部心跳新
  fine-grained PAT **無到期日**；cron-job.org 驗證 **HTTP 204**，
  舊 token 已刪除。原約 2026-10-17 的期限屬於舊 token，不再列為
  現行待辦。`docs/OPERATIONS.md`「External heartbeat」仍建議 90 天
  效期；本次如實記錄使用者設定，不變更續期政策或擴大權限。
- 財經查詢擴充（GNews AI 概念股+財報詞）【已否決，僅待 8 月中複評】：
  **否決關閉**——重點訊號區已於資格閘門上線時選定「寧缺勿濫」為取捨
  （供給不足寧可顯示較少條數，不擴大信源換取湊數），供給面擴張的
  迫切性降低；查詢詞組設計與三廠 GitHub Releases 評估已完成唯讀
  評估（結論：三廠 Releases 皆不足以填補官方一手空缺），changelog
  缺口改在 8 月中複評時視情況升值重提，不在本輪動作
- 一般列表徽章渲染＋事件篩選軸（六類）【可隨時開工，無到期壓力】——
  待開工，無前置依賴

## 7/21 覆核結案記錄（四源審判 + 排程健康，已裁決）

**四源審判判決**（7/17-7/21 全期唯讀取證，從 `data/archive.json`
以現行 `score_ai_relevance()`/`business_event_score()` 重算，因
archive 不保留衍生欄位；四源 fetch 階段皆無 `summary`，重算與正式
產線等價）：

- **iris（Info Flow）：砍**。窗口內 3536 筆新進項目，AI 相關真事件率
  僅約 0.65%（`business_event_score()` 不檢查 `ai_is_related`，原始
  關鍵字命中率 4.33% 中八成以上是非 AI 假陽性）；過 0.65 閘門的
  398 筆中 99.5%（396 筆）精準卡在地板值；v2ex.com 排除後裸露規模
  仍佔 fetch 總量 19.5%；全期僅 2 次真正遇到更高階源競爭且兩戰皆敗
  （tier 排序機制下結構性必輸），**0 次有意義的 primary_item 晉升**
- **techurls：砍**。990 筆新進項目，AI 相關真事件率約 1.11%（原始
  命中率 5.66% 同樣多為非 AI 假陽性，如 Samsung 裁員、Apple Music
  漲價被誤標 earnings/pricing）；60.6% 為瀰漫性非 AI 噪音，規則修
  不動。反向舉證：9 筆獨占真事件中有 6 筆為有意義訊號（HuggingFace
  資安事件 ×2、TSMC 財報、Meta AI bot 流量分析、Z.ai ARR 里程碑、
  Kimi K3 發布），但良率僅 ~0.6%（990 筆中僅 6 筆），**反向證據存在
  但強度不足以推翻預設砍**
- **36Kr AI：留**（因 iris 移除而升值）。OpenCC s2twp 轉繁驗證
  0 殘留簡體字元，fetch 端關鍵字前置過濾使命中 100% 為真 AI 事件、
  0 假陽性，明顯優於 iris/techurls 的訊噪結構。唯窗口內 4 筆命中
  100% 與 iris 重複、0 筆獨占——**這是 iris 仍在架上時的舊局面**；
  iris 移除後 36Kr 不再有更高量級同溫層源分食同一批中國科技新聞，
  其邊際覆蓋價值因果性提升，此為留下的關鍵理由，非其自身訊號
  結構改變
- **xAI/Grok 查詢詞：留，維持不動**。窗口內僅 4 筆新進（樣本過小
  無法穩定量化命中率），但全庫 21 天保留窗（29 筆）人工複查顯示
  查詢詞組精準、無過寬噪音案例

**排程健康三層架構**：全期複測通過，watchdog 由「傾向留」升級為
「確認留」（8 次代觸發 7/8 成功，唯一失敗即已知 `-R` 缺漏事件本身，
修復後 7/7 連續成功）；前端警示帶 6 小時明顯樣式全期 0 次觸發、
2-6 小時低調樣式 6 次且全數發生於心跳上線前，銜接驗證通過；內部
cron 頻率裁決維持 4 tick/hr 不降頻（見上方「已知設計事實」）。此議程
**全數關閉**，不需再排入下一輪待辦。

**個資案結案**（2026-07-27）：桌面兩份 bundle 已銷毀完成，全案結案，
不再列入待辦追蹤。

## 8/4 Claude Code Releases 來源汰除裁決（已裁決）

**裁決：移除 `CURATED_AI_MEDIA_FEEDS` 中的 `Claude Code Releases`
（`github.com/anthropics/claude-code/releases.atom`），tuple 由
15 條降為 14 條。這是**來源汰除**，不是「分類欄位修正」——曾提出
的替代方案（把它搬到 `OFFICIAL_AI_FEEDS`、改標官方分類）已被否決：
該 feed 每筆 entry 的 title 一律是純版本號（如 `v2.1.220`），不落
入六類商業事件任一類（財報/市佔/資安漏洞/價格/benchmark/模型
發布），留在架上無論標哪個分類都只會是噪音，直接下架比改分類更
乾淨。`data/archive.json` 中既有的歷史紀錄維持原值不動，不刪除、
不改寫、不回填；實際筆數以執行當下的 tracked snapshot 為準，不以本
裁決文件固定一個會隨 retention 變動的 point-in-time 數字。

**Anthropic 官方一手內容無缺口**：`official_ai` fetch task 除
`OFFICIAL_AI_FEEDS` tuple 外，`fetch_official_ai_updates()` 另外
硬編爬取 `https://www.anthropic.com/news`
（`parse_anthropic_news_items()`，賦值 `site_id="official_ai"`、
`source="Anthropic News"`），本來就持續涵蓋 Anthropic 公司公告/
產品發布層級的官方一手內容，與被移除的 CLI 版本號 changelog 屬
不同性質、不互相替代，此次移除**不產生**官方一手來源缺口。

## 已知限制
- Meta AI / DeepSeek / xAI 為第三方報導非官方一手（2026-07-19/20
  已評估 GitHub Releases 作為升級路徑：三廠皆不足——Meta/DeepSeek
  幾乎不用 Releases 機制發布模型，xAI 的 xai-sdk-python 雖活躍但
  屬 SDK 版本紀錄非模型公告，維持現狀）
- Artificial Analysis 未接入（每月手動看 leaderboard；已評估
  changelog 頁面可靜態抓取，成本中等，暫不實作）
- 繁簡混排標題理論上可能疊字（極罕見，觀察中）

## 8/21 Market Sensor 與額度政策速報（已實作，待排程樣本觀察）

- 新增 `scripts/market_sensors.py`，沿用既有排程與靜態 JSON 發布，不新增
  server、database、workflow 或 secret。
- 價格與免費額度使用獨立 state 做 deterministic old/new diff；首次執行
  只建 baseline。上游縮水超過安全門檻時不覆蓋前次 state。
- Usage policy 只監控 Usage4Claude 與 Claude Usage Monitor 公開 commit
  Atom；強詞命中才建立 `USAGE_POLICY_CANDIDATE`，不執行第三方工具，
  不接觸個人 quota 或登入狀態。
- 產品排序採雙軸：長期影響 1（價格）> 2（免費額度）> 3（usage policy）；
  時效則 3 >> 2 > 1。首頁因此把第 3 類放在獨立速報區，但所有卡片仍
  明示「待確認」。
- 前端新增「額度與政策速報」及「價格與免費額度變更」兩區；沒有事件時
  隱藏，不影響既有今日重點訊號與一般列表。
- 讀者可見的 market signal（價格、免費額度、usage policy 候選）一律只
  保留 24 小時，與主新聞及 LLM 發布雷達統一；獨立 sensor state 保留作
  old/new 比對，不會讓舊事件重回首頁。
- 後續驗收重點是 14 天候選 precision、官方確認延遲、重複率與漏報；
  未完成觀察前不擴到 issue／PR、大型 scraper 或 changedetection.io。

## 8/22 LLM 發布雷達（已實作，待排程樣本觀察）

- `data/llm-radar.json` 只保留 24 小時內的 `model_release`；價格與
  free-tier diff 全部只在既有「價格與免費額度變更」區呈現，避免雙重卡片。
- 模型證據標示嚴格分級：`official_ai` 為「官方公告」、`llm_stats_models`
  為「模型追蹤」、其餘來源一律為「媒體報導」。不更動全域評分或把媒體報導
  升級成官方確認。
- 此 lane 與七日模型分頁不同：前者強調首次可見的即時提醒，後者保留
  LLM Stats 的 atomic discovery 歷史。後續觀察模型卡 precision、重複率與
  官方來源確認延遲，再決定是否建立更嚴格的 canonical model key。
- 8/22 首次樣本發現 Free LLM APIs 一次目錄異動產生 19 筆訊號，其中
  `Retired — the model catalog is gone` 等說明文字被當作模型名稱。這批
  free-tier 結果不可視為可靠變更；需另開資料品質修正（欄位驗證與目錄
  大幅 churn gate），不可在 UI 排版調整中靜默掩蓋。
