# AI 商業情報儀表板 — 交接摘要（截至 2026-07-21）

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
   `docs/OPERATIONS.md`「翻譯管線」章節；專屬 pytest 約 37 案例
10. 資料時效警示帶：前端讀 `generated_at` 與瀏覽當下比較，2 小時內
    不顯示、2-6 小時低調樣式、6 小時以上明顯樣式，門檻常數化
    （`STALE_DATA_WARN_HOURS`/`STALE_DATA_BAD_HOURS`）
11. 重點訊號區資格閘門：`featuredCandidatesGate()` 前置過濾（不重排，
    既有徽章優先四級排序 `boleStorySortCompare` 不動）——徽章
    （`business_events` 非空）直接入選；無徽章僅在非
    `COMMUNITY_SOURCE_TYPES`（iris/waytoagi/followbuilders/aibase/
    hackernews/zeli）來源時才能補位，寧缺勿濫不硬湊。**未做**地板值
    排除：後端分數已被 `max(score, 0.65)` 覆寫，前端 JSON 無欄位能
    可靠區分真實分與地板值，判斷不可行後只做源類型排除（已回報此
    限制，非遺漏）。掛在 story-pool 與 no-story-data fallback 兩條
    候選池入口
12. 前端死代碼清理：`HN熱議` 分頁/計數器整組移除（背後 hackernews/
    zeli 抓取器已於 07-14 源置換移除，此為孤兒 UI，非過濾結果）；
    07-21 補一批同型殘留——`sourceSignal()`/`sourcePriority()`/
    `clusterBoleEvents()` 內的 `HN熱議`/`GitHub趨勢` 判斷分支同理
    清除（`clusterBoleEvents` 家族經 `renderBolePicks()` →
    `rankedFallbackRows()` 仍有存活呼叫路徑，故只清殘留字串，不構成
    整組退役）
13. **7/21 四源審判裁決**：`iris`（Info Flow）、`techurls` 自
    `collect_all()` 任務列表移除（`fetch_iris()`/`fetch_techurls()`
    原始碼保留供回滾，比照 07-14 源置換慣例）；`36Kr AI`、xAI/Grok
    查詢詞（curated_media 內）維持不動。裁決依據見下方「已知設計
    事實」與 `docs/SOURCE_COVERAGE.md`「2026-07-21 Four-Source
    Trial」章節。`AGGREGATOR_BACKDOOR_EXCLUDED_DOMAINS`（v2ex.com）與
    `SOURCE_TIER_BY_SITE`/`SOURCE_ECOSYSTEM_GROUPS`/前端
    `COMMUNITY_SOURCE_TYPES` 內殘留的 iris/techurls 條目均比照既有
    慣例保留不動（前者為網域鍵值非來源專屬，後兩者為移除後自然
    失效設定，非本輪範圍）。移除後已手動觸發一輪排程並驗證
    `data/archive.json` 內兩源新流入（`first_seen_at` 晚於部署時刻）
    皆為 0，`data/source-status.json` 亦不再出現任一源
14. 內測回報管道文案上線：頁尾新增引導至 GitHub Issues 的說明文字
    （`.app-footer-note`），沿用既有頁尾樣式
15. **7/21 重點訊號區來源多樣性上限（N=2,僅退化層生效）**：診斷
    （`.claude-reports/2026-07-21-aibase-signal-area-diagnosis.md`）
    定位 aibase 佔重點訊號區 39.5%（近期 66%）之成因——非品質問題，
    而是絕大多數合格候選為單源（`storyHotScore=0`），
    `boleStorySortCompare` 前兩層（徽章、熱度）恆平手，勝負落在
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
    `.claude-reports/2026-07-21-featured-diversity-cap.md`

## 已知設計事實（避免重複調查）
- 收錄門檻 = ai_relevance ≥ 0.65；六類只主宰重點區排序，非收錄條件
- ai_relevance 有 has_ai 地板值 max(score, 0.65)——上游設計，
  動它需 14 天回測（治理規則），未動；聚合器條目多靠地板值過關，且
  此覆寫使前端無法回推真實分（見「重點訊號區資格閘門」的地板值排除
  限制）
- BRIEF_SCORE_GATE/daily-brief 原始排序不影響使用者所見
  （調查結論在 story_passes_brief_gate() docstring）
- `renderBoleBrief()` 是死代碼；另發現同批未被呼叫的死代碼：
  `pickBoleItems()`、`clusterBoleEvents()` 的獨立呼叫路徑、
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
- `SOURCE_KINDS` 的 `aihubtoday`／`aibase` label 由「AI站點」改為
  「AI網站」（2026-07-21，`fix/retire-category-v2-0721`）：純語言規範
  修正，「站點」為中國大陸用語，違反本站 zh-TW 用語規範；「網站」為
  對應臺灣用語，語義不變。僅改 label 字串，`tone: "aihub"` 與其他
  site_id 不動
- `SOURCE_KINDS` 的 `opmlrss` label「OPML」對一般讀者是技術縮寫，
  可理解性存疑（2026-07-21 隨上一項一併檢視時發現，**本輪不改**）：
  `opmlrss` 目前屬進階層 site_id，實際曝光範圍（是否觸及一般讀者
  可見的預設層卡片）未經證實，貿然改字可能是無的放矢，也可能改壞
  已熟悉「OPML」一詞的進階使用者的預期用語，留待獨立工單評估曝光
  範圍後再裁決是否修改
- 測試基線：240 pytest
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

## 待辦檢查點
- 【最高優先】archive.json 容量治理：現況約 52-53MB（已超 GitHub
  50MB 軟上限、push 時會印警告，遠低於 100MB 硬限）；21 天保留窗對
  「反覆被抓到的舊條目」形同虛設（last_seen_at 會被刷新）。
  2026-07-16 量測顯示淨縮小，判讀為初始匯入積壓正隨保留窗退場的
  過渡期、非穩態，現有資料不足以外推撞上 100MB 的日期。**2026-07-21
  裁決：不做手動清理，維持自然 21 天窗淘汰機制至 ~2026-08-04 複測**
  ——理由：50MB 為軟上限不擋任何操作，現在清理會污染複測所需的
  自然演化曲線，與既有「資料不足以外推、需持續量測」的方法論矛盾，
  手動清理只會讓下次複測看到失真的人為斷點。title-zh-cache.json
  為第二個成長型檔案（無 prune 機制，目前約 4.4MB，成長速率低但零
  治理，長期仍列待辦）
- PAT 到期追蹤：外部心跳用的 fine-grained PAT 約 **2026-10-17**
  前需續期（90 天效期），續期步驟見 `docs/OPERATIONS.md`「External
  heartbeat」章節
- 財經查詢擴充（GNews AI 概念股+財報詞）：**否決關閉**——重點訊號區
  已於資格閘門上線時選定「寧缺勿濫」為取捨（供給不足寧可顯示較少
  條數，不擴大信源換取湊數），供給面擴張的迫切性降低；查詢詞組
  設計與三廠 GitHub Releases 評估已完成唯讀評估（結論：三廠 Releases
  皆不足以填補官方一手空缺），changelog 缺口改在 8 月中複評時視情況
  升值重提，不在本輪動作
- 個資案已結案，僅剩桌面兩份 bundle 到期銷毀（追蹤銷毀完成即可關閉
  此項）

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

## 已知限制
- Meta AI / DeepSeek / xAI 為第三方報導非官方一手（2026-07-19/20
  已評估 GitHub Releases 作為升級路徑：三廠皆不足——Meta/DeepSeek
  幾乎不用 Releases 機制發布模型，xAI 的 xai-sdk-python 雖活躍但
  屬 SDK 版本紀錄非模型公告，維持現狀）
- Artificial Analysis 未接入（每月手動看 leaderboard；已評估
  changelog 頁面可靜態抓取，成本中等，暫不實作）
- 繁簡混排標題理論上可能疊字（極罕見，觀察中）
