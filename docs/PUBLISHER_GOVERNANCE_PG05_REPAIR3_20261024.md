# PG05 補修（三）：交易肯定狀態與完整模型受詞

本機補修候選完成，**待 PG05 複驗，release_ready=false**。下一階段建議 **GPT-6 Astra／High**；複驗通過才進 PG06。本階段沒有提交、推送、dispatch 或部署。

## 起點與修改範圍

依[補修二複驗](PUBLISHER_GOVERNANCE_PG05_RECHECK2_20261024.md)的兩項缺陷續接。canonical 為 `/Users/lordmi/Documents/ai-news-radar_zhtw`，master，HEAD `8deab0c1b61a7560c2f552c5366b3776bc82dd51`。先核前階段 430 個證據檔、40 個累積 dirty 檔及 HEAD，全部相符。

本次 runtime 僅修改 `scripts/publisher_material.py` 的交易狀態、交易支持與模型完整受詞工具，以及其中模型名詞接中文的字界常數。新增 `tests/test_publisher_relations_repair3.py`；更新本說明與 HANDOVER／SOURCE_COVERAGE／ROADMAP。前階段候選保留，沒有重置既有變更。

事件 matcher、state／phase／時間、.65／.72、重要性權重、來源 registry／准入／計票鍵／cn_aggregator、財務主體函式與前端均保持。沒有新增來源、抓取、正文、跳轉、LLM、排程、觀察或日報工作。

## 修正後行為

### R2-01：肯定交易述語

`transaction_state` 不再把未識別的前置片語預設為 affirmed。它先處理疑問、先行假設、否定與意向，再確認直接陳述、進行／未來式或明確宣布／簽約等肯定框架。未知框架維持 uncertain。

肯定框架以最接近動作的具名主體為界，按實際文字位置排序，避免中英名稱種類的回傳順序影響主體選擇。簽約框架檢查整段主體→動作關係，不能讓「可能已簽署……」的較長前綴繞過判定。保留已簽約待監管核准、尚未交割及正式宣布的交易。

中文價格附語、被動收購、簽署併購協議及已達成交易有對應結構；意向書不能當成正式收購協議。未改監管／停運與市占判斷，不宣稱其他市場事件語態已全面重做。

### R2-02：完整模型發布受詞

`model_is_release_object` 改為檢查模型名詞片語是否完整：句尾、標點、獨立補充語或清楚後接述語可完成受詞。所有格或未結束的名詞尾部不借用 release 動詞，因此不必為每個未知文件修飾詞補黑名單。

模型類型、系列、預覽版與公開權重可形成模型本體；後面仍有文件頭名詞時不成立。真正模型發布附帶文件、API reference 或使用說明仍可通過。中文後接「準確率超過……」、數字規格支援等述語，與「準確率報告」等名詞尾部有正反對照。英文字詞接中文時使用 ASCII 識別字界，不把中文當英文字的一部分；沒有修改事件 matcher 的模型字典。

這是有界語言規則，supported 仍只表示保留材料支持該分類，不是獨立事實查證。未聲稱理解所有自然語言表達。

## 驗證與限制

- 最終 `PYTEST_CLOSURE.log`：**2,110 passed，10.79 秒**；本次新增 127 項正式測試。原七反例、前次 22 例、本次 24 例及七項容量檢查全部通過。容量仍含縮小上限驗配置路徑，不是 100k 文章效能測試。
- 24 例經實際 business_event_score、AI relevance、資格、producer 與 radar；所有負例零 featured／radar，原事件與一般列表保留，沒有注入入選分數。合成官方 URL 不是指稱真實官方曾刊登。
- Chrome 桌機／手機新四個負例零卡片／零雷達，一般新聞仍可讀；已簽約及模型本體正例可入選。加上混版、到期、CNBC 一枚徽章、回復、原三反例及 14 日熱點／時間線，共 62 contexts。固定 34 contexts 的 225 個輸入在後續收斂後逐位元組一致，結果沿用並另存核對；最後 14 日另跑 28 contexts。
- 固定 11:35 讀者快照與直接前階段一致：194 一般篇、183 raw 根、0 featured／daily、1 媒體雷達；來源健康資料 bytes 相同。一般列表仍可能顯示舊共享分類徽章，本次只改用途資格。
- 14 日同輸入／previous state／asof 回放涵蓋 1,914 事件窗口，state 與原 raw 事件投影保持，一般仍 1,976 列次。daily 事件次數由 2 變 1；唯一退出首頁的整組案例屬隔離範圍，僅作機械核對，**未人工判定這筆退出是否改善品質**，列入複驗限制。最終材料差異與隔離判定以 `QUALIFICATION_DIFF.json`／`FEATURED_DIFF.json` 為準。

固定回放來自保留 archive，可能包含後來更新的內容；不是當時網站的可靠性觀察。PG03 baseline 沿用已核封存，本次只重跑 candidate。

## 收斂過程與材料審查

中途曾誤排固定雷達的一篇允許材料，原因是模型名後直接接中文述語；已用通用句型與合成對照恢復。其後對歷史回放的七篇允許降級材料作開發審查，補齊價格附語、簽署協議、混合名稱位置、模型類型及預覽版；不能把中途 `MATERIAL_REVIEW_ALLOWED` 的 after 欄當最終狀態。

最終狀態見 `FINAL_MATERIAL_REVIEW.json`。意向書材料維持不足；其他恢復與新增不足提示均按最終投影核對。所有已讀資料是開發／回歸材料，非獨立留出。沒有依 protected 內容調參。

## 證據與交接

證據根：`/Users/lordmi/Downloads/ai-news-radar-pg05-repair3-20261024/`。先核 `SEAL.sha256`／`MANIFEST.json`，再讀 `HANDOFF.md`、`VALIDATION.json`、`FROZEN_CODE.json`。`START_STATE` 綁複驗封存，`before/` 保留起點 40 檔，`ROOT_STATE` 綁本次最終累積候選，階段 patch 只呈現本次差異。

`PYTEST_CLOSURE` 與最終 history／reader 檔才是最終結果；`PYTEST_RED`、較早測試及 `INTERMEDIATE*` 為過程，不可混用。前階段封存保持唯讀；正式 data hash 維持既有錨點。

強隔離閉包保持 1,039 IDs，包含原 72 protected、448 reserved、先前污染稿、完整／裸 Claude 版本及六 CN 家族。先整組 `Boundary.allowed` 再 `safe`；禁止直接展示原 archive／history／parent 正文。此次無新保護曝光，既有污染標記保留；`independent_precision=not_evaluable`。

複驗請檢查新的等義正反關係，核對肯定框架、完整受詞及正常正例的召回；不能把本次已曝光案例當獨立 precision。選集變動遵守隔離，不能為填數字解除保護。通過後才交 PG06（建議 GPT-6.1 Sol／High）；未通過則列具體補修，不逕行發布。
