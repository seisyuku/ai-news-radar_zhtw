# AI News Radar Pulse 設定參考

適用範圍：`scripts/update_news.py`、`.github/workflows/update-news.yml`。

本文件只記錄穩定的設定介面，不綁定容易漂移的程式行號、來源數量或
第三方費率。常數的現行預設值以程式碼為準；排程參數以 workflow 為準；
營運與事故處理以 [`OPERATIONS.md`](OPERATIONS.md) 為準。

## 公開預設

- GitHub Actions 每 30 分鐘嘗試更新一次。
- 所有讀者可見頁面使用 24 小時資料窗；archive 與去重快取可保留較久，僅供內部比對。
- 沒有任何付費服務憑證時，官方來源、媒體來源與公開 OPML 範例仍可運作。
- `feeds/follow.opml` 是私人檔案，不進版控；公開範本是
  `feeds/follow.example.opml`。

## GitHub Secrets

只在實際啟用相應整合時設定：

| Secret | 用途 |
| --- | --- |
| `FOLLOW_OPML_B64` | 以私人 OPML 覆蓋公開範例 |
| `GROQ_API_KEY` | 選用的重點新聞 AI 短摘要；預設模型為 `qwen/qwen3.8-27b` |

Secret 值不得寫入 repo、Issue、log、截圖或驗收報告。

## 社群來源退役

X API、SocialData及TikHub已從master移除並正式發布；舊憑證、啟用與強制執行變數不再接線，不會啟動收件。憑證本身不由程式清理操作。發布證據見任務台帳。

## AI 摘要 Variables

- `GROQ_SUMMARY_MODEL`：預設 `qwen/qwen3.8-27b`。
- `GROQ_SUMMARY_MAX_NEW`：每輪最多新增摘要數，預設 `6`；快取命中不計入。

AI 摘要沒有 `ENABLED` 開關；是否啟用由 `GROQ_API_KEY` 是否存在決定。
沒有 key 或 provider 失效時，資料管線仍會正常完成。

### Gemini 手動串接（不含新聞摘要備援）

- `GEMINI_API_KEY`：既有讀者翻譯使用；通用手動工具只有在另外明確指定新用途時才讀取。
- `GEMINI_MODEL`：手動 `diagnose_gemini.py` 的可選模型名稱，預設 `gemini-3.5-flash-lite`。
- 通用 `generate_json` 由呼叫端明確傳入 schema、輸出上限及憑證。

T04 新聞摘要備援已刪除並結案，沒有摘要專用 Gemini 變數、provider 或自動重測。
其他用途的串接與通知參數見[保留工具說明](guides/gemini-diagnostic-flow.md)。

## 程式內常數

新聞時間窗與重點排序參數以`scripts/update_news.py`及相關評分模組為準。資安主題／事件的共用判定由`scripts/security_topics.py`維護，不使用付費API或額外模型呼叫。

## 重點訊號池

`data/daily-brief.json` 是全站共用的精選故事池。入選與排序由
`story_passes_brief_gate()`、`calculate_item_importance()` 及 `BRIEF_*`
常數控制。產品原則是「寧缺勿濫」，不可只為填滿版位而降低門檻。

合法空結果的原因記在 `selection_diagnostics`，包括候選數、符合門檻數、
未達門檻數、最高分與來源數；`empty_reason` 區分 `no_candidates`、
`below_brief_gate`、`diversity_or_limit`。有入選時為 null。
`source-status.json.brief_selection` 與 Actions 生成日誌同步同一組診斷。
零精選不等於沒有新聞，也不代表來源覆蓋完整。

私人日報使用獨立的 `daily-news-v2` 政策：明顯噪音先排除，產業與實用
消息共同排序，每期最多10則，不設0.72或兩來源硬門檻；不另附人工候選池。
`--limit`只能縮小第二版題數，不能超過10；公開精選門檻與全域分數不變。
同來源群組內的不同出版者報導保留供故事合併；同出版者近似轉載仍去重。
相似度、時間與模型／廠商合併限制維持原設定；私人第二版另保護明確不同談論點，
並以`current-event-v2`在當期依明確文章引用或同出版者產品摘要高度重疊去除重複名額，
保留既有選題排名較高的一則。不新增服務、環境變數或
每日人工裁決要求。離線可選`--event-citations`與metadata契約見DIGEST_USAGE。

評分公式屬高影響變更；修改前依 repo 規則取得同意並完成所需回測。

## 本機驗證

優先輸出至暫存目錄，避免覆寫排程管理的 `data/*.json`：

```bash
python -m py_compile scripts/update_news.py
python -m pytest -q
python scripts/update_news.py \
  --output-dir /tmp/ai-news-radar-data \
  --window-hours 24 \
  --rss-opml feeds/follow.opml
```

來源整合完成後檢查 `/tmp/ai-news-radar-data/source-status.json`，確認成功、
失敗、跳過原因與筆數都有明確狀態。
