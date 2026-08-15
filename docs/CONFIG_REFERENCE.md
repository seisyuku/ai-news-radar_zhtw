# AI 商業情報雷達設定參考

適用範圍：`scripts/update_news.py`、`.github/workflows/update-news.yml`。

本文件只記錄穩定的設定介面，不綁定容易漂移的程式行號、來源數量或
第三方費率。常數的現行預設值以程式碼為準；排程參數以 workflow 為準；
營運與事故處理以 [`OPERATIONS.md`](OPERATIONS.md) 為準。

## 公開預設

- GitHub Actions 每 30 分鐘嘗試更新一次。
- 主要頁面使用 24 小時資料窗，archive 保留天數由 workflow 參數控制。
- 沒有任何付費服務憑證時，官方來源、媒體來源與公開 OPML 範例仍可運作。
- `feeds/follow.opml` 是私人檔案，不進版控；公開範本是
  `feeds/follow.example.opml`。

## GitHub Secrets

只在實際啟用相應整合時設定：

| Secret | 用途 |
| --- | --- |
| `FOLLOW_OPML_B64` | 以私人 OPML 覆蓋公開範例 |
| `SOCIALDATA_API_KEY` | 選用的 SocialData X 來源 |
| `TIKHUB_API_KEY` | 選用的 TikHub 抖音／小紅書來源 |
| `X_BEARER_TOKEN` | 選用的官方 X API demo |
| `AGENTMAIL_API_KEY` | 選用的 metadata-only 郵件 digest |
| `AGENTMAIL_INBOX_ID` | AgentMail inbox 識別碼 |

Secret 值不得寫入 repo、Issue、log、截圖或驗收報告。

## 緊急停用 Variables

付費來源的 `*_ENABLED=0` 可作為急停開關：

- `SOCIALDATA_ENABLED`
- `TIKHUB_ENABLED`
- `X_API_ENABLED`
- `EMAIL_DIGEST_ENABLED`

未設定不代表一定會呼叫服務；沒有對應 secret 時，adapter 必須安全跳過。

## 程式內常數

查詢字串、平台、時間窗、排序、每次上限與間隔以
`scripts/update_news.py` 內下列常數群組為準：

- `SOCIALDATA_*`
- `TIKHUB_*`
- `X_API_*`
- `PAID_SOURCE_*`
- `AGENTMAIL_*`
- `BRIEF_*`

修改時以常數名搜尋，不依賴文件中的歷史行號。第三方 API 的參數值與費率
可能改變；啟用或擴大額度前必須查閱供應商當期官方文件。

## 重點訊號池

`data/daily-brief.json` 是全站共用的精選故事池。入選與排序由
`story_passes_brief_gate()`、`calculate_item_importance()` 及 `BRIEF_*`
常數控制。產品原則是「寧缺勿濫」，不可只為填滿版位而降低門檻。

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
