# A03來源裁決與A04實作規格（2026-10-22）

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：方案A已結案／階段歷史。** A01～A06已完成正式發布與驗收；下方待複核、待推送與下一步只記當時狀態。裁決及未完成品質限制仍保留，不重啟來源觀察。見[A06](SOURCE_GOVERNANCE_A06_RELEASE_20261022.md)及後續[PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

**A03：done。下一步A04（S06）：GPT-6.1 Sol／High。**
使用者授權「執行a03」，本階段完成裁決及實作交接；尚未改正式程式、生成資料、提交或推送。
本文件接續[A02評估](SOURCE_GOVERNANCE_A02_ASSESSMENT_20261022.md)，並依[方案A](SOURCE_GOVERNANCE_EARLY_CLOSE_20261022.md)縮小收尾範圍。
完整53筆逐來源裁決、原證據引用、驗證與交接在Downloads：
`/Users/lordmi/Downloads/ai-news-radar-source-governance-a03-20261022/`。
本頁的「退役／修正」均是A04待實作決策，不代表已部署。
使用者暫停後已授權續接；最後12項完整性／狀態檢查通過，REPORT／HANDOFF／CHECKPOINT及manifest完成封存。
這些檢查只驗A03交付完整性，不代替A04程式回歸、來源品質或七日可靠性驗收。

## 裁決與可接受的損失

| 議題 | 本輪裁決 | 代價／限制 |
| --- | --- | --- |
| D01 重複佐證 | 必修。同發布者的多版本、跨入口副本只提供一次計數；保留所有文章引用，後端與前端一致。 | 部分故事熱度、分數、排序與內部brief資格會降低；這是移除虛增訊號，不能宣稱首頁少了同等數量事件。發布者不同亦不證明內容獨立或事實正確。 |
| D02 教學／指南 | 本輪不改文章篩選，不整站刪數位時代或xAI查詢池。已知誤收作結案限制保存。 | 教學／常青指南／幣價預測仍可能誤收；沒有通過完整規則驗收，不能稱噪音已解決。 |
| D03 基礎設施漏收 | 本輪不改共享AI分類、語意gate或0.65門檻，不加品牌白名單。 | NVIDIA及iThome的已核漏收保留；TorchTPU有其他入口，不能稱全站缺席。沒有重開長期觀察的待辦。 |
| D04 免費額度感測器 | 必修：單獨退役自動`market_free_tier`分支，保留價格及兩個canary。 | 不再由該資料集自動偵測免費額度／rate limit異動；沒有已驗等價替代。一般新聞仍可能報導，但不是結構化替代服務。 |
| D05 既有來源 | 39新聞入口、OPML池1、人工對照1均保留，維持分級與限量。Reuters／CNBC／The Information維持rank 2。 | 保留目前覆蓋，也保留已知品質限制；這不是逐站品質通過或零維護成本保證。 |
| D06 新候選 | 臺灣5站及Cloudflare／Modular／Zed共8站，本輪不准入並封存。 | 可能放棄尚未證明的新增事件／證據；不把未知收益寫成零，不判定來源永久無價值。無採樣、提醒、Email或新排程。 |

53筆合計：**44保留、8本輪不准入封存、1待退役**。44包含39新聞、OPML1、對照1、正常感測器3，不能當44個獨立新聞發布者。
逐列證據與損失見本目錄所列Downloads的`SOURCE_DECISIONS.jsonl`與`SOURCE_DECISIONS.md`。
所有候選准入仍不成立；不是降低七日、N≥20或品質門檻後通過。A02的200個開發樣本未通過保守85%與未知≤5%要求。
沒有進行共享分類修改，因此本次不以補做分類實驗作結案依賴；未來若另行授權修改，原14日正負例回測及獨立留出要求仍適用。

## B01：發布者計數修正

### 欄位與相容性

採新增明確欄位的最小遷移，避免把原始篇數悄悄改義：

- `source_count`、`item_count`、`sources`、`items`維持原始引用／成員口徑及全部內容；不是獨立佐證數。
- 新增`corroboration_count`：同一故事中可辨識發布者／既有聚合群組的唯一鍵數，允許0。
- `duplicate_count`保留為相容別名，值為`max(1, corroboration_count)`；新後端與前端決策皆讀新欄位，不再以原始引用數替代。
- 為讓前端非story的合併路徑共用口徑，由後端在當期文章與story引用加上`corroboration_key`（已辨識鍵或null）。前端只去重鍵，不複製一套發布者推測規則；不得把來源顯示字串直接當鍵。
- 鍵是公開發布者／既有群組身份，不能包含私人feed名稱、OPML設定、追蹤參數或憑證。不得回寫歷史archive來假裝當時已知；當期輸出可由凍結內容重新計算。
- 缺新欄位的舊JSON：先用可用的新鍵集合；仍無法得知就當0，不以舊`source_count`、`duplicate_count`或合併篇數升級。允許短暫保守排序，沒有版本混用期間的假多源標籤。
- 前端0表示「來源待辨識」而非0篇文章；原始引用仍可閱讀。缺欄位、null、負數、小數、字串與非有限值要有一致保守fallback。

### 身份判定優先順序

1. 優先保留既有`cn_aggregator`群組規則：AIBASE（含curated_media別名）、36Kr、橘鴉共一票。已辨識為同發布者的跨入口副本同樣合併。
2. 已設定的單一發布者入口用明確映射；OpenAI News／Codex Changelog／Skills同鍵，Google AI／Gemini／DeepMind／Cloud Blog同鍵，GitHub AI & ML／Changelog同鍵。NVIDIA等已知別名同鍵。
3. Reuters、CNBC、The Information、Wired等不同發布者各自一鍵，不能用`curated_media`或`official_ai`這種父層site_id合併。沿用既有群組之外，不在本輪研究或推論法律母公司關係；稱發布者計數，不能宣稱法律或採訪獨立。
4. Reuters／The Information／Google Cloud等限定站點的Google News入口可用已配置的發布者映射，但若單篇明示相反發布者則視為衝突。Meta／DeepSeek／xAI等主題查詢不是官方發布者；Epoch入口若缺單篇明確線索亦保守不計。
5. OPML跨入口只依已發布的文章URL（已知發布者host）或可核的同稿身份合併，不讀私人feed映射、不把任意OPML標籤當可信身份。Google opaque URL不解碼、不發請求；既有原始標題尾綴僅在確切允許名單且無衝突時提供有界身份線索。
6. 直接host僅限已知映射（exact host或明確子網域邊界），不憑任意域名／github.com／news.google.com算獨立來源。來源標籤、原始URL與尾綴互相衝突時設null並記診斷，不能挑有利版本。
7. 未知不增加票數：全未知→0，Reuters+未知→1，Reuters兩篇+CNBC→2。單一來源仍可依原分數門檻進brief；未知不影響文章本身收錄資格。

A04須將採用的確切別名／host對照與依據列入變更及測試；可沿用A02公開身份線索作開發起點，但不得直接把A02分析函式當已驗生產resolver。
不得為完成映射增加來源抓取、跳轉解析、帳號或外部服務。未知維持未知即可交付。

### 所有受影響消費端

- `scripts/update_news.py`：`_source_group_key`／群組計數、`choose_primary_story_item`、`calculate_item_importance`、`build_story_record`、`story_category`、`story_reasons`、`story_passes_brief_gate`與選稿診斷。
- 新計數用於熱度、理由與多方門檻；importance既有權重、0.72分數門檻、AI分類／0.65及來源rank維持。不能只改`duplicate_count`卻讓brief繼續讀raw `source_count`。
- `assets/app.js`：`storySourceCount`、`storyToBriefRow`、`rowSourceCount`、`clusterBriefEvents`、`headlineClusterScore`、`itemTagLabels`、`buildTopStoryCard`，以及熱點／時間線使用的熱度與排序。
- `mergedCount`只描述真實合併篇數；不得再以它加多源分、顯示多源標籤或宣稱有companion sources。移除以篇數獲得的`mergeBoost`，保留來源品質與時間等非重複因子。
- 多方標籤採「多方報導」，不用「多源驗證」暗示事實已核實。標籤／熱度／展開引用必須一致，但引用總數可大於發布者數。
- 不改事件聚類、canonical URL選擇、文章篩選、來源優先級或多樣性cap。主文可能因修正熱度而變更，必須列出並解釋；不能以保留舊錯分達成快照相等。
- 全repo搜尋兩個舊count欄位的消費端，清楚區分原始引用統計與佐證用途；私人日報仍退役，不為配合欄位而恢復其工作流。

## B02：單獨退役免費額度自動分支

- `run_market_sensors`不再請求`FREE_TIER_URL`或執行自動free-tier diff；預設及排程路徑都不可再重試。保留純解析／安全驗證函式及既有防線作歷史／離線回歸，不建立替代服務或開關工程。
- 活躍`statuses`移除`market_free_tier`，不偽造ok、不當成本輪失敗／持續失敗；以治理及維運文件明列退役。其餘三個感測器照常報實際成功或錯誤。一般健康史規則不為此放寬。
- 原`state.free_tier`原樣保留；不清baseline、不更新其觀察時間、不製造全部provider移除事件。頂層state時間只能代表其他當輪工作，文件不把它解讀為free-tier新鮮度。
- 目前公開signal payload排除已退役分支的既有`free_tier`事件，避免繼續呈現為當期服務；原payload須先封存於A04 Downloads，歷史state／Git紀錄保留。這是退出讀者清單，不是上游供應商真的取消服務。
- 價格及兩canary的fetch、比較、保留窗口與失敗隔離均維持。公共新聞中的價格方案報導不受此退役影響。
- 更新README中英文、SOURCE_COVERAGE、OPERATIONS及實際前端區名／空狀態，清楚呈現現行價格偵測，不再宣稱自動覆蓋免費額度。改動限於受影響描述，不重新設計整個產品。
- A04以固定回應／禁止FREE_TIER_URL的fake session驗收；不需要真來源probe、帳號或secret。

## B03：候選封存與停用發布包

八個候選全部`not_admitted_closed`；沒有觀察待辦，保存原有限樣本、錯誤與未知。不得重啟兩實驗或重寄結案信。
兩實驗workflow已外部停用；A01本機`config/tw-source-observation.json`為false，遠端Git目前仍true，留A06同步。
保留原始enabled=true plan與artifact hash供查核，不能用新false plan核舊manifest。七日可靠性與正常七日自停仍未驗收。
本批只整理治理文件／現有false差異，不刪觀察程式、不新增schema遷移或清理歷史資料。
公開Radar刷新／watchdog／Pages及公開daily-brief保留；私人日報由使用者在Web Chat要求文檔，D00維持退役。

## A04驗收與拒絕發布條件

| 檢查 | 必須證明 |
| --- | --- |
| 身份與計數 | 同Reuters 5／3／2、Wired2各計1；同發布者跨入口1、Reuters+CNBC2、既有cn群組1；全未知0、已知+未知不加票；衝突／相似域名／主題品牌不誤辨。所有原引用保留。 |
| 後端選稿 | 重播D1完整管線；原192個AI ID與183個故事成員集合不變，計數／分數／主文／排序／brief差異逐故事列出。兩個已知Reuters案例不能再靠虛增來源通過；0.72單源路徑及已知不同發布者路徑仍可用。不得把純計數診斷分數硬寫成完整重播預期。 |
| 14日影響界線 | 固定同錨點資料離線比較所有受影響count與score；文章AI判定及來源集合不得改。保護留出只做不展開內容的機械比較，不能消耗或聲稱通過獨立分類驗收；可讀解釋用既有開發案例。 |
| 前端 | 用真實call chain驗brief+merged聯集、熱點／時間線、非story合併、排序及來源展開；多版單發布者無多方標籤／篇數加分。新舊JSON混用與unknown顯示驗收；記錄實際讀者清單差異，不拿內部brief差額代替首頁損失。 |
| 感測器 | free-tier網路請求0、活躍狀態／失敗數不含退役分支、原baseline內容hash不變、新舊free-tier事件不流入當期payload、無假大量移除；價格合法變化、兩canary去重與單分支失敗照常。 |
| 回歸與產物 | 先相關測試，最終完整Python套件（共享生成／schema／評分變更）、py_compile、node --check、git diff --check。輸出一律Downloads，檢查source-status、AI列表、merged、daily-brief、market-signals與state；不覆寫tracked snapshots作驗證。 |
| 發布邊界 | A04不push、dispatch或寄信。兩實驗仍停用、觀察config false、D00退役；A05審確切差異，A06另依發布授權同步與驗真。 |

最終A04應具備：逐批diff、必要新回歸、全套結果、D1及14日機械差異、受影響前端驗收、source-status與感測器狀態比較、回復說明及A05交接。
若測試失敗先修本批；無法在邊界內修妥則明列該批未完成並阻擋該批發布，不恢復七日觀察或把它悄悄移出必修清單。
B01即使不改AI分類仍改共享評分與schema，因此不能免完整回歸；原分類品質門檻沒有通過，也不冒稱通過。

## 批次順序與回復

1. A04先讀本文件與Downloads HANDOFF，驗A03 manifest與現有差異；以目前HEAD加既有未提交差異作基準，不reset或覆寫P01～A03成果。
2. B01先改後端／前端計數，同批完整驗收；B02獨立退役感測器並驗收；B03同步文件與現有停用包。每批分開保存差異與證據，不要求先commit。
3. B01、B02可獨立撤回，逆序B02→B01；只反向套用該批patch，不用git reset／整份覆蓋。既有A01 false與實驗停用不隨行為回復撤回。
4. free-tier退役後若正式回復舊code會重啟壞分支；發布事故應優先只撤B01，保留B02退役。如果B02自身有問題，採局部前修或保留停用的回復候選，不能以回復為由重新抓取。
5. 發布時code與生成JSON／asset版本需一致，舊JSON採上述保守fallback；A06若需回復，使用A05審過的版本並重新生成／部署，不能只換程式保留不相容新資料。
6. A06之前先唯讀比較遠端差異；遠端bot的data提交須保留，不能force push。最後再確認兩實驗及D00未復活。

此裁決讓本輪可以完成明確缺陷修正與實驗結案，仍承認誤收、漏收、新源可靠性及獨立事實品質未解決。
沒有自動重開條件或延後提醒；日後要擴大規則／來源範圍，需另一次明確需求。

下一階段選GPT-6.1 Sol／High，是對上述跨後端、前端及回歸工作的建議；官方模型頁列出High支援，並非保證任務成功或自動切換模型。
[OpenAI Docs模型頁](https://developers.openai.com/api/docs/models/gpt-6.1-sol)。

## 53筆裁決名冊

完整數據、未知與逐列引用見Downloads SOURCE_DECISIONS.jsonl。以下保留可隨正式版本發布的裁決；所有runtime變更仍待A04。

| 來源／入口 | 裁決 | 理由 |
| --- | --- | --- |
| aibase | 保留 | 保留聚合覆蓋及既有cn_aggregator限制；與36Kr／橘鴉同一群組不增加佐證票。 |
| arc_prize | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| curated_media/cnbc_technology | 保留 | 保留rank 2；缺逐篇調級依據，與Reuters同父層site但為不同發布者。 |
| curated_media/deepseek_news | 保留 | 保留第三方主題覆蓋；不是DeepSeek官方，未知發稿者不增加票。 |
| curated_media/epoch_ai_news | 保留 | 保留既有研究入口；低量／未知不是移除依據，單篇發布者仍需明確身份線索。 |
| curated_media/marktechpost | 保留 | D1讀者4筆、固定樣本scope {'TP': 3}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| curated_media/meta_ai_news | 保留 | 保留第三方主題覆蓋；不是Meta官方，未知發稿者不增加票。 |
| curated_media/reuters_ai_news | 保留 | 保留rank 2及入口；修正已核5／3／2版本過度計數，不將Google News整桶升級。 |
| curated_media/techcrunch_ai | 保留 | D1讀者8筆、固定樣本scope {'FP': 1, 'TP': 8, 'U': 2}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| curated_media/the_decoder | 保留 | D1讀者10筆、固定樣本scope {'TP': 8, 'U': 1}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| curated_media/the_information_news | 保留 | 保留rank 2與既有Google News入口，不繞付費牆；缺逐篇調級依據。 |
| curated_media/the_verge | 保留 | D1讀者5筆、固定樣本scope {'TP': 3, 'U': 4}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| curated_media/xai_grok_news | 保留 | 保留主題查詢入口；幣價預測／指南誤收確實存在，但缺安全規則驗收與完整覆蓋損失，D02本輪不實作。 |
| juya_daily | 保留 | 保留人工對照用途，排除正式新聞品質主分母；維持cn_aggregator既有規則。 |
| kr36_ai | 保留 | 保留現行cap5；D1有效限量，raw量與樣本多U不足以整站刪除。 |
| llm_rumors | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| llm_stats_models | 保留 | D1讀者0筆、固定樣本scope {'TP': 1}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| mcp_blog | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| mistral_news | 保留 | D1讀者1筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| official_ai/anthropic_news | 保留 | D1讀者0筆、固定樣本scope {'TP': 1}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/aws_news | 保留 | D1讀者0筆、固定樣本scope {'TP': 3}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/github_ai_ml | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/github_changelog | 保留 | D1讀者0筆、固定樣本scope {'TP': 1}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/google_ai_blog | 保留 | 保留官方入口；與其他Google發布管道共鍵，與OPML副本合併計數但不刪引用。 |
| official_ai/google_cloud_blog_news | 保留 | D1讀者1筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| official_ai/google_deepmind | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/google_gemini_blog | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/hugging_face_blog | 保留 | 保留官方直連、時間與主文權重；OPML同URL副本不等價於可安全刪除此入口。 |
| official_ai/microsoft_blog | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/nvidia_blog | 保留 | 保留官方新聞價值；已核基礎設施漏收保留限制，D03不加品牌白名單。 |
| official_ai/openai_codex_changelog | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/openai_news | 保留 | 保留官方直連、時間與主文權重；OPML同URL副本不等價於可安全刪除此入口。 |
| official_ai/openai_skills | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/tencent_newsroom | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| official_ai/thinking_machines_lab | 保留 | D1讀者0筆、固定樣本scope {}；證據不足以支持移除或調級，維持既有入口及選取限制。 單窗零列不當作失效或無新聞價值。 |
| opml_pool | 保留 | 保留私人擴充池；不得推論池內每站品質，不讀私人設定；已知同發布者副本合併計數。 |
| runtimewire | 保留 | 保留現有文章分流；不重新納入模型目錄當普通新聞。 |
| tw_media/bnext_news | 保留 | 保留商業事件覆蓋；教學噪音確實存在，但Salesforce等反例阻止整站刪除或單詞封殺，D02不實作。 |
| tw_media/inside | 保留 | D1讀者5筆、固定樣本scope {'TP': 2}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| tw_media/ithome | 保留 | 保留產業報導；TorchTPU入口漏收有原始支持但他站存在，D03不擴共享規則。 |
| tw_media/technews_tw | 保留 | D1讀者30筆、固定樣本scope {'FP': 4, 'TP': 23, 'U': 7}；證據不足以支持移除或調級，維持既有入口及選取限制。 |
| shadow/informationsecurity | 本輪不准入封存 | D1主補parse_error，無候選；沒有七日可靠性或足量品質證據。 |
| shadow/cyberq | 本輪不准入封存 | 有效feed但僅1候選且為初始庫存、一般scope FP；不具最低樣本與新增收益。 |
| shadow/netadmin | 本輪不准入封存 | 3個初始庫存候選一般scope TP，仍不足N20、穩定性與已確認新增收益。 |
| shadow/digitimes_tw | 本輪不准入封存 | 7個觀察期候選TP2/U5；只有一日，品質／新增收益與七日可靠性均未驗。 |
| shadow/meet | 本輪不准入封存 | host_redirect_blocked、無候選；屬本機轉址防線，不冒稱實站403／429或永久封鎖。 |
| limited/cloudflare | 本輪不准入封存 | 僅單次20篇預審TP4/FP14/U2，有工程內容噪音；沒有穩定性及新增收益驗收。 |
| limited/modular | 本輪不准入封存 | 僅單次20篇預審TP6/FP11/U3；低更新頻率不等於失效，但不足准入。 |
| limited/zed | 本輪不准入封存 | 僅單次20篇預審TP10/FP7/U3；低更新頻率不等於失效，但不足准入。 |
| market_price | 保留 | D1正常分支獨立，沒有證據支持隨free-tier連帶退役；保留原成功／失敗與窗口口徑。 |
| market_free_tier | 待退役自動分支 | 原raw含描述型模型識別碼／退役生命週期衝突；只清字串仍撞80%保留防線。選擇退役以免承擔schema／warmup遷移。 |
| canary_usage4claude | 保留 | D1正常分支獨立，沒有證據支持隨free-tier連帶退役；保留原成功／失敗與窗口口徑。 |
| canary_usage_monitor_claude | 保留 | D1正常分支獨立，沒有證據支持隨free-tier連帶退役；保留原成功／失敗與窗口口徑。 |
