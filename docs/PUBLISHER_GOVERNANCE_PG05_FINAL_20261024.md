# PG05最後一輪補修、檢查與定稿

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：階段歷史／已結案。** PG01～PG06已正式發布，最後補修（四）定稿；本頁的下一步、未通過、待推送只描述當時，不再開補修（五）。技術契約與限制保留，對照[PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)及SOURCE_COVERAGE使用。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

日期：2026-10-24。**本機驗收通過，以本輪補修（四）定稿，PG05結束，下一階段PG06。** 尚未提交、推送、dispatch或部署。

## 使用者的停止條件與版本選擇

使用者指定最後一輪補修及檢查；若仍無法驗證，停止修正，採已知錯誤最少方案。此指示取代先前「補修後再開新一輪修正」的循環。開始時先驗補修（三）複驗的594個證據檔及43個候選檔，HEAD保持`8deab0c1b61a7560c2f552c5366b3776bc82dd51`。

最後24個案例、共同比較方式及STOP_RULE在修改前固定；本輪先修既有缺陷、完成相關與完整回歸，再以FROZEN_CODE凍結程式。最後檢查後沒有runtime補修。共同案例依kind／title／summary／expected去除完全重複，97次案例形成95個不同合成案例，各版本使用相同輸入、來源政策與依賴。

| 候選資格實作 | 同一95例的錯誤 | 其中誤收 |
| --- | ---: | ---: |
| 原PG05 | 41 | 13 |
| 補修（一） | 45 | 45 |
| 補修（二） | 31 | 31 |
| 補修（三） | 17 | 13 |
| 本輪補修（四） | **0** | **0** |

錯誤計數涵蓋supported判斷與scope案例；非自然新聞錯誤率，不可與歷輪各自不同案例集的失敗數直接比較。比較保存各輪qualification／material實作快照與hash；最後候選另通過完整producer、state、回放及瀏覽器檢查。本輪最少且無已知阻擋，因此保留本輪，無須回復舊版或啟動補修（五）。

## 修正內容

- 交易判斷保留支配動作的否定；中性插入語可略去，含否定／條件的插入語保留。疑問限制綁定動作所在子句，冒號後的獨立展望問句不再否決已確認交易。
- 模型發布要求該次動作的非疑問、非假設、非否定狀態。型號可由原始摘要建立，動作狀態只從包含該次型號與發布述語的子句判斷。
- 模型後綴要求完整述語，例如「正式開放」；「正式文件／正式使用手冊」不再因「正式」前綴取得資格。所有格依後接受詞區分，weights／權重可作模型分發，指南／文件仍排除，權重文件也不准入。

只改`scripts/publisher_material.py`、`scripts/publisher_governance.py`，新增`tests/test_publisher_relations_final.py`的40項正式回歸及四份治理／交接文件。前端、來源設定、事件matcher／state／phase／時間、評分權重、.65／.72、registry／准入／計票鍵／cn_aggregator保持。

## 最終驗收

| 檢查 | 結果 |
| --- | --- |
| 完整Python | **2,150 passed，10.90秒**；包含新增40項，原補修（三）127項保留。 |
| 合成語義／實際producer | 原七、22、24、20例及最後固定24例全部通過；最後44例同時檢查首頁正例恢復與負例零入選。未注入用途分數。 |
| 容量 | 七項通過；annotation產生器以降低上限驗保守處理，非十萬筆效能測試。 |
| 真Chrome | **150 contexts通過**：固定／legacy／合成10、回復6、舊反例6、前輪反例12、14日28、新20例40、最後24例48。歷史28個為桌機；其他涵蓋1440／390。CNBC只一徽章，混版／過期／回復保持。 |
| 目視 | 手機插入語否定與正式文件不再進今日重點；所有格權重正例恢復。截圖僅合成新聞，外部請求阻擋。 |
| 14日回放 | 相同14份輸入／previous state／asof，56個candidate檔與前輪逐位元組一致；1,914事件窗口、14份state與raw projection保持，daily1、一般1,976列次。無新增資格或選集變化。 |
| 固定讀者資料 | 18檔逐位元組一致；194一般篇／183 raw事件／0 featured／0 daily／1媒體雷達。source-status保持。 |
| 語法與衛生 | 指定Python編譯、三份JavaScript node --check、git diff --check通過；14個正式資料檔對canonical_data錨點保持。 |

「最後檢查」不同於補修前的第三次複驗：BROWSER_NEW_REVIEW與BROWSER_FINAL_CHECK都要求正確產品輸出及product_acceptance_passed=true，不能以錯誤輸出重現成功充當通過。

## 保留的限制

1,039ID固定點隔離、72 protected／448 reserved、六個中文模型族與bare Claude別名保護保持；原PG05污染紀錄保留。本輪沒有新增真實新聞標題／內文人讀，因實際資格與選集無變動，無新增允許的進退出個案需審。

補修（三）相較補修二唯一隔離重點退出仍未人工判定；不為此解除隔離或宣稱自然新聞品質通過。合成、先前已看過內容只能作開發回歸，**independent_precision=not_evaluable**。本輪是同一助理的結構化檢查，不宣稱另一模型獨立審查。

14日回放是保留archive的固定輸入重建，PG03 baseline沿用封存，非當時線上觀測。詞法規則仍有邊界，95例無錯不能保證所有自然語句正確。這些限制不改寫為新的無限補修任務；後續正式缺陷需按個案另行處理。

## 封存與完整交接

證據目錄：`/Users/lordmi/Downloads/ai-news-radar-pg05-final-20261024/`。先驗SEAL.sha256及MANIFEST的全部files與repo_files，再讀HANDOFF、VALIDATION、FINAL_DECISION與ROOT_STATE。

- START_STATE／before：前輪594檔與43候選起點；PG05_FINAL_ONLY.patch只含本輪七檔變更。
- STOP_RULE／FINAL_CHECK_CASES／FROZEN_CODE：事前標準、24個最後案例、最後檢查前凍結hash；凍結後無runtime變更。
- CANDIDATE_COMPARISON／comparison-code／COMPARISON_SOURCE_AUDIT：95例共同比較、歷輪程式快照及前輪封存hash核對。
- NEW_REVIEW_RESULTS／FINAL_CHECK_RESULTS／BROWSER_NEW_REVIEW／BROWSER_FINAL_CHECK：本輪44個案例與88個畫面驗收。
- HISTORY_COMPARISON／REPRODUCIBILITY／history：14日同輸入／state／raw及選集核對；REVIEW_BOUNDARY先於任何人讀。
- PYTEST_FULL／CANONICAL_DATA_CHECK／BROWSER_INPUTS：完整回歸、正式資料保持與瀏覽器輸入綁定。

**下一步PG06發布與上線驗收：GPT-6.1 Sol／High。** PG05候選已定稿，不再開補修（五）。本輪停在本機定稿，未自動執行PG06。

PG06先依docs/OPERATIONS.md核現況、遠端／bot新增提交與既有發布策略，完整保留資料；按依賴順序發布後核既有CI／Pages／正式HTTP同代、資產hash、首頁／一般列表／雷達及CNBC單徽章。先核候選seal，遇到漂移先釐清，不以覆寫資料或重設工作目錄解決。需要回復時沿既有保守gate／副本回復方式，保留state／事件時間。日報、觀察、SMTP及新排程均不重啟。
