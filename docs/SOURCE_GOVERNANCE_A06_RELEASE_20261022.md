# A06正式發布、驗收與結案（2026-10-22）

**A06：done。本輪來源治理已正式發布並完成驗收，方案A結案。**
依使用者「執行a06」整合既有未提交成果與遠端快照、推送master、核對CI／生成／Pages及正式HTTP／瀏覽器。
八候選本輪封存，不重啟七日觀察；日報維持使用者在Web Chat發起的文檔工作。

## 正式版本與執行證據

| 批次／鏈路 | 已驗版本或執行 |
| --- | --- |
| B01發布者計數 | `8171470214be`；同發布者與跨入口副本只計一次，引用保留。 |
| B02免費額度退役 | `d1391f4c1d4a`；保留價格與兩canary、歷史free-tier基準。 |
| 治理與觀察停用設定 | [fdd55ace6fae](https://github.com/seisyuku/ai-news-radar_zhtw/commit/fdd55ace6fae616436ac71498cbdf5075bacdc2b)；遠端enabled=false。 |
| 新版正式刷新 | [39776599882](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39776599882)，head_sha為上述治理提交，成功；本輪唯一手動刷新。 |
| 生成快照 | [3d6ca07eae33](https://github.com/seisyuku/ai-news-radar_zhtw/commit/3d6ca07eae333f616d337a302e4a5a54cc3ef80f)；父提交為新版程式，只有data／item變動。 |
| A06發現的前端篩選補正 | [6dcd788af4af](https://github.com/seisyuku/ai-news-radar_zhtw/commit/6dcd788af4afa57152a9e959f8280cc42cef356e)；五個資產版本同步`20261022-a06`。 |
| 最終前端Offline tests | [39777396187](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39777396187)，success。 |
| 最終前端Asset version | [39777396255](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39777396255)，success。 |
| 最終前端Pages | [39777394890](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39777394890)，success。 |

最初三批發布版本亦已通過Offline tests／Asset version／Pages；完整run回應、HTTP雜湊與最後結案文件部署回執保存在Downloads
`ai-news-radar-source-governance-a06-20261022/`。私人日報契約workflow為既有手動入口，本輪未觸發，相關離線測試已包含在完整套件。

## 完整性與整合

- A05的37個證據檔與28個候選檔雜湊入場驗證通過並備份；A01～A05封存保留，留出內容未語意展開。
- fetch後檢查全部24個遠端新增提交及其中間檔案變更，均限data／item；3,688個淨變動路徑全部保留。
- B01／B02／治理分批提交並rebase整合，28檔仍與A05候選完全相同；沒有force push或以舊本機快照蓋遠端成果。
- 整合後完整1,533項通過。A06前端補正後完整**1,534項通過**，資產基準與語法／差異檢查通過。

## A06補正：高階多方篩選

正式驗收發現A05漏檢：`multiSourceEventKeys`仍按`sourceSignal`顯示名稱投票，且高階選單仍叫「多源驗證」。
這可能把同發布者的不同入口當多方，也可能把不同官方發布者都歸在「官方更新」而漏選。
已改用當期公開`corroboration_key`集合，未知／舊JSON不加票，選單改「多方報導」，並增加跨入口／不同官方／未知／舊資料的正反回歸。
本次只有前端篩選、文案、資產版本及測試補正，後端分類、分數、rank／cap與生成程式沒有再改，所以正式快照沿用同一成功刷新。
A05的「未發現阻擋項」保留作當時審查記錄，不能解讀為沒有此漏檢；本頁記錄發現與修復結果。

## 正式輸出與讀者路徑

- 正式首頁五個資產版本均為`20261022-a06`，內容與發布檔逐位元一致，觀察設定false。
- 快照時間`2026-10-22T12:13:58.089128Z`：AI 187篇、原始264篇、179故事、內部brief 11則。
  全部當期key／status、發布者計數、raw引用、heat、理由及brief gate符合新口徑；已辨識166、未知21、衝突0。
  這是當輪數量，不與早上D1不同時點直接當成來源損失；固定D1比較仍見A04。
- archive 7427筆沒有回填corroboration欄位。當期及保留歷史各一個JSON／HTML resolver皆HTTP200，ID與原文連結吻合。
- 來源failed_sites為空、persistent failures為0；價格64模型、兩canary各20列均ok。free-tier不是活躍status、沒有當期卡片，歷史基準內容與發布前相同。
  頂層updated_at不代表退役分支的新觀察；本輪市場事件0是沒有偵測到新差異，不是假造感測器成功事件。
- 模型雷達1事件；價格／政策區在沒有事件時正確隱藏。
- 正式Chrome在1440／390像素下，熱點10／時間線20、前三卡發布者標籤、高階多方篩選、全AI／全量延遲載入及健康資料均通過；無JavaScript或HTTP錯誤、無橫向溢出。
  當輪多方篩選結果0，保留空結果；不同官方發布者與跨入口副本的正反行為由新增合成回歸驗證，不為填名額加票。
- 20個HTTP回應逐一對上生成／前端提交的檔案雜湊，確認新版程式→生成提交→Pages的鏈路，沒有只憑generated_at或舊CI綠燈驗收。
  正式瀏覽器只輸出ID／數值／固定介面標籤，未語意檢視受保護新聞內容；版面視覺檢查沿用A05合成案例。

## 最終來源名冊與自動化

53筆最終名冊與原始理由、替代、損失及未知都保留在A06 `FINAL_SOURCE_DECISIONS.jsonl`／`FINAL_SOURCE_ROSTER.json`，公開名冊見[A03](SOURCE_GOVERNANCE_A03_DECISIONS_20261022.md)。
**44保留、8本輪不准入封存、1免費額度自動分支已退役**；44包含39新聞入口、OPML池、人工對照及3感測器，不是44個獨立發布者。
A03的待實作語氣是裁決歷史，實際狀態以本頁為準。

兩來源觀察、兩日報、SMTP驗收共5個workflow仍disabled_manually；與A05相比沒有新增run，遠端Git與正式HTTP設定均false。
全部11個workflow狀態與A05相同，公開刷新／watchdog／Pages繼續既有運作。本輪沒有新增監督、提醒、Email或排程。
原D7／D8人工接手義務已依A01提前終止決策取消，不留10/28～10/29等待待辦。

## 已知限制與回復

八新候選沒有完成七日可靠性或准入品質門檻；D02教學誤收與D03基礎設施漏收仍是明示限制，本輪不修改共享分類／0.65。
沒有等價免費額度自動替代；不同發布者不代表獨立採訪或事實正確。沒有持續採樣、重新評估提醒或待跑階段。

回復先保留B02退役與A01 false，只撤B01行為及本輪相關前端篩選；維持程式／JSON相容並使用新的共同資產版本。
A05的B01-only演練仍是原三批的回復證據；本輪另有`A06_FILTER_FIX.patch`，回復時須納入前端補正，不能照舊批次漏撤新增依賴。
B02問題採維持停用的局部修復；不可reset整個repo、丟棄bot資料或整包恢復舊market payload。回復須再驗適用測試、生成及Pages。

**本輪結案，無下一個必跑階段。** 後續例行維護建議GPT-6.1 Sol／Medium；需修改程式時High。模型建議不是新自動化或待辦。
