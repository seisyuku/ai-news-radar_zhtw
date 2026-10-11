# C08-O：一般 Google 帳號的 GitHub → Drive 授權準備

## 目前狀態：正式授權完成（2026-10-12）

Google Audience已顯示「實際運作中」。三份既有GitHub Pages公開說明及品牌URL／授權網域已保存；同一Desktop client重新授權成功，仍只要求drive.file。新私人憑證已成功刷新並唯讀既有目的地／設定，既有GitHub憑證Secret已更新為compact JSON；舊本機憑證保留。沒有新scope、Drive分享或每日私人排程。

External/Testing固定七天期限的前提已解除；仍須遵守[Google一般token撤銷／到期條件](https://developers.google.com/identity/protocols/oauth2#expiration)，不代表永久有效。本輪沒有再次執行GitHub私人交付；已完成的歷史交付與待啟用的每日流程見 [Drive交付操作](DIGEST_GOOGLE_DRIVE_DELIVERY.md) 及HANDOVER頂部。

以下為首次桌面授權及更早device準備的歷史紀錄，Testing／未接通描述不代表目前狀態。

## 2026-10-12 更新：採用桌面授權入口

使用者回報專案 `ai-news-radar-daily`（編號 `636810668699`）已選取、Drive/Docs API均啟用、External/Testing授權畫面已建立、自己已加入test users、scopes只有`drive.file`。這些為使用者控制台回報，沒有另作遠端控制台查驗。

使用者指出既有Console登入的是商業帳號。後續操作必須隔離帳號：桌面使用專用Chrome profile或新無痕工作階段，確認私人Drive帳號與目標專案後才授權；不能沿用現有瀏覽器登入或依名稱猜帳號用途。使用者已改桌面操作並下載Desktop app（中文「電腦版應用程式」）client JSON。只讀該指定檔案，確認installed結構、專案ID、必要憑證欄位及loopback設定，不輸出密鑰；JSON與token不放repo或對話。

修正前階段device flow選型：Google明確建議有瀏覽器的desktop/CLI採installed-app flow。既有device helper與合成測試保留為歷史候選，不再作本案正式入口。新增 `scripts/digest_drive_desktop_oauth.py`：Google固定端點、S256 PKCE、隨機state、只綁127.0.0.1隨機port、15分鐘期限；拒絕錯Host/state、重複code及錯callback path，HTTP不記錄授權code。只要求`drive.file`、offline access及帳號選擇/同意；不自動開瀏覽器，使用者須在同一Mac的隔離瀏覽器開該次網址。

Token交換要求Bearer、精確Drive-file-only scope及refresh token。access token不保存；既有0600、Downloads限定、拒絕覆寫的私人保存規則沿用。成功前不宣稱已授權；接收回應頁也只提示返回Codex查看最後結果。建立listener/接收回應不會寫入Drive、GitHub secret、啟排程或push。

2026-10-12真桌面授權完成：使用者回報接收頁後，CLI exit 0且authorized/credentials_saved；私人JSON讀回僅核對必要欄位存在、drive.file-only、Bearer、无access token及0600/0700權限，未輸出值。listener已關閉。沒有要求email/profile scope，因此未獨立驗帳號身分；下一段需新app合成文件建立/讀回/私密ACL與手機實測，GitHub交付仍未接通。

同日自動續行完成 [新app合成Drive/Docs交付試驗](DIGEST_GOOGLE_DRIVE_TRIAL.md)：refresh token實際刷新成功，三份native Docs建立/複製/修改/讀回及owner-only ACL核對，connector也能讀取。原稿保持，設定尚未執行；使用者已確認iPhone新校稿顯示「校稿保存成功」。GitHub runner私人交付及正式長期token狀態仍未接通，未加scope或改sharing。正式接線前C02控制層是否簡化的裁決見HANDOVER最新停點。

桌面入口需明確`--authorize --client-file <使用者指定私人檔案> --output-file <Downloads內新的私人credentials.json>`。私人輸入路徑及執行狀態記於Downloads交接，不把真client JSON或tokens複製進測試證據。23項新桌面合成測試加25項歷史測試共48項通過；完整測試與真授權結果見HANDOVER最新停點。

[Google桌面OAuth/PKCE/loopback說明](https://developers.google.com/identity/protocols/oauth2/native-app)。External/Testing的7天token期限仍適用，只能宣稱短期驗證；GitHub私人交付接線及正式每日排程仍待完成。

以下為2026-10-11歷史準備紀錄，其「專案未知」與device入口由本節取代。

更新：2026-10-11。使用者已用iPhone開啟原稿、校稿與設定三份文件，內容吻合；確認使用一般個人Google帳號。**本機授權helper／合成測試完成，真OAuth及GitHub寫入未接通。**

後續使用者已選擇建立日報專用Google Cloud專案；表單已提交但控制台核對持續載入失敗，專案是否成立仍未知。
最新停點為 [iPhone核對專案是否出現](DIGEST_GOOGLE_PROJECT_SETUP.md)，不再重問專案選型，也不以未確認ID建立OAuth client。

## 已選路線與顯示規則

生成仍在GitHub Actions。私人原MD/meta、native校稿與設定走Google Drive；Cloudflare延後，不改既有來源刷新或發布。

使用者回報Chat顯示檔案citation的前後控制碼。不能推定是暫時故障，後續交付一律用一般Markdown文字連結，明確標示「原稿」「校稿副本」「設定」；這項明確指示優先於Google Docs技能的output citation格式。Google Docs內文仍使用原生標題／段落，不能把回應控制碼寫進文件。

正式交付的顯示順序固定為：臺北期別 → 前日06:00～當日06:00窗口 → 生成／私人保存是否核對成功 → 題數／必要原因 → 三個可點擊入口。閱讀畫面不放API payload、revision token、憑證、本機路徑或版本SHA。只有實際保存並讀回後才提供觀測到的URL；不猜文件ID或製造待建立連結。

文字樣式示意（下列URL是格式佔位，不能原樣交付）：

```text
YYYY-MM-DD 私人日報
新聞窗口：前一天06:00至今天06:00（臺北時間）
狀態：生成已核對；私人保存尚未接通。
原稿｜校稿副本｜設定
```

不為連結顯示新增公開網頁、網站hosting或Cloudflare。2026-10-11已把手機確認／一般帳號／普通文字連結偏好寫入既有試用設定，讀回通過；automation仍false，設定尚未供runner消費。

## 手機完成一次性授權

新增 `scripts/digest_drive_oauth.py`，為headless專案CLI準備Google的device authorization。
Google支援從另一裝置登入，允許`drive.file`範圍；需要 **TVs and Limited Input devices** 類型的OAuth client。此路線不用在iPhone開Mac的127.0.0.1回呼，也不架新callback服務；它是候選接線，仍須用實際Google client驗證。
[Google device authorization](https://developers.google.com/identity/protocols/oauth2/limited-input-device)。

- 只要求`drive.file`，不要求整個Drive讀寫、Google帳號profile或服務帳號權限。新app只能操作它建立／被使用者向它選定的檔案，不能因知道connector試用文件ID便視為已授權。[Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)。
- 手機將看到Google傳回的verification URL與短碼；helper不改網址、不硬編短碼、不顯示device code/client secret/access/refresh token。
- 輪詢遵守Google interval、至少5秒；slow_down再延長，拒絕／到期就停止，整次最多30分鐘。固定Google端點、不跟隨HTTP redirect；provider原始描述不輸出。
- 只接受Drive-file-only Bearer授權並要求refresh token。access token只在記憶體作完整性檢查，不寫檔；可刷新憑證存Downloads下的新私人JSON，檔案0600，新建目錄0700，不覆寫舊憑證。
- CLI需明確`--authorize`及使用者提供client檔案才會連Google。此輪測試注入合成HTTP與clock，沒有呼叫真授權API、掃描或讀取既有私人憑證。

## 可執行入口與缺少的設定

需要使用者先決定使用哪個Google Cloud專案。下一階段才能在該專案啟用Drive/Docs API、設定OAuth app、建立所需client；本輪沒有新增Google專案、API權限或app，也沒有把它設為正式上線。

Google下載的client JSON存Downloads私人位置後，可由本機協作執行以下入口。這不是要使用者在手機打長命令或把權杖貼進對話：

```bash
python scripts/digest_drive_oauth.py --authorize \
  --client-file "$HOME/Downloads/ai-news-radar-drive/client.json" \
  --output-file "$HOME/Downloads/ai-news-radar-drive/credentials.json"
```

手機只需在該次Google網址輸入短碼、確認app名稱／權限並登入同一Google帳號。client的實際類型由Google核對；若invalid_client，不擅自加大scope或換成新hosting架構。

授權後仍需驗app自己建立的合成原稿／副本／設定，手機及Chat connector可讀、讀回和私密權限。新app的目的位置與試用文件分離或向該app選定；不能直接移用ChatGPT連線的憑證。

External/Testing且包含Drive scope的refresh token在7天到期；只能作短期合成測試，不能宣稱每日保存長期可用。正式啟用前須確認app狀態與重新授權／撤銷流程。[Google token有效條件](https://developers.google.com/identity/protocols/oauth2#expiration)。

GitHub secret規劃名稱為`GOOGLE_DRIVE_OAUTH_CREDENTIALS`，內容來自上述私人JSON；本輪沒有設定secret或改workflow。實際送稿入口、固定期別／跨工作去重及C02私人保存交易仍待實作／驗收。

## 驗證與交接

新增25項合成測試：pending/slow_down等待、期限與拒絕、錯client/範圍、惡意或格式錯誤回應、限定端點／不跟redirect、縮限授權、私人檔案權限／不覆寫及CLI不印憑證。初輪22通過，補上不合法error型別後全套 **1007 passed in 5.84s**。

設定文件是實際connector修改及讀回；真OAuth、Google app建立、GitHub dispatch、正式保存及每日排程都未做。正式文件不含私人file IDs/URLs或真憑證；沒有新增SHA清冊或遠端比對。

過程證據：`/Users/lordmi/Downloads/ai-news-radar-drive-auth-prep-20261011/`。下次先讀HANDOVER頂部與本輪HANDOFF，接Google Cloud專案選擇。例行接線建議Sol／High，交易/身份有新裁決時Astra／High。
