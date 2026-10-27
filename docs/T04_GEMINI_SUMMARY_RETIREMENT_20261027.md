# T04 Gemini 新聞摘要備援退役裁決（2026-10-27）

維護者裁決：刪除 Gemini 新聞摘要備援設計，不再建議未來重複測試；
僅保留已設計的通用串接機制，供另外明確指定的新用途使用。T04 結案。

## 已移除

- Groq 失敗轉送 Gemini 的候選邏輯、相關設定參數與備援快取路徑。
- Gemini 新聞摘要 provider、合成摘要專用執行器及其測試入口。
- T04 合成摘要 workflow、deadline watchdog、站外心跳 dispatch hook。
- 正式接線 gates、未來重測／啟用／再觀察建議與待辦。

原 GitHub T04 workflows 已停用；本地一次性自動化先前已刪除。
舊研究與實測證據留在 Git／Actions 歷史，不作為自動重啟本案的依據。

## 僅保留的通用機制

- `scripts/gemini_api.py`：caller 指定 prompt、JSON schema、輸出 token 與 timeout 的 API 介面。
- `scripts/diagnose_gemini.py`：合成連線與 structured JSON 的手動分層診斷。
- `scripts/provider_diagnostics.py`：安全錯誤分類與密鑰遮罩。
- `scripts/workflow_result_email.py` 與既有 SMTP adapter：可明確配置的其他工作結果通知與收據。

以上均為休眠工具，沒有預設排程、新聞摘要用途或自動呼叫。
只有維護者另行指定新的用途時才能使用；不主動再提出 T04 重測、接線或啟用建議。
現有 Gemini 讀者翻譯繼續依既有操作規則維護。

## 移除驗證

預設分支退役版本完整套件 2,351 項通過；原候選分支移除後 2,350 項通過。
語法、workflow lint 與差異檢查通過。以上均為離線軟體驗證，未重新呼叫
Gemini 模型、未發送測試郵件，也未修改讀者翻譯的 provider 接線。
