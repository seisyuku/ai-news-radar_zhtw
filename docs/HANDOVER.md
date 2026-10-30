# AI News Radar 交接摘要

更新：2026-10-31（臺北）。本頁僅保留目前有效狀態與2026-10-21起的交接紀錄；超過十天的項目與歷程已從本頁移除。任務清單以[TASK_LEDGER](TASK_LEDGER.md)為準，產品／來源／操作細節分別依README、SOURCE_COVERAGE與OPERATIONS。

## 目前續接狀態

正式專案為 /Users/lordmi/Documents/ai-news-radar_zhtw，工作分支master；最近程式發布提交為 `3279606d9c36`，後續文件整理版本以master的Git紀錄為準。私人早報移除、新聞版本／品質診斷及有界官方純文字整合均已發布，沒有下一個必跑功能階段。

本輪僅整理台帳與交接文件，依維護者commit／push指示納入master。程式、來源、資料與排程維持目前版本；後續接手先核對最新master及工作目錄，再依任務範圍處理。

## 10/31 正式發布結果

- 私人早報移除 `7d5a2c4cf1ea`、新聞品質整合 `cbd1e1a5923b`、維護文件 `8edc35b31ffd`已整合master，保留遠端刷新歷史。
- 私人生成／Drive派送／雲端校稿共84個專用檔案移除，3份workflow不在正式清單，3個舊說明頁回傳404。私人稿件、Drive、OAuth／secret及歷史artifact未操作。
- 同URL版本歷史與最新閱讀投影、來源／事件／入選品質診斷、Juya有界官方文字查漏已上線。HF首段補讀與譯文、重點摘要優先、來源摘要回退及金額尺度修正保持。前端共同版本20261030-quality1。
- 首次CI缺少原由雲端套件間接安裝的jsonschema，已由 `1598a2069b88` 明確宣告測試依賴。乾淨Python3.12環境1913項通過；[GitHub離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093539300)1912項通過，1項資產比較由[獨立檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093066138)驗證。98個feedparser棄用警告為既有狀態。
- [公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093175458)由新程式產生 `cf3f601098c2`；該次臺北00:48:35快照168篇一般AI、4則重點（3核心＋1補位），14個來源正常，brief與governance皆ready。這是該次發布驗收快照，不代替下一次維護時的即時查核。
- 首頁與6份資產和發布版本位元一致，8份公開JSON和生成提交一致，資料通過讀者端guard；[最終文件Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41094003358)成功。固定輸入7504檔和已驗整合結果僅實測耗時不同；不宣稱獨立新聞precision。
- 本輪最新唯讀查核：公開刷新於臺北01:05建立的run已成功；公開刷新、watchdog、離線測試、資產檢查及Pages保持啟用，七日觀察／報告／SMTP三流程仍手動停用。

發布備份與驗證材料：/Users/lordmi/Downloads/ai-news-release-20261031/。整合階段入口：/Users/lordmi/Downloads/ai-news-quality-integration-20261030/HANDOFF.md；私人早報移除入口：/Users/lordmi/Downloads/ai-news-private-digest-removal-20261030/HANDOFF.md。這些為已完成階段證據，不是待重跑工作。

## 10/31 分支清理

本機與GitHub均已移除 `codex/featured-duplicate-fix`、`codex/featured-selection-review`、`codex/retire-canary`及 `codex/t04-gemini-summary`。前述三個功能修正已有主線等價內容；T04分支依維護者指示刪除，相關現行功能已各自整合master，不重啟摘要備援。

GitHub目前保留master及asset-version-git-baseline、copy-news-id、gemini-translation、source-health-upstream-cleanup四個codex分支；本機另有reader-summary-translation-fix、retire-gemini-summary。這些分支提交均已包含於master。Gemini翻譯舊工作目錄 /Users/lordmi/Downloads/ai-news-radar-gemini仍保留，可另行指定清理。

## 最近十天其他完成紀錄

| 日期 | 最終結果與續接邊界 |
| --- | --- |
| 10/30 | 核准保留HF首段、補位評分、Juya／官方文字追取、品質診斷與細粒度資格；已在10/31發布，不保留「只完成本機、待發布」接續步驟。 |
| 10/28 | 來源品質修正與AIBase降級已由 `aaba6389dbb0` 發布；HF／重點摘要與金額翻譯補修也已發布，不能因舊分支歷史重列為待合併。 |
| 10/27 | T04 Gemini摘要備援退役結案。通用API／手動診斷／結果通知休眠保留，現有讀者翻譯繼續；[裁決](T04_GEMINI_SUMMARY_RETIREMENT_20261027.md)。 |
| 10/26 | 翻譯快取唯讀量測結案，維持現況，不啟動觀察或預警；[結案](TRANSLATION_CACHE_T06_MEASUREMENT_20261026.md)。 |
| 10/25 | T01一般列表事件篩選已發布；T02模型生命週期與T03摘要回顧結案，T05 Canary移除結案。CyberQ／AlphaLab以官方RSS進入一般池，保留未審來源與用途限制。 |
| 10/24 | PG發布者治理與D+選稿／列表簡化正式發布並結案；不重開補修或自動啟動下一階段。 |
| 10/23 | BR同事件合併、24小時資格與前端同代資料檢查完成發布。 |
| 10/22 | 來源觀察提前停止並以方案A集中評估，A06正式發布；觀察設定false，不補七日驗收或結案信。 |
| 10/21 | 撤回私人早報自動生成／派送目標；後續已完成停用與10/31程式移除，不恢復當時接續工作。 |

## 下次接手

先讀任務台帳的目前待辦，再核對實際Git、工作目錄及來源健康。公開新聞維持24小時窗口與現行來源／用途資格；實作新的來源、評分或產品能力時，依相關權威文件另行處理。

更新本頁時以臺北日期計算十天窗口，只保留目前有效狀態、近期完成結果與必要入口，刪除超期項目和被取代的接續步驟。當前規則依權威文件維護，不藉由保留整串舊歷程傳遞。
