# AI News Radar Pulse — 交接摘要（截至 2026-08-17）

## 2026-08-21 維運與讀者層校正

- **36Kr AI**：一般 RSS 長期回傳 WAF HTML，排程改以 Google News
  `site:36kr.com` 為正式 watchlist 路由；不再每輪先打不可用的直接 feed
  再把可用結果標示為 degraded。直接 feed 僅保留給低頻維運探測。
- **LLM Stats**：已解析的 `latestModels` payload 若沒有近期 allowlisted
  模型，記為健康的零筆結果 (`empty_reason=no_recent_allowlisted_models`)，
  不再累積 persistent failure；HTTP、payload 缺失與 schema 失敗仍是故障。
- **AI 摘要**：保留繁中、數字、版本名與提示注入驗證；相同
  content/model/prompt 鍵的 `insufficient_context`、`validation_length`
  拒絕會負面快取 6 小時，避免無產出的重複 Groq 呼叫。
- **AIBASE**：讀者資料改歸入 `curated_media` 的 `精選媒體` 群組，子來源
  顯示固定為 `AIBASE`。它不再是「AI網站」或社群類，也不再套用舊的
  default-source 100 分地板／AI 垂直源權重；仍與中國聚合來源共用
  corroboration ecosystem，不能藉轉載提高多源熱度。舊 archive 記錄在
  下次排程載入時會一併正規化，避免保留窗內重新產生獨立群組。
- **重點訊號卡**：移除所有固定理由與 RSS 摘要回退文案。只有產生且通過
  驗證的 `news_summary` 才建立「AI 新聞摘要」區塊；沒有摘要即完全不渲染
  其標題、留白或固定字串。

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
4. 噪音閘門：HN 轉發過濾（聚合器後門）+ V2EX 網域級排除
   （`AGGREGATOR_BACKDOOR_EXCLUDED_DOMAINS`，同聚合器後門機制形狀但
   鍵值為網域非來源標籤，掛在 `score_ai_relevance()`，只影響收錄層
   `items_ai`，`items_all` 透明度視圖不變）+ 關鍵字誤判修正（merger/
   hackathon/遊戲排行榜/eval 語境防護，規則詳見程式碼）
5. 生態群組去重：`SOURCE_ECOSYSTEM_GROUPS`（中國聚合器群），
   story_heat 同群多源只計一次
6. 基礎設施：前端資產 `?v=` 版號由 `tests/test_asset_versions.py`
   強制；規則見 `docs/OPERATIONS.md`
7. 教學文收錄過濾：標題模式硬性排除（英文句首錨定 + 中文複合詞，
   規則詳見程式碼）；已知殘差 2 條無徽章教學文，已測試釘住接受
8. 官方源接入：Thinking Machines Lab（thinkingmachines.ai/index.xml，
   Hugo 標準 RSS，非常見 /feed 路徑）
9. 翻譯正典名稱表（`CANONICAL_NAMES`，取代舊 BRAND_GLOSSARY，四階段
   全案已結案）：三層防線——遮罩回填（翻譯前，主防線）/ 出口修正
   （exit-fix，命中 Table A/B 回寫 cache）/ 反向修正（Table C，只修
   顯示不回寫）。Claude 五子系詞另有兩條擴充通道：非相鄰共現（同標題
   有 Claude/Anthropic 即保護）、與第四階段「無 Claude 共現也保護」
   （大寫詞形 + 緊鄰版號 + 同標題任一 CANONICAL_NAMES 實體共現，
   排除微軟/Google/蘋果/亞馬遜/三星/騰訊等綜合巨頭，防遊戲/消費品
   誤中）。範圍刻意維持 Claude 五子系封閉集，不泛化到 Gemini/GPT 等
   其他家族尾綴詞——那些是語意開放的常見英文字，Claude 子系則有大量
   實測誤譯證據支撐。機制全文、匹配規則、日常維護方式見
   `docs/OPERATIONS.md`「翻譯管線」章節；專屬 pytest 約 37 案例。翻譯 provider
   已改為可選、受限時的 Google Cloud Translation Basic v2
   主路徑與 DeepL fallback；缺少 credential 或 provider 故障只保留英文，
   不得阻塞快照更新。`source-status.json.translations` 與
   `translation-state.json` 分別提供無敏感資訊的狀態與六小時拒絕快取。
10. 資料時效警示帶：前端讀 `generated_at` 與瀏覽當下比較，2 小時內
    不顯示、2-6 小時低調樣式、6 小時以上明顯樣式，門檻常數化
    （`STALE_DATA_WARN_HOURS`/`STALE_DATA_BAD_HOURS`）
11. 重點訊號區資格閘門：`featuredCandidatesGate()` 前置過濾（不重排，
    既有徽章優先四級排序 `briefStorySortCompare` 不動）——徽章
    （`business_events` 非空）直接入選；無徽章僅在非
    `COMMUNITY_SOURCE_TYPES`（AIBASE）來源時才能補位，寧缺勿濫不硬湊。**未做**地板值
    排除：後端分數已被 `max(score, 0.65)` 覆寫，前端 JSON 無欄位能
    可靠區分真實分與地板值，判斷不可行後只做源類型排除（已回報此
    限制，非遺漏）。掛在 story-pool 與 no-story-data fallback 兩條
    候選池入口
12. 前端死代碼清理：`HN熱議` 分頁/計數器整組移除（背後 hackernews/
    zeli 抓取器已於 07-14 源置換移除，此為孤兒 UI，非過濾結果）；
    07-21 補一批同型殘留——`sourceSignal()`/`sourcePriority()`/
    `clusterBriefEvents()` 內的 `HN熱議`/`GitHub趨勢` 判斷分支同理
    清除（`clusterBriefEvents` 家族經 `renderBriefPicks()` →
    `rankedFallbackRows()` 仍有存活呼叫路徑，故只清殘留字串，不構成
    整組退役）
13. **7/21 四源審判裁決**：`iris`（Info Flow）、`techurls` 退出預設
    來源；2026-08-26 已將其與其他退役來源的擷取器、來源權重及前端殘留
    一併刪除，不保留 rollback 程式碼。`36Kr AI`、xAI/Grok 查詢詞
    （curated_media 內）維持不動。`AGGREGATOR_BACKDOOR_EXCLUDED_DOMAINS`
    （v2ex.com）保留為非來源專屬的 URL 網域防護。裁決依據見
    `docs/SOURCE_COVERAGE.md`「2026-07-21 Four-Source Trial」章節。
14. 內測回報管道文案上線：頁尾新增引導至 GitHub Issues 的說明文字
    （`.app-footer-note`），沿用既有頁尾樣式
15. **7/21 重點訊號區來源多樣性上限（N=2,僅退化層生效）**：診斷
    （`.claude-reports/2026-07-21-aibase-signal-area-diagnosis.md`）
    定位 aibase 佔重點訊號區 39.5%（近期 66%）之成因——非品質問題，
    而是絕大多數合格候選為單源（`storyHotScore=0`），
    `briefStorySortCompare` 前兩層（徽章、熱度）恆平手，勝負落在
    `storyScore` 的 22% `source_tier` 分量，使 aibase（`ai_vertical`,
    0.78）系統性擊敗供貨量更大但 tier 較低的來源。裁決：不動
    `source_tier`、不動 `storyScore` 權重（aibase 品質乾淨，壓 tier
    是錯誤懲罰；動權重逼近紅線）；改在選卡層加來源多樣性上限——新增
    `applyFeaturedSourceDiversityCap()`（`assets/app.js`），套用於
    `storyRowsForPool()` 產出的已排序 rows、切片為預設可見 5 席
    （Top3+展開2）之前。上限**只在「純靠 source_tier 決勝」的退化
    情形生效**：某來源已佔 2 席時，若其下一條與「下一個不同來源
    候選」在前兩層（徽章、熱度）平手才讓出席位；`hotScore` 有真實
    優勢者，或無不同來源候選可比較者，不受上限約束，仍保留席位
    （寧缺勿濫優先於多樣性，但不因多樣性規則反而剔除合格內容）。
    讓出的席位只由排序中「原本就在候選池」的其他合格候選（有
    `business_events` 徽章）自然遞補，不引入候選池外的內容。回測
    （復用診斷 40 次快照）：aibase 佔比 39.5% → 26.5%（近 10 次快照
    66.0% → 40.0%），40 次快照中無一次因上限造成 <5 席（既有資料
    供給充足，寧缺勿濫分支未被觸發，`applyFeaturedSourceDiversityCap`
    亦從不減少候選總數，只重排順序）；26 個因上限讓出而變更的席位
    100% 由有徽章候選遞補、0 例降級納入無徽章/社群類條目；40 次快照
    樣本中無 aibase 真實熱度豁免案例（該窗口 aibase `duplicate_count`
    100%=1，單源為主下豁免路徑未被觸發，符合診斷 D1 既有發現），
    豁免邏輯正確性改由合成案例的單元測試
    （`tests/test_featured_source_diversity_cap.py`）驗證。細節與
    上限前後完整對照表見
    `.claude-reports/2026-07-21-featured-diversity-cap.md`。
    **範圍追認**：工單原文以「熱點」（`hot`）檢視為診斷對象，實作時
    一併套用到「時間線」（`timeline`／`latestStories()`）路徑——該
    路徑底層同樣呼叫 `briefStorySortCompare`，存在完全相同的單源
    平手退化風險，若不一併套用，使用者切換檢視即可繞過上限、
    aibase 集中問題原封不動重現。此擴大已於驗收時追認為正確範圍，
    非後續才發現的遺漏。

16. **8/16 Model Release Radar v1**：新增三個獨立、可觀測且維持
    `watchlist` tier 的來源：LLM Stats `latestModels` 只負責近期主要實驗室
    模型的 atomic 查漏；LLM Rumors RSS 補長篇策略分析；RuntimeWire RSS
    以嚴格標題篩選補模型、推理、價格與 benchmark 後續，未啟用其高量
    Head-to-Head feed。同步修正模型發布分類器把版本小數點誤當句號的
    bug（Qwen3.8/Grok 4.6/Gemini 3.7 先前因此漏徽章），並擴充
    Qwen/GLM/Kimi 的模型版本識別，避免跨版本錯誤聚合；「模型」分頁
    額外合併 24 小時內的 atomic 發布資料並以發布事件優先，不污染其他分頁的
    24 小時窗口。未修改全域評分公式；後續分析聚合與
    `model_significance` 仍列 Roadmap 待辦。
17. **8/17 Groq 新聞短摘要 v1**：RSS/Atom fetcher 開始保留並清理來源
    `summary`/`description`；排程在設定 `GROQ_API_KEY` 時，以
    `qwen/qwen3.6-27b` 對有內容依據的高優先 story 產生 30–120 字繁中
    摘要，單輪最多新增 6 則，並以 `data/ai-summary-cache.json` 內容雜湊
    快取避免重複呼叫。標題-only 不送出；provider 或輸出驗證失敗不阻斷
    更新。前端「為什麼重要」固定模板已移除，改顯示「AI 新聞摘要」；
    沒有合格摘要時整塊隱藏。未修改全域評分公式。
18. **8/17 Gemini 備選候選裁決（未啟用）**：`gemini-3.5-flash-lite`
    在新 project 已通過 model discovery、plain `generateContent` 與
    structured JSON；七個合成案例為 5 generated pass、1
    `insufficient_context`、1 因缺少精確詞「不可信」未過 deterministic
    gate，但未重現提示注入指令或疑似 key。歷程另確認舊 project 的
    `429 RATE_LIMIT_EXCEEDED` 與 `gemini-2.5-flash-lite` 對新使用者的
    `404 NOT_FOUND` 是不同失敗原因。裁決為
    `qualified backup candidate, disabled by default`：Groq 仍是 primary，
    workflow/production 尚未讀 `GEMINI_API_KEY`、未做 fallback、未授權
    真實 feed 內容送往 Gemini。啟用前必須完成三時段穩定性、同案比較、
    trigger matrix、防雙重計費、provider+model cache、成本/狀態護欄與
    tier 資料政策裁決；完整準入條件見 `docs/OPERATIONS.md`，sanitized
    證據見 `reports/provider-evals/gemini-3.5-flash-lite-20260817.md`。
19. **8/17 LLM 翻譯與 Simon Willison 徽章修正**：`LLM`／`LLMs` 納入
    `CANONICAL_NAMES` 遮罩，Google Translate 不再把 AI 縮寫譯為「法學
    碩士」；既有快取也會依原始英文標題定點修復並回寫。Simon Willison
    是公開示範 OPML 的既有 builder feed，不是臨時來源；其 Qwen 3.8
    文章的錯誤「財報」來自量化格式 `Q4_K_M` 被誤認為季度 `Q4`。ASCII
    關鍵字邊界已將底線視為 token 一部分，該篇保留有內容依據的「評測」
    徽章，不變更全域排序或擴大摘要資料取得範圍。
20. **8/17 Top10 摘要可見性與失敗可觀測性**：Top3 後的故事卡現在在
    `news_summary` 存在時顯示兩行內的「AI 摘要」，避免已生成內容只因
    精簡卡版型而隱藏。title-only 條目仍不會生成摘要；這是來源內容不足
    的安全邊界，不是前端缺漏。`source-status.json.ai_summaries` 保留原有
    `last_error_type`，並新增不含原文與 provider 回覆的
    `last_error_detail` allowlist，供診斷 Groq 輸出被本地 gate 拒絕的原因。
21. **8/17 Top10 來源多樣性與摘要繁體化**：來源多樣性上限現在對熱點完整
    Top10 生效，而非只在預設可見的前五格生效；同源單源平手內容會讓位給
    同層的其他來源，真實多源熱度仍保留，沒有調整 AI relevance 或重要性
    權重。Groq 摘要在生成及快取讀取時都以 OpenCC `s2t` 統一為繁體，修復
    `将`／`并购` 類模型輸出殘留，且不另送內容到翻譯服務。
22. **8/17 摘要候選不中斷與英文 RSS 顯示界線**：`GROQ_SUMMARY_MAX_NEW`
    的上限只計成功新增摘要；驗證失敗不再耗盡額度而讓後段、已在讀者畫面
    的有 RSS 內容故事永遠無法嘗試。候選嘗試仍受既有 20 條上限保護。Top
    卡一旦有合格繁中 AI 摘要，就隱藏原始 RSS 摘要，避免英文原文與繁中摘要
    同時呈現；無合格摘要時仍顯示來源原文，且不為 title-only 項目新增抓取。
23. **8/17 RSS 摘要顯示翻譯**：既有英文 RSS `summary`／`description`
    現在沿用 title 的 Google Translate、正典名稱遮罩及繁體轉換，輸出
    `summary_zh` 供前端優先顯示；原始 `summary` 保留作 Groq 事實依據。
    原生繁體 RSS 摘要只正規化、絕不送翻譯；沒有 RSS 簡介的條目不新增
    抓取或推測。翻譯快取以 `summary::` 前綴與既有 title 快取共存。

## 部署

實測 `gh api repos/{owner}/{repo}/pages`（2026-07-28）：

```json
{
  "status": "built",
  "cname": null,
  "custom_404": false,
  "html_url": "https://seisyuku.github.io/ai-news-radar_zhtw/",
  "build_type": "legacy",
  "source": { "branch": "master", "path": "/" },
  "public": true,
  "https_enforced": true
}
```

- **發佈來源**：`master` 分支根目錄（`path: "/"`），非 `gh-pages` 或
  其他分支
- **build type**：`legacy`——GitHub Pages 直接監看分支內容並發佈靜態
  檔案，無 Jekyll 或其他建置步驟
- **自訂網域**：無（`cname: null`），使用預設 `github.io` 網域
- **HTTPS**：已強制啟用（`https_enforced: true`）
- **`.github/workflows/` 內無 Pages 部署 step，發佈由 GitHub Pages
  直接監看 `master` 分支完成**——`update-news.yml` 的 `update` job
  推送新的 `data/*.json` 後即由 Pages 自動反映，不需額外部署動作

## 已知設計事實（避免重複調查）
- 收錄門檻 = ai_relevance ≥ 0.65；六類只主宰重點區排序，非收錄條件
- ai_relevance 有 has_ai 地板值 max(score, 0.65)——上游設計，
  動它需 14 天回測（治理規則），未動；聚合器條目多靠地板值過關，且
  此覆寫使前端無法回推真實分（見「重點訊號區資格閘門」的地板值排除
  限制）
- BRIEF_SCORE_GATE/daily-brief 原始排序不影響使用者所見
  （調查結論在 story_passes_brief_gate() docstring）
- `renderBriefBrief()` 是死代碼；另發現同批未被呼叫的死代碼：
  `pickBriefItems()`、`clusterBriefEvents()` 的獨立呼叫路徑、
  `renderStoryViewPanel()`——皆僅定義未被任何即時渲染路徑呼叫，
  未清除（非本輪範圍），供未來清理參考
- 重點卡片減噪：下排內容分類標籤列與「優先順序 A/B/C」chip 已移除
  （importance_label 後端欄位與排序引用不動），上排業務事件徽章與
  內容標籤統一去重、近義詞讓位（model_release 抑制「模型釋出」
  內容標籤）
- `to_zh_hant()` 詞彙保護層裁決與已知限制（2026-07-21，
  `ZH_HANT_PROTECTED_TERMS`/`ZH_HANT_BARE_TERM_CONTEXT`，見
  `scripts/update_news.py` 常數上方註解）：`参数` 無條件保護為
  `參數`，前提是本站產品定位排除程式技巧/開發者社群內容（若未來
  納入此類內容，需重新評估）；已知限制是 CLI 引數（argument）語境
  的 `参数` 也會被誤改為 `參數` 而非技術正確的 `引數`——2026-07-21
  全量回溯（`archive.json` 90,826 筆唯一標題）基準：131 筆 diff／
  128 筆修正／3 筆接受誤傷（0.0033%，皆出自已移除的 Show HN／開發者
  社群來源）；曾評估改為 AI/模型語境共現閘門（比照裸詞「字節」）但
  已否決，因為會讓規格參數類標題（手機/鏡頭/晶片/Kubernetes 設定）
  退回錯誤的「引數」，得不償失——**不得未來善意重新引入此共現閘門**
- `to_zh_hant()` s2twp context-collision 定點保護（5 詞，2026-07-21，
  `fix/zh-hant-context-collision-0721`，見
  `.claude-reports/2026-07-21-zh-hant-context-collision.md`）裁決記錄：
  1. **保護內容**：`循环`/`回调`/`图像` 併入 `ZH_HANT_PROTECTED_TERMS`
     無條件保護（`循環`/`回調`/`圖像`，理由與「参数」同一產品範疇
     排除假設）；`ZH_HANT_BARE_TERM_CONTEXT["字节"]` 共現詞集擴充
     「BAT」與公司行為動詞「发现/推出/发布/宣布」；新建
     `ZH_HANT_REVERSE_BARE_TERM_CONTEXT["对象"]`（storage 語境共現詞集：
     存储/存儲/数据库/資料庫/database/storage/S3/OSS/bucket）——**方向
     與「字節」閘門相反**：預設攔回「對象」，僅 storage 語境共現時才
     放行 s2twp 原生輸出的「物件」。全量回溯 `archive.json` 85,926 筆
     唯一標題：249 筆 diff／182 筆預期修正／59 筆共現閘門判定／
     **8 筆已裁決接受的誤傷**
  2. **已接受的 8 筆誤傷**：7 筆為真程式語境（loop/callback 語境被
     `循環`/`回調` 誤保護，範疇外，比照「参数」CLI 引數先例）、1 筆
     為物件儲存罕見措辭（`对象标签读写`，未含 storage 詞集任一關鍵字）
  3. **對象 storage 共現詞集的已知缺口**：以非清單詞（例：`云`、
     `localStorage`、`标签`）描述物件儲存語境的標題，會被反向閘門
     預設攔回「對象」而非 s2twp 原生的「物件」。**明列為未來「第七類」
     工單前置**——第七類上線、物件儲存成為讀者核心內容時，須以該
     類別實際的 `items_ai` 可見樣本重新調校此共現詞集，不在本輪
     （2026-07-21）硬調，避免無實際樣本支撐的臆測性擴詞
- Python `re` 模組在 Unicode 模式下 `\w`/`\b` 會匹配 CJK 表意文字，
  因此 `(?<!\w)term(?!\w)` 形式的 Latin 詞界錨定，在中英混排標題
  （本站最常見的標題形態）下對緊鄰 CJK 字元的英文詞恆為匹配失敗。
  Latin 詞界必須改用 ASCII-only 邊界
  `(?<![A-Za-z0-9])...(?![A-Za-z0-9])`。此類 bug 的特徵是**單元測試
  全綠但實際場景全滅**（純英文測試字串不會觸發，只有真實中英混排
  語料才會曝露），不會自行浮現，日後任何用到 `\w`/`\b` 做 Latin 詞
  境判斷的程式碼都要留意此陷阱（實際案例見
  `_zh_hant_bare_term_context_ok()` 的開發過程，
  `.claude-reports/2026-07-21-zh-hant-term-protection.md`）
- `.site`／`.source`／`.category` 三個徽章的隱藏邏輯彼此獨立，互不
  依賴（2026-07-21，`CATEGORY_REDUNDANT_WITH_SOURCE` 整組退役後）：
  `.site`／`.source` 的隱藏各自由 `renderItemNode()` 內兩個獨立的
  `context.source === item.source` 判斷式負責，在 `buildSourceGroupNode()`
  的巢狀分組渲染情境下對幾乎所有卡片恆為真（該來源子分組內所有項目
  的 `item.source` 本就等於分組鍵本身）；`.category` 現為一般分組
  列表中**唯一**的來源識別徽章，無條件依 `SOURCE_KINDS` 渲染，與
  `.source`/`.site` 是否隱藏完全無關。已刪除的
  `CATEGORY_REDUNDANT_WITH_SOURCE` 常數原意是「避免 `.category` 與
  `.source` 重複顯示同一段文字」，但這個前提在現行渲染架構下從未
  成立——`.source` 早被前述獨立機制恆常隱藏，該常數的實際效果只是
  把碩果僅存的 `.category` 也一併關掉，讓 `official_ai`／
  `curated_media`／`opmlrss`／`aibase` 四個 site_id 的卡片完全沒有
  來源識別文字，並非「去重」。重點訊號區（`buildTopStoryCard()`／
  `buildStoryCard()`）完全不使用 `renderItemNode()`，沒有 `.category`／
  `.source` 元素，此常數的設計前提在該區塊亦無從復活
- `SOURCE_KINDS` 的 AIBASE 顯示名稱維持原文 `AIBASE`，並作為「精選媒體」
  的子來源，不形成獨立來源類別。
- `SOURCE_KINDS` 的 `opmlrss` label「OPML」對一般讀者是技術縮寫，
  可理解性存疑（2026-07-21 隨上一項一併檢視時發現，**本輪不改**）：
  `opmlrss` 目前屬進階層 site_id，實際曝光範圍（是否觸及一般讀者
  可見的預設層卡片）未經證實，貿然改字可能是無的放矢，也可能改壞
  已熟悉「OPML」一詞的進階使用者的預期用語，留待獨立工單評估曝光
  範圍後再裁決是否修改
- 測試基線：267 pytest（2026-07-21 重點訊號區來源多樣性上限工單，
  新增 `tests/test_featured_source_diversity_cap.py` 5 案例，由 262
  → 267；此前基線 240 已隨中間工單的測試增補過時，此處一併更新為
  當下實測值，避免下次比對誤判)
- 排程健康 = 三層架構，已將停擺風險吸收掉（完整事故時間軸與診斷
  記錄見 `docs/OPERATIONS.md`「Schedule (cron) health」/「External
  heartbeat」章節）。**2026-07-21 全期（7/17-7/21）唯讀複測驗證通過**：
  - **內部 cron**（4 tick/hr）：全期 59 筆成功 schedule run，平均間隔
    99.5 分鐘、中位數 81.0 分鐘、最大 293.7 分鐘，44.8%（26/58）間隔
    超過 90 分鐘——不可靠層特性依舊，符合既有基線判讀，靠下兩層兜底
    吸收，非本輪需修復項
  - **watchdog**（90 分鐘門檻代觸發）：**確認留**（原「傾向留」升級
    為確定裁決）。全期完整代觸發記錄（非僅先前對話內看到的 2 筆）
    共 **8 次**，**7 次成功、1 次失敗（87.5%）**；唯一失敗即
    `-R` 旗標缺漏事件本身（07-18 03:21Z，缺口 138 分鐘），修復
    （commit `387d27c`）之後同期內連續 **7/7** 成功，逐次對應主排程
    缺口：118／153／114／109／197／160／158 分鐘
  - **外部心跳**（cron-job.org，`:05`/`:35` + 25 分鐘 freshness
    guard，2026-07-19 上線）：脫離 GitHub schedule 機制的結構性解
    法。GitHub 側可見全期 80 筆 `:05`/`:35` 節奏 dispatch，early-exit
    （內部排程健康）59 筆（73.75%）、接管全量執行 21 筆
    （26.25%）——接管比例偏高，反映內部 cron 中位間隔（81 分鐘）
    本就常態性超過心跳 25 分鐘門檻，心跳已是事實上的共同主排程而非
    罕見備援；發現 1 起 GitHub API 側 503 瞬斷（07-20 00:35Z）導致
    單次 freshness-check 失敗，非 cron-job.org 端問題。**已知限制**：
    cron-job.org 自身執行紀錄（含任何從未送達 GitHub 的
    401/超時案例）不在 GitHub 側可見範圍，完整驗證仍需使用者親自
    登入 cron-job.org 後台確認
  - **前端警示帶銜接**：全期 0 次觸發 6 小時明顯樣式；2-6 小時低調
    樣式觸發 6 次（累計約 5.0 小時），**全數集中於心跳上線（07-19）
    之前**，07-19 之後至 07-21 零次觸發，與心跳上線時間點完全吻合
  - **內部 cron 頻率裁決（2026-07-21）**：維持 4 tick/hr，不降回
    上游預設的 30 分鐘一次。理由：降頻不解決病灶（病灶型態是排程
    「歸零」個案而非「過密」，降低密度對此無效）；且 4 tick/hr
    目前仍對資料新鮮度上限有實質貢獻，降頻會在心跳 25 分鐘 guard
    疊加下犧牲現有新鮮度餘裕，省下的 Actions 用量不足以抵銷代價
  - **定調**：停擺已由三層架構吸收，且本輪唯讀複測未發現新的
    未結案異常；若之後又看到前端 2 小時警示帶浮現，代表連心跳層都
    失效了，排查入口 = `docs/OPERATIONS.md`「External heartbeat」
    章節「失效排查順序」
- **分析 `data/*.json` 前必須先同步遠端**（2026-07-27）：`data/*.json`
  由排程每 30 分鐘更新並推送。本機工作目錄極易落後數百個 commit，
  直接讀取會分析到歷史切片。任何以 `data/*.json` 為輸入的評估、
  掃描、統計工單，執行前必須先 `git fetch` 並確認落後筆數；需要
  最新資料者須 `git pull --ff-only`。2026-07-27 曾因本機落後 207
  個 commit，誤判「排程停擺 3.5 天」，實際排程全程正常（每 30
  分鐘一筆快照、GitHub Actions 連續 success）。判斷排程健康須以
  `origin/master` 或 `gh run list` 為準，`stat` 的 mtime 與本機
  `git log` 皆為本機視角，不可作為依據
- **archive.json 容量現況與縮小成因**（2026-07-27）：實測 29 MB、
  70,439 筆，`published_at` 範圍 2015-12-11 ～ 2026-07-27。相較
  07-21 的 52.5 MB 大幅縮小，已退回 GitHub 50 MB 軟上限之下。成因
  查證：07-23 至 07-27 退場 20,358 筆唯一 URL，其中 94% 集中於
  TopHub（9,348）／Buzzing（5,091）／Info Flow（2,279）／
  TechURLs（799）／NewsNow（479）等**已於先前來源整頓移除、不在
  現行 6 個啟用 fetch 任務內**的來源。屬已移除來源歷史積壓的一次性
  退場，非穩態衰減，證實 07-21「淨縮小疑為初始積壓退場」之假設。
  原訂 ~2026-08-04 之容量複測降級為「確認積壓退完後檔案是否止跌
  回穩」，不再視為風險項目
- **已移除來源的歷史積壓污染語料分析**（2026-07-27）：archive.json
  保留已移除來源的歷史條目直至其自然退場。2026-07 期間語料中約 2
  萬筆來自已停用來源，任何以 archive.json 為基礎的規則校準或噪音
  分析，若未過濾來源，會對**再也不會出現的噪音**進行最佳化。後續
  同類分析工單須明列來源過濾條件
  - **六類上線規則之污染影響：已診斷結案（2026-07-27），不做任何
    規則修改。** 依 `.claude-reports/2026-07-27-six-category-corpus-audit.md`
    與 `.claude-reports/2026-07-27-benchmark-gate-output-audit.md`：
    - 六類規則主體（五類共 169 個關鍵字，commit `bf2d47a`）為人工
      編訂，無語料依據，無暴露面
    - 後續三次語料驅動調整（`ab1e088`／`595bb13`／`1b08987`）之用途
      為「發現失效案例」而非「擬合參數」，與 infrastructure 第七類
      的統計擬合性質不同，過擬合風險不可類比
    - 輸出端實測：四條排除規則／共現閘門在現行 6 源 3,004 筆樣本上
      合計僅作用 4 次（0.13%），其中 3 次攔阻正確、1 次為 market
      軸誤殺但已由 earnings 接住。作用面過小，不足以承載有意義的
      偏誤
    - 結論：污染事實成立，但對六類的實質影響為可忽略，**不重新
      校準、不修改規則**
  - **休眠規則登記（0 觸發，保留不移除）**：
    `BUSINESS_EVENT_EXCLUDE_KEYWORDS["security"]`（駭客馬拉松等 5
    詞）與 `BUSINESS_EVENT_EXCLUDE_KEYWORDS["benchmark"]`（遊戲等 4
    詞）在現行來源上觸發次數為 0。判定為休眠而非失效——詞條語意
    自足，未來新增來源若產出該類內容即刻生效。保留成本趨近於零，
    不移除
- **21 天保留窗口對現役來源的實際行為（2026-07-27 實測）**：保留邏輯
  以 `last_seen_at` 而非 `published_at` 為準。現役來源若在其索引頁／RSS
  持續列出舊文，該條目的 `last_seen_at` 會反覆刷新，使條目留存時間
  遠超過 21 天。實測現行 6 源共 3,015 筆中，`published_at` 超過 21 天
  者 385 筆（12.77%），集中於 official_ai（324 筆），最舊者發佈於
  2026-04-06。判定為**已知行為，不修正**：留存量上限由來源索引頁
  大小決定，非無限膨脹；`archive.json` 為去重與歷史存底，展示層另走
  `data/latest-24h.json`，舊條目不會外洩至使用者可見範圍。對比：
  已移除來源因 `last_seen_at` 凍結，會準時於 21 天後整批退場（見下方
  「archive.json 容量現況」條目）
- **無人值守失效模式（2026-07-27 盤點）**：
  - 通知機制為零——無 status badge、無自動開 issue、無 webhook。
    workflow 內的 `::warning::`／`::error::` annotation 僅顯示於該次
    run 的日誌頁，不會主動推送
  - 單一來源抓取失敗為靜默跳過（`scripts/update_news.py`
    `collect_all()` 的 per-source `try/except`），不會導致 job 失敗。
    來源健康須主動查 `data/source-status.json` 或前端進階層
  - `watchdog.yml` 每小時觸發，可涵蓋排程掉線，但無法涵蓋
    「job 成功但資料劣化」
  - GitHub 對無活動 repo 會靜默停用排程 workflow（60 天）。本 repo
    的快照 commit 由 `github-actions[bot]` 每 30 分鐘推上 default
    branch，推定可持續重置計時器，但未經實證。**失效徵狀為網站資料
    停在某一天不再更新；恢復方式為 `gh workflow enable` 後推任一
    commit。**
- **`primary_item.site_id` 欄位遺漏修復（2026-07-27）**：
  `build_story_record()` 的 `primary_item` 輸出字典原未列入 `site_id`
  鍵（同函式內 `story_reasons()`／`story_category()` 皆能正常讀取
  `primary.get("site_id")`，證實為純欄位遺漏而非資料不可得）。
  - 影響範圍：`assets/app.js` 的 `storyCandidateSiteId()` 恆讀到
    `null`，導致兩項機制在故事池路徑上自始未生效——
    (a) `featuredCandidatesGate()` 的社群來源補位排除；
    (b) `applyFeaturedSourceDiversityCap()` 的來源多樣性上限 N=2
    （2026-07-23 合併，**自合併起即為無效狀態**）
  - 修復前實測（2026-07-27 快照）：重點訊號區前 10 名中前 4 席
    皆為 aibase，預設 Top 3 全數同源
  - 修復後模擬：故事集合不變（0 新增、0 移除），僅排序調整，
    前 5 席內 aibase 由 4 席收斂至 2 席，符合 N=2 設計目標
  - **預期附帶效果（非回歸）**：徽章故事少於 10 則的日子，aibase
    無徽章故事將被排除於補位之外，重點訊號區可能較先前為短。
    此為設計預期，依北極星原則不得以「條數不足」為由回調。
- **infrastructure 第七類規則：整條退場（2026-07-27 裁決，非待辦、
  非未結項目）**。V5/V6/V7 三輪校準與驗證歷史見下方三項退場依據：
  1. **樣本可行性**：全量命中率僅 0.43%，新資料累積速率約 0.4
     筆／日，欲湊足 60 筆獨立留出樣本需 120 天以上；既有語料的
     獨立樣本池已被前四輪抽樣（calib100／holdout98／C1／C2）抽乾，
     此後任何驗證設計都無足夠新樣本可用，非可透過調整方法論解決
  2. **精準度逐輪惡化**：V6 holdout 67.35% → V7 C1（擴張型時間
     留出）51.67%／C2（收縮型專屬池）46.88%，且 C1 44.8% 的誤判
     可溯源至 V6 上一輪修正動作本身（英文動作動詞＋裸詞主體擴大
     後的副作用），判定為**過擬合**而非單輪實作瑕疵，換人重做或
     換方法論皆無法迴避同一結構性問題
  3. **產品價值不成立**：日均約 0.4 則的類別規模，不足以支撐獨立
     徽章與獨立篩選軸這類使用者可感知的呈現層投資
  - V5/V6/V7 全部評估報告（`.claude-reports/2026-07-21-infrastructure-*`
    與 `.claude-reports/2026-07-27-infrastructure-v7-structural.md`
    等）保留作為歷史紀錄，不進版控、不再更新
  - 前一輪「須在同步後語料上重做」之裁決，**就第七類而言隨本次
    退場裁決一併取消**——不再有下一輪重做

## 通用評估規範

適用於未來任何規則驗證，不限 infrastructure 第七類：

- **精準度門檻一律 85%。** 門檻調整僅得在無待決候選規則的時點提出，
  且理由須獨立於任何特定規則；不得於某規則未達標後向下調整
- **評估樣本分母限定「評估執行當下啟用中的來源」**，名冊須於執行
  時凍結並記錄於報告。評估期間若有來源退場，樣本重算，不得事後
  剔除。反向舉證中但尚未裁決的來源納入分母，但須在報告中分層
  列出其貢獻筆數
- **來源盤點須以「fetch 函式實際產出的 entry」為準，不得只列舉
  設定檔 tuple。** 已知 tuple 之外仍有來源路徑：`official_ai` 除
  `OFFICIAL_AI_FEEDS` tuple 外，`fetch_official_ai_updates()` 另
  硬編爬取 `anthropic.com/news`（`parse_anthropic_news_items()`）
  與 `developers.openai.com/codex/changelog`；另有 `--rss-opml`
  CLI 參數指向的外部使用者 OPML 檔案（不進版控，內容無法從
  repo 檢查）。僅讀 tuple 定義會漏算這些來源，盤點/去重/缺口
  判斷前須先確認涵蓋範圍

## 待辦檢查點
- archive.json 容量治理【已降級，非最高優先】：現況已降至 29MB
  （2026-07-27 實測，見「已知設計事實」章節「archive.json 容量現況
  與縮小成因」），退回 GitHub 50MB 軟上限之下。原 52-53MB、逼近軟
  上限的風險已隨已移除來源（TopHub／Buzzing／Info Flow／TechURLs／
  NewsNow 等）的歷史積壓一次性退場而解除，證實 07-21「淨縮小疑為
  初始積壓退場」之假設為真、非穩態衰減。**原訂 ~2026-08-04 之複測
  範圍縮小為「確認積壓退完後檔案是否止跌回穩」，不再視為風險項目
  或治理行動項**；若複測發現止跌後仍持續成長，才需重新升級處理。
  title-zh-cache.json 為第二個成長型檔案（無 prune 機制，目前約
  4.4MB，成長速率低但零治理，長期仍列待辦）。已移除來源（12 源）
  將分兩批整批自然退場：10 源（tophub／buzzing／aihot／newsnow／
  zeli／aibreakfast／aihubtoday／followbuilders／bestblogs／
  hackernews）**2026-08-04**、iris／techurls **2026-08-11**，屆時
  全庫由 69,446 筆降至約 3,000 筆量級，容量問題自我解決，本項
  降級為觀察
- PAT 到期追蹤【時效性最高，2026-10-17 硬期限】：外部心跳用的
  fine-grained PAT 約 **2026-10-17** 前需續期（90 天效期），續期
  步驟見 `docs/OPERATIONS.md`「External heartbeat」章節
- 財經查詢擴充（GNews AI 概念股+財報詞）【已否決，僅待 8 月中複評】：
  **否決關閉**——重點訊號區已於資格閘門上線時選定「寧缺勿濫」為取捨
  （供給不足寧可顯示較少條數，不擴大信源換取湊數），供給面擴張的
  迫切性降低；查詢詞組設計與三廠 GitHub Releases 評估已完成唯讀
  評估（結論：三廠 Releases 皆不足以填補官方一手空缺），changelog
  缺口改在 8 月中複評時視情況升值重提，不在本輪動作
- 一般列表徽章渲染＋事件篩選軸（六類）【可隨時開工，無到期壓力】——
  待開工，無前置依賴

## 7/21 覆核結案記錄（四源審判 + 排程健康，已裁決）

**四源審判判決**（7/17-7/21 全期唯讀取證，從 `data/archive.json`
以現行 `score_ai_relevance()`/`business_event_score()` 重算，因
archive 不保留衍生欄位；四源 fetch 階段皆無 `summary`，重算與正式
產線等價）：

- **iris（Info Flow）：砍**。窗口內 3536 筆新進項目，AI 相關真事件率
  僅約 0.65%（`business_event_score()` 不檢查 `ai_is_related`，原始
  關鍵字命中率 4.33% 中八成以上是非 AI 假陽性）；過 0.65 閘門的
  398 筆中 99.5%（396 筆）精準卡在地板值；v2ex.com 排除後裸露規模
  仍佔 fetch 總量 19.5%；全期僅 2 次真正遇到更高階源競爭且兩戰皆敗
  （tier 排序機制下結構性必輸），**0 次有意義的 primary_item 晉升**
- **techurls：砍**。990 筆新進項目，AI 相關真事件率約 1.11%（原始
  命中率 5.66% 同樣多為非 AI 假陽性，如 Samsung 裁員、Apple Music
  漲價被誤標 earnings/pricing）；60.6% 為瀰漫性非 AI 噪音，規則修
  不動。反向舉證：9 筆獨占真事件中有 6 筆為有意義訊號（HuggingFace
  資安事件 ×2、TSMC 財報、Meta AI bot 流量分析、Z.ai ARR 里程碑、
  Kimi K3 發布），但良率僅 ~0.6%（990 筆中僅 6 筆），**反向證據存在
  但強度不足以推翻預設砍**
- **36Kr AI：留**（因 iris 移除而升值）。OpenCC s2twp 轉繁驗證
  0 殘留簡體字元，fetch 端關鍵字前置過濾使命中 100% 為真 AI 事件、
  0 假陽性，明顯優於 iris/techurls 的訊噪結構。唯窗口內 4 筆命中
  100% 與 iris 重複、0 筆獨占——**這是 iris 仍在架上時的舊局面**；
  iris 移除後 36Kr 不再有更高量級同溫層源分食同一批中國科技新聞，
  其邊際覆蓋價值因果性提升，此為留下的關鍵理由，非其自身訊號
  結構改變
- **xAI/Grok 查詢詞：留，維持不動**。窗口內僅 4 筆新進（樣本過小
  無法穩定量化命中率），但全庫 21 天保留窗（29 筆）人工複查顯示
  查詢詞組精準、無過寬噪音案例

**排程健康三層架構**：全期複測通過，watchdog 由「傾向留」升級為
「確認留」（8 次代觸發 7/8 成功，唯一失敗即已知 `-R` 缺漏事件本身，
修復後 7/7 連續成功）；前端警示帶 6 小時明顯樣式全期 0 次觸發、
2-6 小時低調樣式 6 次且全數發生於心跳上線前，銜接驗證通過；內部
cron 頻率裁決維持 4 tick/hr 不降頻（見上方「已知設計事實」）。此議程
**全數關閉**，不需再排入下一輪待辦。

**個資案結案**（2026-07-27）：桌面兩份 bundle 已銷毀完成，全案結案，
不再列入待辦追蹤。

## 8/4 Claude Code Releases 來源汰除裁決（已裁決）

**裁決：移除 `CURATED_AI_MEDIA_FEEDS` 中的 `Claude Code Releases`
（`github.com/anthropics/claude-code/releases.atom`），tuple 由
15 條降為 14 條。這是**來源汰除**，不是「分類欄位修正」——曾提出
的替代方案（把它搬到 `OFFICIAL_AI_FEEDS`、改標官方分類）已被否決：
該 feed 每筆 entry 的 title 一律是純版本號（如 `v2.1.220`），不落
入六類商業事件任一類（財報/市佔/資安漏洞/價格/benchmark/模型
發布），留在架上無論標哪個分類都只會是噪音，直接下架比改分類更
乾淨。`data/archive.json` 中既有的歷史紀錄維持原值不動，不刪除、
不改寫、不回填；實際筆數以執行當下的 tracked snapshot 為準，不以本
裁決文件固定一個會隨 retention 變動的 point-in-time 數字。

**Anthropic 官方一手內容無缺口**：`official_ai` fetch task 除
`OFFICIAL_AI_FEEDS` tuple 外，`fetch_official_ai_updates()` 另外
硬編爬取 `https://www.anthropic.com/news`
（`parse_anthropic_news_items()`，賦值 `site_id="official_ai"`、
`source="Anthropic News"`），本來就持續涵蓋 Anthropic 公司公告/
產品發布層級的官方一手內容，與被移除的 CLI 版本號 changelog 屬
不同性質、不互相替代，此次移除**不產生**官方一手來源缺口。

## 已知限制
- Meta AI / DeepSeek / xAI 為第三方報導非官方一手（2026-07-19/20
  已評估 GitHub Releases 作為升級路徑：三廠皆不足——Meta/DeepSeek
  幾乎不用 Releases 機制發布模型，xAI 的 xai-sdk-python 雖活躍但
  屬 SDK 版本紀錄非模型公告，維持現狀）
- Artificial Analysis 未接入（每月手動看 leaderboard；已評估
  changelog 頁面可靜態抓取，成本中等，暫不實作）
- 繁簡混排標題理論上可能疊字（極罕見，觀察中）

## 8/21 Market Sensor 與額度政策速報（已實作，待排程樣本觀察）

- 新增 `scripts/market_sensors.py`，沿用既有排程與靜態 JSON 發布，不新增
  server、database、workflow 或 secret。
- 價格與免費額度使用獨立 state 做 deterministic old/new diff；首次執行
  只建 baseline。上游縮水超過安全門檻時不覆蓋前次 state。
- Usage policy 只監控 Usage4Claude 與 Claude Usage Monitor 公開 commit
  Atom；強詞命中才建立 `USAGE_POLICY_CANDIDATE`，不執行第三方工具，
  不接觸個人 quota 或登入狀態。
- 產品排序採雙軸：長期影響 1（價格）> 2（免費額度）> 3（usage policy）；
  時效則 3 >> 2 > 1。首頁因此把第 3 類放在獨立速報區，但所有卡片仍
  明示「待確認」。
- 前端新增「額度與政策速報」及「價格與免費額度變更」兩區；沒有事件時
  隱藏，不影響既有今日重點訊號與一般列表。
- 讀者可見的 market signal（價格、免費額度、usage policy 候選）一律只
  保留 24 小時，與主新聞及 LLM 發布雷達統一；獨立 sensor state 保留作
  old/new 比對，不會讓舊事件重回首頁。
- 後續驗收重點是 14 天候選 precision、官方確認延遲、重複率與漏報；
  未完成觀察前不擴到 issue／PR、大型 scraper 或 changedetection.io。

## 8/22 LLM 發布雷達（已實作，待排程樣本觀察）

- `data/llm-radar.json` 只保留 24 小時內的 `model_release`；價格與
  free-tier diff 全部只在既有「價格與免費額度變更」區呈現，避免雙重卡片。
- 模型證據標示嚴格分級：`official_ai` 為「官方公告」、`llm_stats_models`
  為「模型追蹤」、其餘來源一律為「媒體報導」。不更動全域評分或把媒體報導
  升級成官方確認。
- 此 lane 與七日模型分頁不同：前者強調首次可見的即時提醒，後者保留
  LLM Stats 的 atomic discovery 歷史。後續觀察模型卡 precision、重複率與
  官方來源確認延遲，再決定是否建立更嚴格的 canonical model key。
- 8/22 首次樣本發現 Free LLM APIs 一次目錄異動產生 19 筆訊號，其中
  `Retired — the model catalog is gone` 等說明文字被當作模型名稱。這批
  free-tier 結果不可視為可靠變更；需另開資料品質修正（欄位驗證與目錄
  大幅 churn gate），不可在 UI 排版調整中靜默掩蓋。
