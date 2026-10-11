# C08-P：日報專用Google Cloud專案建立核對

## 2026-10-12 最新狀態

使用者已確認專案ai-news-radar-daily/636810668699、Drive/Docs API啟用、External/Testing及本人test user、drive.file-only scopes，並下載電腦版應用程式client。真桌面授權、新app私人合成保存、connector讀回與iPhone校稿驗收完成；以下控制台建立未知是歷史紀錄。商業與私人帳號隔離，不能依既有登入猜用途。2026-10-12已補公開工具說明／品牌設定，Audience顯示實際運作中；同一client正式重新授權完成且既有GitHub憑證Secret更新。後續入口見 [Drive交付操作](DIGEST_GOOGLE_DRIVE_DELIVERY.md) 及HANDOVER。

日期：2026-10-11。使用者選擇建立日報專用專案，已授權這項工作；不再詢問沿用／新建。
**狀態：建立表單已提交，建立成功尚未核對。**

## 本輪操作與證據

- 目前沒有本機gcloud或Google Cloud connector，使用已登入的Google Cloud控制台。
- 新專案名稱填為 `AI News Radar Daily`，父項資源「無組織」，沒有選取或連結帳單。
- 初次填值／提交遇表單欄位錯誤；改用正常鍵盤輸入並移開焦點，表單顯示候選project ID後再次提交，頁面跳到creatingProject狀態。
- 沒有成功通知或可用專案資料；近期專案及通知載入失敗。資源選擇器搜尋本次候選ID也顯示載入資源錯誤。
- 直接開啟候選專案核對頁仍「無法載入」，使用頁面重試一次後同樣失敗。此畫面不能證明專案不存在、被拒絕或已成功；根因未確認，不把「可能瀏覽器或網路」當成確切診斷。

過程狀態與畫面保存於 `/Users/lordmi/Downloads/ai-news-radar-google-project-20261011/`：
`attempt-result.json`、`cloud-console-error.jpg`及`HANDOFF.md`。私人帳號資訊不寫正式文件，候選ID只留過程證據；正式配置仍未填值。

## 精確下一步

請使用者在iPhone開啟 [Google Cloud控制台](https://console.cloud.google.com/)，按「選取專案」，搜尋 `AI News Radar Daily`。

- 看得到：回報實際project ID，接續核對專案並準備Drive/Docs API與OAuth。
- 搜尋可正常完成但看不到：才確認尚未建立，再使用 [新增專案頁](https://console.cloud.google.com/projectcreate) 建立同名專案；保留Google實際產生的ID，不要求與本輪候選完全一樣。
- 手機也載入失敗：回報失敗畫面狀態，保留未知結果；不持續點建立、不刪專案或改安全／網路設定。

Google的 [專案建立說明](https://docs.cloud.google.com/resource-manager/docs/creating-managing-projects) 與
[控制台載入問題說明](https://docs.cloud.google.com/support/docs/troubleshoot-console-page-loading) 僅作操作參考；它們不是本專案建立成功的證據。

## 範圍與後續

只有取得實際可用專案後才進API/client設定；本輪沒有啟用API、建立OAuth client、下載憑證、設定GitHub secret、連結付費、改workflow或啟每日排程。若後續瀏覽器需要新增敏感授權／接受服務條款，按當時畫面提出具體確認，不能用本次選型涵蓋未知條款或權限。

程式未變更，不為控制台問題重跑已有1007項本機測試；該數字仍是C08-O歷史基線。沒有做Git/來源SHA查驗。
本輪只更新決策與未知結果交接，原OAuth helper及Google Drive試用文件保持。接線沿用Sol／High；涉及新身份或交付交易裁決再用Astra／High。
