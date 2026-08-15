# Claude Code Notes

Before changing this project, read:

- `skills/ai-news-radar/SKILL.md`
- `docs/SOURCE_COVERAGE.md`
- `README.md`

Do not commit private OPML files, API keys, cookies, browser exports, or `.env`
values. Keep the public repo usable without secrets.

The product direction is a two-layer AI business-intelligence tool:

- Default layer: a Taiwan Traditional Chinese view focused on six material
  AI-industry business-event categories.
- Advanced layer: custom OPML/source configuration and source health details for maintainers.

When adding sources, prefer official RSS/Atom feeds or OPML first. Add custom
fetchers only for stable, public, high-signal sources.

## 專案永久規則

- 所有輸出（回報、commit message、註解、文件）一律臺灣正體中文（zh-TW），
  嚴禁簡體字與中國用語；技術名詞、代碼保留英文。
- 分支紀律：功能改動走 feature branch，commit 後停住等驗收，除非工單明示
  「授權直接 merge push」。
- `data/*.json` 為排程機器產物：不手改、merge 衝突一律取遠端。
- `assets/`（`app.js`/`styles.css`/`motion.js`）有任何變更 → `index.html`
  的 `?v=` 版號遞增 + `tests/asset_manifest.json` 同步更新。
- 修改評分邏輯（`ai_relevance` 公式本體）前停手回報，需 14 天回測。
- 完成任何任務必附：修改清單、pytest 結果。

### 驗收回報協定

終端機互動介面（可折疊工具紀錄、box 邊框、視窗寬度換行）不適合
手動複製長內容，回報一律改用寫檔方式交付，不依賴終端機複製貼上：

- 每次工單驗收回報，除終端機正常顯示外，**額外**寫成單一檔案：
  `.claude-reports/YYYY-MM-DD-<簡短代稱>.md`。
- `.claude-reports/` 已加入 `.gitignore`，屬暫存交接產物，不進版控。
- 檔案內容規格：
  - 開頭附三行 metadata：對應工單標題、分支名、commit hash。
  - 完整 Markdown，表格用標準 `|---|---|` 語法，不因終端機寬度縮寫
    或斷行。
  - 所有數字、commit hash、修改清單逐項完整列出，不省略、不截斷。
  - 若過程中產生截圖，實際存成 png 檔於同一時間戳目錄下，回報
    檔案內用相對路徑引用；不得只聲稱「已存於某處」卻不交付實體檔。
- 寫檔完成後，終端機只需顯示一行：
  `回報已寫入 .claude-reports/<檔名>，請開啟該檔案複製。`
  不需要在終端機重複輸出完整回報內容。

## Subagent 委派規則

- 跑測試、比對 diff、檢查 lint、驗證檔案格式：一律委派 `verifier` subagent，不在主線以 high effort 執行
- 委派 `verifier` 時，須於任務描述中附上工單載明的檔案範圍，供其執行範圍比對
- 程式庫搜尋與探勘：交由 `Explore` subagent（已覆寫為 haiku），不在主線親自搜尋大量檔案
- 主線只保留：規劃、程式碼撰寫、跨步驟判斷
- **驗收裁決不在 CC 端進行**。CC 完成查驗後產出回報，裁決由 chat 端執行。此分工是刻意設計：由與執行端不同的模型評判執行端產出，避免共享推理盲點
- 不得將 `verifier` 擴充至判斷類任務（評價實作是否恰當、架構是否合理）。它與執行端同為 Sonnet，唯有限定在機械量測才不破壞上述異質性
- 禁止設定 `CLAUDE_CODE_SUBAGENT_MODEL` 環境變數——此變數會覆蓋所有 subagent 的 `model` 欄位，包含 `verifier` 與 `Explore` 各自指定的模型，會使分層路由失效
