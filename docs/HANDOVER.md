# AI News Radar 交接摘要

更新：2026-10-31（臺北）。本頁僅保留目前有效狀態與2026-10-21起的交接紀錄；超過十天的項目與歷程已從本頁移除。任務清單以[TASK_LEDGER](TASK_LEDGER.md)為準，產品／來源／操作細節分別依README、SOURCE_COVERAGE與OPERATIONS。

## 10/31 來源摘要移除發表尾註（實作完成，發布驗收中）

依維護者要求，所有使用來源摘要的前端顯示統一在截短前移除末尾的「本文最先發表於…」「本文〈標題〉最初發布於…」與英文 appeared first on 等發表聲明；來源名稱及連結保留。共用itemSummaryText涵蓋來源首段、一般新聞及重點來源摘要備援，生成AI摘要不變；原始來源、翻譯快取、評分與翻譯預算不改寫。

新增36組中英文／三種摘要欄位尾註案例與正文保留、純尾註及不改寫來源測試；相關58項、JavaScript語法與差異檢查通過。以臺北21:00:37正式資料93篇離線回放，9篇顯示摘要去除尾註，英文原文備援亦通過檢查；OpenAI募資摘要保留110億／300億美元正文。共同資產更新為20261031-summary-clean1，待GitHub與正式站桌面／手機驗收後結案。

## 10/31 The Decoder讀者翻譯補修（已發布並驗收，結案）

維護者回報正式站有一則The Decoder標題未翻譯。重新下載臺北20:05:28正式快照並核對最新主線，確認新聞4fe9c610a0a546976837774949a06b2f4dbf77db（OpenAI募資未達目標）title_zh為null；17:35:30首次翻譯留下invalid_translation後，原流程六小時不補試，其他新聞仍正常翻譯。未保留首次provider原回應，不能斷言是空回應、原文重送或品牌佔位符哪一項驗證失敗。同篇來源摘要譯文另把$11 billion／$30 billion寫成11百萬／30億美元，正確量級應為110億／300億美元。

修正範圍：標題無效時在既有翻譯階段最多補試一次，僅傳固定修正提示與原始材料，不重送失敗回應；舊六小時拒絕中的標題滿30分鐘可補救一次，失敗後維持六小時冷卻，避免每輪重試。預算不足而未送出的補試保留到後續輪次。摘要不新增補試，429及暫時provider故障沿用原規則。45秒單次／120秒整輪／最多6次請求、80候選與原Gemini模型均保持。

顯示翻譯重用既有Decimal金額解析，檢查受支援的幣別與量級，不做匯率換算、金額所屬公司判定或一般語意查證。新回應及當期快取都檢查，錯誤的當期快取移出後走正常翻譯；失敗時保留原文，不展示舊錯譯。來源摘要／標題、歷史快取、選稿及事件資格不因顯示校驗改寫。固定正式快照僅兩筆當期摘要快取被攔下，不做全庫重譯。

首次修補22de9f2a8cbe的正常刷新38e731f91e72（臺北20:50:55）仍有四筆回應未通過驗證，目標title_zh尚未恢復，錯誤summary_zh已停止顯示。追加精確品牌回填：缺失marker只有在回應中出現唯一、完整且完全相同的正典名稱時才還原，不接受別名、模糊匹配、額外重複或歧義。健康只增加固定枚舉的失敗彙總與還原筆數，不存provider原回應／逐項新聞紀錄；狀態升v5清除舊驗證語意的短期拒絕，成功翻譯快取保留。

本機完整2000項通過，98個既有feedparser警告；Python編譯與差異檢查通過。24項新增回歸涵蓋本案金額與舊拒絕快取、單次修正、再次失敗冷卻、30分鐘補救、額度／時間上限、摘要不補試、缺憑證原文回退、不推測幣別及精確品牌還原邊界。測試使用模擬provider，沒有呼叫真實模型或覆寫正式data。證據保存在 /Users/lordmi/Downloads/ai-news-title-gap-20261031/ 。前端資產無變更，維持20261031-security1。Groq第五項維持暫緩，不增加監控、排程或provider。

修補[4beb9d04e444](https://github.com/seisyuku/ai-news-radar_zhtw/commit/4beb9d04e444d98d47bbc50690f6213964b142eb)已整合master；[GitHub CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41203524593)1999項通過、1項Git資產比較分流，[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41203524330)成功。既有[正常公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41203574252)產生1dd95b566107，[資料Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41203718128)成功；臺北21:00:37正式資料中目標title_zh及summary_zh均已恢復，金額為110億／300億美元及1.25兆美元，目標拒絕記錄清除。當輪4候選、2次請求、2筆成功，另外3次驗證拒收彙總為原文未改2次、金額1次，均在既有上限內；沒有證據能從這些其他拒收推回17:35首輪的精確原因。

正式站首頁、app.js及七份相關JSON共9檔HTTP與生成提交一致；目標中英文主／副標、完整來源摘要與金額通過資料核對。1440桌面／390手機實際搜尋目標後，中文主標可見、英文原文保留副標、無JS例外或橫向溢出，治理ready；來源失敗／降級均0。[正式站](https://seisyuku.github.io/ai-news-radar_zhtw/?fix=20261031-reader-title)。本案已發布並驗收結案，沒有待恢復標題或新增監控項目。

## 10/31 社群退役與資安分類（已發布並驗收，結案）

目標：將一般分類「社群」改為「資安」，建立分類、統計、篩選、重點連動與標籤功能，完整移除社群專用收件與顯示機制。依維護者確認的本節計劃，階段1～7均完成：後端a910ced30573先行、正常刷新738a761f45d2產生配對資料，再發布前端a5c54b36cb71。GitHub CI／資產／Pages、同代HTTP與正式站驗收均通過，本案結案，沒有必須續行的工作。先前用詞統一已人工審閱通過，維持結案、不追蹤。

### 範圍與判定

- 資安主題涵蓋AI產品／模型／Agent／開發環境的漏洞與修補、攻擊與外洩、提示注入／越權／供應鏈，以及有實質材料的防禦產品更新或安全研究。一般平台重大事件沿用原有來源限定例外，不擴張為全領域資安聚合站。
- 主題與事件分開：有具體方法與結果的安全研究可進資安分類；security事件徽章須有具體漏洞、攻擊、外洩、修補或安全披露材料。重點仍須通過發布者／材料資格、I／P／E／C及70分門檻，不因分類取得加分。
- 原始標題與來源摘要作判定材料，翻譯與生成摘要不作新增證據。排除玩笑、裝扮、泛稱安全、兒少／內容安全、駭客松及既有範圍外教學；同篇真有資安事件時，不以出現排除詞一律整篇否決。材料不足時保守不標。
- 沿用既有來源、24小時窗口、I／P／E／C公式、核心3分、新鮮度及Groq／Gemini既有用途。零篇／零則可接受，不增來源、模型分類呼叫、排程或監控，Groq第五項維持暫緩。

### 本機實作與驗收結果

- 新增scripts/security_topics.py，使用原始標題／摘要分別判定主題與事件；公開archive／resolver、一般與全量列表、模型窗口、事件primary／sources及治理投影皆帶布林security_topic。衍生欄位由公開輸出覆本附加，不作事件配對或評分證據，不更改ID／時鐘或impact-v2公式。前端僅讀布林true，不用事件徽章或來源名稱補猜分類。
- 分類導覽、進階選單、分類篇數、三種閱讀模式、搜尋／來源／事件交叉篩選、重點連動、空區、標籤／去重及資安樣式已完成，共同資產20261031-security1。
- X API／SocialData／TikHub收件器與專用額度／間隔／狀態處理、probe、作者篩選與健康顯示、workflow憑證接線及force_tikhub、專用OPML／環境範本／demo指南及未使用的社群tier已移除。保留一般RSS／OPML、原來源資格、論壇／未證實貼文排除與共用健康歷史測試。舊paid-source-state.json不再讀寫，但不刪歷史檔或操作憑證。
- 固定基準為master def13a729491及臺北10/31 15:59:35快照，修改前後同輸入離線完整生成，真實網路／翻譯／摘要呼叫皆0。一般AI105篇、全量去重120篇、archive7580筆保持；AI文章順序／分數／來源權限／發布與收錄時間、事件state／ID、價格及翻譯／摘要快取逐項一致，重點均0則。這是固定材料回放，非新的線上來源健康盤點。
- 新資安分類5篇，其中2篇符合現有精選條件、3篇有具體security事件標籤。VulnOps管理模式與安全代理比較保留資安主題、移除事件徽章；萬聖節裝扮及只有標題重述的Epoch漏洞條目不取得資安主題或事件標籤。原社群5篇保留在其他適用分類，三篇原本僅社群者沿用產業fallback，沒有直接轉成資安或刪新聞。
- 完整1976項測試通過，98個既有feedparser警告；退休API專用測試隨功能移除，共用來源跳過／失敗歷史移至test_source_health_skips.py並保留。JS／Python語法、workflow YAML、資產版本與git diff --check通過。殘留舊啟用／強制執行與測試憑證時，真實main流程只呼叫既有價格感測器，不呼叫退役provider。
- 隔離Chrome實測1440桌面及390手機：精選資安2篇／全部AI資安5篇／事件篩選3篇，搜尋與來源、全量與合併開關正常，篩選不改全站統計，資安標籤不重複，無JS例外或整頁橫向溢出。舊資料缺欄位及零結果顯示0篇而保留一般新聞；混版時重點投影拒收、一般新聞仍可讀。未關閉既有治理guard或改門檻。

基準備份、移除函式清單、回放與comparison.json、測試日誌、browser-results.json及桌面／手機截圖位於 /Users/lordmi/Downloads/ai-news-security-20261031/ 。正式data／item、私人feeds、憑證及歷史狀態未因離線驗證變更；正式發布資料由正常刷新生成。本輪依維護者指示完成第7階段發布並驗收，不自動增加來源、分類子選單、模型判定或監控。

### 正式發布與驗收完成

後端[a910ced30573](https://github.com/seisyuku/ai-news-radar_zhtw/commit/a910ced305735350c7b46c1c1dd2521de71e5818)已保留最新master快照後先行發布；[後端離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41187240534)1969項通過、1項資產比較分流，[後端Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41187240328)成功。既有[正常公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41187350005)產生資料738a761f45d2，[資料Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41187471281)成功且六份主要JSON正式HTTP先驗同代，才推送前端[a5c54b36cb71](https://github.com/seisyuku/ai-news-radar_zhtw/commit/a5c54b36cb719e3fd5eab5788fa3e50e384e3900)。[前端離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41187611633)1975項通過、1項資產比較分流，[前端Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41187610914)與[資產版本檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41187611542)均成功；本機完整1976項已通過。

發布快照為臺北10/31 17:07:26：AI新聞96篇、精選27篇、資安3篇（其中精選2篇、具體資安事件2篇）、重點0則；14/14來源正常，失敗／降級及RSS訂閱失敗皆0。這是新的發布快照，與前述15:59固定輸入回放分開記錄。公開資料的新聞副本皆有布林security_topic，事件／治理ready；source-status不再包含三條退役社群API狀態。

首頁、manifest、六資產、九份JSON、一份資安新聞HTML及其JSON resolver共19檔正式HTTP與發布提交逐檔一致。正式站1440桌面／390手機的精選／全部AI／全量／合併、來源／搜尋／事件篩選、導覽／手機選單及標籤去重均通過；全站統計不因篩選改變，無JS例外或整頁橫向溢出。正式站：[GitHub Pages](https://seisyuku.github.io/ai-news-radar_zhtw/?review=20261031-security1)。發布HTTP、瀏覽器結果、截圖及備份位於 /Users/lordmi/Downloads/ai-news-security-20261031/release/ 。正式data／item由正常刷新產生，沒有以本機離線資料覆寫、改排程或重啟已結案工作。

### 執行順序與完成條件

| 階段 | 實作工作 | 驗收條件 |
| --- | --- | --- |
| 1 邊界與基準 | 重新核對最新master、工作目錄、資料及來源狀態；盤點社群專用呼叫、workflow、狀態、測試與文件，固定同一輸入建立比較基準；保留未提交的人工審閱結案文件。 | 每個待移除項目有用途及呼叫者清單；判明共用RSS／OPML、品質排除及發布者權限不能隨專用機制刪除。 |
| 2 共用判定與資料 | 建立scripts/security_topics.py共用判定，輸出主題與事件兩個不同結果；每篇公開新聞新增布林security_topic，security事件徽章採事件結果並保留既有材料資格。盤點一般／全量／事件primary與sources、快取投影及新聞資訊輸出的實際複製路徑，保持欄位一致。 | Python正反例涵蓋中英繁簡、否定／背景提及、只有標題、AI安全歧義、萬聖節誤判及同句真實事件；主題不等於事件，不自行升級證據。新增欄位不更動原有事件ID／時鐘／policy或來源權限。 |
| 3 前端相依功能 | SECTION_DEFS以security取代community；selection.js讀取security_topic，不另寫一套資安關鍵字。同步導覽／手機選單、分類篇數、列表／重點交叉篩選、空區、標籤與樣式；事件徽章與主題同名時去重。 | 精選／全部AI／全部收錄、來源／搜尋／產業事件篩選皆能交叉使用；分類篇數對應現有模式且全站統計不變；容許跨分類，不將舊社群成員直接轉入資安。缺欄位舊資料不臆測資安，其他分類仍可讀。 |
| 4 社群專用機制退役 | 移除community分類／中文廠商歸類／色彩、無呼叫的舊社群補位函式；移除X API、SocialData、TikHub收件器與手動probe、作者／社群專用篩選、額度／間隔處理、workflow輸入及憑證接線、專用範本／測試／說明。核對共用引用後才移除未使用的來源tier與付費狀態產生機制。 | 即使環境殘留舊憑證與啟用變數，生成流程也不發出退役provider請求；workflow不再提供force_tikhub等入口。共享新聞、RSS／OPML、來源治理與論壇／未證實貼文排除防線正常；私有feed／憑證與歷史新聞不刪改，不把舊tier轉成更高資格。 |
| 5 同輸入比較與回歸 | 離線輸出置於Downloads，跑完整Python測試、JS語法／模組／資產版本檢查；列出資安分類、事件徽章、重點資格與排序的逐筆差異及理由。 | 誤判修正可解釋；其餘來源資格、文章ID、去重、原發布／事件時間與評分公式保持，差異不因重抓或模型輸出造成。不得用刪除品質測試來掩蓋退役以外的回歸。測試不覆寫正式data或呼叫真實翻譯／摘要provider。 |
| 6 桌面／手機與文件 | 實測1440與390寬度的導覽、篩選、標籤、零資料／缺欄位／資料過渡情境；更新README、ROADMAP、SOURCE_COVERAGE、OPERATIONS、台帳及本節。 | 無JS例外、重複資安標籤或整頁橫向溢出；「社群」僅可出現在保留的新聞文字、品質限制或必要退役紀錄，不能再代表可用功能。移除清單逐項對照，既有用詞審閱結案不重開。 |
| 7 發布階段 | 接獲commit push指示後保留最新bot提交，先發布後端並由既有公開刷新產生含security_topic的資料，再部署共同版本一致的新前端；完成CI、資產、Pages、HTTP同代與正式瀏覽器驗收。 | 正式站資安分類可用且社群入口消失，正常刷新無退役provider接線；保留既有事件state／時鐘。出現問題時另發修正提交，必要時撤下資安入口，不回推舊資料或重啟社群收件。 |

建議以「資安判定與資料」「前端分類整合」「社群流程移除」「驗收與文件」分段形成可審查差異；各段不混入無關草稿。前端必須等配對後端資料可用後再正式部署。測試輸出、固定輸入與比較證據置於Downloads，不另新增例行報告。

### 建議模型與思考強度

主實作建議GPT-6.1 Sol／High，同一模型完成後端、前端、移除與回歸。跨資料投影一致性、隱藏社群呼叫或難以解釋的回歸可短暫提高到xhigh；文件收尾與依程序發布可用Medium。這是依本案相依範圍所作的工程建議，非官方對本案的保證；不需全程max，也不因此自動切換模型或啟動子代理。

已查核[官方模型說明](https://developers.openai.com/api/docs/models/gpt-6.1-sol)：GPT-6.1 Sol適用複雜程式工作，支援low／medium／high／xhigh／max；[Codex模型清單文件](https://learn.chatgpt.com/docs/app-server#list-models-modellist)說明實際選項依帳號與客戶端提供為準。本案新增的是確定性程式判定，不把此開發模型加到網站例行刷新。

## 10/31 前端用詞統一（人工審閱通過，結案）

維護者要求先全部實作再人工審閱；因遠端手機無法開啟本機連結，另明確指示commit／push至GitHub。程式692c0e9c1d18與共用資產版本20261031-wording1已整合master並發布GitHub Pages。沒有改動70分門檻、來源／材料資格、新鮮度、24小時窗口、資料schema或API路徑；正式data與item僅由既有正常公開刷新生成，未以離線驗證輸出覆寫。

| 概念 | 前端統一名稱與範圍 |
| --- | --- |
| 一般文章 | AI 新聞／精選新聞／全部 AI 新聞，以篇計；精選為一般閱讀條件，與重點門檻不同。 |
| 入選事件 | 重點訊號，以則計；後續卡改為更多重點訊號，排序稱依重要性／依時間，導覽總覽取代熱點。 |
| 全部內容 | 全部收錄內容；沿用合併重複開關，同發布者重複連結仍合併顯示，沒有改去重規則。 |
| 來源 | 來源類型（單一選單）／發布者／抓取來源／RSS 訂閱；一手來源包含官方與評測第三方，不混稱全部為官方。指定來源清單沿用既有資格。 |
| 分數 | AI 相關度／優先閱讀分／重點排序分；第4～5則重點卡顯示實際impact-v2排序分，不再顯示舊多源熱度，排序計算本身未改。 |
| 摘要 | AI 摘要／來源摘要／來源首段或其譯文，依實際來源標示。 |
| 時間與健康 | 資料更新時間、新聞發布／首次收錄時間；本輪讀取量不稱今日累計，抓取來源失敗與RSS訂閱失敗分開標示。 |

前端載入錯誤使用區域名稱而非JSON檔名；新聞資訊頁生成器已中文化欄位與狀態，原始JSON欄位保留，正式新聞資訊頁已由正常刷新更新。README同步用詞。只修正顯示與篩選入口命名，舊sourceTypeFilter程式介面保留相容，頁面只保留一個來源類型選單。

驗證：完整1991項通過（98個既有feedparser警告），JS語法、Python編譯及資產版本檢查通過；隔離Chrome在1440桌面及390手機寬度實際載入，來源篩選、精選／全部AI／全部收錄切換、合併開關、空區及新聞資訊頁皆正常，無JS例外或整頁橫向溢出。正式站臺北15:59:35快照顯示105篇AI新聞、30篇精選、0則重點，治理ready；篩選後全站統計不變。

發布驗收：[程式692c0e9c1d18](https://github.com/seisyuku/ai-news-radar_zhtw/commit/692c0e9c1d18bf9a1d78abdc3478cf4167a2de24)、[離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182642617)1990項通過／1項資產比較分流、[資產檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182642586)、[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182641617)皆成功。[正常公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182725807)產生940aaf86a7ee，[資料Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182843549)成功；首頁、manifest、六資產、九份JSON及一份中文新聞資訊頁共18檔HTTP內容與該生成提交一致，來源失敗／降級與RSS訂閱失敗皆0。正式站1440桌面與390手機瀏覽器檢查通過，無JS例外或整頁橫向溢出。

正式站入口：[GitHub Pages正式站](https://seisyuku.github.io/ai-news-radar_zhtw/?review=20261031-wording1)。截圖、browser-results.json、單頁審閱範例、測試及發布備份位於 /Users/lordmi/Downloads/ai-news-wording-review-20261031/ 。維護者已確認人工審閱通過，本案結案，無需後續追蹤；Groq第五項維持暫緩。

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

核心／產業動態共用I／P／E／C與70分門檻，核心僅加3分；混合排序最多五則。新鮮度為2^(-sqrt(t/48))，保留48小時減半點、加快前段衰減，24小時窗口及來源資格保持。後端80085cca0c03、前端4a1148c616d4已在master，impact-v2已正式上線；本次用詞發布將共同資產升為20261031-wording1，排序規則不變。

先前GitHub平台事故造成的待驗收狀態已解除；原[離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41102288333)與[資產檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41102288393)均成功。本次Groq發布再核對16檔正式HTTP、同代資料與讀者端guard／混排，全部通過。規則及固定輸入結果見[全區影響排序](FEATURED_IMPACT_20261031.md)。降標研究依維護者裁決維持現狀結案，不重列待辦。

## 目前續接狀態

正式專案為 /Users/lordmi/Documents/ai-news-radar_zhtw，分支master；最新資安分類前端a5c54b36cb71、後端a910ced30573與正常刷新資料738a761f45d2已正式發布並驗收，後續版本以master紀錄為準。私人早報移除、新聞品質、全區影響排序及Groq前四項修正均已發布並驗收；前端用詞統一已通過人工審閱，結案且無需追蹤。資安分類與社群退役亦已結案，沒有必須續行的工作，待辦以任務台帳為準。

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
