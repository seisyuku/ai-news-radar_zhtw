# PG05補修複驗（2026-10-24）

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：階段歷史／已結案。** PG01～PG06已正式發布，最後補修（四）定稿；本頁的下一步、未通過、待推送只描述當時，不再開補修（五）。技術契約與限制保留，對照[PG06](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)及SOURCE_COVERAGE使用。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

**複驗完成，發布驗收未通過。下一步為PG05補修（二），建議GPT-6.1 Sol／High；修後再由GPT-6 Astra／High複驗。** 本階段未改runtime，未提交、推送、dispatch或部署。

原七個反例已修好，完整1,904項回歸重新通過；新增22個合成正反案例中14個通過、8個不符預期。失敗集中在以下三類材料關係，不能以既有回歸全過作為發布依據。

## 必修發現

| 編號 | 可重現問題 | 根因與修正範圍 |
|---|---|---|
| R01（P1） | `OpenAI is not acquiring Cedar Labs`、`considers acquiring`、`hopes to acquire`及「不會收購」均取得market supported。明確否認或尚在考慮不能作為已成立交易。 | `publisher_material.py`的交易動作只要前後有名稱就接受；`uncertain_market`與`publisher_governance.py`的DENIAL未涵蓋這些語態。須把肯定／否定／未定案狀態綁到具體交易動作，而非只補單篇詞例；保留已公告協議、待監管核准與未來生效停運正例。 |
| R02（P1） | `OpenAI releases GPT-6.1 Sol documentation`及`OpenAI releases Photon Nova AI model documentation`均被當作模型發布。後者也進入真正的模型雷達輸出。 | `has_model_release`只核release到模型名稱之間的字串，沒有確認完整受詞的中心是模型本身；模型名稱後的documentation等附屬物被忽略。須區分模型本體發布與文件／報告發布，保留真正新模型附帶文件、價格或使用說明的新聞。 |
| R03（P1） | 標題`OpenAI earnings discussion`搭配摘要`ExampleCloud reports Q3 revenue of $2 billion.`，把另一家公司數據授給標題事件；兩個未列名公司亦有同樣問題。 | `focused_text`公司／產品分支仍只用舊詞表排除其他主體，未列名ExampleCloud不被當成不同主體；earnings又只要求某處存在公司、某句有數字與期間。須以具體公司—財務動作—數據關係判定，不能跨公司借材料。 |

上述皆為明確標示的**合成反例**，不是指稱真實OpenAI發表過這些新聞。三個代表案例通過實際AI相關性判斷，使用正式產生器、原分數與官方fixture身分，均得到一張首頁卡；R02未知模型文件案例另有一則雷達。真Chrome桌面／手機六個contexts重現，截圖只含合成稿。沒有注入資格分數或修改registry。

八個分類失敗案例並不都代表生產環境的收錄率；例如完全未列名公司案例另可能先被AI相關性攔住。發布阻擋依據是三個代表案例已穿過實際讀者鏈路，以及其餘等義變體的材料判定不符D05。未知來源拒收、來源分級與.72門檻都不能取代正確的材料關係。

## 已通過與可重現部分

- 補修封存233個證據檔、36個候選檔與HEAD在開工時完全相符。runtime、前端、資料、來源registry、matcher、state與時間未變。
- 完整1,904項回歸、七個原驗收反例、七個容量檢查、Python／JavaScript語法及diff檢查通過。
- 沿用14個固定時鐘、同輸入與previous state、21日前置warmup；重新產生的56個candidate檔與補修封存逐位元組一致。1,914事件窗口原始投影與state保持，daily仍合計2個事件次數。
- 固定快照及兩組合成正例共18個JSON檔重建一致。固定194一般篇、183根、零featured／daily與一則媒體雷達保持，沒有新的線上觀察結論。
- 原有44個Chrome contexts重新通過，涵蓋14日首頁、桌機／手機、混版／到期、CNBC一枚徽章及副本回復；另6個contexts成功重現上述缺陷。合計50個contexts，但不能寫成「50個產品驗收全通過」。

## 實際影響與隔離

沿用補修版強隔離工具，以PG05擴增ID為下界核對原／canonical URL、duplicate、完整模型與裸Claude家族版本別名、六CN家族。1,039個隔離ID與前階段完全一致，本次沒有新增保護內容曝光。

只重讀隔離允許的四篇實際讀者變化：TechCrunch購票促銷、Copilot初心者教學、企業治理泛建議三篇排除合理；LingDT-Decision-1.0的保存材料有明確模型發布與平台可用動作，雷達維持媒體報導標示合理。這四篇及先前已審材料均是開發回歸資料；**independent precision仍為not_evaluable**。新的合成對抗測試也不是自然新聞品質抽樣。

## 補修交接

證據：Downloads `ai-news-radar-pg05-recheck-20261024/`。先驗`SEAL.sha256`／`MANIFEST.json`，再讀`HANDOFF.md`、`FINDINGS.json`、`adversarial_probes.py`／`ADVERSARIAL_RESULTS.json`及`BROWSER_COUNTEREXAMPLES.json`。前階段封存保持唯讀。

1. 把八個失敗情境及十四個對照轉為正式回歸；優先處理交易狀態、發布受詞與財務主體三種關係，不新增逐篇ID／URL或逐品牌例外。
2. 修改限於資格與材料關係層；保持來源准入、計票鍵、matcher／state／時間、importance權重與.65／.72。不新增遠端LLM、全文、跳轉、來源、觀察或排程。
3. 使用新Downloads目錄驗證完整suite、原七反例、新22反例、固定14日資料與真Chrome正反例；實際選集改變須先經強隔離閉包再閱讀。
4. 補修後另階段複驗通過，才開PG06。原補修候選沒有因本次文件更新自動取得發布資格。

**下一階段：PG05補修（二），GPT-6.1 Sol／High。**
