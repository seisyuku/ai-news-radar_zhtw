# AI News Radar 維護 Skill

此 Skill 是 `seisyuku/ai-news-radar_zhtw` 的 repo 內維護規範，用於來源
治理、抓取器、資料輸出、前端、GitHub Actions 與 GitHub Pages。它不是
另一個公開站點，也不是供讀者查新聞的獨立 Reader Skill。

## 使用時機

- 評估或新增 RSS、Atom、OPML、公開 JSON feed 或靜態頁面來源
- 診斷 `source-status.json` 與來源健康度
- 修改 `scripts/update_news.py`、資料 schema 或 AI 商業事件呈現
- 維護 GitHub Actions、Pages 與外部 heartbeat
- 調整首頁資訊架構、篩選器或來源徽章

## 專案基準

- 公開站點：<https://seisyuku.github.io/ai-news-radar_zhtw/>
- GitHub：<https://github.com/seisyuku/ai-news-radar_zhtw>
- 產品定位：臺灣繁體中文 AI 產業商業事件儀表板
- 公開預設：不依賴 API key、cookies、登入狀態或私人信箱
- 私人客製：以未納管的 `feeds/follow.opml` 或 GitHub Secrets 提供

## 開始工作前

依序閱讀：

1. [`SKILL.md`](SKILL.md)
2. [`../../README.md`](../../README.md)
3. [`../../docs/HANDOVER.md`](../../docs/HANDOVER.md)
4. [`../../docs/SOURCE_COVERAGE.md`](../../docs/SOURCE_COVERAGE.md)
5. [`../../docs/OPERATIONS.md`](../../docs/OPERATIONS.md)

來源評估細節見 [`references/source-intake.md`](references/source-intake.md)，
產品與工程方法見 [`references/v2-method.md`](references/v2-method.md)。

## 核心原則

- 優先採用穩定、公開、具時間戳的官方 RSS／Atom／JSON。
- 新增預設來源前先檢查重複度、訊噪比與 GitHub Actions 可抓取性。
- 來源失敗必須在 `source-status.json` 可見，不可靜默消失。
- 不為了填滿重點區而加入低品質來源。
- 不提交私人 OPML、secret、token、cookies、信箱內容或 `.env`。
- 保持變更小且可審查；資料 schema 或評分邏輯變動必須有測試。

## 驗證

```bash
python -m py_compile scripts/update_news.py
python -m pytest -q
node --check assets/app.js
git diff --check
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/ai-news-radar
```

完整本機生成應輸出至暫存目錄，除非工單明確要求更新版控中的
`data/*.json`。
