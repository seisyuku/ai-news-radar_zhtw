# AI 商業情報儀表板 — 交接摘要（截至 2026-07-15）

## 專案身份
- Fork：seisyuku/ai-news-radar_zhtw（上游 LearnPrompt/ai-news-radar，MIT）
- 線上：https://seisyuku.github.io/ai-news-radar_zhtw/
- 架構：GitHub Actions 每 30 分鐘排程（含 concurrency 排隊 + push rebase 重試）
  + Pages 靜態頁，零伺服器零月費
- 目標：五類商業事件情報（財報/市佔/資安漏洞/價格/benchmark），
  排除程式技巧與社群意見；全站繁中（zh-TW）

## 協作協議
- Chat = 規劃/決策/驗收裁決；Claude Code（Sonnet 5:high）= 執行
- 一次一步，執行後回報再進下一步
- Git：GitHub Flow 極簡版，feature branch 短命速合；
  data/*.json 為機器產物不手改，衝突取遠端；shallow clone 屬預期

## 已落地的關鍵改造
1. 信息源置換：砍 11 個社群熱榜源；接入廠商一手（含 Gemini RSS）、
   財經（Reuters/CNBC 走 Google News RSS 查詢式接法）、benchmark 第三方、
   台灣繁中三媒體、36Kr（OpenCC 轉繁）、橘鴉日報（daily.juya.uk，對照源）
2. 繁中化：UI 全繁中 + 全管線 to_zh_hant()（含 s2t 冪等性防護）
   + SITE_NAME_ALIASES 出口正規化（含 source-status 旁路）
3. 商業事件加權：BUSINESS_EVENT_KEYWORDS 五類雙語規則 → business_events
   欄位 → 前端四級排序（徽章優先）+ 類別徽章；importance 公式未動
4. 噪音閘門：HN 轉發過濾（聚合器後門）；關鍵字誤判修正
   （merger 共現要求、hackathon 排除、遊戲排行榜排除）
5. 生態群組去重：SOURCE_ECOSYSTEM_GROUPS（中國聚合器群），
   story_heat 同群多源只計一次
6. 基礎設施：前端資產 ?v= 版號由 tests/test_asset_versions.py
   （manifest hash 雙向鎖）強制；規則見 docs/OPERATIONS.md

## 已知設計事實（避免重複調查）
- 收錄門檻 = ai_relevance ≥ 0.65；五類只主宰重點區排序，非收錄條件
- ai_relevance 有 has_ai 地板值 max(score, 0.65)——上游設計，
  動它需 14 天回測（治理規則），未動；聚合器條目多靠地板值過關
- BRIEF_SCORE_GATE/daily-brief 原始排序不影響使用者所見
  （調查結論在 story_passes_brief_gate() docstring）
- renderBoleBrief() 是死代碼
- 測試基線：179 pytest

## 待辦檢查點
- 7/21 觀察名單覆核：techurls / iris(Info Flow) / 36Kr / xAI 查詢詞
  - 三指標：事件命中率 / 獨占性 / 噪音型態（可修 vs 瀰漫）
  - 卷宗既有證據：兩源幾乎全數壓線 0.65（地板值撐起）、
    1shotchallenge 與 Thinking Machines 宣言均為 HN 後門流入（已堵）、
    Info Flow 參與 OPPO 回聲室；techurls 舉證責任已反轉（預設砍）
  - juya_daily 不參審（對照源定位）
- 8 月中複評：changelog 缺口（六廠 SOTA release notes 層，暫緩中）、
  財經查詢漏接蒐集（預案=AI 概念股+財報詞 GNews 查詢）、
  juya_daily 查漏價值、LLM 重排層觸發評估（影響範圍誤排已有證據 #1）

## 已知限制
- Meta AI / DeepSeek / xAI 為第三方報導非官方一手
- Artificial Analysis 未接入（每月手動看 leaderboard）
- 繁簡混排標題理論上可能疊字（極罕見，觀察中）
- 內測回報管道待補進說明文案
