# BR02：Brief事件規則與資料契約 v1

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：階段歷史／已結案。** BR01～BR06已正式發布；舊階段下一步不續跑。技術契約、驗收限制與回復依[BR06](BRIEF_EVENT_BR06_RELEASE_20261023.md)及最新操作文件使用，不重開本輪已接受的去重限制。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

完成於2026-10-23（臺北）；承接2026-10-22 BR01。狀態：契約已凍結，BR03實作尚未開始。

正式基準HEAD `c43816047bc388ff9b94382ca3523ffa0d9a39e3`。本輪只增加規格及交接文件，未改正式程式、來源、輸出資料或工作流，未提交／推送。過程證據與逐案預期在 `/Users/lordmi/Downloads/ai-news-radar-brief-event-br02-20261022/`（按開始日期命名，沒有搬移）。

機器可讀契約：[brief-events-v1.schema.json](contracts/brief-events-v1.schema.json)。18組案例逐案預期、20個故障／邊界情境、26項schema／隔離／完整性核對已備；這些不是新matcher的品質通過結果。

下一階段 **BR03：GPT-6.1 Sol／High**。先驗BR02 manifest，再實作後端及既有推送重試的state guard；前端留BR04，發布留BR06。

---

# BR02 裁決 v1 — 待 BR03 實作

本文件凍結規則與接口；沒有正式執行行為。適用於首頁 brief，同時處理跨來源同事件及重發續命。讀者一般列表、原始文章 ID／URL／時間、原 stories 不改。PHP 是新聞事件，不是本站依賴。

## D01 單一事件投影

新增純 Python 模組 scripts/brief_events.py，由既有 update_news 呼叫一次。從現行 stories 的所有成員建立候選根，使用當期文章與既有 archive 的原始標題／摘要提供匹配與歷史。archive 只補歷史及引用；未進現行 stories 的文章不能單憑歷史匹配多生一個 brief 名額。原 stories 可跨多個新事件引用，不能把原 story 當不可分割的真實事件。

在 stories-merged.json 增加完整、自足的 brief_events v1 投影，包含唯一事件候選、選中 ID、時間、引用、世代與診斷。前端所有 brief 路徑只使用這份投影。daily-brief.items 改為已選事件的舊形狀適配器（story_id 等於 brief_event_id），另加 brief_event_meta；stories-merged.stories 的原 story_id、原一般列表資料與 resolver 全部保留。舊前端可讀適配器，但完整去重承諾從 BR04 新前端部署後成立。

## D02 具體事件的界線

- 完整模型版本及變體不能省略：GPT-6 Astra ≠ GPT-6.1 Sol；Sol 的模型發表、Ultrafast 速度層、上下文擴容是不同 action root。
- 同一完整版本的預告→正式推出→同廠商擴大可用性，屬同一發表根的不同 phase。沒有明確指向同一發表根者先獨立待判，不因公司相同就附掛。
- 第三方平台導入另立根：Haiku 發表與 GitHub Copilot／AWS 開放，各有平台限定的 availability root。不同地區／方案是條件，不能丟失。相同平台的明確後續擴大可更新同根。
- 漏洞披露以 CVE／共同公告批次為根；發現→修補→實際遭利用可更新同根。不同 CVE 不自動拆開：同公告明列的集合可為一批；不同批次不因同軟體合併。
- 價格異動須保留完整產品、計費單位、適用區間、地區／方案、old→new 及生效日期。運行成本 -75% 與單價 -90% 是不同量測口徑，不能自動當兩次降價，也不能互當矛盾值。
- 不支持的事件類型沿用原故事分組作單例投影，只做精確文章／URL連續性；不宣稱 v1 可識別所有商業新聞改寫。

## D03 時間與更新

每根分開保存 initial_effective_at、initial_basis、first_observed_at、last_material_at、last_reported_at、last_mentioned_at；每 phase 有不可被重述推遲的 effective_at 與 fact fingerprint。

initial_effective_at 是已知最早有效報導的時間錨，不冒稱事件真正發生時間。優先相同公告／phase 的可靠來源時間；沒有時間用該文最早 Radar 初見，basis=first_observed。既有 archive 可回補更早時間，只能把 initial／同 phase 時間往前修正，不得因換稿向後推。原文 published_at／first_seen_at 不改。

日期只做公告關係及批次辨識，不把本機臺北日直接當境外公告時區。只有日期、沒有時區與時刻時保存 precision=day；若是回顧舊日公告且找不到原稿時間，以該日期在全球時區的最晚可能時刻（D+1日12:00Z）作上界，effective_at 不得晚於稿件本身有效時間，basis=reported_day_upper_bound。同日／跨一日的時區差異，不單獨構成新公告。若文中無法確定日期指向哪個動作，保留 unknown，不能用來確認更新。

明確新進展需同時滿足：已識別同一 root；可解析的新狀態／值／條件；與既知 phase 有具體變化或明確轉移語句；有已識別發布者的肯定式報導及可歸屬的時間證據；非摘要新添的形容詞／數字口徑／預測／風險警告。未知舊條件→新寫到條件不算已確認轉移。單一具名媒體可提供「報導上的實質進展」，不標成事實已獨立查證。

只有新 phase 的 effective_at 比現有有效時間晚，才可更新 last_material_at；同 phase 的重述、換 URL／語言、補細節均不續命。last_reported_at 隨稿件發稿時間，last_mentioned_at 隨系統真正再次看到相關稿件的時間；單純重讀 state 不更新它。

brief 有效時間=max(initial_effective_at,last_material_at)，期限24h。過期事件只增加引用，eligible=false。不同新事件可補位；名額不足可留空。對初次、無法匹配的候選仍採現行選稿資格，但 uncertainty 明列，不能掛到舊根並以 unknown 更新續命。未辨識的全新改寫仍可能漏併，這是 v1 限制。

## D04 資料來源與排序

匹配使用原始 title/title_original 與既有來源摘要；新翻譯與生成摘要只供顯示，不作事件證據，以免新翻譯／摘要使身份或 phase 改變。不新增來源、LLM、embedding、全文請求、DB 或服務。

根身份與卡片主文分離。主文候選依既有 source_tier_rank，接著有可用來源摘要、有可解析來源時間、最後穩定 article ID；同級已用主文若未喪失資格保持，較晚發稿不是換主文理由。有新 phase 時，顯示該 phase 的代表稿及「更新」時間，舊發表引用保留，避免用舊標題冒充新進展。

原評分係數、AI0.65、來源 rank／cap 全保留。事件投影按既有 importance 計算，唯 recency 改用事件有效時間、heat／corroboration_count 只用該有效 phase 的當期候選成員之發布者鍵。歷史／未知 phase 引用不加熱度；cn_aggregator一票，unknown零票。event 的 source_count/item_count 是引用數，不能冒充發布者票數。新聚合必然會變更部分資格與排序，BR03/04逐筆列出原因。

## D05 有限事件記憶

新增一個公開 data/brief-event-state.json，沿用既有生成與 git add data/ 流程。只持久化本輪由現行stories播種的根及仍在保留窗內的前次根；純archive歷史只是暫時索引，不把7,427篇歷史全部強制存成state。保留按 last_mentioned_at 21天；超窗先剪枝。不保存全文、私人來源內容或模型呼叫。

硬上限：10,000 event roots；整份 compact UTF-8 JSON 8,388,608 bytes；每 root identity/descriptor 1,024 bytes、alias event IDs 16、強匹配 keys 16、phase 16、每phase evidence article IDs 8。事件投影整份也最多8MiB。state不存全成員列表；每輪從保留archive重建引用，投影保留全部仍可取得的member IDs／引用。不得為符合上限悄悄截掉已知歷史並當作新事件。

完整事件鍵／phase fingerprints不可任意淘汰。個別root超界，保留前次state，該root本輪不進brief並記history_overflow；整份state超界則保留舊state、事件brief unavailable，普通新聞仍照常。80%只在既有source-status診斷，沒有新通知或排程。BR03須量實際bytes與CPU，不以BR01示意2.93MB冒稱新schema成本；若固定真資料即超界，回報契約不適配，不自行放寬。

## D06 身份與決定性

新強根ID=be1_+sha256(UTF-8 canonical identity key)前24hex。未知單例鍵為 canonical URL（無URL才article ID）。同一批先處理強anchor，再處理弱附掛；相同輸入、state、asof，不受輸入順序影響。

有效state中的根ID固定。晚到證據連起兩個可相容既存根時，選最早 first_observed_at、再ID字典序的既存根；被併ID成alias，引用不丟。如alias或phase容量不足，不合併／不續命並診斷。衝突不能靠傳遞相似度消掉；弱附掛不能成為新anchor。既存根合併時，phase以存活root key重新正規化，同一transition取最早已知時間；不能因root／phase ID重映射製造新更新。

state遺失時依archive重建可證明歷史，明標recovered；若舊根已不在保留歷史，不能保證辨認久遠重發或恢復所有event alias。文章ID／resolver仍不受影響。

## D07 升級、失敗與推送

詳見 STATE_RECOVERY.md、INTERFACE.md。前端讀不到有效投影時不回退到未去重的原故事池；可保留同頁記憶中的未過期有效投影並顯示其資料時間，否則簡短提示使用新聞列表。一般新聞正常。

BR03須在既有update-news推送重試加入state blob並行保護：生成前記錄輸入state Git blob（缺檔哨兵亦要記錄）；fetch後如origin/master的state blob不同，停止該次push，不用-X theirs覆蓋它、不重新抓來源。既有排程下一輪可接續遠端狀態。保留原cron、concurrency與停用workflow；沒有新排程。

## D08 驗證裁決

原448預留經保守版本／URL／已曝光家族閉包，全部隔離，不能宣稱獨立品質。另封存13個未展開正文的候選群、73篇（含同家族歷史），各群在既有14日窗內至少2個不同URL。只證明機械曝光隔離，不保證跨語言語意獨立。BR04先在規則凍結後盲標整群、核別名及非新聞，再揭曉演算法輸出；污染／unknown整群排除，報真實分母，不用來調參。

如果沒有合格獨立群，獨立品質欄保持not_evaluable，BR05必須明確審查是否足以發布，不能填pass。固定開發回歸、全部歷史輸出差異與確認誤併零容忍仍必做；不因此再等日數或重抓來源。

---

# Matching rules v1

本文件是BR03須實作與受測的凍結規格，不是已執行的新matcher。不能寫入PHP／文章ID／日期的專用合併白名單。

## 1. 特徵抽取

NFKC、大小寫、既有繁簡轉換、Unicode dash／空白正規化；保留完整數字、版本、型號後綴、數量單位及否定語。27.2萬=272k=272000，50萬=500k=500000；輸出token上限、context、價格／運行成本是不同欄位。抽取須記原字段及span，不能從生成摘要推導事實。

識別有界辭典／regex類別：公司與平台公開名稱、完整模型與variant、產品／套件名稱、CVE（含同句CVE-YYYY-NNNNNN、NNNNNN縮寫）、有明確命名的公告／計畫、release/context/speed tier/availability/security/pricing動作、scope、from→to、公告日／effective日、肯定／預告／否定狀態。縮寫CVE只沿同句明確年份展開，不能拿所有數字當CVE。

完整模型slug保留系列+主次版+代號／size／mode等可區別部分；只知道GPT-6而另一篇GPT-6.1 Sol，不當別名。brand作候選索引，不是合併鍵。比較文中的競品不是主事件subject；只有能把動作歸屬到唯一主體的文章才產強anchor。多主體／多事件日報不作跨根橋樑，保留unknown單例或逐個有明確span的atomic claims，不能讓一篇摘要把所有模型串起來。

## 2. 先拒絕，再比正證據

優先拒絕：不同完整型號／版本、不同action root、相反狀態且無明確時間順序、不相容CVE／公告批次、明確不同第三方平台、同一計價欄位的不相容條件或生效日、兩份明示不同公告。衝突屬性缺失不等於相容證據；有多個可能anchor則unknown。

日期允許跨時區相鄰日，前提同一完整版本／動作且發稿相距<=36h；相鄰日規則不能覆蓋明確不同生效時間。強同公告URL或完整不變的model-release identity可跨21天保留歷史匹配，但後續phase另判。

## 3. 允許的匹配路徑（優先順序固定）

R1 精確同文章：同既有article ID／AIBASE article key／canonical URL，且內容沒有新atomic action衝突。僅文稿更新沿用root；若同URL變成明確不同事件，分claim並記url_reused，不能由URL壓掉衝突。

R2 強公告：同既有資料中的明確官方公告URL（非媒體各自文章URL），或相同完整CVE集合／同公告明列集合，以及相同subject/action。明確的CVE交集可附到同batch，前提沒有另一公告批次衝突；A={cve1,cve2}不是讓cve2任意橋接另一不相容batch。

R3 完整模型發表：唯一主體完整model/version/variant + release或speed-tier action + 相容provider與平台scope。launch當天的成本／benchmark描述是同公告細節；沒有明確新日期／新條件轉移，不拆pricing事件。日期重大矛盾或多版本競品比較則unknown。第三方platform availability使用model+platform+scope獨立鍵。

R4 參數／能力變更：完整產品+action+可比較from→to（如context272000→500000），或同產品/平台+至少2個互相獨立的具體功能特徵。不同措辭的同一能力只算一個特徵；Chrome跨tab讀取與瀏覽器任務操作算兩個，副詞「智能／強大」不算。21天內須唯一相容根，且無新版本／effective日／反向條件衝突。只補全先前unknown條件不授予更新。

R5 漏洞公告脈絡：僅當缺CVE文章不能走R2時，subject軟體+security disclosure action，發稿落於已知批次anchor前後36h，且可匹配至少2個獨立具體事實：具名協同行動／共同發現者、漏洞數量、漏洞機制（RCE／unauthenticated）、協調修補期間、明示同一公告日。泛詞嚴重／全球／AI不算。兩個獨立具名參與者可各算一事實，但Google/Wiz這種同組織別稱不能重複計數。存在唯一相容強batch；匹配事實可來自R2或已通過至少2個獨立特徵的strong-context成員。只有「數量+機制」等較弱組合時標context_attachment，不能新增anchor事實、不能單獨確認phase、不能提升更新可信度。每個附件須與root的全部已知排他屬性相容，不能A像B、B像C就合併矛盾A/C。出現第二個符合batch就unknown，不按最高分硬選。

R6 不足證據：維持原story單例／article identity；match_status=unresolved，不能聲稱已去重成功。已知可能指向舊事件但無法確認phase者不讓該舊根續命。選稿資格沿D03，不因某媒體來源或某關鍵字黑名單排除。

不以新全局相似度門檻取代R1–R5；既有title similarity僅保留原stories的既有用途，不能覆蓋排他條件。

## 4. phase 與時間（匹配root後才做）

phase key來自action內的具體變化：預告／可用、受眾／平台條件、明確old→new、披露／patched／actively_exploited，加可歸屬公告批次。固定根的「未知→這次摘要有寫」不是新phase。只描寫不同能力或同成本不同量測口徑，維持原phase。

採用具名publisher已識別的肯定式來源報導：例如「AWS logged attempts」「now broadly exploited」是觀察報告；「could be exploited」「warns attackers may」是風險，不能續命。PoC／漏洞利用程式流傳不等於已觀察到真實攻擊。首次報導新的實際觀察（例如AWS早在修補前記錄到攻擊）可採首次報導該新事實的時間；被觀察攻擊的歷史發生日不是本次披露時間，日期須標明角色。若archive已有相同觀察，則不是新phase。

同一明示公告日／既有transition fingerprint的晚稿使用已知phase時間，不使用晚稿日期。對缺日期的late update，只有明示已發生的觀察／轉移並非舊公告重述才可採報導時間；無法判別就unknown_update。

代表稿／引用／投票與有效時間按DECISIONS，material是reported且qualified，不是外部fact-verified。

## 5. BR03演算法次序與界線

extract原文特徵→建立硬衝突及強keys→從valid state／archive建立root與舊phase→強anchor批量歸群→依穩定ID順序處理context attachments→逐根phase判斷→選代表與current phase發布者票→計時效與既有score/gate→唯一投影及daily adapter→驗schema與容量→安全輸出。

用索引(model+action、CVE、產品+action+時間bucket、canonical URL)列候選，不全archive兩兩O(n²)。原文每篇最多title2048字、來源summary8192字作匹配；超出只診斷截斷，原文仍在archive，截斷造成不確定時不可強併。摘要新模型生成／翻譯不在此流程。

所有合併要輸出rule_id、basis字段／span、強／context狀態、衝突／ambiguity reasons。每批輸入排列、重跑與晚到資料都要驗，既有state根不因代表稿變更換ID。單根alias/phase上限不足時按D05降級，不能默默刪記憶再稱新事件。

## 6. ID與key的確切編碼

identity.key是UTF-8、sort_keys=true、ensure_ascii=false、compact separators、禁止NaN的JSON字串，固定含v=1、action、subject；其餘欄依action如下。descriptor其餘facts可補充，但state中已分配key不改，新增等價強key以SHA256放match_keys。event ID依key字串hash；合併兩個既存根按D06保留原ID，identity.key保留該存活根key，其他keys成alias。不能以代表稿URL作強事件的key。

- model_release／speed_tier_release：subject包含vendor、完整model/version/variant；scope=native，不放可變受眾／評測／成本數字或晚稿日期。
- platform_availability：subject完整model；platform第三方平台slug；根不因後續受眾擴大換ID，scope變化放phase。
- context_change：subject完整model；platform排序集合；from/to標準化數值與unit。必要參數缺失不產此強key。
- capability_change：subject產品、platform、排序後至少兩項共同能力核心。批量匹配先求所有相容strong members的共同核心，至少2項；只與中間某篇相似不夠。既存root可補facts，不替換key。
- security_disclosure：subject軟體、batch排序CVE集合；沒有CVE但足以構成強anchor時用具名公告key與公告日期。沒有強anchor者article單例，不能只有software作key。
- pricing_change：subject、platform/scope、metric/unit、from/to、effective批次全部編入key；缺關鍵條件不作強價格匹配。
- legacy_story／article：canonical URL，缺URL才原article ID；沒有題目語意猜測。

phase fingerprint是根key、kind、具體transition核心與可歸屬公告批次的canonical JSON SHA256；phase_id=bp1_+fingerprint前24hex。不放稿件URL／pub／first_seen／執行時間。baseline同根固定一個；同公告／同transition補條件時沿已匹配phase，不因facts新增產新fingerprint。無法判同公告時unknown_update；已有相同observed_exploitation報告後，新的形容詞／單純每日重述不成下一phase。

每phase最多8個evidence IDs是有界代表證據，依rank及穩定ID取；不是截斷所有引用。完整成員仍由archive投影，phase fingerprint／最早時間不可因代表證據換掉而遺忘。

---

# 前後端接口 v1

## Python純函式

`build_brief_events(*, stories, archive_records, archive_meta, previous_state, now, window_hours=24) -> BriefEventResult`

archive_meta固定為{status:valid|missing|invalid, generated_at:UTC字串或null}；previous_state固定為{status:valid|missing|corrupt|unsupported, payload:StateV1或null, error_code:不含內容的代碼或null}。不能以None混淆missing與corrupt；valid時payload必先通過schema／revision。

輸入均不修改；沒有I/O／provider。Result含projection、next_state或None、daily_items適配器、diagnostics。呼叫者先區別missing/invalid/unsupported state，不把失敗吞成{}。stories既有score／sources不可被原地改寫。archive原始文字抽特徵；current文章顯示欄位與existing importance可經具名adapter注入，勿造成循環import。

純函式分責任：extract_claims → resolve_roots → resolve_phases → select_representative → project_events → enforce_bounds。上游共用的AI分類／source cap不搬進新matcher，不改共享門檻。事件recency/發布者計數只作用於新投影的importance adapter。

## 公開輸出

- `data/stories-merged.json`原`stories`不變；新增`brief_events`完整envelope（SCHEMA.json中的projection）。所有當期seeded根都列出eligible及理由，過期根也可列診斷；前端只取eligible=true。來源歷史不新生seed。
- `data/daily-brief.json.items`為投影selected_event_ids的順序適配器，保留舊story欄位／引用結構，但story_id=brief_event_id，並保留member_story_ids。新增`brief_event_meta`（selection schema）；其世代與projection一致。
- `data/brief-event-state.json`是state schema。前端不下載它。JSON皆走既有public sanitize及atomic writer。
- `source-status.json.brief_events`沿用status文件加診斷：status/recovery_mode/input/output roots/strong/context/unresolved/expired/update counts/state bytes/capacity/errors。不是新聞來源site，不改source_health分母，不新建監控通知。

`generation_id = bg1_ + sha256(canonical compact JSON of full projection excluding generation_id)[:24]`；canonical使用字典鍵排序、set／ID集合排序、UTF-8、禁止NaN。state revision亦hash整份state除revision，state自己的generated_at是實際asof；同asof與同有效輸入應相同。不要把parent revision加進被hash的內容造成無效循環變化。

Projection的events含legacy adapter用的主文／score/category/importance_breakdown/business_events及全部保留archive可取得的refs，refs可簡化摘要欄位但不能丟ID／URL／原文時間。`member_story_ids`指本輪原stories，`member_article_ids`指全部保留成員；一個原story可被新層拆成多個root（原story仍不改）。primary與每phase的evidence IDs須能解析到refs或明確歷史state證據，不可捏造引用。

selected_event_ids最多20、唯一、必為eligible事件，先套既有score／corroboration gate及source diversity；跨事件不再用舊title-similarity再次硬併。每個root最終只有一筆。引用raw count、current_phase_corroboration_count及所有publisher鍵分開；未知不加票。

## 前端

1. 驗brief_events schema_version=1、matcher_version、generated_at與同一stories payload一致、ID／選中集合／時間值合理及generation格式。前端不驗大state也不重做語意匹配。
2. 使用projection.events中eligible且client now<=expires_at的唯一根。後端selected IDs與其餘eligible根可形成現有brief／補位兩池，但不得混入legacy raw stories/daily items。舊eventKey／uniqueStories語意排除不再用於v1事件池。
3. 熱點／時間線／Top3／展開／query／source／多方篩選共用這些根，篩選檢查完整refs集合，名額按root ID計。篩選只能減少候選，不能重新讓expired／unresolved_update續命。一般列表原篩選不變。
4. frontend排序沿原business事件／熱度／importance層次；時間tie-break改event effective_at。當期phase一票／unknown0，不能以歷史引用數改成多方。
5. 卡片顯示代表稿及事件有效時間，material phase可標「更新」；系統初見用「本系統初見」，日期上界用公告日期並註時間未明；原文發稿時間保留在引用。不要顯示schema／hash給讀者。
6. 不同generation的daily meta只忽略daily副本，使用自足projection.selected_event_ids。讀不到projection／未知schema／invalid時，不跑舊raw fallback重灌同事件：先使用同頁尚未過期的已驗projection並呈現其asof，否則brief簡短顯示「重點整理暫不可用，可先查看新聞列表」。新聞列表保持現行行為。
7. 瀏覽器需要一般列表資料而stories延遲，不阻塞一般列表；projection到達後一次切換。少於10／20筆不補回被抑制根。

## BR03/04交界

BR03交schema實例、next_state、projection、daily adapter及diagnostic。BR04只實作消費，不自行補語意規則。兩階段以同一CASE_EXPECTATIONS及GENERATION_FAILURE_CASES對接。若某例無法達成，不自行降低期待；記最小反例回BR02契約修訂並版本化，再重封存。

## 舊形狀適配欄位的精確映射

projection event及daily.items保留primary_url/source_name/source_names/items/importance/importance_score/importance_label/reasons/earliest_at/latest_at等舊欄位。story_id=brief_event_id；items=sources；importance=importance_score=score；earliest_at=initial_effective_at；latest_at=effective_at。這是brief事件適配器的時間語意，原stories的同名欄位不改。source_count=item_count=len(sources)，corroboration_count取active phase當期候選的唯一已識別publisher keys，duplicate_count=max(1,corroboration_count)。

額外semantic checks：所有timestamp normalize到UTC Z；初始時間<=有效時間，expires_at=effective_at+24h；last_material必對應已知qualified phase；selected IDs唯一且eligible；unavailable時events/selected皆空；refs/member IDs全集一致且primary存在；event IDs唯一；state alias不能指自己／形成環，phase IDs唯一；state revision／projection generation需重算吻合。identity descriptor的serialized UTF-8亦受1024bytes限制，不只schema的字元長度。

來源pub>asof+6h不進brief；其餘小幅未來時間只在事件投影以min(pub,asof)作錨，原文不改，basis仍記source_report並診斷clamped_future。沒有來源時間才用最早first_seen；未知／矛盾日期不能當新phase。

---

# 狀態／世代／失敗契約

## 載入與恢復

- valid v1 state：保留根與已知phase時間；用archive補更早證據及成員。state可能因前次單檔原子寫入而比某個payload新，不能因此清空它。
- 首次部署missing，或state損毀：如archive是結構有效、非空且時間合理的保留歷史，從archive重建known roots/phase，status=recovered，recovery_mode=archive，標history_complete=false。使用歷史最早已知報導，不用本次執行時間重置所有事件。
- state有未知future schema：不覆寫該檔，brief unavailable；普通新聞繼續。不能用舊程式降版清空新格式。
- missing/corrupt且archive不存在／無法解析／空／未來時間不合理：brief unavailable，不把本輪新抓到的數篇當完整冷啟動歷史；一般刷新可建立archive，下一輪仍必須明列history範圍。此情況沒有完整歷史保證，不能宣稱所有舊重發已排除。
- 同一event歷史已被21天last-mentioned保留窗剪除，且無archive證據：可能被當新根；標documented retention limit。持續真的重發會更新last_mentioned，不能靠不變payload讀取來續保留。

## 原子檔寫入順序

先在記憶體完成所有新物件、schema及bytes驗證，再逐檔寫入。普通latest／archive仍使用既有atomic write。事件bundle依序：有效archive → next_state（若可寫） → stories-merged含自足projection → daily-brief適配器。最後source-status。不要把「逐檔原子」說成跨檔transaction。

邏輯matcher錯誤／schema或容量不合法：catch於事件邊界，保留舊state，輸出brief unavailable及原因；原stories與一般新聞仍產生。state單檔寫入失敗：不發佈聲稱已持久化的新eligible事件，保持舊檔並按可行情況輸出unavailable；若連一般輸出目錄都不可寫，既有generation應失敗，不能假裝新聞照常。

強制中斷可能留下不同代的完整檔案：
- state已寫、projection未寫：下輪用較新的valid state，不重置；瀏覽器只見上一代projection，按原expires_at失效。
- projection已寫、daily未寫：新前端只用projection，忽略不同代daily，不混池。
- archive已寫、state未寫：下輪從舊valid state+新archive恢復同根／phase，first/phase時間取最早證據。
- 同代生成重跑不新增phase，不延長有效時間；檔案名.tmp不作正式輸入，沿既有writer清理規則。

## 容量

先剪真正超21天last_mentioned的roots，再驗10k根／8MiB與每root bounds。不要丟未過期fingerprint來補容量；不能寫一份缺歷史的state卻宣稱ready。單root超界可隔離該root；全局超界保存前次檔、projection unavailable（events與selected空），source-status給明確錯誤。BR03必須以真凍結archive量測，不合即阻擋契約實作驗收。

## Git推送競爭

既有update-news concurrency序列化一般run，但維護者或其他寫入仍可能變動state。生成前保存當前HEAD的state blob ID或MISSING，不能印檔案內容。每次push失敗後fetch，讀origin/master的同路徑blob；不同即停止該run的重試，保留遠端，不能-X theirs覆蓋，也不重抓付費來源。相同才沿既有rebase重試。下一次原有刷新從新遠端起點執行。初次MISSING→新建state也受此比較保護。

只有新增state guard，不改cron／concurrency／watchdog，也不恢復觀察／日報。BR03用臨時本機Git倉庫演練同blob可重試、異blob中止、缺檔轉有檔中止；不真push驗這個分支。

---

# BR06發布／回復交接（本階段不執行）

1. BR03/04候選全部驗收與BR05複核後，先保留正常bot最新data；按當時遠端狀態整合，不倒灌BR01快照。
2. 先推後端、相容adapter與既有workflow state guard，保留前端舊版。等一次既有正常刷新（需要時BR06授權範圍內一次手動既有update-news），核state v1與stories projection／daily同代、容量及恢復診斷。新前端尚未上線時，舊介面可能仍從raw stories補位，不能提早宣稱正式去重通過。
3. 再推BR04前端與全部共用asset tag，核Pages、真HTTP世代與Chrome桌面／手機路徑。今日PHP過窗不倒灌，以凍結快照核固定案例、以當期資料核正式鏈路。
4. 回復優先只回前端到相容已知版本並升新asset tag；後端v1/state保留，避免歷史歸零。回到舊前端會恢復既有重複限制，需如實記錄。
5. 若後端有錯，先保留最近valid state備份與commit hash，再部署接受v1並輸出unavailable的修復版／停用事件層；一般新聞維持。不要刪state、降schema或直接反向patch恢復退役日報／來源觀察。未知較新版state只讀保留。
6. 封存輸入、輸出、state revision、各commit/run/head_sha/asset tag、正式asof，分清Git更新與CDN混代。沒有新增7日／14日等待或外部服務。
