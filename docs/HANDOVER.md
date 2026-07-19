# AI 商業情報儀表板 — 交接摘要（截至 2026-07-19）

## 專案身份
- Fork：seisyuku/ai-news-radar_zhtw（上游 LearnPrompt/ai-news-radar，MIT）
- 線上：https://seisyuku.github.io/ai-news-radar_zhtw/
- 架構：GitHub Actions 排程 + watchdog + 外部心跳三層（見下方「排程
  健康」）+ Pages 靜態頁，零伺服器零月費
- 目標：六類商業事件情報（財報/市佔/資安漏洞/價格/benchmark/模型發布），
  排除程式技巧與社群意見；全站繁中（zh-TW）

## 協作協議
- Chat = 規劃/決策/驗收裁決；Claude Code（Sonnet 5:high）= 執行
- 一次一步，執行後回報再進下一步
- Git：GitHub Flow 極簡版，feature branch 短命速合，文件類變動經
  明示授權可直接 commit master；data/*.json 為機器產物不手改，衝突
  取遠端；shallow clone 屬預期

## 已落地的關鍵改造
1. 信息源置換：砍 11 個社群熱榜源；接入廠商一手、財經（GNews 查詢式）、
   benchmark 第三方、台灣繁中媒體、36Kr、橘鴉日報（對照源）
2. 繁中化：UI 全繁中 + 全管線 `to_zh_hant()`（含冪等性防護）+
   `SITE_NAME_ALIASES` 出口正規化
3. 商業事件加權：`BUSINESS_EVENT_KEYWORDS` 六類雙語規則 → 前端排序
   + 徽章；第六類「模型發布」為主體×發布詞×語境詞三重防護，規則
   詳見程式碼
4. 噪音閘門：HN 轉發過濾（聚合器後門）+ 關鍵字誤判修正（merger/
   hackathon/遊戲排行榜/eval 語境防護，規則詳見程式碼）
5. 生態群組去重：`SOURCE_ECOSYSTEM_GROUPS`（中國聚合器群），
   story_heat 同群多源只計一次
6. 基礎設施：前端資產 `?v=` 版號由 `tests/test_asset_versions.py`
   強制；規則見 `docs/OPERATIONS.md`
7. 教學文收錄過濾：標題模式硬性排除（英文句首錨定 + 中文複合詞，
   規則詳見程式碼）；已知殘差 2 條無徽章教學文，已測試釘住接受
8. 官方源接入：Thinking Machines Lab（thinkingmachines.ai/index.xml，
   Hugo 標準 RSS，非常見 /feed 路徑）
9. 翻譯正典名稱表（`CANONICAL_NAMES`，取代舊 BRAND_GLOSSARY，全案
   已結案）：三層防線——遮罩回填（翻譯前，主防線）/ 出口修正
   （exit-fix，命中 Table A/B 回寫 cache）/ 反向修正（Table C，只修
   顯示不回寫）。Claude 五子系詞另有非相鄰共現通道，刻意不泛化到
   Gemini/GPT 等其他家族尾綴詞——那些是語意開放的常見英文字，緊鄰
   要求才能避免誤傷無關句子，Claude 子系則有大量實測誤譯證據支撐。
   機制全文、匹配規則、日常維護方式見 `docs/OPERATIONS.md`「翻譯
   管線」章節。pytest 30 案例（199→226）
10. 資料時效警示帶：前端讀 `generated_at` 與瀏覽當下比較，2 小時內
    不顯示、2-6 小時低調樣式、6 小時以上明顯樣式，門檻常數化
    （`STALE_DATA_WARN_HOURS`/`STALE_DATA_BAD_HOURS`）

## 已知設計事實（避免重複調查）
- 收錄門檻 = ai_relevance ≥ 0.65；六類只主宰重點區排序，非收錄條件
- ai_relevance 有 has_ai 地板值 max(score, 0.65)——上游設計，
  動它需 14 天回測（治理規則），未動；聚合器條目多靠地板值過關
- BRIEF_SCORE_GATE/daily-brief 原始排序不影響使用者所見
  （調查結論在 story_passes_brief_gate() docstring）
- renderBoleBrief() 是死代碼
- 重點卡片減噪：下排內容分類標籤列與「優先順序 A/B/C」chip 已移除
  （importance_label 後端欄位與排序引用不動），上排業務事件徽章與
  內容標籤統一去重、近義詞讓位（model_release 抑制「模型釋出」
  內容標籤）
- 測試基線：226 pytest
- 排程健康 = 三層架構，已將停擺風險吸收掉（完整事故時間軸與診斷
  記錄見 `docs/OPERATIONS.md`「Schedule (cron) health」/「External
  heartbeat」章節）：
  - **內部 cron**（4 tick/hr）：會不定期靜默註冊衰變，不可靠層
  - **watchdog**（90 分鐘門檻代觸發）：機率性防線，實績 2/3（首次
    因 `-R` 旗標缺漏而失敗、已修正；之後 2 次代觸發皆成功）
  - **外部心跳**（cron-job.org，`:05`/`:35` + 25 分鐘 freshness
    guard，2026-07-19 上線）：脫離 GitHub schedule 機制的結構性解
    法，上線後段二驗證 5 筆 heartbeat run 行為全數符合預期，已結案
  - **定調**：停擺已由三層架構吸收；若之後又看到前端 2 小時警示帶
    浮現，代表連心跳層都失效了，排查入口 =
    `docs/OPERATIONS.md`「External heartbeat」章節「失效排查順序」

## 待辦檢查點
- 【最高優先】archive.json 容量治理：現況 52.5MB／128,527 條（已超
  GitHub 50MB 軟上限、push 時會印警告，遠低於 100MB 硬限）；21 天
  保留窗對「反覆被抓到的舊條目」形同虛設（last_seen_at 會被刷新）。
  2026-07-16 量測顯示淨縮小，判讀為初始匯入積壓正隨保留窗退場的
  過渡期、非穩態，現有資料不足以外推撞上 100MB 的日期——建議
  2026-08-04 前後（積壓退場窗口過後）再測一次。title-zh-cache.json
  為第二個成長型檔案（無 prune 機制，目前 4.4MB，成長速率低但零
  治理，長期仍列待辦）
- PAT 到期追蹤：外部心跳用的 fine-grained PAT 約 **2026-10-17**
  前需續期（90 天效期），續期步驟見 `docs/OPERATIONS.md`「External
  heartbeat」章節
- 7/21 覆核議程：
  - 四源審判：techurls / iris(Info Flow) / 36Kr / xAI 查詢詞
    - 三指標：事件命中率 / 獨占性 / 噪音型態（可修 vs 瀰漫）
    - 卷宗既有證據：兩源幾乎全數壓線 0.65（地板值撐起）、
      1shotchallenge 與 Thinking Machines 宣言均為 HN 後門流入（已堵）、
      Info Flow 參與 OPPO 回聲室；techurls 舉證責任已反轉（預設砍）
    - juya_daily 不參審（對照源定位）
  - 排程項：確認 7/17-7/21 這段期間前端 2 小時警示帶未曾擊穿即可
    ——三層防線已結案，不需再拆解個別 tick 間隔複測
  - watchdog.yml 去留裁決：保留，傾向留（零成本縱深防禦，外部心跳
    上線不代表 watchdog 該退役，三層互為備援）
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
