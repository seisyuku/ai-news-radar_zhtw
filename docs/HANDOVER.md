# AI 商業情報儀表板 — 交接摘要（截至 2026-07-17）

## 專案身份
- Fork：seisyuku/ai-news-radar_zhtw（上游 LearnPrompt/ai-news-radar，MIT）
- 線上：https://seisyuku.github.io/ai-news-radar_zhtw/
- 架構：GitHub Actions 排程（cron 已加密至每小時 4 tick，含 concurrency
  排隊 + push rebase 重試）+ 獨立 watchdog.yml（每小時整點檢查代觸發）
  + Pages 靜態頁，零伺服器零月費
- 目標：六類商業事件情報（財報/市佔/資安漏洞/價格/benchmark/模型發布），
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
3. 商業事件加權：BUSINESS_EVENT_KEYWORDS 六類雙語規則 → business_events
   欄位 → 前端四級排序（徽章優先）+ 類別徽章；importance 公式未動
   （2026-07-17 定版：新增第六類「模型發布」，判定=主體白名單
   （MAJOR_AI_LABS 15 家）× 發布詞 × 模型語境詞三重防護，僅掃標題不
   掃摘要，子句層級共現避免 AI 日報類多主題長標題跨子句誤配）
4. 噪音閘門：HN 轉發過濾（聚合器後門）；關鍵字誤判修正
   （merger 共現要求、hackathon 排除、遊戲排行榜排除、eval/evals
   開發語境共現防護）
5. 生態群組去重：SOURCE_ECOSYSTEM_GROUPS（中國聚合器群），
   story_heat 同群多源只計一次
6. 基礎設施：前端資產 ?v= 版號由 tests/test_asset_versions.py
   （manifest hash 雙向鎖）強制；規則見 docs/OPERATIONS.md
7. 教學文收錄過濾（2026-07-17 定版）：收錄階段標題模式硬性排除，
   英文句首錨定（^how to/^guide to/^tutorial/^hands-on/
   ^step-by-step/^a coding guide + sdk guide/coding guide 不錨定
   高精度白名單）、中文複合詞（使用教學/教學文/入門教學/新手教學/
   保姆級/教程/手把手/實作指南，裸詞「教學/教学」已移除避免誤殺
   商業新聞）；已知殘差 2 條真教學文外洩但無徽章、不進重點區，
   已測試釘住接受
8. 官方源接入：Thinking Machines Lab（thinkingmachines.ai/index.xml，
   Hugo 標準 RSS，非常見 /feed 路徑）
9. 翻譯品牌詞彙表機制：BRAND_GLOSSARY 單一擴充點，掛在既有
   repair_zh_title_translation() 後處理流程，首條 Morning Squawk →
   晨間快評(Morning Squawk)
10. 資料時效警示帶（2026-07-17 上線）：前端讀 generated_at 與瀏覽當下
    UTC 時間比較，2 小時內不顯示、2-6 小時低調樣式、6 小時以上明顯
    樣式，門檻常數化（STALE_DATA_WARN_HOURS/STALE_DATA_BAD_HOURS）

## 已知設計事實（避免重複調查）
- 收錄門檻 = ai_relevance ≥ 0.65；六類只主宰重點區排序，非收錄條件
- ai_relevance 有 has_ai 地板值 max(score, 0.65)——上游設計，
  動它需 14 天回測（治理規則），未動；聚合器條目多靠地板值過關
- BRIEF_SCORE_GATE/daily-brief 原始排序不影響使用者所見
  （調查結論在 story_passes_brief_gate() docstring）
- renderBoleBrief() 是死代碼
- 重點卡片減噪（2026-07-17）：下排內容分類標籤列與「優先順序
  A/B/C」chip 已移除（importance_label 後端欄位與排序引用不動），
  上排業務事件徽章與內容標籤統一去重、近義詞讓位（model_release
  抑制「模型釋出」內容標籤）
- 測試基線：199 pytest
- 排程健康：cron 已從每 30 分鐘加密至每小時 4 tick（7,22,37,52），
  效果存疑——實測間隔仍達 92-147 分鐘，未見明顯改善；同一日內
  註冊衰變（schedule 觸發完全停止、無外部原因）已發生兩次，處方皆為
  對 workflow 檔 touch 重新註冊；watchdog.yml 已上線作為結構性解法
  （獨立 schedule 註冊、每小時整點檢查 update-news.yml 最後一筆
  schedule run，超過 90 分鐘未出現則 workflow_dispatch 代觸發），
  設計上與前端警示帶 2 小時門檻銜接（兩次衰變 + 看門狗防線詳見
  docs/OPERATIONS.md「Schedule (cron) health」章節）

## 待辦檢查點
- 【最高優先】archive.json 容量治理（2026-07-16 唯讀診斷）：
  - 現況：52.5MB（55,032,022 bytes）、128,527 條、最舊
    first_seen_at 2026-02-19——但 last_seen_at 只要條目被來源
    重複回傳就會刷新，21 天 archive_days 保留窗對「反覆被抓到
    的舊條目」形同虛設，並非真的每 21 天清一輪
  - git 歷史僅回溯到 2026-07-14（repo 當天重新匯入/壓縮歷史，
    無完整 7 天資料），以現有約 2.1 天窗口量測：archive.json
    從 59.5MB／138,818 條降到 52.5MB／128,527 條，即 **-2.12
    MB/日、-4,892 條/日**（目前是淨縮小，不是成長）
  - 判讀：這段淨縮小很可能是「初始匯入挾帶的一次性歷史積壓」
    正隨 21 天視窗持續退場，屬過渡期而非穩態；積壓何時清空、
    清空後的真實穩態成長/縮小速率都還不知道，**現有資料不足
    以外推撞上 100MB 的日期**，不要用這段負斜率下結論，需持續
    量測（建議積壓期過後，即匯入日 + 21 天 ≈ 2026-08-04 前後
    再測一次）
  - 已知風險：目前已超過 GitHub 建議的 50MB 軟上限（近期每次
    push 都會印警告），但仍遠低於 100MB 硬限（超過會直接拒絕
    push，屬於會擋線上更新的等級）
  - 第二個成長型檔案：title-zh-cache.json——**沒有任何
    prune/淘汰機制**，單調成長，同一 2.1 天窗口 +0.084MB
    （約 0.04 MB/日）；目前僅 4.4MB，照此速率離出事還很久，
    但因為完全零治理機制，長期仍列待辦，且風險型態跟
    archive.json 不同（archive.json 有時間窗設計但被繞過，
    title-zh-cache.json 是壓根沒設計）
  - data/ 其他檔案量測（2026-07-16，均非成長型隱憂）：
    latest-24h-all.json 3.2MB、stories-merged.json 1.2MB、
    latest-24h.json 1.1MB、daily-brief.json 72KB、其餘 < 15KB
- 7/21 覆核議程：
  - 四源審判：techurls / iris(Info Flow) / 36Kr / xAI 查詢詞
    - 三指標：事件命中率 / 獨占性 / 噪音型態（可修 vs 瀰漫）
    - 卷宗既有證據：兩源幾乎全數壓線 0.65（地板值撐起）、
      1shotchallenge 與 Thinking Machines 宣言均為 HN 後門流入（已堵）、
      Info Flow 參與 OPPO 回聲室；techurls 舉證責任已反轉（預設砍）
    - juya_daily 不參審（對照源定位）
  - 排程間隔複測（含看門狗成效）：驗證 4 tick/hr cron 是否真的把
    間隔壓回基線、watchdog.yml 上線後是否已出現代觸發事件、代觸發
    頻率是否符合設計預期（同時衰變機率應遠低於單一註冊）
  - 警示帶與看門狗門檻銜接檢視：看門狗 90 分鐘門檻 + 最壞情況下的
    watchdog 自身丟包，實際能否把停擺壓在前端警示帶 2 小時門檻內，
    需拿 7/17-7/21 這段實測資料驗證，而非只憑設計推論
- 8 月中複評：changelog 缺口（六廠 SOTA release notes 層，暫緩中）、
  財經查詢漏接蒐集（預案=AI 概念股+財報詞 GNews 查詢）、
  juya_daily 查漏價值、LLM 重排層觸發評估（影響範圍誤排已有證據 #1）
- 個資案已結案，僅剩桌面兩份 bundle 到期銷毀（追蹤銷毀完成即可關閉
  此項）

## 已知限制
- Meta AI / DeepSeek / xAI 為第三方報導非官方一手
- Artificial Analysis 未接入（每月手動看 leaderboard）
- 繁簡混排標題理論上可能疊字（極罕見，觀察中）
- 內測回報管道待補進說明文案
