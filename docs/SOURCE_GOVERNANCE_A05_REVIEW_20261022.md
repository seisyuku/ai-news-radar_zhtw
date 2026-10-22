# A05發布前複核與A06交接（2026-10-22）

**A05：done。候選通過本階段複核，未發現阻擋發布的缺陷；下一步A06：GPT-6.1 Sol／High。**
本輪依使用者「執行a05」審查[A03規格](SOURCE_GOVERNANCE_A03_DECISIONS_20261022.md)與[A04實作](SOURCE_GOVERNANCE_A04_IMPLEMENTATION_20261022.md)。
沒有修改正式程式、測試或生成資料，沒有提交、推送、fetch／merge、部署、寄信或觸發工作流。
本結論只涵蓋這份候選，不表示來源品質、七日穩定性或正式部署已驗收。

## 確切候選與證據

- 本機master HEAD：`4036a57c87ea6e31169d3abcd7301d0e543ef630`；既有未提交成果全保留。
- 入場核對A04的212個證據檔及全部候選檔案雜湊，完全一致；另驗A01的171檔、A02的64檔、A03的23檔，均無差異。
- A04的15個受測程式／測試檔案雜湊未變，沿用其完整**1,533項通過**及語法檢查結果，本輪不重複執行相同全套測試。
- 新證據在Downloads `ai-news-radar-source-governance-a05-20261022/`：ENTRY_INTEGRITY、PRIOR_EVIDENCE_INTEGRITY、BROWSER_REVIEW、ROLLBACK_REVIEW、REMOTE_READONLY、RELEASE_PREFLIGHT_READONLY、HANDOFF及MANIFEST。
- A04封存不重寫；A05只追加治理文件與證據。A05 manifest提供新的完整候選清單，含未追蹤的新程式、測試及治理文件；不能只憑`git diff`收集發布檔案。

## 複核結論

| 範圍 | 審查結果 |
| --- | --- |
| 發布者身份 | 固定公開host／別名／Google News尾綴有界映射，網域邊界及OpenAI Skills repo路徑受限；OPML標籤不作身份依據；主題query不當官方。衝突與未知不加票，既有cn_aggregator保留。沒有增加來源請求或私人映射。 |
| 所有計數消費端 | 後端熱度、主文選取、類別／理由、brief gate；前端story、非story合併、排序、首卡與標籤均使用發布者計數。原始引用數只留作引用／診斷／顯示，mergedCount不再當多方加分。 |
| 舊資料與歷史 | 缺新欄位時只用可用新鍵，否則0；有效0不回退到舊篇數。當期view採副本註記，archive不回填；文章ID、時間與連結生成邏輯不變。 |
| 免費額度退役 | 不再抓取、diff或產生活躍status，舊free-tier卡片排除；歷史state保留且不偽造新鮮度。source_health只遍歷當輪status，不會把已退役分支舊失敗重新列成活躍警報。價格與兩canary的隔離／去重／窗口維持。 |
| 產品範圍 | rank／cap、AI relevance與0.65、聚類規則未改；八候選不准入，D02／D03留已知限制。中英文README及價格區名對齊；多方報導不宣稱事實已查證。 |
| 自動化邊界 | 兩來源觀察、兩日報、SMTP驗收仍disabled_manually；公開刷新、watchdog、Pages保持active。私人日報不恢復；公開daily-brief保留。 |

重查A04機械比較：D1的192個AI ID、183故事成員／引用與主文保持，內部brief20→18；前端聯集182不變，時間線20／熱點10各有一個名額替換。
14日2,842原始列分類不變，2,669正例列合成2,375故事，449組計數紀錄改變、主文不變。
這些是去除虛增佐證後的預期排序變化，不等於首頁少兩事件，也不是分類品質或歷史逐日回測通過。
審查只讀聚合、ID／數值與既有開發案例，未展開sealed留出標題／摘要。

## 新增驗證

實際Chrome無頭瀏覽器載入候選HTML／CSS／JS及純合成JSON，封鎖非localhost請求：

- 新版資料在1440與390像素寬度均通過：同發布者五版顯示1、兩發布者顯示2且僅此案例有「多方報導」、未知顯示「來源待辨識」。
- 舊JSON移除全部corroboration欄位後，1440像素下三卡均保守顯示「來源待辨識」，沒有多方標籤。
- 三個情境皆保留價格與政策卡、隱藏free-tier卡，無JavaScript執行錯誤或頁面橫向溢出。
- 已檢視桌面與手機完整截圖；這補足A04的真瀏覽器缺口，但不是正式站最新資料或全部裝置驗收。

瀏覽器工具初次缺少自帶Chromium，改用已安裝Chrome；第一次檢查選取器漏掉價格的compact清單，修正測試腳本後通過。兩者均非正式程式缺陷。

另在Downloads副本實際反向套用B01，確認B02程式／前端退役及觀察false仍保留，再跑故事、brief、signal gate、感測器與UI相關回歸：**46項通過**。
未對正式工作目錄執行回復。A04的三批完整正反演練仍保留。

## A06發布順序與退出條件

1. 先驗A05 manifest與本機狀態，再讀最新遠端。A05唯讀檢查19:46臺北時間的master為`f170eed88a597ab7a8d81bc18168ede1be7901f3`，比本機HEAD多23提交。
   GitHub compare只回傳上限300檔，已回傳部分皆data／item，**不能據此斷言全部只有快照**。A06須fetch後檢查完整commit與diff，保留遠端bot成果；禁止force push或用本機舊資料覆蓋遠端新快照。
2. 按完整候選清單保存／提交已授權成果後整合遠端；遇程式衝突逐項審查，不採全檔ours／theirs。若受測程式有變，重新執行對應驗證；共享生成／schema／評分變更跑完整套件，basetemp仍用Downloads。
   檢查未追蹤的`corroboration.py`、其測試及治理文件都進發布包；私人OPML、憑證、Downloads證據不進Git。發布提交保留B01／B02可區分的回復邊界。
3. 同步`config/tw-source-observation.json`的`enabled=false`。A05核得遠端Git仍true，外部工作流停用才是目前生效的防線；不可重新enable兩實驗、日報或SMTP驗收，也不重新驗寄信。
4. 推送後核對確切commit的Offline tests、Asset version與適用契約檢查，及master根目錄的Pages建置。失敗須讀錯誤並處理，不以舊綠燈代替新版本驗收。
5. 核對公開首頁五個資產版本與app內容，再核對**由含本次程式的commit生成**之新快照。若有舊程式在途run於發布後落地，以後續新版成功run／生成commit為準，不只看時間戳。
   優先使用既有正常刷新；若尚無可驗的新輸出，A06可在發布授權內做一次既有update-news手動刷新，不新增排程／觀察。正式JSON不可手動偽造通過。
6. 對新快照核對當期文章key／status、story的corroboration_count與raw引用、brief gate、前端新舊資料fallback、來源健康，以及價格／兩canary仍產生真實status、free-tier不再是活躍來源或卡片。未知身份允許0，不要求硬湊來源數或事件數。
   另外核查一般列表、時間線／熱點、模型雷達、價格、政策、詳細來源與歷史連結可用。新上游失敗如實記錄並區分既有問題，不修改品質門檻掩蓋。
7. 讀回兩實驗與D00工作流仍停用、遠端config false，記錄發布SHA、CI／刷新／Pages run與HTTP證據後結案。不恢復七日等待、採樣、提醒或Email待辦。

## 發布事故回復

優先只撤B01、保留B02退役與A01 false；本輪已實際驗此路徑。
**反向B01會帶回舊index資產版本，不能直接拿來發布。** 真回復必須給五個資產一個新的共同版本，避免快取重用；回復程式與當期JSON要相容。
在回復後程式保留B02的條件下重新生成當期輸出，不能整包恢復舊market-signals／state而重新呈現已退役分支，也不能reset整個repo或丟掉bot快照、治理證據。
B02若出問題採維持停用的局部修復。回復提交及新版生成／Pages仍需完整驗收；當次任何額外程式修正要重跑適用測試。

## 結案限制與下一步

沒有已驗證等價的免費額度自動替代；不同發布者也不等於獨立採訪或事實正確。
八個候選的七日可靠性、D02教學誤收與D03基礎設施漏收仍未解決，按A03作明示限制，沒有新增持續作業。
A05無待修阻擋項；A06仍需實際整合、推送與正式鏈路驗收，不能以本文件冒稱已完成。

**下一步A06（S08）：GPT-6.1 Sol／High。** 延用既定階段模型建議；模型由使用者選擇，本輪不自動切換或跨階段發布。
