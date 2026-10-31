# AI News Radar 交接摘要

更新：2026-10-31（臺北）。本頁僅保留目前有效狀態與2026-10-21起的交接紀錄；超過十天的項目與歷程已從本頁移除。任務清單以[TASK_LEDGER](TASK_LEDGER.md)為準，產品／來源／操作細節分別依README、SOURCE_COVERAGE與OPERATIONS。

## 10/31 前端用詞統一（發布中，待遠端人工審閱）

維護者要求先全部實作再人工審閱；因遠端手機無法開啟本機連結，另明確指示commit／push至GitHub。共用資產版本20261031-wording1正在整合master發布，完成後從GitHub Pages正式站人工審閱。沒有改動70分門檻、來源／材料資格、新鮮度、24小時窗口、資料schema或API路徑，也未覆寫正式data與既有item快照。

| 概念 | 前端統一名稱與範圍 |
| --- | --- |
| 一般文章 | AI 新聞／精選新聞／全部 AI 新聞，以篇計；精選為一般閱讀條件，與重點門檻不同。 |
| 入選事件 | 重點訊號，以則計；後續卡改為更多重點訊號，排序稱依重要性／依時間，導覽總覽取代熱點。 |
| 全部內容 | 全部收錄內容；沿用合併重複開關，同發布者重複連結仍合併顯示，沒有改去重規則。 |
| 來源 | 來源類型（單一選單）／發布者／抓取來源／RSS 訂閱；一手來源包含官方與評測第三方，不混稱全部為官方。指定來源清單沿用既有資格。 |
| 分數 | AI 相關度／優先閱讀分／重點排序分；第4～5則重點卡顯示實際impact-v2排序分，不再顯示舊多源熱度，排序計算本身未改。 |
| 摘要 | AI 摘要／來源摘要／來源首段或其譯文，依實際來源標示。 |
| 時間與健康 | 資料更新時間、新聞發布／首次收錄時間；本輪讀取量不稱今日累計，抓取來源失敗與RSS訂閱失敗分開標示。 |

前端載入錯誤使用區域名稱而非JSON檔名；新聞資訊頁生成器已中文化欄位與狀態，原始JSON欄位保留，審閱範例另外生成於Downloads。README同步候選用詞。只修正顯示與篩選入口命名，舊sourceTypeFilter程式介面保留相容，頁面只保留一個來源類型選單。

驗證：完整1991項通過（98個既有feedparser警告），JS語法、Python編譯及資產版本檢查通過；隔離Chrome在1440桌面及390手機寬度實際載入，來源篩選、精選／全部AI／全部收錄切換、合併開關、空區及新聞資訊頁皆正常，無JS例外或整頁橫向溢出。固定正式快照顯示109篇AI新聞、32篇精選、0則重點，治理ready；篩選後全站統計不變。

遠端審閱入口：[GitHub Pages正式站](https://seisyuku.github.io/ai-news-radar_zhtw/)。本機連結僅適用同一台電腦，不再作為遠端審閱入口。截圖、browser-results.json、單頁審閱範例、測試及發布備份位於 /Users/lordmi/Downloads/ai-news-wording-review-20261031/ 。本輪依使用者指示發布並驗收，人工審閱仍待使用者進行；Groq第五項維持暫緩。

## 10/31 重點訊號空區研究（維持現狀，結案）

依10:31:03正式快照、10:38:45模擬截點（臺北），資料與前端guard均ready；微軟與Anthropic／SpaceX於08:38、09:04超過24小時，剩餘四個來源／材料合格候選為65／65／55／55分，現行70分門檻入選零則。純降65或60分會選航空AI定價、Dessa；降55分會再加入Marvis、Spotify；65分加排除純標題重述則只剩Dessa。這是同資料的機械模擬，未改正式門檻。

維護者裁決「不調整，結案」：保留70分及原I／P／E／C條件、來源／材料資格、24小時窗口、核心3分與新鮮度排序，接受沒有合格熱門事件。降低門檻、額外材料gate與中文E詞彙校正建議均不自動續行，不列待辦。既有Groq摘要前四項修正仍是另一案件，已完成發布；其第五項仍暫緩。分析暫存位於 /Users/lordmi/Downloads/ai-news-featured-threshold-20261031/，正式程式／資料未因本研究變更。

## 10/31 Groq摘要修正（已發布並驗收）

維護者核准前四項規劃並執行；第五項只記錄，日後健康盤點有更多證據時再評估成本與價值，本輪不實作。

| 修正 | 實作與驗收條件 |
| --- | --- |
| 數字驗證 | 使用Decimal比對金額、幣別、百分比及支援的數量／單位，保留完整模型識別。$25 billion與250億美元等值；25億美元、錯幣別、25%誤作25個百分點及版本更動均拒收。不做匯率換算；未知寫法保留來源形式。這仍是有界材料檢查，不宣稱跨企業／條件的完整語意驗證。 |
| 有界補試與冷卻 | 長度、數字、必要版本、語言與格式驗證失敗最多補試一次；只傳固定修正提示與原始材料，不重送失敗回應。最終內容拒收同鍵冷卻六小時，材料更新改鍵立即可試；資訊不足／安全拒收不補試，暫時provider異常不套內容六小時冷卻。failed沿用失敗嘗試次數，補試成功可同輪有failed與generated。 |
| 長度 | 提示以含英文、數字、空白、標點的總字元計算，目標50～90，硬性30～120；只取一至兩項核心事實，不用截斷文字湊長度。 |
| 標題重述 | 生成前排除只重複標題／媒體名的片段，三則歷史不足材料案例不再呼叫provider；短而有實質資訊或同事件其他來源仍可使用。 |

prompt版本提升為v3；v2成功快取通過新版完整數字／版本驗證後可重用，避免全部重生成。來源、選稿、Gemini讀者翻譯與現有來源摘要回退不變；離線驗證不覆寫正式data／state，也不呼叫真實provider；正式發布資料由既有公開刷新生成。

第五項暫緩範圍：逐項新聞ID／失敗分類／輸出長度／截斷等詳細紀錄及另設每輪總請求上限，均不加入本輪例行流程；維持既有彙總狀態、20候選與最多6則成功新增規則，不新增監控、排程或報告。未來只在另一次健康盤點，以新增證據衡量是否值得額外處理能力。

驗證完成：完整1990項通過，98個既有feedparser警告；Python編譯與git diff --check通過。新增63項測試覆蓋等值／錯誤量級、幣別、百分比／百分點、版本、單次補試、冷卻及到期／材料更新、失敗文字不回送、標題重述／豐富同儕材料與v2快取移轉。使用10:08正式快照檢查，14筆有效成功快取可重用，3筆只有標題的舊成功快取不再展示；三則歷史insufficient_context原始材料回放皆為零provider呼叫。本機測試暫存位於 /Users/lordmi/Downloads/ai-news-groq-fixes-20261031/；發布前離線階段未改動正式快照或呼叫真實provider。後續實際模型成功率沿用既有健康彙總，不擴充第五項紀錄。

Groq修正程式[5e911b10e93e](https://github.com/seisyuku/ai-news-radar_zhtw/commit/5e911b10e93e9bf30b982de3443d5e27531ec768)已整合最新master並推送。[GitHub離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161478560)1989項通過、1項資產比較分流，98個既有警告；本機完整1990項已通過，前端資產未修改。[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161477951)成功後，以既有[公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161538219)產生e19bf57e1ebb，資料[Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161652223)亦成功。

臺北10:47:34快照：Groq新增6則、失敗0次、成功快取重用14筆，prompt版本v3；來源失敗／降級皆0。一般AI139篇，事件與治理ready，重點0則符合維持70分的裁決。首頁＋六資產＋八份公開JSON與摘要快取共16檔HTTP bytes和生成提交一致；正式下載資料通過讀者端guard與實際混排選集檢查。這是單次正式執行結果，不宣稱長期成功率或獨立新聞precision。發布備份及HTTP證據位於 /Users/lordmi/Downloads/ai-news-groq-fixes-20261031/release/。

## 10/31 全區影響排序（已發布並驗收）

核心／產業動態共用I／P／E／C與70分門檻，核心僅加3分；混合排序最多五則。新鮮度為2^(-sqrt(t/48))，保留48小時減半點、加快前段衰減，24小時窗口及來源資格保持。後端80085cca0c03、前端4a1148c616d4已在master，impact-v2及共同資產20261031-impact3正式上線。

先前GitHub平台事故造成的待驗收狀態已解除；原[離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41102288333)與[資產檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41102288393)均成功。本次Groq發布再核對16檔正式HTTP、同代資料與讀者端guard／混排，全部通過。規則及固定輸入結果見[全區影響排序](FEATURED_IMPACT_20261031.md)。降標研究依維護者裁決維持現狀結案，不重列待辦。

## 目前續接狀態

正式專案為 /Users/lordmi/Documents/ai-news-radar_zhtw，分支master；最新程式發布為5e911b10e93e，本次正常刷新資料為e19bf57e1ebb，後續文件及自動資料版本以master紀錄為準。私人早報移除、新聞品質、全區影響排序及Groq前四項修正均已發布並驗收；前端用詞統一正依維護者指示發布，完成後待遠端人工審閱，待辦以任務台帳為準。

維持公開24小時窗口與重點70分門檻，接受零則，不加入第五項詳細健康紀錄或新總請求上限；不重啟退役工作。續接先核對最新master、工作目錄與來源健康，不沿用事故期間的過期發布待辦。

## 10/31 正式發布結果

- 私人早報移除 `7d5a2c4cf1ea`、新聞品質整合 `cbd1e1a5923b`、維護文件 `8edc35b31ffd`已整合master，保留遠端刷新歷史。
- 私人生成／Drive派送／雲端校稿共84個專用檔案移除，3份workflow不在正式清單，3個舊說明頁回傳404。私人稿件、Drive、OAuth／secret及歷史artifact未操作。
- 同URL版本歷史與最新閱讀投影、來源／事件／入選品質診斷、Juya有界官方文字查漏已上線。HF首段補讀與譯文、重點摘要優先、來源摘要回退及金額尺度修正保持。前端共同版本20261030-quality1。
- 首次CI缺少原由雲端套件間接安裝的jsonschema，已由 `1598a2069b88` 明確宣告測試依賴。乾淨Python3.12環境1913項通過；[GitHub離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093539300)1912項通過，1項資產比較由[獨立檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093066138)驗證。98個feedparser棄用警告為既有狀態。
- [公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093175458)由新程式產生 `cf3f601098c2`；該次臺北00:48:35快照168篇一般AI、4則重點（3核心＋1補位），14個來源正常，brief與governance皆ready。這是該次發布驗收快照，不代替下一次維護時的即時查核。
- 首頁與6份資產和發布版本位元一致，8份公開JSON和生成提交一致，資料通過讀者端guard；[最終文件Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41094003358)成功。固定輸入7504檔和已驗整合結果僅實測耗時不同；不宣稱獨立新聞precision。
- 該次唯讀查核：公開刷新於臺北01:05建立的run已成功；公開刷新、watchdog、離線測試、資產檢查及Pages保持啟用，七日觀察／報告／SMTP三流程仍手動停用。

發布備份與驗證材料：/Users/lordmi/Downloads/ai-news-release-20261031/。整合階段入口：/Users/lordmi/Downloads/ai-news-quality-integration-20261030/HANDOFF.md；私人早報移除入口：/Users/lordmi/Downloads/ai-news-private-digest-removal-20261030/HANDOFF.md。這些為已完成階段證據，不是待重跑工作。

## 10/31 分支清理

本機與GitHub均已移除 `codex/featured-duplicate-fix`、`codex/featured-selection-review`、`codex/retire-canary`及 `codex/t04-gemini-summary`。前述三個功能修正已有主線等價內容；T04分支依維護者指示刪除，相關現行功能已各自整合master，不重啟摘要備援。

GitHub目前保留master及asset-version-git-baseline、copy-news-id、gemini-translation、source-health-upstream-cleanup四個codex分支；本機另有reader-summary-translation-fix、retire-gemini-summary。這些分支提交均已包含於master。Gemini翻譯舊工作目錄 /Users/lordmi/Downloads/ai-news-radar-gemini仍保留，可另行指定清理。

## 最近十天其他完成紀錄

| 日期 | 最終結果與續接邊界 |
| --- | --- |
| 10/30 | 核准保留HF首段、補位評分、Juya／官方文字追取、品質診斷與細粒度資格；已在10/31發布，不保留「只完成本機、待發布」接續步驟。 |
| 10/28 | 來源品質修正與AIBase降級已由 `aaba6389dbb0` 發布；HF／重點摘要與金額翻譯補修也已發布，不能因舊分支歷史重列為待合併。 |
| 10/27 | T04 Gemini摘要備援退役結案。通用API／手動診斷／結果通知休眠保留，現有讀者翻譯繼續；[裁決](T04_GEMINI_SUMMARY_RETIREMENT_20261027.md)。 |
| 10/26 | 翻譯快取唯讀量測結案，維持現況，不啟動觀察或預警；[結案](TRANSLATION_CACHE_T06_MEASUREMENT_20261026.md)。 |
| 10/25 | T01一般列表事件篩選已發布；T02模型生命週期與T03摘要回顧結案，T05 Canary移除結案。CyberQ／AlphaLab以官方RSS進入一般池，保留未審來源與用途限制。 |
| 10/24 | PG發布者治理與D+選稿／列表簡化正式發布並結案；不重開補修或自動啟動下一階段。 |
| 10/23 | BR同事件合併、24小時資格與前端同代資料檢查完成發布。 |
| 10/22 | 來源觀察提前停止並以方案A集中評估，A06正式發布；觀察設定false，不補七日驗收或結案信。 |
| 10/21 | 撤回私人早報自動生成／派送目標；後續已完成停用與10/31程式移除，不恢復當時接續工作。 |

## 下次接手

先讀任務台帳的目前待辦，再核對實際Git、工作目錄及來源健康。公開新聞維持24小時窗口與現行來源／用途資格；實作新的來源、評分或產品能力時，依相關權威文件另行處理。

更新本頁時以臺北日期計算十天窗口，只保留目前有效狀態、近期完成結果與必要入口，刪除超期項目和被取代的接續步驟。當前規則依權威文件維護，不藉由保留整串舊歷程傳遞。
