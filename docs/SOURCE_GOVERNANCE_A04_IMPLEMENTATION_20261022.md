# A04本機實作與A05交接（2026-10-22）

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：方案A已結案／階段歷史。** A01～A06已完成正式發布與驗收；下方待複核、待推送與下一步只記當時狀態。裁決及未完成品質限制仍保留，不重啟來源觀察。見[A06](SOURCE_GOVERNANCE_A06_RELEASE_20261022.md)及後續[PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

**A04本機實作完成；下一步A05複核：GPT-6 Astra／High。**
依[A03裁決](SOURCE_GOVERNANCE_A03_DECISIONS_20261022.md)完成B01／B02，B03同步治理文件及既有停用包。
這是本機發布候選，尚未提交／推送／部署；正式線上行為不以本文件宣稱已更新。
Downloads `ai-news-radar-source-governance-a04-20261022/`保存before、原輸入、逐批patch、完整回歸、重播、CHECKPOINT／HANDOFF與manifest。

## B01：引用與佐證分開

新增`scripts/corroboration.py`提供固定公開身份映射，不連線、不讀私人OPML、不解碼Google跳轉。
確切LABELS／HOSTS／SUFFIXES及ECOSYSTEM_SITES即本候選的映射清單；依既有公開來源設定與A02已見發布者線索建立，無任意域名推論。
OpenAI News／Codex／Skills同鍵，Google數個管道同鍵，GitHub兩管道同鍵；Reuters與CNBC各一鍵。
保留AIBASE／36Kr／橘鴉既有cn_aggregator口徑。未知及互相衝突的線索分別標unknown／conflict，均不加票。
直接host按網域邊界比對；通用github.com只認OpenAI Skills既有repo路徑，不認其他repo；OPML標籤不構成發布者依據。
主題query的公司名稱不是官方身份。精確Google News原始標題尾綴僅提供有界發稿者線索，不能證明法律／採訪獨立或事實正確。

- 當期文章／story引用有`corroboration_key`及`corroboration_status`，歷史archive不回填。生成整合回歸亦確認新key只進當期view。
- `source_count`／`item_count`及完整引用維持原口徑；新`corroboration_count`允許0，`duplicate_count=max(1,count)`只作相容別名。
- 熱度、分數、多方分類／理由及brief gate採發布者計數；權重、0.72 gate、AI relevance／0.65、來源rank／cap及聚類算法保持。
- diagnostics的`max_source_count`仍是raw引用數，另加`max_corroboration_count`以免維運誤解。
- 前端story及非story合併共用公開鍵集合；`mergedCount`只表示合併篇數，不再加熱度或觸發多方標籤。
- 標籤改「多方報導」，未知顯示「來源待辨識」。舊JSON若缺新資訊保守不升級；0、無效數字及新鍵fallback有回歸。
- index五個資產共用版本已更新為`20261022-a04`，避免舊app快取沿用錯誤計數。

## B02：免費額度自動分支退役

`run_market_sensors`已移除free-tier網路／diff／活躍status；價格及兩canary繼續使用原邏輯。
原`state.free_tier`保持內容及觀察時間，不產生假大量移除事件；純離線parser、識別碼與80%安全防線保留。
舊free-tier訊號退出當期payload，前端也過濾舊JSON卡片。README中英文、讀者區名及維運說明改為現行價格監測。
退役的代價是失去該資料集免費額度／rate limit自動偵測，沒有等價替代服務；一般新聞收錄另依既有規則。
頂層state時間只代表其餘當輪工作，不代表free-tier新鮮；退役分支不偽造ok，也不繼續增加失敗次數。

## 驗證結果與限制

- 完整Python套件**1,533項通過**，三支Python及四支JavaScript語法／差異檢查通過；測試暫存按既有CI規範位於Downloads。
  首次使用系統tmp引發舊日報路徑防線失敗，改用既有規範後通過，沒有為此改防線或恢復日報。
- D1精確重播保留192個AI ID、183組故事成員及全部引用，主文沒有變更。
  24組計數紀錄改變，其中5組score改變；內部brief 20→18，移除兩則只靠Reuters5／3版本過gate的故事。
  四個已核Reuters5／3／2、Wired2版本均只計1；前兩分數0.6802→0.5802、0.6377→0.5877。
- 固定14日2,842列所有正負例AI判定及rank相同；2,669正例列整窗機械合併2,375故事，449組計數紀錄變動，主文均不變。
  此分母是原始正例列，與A02去URL／控制源後2,420新聞URL不同；不冒稱歷史逐日選稿、可用率、精準度或留出驗收。
- 完整正式app＋loader＋selection在固定D1時間及DOM adapter執行。前後候選聯集均182；時間線均20、熱點均10，排序與名額有替換。
  內部brief減2不等於首頁少2事件。FRONTEND_REPLAY列全部ID差異、實際前三卡及來源標籤；所有183故事的新計數與標籤一致。
  非story多版本、舊JSON、未知及舊free-tier卡片均驗；未執行真瀏覽器／像素驗收，A05應留意實際呈現。
- 真實封存64個價格模型、26個free-tier provider state以固定回應重播：三個活躍感測器狀態正常，free-tier基準hash不變、零新請求／當期事件。
  這是離線重播，非新鮮度或真上游可用率證明；另有價格變動、兩canary去重、單分支失敗隔離回歸。
- 來源rank／cap、AI分類程式、來源設定、tracked data及實驗workflow原碼不改。A01本機false保持；兩實驗仍停用，遠端Git false待A06同步。

封存留出未做語意展開或重新標記。機械重播輸出在Downloads的`sealed/`，不直接讀其標題／摘要；審查用聚合、ID／hash及既有開發案例。
八個新候選仍本輪不准入並封存；D02教學誤收、D03基礎設施漏收仍是已知限制，沒有新採樣待辦。

## A05先查與回復

1. 驗A04 manifest、讀Downloads HANDOFF／REPORT及B01／B02／B03 patch；原P01～A03未提交成果完整保留。
2. 複核身份映射、衝突與unknown fallback、所有count消費端、私有／歷史資料邊界，以及機械比較的全部受影響輸出。
3. 檢查前端20／10名額替換是否符合產品邊界；DOM adapter驗收不能取代真瀏覽器版面觀察。
4. B01／B02分批可回復，patch順序B01→B02→B03；局部回復不可reset既有工作。發布事故優先只撤B01並保留free-tier退役，程式與JSON／asset一起回復相容版本。
   三批已在Downloads副本實際正向套用、反向還原並逐檔比對；沒有為演練改動正式工作目錄。
5. A06才依發布授權處理遠端bot提交、push／CI／Pages與enabled=false，不能force push或重啟兩實驗／D00。

本輪止於A04。**下一步A05（S07）：GPT-6 Astra／High**；A05完成後A06：GPT-6.1 Sol／High。
