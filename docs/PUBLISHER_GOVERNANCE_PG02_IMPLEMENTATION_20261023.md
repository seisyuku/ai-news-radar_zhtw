# PG02：發布者身分資料鏈實作與交接（2026-10-23）

**PG02完成，下一步PG03：GPT-6.1 Sol／High。** 本階段依[PG01契約](PUBLISHER_GOVERNANCE_PG01_CONTRACT_20261023.md)完成本機候選；未提交、推送或部署。來源分級／准入表與首頁資格gate尚未啟用。

## 實作結果

- 新增 `scripts/publisher_identity.py`：以既有有界發布者映射、已配置公開入口與Google RSS source資訊產生 `ingress`／`publisher`。只識別身分，不提供來源准入、評分或新增計票鍵。
- XML備援現在和feedparser一樣保存RSS source名稱／URL，也處理帶namespace的RSS及Atom source。官方、精選媒體、台灣媒體與模型分析RSS皆接上RawItem metadata。
- 安全公開欄位、archive／item JSON與HTML、latest／all-mode／模型發布資料、普通故事、事件引用／主文、daily相容投影及LLM雷達持續攜帶身分。原 `source`、ID、URL、日期與tier含義保持；不把RSS來源首頁當成文章直連。
- `publisher.status`分identified／reported／unknown／conflict。新見媒體可呈現聚合方提供的名字，且保留來源線索；未審名稱不自動變成可計票發布者。
- 私人OPML的新入口欄位只公開標準RSS/OPML名稱，source_id／feed_url為null，不以私人標籤或偽造RSS metadata取得身分權威。既有可確認的公開文章host仍可提供身分。

Google固定媒體bridge若RSS資訊與舊歸屬矛盾，撤為null並記conflict；Epoch沒有舊計票鍵，也須核固定媒體範圍。HOSTS／LABELS／SUFFIXES等計票字典及 `cn_aggregator` 群組不變。

事件matcher原先有兩處依賴計票判斷phase。為維持使用者接受的行為，這兩處明確使用原有 `_legacy_identity`；公開引用與計票仍使用可撤回矛盾舊票的新 `identity`。合成回歸驗證撤票不改事件state／phase／時間。

## 讀者顯示與相容性

前端來源名稱、分組、卡片、來源搜尋與雷達改讀有效publisher資料；reported提示資訊由Google News提供。零票不再一律等同無法顯示發布者，會區分「來源資訊待核」等狀態。舊JSON保留相容fallback。

首頁多樣性cap與舊priority signals仍用原入口身分，沒有因新顯示名稱而提前改席位。原事件去重、排序、AI .65門檻、來源tier／cap與首頁gate均不重調。CNBC既有單枚徽章修正完整接續；五資產版本為 `20261023-pg02`。

## 驗證

- 完整 **1,671項** Python／JS相關回歸通過；Python編譯、JavaScript語法與diff檢查通過。
- 五組既有成對歷史fixture，用精確PG02前程式與最終候選重播，事件根分別172／168／121／92／190。state完全一致；剔除新增身分欄位及投影generation_id後，整份事件投影一致，包含成員、phase、時效、計票、分數及選集；實際daily相容轉接亦驗證身分傳遞。這些是已封存重建窗口，不宣稱當時正式頁面或獨立品質驗收。
- 11:35臺北固定正式快照的身分顯示重播：195篇中177 identified／8 reported／10 unknown；56篇Google URL中48 identified／8 reported。原八筆未知計票來源均取得RSS提供的媒體名稱，仍不新增票；不是八家整站准入通過。
- 7,466個archive輸出副本的publisher／ingress通過PG01 schema components；215筆能與封存RSS按site／source／URL精確對應。13筆OPML的新入口ID及URL遮蔽；本期其餘182篇有穩定公開source_id。
- 真Chrome桌面1440／手機390，正式舊版、候選新版、新版讀舊資料共6contexts／12個view通過。熱點／時間線事件ID與順序一致；CNBC在當期時間線第17位只一枚，媒體名稱搜尋在「全部AI」模式通過。來源不在Top10時不假稱已在熱點顯示。

身分顯示fixture以11:35公開JSON及09:35封存RSS的精確URL配對建立，未重跑當期正式state或修改新聞內容；真實producer／state另由五窗口及合成端到端測試驗證。缺metadata的歷史／私人入口仍可unknown，不猜補成已知；independent precision維持not_evaluable。

## PG01種子矩陣更正與PG03入口

實作核對發現：`mcp_blog`／`mistral_news`是健康collector鍵，實際feed輸出 `site_id=official_ai`，既有tier為official／rank0。PG01種子矩陣以collector鍵估出的other／rank9不準確；原封存不覆寫，更正記在本階段 `PG01_SEED_CORRECTIONS.json`。**PG03應保留實際rank0，不把矩陣誤差當成升降級決策。**

PG03開始先驗本階段MANIFEST／HANDOFF，建立 `config/publisher-policy.json`，分開套用身分、scoped准入、來源tier及一般／精選／雷達用途；未審預設rank6。不得把本階段identified／reported視為整站已准入，亦不得將scoped新rank回灌事件matcher或同源選版。首頁資格gate仍接PG04。

完整證據、逐檔hash、精確patch、測試log及交接在Downloads `ai-news-radar-publisher-governance-pg02-20261023/`。PG01封存與schema保持，原保護／預留內容仍隔離；未新增來源、逐篇跳轉、全文抓取、LLM呼叫、觀察、日報或排程。
