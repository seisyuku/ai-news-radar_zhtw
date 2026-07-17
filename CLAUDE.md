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
