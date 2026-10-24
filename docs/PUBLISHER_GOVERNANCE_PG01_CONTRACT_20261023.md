# PG01：發布者治理契約與驗收基線（2026-10-23）

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：階段歷史／已結案。** PG01～PG06已正式發布，最後補修（四）定稿；本頁的下一步、未通過、待推送只描述當時，不再開補修（五）。技術契約與限制保留，對照[PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)及SOURCE_COVERAGE使用。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

**PG01 完成；下一階段 PG02：GPT-6.1 Sol／High。** 本文件凍結 PG02～PG06 的實作邊界；目前尚未實作、提交或部署發布者治理。每階段結束均須交付完整交接並推薦下一階段模型與思考強度。

使用者已接受目前事件去重效果。本案處理實際發布者、來源分級及首頁用途資格；事件 matcher、根／phase 身分與時效規則保持。日報自動化與來源觀察不恢復。

## 1. 基線與可接受代價

- Git 基線 `8deab0c1b61a7560c2f552c5366b3776bc82dd51`，`master`。既有 CNBC 徽章候選三檔已封存並核對 SHA256，PG01 不修改它們。
- 正式 HTTP 固定快照：2026-10-23 **11:35:27 臺北**（`2026-10-23T03:35:27.361917Z`）。latest／stories／daily／source-status 同代；13 個公開 JSON／HTML／資產已封存。
- 當期 195 篇 AI、56 篇 Google News；Google 身分 48 identified／8 unknown。事件投影 183 根、182 有效；既有讀者熱點 10、時間線 20。
- 固定舊分數／計票欄位，只套「有核心徽章、當期材料、官方或兩發布者或 .72」的結構檢查，舊熱點 9／10、時間線 19／20 不符；從完整候選池重排也只剩 **1 則結構候選**。這尚未做來源准入、具體證據及新 tier 重算，**不是新版結果、最終數量上限或品質驗收**。
- 此門檻可能明顯減少重點數量。接受不足 10／20、甚至零則，不降低門檻湊數；一般列表仍承載較廣產業新聞。後續須量化最終變化，不用這個結構上限代替實作回測。

封存與完整交接：`/Users/lordmi/Downloads/ai-news-radar-publisher-governance-pg01-20261023/`。先讀 `HANDOFF.md`、`DECISIONS.json`、`VALIDATION.json`；`MANIFEST.json` 驗證精確檔案版本。

## 2. D01：新增身分欄位，保留既有入口身分

資料結構由 [publisher-governance-v1.schema.json](contracts/publisher-governance-v1.schema.json) 定義。PG02 只加身分資料鏈；PG03 加來源政策；PG04 才產生並消費完整資格投影。

每篇文章及公開引用新增三組有界欄位：

| 欄位 | 意義 |
|---|---|
| `ingress` | `site_id`、穩定 `source_id`、入口種類、名稱及公開 feed URL。搜尋 query 是入口，不是發布者。 |
| `publisher` | canonical `publisher_id`（可 null）、可呈現名稱／網域、`status`、`basis` 與有界公開證據。 |
| `source_policy` | 政策版本／registry revision、適用 scope、publisher_kind、准入狀態、tier／rank、一般／精選／雷達許可與原因。 |

`source`、`site_id`、原 `url`、文章 ID、日期及同源去重鍵維持既有含義。不要把 `source` 改成新媒體名稱，藉此改動分群、翻譯快取、配額或 ID。讀者來源名稱改讀 `publisher.name`，有明確 fallback；不能把缺資料的歷史稿猜補成新發布者。

私人 OPML 的入口名稱／URL／source_id 不新增到公開欄位；公開入口只標準化為 RSS/OPML。登錄表與公開證據均不得包含私人 feed、tokens、cookies 或設定檔內容。

## 3. D02：身分狀態與證據優先序

- `identified`：命中已凍結登錄表與確切 host／path／公開 bridge 規則，線索一致。只表示發布者身分可歸屬。
- `reported`：Google RSS 給出可用的 source 名稱與網域，尚無已核 canonical 身分規則；讀者可看名稱並知道由聚合方提供。
- `unknown`：線索缺失或不能形成可用名稱／網域。
- `conflict`：具體發布者線索互相矛盾；不得選擇對升級有利的一個。

直接文章 host 與有界登錄表為主要依據。僅允許已配置、真正來自 Google News 的 RSS source.title/href 作聚合方線索；任意 OPML 標籤或偽造 metadata 不具同等權限。公開 Google bridge 的固定媒體約束須核對；開放 Meta／DeepSeek／xAI query 沒有廠商身分權威。

標題尾綴只用既有允許名單作較弱相容線索。RSS 網站首頁不可寫成原文 URL；`publisher.article_url` 只有原 URL 已是原文或既有封存有正常確認證據時才填，否則維持 null 並沿用可點擊的 Google 連結。PG02／日常刷新都不新增逐篇跳轉或全文請求。

host 使用 IDNA／大小寫／尾點正規化、明確網域邊界、最具體 host／path 規則；不信任 userinfo、非 http(s)、字串包含或任意 github.com。私有／本機網域不提供公開身分權威，也不因此發送請求。上限與安全字串詳見 schema。

feedparser 與 XML fallback 必須同樣保留 source metadata，通過 RawItem meta → 公開安全欄位 → archive／latest → stories refs／事件 refs → daily／雷達。只補 parser、卻在公開安全欄位白名單丟掉資料，不能算完成。

## 4. D03：身分、佐證與准入分開

`publisher_id` 供身分與顯示；`corroboration_key` 維持既有有界發布者／群組口徑。本輪不自動擴充計票字典；補八個名稱不會讓它們立即有票。AIBASE／36Kr／橘鴉保留 `cn_aggregator` 一票的限制；新身分欄位不拆群組。

新增 RSS 證據若明確推翻舊鍵，必須撤為 null 並記 conflict，不保留已知錯誤歸屬；這可能降低既有計數，須列差異。允許撤回錯票，不新增正向計票映射，也不藉此改事件配對。

既有 `corroboration_count`、raw 引用與事件成員保留原意。新增 `qualified_source_count` 是**當期、通過准入與用途、具合格事件材料的既有非空 corroboration_key 唯一數**，必須是原當期鍵集合的子集。新來源准入若另需擴充計票鍵，須另列決策與回歸，不能藏在 metadata 修復中。

已辨識但未審應顯示「未審」，不能繼續把計票為零一律解讀成「不知道發布者」。多方只表示不同合格發布者／既有群組；不用「已驗證」或「獨立查證」描述票數。

## 5. D04：來源政策與初始裁決

正式單一政策表預定為 `config/publisher-policy.json`，PG03 建立，Python 為權威、JavaScript 消費已算結果。PG01 的 `SOURCE_POLICY_MATRIX.json` 是凍結的種子／範圍裁決，不是已啟用配置。

| 准入狀態 | 作用 |
|---|---|
| `approved` | 明確發布者及允許範圍，保留已核既有 tier／rank；每篇仍須過範圍／證據要求。 |
| `limited` | 明列 host、path、用途或稿件類型；不向其他子站或用途擴張。 |
| `unreviewed` | `watchlist`／rank 6／現有 importance 0.3；一般列表依文章規則，精選與雷達預設 false。 |
| `excluded` | 該範圍不進公開新聞；archive 與理由保留，不能刪除歷史。 |

既有 39 新聞入口保留，代表輸入路線持續可用，不代表開放 query 的所有動態媒體已准入。configured 單一媒體按原有明確範圍承接許可；僅存在於 corroboration 的 SUFFIXES／HOSTS，不等於曾通過來源品質准入。

保留 iThome／The Decoder rank 1、數位時代 rank 4、RuntimeWire rank 4、Reuters／CNBC／The Information rank 2 等既有裁決。相同已審發布者透過不同公開入口應得到同一政策；原有明示用途／路由限制優先。

新政策每輪從當次 registry 重算，不能信任 archive 內過期的准入結果。以既有 claim／事件管線先形成固定輸入，再在公開 reader 副本及用途投影套 effective tier；公開 `source_tier*` 可在輸出副本更新，archive／matcher 用的舊來源排序不回灌新分級。若共用 `source_tier_for_record` 會改事件 ranker 或同源選版，先分離用途層，不能直接全域換函式而造成去重變動。新增顯示身分本身不改 reader 配額。

開放 query 本身無 publisher tier，單篇按實際發布者／範圍取政策。未知、衝突、無法核對的舊子站均採未審預設，取消 curated_media 父層 rank2 繼承。

數位時代主站的有限准入不自動覆蓋 Meet／未來商務等子站。名稱可歸同一媒體家族，計票仍遵守既有群組，但用途須獨立核對；不因母站保留就放行全部子站，也不整站封鎖數位時代。

八家新見媒體均先 `unreviewed`：Latin Times、Android Headlines、AI Insider、New York Post、Wccftech、FEDagent、SCMP、Computing UK。PG03 可用既有公開證據做具理由的單家裁決；不足就維持未審完成本案。FEDagent 單篇有官方佐證不等於整站升級；403／robots 不直接等於低品質。

LLM Stats 保留模型追蹤用途與 watchlist，不能因允許雷達而取得一般精選許可；橘鴉為人工對照，不加入新聞排名。AIBASE、36Kr、LLM Rumors 等有限用途須遵守既有範圍，沒有整批升級。此前封存八個候選與 free-tier 退役不變。

## 6. D05：文章範圍與核心事件材料

一般列表維持 AI／產業與 24h 收錄規則；未審來源不是自動拒收理由。活動宣傳、泛建議、教學等明確不符範圍者排除。PG04 在既有收錄之後增加有證據的用途資格層，不改共享 AI relevance 分類或 .65 地板；不為處理 Meet 個案加入文章 ID／URL 黑名單。

核心材料只取原始標題／RSS 摘要／已保存引用，不取翻譯或生成摘要當證據。`supported` 代表公開材料明確支持該事件分類，**不是事實獨立查證通過**。缺資料用 `insufficient`，矛盾用 `conflict`，非核心用 `not_core`。

| 類型 | 最低可追溯具體材料 |
|---|---|
| earnings | 明確公司、財務期間／財務動作與具體數據；泛成長建議不算。 |
| market | 明確併購／監管／停運動作，或帶時間、母體及數據的市占變化；特定平台流量不可擴成全球市占。 |
| security | 受影響產品／元件、具體問題及風險／影響，且有廠商／研究者原始技術材料或具方法證據的合格技術報導；CVE非唯一條件。只有社群示範的二手轉述、未讀正文或無關連結不足。 |
| pricing | 明確產品／方案、價格或條件變更與適用範圍；文章提到價格不算。 |
| benchmark | 明確模型、基準／方法及結果；不可把一般評論或歷史排行提及當今日新評測。 |
| model_release | 明確完整模型、發布／可用動作與狀態；預測、傳聞或順帶提及舊模型不算。 |

資格層須提供來源欄位、可核對 span／已保存 URL 及 reason codes；不能只輸出模型判斷而無依據。不得新增每篇遠端 LLM／跳轉／正文工作來達成門檻。

## 7. D06：首頁用途與門檻

### 一般列表

維持既有合格新聞、24h 與限量，並套來源範圍排除。未審可進一般列表並標示；身分 unknown／conflict 不取得精選資格。原始引用持續保留。

### 今日重點訊號

熱點／時間線／各分類／查詢共用同一後端結果，按下列順序：

1. 事件投影有效，原 `eligible` 為真且 `effective_at <= asof < expires_at`。
2. 有當期 `active_phase`、來源身分 `identified`、來源狀態 approved／limited 且 allow_featured 的文章。
3. 其中有符合範圍、材料 supported 且對應六類核心事件的文章；past_phase／context_unknown 不替當期取得資格。
4. 以下其一成立：同事件的合格官方一手主文；`qualified_source_count >= 2`；合格主文 `featured_score >= 0.72`。
5. 合格主文及支持證據沒有阻擋衝突。其他未審／衝突引用不污染合格主文，亦不能提供票數或徽章。

官方例外僅限主文自身為登錄的官方原文／明確官方 bridge，且材料與事件對應。未審媒體附一個官方網站首頁，不構成官方例外；沒有原文材料就保守維持一般列表。

取消無徽章補位；不足可零則，不顯示較低資格替代稿。只有一則時沿用既有切換規則，可只顯示時間線，不強迫呈現兩種 view。

`featured_score` 使用現有 importance 公式與權重、scoped tier、原事件 effective_at 代理發布時間、固定 asof、qualified_source_count；不使用未審引用提升熱度。不覆寫原事件 score。

合格主文由合格文章按 `(-featured_score, tier_rank, article_id)` 穩定選擇。展示名稱、標題、連結、核心徽章及分類篩選均用這份用途材料；查詢／來源篩選不得借其他不合格引用取得席位。完整參照仍保留作閱讀。

生成摘要只有在原摘要主文 ID 等於 featured_primary_article_id 時沿用；否則省略。精選排序保留既有熱度／時間與多樣性規則，但讀用途分數、合格計數及用途主文的發布者鍵；不按 Google query 名稱分配多樣性席位。AIBASE 等佐證群組不因此變成多票。

### 模型雷達與獨立元件

LLM 雷達／model_releases_24h 先核用途許可，再沿用既有模型證據／24h／型號允許名單。LLM Stats 仍標模型追蹤，媒體仍標媒體報導，不冒充官方。沒有資格版本或身分衝突的新聞不得從雷達繞入首頁。結構化價格、兩 canary 與原健康判斷獨立保留。

## 8. D07：加法投影、相容、發布與回復

在 `stories-merged.json` **頂層**新增 `publisher_governance`，schema_version=1、policy_id=`publisher-governance-v1`；不用既有 additionalProperties=false 的 brief_events 頂層承載新 envelope。brief-events v1 schema、matcher version、state schema 不改。

投影綁定 parent generated_at、brief_generation_id、brief_state_revision 與 registry_revision。articles 包含所有事件參照的唯一文章 annotation；events 與原事件一一對應，另列 featured_event_ids／daily_selected_event_ids。各事件帶 active_phase_id、featured_eligible、reason_codes、qualified keys/count、支持文章、用途主文／分數／徽章／可用摘要。

registry_revision 為政策物件移除自身 revision 欄位後的 canonical JSON SHA256；投影 generation_id 為公開安全處理後、移除自身 generation_id 的 canonical JSON SHA256 前24hex加 `pg1_`。canonical 採 UTF-8、sort_keys、ensure_ascii=false、separators=(comma, colon)，不含縮排。兩者均不得使用當次執行時間隨機產生版本。

PG04 可將原 brief_events 的 `selected_event_ids` 改為同政策的 daily 選集，再用既有方法重算 brief generation_id；只改選集，不改事件根／成員／phase／時間。之後才將此最終 generation_id 綁入治理投影，避免循環雜湊。daily 的 items、brief_event_meta 與選稿診斷必須和最終選集一致，不能留舊 meta 描述另一套入選稿。

資料無效、重複 ID、跨代、缺 annotation、非當期支持、對不上的主文／摘要、未知政策版本、容量超限，都不能導出精選資格。單篇缺原 metadata 是合法 unknown，不等同整份格式損壞。只為同代載入不做跨檔時間拼接。

投影最多 10k events、100k article annotations、8MiB；超界明示 unavailable，不截掉證據後仍標 ready。既有事件歷史容量／推送競爭保護照舊。每日公開 daily-brief 是同政策的相容選集，不恢復私人日報。

前端只接受支援且完整綁定的資格投影；缺失時重點提示不可用，普通列表仍可用，不回退舊「有徽章即過」。同頁快取只可在無更新 registry revision 的訊號時使用原同代、同 policy/revision、未逾期資料；一旦收到新 revision 或明示 unavailable，不再展示舊 revision。到期仍沿用本機 timer，不加請求／排程。

同頁已見較新的 generated_at／revision 後，不接受較舊時間的政策覆蓋；同時間卻不同 revision 視為混版，保守停用重點。不同檔案的政策 revision 不一致時也不能拼裝資格。

PG06 發布順序：保留遠端 bot 提交 → 後端／registry 先部署並由既有刷新產生綁定完整資料 → 核對 ready 與影響 → 前端與共同資產版本 → CI／Pages／HTTP／真 Chrome。前端提早到、資料較晚到時可短暫沒有重點，不能偷用舊 gate。PG01～PG05 不推送或 dispatch。

回復演練使用 Downloads 副本。正式回復若後端不能供應新版資格，前端維持保守不可用、普通列表可用；不得把來源未審自動重新授予精選資格。可回復展示實作但保留 policy gate；不恢復舊資料時間、事件 state、日報、觀察或 free-tier 分支。任何更改凍結政策須新 revision 與明列決策。

## 9. D08：驗證隔離與完成標準

既有 72 protected、448 validation 預留與六個 CN 模型家族邊界延續；不批量顯示其新聞內容，不使用保護稿調參。當期新稿按同家族／URL／版本閉包繼續隔離。已曝光來源調查個案僅作開發回歸，不能宣稱獨立 precision。

PG01 的 synthetic cases／schema 正反例／固定資料結構檢查只驗契約一致性，**不是 runtime 已通過**。PG02～PG04 須把預期轉為真實程式測試；PG05 完整 Python、JS、固定 14 日重播、所有新進／退出重點的允許審查案例、真 Chrome 桌面／手機與混版／回復。

同一 claim 集合／state／asof，事件根、成員、phase 與時間必須保持；來源 tier 的變化可能改 reader 入選集合，須與事件配對變化分開。若 ranker 會改原主文／state evidence 順序，先解耦用途排序，不能藉本案重設事件歷史。舊 source／URL／IDs 不改；兩筆 CNBC 引用保留、一枚徽章。所有 source／rank／席位差異須有理由。

PG01 出口：契約、schema、來源種子矩陣、案例預期、混版／回復、基線及影響限制、隔離與完整 manifest 已驗。PG02 入口為本契約及 Downloads/HANDOFF；先驗 manifest、三檔 CNBC 候選與 runtime 基線，完成身分鏈後停下並推薦 **PG03：GPT-6.1 Sol／High**。
