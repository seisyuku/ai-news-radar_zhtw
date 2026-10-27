# Gemini API 手動串接工具（供其他用途保留）

T04 新聞摘要備援已於 2026-10-27 刪除並結案；不再建議重測該設計。
本頁只記錄保留的通用介面，沒有摘要評估第二階段或例行驗收工作。

## 保留介面

`gemini_api.generate_json(prompt, api_key=..., schema=..., max_output_tokens=..., model=..., timeout=...)`
沿用已驗證的 `generateContent`、API key header、JSON schema 與有界 timeout。
用途、prompt、schema、輸出上限由呼叫端明確指定；不載入新聞、不自動重試、
不記錄憑證，也不建立排程。

`diagnose_gemini.py` 保留 model discovery、plain、structured JSON 的分層診斷。
只有維護者另外指定新用途需要連線診斷時才手動執行；使用環境變數
`GEMINI_API_KEY` 與可選的 `GEMINI_MODEL`，或 `--model` 明確選擇模型。
不將 key 寫入 command argument、repo、.env 或報告。

診斷只使用合成連線文字，首個失敗點即停止；成功結果只代表本次介面可用。
它不構成新用途的資料使用或正式接線授權。

## 通知介面

`workflow_result_email.py` 沿用 GitHub job／安全 JSONL 階段紀錄、TLS SMTP
及接受收據。其他工作需明確配置 `WORKFLOW_JOB_NAME`、`WORKFLOW_LABEL`、
`WORKFLOW_EVENT_LOG`、`WORKFLOW_RECEIPT_PATH` 及既有 `TW_SOURCE_EMAIL_SETTINGS`。
工具沒有任何預設 workflow 或排程呼叫；SMTP 接受仍不等於收件匣送達。

## 現行裁決

[T04退役紀錄](../T04_GEMINI_SUMMARY_RETIREMENT_20261027.md)是權威入口。
不由本頁、舊研究或暫時 API 故障重新提出摘要備援測試或恢復工作。
