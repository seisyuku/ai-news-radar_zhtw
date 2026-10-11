# GitHub → 私人 Google Drive：單人手動交付

更新：2026-10-12。使用者已批准 [簡化交付標準](DIGEST_CLOUD_CONTRACT.md)，不新增交易控制服務。

實測結果：GitHub [38157491285](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/38157491285)手動historical+deliver_drive成功，runner私人保存/readback、pair/rerun核對完成，沒有公開artifact。這是06:00截止前的歷史驗證，0題review-only，不是有效當期日報。現有Offline tests亦成功，無新排程。最新停點為Google授權正式狀態及新授權，不再重問Drive選型或重測iPhone。

## 操作入口

Actions → **Daily digest generation check** → Run workflow：填明確臺北期別；舊資料補驗勾historical；需要私人保存時勾deliver_drive（預設false）。固定前日06:00～當日06:00，不推測日期、不新增來源刷新或LLM呼叫。

GitHub Secrets：

- `GOOGLE_DRIVE_OAUTH_CREDENTIALS`：desktop授權產出的私人JSON（client_id/client_secret/refresh_token/scope/token_type）。
- `GOOGLE_DRIVE_DIGEST_TARGET`：JSON含app有權操作的`folder_id`與`settings_id`。真值只放Secrets與Downloads，不寫repo、公開log或Step Summary。

credentials Secret使用compact單行JSON，避免GitHub把多行Secret中單獨括號也自動遮罩而污染安全摘要；沒有把憑證加入日誌。真正的私人目的地與本機試稿分開，原設定Doc沿用，其狀態已更新為GitHub手動交付驗證完成。

只讀已選定私人設定Doc：schema_version=1、timezone=Asia/Taipei、cutoff=06:00、generation_location=github-actions、automation_enabled=false；其餘只允許mode/trial_status等既有欄位。未知欄位/改窗口/要求其他生成服務拒絕。改設定不是排程啟用指令。

## 保存及重送

每一期/mode一個資料夾，appProperties記既有base identity。保存原始MD/meta，下載讀回沿用pair核對；另外產生native TITLE/HEADING_1/HEADING_2及原文超連結的可讀原稿，再native copy作校稿副本。identity控制碼只在原始pair，不出現在閱讀畫面。

重送相同base只讀既有檔案，保留人工校稿；不同base停止，不換稿。原稿已被手動修改或部分native建立後寫入失敗，停止並保留現況，不自動覆寫或清除。原始pair部分上傳可以透過既有名稱及bytes核對續接；没有跨檔原子交易保證。

owner可手動改Drive文件。這是程序不覆寫規則，不宣稱儲存層不可變或C02 v1完整交易成立。

## 狀態與隱私

公開摘要只含日期、生成狀態、題數、既有pair/rerun、delivery_verified、保存觀測時間/storage_quality/storage_reason/storage_timeliness；不含稿件內容、題目、私人URLs/IDs/路徑或原始例外。完整入口及file IDs存在runner的0600 private-delivery.json，收尾連同私人pair清除；不upload artifact或commit稿件。手機從私人Drive/ChatGPT connector讀取。

delivery_verified代表私人保存與內容核對，資料陳舊/遲到仍不算每日達標。當期資料不足仍exit3；明確historical且保存成功可exit0，摘要仍review-only/historical，這是歷史保存驗證，不是有效當日日報。

OAuth External/Testing的refresh token有7天期限，這輪可做短期手動接線；正式每日排程前需要處理app正式狀態及重新授權。没有啟新schedule、分享、通知、Pages、Cloudflare或新帳號。真GitHub執行結果與下一停點以HANDOVER為準。
