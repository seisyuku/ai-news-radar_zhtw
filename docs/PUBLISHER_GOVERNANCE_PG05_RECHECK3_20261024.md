# PG05補修（三）複驗與補修（四）交接

日期：2026-10-24。結論：**發布驗收未通過，release_ready=false，不進PG06。**

本階段只修改本文件與HANDOVER／SOURCE_COVERAGE／ROADMAP，未修改runtime、測試、正式資料或來源設定，未提交、推送、dispatch或部署。HEAD仍為`8deab0c1b61a7560c2f552c5366b3776bc82dd51`，累積候選從42檔增為43檔。

## 可重現結果

起始核對補修（三）MANIFEST的477個證據檔、42個候選檔及HEAD均相符。完整Python測試2,110項通過（11.43秒），既有原七／22／24個合成案例與七個容量檢查通過；三份JavaScript語法與git diff --check通過。容量測試使用降低的annotation上限觸發保守路徑，不能宣稱十萬筆效能已測。

新20個合成案例在執行前寫定預期，14通過、6失敗（4誤收、2誤排）。測試經實際AI關聯、business-event、來源政策、資格判斷、story／brief產生器與雷達路徑，未注入用途分數。合成官方網址僅是本機fixture，並不表示真實發布者發表了這些文字。

| 檢查 | 結果與限制 |
| --- | --- |
| 固定14日回放 | 56個candidate檔與補修（三）逐位元組一致，14份輸入保持；1,914事件窗口原state／raw保持，daily1、一般1,976列次。PG03 baseline沿用封存；這是保留archive重建，非當年線上實測。 |
| 固定讀者fixture | 18檔逐位元組一致；194篇一般新聞、183 raw事件、0 featured／daily、1則媒體雷達。 |
| 正常Chrome驗證 | 62 contexts通過：固定／legacy／合成／命名10、回復6、舊反例6、補修（三）反例12、14日配對28；桌機1440與手機390，含CNBC單徽章、混版及過期保守處理。 |
| 新反例Chrome | 8例×2寬度共16 contexts成功重現producer輸出，product_acceptance=false；含六個失敗及兩個正例。四個誤收均進首頁，其中假設句及正式文件另進雷達；兩個誤排未入選。無溢位或頁面錯誤不代表資格正確。 |
| 正式資料 | 14個正式資料檔與先前canonical_data錨點一致。 |

手機截圖另目視確認插入語否定、模型假設句及正式文件三個案例。所有新案例均保留一般列表一篇，缺陷集中於用途資格。

## 必修發現

### R3-01：交易述語範圍被標點切錯

`OpenAI has not, in fact, acquired Cedar Labs`＋`There is no transaction.`仍為supported並進首頁。`scripts/publisher_material.py:239`在最後逗號截取action前片語，丟掉支配acquired的not。

反方向，`OpenAI acquired Cedar Labs: what happens next?`＋`The transaction closed today.`被降為insufficient。相同檔案243–245行把整個clause任何問號都當成交易未確認，後接的獨立展望問句誤擋已肯定的交易。

修正應保存插入語兩側的否定作用範圍，將疑問綁定交易述語。保護無插入語否定、破折號否定、直接完成交易與已簽約待核准四類既有正反例；不得以全篇含問號一律排除處理。

### R3-02：模型發布未要求肯定、非假設的動作狀態

`Did OpenAI release Photon Nova AI model?`＋`No launch has been announced.`仍supported並進首頁。`If OpenAI releases Photon Nova AI model, developers will get new features`＋`This is a hypothetical scenario.`仍supported，進首頁及雷達。

`scripts/publisher_governance.py:72–84`的has_model_release先排部分傳聞／歷史字串，之後以release與model橋接成立；缺少綁定該動作的疑問／條件狀態。應要求當期肯定發布，保留直接發布及「模型本體附帶文件」正例；不要改成全篇關鍵字封鎖。

### R3-03：完整受詞判斷仍有前綴誤收與所有格誤排

`OpenAI發布Photon Nova模型正式文件`＋`這次僅發布既有模型的文件。`仍supported並進首頁及雷達。`scripts/publisher_material.py:116–120`把正式當允許後綴的前綴，未確認後續完整詞組是文件。

`OpenAI releases GPT-6.1 Sol's weights`＋`The new open-weight model can be downloaded today.`反而insufficient；無所有格的同句weights正例可supported。相同檔案102–104／111–112行在辨識weights之前全面拒絕所有格。權重是既定可接受發布受詞，修正需區分weights與training guide／documentation等附屬內容。

應以完整受詞及後接述語判斷，不只增加六條字串特例。保留引號文件、所有格指南、model series documentation排除，直接模型／中文發布／預覽版／模型附指南的正例。

## 隔離與解讀邊界

強隔離維持1,039個ID固定點閉包，包括ID、raw／canonical URL、重複鏈、完整型號、bare Claude別名與六個中文模型族。先前72個protected／448個reserved及既有污染標記保持；不得消除原PG05的一筆曝光紀錄。

本輪沒有人工閱讀新的真實新聞標題／內文，只看合成內容、機械計數及hash。補修（三）相較補修二的daily2→1及唯一隔離重點退出仍未人工判定，這次沒有新增退出。既有允許材料、合成例與已看過內容只能作開發回歸，**independent_precision=not_evaluable**；不能宣稱另一模型獨立審查或自然新聞品質已驗收。

## 下一階段完整交接

證據目錄：`/Users/lordmi/Downloads/ai-news-radar-pg05-recheck3-20261024/`。先驗SEAL.sha256、MANIFEST全部檔案與repo_files，再讀HANDOFF、VALIDATION、FINDINGS、NEW_REVIEW_RESULTS及new_review_probes.py。START_STATE保留補修（三）manifest hash與42檔起點；before與PG05_RECHECK3_ONLY.patch可核對本輪僅四份文件變更。

**下一步PG05補修（四）：GPT-6.1 Sol／High；完成後GPT-6 Astra／High複驗。**

1. 限於material述語範圍、模型動作肯定狀態及完整受詞補修，先加入六個失敗及十四個控制的正式回歸；保留既有127個補修（三）新增測試。
2. 將新反例瀏覽器檢查改為正確產品預期：四個負例首頁／雷達為零，兩個正例恢復support及對應用途資格。現有browser_new_review.cjs刻意斷言「目前錯誤輸出可重現」，不能直接把verification_passed=true當補修驗收。
3. 完整Python、原七／22／24例、20個新例、容量、同輸入／state／asof的14日回放與真Chrome重驗。先跑隔離閉包，再看允許的實際進退出材料；保護案例只能機械核對，保留品質限制。
4. 封存新證據並更新交接；複驗通過前不進PG06。維持事件matcher／state／phase／時間、.65／.72、評分權重、registry／准入／計票鍵／cn_aggregator、來源fetch與現有前端契約，不引入LLM／全文／跳轉抓取、日報自動化、寄信或新排程。

本次沒有授權直接發布；不因反例修好或推薦數變多而自行推送。
