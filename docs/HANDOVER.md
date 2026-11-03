# AI News Radar 交接摘要

更新：2026-11-03（臺北）。本頁僅保留目前有效狀態與2026-10-25起的交接紀錄；超過十天的項目與歷程已從本頁移除。任務清單以[TASK_LEDGER](TASK_LEDGER.md)為準，產品／來源／操作細節分別依README、SOURCE_COVERAGE與OPERATIONS。

## 11/3 Claude公告漏報補洞第1～4階段（已發布並驗收，結案）

維護者已授權按階段實作，每階段完成後直接在對話回報結果及下一階段模型／推理強度；遠端手機操作不依賴本機報告或跳轉頁面。已核准只接Claude Product announcements、沿用Anthropic官方逐篇用途且同發布者只計一票、補強既有Issue／診斷流程。來源限RSS／Feed及HTTP可取得的結構化文字，轉檔、非結構化正文搜尋、圖像及影音處理均不在本案。

第1階段新增`parse_claude_product_announcements_items`與獨立fetcher，只讀固定官方索引內嵌JSON；不執行腳本、不補抓文章或附件。單頁2MiB、最多20篇，分類／型別／slug／日期檢查後去重限量，回補沿用官方45日設定；未來日期即使落在既有六小時容忍內也排除。合法空索引、僅舊文或未來日期的有效資料可成功回零；缺少結構、必要欄位全失效或歧義payload回報來源失敗。原始日期與日期精度先保存在RawItem metadata，第2階段已接入公開投影。

49項新增測試、相關81項與完整2212項通過（98個既有feedparser警告）；完整測試需將內建Node的bin加入PATH。Python編譯及差異檢查通過。臺北11/3 16:13:15以既有HTTP session隔離抓取：一次請求588849 bytes、13篇／13網址、來源正常，包含Message Threads且UTF-8標點保持。官方只給2026-11-02，按已接受規則換算UTC零時；固定11/2 20:00臺北回放可發現，當前24小時窗口已過期，不以抓取時間續命。

第1階段精簡文字樣本與隔離診斷位於`/Users/lordmi/Downloads/ai-news-claude-announcements-stage1-20261103/`。第2階段已將入口註冊為`official_ai/claude_product_announcements`，使用獨立子來源健康與既有失敗歷史，Claude失敗保留Anthropic正常新聞、反向失敗亦保留Claude；有效空值不降級。`claude.com/resources/articles/`沿用Anthropic官方逐篇用途，其他Claude頁面、未知子網域及仿冒host不取得權限。兩入口計票均為`publisher:anthropic`，沒有新增獨立發布者票。`source_published_date`、`source_time_precision`是可選的向後相容欄位，保留於archive、一般池、resolver及事件引用；舊文章不補造精度。

第2階段新增30項，相關250項與完整2242項測試通過（98個既有feedparser警告），Python編譯及差異檢查通過。固定樣本跑完整main：可進原始／一般AI池、沒有強制入選重點；到期後退出讀者池但保留archive／resolver。真實前端治理驗證器接受投影，跨網址改寫仍可能兩事件但同發布者只算一票。

臺北11/3 08:46:04保留快照配對離線生成：原archive7601筆全部ID／URL／發布／首次與末次觀測／原標題／摘要保持，新增13篇至7614；一般AI172、全部183、重點2均保持，173個當期事件的ID、initial/effective/expiry與active phase均相同。新13篇resolver逐筆等於archive，Python與讀者JS治理ready。此為以16:13取得的索引回放08:46截點的反事實收件測試，不能宣稱當時已可見或當時抓取正常。七日對照為4個公告候選、1449筆既有記錄，hard／possible重複均0；樣本不足5，僅作輔助，不推論整站品質。證據位於`/Users/lordmi/Downloads/ai-news-claude-announcements-stage2-20261103/`，含before／after完整輸出、`verification.json`及`overlap.json`；全程無真實模型或網路呼叫，不覆寫正式data。

第3階段已補強既有feedback Issue模板：分開收集臺北觀察時間與頁首資料更新時間、頁尾版號、原始文字來源／發布資訊，以及查看位置、模式與篩選。未知欄位可如實註記。OPERATIONS新增六步定位：綁定同代快照→入口健康→archive與時間→公開池與品質追蹤→事件／重點→證據與缺口結案。明確區分公開`items_all_raw`與原始HTTP回應、舊快照缺診斷與未收件、現在規則回放與歷史實際結果；介面截圖僅定位顯示問題。沿用既有Issue與診斷資料，沒有新增CLI、來源、評分或排程。

補充案例已查六份歷史快照；下表時間皆為臺北。10/29 10:35快照61168d24c6e9的archive、latest、all-mode、daily、merged及source-status六檔SHA256，均與既有pulse-quality固定樣本相符。此次只讀歷史JSON及兩個已知官方URL的metadata／JSON-LD，未搜尋正文或解析附件、圖片、影音。

| 案例 | 保存快照的證據 | 可支持的結論與限制 |
| --- | --- | --- |
| ChatGPT API credits | 10/29 10:35的61168d24c6e9已有Juya對照早報提及，政策為control且不進公開一般池；10:56的6829725f47e6已有RuntimeWire原始／一般AI池文章，但重點為`no_current_qualified_article`。10/30 07:35的9adcdc3fb165中Simon Willison文章也在一般池，來源用途禁止重點。10/31 12:35的2a06a12f580d中LLM Rumors領取教學、11/2 13:35的4af7f544eafb中數位時代開通教學，均保存`out_of_scope`追蹤。 | 已證實不同時間有對照、一般收錄、用途限制與教學排除，不能歸為全面未抓到。官方[政策頁](https://developers.openai.com/api/docs/guides/chatgpt-api-credits)現在HTTP200，但無發布時間metadata，六份快照均無此URL。01:41的6a827d395150等抽樣快照中既有primary recovery為0次，不能推成全期間0次；也不能用後來的補讀能力宣稱10/29已可補證。 |
| Alphabet 2026 Q3 | 10/29 10:35的61168d24c6e9中CNBC財報前預告與改標題稿、The Verge均在原始／一般AI池；當時事件未選入重點，保存`no_current_qualified_article`。CNBC同URL稿件保留的摘要仍為「準備公布財報」，未給出具體財務數值；The Verge摘要聚焦搜尋成長。 | 已證實收件及一般池可見，保存材料不足支持回報中的Cloud／現金流具體主張；不能說整則事件沒抓到。官方[CEO講稿](https://blog.google/company-news/inside-google/message-ceo/alphabet-earnings-q3-2026/)現在HTTP200且JSON-LD有日期，但六份快照均無此URL。當時配置是Google AI／Gemini分類RSS；缺原始Feed回應，不能判定該官方稿當時未被Feed提供或被解析漏掉。 |

查核快照依序為61168d24c6e9（10/29 10:35）、6829725f47e6（10/29 10:56）、9adcdc3fb165（10/30 07:35）、6a827d395150（10/31 01:41）、2a06a12f580d（10/31 12:35）、4af7f544eafb（11/2 13:35）。前三份沒有`news_quality`，以上歷史結論直接讀當版池／治理資料，未套用現行診斷反推。沒有編輯端原始觀察時間／版號、當時HTTP回應或下游Social Editor選稿紀錄，所以結論只及於已查快照，不能核定原回報那一刻的全部原因。本輪沒有提高分數、強制入選、回補舊文或新增Alphabet入口。

機器可重查的快照雜湊、文章／事件ID、池成員與判定、當前官方metadata保存於`/Users/lordmi/Downloads/ai-news-claude-announcements-stage3-20261103/historical-audit.json`，用於保存本輪歷史證據；結果直接在對話呈現。既有品質診斷／文字來源邊界77項通過（1個既有feedparser警告），差異檢查通過；本階段僅改Issue與文件，前階段完整2242項結果保持適用。

第4階段已完成累積14個檔案的整體複核。發現並修正一個健康邊界：合法分類索引若只有已排除的外站連結、非文章類型或其他分類，應健康回零；原先會誤報`invalid_source`。現在將已知收錄範圍過濾與文章欄位驗證分開；若有本案候選但必要欄位全失效，即使混有排除項仍回報錯誤。沒有擴張收錄類型、抓取位置或格式。調整4個既有反例的健康預期，新增3個回歸；本案合計82項新增測試，最終完整2245項通過（98個既有feedparser警告），Python編譯及差異檢查通過。

修正後重讀第1階段保存的結構化索引，產生的13篇ID、來源、標題、摘要、URL、發布日期與精度，逐項等於第2階段配對輸出；政策revision保持`c8484c3bb9fd3de075b75cf96a9a2469efe41120789b8aa743c24293397a19c7`。因此沿用已驗的7601→7614封存、172一般AI／183全部／2重點及173事件ID／時鐘保持結果，不重抓來源或重跑模型。最終核對正式data、assets、workflow均無差異；工作樹只有本案14檔，沒有私人Feed、憑證或環境檔。

最終本機證據位於`/Users/lordmi/Downloads/ai-news-claude-announcements-stage4-20261103/verification.json`，綁定變更檔案SHA256、第2階段配對結果及第3階段稽核證據雜湊。本機原驗收基底為master `d5f85fd8f3d0e8a7b03de559f2cd533e7f0344a4`。維護者11/3授權commit push後，保留並整合18筆並行快照至3bfe099dd4ac；整合後2245項測試通過，程式提交[fc96e417d4bd](https://github.com/seisyuku/ai-news-radar_zhtw/commit/fc96e417d4bd0c58797413f4230adea25d0609b9)已推送master。[CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41617120442)、[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41617120019)、[正常刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41617142956)及資料提交[6d58d3d27c8d](https://github.com/seisyuku/ai-news-radar_zhtw/commit/6d58d3d27c8df6c1f96effc600e8bb4daf272a4c)的[Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41617441392)均成功；資料由既有Actions生成，未以本機輸出覆寫。

正式臺北11/3 18:11:39快照：Claude子來源成功13篇、353ms，來源失敗／降級均0；13篇官方文章均為Anthropic、rank0、已核准逐篇用途，保留原日期與date精度。18份正式HTTP首頁／manifest／文字資產／政策／JSON與生成提交逐檔bytes相同，13份公開resolver逐筆等於archive。Message Threads ID為`4d9d80a2333ecca761556dbad4a4301e78ea06cb`，原URL與2026-11-02T00:00:00Z保持；已封存但超過24小時，不強制重新進讀者池。Python驗證與實際上線JS治理valid／resolve／meta均通過，正式一般AI184篇、全部203篇、重點3則，讀者guard可讀3則。

發布證據保存於`/Users/lordmi/Downloads/ai-news-claude-announcements-release-20261103/http-6d58d3d27c8d/verification.json`，含HTTP雜湊、resolver、來源狀態與前後端治理；本機與正式刷新／Pages均已驗收完成，無必須續行功能。日期只有天的換算與跨網址改寫可能分事件，維持已接受邊界；原回報時刻與原始Feed／下游選稿缺口也保持。

## 11/3 AIBase用途裁決（已發布並驗收，結案）

AIBase維持rank 4與一般收錄，關閉重點／雷達，其他來源維持；本機完整2163項、固定快照重投影通過。裁決提交[757fcbcbd135](https://github.com/seisyuku/ai-news-radar_zhtw/commit/757fcbcbd135c47b140990f84cf271537cfd2ed3)已整合最新master並推送；[CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41555128484)與[正常刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41555128982)成功，資料提交2819ba05e83b的[Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41555340395)成功。臺北11/3 08:46:04快照：18份正式HTTP檔與生成提交位元一致，465筆AIBase封存政策均為rank 4／僅一般收錄，當期重點支持與雷達均無AIBase。治理ready、Python與讀者JS同代驗證通過，重點2則、來源失敗／降級0；正式資料由正常Actions生成，沒有以離線輸出覆寫。驗收證據位於`/Users/lordmi/Downloads/ai-news-source-review-20261103/release/verification.json`。本案已發布驗收，無必須續行項目。 政策與審查邊界見[SOURCE_COVERAGE](SOURCE_COVERAGE.md)最新節。

## 11/1 服務條件與內容類型修正（已發布並驗收，結案）

維護者已授權按本輪診斷實作並推送master，重大變更先詢問。邊界限額度／計量／共用配額及付費帳戶限制沿用pricing，原始摘要可提供動作與機制；資料訓練用途／退出條件及浮水印部署只作industry_news材料；修正研究刺激材料tips誤排及媒體購票宣傳誤收。不新增類別、來源、模型、排程、評分級距或門檻，翻譯／AI摘要不作證據。研究及政策取得材料資格後仍可能不達重點分數。

新增33項正反例通過；包含原文支持、競品條件借用、否定／傳聞／缺生效時間、中文、翻譯與生成摘要不能補證、未審來源、介面合併不當併購、事件時鐘與Python／瀏覽器資料契約。完整2162項通過（98個既有feedparser警告）、Python編譯與差異檢查通過。14日AI相關度回測涵蓋2971篇，2790→2787，僅移除3篇TechCrunch峰會購票／人脈宣傳，新增0。

臺北20:55:48固定快照完整離線生成：一般AI58→57，僅移除購票宣傳；重點0→2，為ChatGPT付費帳戶限制及Chat／Work共用Token配額，均I15／P20／E20／C20=75。Daybreak資料用途、浮水印部署及刺激材料研究3篇取得industry_news材料資格，仍未達重點門檻。讀者事件投影59→58只退出該宣傳；保留事件身分／有效與到期時間、完整事件state、archive、價格、雷達內容及翻譯／摘要快取逐項一致；治理綁定雜湊按新選集重算。完整離線投影通過Python與瀏覽器guard。未呼叫真實provider，不以離線輸出覆寫正式data；證據留於 /Users/lordmi/Downloads/ai-news-service-terms-release-20261101/。程式[21f572d43761](https://github.com/seisyuku/ai-news-radar_zhtw/commit/21f572d43761de1801be0c40940cfaa867259c7f)已保留並行快照推送master；[GitHub CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41311343239)2158項通過／1項資產比較分流，[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41311342866)成功。既有[公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41311450787)產生1ebd142042c7，[資料Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41311548971)成功。

正式臺北21:29:09快照為57篇AI、2則主要重點（付費帳戶限制及共用Token配額，各75分），14/14來源正常，失敗／降級0，治理ready。首頁、manifest、六資產及六份JSON共14檔HTTP與生成提交逐檔一致；Python重算、讀者JS guard、跨檔meta與實際resolve均通過，可讀重點2則。前端資產未改，沿用20261101-empty-fallback2；只以現有Actions產生正式資料，不推本機回放輸出。本輪已發布並驗收結案，無必須續行工作。

同輪追加生效日期反例：僅具體月份／日期可支持未來排程，額度「from 100 to 200」及「on ChatGPT Pro」不當日期，May月份亦不當may推測。追加3項後完整2162項通過；既有正式21:29資料以補強後Python驗證器逐筆重算一致，不需額外重抓或模型呼叫。

## 11/1 空白候補與Factory誤判修正（已發布並驗收，結案）

維護者已確認前輪方案並要求commit到正式站。本輪依既定邊界實作：主要新聞原70分及I／P條件、最多5則；只有全站24小時有效主要名單為0且資料正常時，才採65分且P20／E20的原有合格候選，最多2則，卡片標候補。有主要不混入候補，篩選歸零不啟動、資料失效不啟動，沒有候補仍空；不加來源、模型、排程或新評分軸。保留passes的原主要門檻語意，另加selection_tier=primary／fallback／null，選集policy升為impact-v3-empty-fallback，schema仍2；Python與JS重算並拒收舊policy／偽造身分。

Factory修正限Factory Droid產品名稱及其直接發布句型，不把品牌名當作工廠產業／部署詞；真正工廠、銀行等部署保持原分類。完整2129項通過（98個既有feedparser警告），新增23項涵蓋前後端選集、兩則上限、P／E與65分界線、舊policy與偽造候補、資料缺失／失效、原24小時到期、主要出現撤候補、事件時鐘、篩選零結果、兩種排序及候補徽章、品牌／真實產業反例，以及中英混排的字詞邊界一致性。臺北10:35:28正式快照離線回放由0則變為Factory Droid主要1則，I15／P20／E20／C20=75，事件ID／有效與到期時間逐項相同；實際瀏覽器驗證器接受新投影。未用離線輸出覆寫正式data。

發布順序：先提交後端、契約及配對驗證器（共同資產20261101-empty-fallback1），由既有正常公開刷新生成v3資料，再提交候補顯示與配對前端（20261101-empty-fallback2），最後核對GitHub CI／資產／Pages、正式HTTP與桌面／手機及候補情境。過渡期間不相容資料保守拒收，一般新聞保持可讀。正式資料只由Actions生成。證據位於 /Users/lordmi/Downloads/ai-news-empty-fallback-release-20261101/ 。發布與驗收已完成，無必須續行項目。

後端ddde3d51c980與[GitHub CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41267869409)2123項通過／1項資產比較分流；先行後端與舊顯示的完整本機2124項亦通過。[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41267869230)成功後，[正常刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41267952897)產生b3583215ccd5，[資料Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41268060397)成功，四份主要正式資料HTTP逐檔一致。臺北11:08:50快照主要1則為Factory Droid 75分、候補0；來源失敗／降級0，Gemini0請求、55筆快取重用，Groq重用21則／新增1則／失敗0。配對前端與最終驗收見下段，沒有以離線資料填補。

配對前端[8117a6a700a7](https://github.com/seisyuku/ai-news-radar_zhtw/commit/8117a6a700a7c010191a23a227569421ad8935ba)、[前端CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41268188069)2126項／1項分流、[資產版本](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41268187954)及[Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41268187360)均成功。追加中英混排邊界對齊[a6b0acf1a3d5](https://github.com/seisyuku/ai-news-radar_zhtw/commit/a6b0acf1a3d5747085aea87512279193a775019c)，本機完整2129項、[最終CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41268457538)2128項通過／1項資產比較分流，[最終程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41268456752)成功；原正式資料亦通過對齊後Python與JS重算，不必額外重抓或重譯。共同資產20261101-empty-fallback2。

首頁、manifest、六資產與六份資料共14檔正式HTTP逐檔一致。1440桌面／390手機實際顯示Factory Droid主要新聞1則、沒有候補，治理ready，無JS例外或橫向溢出。隔離瀏覽器注入本機合約案例，確認3個候補最多顯示2則且有「候補」徽章；加入主要後只顯示主要1則，搜尋僅符合候補時顯示0、不另啟候補；無合格材料時0，資料unavailable時0且治理拒收。這些是隔離案例，不是正式來源另有3篇候補；沒有改動公開資料。來源失敗／降級0。本案正式發布並驗收結案，無新增監控、來源或模型預算。

## 11/1 重點新聞用詞統一與空白候補方案

本節為前輪用詞發布與方案紀錄；候補已依上方發布結果正式啟用。

維護者要求將讀者用詞統一為「重點新聞」，另規劃完全空白時放寬候補、重要新聞仍優先的方案。本輪用詞已發布並驗收，涵蓋標題、統計、搜尋與無障礙提示、展開／空白／載入提示、分享描述、manifest及維護文件；英文副標改TODAY'S NEWS，內部事件ID、欄位、評分與入選結果不變。共同資產20261101-featured-news1。候補規則僅完成規劃，不在本輪先行啟用；現行仍是impact-v2／70分與24小時窗口。

用詞[a516c1e916e5](https://github.com/seisyuku/ai-news-radar_zhtw/commit/a516c1e916e5b8bdf65a54f7ec0c5c30e55be226)已整合master，保留最新快照8eb4958d5f07；相關66項、兩份JS語法與差異檢查通過。[GitHub CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41266884261)2105項通過、1項資產比較分流，[資產版本](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41266884323)與[Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41266884320)成功。首頁、manifest、六資產與四份資料共12檔正式HTTP與發布內容一致；臺北10:35:28快照54篇AI／12篇精選／0則重點，14/14來源正常。1440桌面／390手機的主標、分類重點標題、統計、搜尋提示、空白提示及模式切換均通過，無舊用詞、JS例外或橫向溢出，治理ready。沒有觸發新模型請求或改寫生成資料。

### 建議規則與邊界

1. 先按現行70分及I至少30或P為20選主要新聞，最多5則，沿用影響／新鮮度排序。有至少1則時不補候補；因此只剩1則也不自動湊滿5則。新主要新聞出現即撤下候補，重要新聞不被候補擠到後面。
2. 只有全站24小時主要名單為0且資料／治理正常時，才從已通過既有來源、材料與事件資格的候選放寬至65分，另外要求E=20、P=20，最多2則，沿用既有新鮮度、來源限制與去重排序。主區仍稱今日重點新聞，候補卡標「候補」。不宣稱候補已達主要門檻。
3. 不因使用者搜尋、分類／來源篩選後歸零或資料暫不可用而降標。仍限24小時，不重置事件時鐘或延長舊新聞；沒有符合候補條件者仍明示無合格內容，不逐級降至60／55分、不新增來源、模型呼叫或排程。翻譯與生成摘要不作入選證據。
4. 後續若採納，先實作後端選集與主要／候補層級、升選集policy，再同步Python／JS重算驗證與前端；資料須明示候補身分，保留原分數與原主要門檻passes語意，不能在前端偷偷從一般列表補卡或關閉治理guard。一般列表與來源准入不變。

### 最新材料模擬與驗收計畫

重新同步master 8eb4958d5f07，正式HTTP快照為臺北11/1 10:35:28。抽取10/31 14:35:24～11/1 10:35:28約20小時的7份已存快照，現行主要名單皆0；65分且E20／P20、最多2則可使5份變成1則，另2份仍0。60或55分在同一材料gate下不增加內容。最近一份候補為Factory Droid 1.0，I15／P20／E20／C10、共65分；5份有結果者都是同一事件，不能視作5篇不同新聞或長期改善率。這是機械模擬，不改正式選集、不代表已做新聞價值人工審查。證據位於 /Users/lordmi/Downloads/ai-news-featured-empty-plan-20261101/ 。

另確認材料限制：Factory品牌字樣命中factory產業／部署詞，C被判10。僅在離線對照中將標題Factory拼為Fctry、其餘材料不變，C即20、總分75且passes=true。此為明確詞彙誤判，應在採納方案時分開檢視，不能把候補帶來的改善全部歸因於70分門檻太高；本輪未改評分程式，也未自動擴張為一般語意分類重做。

若採納，驗收須涵蓋主要3＋候補2只顯示主要3、主要0＋候補3最多顯示2、僅1候補顯示1、候補也不合格仍0、搜尋／分類歸零不啟動、資料失效不補、主要新出現撤下候補；並驗證24小時到期、事件去重／來源限制、Python與JS選集一致、混版拒收、桌面／手機及正式資料配對。發布依後端→正常刷新→配對前端順序，另行執行，不混入本輪用詞發布。

## 10/31 來源摘要尾註補修與模型輸入清理（已發布並驗收，結案）

維護者再次回報「文章（原標題）…」殘留。重新同步master 0231cda9e3a9並下載臺北22:51:18正式資料，87篇新聞中確認Claude小鼠手術條目的summary_zh含「文章〈Claude模型…〉最初發表於The Decoder」。英文summary本來就有The article…appeared first on，Gemini把尾註一起翻譯；第一版前端規則漏掉單獨「文章」前綴，前次僅檢查原先句型的驗收不足。本輪取代第一版的無待辦結論。

正式stories-merged共有44個news_summary欄位，含重複投影，實際22則AI摘要；這22則與500筆Groq成功快取未發現重複文章標題／發表聲明。快取一筆「部落格文章表示」屬正文歸因，保留。不能由此宣稱所有歷史回應都無問題。總結的來源輸入確實仍夾尾註，11組當期總結材料會受清理影響。

維護者續報無文章前綴的「（標題）…發表於The Decoder」。直接核對公開RSS，當下10/10篇description都有The article〈標題〉appeared first on The Decoder，證實來源原附標題重複尾註而非程式新增。先行補修9d9bcce9ec62已發布輸入清理；本輪再把舊譯文處理改為原文發布者＋句子邊界判定，不只枚舉中文前綴。

統一規則：新資料在送Gemini翻譯、送Groq總結前移除完整來源出版尾註，再做既有截長。舊譯文除標準明確句型外，從原文標準尾註取得發布者，只有譯文末句的發表／出現聲明指向同一發布者時才清除該句，不要求本文／文章前綴。定位句子邊界時辨識括號與引號，避免標題內的問句造成殘片；未找到正文邊界時須有明確標題／文章起頭，否則保留。普通研究發表、其他發布者、非末尾與邊界不明均不泛刪。規則不把The Decoder硬編為唯一來源；依每篇原文實際尾註建立對應。

新譯文與當期成功快取輸出再次清理；Groq提示明訂直接陳述事實、不重述報導標題或加入出版聲明，輸出清理後仍須通過原長度、數字、版本與語言驗證。保留原始來源與翻譯／總結既有快取識別，22則現有總結均可重用，不全庫清除或重譯，不增加預算、排程、provider或逐篇健康紀錄。Python與前端共用43個基礎正反例與13個原文發布者／句子邊界案例驗證，涵蓋無前綴括號標題、《標題》一文、首先出現在網站上、標題內問句與錯誤發布者。

本機完整2106項通過，98個既有feedparser警告；Python／JS語法、資產版本與差異檢查通過。臺北22:51:18資料離線回放87篇AI新聞中10篇清理、全部收錄104篇中11篇清理且無殘留，前後端逐筆一致；目標中文譯文清理，原始記錄逐項保持。翻譯0次請求，Groq快取重用22則、新增／失敗均0。共同資產20261031-summary-clean3。證據位於 /Users/lordmi/Downloads/ai-news-summary-attribution-recheck-20261031/ 。

統一規則[2c19e03b1ce7](https://github.com/seisyuku/ai-news-radar_zhtw/commit/2c19e03b1ce72bc88a9a84b3c510df2c74964a26)已推送master；[GitHub CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41214129310)2105項通過、1項資產比較分流，[資產版本](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41214129423)與[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41214128823)成功。[正常公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41214197364)產生28a575ec2aeb，[資料Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41214323992)成功。臺北23:18:32正式快照：86篇AI新聞／102篇全部收錄，所有來源譯文均通過尾註檢查，目標summary_zh只留正文、原始summary仍保留來源原附聲明。Gemini重用113筆快取、1次請求成功2筆／失敗0；Groq重用20則、新增1則／失敗0，來源失敗／降級均0，沒有整批重譯。

首頁、六資產與五份資料共12檔正式HTTP與生成提交一致。隔離Chrome1440桌面／390手機實際搜尋目標，中文主標／英文副標及來源正文可見、無尾註、無JS例外或橫向溢出；重點治理ready。正式載入的共用函式另外驗證「正文。（原標題）發表於The Decoder」只保留正文。本輪已發布並驗收結案，無後續監控或待處理項目；第一版不足之處由本輪統一規則取代。

## 10/31 來源摘要移除發表尾註（第一版已發布，殘留已由本輪補修）

依維護者要求，所有使用來源摘要的前端顯示統一在截短前移除末尾的「本文最先發表於…」「本文〈標題〉最初發布於…」與英文 appeared first on 等發表聲明；來源名稱及連結保留。共用itemSummaryText涵蓋來源首段、一般新聞及重點來源摘要備援，生成AI摘要不變；原始來源、翻譯快取、評分與翻譯預算不改寫。

新增36組中英文／三種摘要欄位尾註案例與正文保留、純尾註及不改寫來源測試；相關58項、JavaScript語法與差異檢查通過。以臺北21:00:37正式資料93篇離線回放，9篇顯示摘要去除尾註，英文原文備援亦通過檢查；OpenAI募資摘要保留110億／300億美元正文。共同資產更新為20261031-summary-clean1。

修正[e5bc602f8f49](https://github.com/seisyuku/ai-news-radar_zhtw/commit/e5bc602f8f496b0305b9baf6e922e58a9a7a00b5)已推送master；[GitHub CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41205320645)2041項通過、1項資產比較分流，[資產版本](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41205320639)與[Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41205320474)成功。首頁、六資產及當期兩份資料共9檔正式HTTP與發布內容一致。1440桌面／390手機實際搜尋目標，來源摘要無發表尾註、中文主標／英文副標及金額正文保留，無JS例外或橫向溢出；正式前端全93篇的摘要尾註檢查亦通過。資料沿用正常刷新1dd95b566107，沒有新增模型呼叫或覆寫生成快照。證據保存在 /Users/lordmi/Downloads/ai-news-summary-attribution-20261031/ 。本案已驗收結案，無後續追蹤項目。

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
| 入選事件 | 重點新聞，以則計；後續卡改為更多重點新聞，排序稱依重要性／依時間，導覽總覽取代熱點。 |
| 全部內容 | 全部收錄內容；沿用合併重複開關，同發布者重複連結仍合併顯示，沒有改去重規則。 |
| 來源 | 來源類型（單一選單）／發布者／抓取來源／RSS 訂閱；一手來源包含官方與評測第三方，不混稱全部為官方。指定來源清單沿用既有資格。 |
| 分數 | AI 相關度／優先閱讀分／重點排序分；第4～5則重點卡顯示實際impact-v2排序分，不再顯示舊多源熱度，排序計算本身未改。 |
| 摘要 | AI 摘要／來源摘要／來源首段或其譯文，依實際來源標示。 |
| 時間與健康 | 資料更新時間、新聞發布／首次收錄時間；本輪讀取量不稱今日累計，抓取來源失敗與RSS訂閱失敗分開標示。 |

前端載入錯誤使用區域名稱而非JSON檔名；新聞資訊頁生成器已中文化欄位與狀態，原始JSON欄位保留，正式新聞資訊頁已由正常刷新更新。README同步用詞。只修正顯示與篩選入口命名，舊sourceTypeFilter程式介面保留相容，頁面只保留一個來源類型選單。

驗證：完整1991項通過（98個既有feedparser警告），JS語法、Python編譯及資產版本檢查通過；隔離Chrome在1440桌面及390手機寬度實際載入，來源篩選、精選／全部AI／全部收錄切換、合併開關、空區及新聞資訊頁皆正常，無JS例外或整頁橫向溢出。正式站臺北15:59:35快照顯示105篇AI新聞、30篇精選、0則重點，治理ready；篩選後全站統計不變。

發布驗收：[程式692c0e9c1d18](https://github.com/seisyuku/ai-news-radar_zhtw/commit/692c0e9c1d18bf9a1d78abdc3478cf4167a2de24)、[離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182642617)1990項通過／1項資產比較分流、[資產檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182642586)、[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182641617)皆成功。[正常公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182725807)產生940aaf86a7ee，[資料Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41182843549)成功；首頁、manifest、六資產、九份JSON及一份中文新聞資訊頁共18檔HTTP內容與該生成提交一致，來源失敗／降級與RSS訂閱失敗皆0。正式站1440桌面與390手機瀏覽器檢查通過，無JS例外或整頁橫向溢出。

正式站入口：[GitHub Pages正式站](https://seisyuku.github.io/ai-news-radar_zhtw/?review=20261031-wording1)。截圖、browser-results.json、單頁審閱範例、測試及發布備份位於 /Users/lordmi/Downloads/ai-news-wording-review-20261031/ 。維護者已確認人工審閱通過，本案結案，無需後續追蹤；Groq第五項維持暫緩。

## 10/31 重點新聞空區研究（維持現狀，結案）

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

## 下次接手

先讀任務台帳的目前待辦，再核對實際Git、工作目錄及來源健康。公開新聞維持24小時窗口與現行來源／用途資格；實作新的來源、評分或產品能力時，依相關權威文件另行處理。

更新本頁時以臺北日期計算十天窗口，只保留目前有效狀態、近期完成結果與必要入口，刪除超期項目和被取代的接續步驟。當前規則依權威文件維護，不藉由保留整串舊歷程傳遞。
