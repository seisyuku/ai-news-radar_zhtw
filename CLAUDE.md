# Claude Code Notes

Before changing this project, read:

- `skills/ai-news-radar/SKILL.md`
- `docs/SOURCE_COVERAGE.md`
- `README.md`

Do not commit private OPML files, API keys, cookies, browser exports, or `.env`
values. Keep the public repo usable without secrets.

The product direction is a two-layer AI news tool:

- Default layer: curated AI-focused view for ordinary AI enthusiasts.
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
