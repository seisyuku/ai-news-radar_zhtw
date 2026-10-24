# PG04：首頁、daily與模型雷達用途資格（2026-10-23）

**PG04本機候選完成；下一步PG05：GPT-6 Astra／High。** 未提交、推送、dispatch或部署。依[PG01契約](PUBLISHER_GOVERNANCE_PG01_CONTRACT_20261023.md)接續[PG03來源政策](PUBLISHER_GOVERNANCE_PG03_POLICY_20261023.md)，不修改既有事件matcher、state、來源准入表或AI relevance .65地板。

## 實作結果

新增 `scripts/publisher_governance.py`，在原事件引擎完成後建立 `stories-merged.json` 頂層 `publisher_governance`。brief-events頂層schema與state版本保持；原事件根、成員、phase、主文、分數及時間不重寫，只有公開來源材料、generation_id與同政策daily選集追加／更新。

文章annotation分開保存ingress、publisher、source_policy與qualification。用途材料只取同ID archive中的原始標題／RSS摘要／已保存公開引用，保留可逐字核對的field／code-point span與URL；不用翻譯或生成摘要作證據。缺原材料合法標unknown，不把它當成整包損壞。source_material隨公開refs保存，沿用既有遮蔽；不新增逐篇跳轉、正文或LLM工作。

六類核心材料採有界、保守規則：完整模型與發布／可用動作、財務期間／動作與數據、具體併購／監管／停運或有範圍的份額資料、產品價格變更及適用條件、具名benchmark與結果，以及有具體元件／風險與原始或具方法技術材料的資安報導。只提到價格、模型、漏洞、排行或未讀連結不算。相關文章尾段與另一型號／產品的數據不借作標題主體證據；官方站也不能把二手社群示範當成原始技術材料。傳聞、否認、歷史評測及矛盾資料不能取得supported。活動、教學與明確泛建議另作文章範圍排除，不以媒體／URL黑名單處理。

`supported`只表示保存的材料支持該事件分類，不代表事實獨立查證。用途徽章依這份材料產生，原分類器與事件business_events保持，因此不是把原粗略徽章當成資格證據。

## 用途選稿與計數

只取當期有效事件、active_phase、identified、approved／limited、allow_featured、scope in_scope且有對應核心材料的文章。具體model／software／product主題須與原事件相符；其他舊階段或未審／衝突引用保留，但不提供支持、徽章或票數。

qualified_source_count只計上述支持文章已有的非空corroboration_key，仍受 `cn_aggregator` 一票限制，沒有新正向計票鍵。合格主文按用途分數、scoped rank與文章ID穩定選擇；門檻仍是合格官方一手主文、兩個合格鍵、或單源用途分數≥.72其中之一。官方網站首頁連結不提供官方例外。

用途分數沿用原importance權重，輸入改為scoped tier、事件effective_at、固定asof與合格計數；官方editorial輸入依實際publisher_kind，避免入口假加分。原事件分數保持。daily沿用原事件引擎的每發布者衰減選法，但使用實際合格發布者／群組鍵，不按query名稱分席位。

用途view只用合格主文、支持引用、分數及徽章；完整原始引用仍在raw事件與all_sources。摘要只有原摘要主文ID等於用途主文ID才沿用，否則省略。查詢／來源／分類篩選不借不合格引用入選。取消首頁舊補位路徑，允許零則；單則沿用只顯示時間線的規則。

先定daily_selected_event_ids與daily items／meta／diagnostics，再重算brief generation_id，最後綁治理投影的generation_id。治理投影與原事件一一對應，包含全部參照文章的唯一annotation；綁generated_at、brief generation／state revision及PG03 registry revision，避免循環hash。

## 雷達、一般列表與前端

LLM雷達與model_releases_24h先核當次用途許可、身分及24h，再保留原模型證據／型號條件。LLM Stats另核原organization allowlist與保存的結構化discovery欄位，仍是「模型追蹤」；官方／媒體標示依實際發布者，取消僅以official_ai入口稱官方的捷徑。雷達連結明示官方公告／模型追蹤／媒體報導與發布者，價格及兩canary獨立不變。

一般列表維持原AI／產業與時效收錄，增加明確文章範圍排除，未審本身不排除；archive與resolver保留原文與歷史tier。latest／all-mode／daily／radar攜帶同一治理metadata。全量列表載入也會傳遞政策revision訊號，沒有新增請求。

新增純前端 `assets/publisher-governance.js`，核對shape、容量、綁定、參照、當期角色、合格鍵／主文／摘要、來源span及daily實際內容／診斷。前端不重做來源准入或核心分類。缺／錯版／跨代／明示unavailable即保守停止重點及雷達，一般列表可用，不回退舊徽章gate。

同頁快取只接受原同代同revision；見新revision、較新generation或同時間不同revision後，不能以舊資料覆蓋。同時間衝突保守停用，直到較新一致generation。沿用一個本機到期timer及tab恢復重繪，兼顧重點與模型列，不新增排程／網路工作。六個共同資產版本為 `20261023-pg04`。

## 驗收與影響

- 完整 **1,845項** 回歸通過；Python編譯、三個變更JavaScript語法及diff檢查通過。
- PG01的24個合成門檻案例已執行runtime；23個跨欄位拒絕案例加新revision快取、到期，以及mixed daily／radar／all-mode等檢查通過。額外驗證daily文字、摘要與診斷不能只靠正確meta蒙混。
- 五組同claim／state／asof歷史重播，原事件根172／168／121／92／190，state完全一致。除source_material、選集與generation_id外，整份raw投影一致，包含原主文、分數、角色與時間。各窗口治理投影ready且通過schema；新daily均為零，原daily數分別11／5／4／0／6。這是用途選集變動，不是事件被刪除或重設。
- 固定11:35臺北公開archive／投影加既有精確RSS provenance：183 raw根、194篇一般AI新聞保持；新featured／daily／雷達均零（舊daily12、雷達3）。178根沒有當期合格材料、4根未達合格門檻、1根到期。治理投影318,973 bytes，原brief加材料1,835,390 bytes，均低於8MiB。**不是今天沒有新聞，也不是獨立品質驗收通過。**
- 真Chrome 1440／390，PG03基線、PG04候選、候選讀舊資料、實際producer合成正例共8contexts通過。一般列表與未審來源搜尋可用、零則不補位、混版停用；合成三稿包含兩篇CNBC及一篇Reuters，CNBC僅一枚、計兩個發布者。本機到期不發請求。

固定顯示驗收是原同代投影後的用途重播，不冒充重建當期正式state；真producer／state另以成對歷史及離線main驗證。未抓新端點，不宣稱即時來源穩定性。72 protected、448 reserved及六CN家族隔離保持，僅作機械檢查；截圖只含合成文章。independent precision仍not_evaluable。

## PG01合成計票補正

PG01有九個簡化案例，在過期、無效投影、scope不明／排除、無核心材料或衝突時，仍把篩選前的一個來源鍵寫成qualified_source_count=1。這與D03／D06「當期、准入且有合格材料才計票」的文字定義不一致。

本階段runtime測試保留PG01原預期，另把這九筆合格計數補正為0；其最終featured eligibility與摘要預期、.72門檻、官方例外、來源裁決均不變。原PG01封存與schema不覆寫。逐案理由在Downloads `PG01_RUNTIME_COUNT_ERRATA.json`，可攜測試在 `tests/fixtures/publisher-governance-cases.json`。

## 下一階段

PG05先驗本階段MANIFEST／HANDOFF，複核核心材料保守規則與九筆計票補正，完成固定14日回放、所有允許人工審查的進／退出差異、混版／容量／回復與獨立複核。零則輸出是已接受代價，不能為補席位放寬門檻；若要改凍結政策，必須另列理由與新revision。

證據封存在Downloads `ai-news-radar-publisher-governance-pg04-20261023/`，含逐事件用途理由、schema／state比較、測試log、Chrome、精確patch及交接。本階段未發布，PG05也不push／dispatch；PG06才依既定順序部署。**下一步PG05：GPT-6 Astra／High。**
