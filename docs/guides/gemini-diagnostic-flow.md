# Gemini API 獨立複測流程

## 事件邊界

本流程只診斷 Gemini API 為何無法呼叫，使用合成文字，不讀取或送出
`data/*.json`、真實 RSS 內容或文章內容。它不接入排程、不啟用 fallback，
也不修改 Groq 作為 production AI 摘要預設 provider 的決定。

Gemini 測試結果只能回答 Gemini 本身在本次時間點是否可用；不得用來推翻、
替代或轉移 Groq 的 production 驗證結果。

截至 2026-08-17 的 repo 裁決是
`qualified backup candidate, disabled by default`。一次 diagnostic 成功不等於
已核准 production fallback；完整準入條件與成本／資料政策見
[`docs/OPERATIONS.md`](../OPERATIONS.md#gemini-backup-candidate--disabled-by-default)。

## 前置條件

- 使用 repo 自己的 Python 3.11+ `.venv`，不要借用其他專案的 venv：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

- 從 Google AI Studio 取得測試用 Gemini API key。
- 不要把 key 寫入 `.env`、command argument、JSON report、GitHub Issue 或 repo。
- 在目前 shell 暫時設定：

```bash
export GEMINI_API_KEY='貼上測試用 key'
```

若要測特定模型，可另外設定；未設定時使用 `gemini-3.5-flash-lite`：

```bash
export GEMINI_SUMMARY_MODEL='gemini-3.5-flash-lite'
```

## 第一階段：API 分層診斷

```bash
python scripts/diagnose_gemini.py \
  --output /tmp/ai-news-radar-gemini-diagnostic.json
```

此命令依序執行並在首個失敗點停止：

1. `configuration`：只確認 `GEMINI_API_KEY` 非空，不輸出 key。
2. `model_discovery`：呼叫 `v1beta/models.list`，確認指定模型存在且宣告支援
   `generateContent`。
3. `plain_generation`：送出最小合成文字請求，隔離 key、權限、配額與模型問題。
4. `structured_generation`：再測 production/eval 所需的
   `responseMimeType=application/json` 與 `responseSchema`。

Exit code：`0` 表示四層通過；`1` 表示已送出請求且診斷到失敗；`2` 表示
本機缺少 `GEMINI_API_KEY`，因此沒有發出網路請求。

報告中的 `diagnosis.code` 是主要判讀欄位：

| code | 判讀 |
| --- | --- |
| `missing_api_key` | 執行環境沒有 key，尚不能判斷遠端 API 狀態 |
| `invalid_api_key` | key 被 Google 拒絕 |
| `api_not_enabled` | key 所屬專案未啟用 Generative Language API |
| `permission_or_region_denied` | key restrictions、專案權限、billing 或區域限制 |
| `quota_or_rate_limit` | RPM、TPM、每日額度或 spend limit 已滿 |
| `model_not_found` | 模型不存在、退役或不對該 key 開放 |
| `structured_output_incompatible` | plain call 可用，只有 JSON schema 設定失敗 |
| `transient_or_transport_failure` | 網路、timeout 或 Gemini 5xx 暫時失敗 |
| `gemini_api_usable` | key、模型、plain 與 structured call 本次均通過 |

`429`/`5xx` 可保留報告後稍晚重測；`400`/`403` 應先修正 key、請求、權限、
billing 或區域設定，不要用密集 retry 掩蓋根因。

## 第二階段：Gemini-only 合成摘要評估

只有第一階段 exit `0` 才執行：

```bash
python scripts/evaluate_ai_summaries.py \
  --providers gemini \
  --require-live \
  --output /tmp/ai-news-radar-gemini-eval.json
```

這一階段只送出 `tests/fixtures/ai_summary_cases.json` 的合成案例，用來判斷摘要
格式、繁中長度、必要數字保留與提示注入防護。它不是 production 切換測試，
也不讀取新聞 snapshot。

## 證據與停止條件

每次複測保留兩個 `/tmp` JSON 檔及執行時間，但不要提交 repo：

- `ai-news-radar-gemini-diagnostic.json`
- `ai-news-radar-gemini-eval.json`（僅第一階段通過時產生）

遇到以下任一情況即停止，不繼續跑完整案例：

- key 缺失或無效
- model discovery 失敗或指定模型不可用
- permission、billing、region 或 quota 錯誤
- plain generation 失敗
- structured generation 失敗

完成後清除目前 shell 的 key：

```bash
unset GEMINI_API_KEY
```

## 官方判讀依據

- [Models API](https://ai.google.dev/api/models)：`models.list` 與
  `supportedGenerationMethods`。
- [GenerateContent API errors](https://ai.google.dev/gemini-api/docs/generate-content/api-errors)：
  `API_KEY_INVALID`、`PERMISSION_DENIED`、`NOT_FOUND`、
  `RESOURCE_EXHAUSTED` 等錯誤語意。
- [Gemini API troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting)：
  只對 `429`、timeout 與 `5xx` 等暫時性錯誤做 bounded retry；不要重試
  `400`/`403` 來掩蓋設定問題。
