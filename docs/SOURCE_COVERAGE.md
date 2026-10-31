# Source Coverage

2026-10-31發布狀態：本頁10/30新增的新聞版本／品質診斷與有界官方文字查漏已合併master並完成正式刷新、CI與HTTP驗收，詳見[TASK_LEDGER](TASK_LEDGER.md)最新節；10/28來源品質修正及AIBase降級亦早已發布。

## 2026-10-30 新聞品質與來源首段整合（本機已驗證，未發布）

已整合新聞同URL版本歷史與最新內容投影、來源／篩選／事件／入選排除原因，以及Juya線索的有界官方純文字政策查漏。僅一份當期對照早報、最多兩個直接官方政策正文；沒有新增排程或任意連結爬取，未知原發布時間保持first_observed，不補造發布日期。
一併整合Hugging Face首段補讀／翻譯展示、今日重點摘要優先、來源摘要回退、金額譯文修正及既有補位分數相容修正。前端共同版本20261030-quality1；維持AI門檻與24h窗口、來源治理與用途限制。
私人早報整組移除與PDF／多媒體附件不作證據的裁決保持。實作已落於正式專案工作目錄，完整1913項回歸通過；固定輸入與候選結果一致，原始7489筆新聞內容保留，官方文字查漏與Hugging Face首段回放通過。沒有commit、push、部署或改線上設定。完整交接：/Users/lordmi/Downloads/ai-news-quality-integration-20261030/HANDOFF.md。

## 官方文字來源與格式邊界

一手材料限官方RSS／Atom的實際文字與官方可讀正文；現有媒體新聞按既有規則收錄。附件、圖片與影音不作證據，不開發文件解析、OCR或轉錄。正文不足就保留缺口。

既有當期Juya對照早報可提供直接官方連結線索；政策頁補讀限developers.openai.com/api/docs/guides/，每輪最多一份早報與兩頁正文，原早報不增加證據票。這是已依維護者核准整合的有界額外網頁請求；不擴大成任意連結爬取。沒有人工財報／文件JSON匯入或Alphabet專用准入例外。


This project should help readers track material AI-industry events without
forcing them to follow noisy timelines or manage many source choices.

## 2026-10-28 三日品質複審與修正（已發布）

維護者核准修正重點誤判、稿型／目錄範圍及同事件／改稿去重，並要求複審 AIBase 後決定降級。資料窗口為臺北 2026-10-25 09:05～10-28 09:05：41 個新聞入口，共 477 筆封存紀錄、439 個不同網址，包含 OPML、對照、跨入口及改稿紀錄，不能當作獨立事件數或原站發稿分母。本輪標題／短摘要全面檢視與關鍵原文核對屬開發材料，不宣稱獨立 precision。

**AIBase 裁決：由 `ai_media` rank 2 降為 `advanced`／次級AI媒體 rank 4。** 保留公開靜態索引 adapter、既有 host scope、`limited` 准入及 general／featured／radar 逐篇用途許可，沒有升降其他來源、擴張計票或新增來源。唯一有效分級在 `config/publisher-policy.json`；舊 archive tier 與既有 matcher 的 transport tier 不回寫，所有新公開副本依目前政策重算。

窗口內 AIBase 58 筆材料中，可辨至少十組同題雙稿，例如靈光 2.0、PS5 漏洞、GPT-6.1 Terra、Kimi 補額度；同題不代表每篇均可刪。原文另確認兩個證據狀態缺口：[兩萬套機架](https://news.aibase.com/tw/news/31905)標題寫成確定行動，內文其實是分析師預測；[K3.1 Pro 開源](https://news.aibase.com/tw/news/31903)內文說完整權重仍預計 11/4 釋出。這些支持降低編輯權重，沒有證明整站全是假消息或應刪除。既有 overlap 工具以同窗其他來源比對，hard 0／possible 1；中英改寫的標題比對不能證明其餘 57 篇都是獨有事件，亦不拿這個工具的自動 accept 建議推翻人工降級裁決。

本機行為修正：

- 財務核心須有同主體的財務指標／期間／數值，或明確 IPO 申報／募得資金行動；IPO 文件寫作偵測百分比、創辦人身價與募資估值不能借 IPO 字樣取得財報核心資格。一般列表 IPO 徽章亦使用此邊界。
- 模型名與「模型」名詞的鄰接不得跨過標題／摘要或不同句子的換行；避免把下一欄開頭的公司名稱當作已發布模型。網頁標準／瀏覽器產品新聞仍可保留一般收錄，不能靠此誤判取得模型核心或雷達資格。
- 排除排錯、提示詞實戰／指令用法、工作教學、論壇宣傳與 documentation Downloads／Changelog 入口頁；保留發布教學產品、研究成果及具方法與限制的實測報導。一般列表、重點與雷達沿用共同 scope 判定，AI relevance 公式及 0.65 不改。
- 36Kr 尾綴 `36氪`／`36Kr` 同標題合併；同文章 URL、同原發布時間的改標題版本選最近抓到的文稿，滾動 changelog 與不同發布證據不靠此規則合併。archive、文章 ID 及 resolver 歷史不刪改。
- 同公司明確首次 IPO 申報，在 36 小時界內合併 article 根，保留多發布者及既有計票規則；修訂申報、定價、掛牌與周邊稿不混入。英文投資標題另須有相同投資方、受資方、美元金額才合併，不做泛主題合併。沿用既有 alias 遷移與最早事件／phase 時鐘，晚發轉述不續命。

驗證輸出置於 Downloads `ai-radar-source-audit-20261028/`，正式 `data/` 未覆寫；健康探測與完整生成使用同一現有流程，停用翻譯／摘要／付費來源憑證。保留全站 24 小時讀者窗口，沒有重啟觀察、日報或新排程。以下保留本機驗證紀錄，正式發布結果見下一段。

最終完整測試 **2,401 passed**；語法與 `git diff --check` 通過。固定 10/28 09:05 快照配對重算：一般池 207→201（排除六筆教學／宣傳／目錄材料）、daily 6→4，AI 分數逐筆相同；這是固定保留材料的機械比較，不是歷史當時可見性或獨立品質驗收。11:06 臺北的完整公開刷新來源失敗／降級皆空，事件及治理 ready，前端 `publisher-governance.js` 驗證通過；AIBase 公開副本均套 rank 4。模型跨欄位與引號名稱另有正反例，來源政策僅 AIBase scope 變更。

歸因隔離：保留本輪其他修正、僅將 AIBase 政策恢復 rank 2 重算同一快照，四則重點與順序完全相同；6→4 並非此次降級造成。兩區選題規則分開，但上方重點原有排序仍含來源品質權重，並未在本輪新增此連動。

正式發布：以最新 master 保留全部 bot 資料與 `20261026-impact2` 前端補修，只整合本次來源 commit 為 `aaba6389dbb0`，完整 **2,402 項測試通過**。master 離線 CI `40626275722`、程式 Pages `40626275654`、既有公開刷新 `40626297765`、資料 Pages `40626443195` 皆成功；資料提交 `ff3912e294be` 生成於臺北 **10/28 11:22:43**。正式站 16 個前端／資料檔與該提交 bytes 相同；一般 AI 171 篇、重點 4 則（2 核心＋2 補位）、雷達 1 則，14/14 頂層來源正常，28 篇 AIBase 皆 rank 4。瀏覽器確認重點四則、IPO 偵測稿退出重點及 Epoch 文件目錄退出一般列表。861 個既有根皆保留或由 alias 延續，initial／phase 時鐘無向後移動。原工作目錄未提交的其他文件保持；沒有改排程或重啟退役流程。發布證據保存於原 Downloads 審核資料夾的 `release-http.json`。

2026-10-25 的[全站來源盤點](SOURCE_AUDIT_20261025.md)為歷史基準：當時未調整來源等級；讀者名稱顯示修正後來已發布。現行 AIBase 分級以上節為準。

## CyberQ／AlphaLab 正式一般入口（2026-10-25）

兩站各以公開原站 RSS 接入既有 `tw_media` 收件群組，使用獨立 `source_id`，新聞入口由 39 增至 41；不新增排程、前端模式、來源計票鍵或上方重點／雷達權限。AlphaLab 只接受 RSS 標為本站 AI 分類的文章；CyberQ 排除整期彙整、教學及已知 AI 附帶提及的稿件。兩站都只收原站 HTTPS 文章、明確原發布時間與短摘要，並經現行 AI／PG 判定；每站最多八篇，收件回補上限五日。讀者可見時間仍為全站滾動 24 小時。

兩站政策為明確 host scope 的 `unreviewed`／watchlist rank 6：可進一般池並照單篇分數競爭下方精選，預設折疊；`allow_featured=false`、`allow_radar=false`。來源身分仍可能是 unknown，不新增獨立佐證票。先前 `shadow/cyberq` 是歷史隔離紀錄，新 `tw_media/cyberq` 為本次正式 RSS 路線，不重啟舊觀察 workflow。七日回放僅用於來源評估，不是此接入的驗收門檻。

## CyberQ／AlphaLab 隔離驗證第二階段（2026-10-25，當時仍未准入）

全站正式讀者視窗維持滾動 24 小時。下述七日回放僅供來源評估與查漏，不是實作或發布驗收規格；五日 RSS 收件限制也不延長讀者可見時間。

補上兩站**來源限定**的漏收處理：AlphaLab 的本站 AI 分類稿改由現行 AI 判定接受 Kimi／Agent Skills 等標題，不把分類本身當分數；CyberQ 只讓標題為「實測／深度實測」且現行 AI 判定通過的稿件補過通用標題詞表。全域 AI 詞表、0.65 與下方精選 75／82 門檻均未改。

固定七日 120 篇的隔離回放：CyberQ 8 篇、AlphaLab 18 篇，共 26 篇符合目前預篩、AI 與 PG 一般範圍；其中 16 篇為前階段暫判有效，新增 10 篇亦按標題與原站短摘要暫判適合一般 AI 情報（含一篇明確標為預測的算力展望）。這是同一批開發樣本的回看，不能當獨立 precision 或七日單次 RSS 收件能力。AlphaLab 85 篇中的 43 篇可對上當前 RSS 分類，其餘 42 篇用文章 `article:section` 核對；64 篇標為 AI。仍有至少 13 篇看似有價值的 AlphaLab AI 分類分析稿被現行 AI 判定排除，另有 CyberQ 個別漏收待審，因此 26 **不是來源全部有效稿件的上限**。

當時若依既定接線設計，兩站保留各自 `source_id` 並使用 `tw_media` 的 `site_id`，26 篇中有 2 篇可在七日回放的下方精選門檻競爭勝出；當時單頁 RSS 隔離收得 10 篇，最近 24 小時有 3 篇可進一般池、0 篇達下方精選。當時預設政策為未審／rank 6：允許一般，禁止上方重點與雷達；正式入口及 scope 尚未接入。後續 2026-10-25 正式 RSS 接入見本頁首節；不得把七日回放、同 URL 零重複或同批正反例全通過當成來源准入結論。詳細審查在 Downloads `ai-radar-candidate-probe-20261025-stage2/STAGE2_VALIDATION.md`。

## CyberQ／AlphaLab 隔離收件第一階段（2026-10-25，當時未准入）

`scripts/candidate_feed_admission.py` 已加入兩站官方 RSS 的隔離解析與來源專屬預篩；正式 collector、來源 registry、政策、排程、網站與既有快照均未接入。AlphaLab 須由 RSS 分類 scheme 指向本站 `/category/ai/`，CyberQ 須排除已知整期彙整與 AI 僅作背景的標題；兩站都要求本站 HTTPS 文章連結、明確帶時區的原發布時間、五日內稿件，先篩後套每站八篇上限。分類及標題僅決定候選，不授予 AI 分數或精選資格。

七日來源評估曾人工審閱 27 篇現行機械範圍稿，標題預篩保留 16 篇暫判有效稿並排除 11 篇已知誤收。這不是七日完整 RSS 回放，也未驗證未入機械範圍稿件；這批歷史樣本不列為實作驗收門檻。該階段 CyberQ 和 AlphaLab 仍是**未准入候選來源**，當時未增加 39 個新聞入口。

手動隔離探測：`python -m scripts.candidate_feed_admission --output-dir /Users/lordmi/Downloads/ai-radar-candidate-probe`；只寫短候選與 `source-status.json`，不更新 `data/`。

## D+用途選稿已發布（2026-10-24）

[I04正式發布](SIGNAL_SELECTION_I04_RELEASE_20261024.md)接續PG06來源治理：來源registry、39入口、准入／封存裁決、發布者身分與計票鍵均未變，沒有新增來源品質升降級。schema2用途投影將合格核心優先、具體產業動態與有材料的能力／安全披露補位，保留廠商宣稱及未發布標示；首頁／daily升版，雷達仍沿用原材料資格。這不是讓reported／unknown／unreviewed繼承聚合入口精選資格。原PG06結案及隔離限制保持，independent_precision仍not_evaluable。

## PG06正式發布完成（2026-10-24，歷史基礎）

[PG06發布與結案](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)已正式部署發布者識別、scoped來源政策及共用首頁／daily／雷達資格。後端先由既有刷新產生ready資料，再上前端；正式HTTP、CI／Pages與Chrome桌機／手機通過。來源registry、39新聞入口、准入裁決與既有計票鍵均沿用定稿，沒有新增來源品質升降級。

15:05臺北快照105一般AI篇、0重點／daily、1雷達；82 identified／3 reported／20 unknown，46篇未審來源保留一般列表且不進精選。來源健康、價格及兩canary正常。1,085ID隔離與既有污染保持，precision仍not_evaluable；不因正式部署宣稱所有來源已識別或自然新聞品質已獨立驗收。

**PG01～PG06結案，無下一必跑階段。日常維護GPT-6.1 Sol／Medium，修程式High。** 來源重新准入另案處理，不新增觀察排程。

## PG05最後一輪定稿（2026-10-24，歷史階段）

[PG05最後補修／定稿](PUBLISHER_GOVERNANCE_PG05_FINAL_20261024.md)通過本機驗收。相同95個合成案例比較，本輪0個已知錯誤，少於補修（三）的17個；完整2,150項及Chrome150個contexts通過。依使用者最後一輪指示，本輪定稿、停止追加補修，交接PG06。

14日與固定讀者選集保持，沒有新的真實進退出材料或來源品質結論。來源registry、39入口、准入、計票鍵與封存裁決保持；1,039ID隔離及既有污染保持，先前隔離重點退出仍未人工判定，precision仍not_evaluable。正式版本尚未部署。**下一步PG06：GPT-6.1 Sol／High。**

## PG05補修（三）複驗未通過（2026-10-24，歷史階段）

[補修（三）複驗](PUBLISHER_GOVERNANCE_PG05_RECHECK3_20261024.md)的新20個合成案例有4個誤收、2個誤排，仍是材料述語範圍／肯定狀態／完整受詞缺陷。2,110項既有回歸與固定回放通過，不足以放行發布。來源registry、39入口、准入、計票鍵與封存裁決保持，沒有新增來源品質或升降級結論。

本輪未人讀新的實際新聞內容，1,039ID隔離與既有污染標記保持；先前隔離重點退出仍未人工判定，precision仍not_evaluable。**下一步PG05補修（四）：GPT-6.1 Sol／High，之後GPT-6 Astra／High複驗。** 通過前不進PG06。

## PG05補修（三）候選完成（2026-10-24，歷史階段）

[PG05補修（三）](PUBLISHER_GOVERNANCE_PG05_REPAIR3_20261024.md)已修交易肯定框架與模型完整發布受詞，2,110項回歸、原七／22／24例及Chrome驗證通過。來源registry、39入口、准入、計票鍵及封存裁決保持，沒有新的來源品質或升降級結論。

一般列表保持；固定雷達一則維持。14日有一則隔離重點退出，只作機械核對、不宣稱人工品質已驗。**下一步PG05複驗：GPT-6 Astra／High**，通過前不進PG06。

## PG05補修二複驗未通過（2026-10-24，歷史階段）

[補修二複驗](PUBLISHER_GOVERNANCE_PG05_RECHECK2_20261024.md)的新24個合成案例有11個誤收：未確認交易及帶修飾詞的模型附屬文件仍可取得首頁／雷達資格。來源registry、39入口、准入與計票鍵保持；這是材料關係判斷缺陷，沒有新的來源升降級或品質結論。

原回歸、反例及固定14日重建通過且選集不變。發布驗收仍未通過。**下一步PG05補修（三）：GPT-6.1 Sol／High，之後GPT-6 Astra／High複驗。**

## PG05補修二候選完成（2026-10-24，歷史階段）

[PG05補修二](PUBLISHER_GOVERNANCE_PG05_REPAIR2_20261024.md)已修交易狀態、模型文件受詞及跨公司財務借用；1,983項回歸與22個複驗案例通過。來源registry、39新聞入口、准入、計票鍵與封存裁決保持。

本次沒有新的來源品質結論或正式部署；實際首頁、一般列表及雷達選集與補修二前相同。**下一步PG05複驗：GPT-6 Astra／High**，通過前不進PG06。

## PG05複驗未通過（2026-10-24，歷史階段）

[PG05複驗](PUBLISHER_GOVERNANCE_PG05_RECHECK_20261024.md)確認否定／未定案交易、模型文件發布與跨公司財務材料仍可誤取得用途資格。三個合成代表案例已重現首頁影響，需修材料關係；不是來源升降級或新增准入問題。

本輪未改來源registry、39新聞入口、計票鍵與封存裁決。四篇隔離允許的實際讀者變化重核合理，沒有新增來源品質結論；發布仍未通過。**下一步PG05補修（二）：GPT-6.1 Sol／High，之後GPT-6 Astra／High複驗。**

## PG05補修候選完成（2026-10-24，歷史階段）

[PG05補修](PUBLISHER_GOVERNANCE_PG05_REPAIR_20261023.md)已修正四類文章資格／範圍缺陷；七個原反例及1,904項回歸通過。十四日相較PG05追加排除3篇教學、促銷或泛建議稿；固定194篇一般新聞保持，雷達恢復1則媒體報導，沒有提高來源等級或變更39個新聞入口、既有票數鍵及封存決策。

原有隔離及PG05污染稿持續排除，沒有新的來源品質／獨立precision結論。正式網站尚未部署。**下一步PG05複驗：GPT-6 Astra／High**，通過後再進PG06。

## PG05發布驗收未通過（2026-10-23，本機候選）

[PG05審查](PUBLISHER_GOVERNANCE_PG05_REVIEW_20261023.md)確認來源身分／政策與事件歷史鏈路保持，但文章資格仍有字界與金額漏判、封閉主體詞表、教學／活動漏排及未定案併購材料誤收。必須先補修，不因零則推薦或測試通過便發布；不調高來源准入或降低門檻。

14日機械回放、1,857項回歸及42個Chrome contexts完成；291個允許案例已審。來源registry、39新聞入口、既有計票鍵及封存候選均未變。縮寫型號閉包另增30ID，有1筆一般列表檢查先前曝光已標污染；不宣稱獨立品質或即時可靠性通過。**下一步PG05補修：GPT-6.1 Sol／High，補修後GPT-6 Astra／High複驗；PG06暫不進入。**

## PG04用途資格完成（2026-10-23，本機候選）

[PG04共用資格](PUBLISHER_GOVERNANCE_PG04_QUALIFICATION_20261023.md)將PG03政策接到首頁／daily／雷達，以當期合格材料與既有發布者鍵計票；未審可留一般列表，不能提供重點支持。原39入口、來源准入表、計票字典、cn_aggregator與封存／退役決策保持。

固定11:35快照194一般AI篇保持、183 raw根保持，新精選／daily／雷達均零；沒有刪除原事件或為補席位提高來源資格。原scope不足的子站與八家動態媒體不因有名稱就升級。這不是來源品質或即時可靠性通過。

1,845項、五窗口state不變及Chrome8contexts通過；正式網站尚未部署。下一步 **PG05：GPT-6 Astra／High**，複核14日影響與允許審查的進退出案例；所有保護／預留資料邊界維持。

## PG03來源政策完成（2026-10-23，本機候選）

[PG03分級與准入](PUBLISHER_GOVERNANCE_PG03_POLICY_20261023.md)新增唯一有範圍registry及公開source_policy；已知身分不等於品質准入，開放query／未知子站不繼承父層rank。八家新見媒體保持未審，沒有新來源升級或collectors；原39新聞入口、OPML池、人工對照、封存候選與sensor狀態保持。

一般列表使用新tier及來源許可，archive保留原內容與舊tier並附目前政策。固定快照42篇標為未審，其中37篇rank改為6；1篇人工對照稿退出一般列表但未刪歷史。TechNews主站不自動覆蓋finance／infosecu子站，Meet／未來商務同樣獨立；所有變化均有scope理由。

1,727項、五窗口、Chrome桌面／手機驗收通過；正式網站尚未部署。首頁／雷達用途gate仍待 **PG04：GPT-6.1 Sol／High**；本階段不宣稱來源穩定性或獨立品質通過。

## PG02身分資料鏈完成（2026-10-23，本機候選）

[PG02實作與交接](PUBLISHER_GOVERNANCE_PG02_IMPLEMENTATION_20261023.md)完成實際發布者metadata與顯示、可撤回矛盾舊票的防線；來源准入／tier仍待PG03，首頁資格待PG04，正式網站尚未部署。identified只表示身分歸屬，reported表示聚合方提供名稱，均不等於品質准入。

MCP／Mistral實際feed輸出official_ai／rank0，PG01矩陣的collector鍵估級須按本階段更正；沒有實際升降級。**下一步PG03：GPT-6.1 Sol／High**。既有39入口、計票字典、cn_aggregator群組、封存候選與退役分支保持。

## PG01發布者治理契約凍結（2026-10-23，歷史階段）

[PG01契約／驗收基線](PUBLISHER_GOVERNANCE_PG01_CONTRACT_20261023.md)凍結實際發布者、來源准入與首頁用途的分離規則；下一步PG02（GPT-6.1 Sol／High）。正式版本目前仍採原分級與首頁gate，不能把本節當成已部署政策。

開放Google主題查詢是入口保留，不代表動態返回的媒體整站准入。後續以有範圍的發布者政策取代父層繼承；八家新見媒體及未審子站預設watchlist／rank6、沒有精選／雷達資格，一般列表仍依文章範圍判斷。既有來源的明確人工裁決保留，沒有新增抓取、逐篇跳轉或七日觀察。

現有計票字典不自動擴充；身分識別、來源品質與事實證據分別記錄。完整初始矩陣、案例預期與證據在Downloads `ai-news-radar-publisher-governance-pg01-20261023/`；PG03才建立可啟用registry，PG06才發布。

## A06正式發布與來源治理結案（2026-10-22）

[A04實作與交接](SOURCE_GOVERNANCE_A04_IMPLEMENTATION_20261022.md)已修正發布者計數及前端標籤，單獨退役免費額度自動分支。
引用／篇數完整保留，`corroboration_count`為已辨識發布者／既有聚合群組數，未知不加票；同群組或同發布者多版不加熱度。
[A06正式版本與驗收](SOURCE_GOVERNANCE_A06_RELEASE_20261022.md)已推送並驗CI／刷新／Pages與讀者路徑；下方描述已生效。兩實驗工作流維持停用，遠端觀察false已同步。
[A05複核](SOURCE_GOVERNANCE_A05_REVIEW_20261022.md)保留作審查歷史；A06另修高階多方篩選漏項，完整1,534項通過。53列最終裁決不變，未提升品質／可靠性結論。

## A03治理裁決（2026-10-22；裁決歷史）

[最終規格與53筆名冊](SOURCE_GOVERNANCE_A03_DECISIONS_20261022.md)裁定：39既有新聞入口、OPML池、橘鴉對照及價格／兩canary保留；來源rank與cap維持。
臺灣五站（資安人、CyberQ、網管人、DIGITIMES、Meet）及Cloudflare／Modular／Zed本輪不准入並封存，沒有持續觀察待辦。
Free LLM APIs自動感測分支及同發布者多版本佐證已交A04本機實作，保留原始引用與正式來源。
一般分類／0.65不改，教學誤收及基礎設施漏收仍是已知限制。
本次裁決不是品質門檻通過或七日可靠性證明；兩觀察workflow持續停用，沒有新增採樣／寄信。

## 10/31 社群來源退役與資安分類（候選程式，未發布）

資安分類沿用既有AI與平台重大事件範圍；沒有新增來源或提高用途資格。X API／SocialData／TikHub、專用設定與probe已移除，正常刷新不再讀寫付費社群狀態；歷史新聞及既有狀態檔不由此次驗證刪改。一般RSS／OPML與論壇／未證實貼文排除保留。資安主題與具體資安事件分別判定，前者不授予重點或雷達資格。正式發布狀態見任務台帳。

## Product Model

Use a two-layer model:

1. **Signal layer**: the default web UI. It should show a high-priority curated
   subset first, with the complete AI-related pool available as an explicit
   choice. It shows AI news, topic categories including security, search,
   source filtering, and selected/all-AI reading modes.
2. **Advanced layer**: maintainer and power-user workflows. It includes OPML,
   source health data, GitHub Actions secrets, and custom fetchers.

Do not expose every source-management decision in the first screen. Too many
choices make the tool harder for new users to understand.
The first screen may show coverage and health as read-only status signals:
source health, AI article counts, official/media coverage, and RSS subscription
status. Retired social API sources have no reader-facing controls.

`source-status.json.sites` reports subsource health for
`official_ai`, `curated_media`, and `tw_media` in `subsources`. Each row has a
stable, public `source_id`, `ok`, `item_count`, and a safe `error` code
(`invalid_source` or `fetch_failed`; `null` on success). A valid feed or page
with no recent matching articles is successful with `item_count: 0`; malformed
content or unusable article fields fail. If some subsources fail, the group
keeps successful articles and sets `degraded: true` with
`degraded_reason: partial_subsource_failure`. If all fail, group `ok` is false
and `error` is `all_subsources_failed`. Each child also carries `skipped`,
`attempted`, `last_attempt_ok`, `consecutive_failures`, `first_failure_at`,
`last_failure_at`, `last_success_at`, and `persistent_failure`. These history
fields match only the exact `(site_id, source_id)` in the previous snapshot;
a new or renamed child starts fresh, and an older snapshot without children
does not transfer its group streak. A skipped child keeps its prior history
without adding a failure or updating success time. Once its streak reaches the
configured threshold, `persistent_failures` identifies both `site_id` and
`source_id`; an all-failed group does not produce a duplicate group alert.
Group-level history remains a separate summary of whole-group failure.

RSS/Atom adapters preserve a sanitized plain-text `summary`/`description` when
the publisher supplies one. This text supports the optional short-summary layer;
the project does not scrape full article bodies for that purpose, and title-only
items remain ineligible for AI summarization. The maintainer-approved
2026-10-28 Hugging Face display exception reads one bounded first paragraph
only for current AI-reader articles lacking RSS copy. It is retained separately
as `reader_summary` and translated for display; it never becomes native feed
evidence, changes admission/selection, or supplies AI news summaries. Official
HTTPS blog URLs only, no redirects, six pages per run, 1 MiB per page, cached
for the current reader window; failures keep the existing title. See OPERATIONS.

RSS/Atom evidence also retains up to 24 HTTP(S) anchor URLs as optional
`publisher_links`, using the same HTML parse and existing feed request. This
preserves citations that plain-text conversion removes. The field is additive
in the archive/resolver and private source refs; it does not alter public
selection, imply independent verification, or fetch linked pages. The private
daily digest may use an exact link to another eligible in-window article to
group derivative reports while retaining different foreground aspects.

Private-digest exception approved on 2026-10-12: selected TechNews items whose
RSS summaries end in `[…]` may use `scripts/digest_article_excerpts.py` to read
the publisher article's first complete paragraph. Preparation is limited to
ten selected items, uses a private URL/version cache, fetches HTML only, and
does not call an LLM. The captured excerpt is applied without network access
on replay, with the article URL/method recorded and the original RSS references
retained. Failed reads fall back to title/link. The daily job prepares these inputs after V2 selection and captures them for
independent offline replay; the public refresh and feed-summary policy above
remain unchanged.

OPML RSS/Atom now uses the same feed validity checks as grouped sources:
HTML/error pages, malformed XML and feeds whose entries all lack usable fields
fail; valid empty feeds remain healthy. A failed OPML peer does not discard
successful peers. Explicit Telegram/Jike page adapters retain their own parsers.

## Coverage Claim

The project can be packaged as a Skill because it covers the common public paths
for AI news collection:

- official RSS/Atom/JSON and changelog pages
- OPML collections for personal source lists
- public GitHub-generated feeds such as curated X/blog/newsletter projects
- public newsletter archives and static pages
- optional secret-backed adapters for sources that need user-owned credentials

It does not promise reliable default coverage for private inboxes, cookies,
WeChat accounts, or raw social timelines. Those belong in the advanced layer or
private forks because they need credentials, bridges, or ongoing maintenance.

## Supported Source Types

| Source type | Current support | Recommended path | Notes |
| --- | --- | --- | --- |
| Official RSS / Atom | Supported through OPML | Add to `feeds/follow.opml` locally, or `FOLLOW_OPML_B64` in GitHub Actions | Best default for personal customization. |
| Official AI vendor updates | Built in for selected high-signal sources | Keep OpenAI, Anthropic, Google DeepMind/AI, Hugging Face, and GitHub AI/Changelog as first-class sources | These should not depend only on aggregator coverage. |
| Curated AI media RSS | Built in for selected high-signal public feeds | Keep source-specific caps and AI/research filters so media breadth does not drown the default view | Useful for product, industry, model, and research coverage. |
| OPML collections | Supported | Export from RSS reader, copy from `feeds/follow.example.opml`, keep private file out of git | Good for cross-device and multi-agent workflows. |
| Public JSON APIs | Supported by custom Python fetchers | Add a `fetch_*` function in `scripts/update_news.py` and register it in the task list | Use only stable APIs with timestamps. |
| Public GitHub-generated feeds | Supported by custom Python fetchers | Prefer raw `feed*.json` / RSS / Atom files generated by another repo's Actions | Apply the existing publisher and content qualifications before admission. |
| Public static pages | Supported by custom Python fetchers | Parse with `requests` + BeautifulSoup and normalize titles/URLs/times | Avoid fragile selectors when possible. |
| GitHub releases/blogs | Usually supported through Atom/RSS | Prefer GitHub Atom feeds or official blog RSS | Useful for model/platform/tool release tracking. |
| Newsletters | Partially supported | Prefer public archive RSS or stable archive pages | Do not scrape private inboxes. |
| X / Twitter | 社群專用API收件已退役 | 不提供X API、SocialData或TikHub入口 | 一般RSS／OPML保留，來源與內容資格仍逐篇判定。 |
| WeChat public accounts | Not recommended as a default | Use stable third-party RSS only if the maintainer accepts breakage risk | Login/copyright/bridge stability can be poor. |
| Telegram / Bilibili / Zhihu / podcasts | Skipped by default when feeds are unreliable | Add only as opt-in OPML entries | These can be noisy or bridge-dependent. |

## Source Selection Rules

### 2026-10-21 整體修正入口與正式基準（歷史）

新來源准入與既有來源刪減／優化統一依[來源治理計畫](SOURCE_GOVERNANCE_PLAN_20261021.md)
接續；S01的[來源名冊與正式狀態](SOURCE_GOVERNANCE_BASELINE_20261021.md)涵蓋實際
fetch路徑、OPML邊界及獨立感測器。正式22:58臺北快照確認INSIDE、RuntimeWire、
Anthropic抓取成功，三個已移除入口不在curated_media；不代表長窗品質審查完成。
當時未新增或調級來源。電腦王阿達依使用者明確裁決排除，不列P2候選。
S02已完成[審查](SOURCE_GOVERNANCE_S02_REVIEW_20261021.md)及
[評估契約v1](SOURCE_EVALUATION_CONTRACT_20261021.md)：凍結分母、最低樣本、未知案例、
穩定性與事件增益規則；S03固定版本後才做真實觀察。

日報自動生成／派送／排程目標已撤回，[D00](DIGEST_RETIREMENT_HANDOFF_20261021.md)已於S03
外部停用並推送封存差異，私人開關false讀回；來源觀察code與有限七日workflow曾推送啟用。
原訂10/22～10/28、臺北08:00／08:30採樣，後依使用者選擇[方案A](SOURCE_GOVERNANCE_EARLY_CLOSE_20261022.md)，
10/22 12:41兩實驗workflow已停用並封存；不再等待後續日期，七日穩定性未驗收、品質門檻不降。
[A02集中評估](SOURCE_GOVERNANCE_A02_ASSESSMENT_20261022.md)後，A03當時裁定八候選本輪不准入封存，A06正式結案；後續 CyberQ 以新官方 RSS 路線接入一般池，舊 `shadow/cyberq` 封存裁決不變，亦未恢復持續採樣。
首日技術驗真見[S03狀態](SOURCE_GOVERNANCE_S03_STATUS_20261022.md)。
上方私人日報摘要／補讀等為既有技術行為記錄，不代表繼續啟用該工作。
公開RSS摘要保存、Radar精選及來源治理繼續維護。

### 2026-10-21 台灣媒體候選：隔離影子測試，未正式准入

新增維護者工具 `scripts/evaluate_tw_source_admission.py`，僅在明示
`--live` 時探測資安人、CyberQ、網管人、DIGITIMES 與 Meet 的原生入口，
支援離線重播及人工事件／新增證據裁決。輸出強制在 repo 外，不寫
正式新聞池、來源健康、分級、配額或日報，也沒有新增排程。
CyberQ、網管人與 DIGITIMES 找到可解析 feed；資安人本輪未找到可用
feed；Meet 官方內容站轉至另一 host，受限未確認，沒有繞過或第三方接法。
單次 50 篇有效文章、12 篇初篩候選，不能推論新增事件或長期可靠性。
Meet 與數位時代同屬 `bnext_media` 出版群組，不增加獨立 corroboration。
逐站證據、分母、操作方式及准入前仍缺的人工／時間窗量測見
[台灣來源影子准入評估](TW_SOURCE_ADMISSION.md)。所有候選仍未正式加入；
P2 僅建檔、P3／商傳媒不自動抓取。

### 2026-09-22 五站決策：僅供未來人工查漏

依使用者審閱結論，以下五站統一保留為未來檢查內容缺漏的候選參考。
均不接入排程抓取、新聞列表、來源健康計數或重點排序；也沒有自動查漏工作。

| 候選參考 | 入口 | 本次不接入原因 |
| --- | --- | --- |
| YunNEWS | https://news.yuhuanstudio.com/ | 彙整新聞格式不利現有排版，接入收益不值得維護成本。 |
| TheAI學院 | https://www.theai.tw/ | 文章品質與類型落差大，不維護專用篩選。 |
| AIReiter | https://aireiter.com/tw/ | 英文 RSS 新聞比例低，繁中頁需額外解析及語言檢查。 |
| Look AI 一分鐘 | https://lukeverstopia.com/ | 整期多事件日報，沒有單則新聞 feed。 |
| Array 報報 | https://ai-5min-news.israynotarray.dev/ | 日報混 glossary，逐則原始出處不足。 |

9/21 的 RSS/API、文章品質、重疊及成本驗證保留為歷史證據；當時的
YunNEWS／TheAI 試行建議已被本次決策取代，兩站試行程式及專用測試已撤回。
完整歸檔（18 份 JSON、校驗碼、撤回前差異及文件）在本機：
`/Users/lordmi/Downloads/ai-news-radar-source-review-20260922/`。
保留摘要歸因限制與資安新聞誤判回歸，不擴張 README 產品邊界。

YunNEWS 上游來源另做一次公開資料盤點與逐站探測：使用公開歷期文章的
原始連結與 corroborations，去除片段及已知同發布者子網域重複。
它不等同 YunNEWS 的私有完整訂閱設定；媒體、社群、聚合站也不因被列出
就成為官方一手消息。本輪只驗證既有 RSS/Atom／公開資料接法，不自動新增來源。

本輪結果：60 個公開期別、2,486 則文章、195 個出處網域；93 個 feed
通過兩次欄位解析，4 個為第三方搜尋轉接、4 個有解析警告、85 個未找到
有效標準 feed、8 個因社群／橋接邊界排除，另 1 個 Anthropic 既有靜態
解析器成功。未找到 feed 僅代表本次有限探測結果，不是永久不支援。
完整逐站列表與證據見歸檔中的 `sources-verified.csv`、`REPORT.md`。

2026-09-23 已完成下列直接 feed 的欄位、45 日文章及線上 archive 對照。
Mistral、MCP Blog 與 ARC Prize 已依准入範圍部署於正式生成任務；完整逐站證據存於本機
`/Users/lordmi/Downloads/ai-news-radar-source-review-20260923/ADMISSION_REVIEW.md`。

| 出處 | 公開 Feed | 目前狀態 |
| --- | --- | --- |
| Mistral | https://mistral.ai/news/rss | 已正式接入官方公告；排除明確客戶案例／教學，單輪上限 8 則。 |
| MCP Blog | https://blog.modelcontextprotocol.io/index.xml | 已正式接入官方協定公告；只收規格、SDK、roadmap 等發布與治理變更，單輪上限 6 則。 |
| ARC Prize | https://arcprize.org/feed.xml | 已正式接入第三方評測；只收基準與結果，來源與模型雷達均不標為模型廠商官方公告，單輪上限 6 則。 |
| LM Studio | https://lmstudio.ai/rss.xml | 暫不准入；教學／操作文章混入。 |
| Cloudflare | https://blog.cloudflare.com/rss/ | 暫不准入；一般基建與工程文章比例高。 |
| Modular | https://www.modular.com/blog/rss.xml | 暫不准入；既有 AI 閘門未辨識近期公告，專用例外成本高。 |
| Zed | https://zed.dev/blog.rss | 暫不准入；一般編輯器與使用內容混入。 |
| Google Antigravity | https://antigravity.google/blog/rss.xml | 暫不准入；無摘要、部分文章不符範圍，與既有 Google 來源可能重疊。 |

八站入口重取均成功，標題、連結與日期完整；45 日共 51 則，與 9/21
線上 8,723 筆 archive 無相同原文網址，但 Mistral、ARC Prize、Cloudflare
的部分事件已有媒體報導，不能把網址差異算作全新事件。這一輪不能證明
Actions 長期網路穩定；低頻來源沒有 24h 文章時自然為零，不擴張內容邊界。
三站各有獨立來源健康任務；有效 feed 暫無近期合格文章記為健康零則，
格式、必要欄位與網路錯誤則可見為失敗。只採各自網站的原文連結，不使用第三方轉接。

Add a source only when it passes most of these checks:

- Publishes AI, model, developer tool, or tech industry updates with low noise.
- Has a stable URL, feed, API, or page structure.
- Provides usable timestamps or enough ordering information.
- Does not require private cookies, login sessions, browser automation, or secrets.
- Can be fetched politely by GitHub Actions without heavy rate limits.
- Adds coverage not already represented by stronger sources.

## Built-In Official Nodes

The public site should directly track these high-signal official sources:

- OpenAI News RSS
- Anthropic News page
- Tencent Newsroom static index (official public list; its RSS route returns a homepage and the public REST API requires authentication)
- Google DeepMind RSS
- Google AI Blog RSS
- Hugging Face Blog RSS
- GitHub AI & ML RSS
- GitHub Changelog RSS
- Mistral News RSS（已排除明確客戶案例／教學）
- MCP Blog RSS（協定公告、規格與 SDK 發布）

Aggregator sites may already surface some of these updates, but they are not
guaranteed to be complete or timely. Keep these official sources as a stable
baseline, then let the aggregator layer add breadth.

ARC Prize 另以 `arc_prize` 記錄第三方評測公告；其來源層級與模型雷達標示
不同於 `official_ai`，評測文章可沿用既有「評測基準」事件徽章。

## Built-In Curated Feeds

### 2026-10-18 平台事件與 RuntimeWire 文章分流

INSIDE 原生 `https://www.inside.com.tw/feed/rss` 加入 `tw_media`，獨立子來源
ID 為 `inside`，每輪最多八則合格新聞、五日收件窗口；維持 `tw_media`
rank 2／importance 0.56，不加整站 AI trusted-source 捷徑。

`scripts/source_scope.py` 共用於收件、AI 範圍與事件分類。原生 INSIDE、iThome、
科技新報的部署／託管平台重大事件，可在無 AI 字樣、未知品牌時依 RSS 服務
用途與事件證據納入。Zeabur、OpenCode、n8n、Dify 名稱只是辨識捷徑。
個人相簿／雲端硬碟訂閱排除；價格與資料存取異動須具體新舊條件、既有用戶
影響及生效安排，宣傳與未定案說法不走例外。相關性至少 0.65 表示符合 Radar
範圍，不代表產品內建 AI 或已獨立證實報導；來源層級與全域分數公式不變。

永久退場公告納入既有 `market`，不新增分類或保證重點席次。臨時中斷僅在
RSS 明示實際連續超過 72 小時，或有帶時區的明確起訖／持續中斷時間證據時
納入；不使用抓取時間推估，不累加短故障、不新增延後發稿或狀態頁監測。
資安披露不必等三天；資料不足時不靠額外全文抓取補證。

RuntimeWire 同一 RSS 只接受自身 `/article/`，七日收件窗口、每輪最多十則
合格文章；維持 rank 4。模型分析與已知平台重大事件以 OR 收件，包含
OpenCode 類憑證事件；`/models/` 與其他路徑不新收件。舊目錄在所有讀者列表
及共享 AI 判斷排除，不翻譯、不改 archive／resolver 的保留政策。
有效 feed 全是目錄／不合格內容記健康零則，壞 XML／HTML 假 RSS 仍失敗；
LLM Rumors、LLM Stats 與獨立模型雷達未改。日報選題 policy 未改，來源範圍
差異只間接影響候選；完整邊界見 [實作規格](RADAR_SOURCE_CHANGE_PLAN_20261018.md)。

### 2026-10-18 失效入口移除

依使用者裁決，移除 VentureBeat AI、Artificial Intelligence News、LMArena Blog
三個固定 RSS 入口與其 AI 來源信任捷徑，不研究替代抓法、不加重試或爬蟲。
10/18 GitHub 子來源紀錄各有 897 次連續失敗；本輪單次公開探測分別遇到
HTTP 429、TLS 錯誤及轉址後 HTML 而非 RSS。這是入口可用性裁決，不是
媒體內容可信度的降級判決。下一次刷新不再抓取或產生這三個子來源的健康列。
既有 archive、resolver 與歷史審查資料照原保留規則處理；發布者辨識仍供
歷史資料與使用者 OPML 正確呈現。本輪不新增來源、不改日報選題規則。

- **Curated AI media RSS**: reads a small set of public RSS/Atom feeds that add
  coverage without requiring login: The Decoder AI News, TechCrunch AI, The
  Verge RSS with strict AI-title filtering, MarkTechPost Research with research
  filtering, and selected business/research feeds listed in the source
  configuration. These feeds are
  capped per source and pass through the same
  AI relevance scoring as the rest of the radar. Research-heavy feeds are
  intentionally filtered and downweighted so they fill the research lane without
  dominating the default hot view. The shared fetch task retains
  `site_id="curated_media"`, while The Decoder receives the publisher-level
  `ai_vertical` rank 1 tier after the 2026-09-12 review found 144 items over 21
  days, 100% AI relevance, 19.4% business-event coverage, and 0.7% same-source
  duplicates.
## Model Release Radar v1 Watchlists (2026-08-16)

These sources address a specific blind spot: model releases and their follow-up
technical/business analysis. LLM Stats and LLM Rumors retain the low-weight
`watchlist` tier. RuntimeWire uses the still-conservative `advanced` tier after
passing its follow-up quality review; no global importance formula changed.
Atomic discovery records remain visible for 24 hours in the「模型」section,
matching the rest of the reader-facing dashboard.

The reader-facing `llm-radar.json` is a separate 24-hour release-alert lane.
It may surface any current `model_release` event from the regular curated pool,
but labels its evidence conservatively: `official_ai` is an official
announcement, LLM Stats is model tracking, and all other sources remain media
reports. Price cards remain only in the structured Market Sensor
view; neither lane changes the global news score.

- **LLM Stats model discovery** reads the server-rendered `latestModels` payload
  from `https://llm-stats.com/ai-news`. It emits one atomic item per recent
  allowlisted lab model and links to that model's LLM Stats page. It is a
  discovery/cross-check source, not an official lab authority; the site's broad
  aggregated news stream is not ingested. A reachable, parseable payload with
  no recent allowlisted release is a healthy zero-item run, not a source
  failure; HTTP/payload/schema failures remain observable failures. The initial
  live probe contained the previously missed Qwen3.8-27B and Grok 4.6 releases.
- **LLM Rumors** reads the public `https://www.llmrumors.com/news/rss.xml` feed.
  It adds low-frequency, long-form model strategy and deployment analysis. Its
  seven-day overlap sample contained zero recent items, so it remains a
  watchlist until cadence and unique coverage can be observed over time.
- **RuntimeWire** reads `https://runtimewire.com/rss` as an article-only route,
  retaining named-model/model-economics analysis and bounded platform events.
  Catalog records are excluded; valid filtered-empty feeds are healthy.
  The broad feed's seven-day intake had 50 items, 0 hard duplicates, 2 possible
  duplicates, and 48 unique items against the live archive, but unrelated
  startup coverage was visible; therefore only the focused subset is enabled.
  The 2026-09-12 follow-up covered 43 items over 21 days: 100% passed the AI
  gate, 32.6% carried a business event, none were same-source duplicates, and
  90.7% were estimated unique against other sources. It therefore moves one
  step to `advanced` rank 4 / `次級AI媒體`, below established professional
  media. The high-volume automated Head-to-Head feed is not enabled.

Intake evidence is stored in
`reports/source-intake/llm-rumors-overlap.json` and
`reports/source-intake/runtimewire-overlap.json`. Further promotion requires a
longer editorial-accuracy record; current signal density alone does not justify
professional-media weight.

## Reader-window timestamp guard

The rolling reader view accepts publication timestamps only through six hours
after `generated_at`. This tolerance covers small source clock and timezone
errors while keeping articles dated days in the future out of the 24-hour list.
Archive and item-resolver records preserve the upstream timestamp for diagnosis.

## Disabled Default Sources

- **AgentMail digest**: supported as an advanced, secret-backed metadata digest
  through `EMAIL_DIGEST_ENABLED=1`, `AGENTMAIL_API_KEY`, and
  `AGENTMAIL_INBOX_ID`, but disabled by default. It deliberately lists messages
  only and does not publish body text, raw `.eml`, full email addresses, or
  secrets. For a single-newsletter demo, set
  `AGENTMAIL_ALLOWED_SENDER_DOMAINS=alphasignal.ai` to keep shared-inbox output
  scoped to AlphaSignal metadata.

## Example OPML Seeds

`feeds/follow.example.opml` contains a public, low-risk demo set that is expected
to pass through the real project fetch path on GitHub Actions:

- **Official examples**: OpenAI News, Hugging Face Blog, Google DeepMind Blog,
  Google AI Blog, and Microsoft AI Blog.
- **AI media / builder feeds**: Wired AI, InfoQ CN, NVIDIA Generative AI Blog,
  宝玉, and Simon Willison.

In GitHub Actions, `feeds/follow.example.opml` is also used as the public demo
fallback when no private `FOLLOW_OPML_B64` secret is configured. This keeps the
hosted page visibly proving that RSS/OPML import works without requiring any
private subscriptions. Maintainers can override it by setting `FOLLOW_OPML_B64`.
Substack newsletters are intentionally excluded from the public demo OPML because
GitHub Actions runners can receive `403 Forbidden` even when the same feeds work
locally. QbitAI remains on the watchlist because the direct feed probed via
`urllib` but returned `403 Forbidden` through the project fetch path. Broad
sources such as Hacker News frontpage, general hot lists, X bridges, and WeChat
bridges remain outside the example file unless the maintainer explicitly accepts
the extra filtering and maintenance risk.

Recent candidates skipped from the built-in default set:

- **OpenRouter Announcements**: the public page advertises an RSS alternate, but
  the observed `/blog/feed.xml` target returned a Not Found page during intake.
- **LMSYS Blog**: probed feed endpoints redirected or returned 404.
- **Hugging Face Daily Papers**: probed RSS-style endpoints returned 401/404;
  keep it out of the default set until a stable public feed is available.
- **Berkeley RDI Blog**: `/feed.xml` returned only a stale Jekyll placeholder
  item from 2021, so it is not useful as a default source yet.

## 2026-07-14 Source Curation (feature/business-sources)

The evaluated adapters were retired after this trial. Their runtime code and
reader-facing artifacts were removed in the 2026-08-26 repository cleanup.

Added:

- **NVIDIA Blog** (`blogs.nvidia.com/feed/`) — added to `OFFICIAL_AI_FEEDS`.
  `nvidianews.nvidia.com` has no working `/rss` feed (200 but 0 parseable
  entries), so this is NVIDIA's actual public blog feed instead; it mixes
  GeForce/gaming posts with AI posts and relies on the shared downstream
  `ai_relevance_score` gate, same as GitHub Changelog already does.
- **Microsoft Blog** (`blogs.microsoft.com/feed/`) — added to
  `OFFICIAL_AI_FEEDS`. The originally requested `news.microsoft.com/feed/`
  ("Microsoft News") is stale (no item published since May 2025, so
  everything fails the 45-day freshness window); `blogs.microsoft.com/ai/feed/`
  returns 410 Gone. The corporate Blog feed is active and already
  heavily AI-focused.
- **AWS News** (`aws.amazon.com/about-aws/whats-new/recent/feed/`) — added to
  `OFFICIAL_AI_FEEDS`.
- **Google Gemini Blog** (`blog.google/products-and-platforms/products/gemini/rss/`)
  — added to `OFFICIAL_AI_FEEDS`; more precise than the general Google AI
  Blog/DeepMind feeds for Gemini-specific coverage.
- **Google Cloud Blog (Google News)** — `cloud.google.com/blog/rss/` returns
  200 with 0 parseable entries and no autodiscovery link (no working native
  feed found), so this queries Google News scoped to `site:cloud.google.com/blog`
  instead, added to `OFFICIAL_AI_FEEDS`.
- **CNBC Technology** (`cnbc.com` id `19854910` RSS) — added to
  `CURATED_AI_MEDIA_FEEDS` with a strict title AI-keyword filter (general
  tech/finance feed). TechCrunch AI was already present in
  `CURATED_AI_MEDIA_FEEDS` before this change, so it was left as-is.
- **LMArena Blog** (`blog.lmarena.ai/rss/`, redirects to `arena.ai/blog/rss/`)
  — historically added to `CURATED_AI_MEDIA_FEEDS` and to `CURATED_MEDIA_TRUSTED_SOURCE_KEYWORDS`
  in `scripts/ai_relevance.py` (whole feed is AI model evaluation content, so
  it bypassed the per-title AI check like other narrow-topic trusted feeds).
  Removed on 2026-10-18 by the failed-entry decision above.
- **Reuters AI (Google News)** — Reuters closed its own public RSS, so this
  queries Google News (`news.google.com/rss/search?q=site:reuters.com AI...`)
  instead, added to `CURATED_AI_MEDIA_FEEDS`. Links are Google News redirect
  URLs that resolve back to the original Reuters article on click.
- **The Information (Google News)** — `/feed`, `/feed.rss`, and homepage
  autodiscovery all return `403 Forbidden` even with a browser user agent
  (Cloudflare/bot block); rescued via a `site:theinformation.com` Google News
  query instead, added to `CURATED_AI_MEDIA_FEEDS`. Titles/summaries only, no
  paywall bypass.
- **Meta AI (Google News)** — `ai.meta.com/blog/` returns `400` to
  non-browser requests (no working feed, and scraping is unreliable too), so
  this is third-party `"Meta AI" OR "Meta FAIR"` coverage via Google News,
  added to `CURATED_AI_MEDIA_FEEDS`.
- **DeepSeek (Google News)** and **xAI / Grok (Google News)** — neither
  vendor has an official blog RSS (`deepseek.com`, `x.ai/news` both checked,
  no feed); added to `CURATED_AI_MEDIA_FEEDS` as third-party news coverage
  via Google News.
- **Epoch AI (Google News)** — probed `/rss.xml`, `/feed.xml`,
  `/blog/feed.xml`, `/gradient-updates/rss.xml`, `/data-insights/rss.xml`,
  and homepage autodiscovery; no working feed found anywhere. Rescued via a
  `site:epoch.ai` Google News query, added to `CURATED_AI_MEDIA_FEEDS` and to
  `CURATED_MEDIA_TRUSTED_SOURCE_KEYWORDS` (whole feed is AI
  benchmark/forecasting research).
- **Artificial Analysis**: probed `/insights/rss.xml`, `/blog/rss.xml`,
  `/rss.xml`, and homepage HTML for any `rss`/`atom`/`feed` reference; none
  found. No Google News rescue was requested for this one either, so it
  remains skipped.
- **`TW_MEDIA_FEEDS`** (new group, `site_id="tw_media"`, own source tier
  `台灣繁中媒體`): **iThome** (`ithome.com.tw/rss`), **TechNews 科技新報**
  (`technews.tw/feed/`), both general Taiwan IT/tech feeds filtered by a
  zh-TW/English AI keyword allowlist at fetch time (`fetch_tw_media`), and
  **數位時代 (Google News)** — `bnext.com.tw` has no `/feed`, `/feed.xml`, or
  `/articles/rss`, and no autodiscovery link either; rescued via a zh-TW
  Google News query (`hl=zh-TW&gl=TW&ceid=TW:zh-Hant`) scoped to
  `site:bnext.com.tw`, with the same keyword filter as the other two. Health
  reporting remains grouped under `tw_media`, but ranking is publisher-level:
  iThome uses `professional_media` rank 1, TechNews retains `tw_media` rank 2,
  and the Google News-backed 數位時代 route uses `advanced` rank 4. Exact
  數位時代 headline variants with `數位時代` / `未來商務` / `bnext.com.tw`
  suffixes are folded before reader output.
  INSIDE joined this same native-feed group on 2026-10-18 with `source_id="inside"`
  and rank 2. Native iThome/TechNews/INSIDE intake also applies the bounded
  platform policy described above; the Google News-backed 數位時代 query is unchanged.
- **36Kr AI** (`site_id="kr36_ai"`, watchlist tier `观察名单源`): 36Kr has no
  dedicated AI-channel feed (`/feed-ai`, `/feed-motif/*`, `/information/AI`
  all probed with no RSS), and the general `36kr.com/feed` repeatedly serves a
  JavaScript WAF page. The scheduled reader path is therefore the public
  Google News RSS query scoped to `site:36kr.com`, not a degraded fallback.
  It retains the Simplified-Chinese AI-keyword title filter, watchlist tier,
  and shared Simplified-to-Traditional output conversion. Google News headline
  variants from the same publisher are folded before translation; both a single
  fetch and the rolling 24-hour reader output are capped at five 36Kr items.
  The direct URL stays
  available only for occasional maintainer probes; its WAF behaviour no longer
  creates a false degraded status on every refresh. Unrecovered Google News
  failures still carry a cross-run streak and become `persistent_failures`
  after three consecutive runs.

- **AIBASE** keeps its shared `curated_media` / `AIBASE` data identity and
  existing relevance/tier scoring, but the general reader list now presents it
  in **聚合／二次整理**, below original publishers and professional media.
  It remains in the Chinese aggregator ecosystem for duplicate corroboration.
  The source adapter reads the public news-list payloads at
  `https://news.aibase.com/tw/news` (primary) and
  `https://news.aibase.com/news` (English supplementation), using the same
  first-page scope. Native Traditional fields win; English fills missing fields
  and articles through the existing translation pipeline. No full bodies are
  scraped. Publication dates come from the list payload, never fetch time;
  undated records remain archived but cannot enter the 24-hour reader window.
  Cross-language publisher article IDs reuse existing Radar IDs. Historical
  duplicate IDs retain their resolvers until normal retention expiry while
  being excluded from reader counts and heat. Per-language health and fallback
  mode are exposed in the existing source-status task.

zh-TW keyword support: `AI_KEYWORDS`/`TECH_KEYWORDS` in both
`scripts/ai_relevance.py` (the gatekeeper used for `ai_is_related`/`ai_score`)
and the mirrored copy in `scripts/update_news.py` (used by the local
`ai_relevance_score()` ranking helper) were extended with Traditional
Chinese/Taiwan-usage terms (人工智慧, 機器學習, 深度學習, 大型語言模型, 生成式人工智慧,
智慧體/智能體, 演算法, 晶片, 機器人, etc.) alongside the existing Simplified forms, so
zh-TW sources are not dropped purely because they use different wording for
the same concepts.

A related fix: `curated_feed_entry_allowed()`'s per-feed `include_keywords`
matching treated the bare token `"ai"` as a plain substring, which
false-matched inside ordinary English words (`AirPods`, `training`,
`raising`, `maintain`, ...). It now requires a word boundary for that
specific short token (`_feed_keyword_matches` / `_KEYWORD_WORD_BOUNDARY_ONLY`);
longer/CJK keywords are unaffected. This also tightens the pre-existing
`ai` keyword already used by The Verge's feed entry.

## 2026-07-21 Four-Source Trial (feature/source-removal-0721)

`techurls` and `iris` were retired after this trial; `36kr_ai` and the
curated-media xAI/Grok Google News query were evaluated in the same trial and
kept unchanged. The retired adapters' runtime code was removed in the
2026-08-26 repository cleanup.

A read-only forensic audit over 2026-07-17 through 2026-07-21 (recomputing
`ai_relevance`/`business_events` from archived raw items with the actual
scoring functions, since `data/archive.json` does not retain those derived
fields) found:

- **techurls**: 990 new items in the window, but only ~1.1% were both
  business-event-tagged *and* actually AI-relevant (most raw keyword "hits"
  were non-AI false positives — `business_event_score()` does not check
  `ai_is_related`, so e.g. a Samsung layoffs headline or an Apple Music price
  hike gets tagged `earnings`/`pricing` despite having nothing to do with AI).
  60.6% of all items were plain diffuse non-AI noise
  (`missing_meaningful_ai_signal`), not fixable by a keyword rule.
- **iris**: 3,536 new items in the window, ~0.65% true AI-relevant business
  events. 99.5% of items that cleared the 0.65 `ai_is_related` gate were
  pinned exactly at the floor value (`max(score, AI_RELEVANCE_THRESHOLD)`),
  not a real score. Across the full window, iris items landed in a
  cross-source story cluster only 326/3536 times, and competed against a
  genuinely higher-tier source (`source_tier_rank` 0-4) only twice — losing
  both times by tier rank. v2ex.com (excluded via
  `AGGREGATOR_BACKDOOR_EXCLUDED_DOMAINS`, see `85d2ebf`) still accounted for
  19.5% of iris's raw fetch volume even after exclusion took effect.
- **36Kr AI**: kept. OpenCC `s2twp` conversion verified clean (0 residual
  Simplified characters via `s2t` cross-check on the sampled window) and its
  fetch-time keyword pre-filter means 100% of its business-event hits are
  genuinely AI-relevant — no false positives, unlike techurls/iris. However,
  0 of its 4 business-event hits in the window were exclusive: all 4 were
  also covered by iris. With iris now removed, 36Kr's marginal coverage value
  increases correspondingly (kept for this reason, not because its own
  standalone signal changed).
- **xAI/Grok query** (curated-media Google News query): kept, unchanged. Only
  4 new items in the window (too small a sample to fully characterize), but a
  manual review of the full 21-day retention window (29 items) found the
  query terms precise with no noise from over-broad matching.

`AGGREGATOR_BACKDOOR_EXCLUDED_DOMAINS` (`v2ex.com`) remains because it is a
generic URL-host safeguard for future/OPML feeds; the retired sources' tier
and ecosystem entries were removed with their adapters.

## Market Sensor（現行）；Canary 已退役

價格來源不進入一般新聞 `RawItem`、AI 相關性評分或六類事件排序；
由 `scripts/market_sensors.py` 產生獨立的 `data/market-signals.json`：

- **價格（長期影響順位 1、時效順位 3）**：讀取 LLM Price Tracker 的
  公開 `prices.json`，保存核心價格欄位快照，以 deterministic diff 產生
  old/new 事件。第三方結構化資料屬 `reported`，不是官方 GT。

原 Usage4Claude 與 Claude Usage Monitor commit Atom Canary 依 T05 結案裁決退役；
不再抓取、產生候選、維護 seen IDs 或顯示舊卡片。14 天品質研究與新增入口取消。

價格初次執行只建立 baseline，不把上游既有內容當成新事件。結構化資料若突然
縮至前次 80% 以下會 fail closed，保留既有 state；單一 Sensor 失效不拖垮
新聞更新，錯誤會進入 `source-status.json`。

**免費額度自動分支已退役**：不再請求`xyzs996/free-llm-api`，不列活躍健康狀態，
不把退役當作成功或新增失敗。`state.free_tier`及其原觀察時間保留作歷史；不清baseline、不產生假大量移除。
舊free-tier卡片不再流入當期payload，前端亦過濾舊快照的該類卡片；沒有等價替代服務。
純離線parser／provider身份／模型名稱與80%保留防線仍保留，不能為重啟而放寬。

所有寫入公開 `market-signals.json` 的價格事件，讀者可見窗口一律為 24 小時。供 old/new 比對的 sensor state
另行保存，並不延長首頁事件的可見期限。

## Personal Source Workflow

For a private custom setup:

1. Copy `feeds/follow.example.opml` to `feeds/follow.opml`.
2. Add official RSS/Atom feeds to `feeds/follow.opml`.
3. Run:

   ```bash
   python scripts/update_news.py --output-dir data --window-hours 24 --rss-opml feeds/follow.opml
   ```

4. Check `data/source-status.json` for `failed_feeds`, `zero_item_feeds`,
   `skipped_feeds`, and `replaced_feeds`.
5. Keep `feeds/follow.opml` private. For GitHub Actions, store its base64
   content in the `FOLLOW_OPML_B64` secret.

## Adding A Built-In Source

Use this only for sources that should benefit every public visitor:

1. Add a `fetch_<source_name>(session, now)` function in `scripts/update_news.py`.
2. Return `RawItem` objects with `site_id`, `site_name`, `source`, `title`, `url`,
   `published_at`, and `meta`.
3. Register the fetcher in the built-in task list.
4. Normalize URLs and dates using existing helpers.
5. Update this document if the source changes coverage.
6. Run the fastest relevant checks:

   ```bash
   python -m py_compile scripts/update_news.py
   pytest -q
   ```

## Deployment

The public deployment should remain GitHub Pages + GitHub Actions:

- GitHub Actions updates `data/*.json`.
- GitHub Pages serves `index.html` and `assets/*`.
- Private OPML input belongs in `FOLLOW_OPML_B64`, not in the repository.

This keeps the public version easy to fork while still letting each maintainer
bring their own private source list.
