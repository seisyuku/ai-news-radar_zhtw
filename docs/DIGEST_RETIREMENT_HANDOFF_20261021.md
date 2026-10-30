# 私人早報功能退役與移除

2026-10-21撤回私人早報自動生成、派送與排程目標；2026-10-22已發布停用，歷史狀態見[S03](SOURCE_GOVERNANCE_S03_STATUS_20261022.md)。2026-10-30維護者進一步要求移除生成／Drive交付／雲端校稿工具、專用測試與手動雲端合約流程。

本機已移除31個模組、27份測試、3份workflow、專用依賴、18份舊操作／設計文件、3頁工具說明及1份部署範本；2026-10-31已推送master並完成CI／Pages與HTTP驗收；三個舊頁均404，私人workflow已從正式清單移除。現行進度見[TASK_LEDGER](TASK_LEDGER.md#私人早報功能移除2026-10-30)，逐階段交接位於 /Users/lordmi/Downloads/ai-news-private-digest-removal-20261030/HANDOFF.md。

公開新聞收集、橘鴉外部來源、官方純文字查漏、daily-brief、精選／本日重點訊號、24小時窗口與既有刷新保留。私人稿件、Drive資料、OAuth／secret及歷史資料不在清理範圍內；不恢復排程、不重送稿件。

本頁取代已刪除的私人操作文件，舊程式與接口只可由Git歷史查閱。保留[人工選題研究](DIGEST_EDITORIAL_HANDOFF_20261018.md)供使用者明確要求時參考，不能據此恢復自動產文。2026-10-31已核對正式workflow清單無私人早報入口；歷史artifact與私人資料保留。
