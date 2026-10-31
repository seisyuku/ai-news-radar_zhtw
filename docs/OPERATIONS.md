# Operations Notes

## 10/31 Groq修正與影響排序發布驗收完成

Groq修正程式[5e911b10e93e](https://github.com/seisyuku/ai-news-radar_zhtw/commit/5e911b10e93e9bf30b982de3443d5e27531ec768)已整合最新master並推送。[GitHub離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161478560)1989項通過、1項資產比較分流，98個既有警告；本機完整1990項已通過，前端資產未修改。[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161477951)成功後，以既有[公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161538219)產生e19bf57e1ebb，資料[Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41161652223)亦成功。

臺北10:47:34快照：Groq新增6則、失敗0次、成功快取重用14筆，prompt版本v3；來源失敗／降級皆0。一般AI139篇，事件與治理ready，重點0則符合維持70分的裁決。首頁＋六資產＋八份公開JSON與摘要快取共16檔HTTP bytes和生成提交一致；正式下載資料通過讀者端guard與實際混排選集檢查。這是單次正式執行結果，不宣稱長期成功率或獨立新聞precision。

先前影響排序的GitHub事故待辦已核對解除：impact-v2與共同資產20261031-impact3正式上線，原CI及資產檢查成功，本輪同代HTTP與讀者guard再驗通過。維持70分與24小時規則；降標研究結案，不更動門檻或中文E判讀。第五項詳細健康紀錄／總請求上限仍暫緩。發布證據位於 /Users/lordmi/Downloads/ai-news-groq-fixes-20261031/release/。

## 2026-10-31 正式發布與驗收完成

本次依維護者commit／push指示，以遠端master `78435f6b493b`為基礎，保留113筆既有刷新提交；私人早報移除 `7d5a2c4cf1ea`、新聞版本／品質與有界官方文字整合 `cbd1e1a5923b`、維護文件 `8edc35b31ffd`已推送master。既有HF／摘要修正及10/28來源品質／AIBase降級均保留；未合併舊T04實驗歷史，也未刪其他分支。

首次離線CI因刪除雲端套件後不再間接安裝jsonschema而失敗（run 41093066318），已由 `1598a2069b88` 明確宣告測試依賴jsonschema==4.26.0。全新Python3.12環境完整1913項通過；[GitHub離線CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093539300)為1912 passed、1項資產比較刻意分流、98個既有feedparser警告；[獨立資產版本檢查](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093066138)成功。Python／5份JS語法、workflow YAML及差異檢查通過。

[程式Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093065891)與[依賴補修後Pages](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093537947)成功；[一次既有公開刷新](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/41093175458)由新程式產生 `cf3f601098c2`。臺北00:48:35快照168篇一般AI、4則重點（3核心＋1補位），14/14來源正常；brief與publisher governance皆ready。首頁＋6份資產HTTP與發布版本位元一致，8份公開JSON與生成提交逐檔一致，正式資料通過讀者端guard。前端共同版本20261030-quality1。

私人早報84檔已從master移除，3份私人workflow不再出現在正式清單，3個舊說明頁HTTP均404。七日來源觀察／報告／SMTP三流程仍disabled_manually；私人稿件、Drive、OAuth／secret與其他歷史artifact未操作，T04摘要備援未恢復。正式data／item／state只由正常公開刷新更新，未以Downloads離線輸出覆寫。

固定輸入7504檔與已驗整合結果一致，僅source-status實測耗時不同；這不宣稱獨立新聞precision。程式／移除／發布驗收已完成，無下一個必跑功能階段。備份及HTTP／離線證據位於 /Users/lordmi/Downloads/ai-news-release-20261031/；下方10/30「未發布」及較早狀態均為當時階段紀錄。

## 2026-10-30 私人早報程式移除（本機已驗證，未發布）

已移除31個私人生成／派送／Drive／雲端校稿模組、27份專用測試、3份workflow、專用雲端依賴、18份舊操作／設計文件、3頁私人工具說明及1份部署範本；同步清理一般CI引用。RSS原文連結測試改驗公開新聞archive及故事來源投影。完整階段交接位於 /Users/lordmi/Downloads/ai-news-private-digest-removal-20261030/HANDOFF.md。

公開新聞與既有核准保留功能不變，私人稿件／Drive／憑證／資料與state未刪改。本機全套離線驗證已通過：正式1817項、候選1913項；兩版本各7503個同輸入輸出內容一致，僅7項實測耗時不同。沒有commit、push、部署或改遠端設定。遠端手動雲端合約流程仍以發布前狀態為準；不能因本機刪檔宣稱遠端已移除。


私人日報、七日來源觀察與七日回放的取消狀態及相依功能移除評估見[2026-10-25盤點](RETIREMENT_AUDIT_20261025.md)。現行公開刷新、Pages、daily-brief 與全站 24 小時讀者窗口維持。

## 2026-10-26 補位影響評分正式發布

[補位評分與發布驗收](SUPPLEMENT_IMPACT_SIMULATION_20261026.md)記錄 `544d1b79de3d`、`20261026-impact2` 與 21:43 公開快照。I／P／E／C 為 40／20／20／20，僅評估既有合格補位；全站維持 24 小時。CI、Pages、同代 HTTP 及正式瀏覽器驗收通過，當期為 Block、LiteLLM、Meta 三則重點。使用者已明確指定本專案的 `commit push` 包含 master 正式發布與驗收，規則見 `AGENTS.md`。

## 2026-10-28 來源品質修正發布

來源裁決與限制見 [SOURCE_COVERAGE](SOURCE_COVERAGE.md#2026-10-28-三日品質複審與修正已發布)。只將來源品質 commit 整合為 `aaba6389dbb0`，保留 master 較新的前端 impact2 與 bot 資料；無前端資產改動，因此保留既有資產版本。master CI `40626275722`、程式 Pages `40626275654` 成功後，沿用既有 `update-news.yml` 手動公開刷新 `40626297765`，產生資料 `ff3912e294be`，資料 Pages `40626443195` 成功。沒有新增或修改排程。

正式資料臺北 11:22:43，來源失敗／降級皆空、事件／治理 ready；16 個正式 HTTP 檔與發布提交完全一致，瀏覽器實際顯示四則重點。AIBase scope 為 rank 4，其他來源權限與既有計票保持；861 舊根皆保留／alias 延續，initial／phase 時鐘未後移。本輪原工作目錄既有未提交維護文件未混入發布，正式資料由 Actions 生成，沒有拿本機驗證輸出覆寫。

## 2026-10-25 T01 六類事件篩選正式發布

[T01發布與驗收](T01_EVENT_FILTER_IMPLEMENTATION_20261025.md)記錄六資產共同版本 `20261025-t01`、離線 CI 修正、Pages 及正式站 Chrome 驗收。這次只改前端顯示與高階篩選，沒有資料 schema、評分、來源、排程或 provider 變更；例行刷新及 24 小時窗口維持。

## 2026-10-25 CyberQ／AlphaLab 一般入口發布

本次來源接線、刷新與公開 Pages 驗證記在[交接摘要](HANDOVER.md)；來源範圍及未審政策見[來源覆蓋](SOURCE_COVERAGE.md)。兩站沿用現有刷新與子來源健康機制，沒有新排程。

## 2026-10-24 D+ I04正式發布與驗收完成

[I04發布紀錄](SIGNAL_SELECTION_I04_RELEASE_20261024.md)為本案操作入口。後端1fbc429cfdfb由既有正常刷新40107644368產生資料adcdd06ff420，HTTP同代ready後才推前端11e79527f20c；六資產版本20261024-i02。後端／前端離線CI、Asset version 40107902751、Pages、HTTP與Chrome桌面／手機均通過。沒有助理額外dispatch、變更排程或重啟退役工作。

23:35臺北快照68一般AI、3核心＋2補位、1雷達，來源失敗0；417舊根／418舊phase時鐘保持。一般來源准入、雷達資格、價格／兩canary與事件記憶不變；schema2只調整D+用途選稿。回退維持I03／I04的成對相容、保留state／時鐘與新資產版本，不回推舊資料。本案結案，下方I03「未發布」為當時階段記錄。

## 2026-10-24 D+ I03發布前候選定稿，尚未正式發布

[I03驗收與發布程序](SIGNAL_SELECTION_I03_ACCEPTANCE_20261024.md)為D+候選操作入口。I01～I03本機驗收完成，正式站仍為既有PG06版本；沒有推送、dispatch或變更排程。新browser guard拒收schema1，發布須先整合最新bot資料，再後端先行、等既有正常刷新驗同代schema2後才推前端。過渡或失敗時重點／雷達保守不可用，一般列表可讀；不以取消guard或回推舊state修飾。正式推送與線上驗收仍待使用者指定，詳見I03的執行順序及回退邊界。

## 2026-10-24 PG06發布者治理正式發布與結案

[PG06發布紀錄](PUBLISHER_GOVERNANCE_PG06_RELEASE_20261024.md)為目前發布者治理的操作入口。先整合71筆bot提交，後端0a59ff01fa3b由既有07:05 UTC刷新40072742914產生資料4ab86774c904；正式HTTP確認ready及同代綁定後，再推前端eac8c2970ad9。六資產共同版本20261023-pg04，CI／資產版本／Pages／HTTP／真Chrome均通過。

新資料以publisher_governance綁定brief generation／state revision／registry revision；latest／all／daily／radar的meta必須同代。正式檢查先驗schema及跨欄位，再核HTTP bytes與Git生成提交、六資產hash和實際UI；零重點不能以舊gate或無徽章稿補位。15:05臺北快照105一般篇／0重點／1雷達，來源健康與價格／兩canary正常，398舊phase時鐘保持。

未新增或更動排程，沒有助理額外dispatch；五份觀察／日報／SMTP workflow仍disabled_manually，觀察enabled=false，free-tier自動分支退役。PG06本案已結束，不恢復下方歷史日報與來源觀察流程。

回復必須保留有效state與事件時間、保留用途gate，展示變更另升共同資產版本；後端不能供應新資格資料時，重點／雷達明示不可用，一般新聞繼續。不得回放舊資料、刪歷史或將未審來源自動升級。完整封存與下一次維護入口見PG06交接；日常維護GPT-6.1 Sol／Medium，程式變更High。

## 2026-10-22 A06正式發布與驗收完成

[A03實作與回復規格](SOURCE_GOVERNANCE_A03_DECISIONS_20261022.md)裁定單獨退役自動free-tier分支，保留價格與兩canary。
實作歷史見[A04交接](SOURCE_GOVERNANCE_A04_IMPLEMENTATION_20261022.md)；[A06正式版本與驗收](SOURCE_GOVERNANCE_A06_RELEASE_20261022.md)記推送、刷新、CI／Pages及讀者驗收。
下方感測器數量、讀者區名與資料新鮮度已同步正式版本。
兩來源觀察workflow仍disabled_manually，遠端enabled=false已發布；兩日報與SMTP驗收亦維持停用，沒有新增run。
A06補正高階多方篩選漏項，已用20261022-a06共同資產版本部署，完整1,534項通過；[A05發布順序](SOURCE_GOVERNANCE_A05_REVIEW_20261022.md)已執行。
真回復只撤B01時仍保留B02退役，必須另設新資產版本並生成相容當期JSON；不能直接回用反向patch帶回的舊版本號。
A06已保留全部遠端bot提交，核過新版程式→生成commit→Pages與20個HTTP檔案雜湊；後續發布仍須沿用同樣鏈路驗收。

## 2026-10-22 來源觀察提前停止（方案A／A01）

使用者選擇[方案A](SOURCE_GOVERNANCE_EARLY_CLOSE_20261022.md)，兩個實驗workflow
`tw-source-observation.yml`、`tw-source-report.yml`於臺北12:41讀回`disabled_manually`，
查無在途run，其他workflow狀態不變。下方原10/28～10/29核查／停止待辦已取消，不需等待。
停止前36個run的12個artifact全封存並驗GitHub SHA256，分類為依使用者決策提前停止；
七日穩定性、正常結案包／最終Email／自停未驗收，不冒稱通過。

A01本機plan只改`enabled=false`，五種CLI驗為無憑證直接跳過；A06已併入正式發布。
A01當時遠端Git plan仍true，當時由workflow停用阻止排程；A06已同步false。勿依歷史plan自動恢復。
原plan／code pin／manifest用於歷史驗證，停用不刪除artifact、來源、SMTP secret或研究檔。
後續A02使用封存資料集中評估，不新增觀察／提醒／寄信排程；公開Radar刷新、watchdog、
heartbeat、Pages與daily-brief持續按既有設定運作。

## 2026-10-22 日報自動化退役（外部停用與封存提交已落地）

使用者撤回日報自動生成、自動派送與排程目標，改為在Web Chat專案主動要求
收集題目／產生文檔。舊日報生成、Drive交付及三日排程驗收不再作為應恢復或完成的目標。已產生的稿件與校稿保留。

S03已推送封存提交`7b2f8e1f256f`，移除自動觸發，手動dispatch也以false job禁用；
兩份workflow讀回disabled_manually、無在途run，私人開關false讀回。1495項回歸、
GitHub CI與Pages通過；一次性公開刷新／發布讀回正常，停用後零新增日報run，
D00驗收完成，證據見[S03狀態](SOURCE_GOVERNANCE_S03_STATUS_20261022.md)。D00涵蓋
`digest-generation.yml`的workflow_run與派送、`digest-validation.yml`的兩個cron、
私人automation_enabled及在途run；僅設定false仍會有workflow觸發負荷。
具體順序、邊界及驗收見[日報退役交接](DIGEST_RETIREMENT_HANDOFF_20261021.md)。
Radar的update-news、watchdog、外部heartbeat、Pages及公開daily-brief持續維護。

原S03來源七日觀察規格與每日通知流程已由A01提前停止、A06發布 `enabled=false`；原D7／D8及收尾 Email 義務取消。歷史契約與實際停用證據分別見[評估契約v2](SOURCE_EVALUATION_CONTRACT_20261022.md)、[S03狀態](SOURCE_GOVERNANCE_S03_STATUS_20261022.md)及[A06結案](SOURCE_GOVERNANCE_A06_RELEASE_20261022.md)。

## 公開精選診斷與私人日報歷史

公開 `daily-brief.json` 的 `selection_diagnostics`、來源健康快照的
`brief_selection` 及生成日誌仍用於目前的網站維運；全站讀者視窗維持 24 小時。
私人日報的生成、驗證、Drive 派送與每日觸發已退役，不能依舊操作說明重新啟用。
歷史設計與退役證據見[日報退役交接](DIGEST_RETIREMENT_HANDOFF_20261021.md)、
人工選題研究及 Git 紀錄；不再把過時的排程、登入與派送步驟
列在現行維運手冊。

## Pre-push source boundary fixes (2026-10-03)

OPML uses the existing grouped-feed validator, preserving valid empty feeds and
successful peers. TikHub newly observed missing/invalid creator counts are null,
while reported zeroes and historical archive values stay intact. SocialData
search stops after 10 pages or after observing 100 raw reads before the next
request; a whole page can exceed that threshold. Retained-item estimates are
separate from billing limits; no exact cost ceiling is claimed. Later malformed
search responses preserve earlier results with a diagnostic. No paid live probe
or source schedule change was used to validate these fixes.

## Generated file replacement and resolver cleanup

The I/O implementation lives in `scripts/archive_output.py`; `update_news.py`
supplies the existing normalization/public policies and coordinates generation.
See [the archive/output contract](ARCHIVE_OUTPUT.md) for module APIs and shapes.

`scripts/update_news.py` writes each JSON snapshot, state/cache file, JSON
resolver and HTML item page to a temporary file in the target directory, then
uses `os.replace` after the UTF-8 write closes successfully. Existing file modes
are retained; new generated files use mode `0644`. Temporary names follow
`.<target-name>.<random>.tmp`; a handled write/replace failure removes only that
invocation's temporary file and leaves the previous target intact.

The main generation run prunes expired JSON and HTML resolvers only after all
snapshot, resolver, state and optional cache writes succeed. Standalone resolver
writers retain their default cleanup behavior after their own writes succeed;
callers coordinating multiple outputs can pass `prune=False` and call
`prune_item_outputs` after the complete write phase.

Replacement is atomic **per file**. A later failure can leave complete files from
different generations together; earlier successful replacements are not rolled
back. Resolver cleanup itself is not transactional. This does not guarantee
durability after power loss, and forced termination may leave a recognizable
temporary file. Offline audit/evaluation reports and diagnostic outputs are
outside this scheduled-generation protection.

## Front-end asset cache busting

`index.html` references `assets/styles.css`, `assets/motion.js`,
`assets/loader.js`, `assets/selection.js`, and `assets/app.js` with a shared `?v=<tag>` query parameter.
The deferred loader and selection scripts must precede app.js; see the
[frontend loader contract](FRONTEND_LOADER.md). For example:

```html
<link rel="stylesheet" href="./assets/styles.css?v=taste-ui-0716a" />
<script src="./assets/motion.js?v=taste-ui-0716a" defer></script>
<script src="./assets/loader.js?v=taste-ui-0716a" defer></script>
<script src="./assets/selection.js?v=taste-ui-0716a" defer></script>
<script src="./assets/app.js?v=taste-ui-0716a" defer></script>
```

**Rule: any PR that changes `assets/app.js`, `assets/styles.css`,
`assets/loader.js`, `assets/selection.js`, or `assets/motion.js` must bump the shared `?v=` tag in
`index.html`, in the same PR, and say why in the PR description.**

`tests/test_asset_versions.py` 直接比較目前資產與 Git baseline。只要五個
資產之一相對 baseline 有內容變更，目前 `index.html` 的共用 `?v=` tag
也必須不同。測試不維護檔案雜湊或人工 manifest；CI 使用 push 前一個
commit 或 pull request base commit 作為 baseline。

### Why this matters

GitHub Pages sits behind a CDN, and browsers cache static assets aggressively.
`data/*.json` is fetched unversioned and updates every ~30 minutes via the
scheduled workflow, so readers' browsers pick up new data quickly - but the
front-end JS/CSS that renders that data can stay cached far longer. Without a
version bump, a shipped front-end change (new field, new rendering logic, a
bug fix) can sit invisible for readers who already have the old
`app.js`/`styles.css` cached, while they're already receiving the new
`data/*.json` shape. That mismatch is exactly the class of bug this rule
exists to prevent: new data + old code silently reading fields or DOM
structure it doesn't understand.

### How to bump it

Pick a new tag and replace `?v=<old-tag>` with `?v=<new-tag>` on every
reference in `index.html` (`styles.css`, `motion.js`, `loader.js`, `selection.js`, `app.js` - keep them in
sync even if only one file actually changed, so there is only ever one tag to
reason about). The existing convention is `taste-ui-MMDDx` (month, day, and a
letter suffix for same-day revisions, e.g. `taste-ui-0715a`, then
`taste-ui-0716a` for a second bump the same day) - keep using it unless there
is a reason to switch.

Standard workflow, in order: **1) change the asset file(s) → 2) bump the
shared `?v=` tag in `index.html` → 3) run
`.venv/bin/python tests/test_asset_versions.py` before committing.** The local
default compares staged and unstaged content with `HEAD`. To verify an already
committed branch against its integration base, set `ASSET_VERSION_BASE`, for
example:

```sh
ASSET_VERSION_BASE=origin/master .venv/bin/python tests/test_asset_versions.py
```

`.github/workflows/asset-version.yml` performs the same comparison on pushes
and pull requests. It only runs when an asset, `index.html`, this test, or the
workflow itself changes, so scheduled data-only snapshot commits do not trigger
it.

### What NOT to do

Do not automate this (e.g. a workflow step that rewrites `index.html`'s `?v=`
tag on every scheduled run). The scheduled `update-news.yml` workflow already
commits `data/*.json` every ~30 minutes; having it also touch `index.html`
would pull a source file into that same automated commit and create merge
conflicts between the bot's commits and any concurrent front-end PR touching
the same line. Bump the tag by hand, as part of the PR that changes the
asset, same as any other source change.

## Optional Groq news summaries

T03 既有資料跨期回顧已完成，維持每輪成功新增六則上限與現有 prompt；樣本、可用率、失敗與快取限制見[評估紀錄](GROQ_SUMMARY_T03_REVIEW_20261025.md)。

重點卡片的「AI 新聞摘要」由 `scripts/news_summaries.py` 產生，預設模型
是 Groq `qwen/qwen3.8-27b`。這是選用的增強層，不是資料更新的必要條件：

- GitHub Secret `GROQ_API_KEY` 未設定時安全跳過；不要把值寫入 repo、
  log、Issue 或報告。
- GitHub Variables `GROQ_SUMMARY_MODEL`、`GROQ_SUMMARY_MAX_NEW` 可覆蓋模型
與單輪新增上限；預設分別為 `qwen/qwen3.8-27b`、`6`。
- 只把 RSS/Atom 發布者提供的 `summary`／`description` 送去摘要；只有
  標題的新聞不呼叫 API，也不顯示固定模板假裝成內容摘要。
- 摘要候選優先處理實際入選重點區的主文章，再沿用一般故事順序；候選
  20 則與成功新增 6 則的限制不變。事件投影保留同篇來源摘要／譯文，
  AI 摘要不可用時重點卡顯示「來源摘要」，不借用其他篇內容。
- 摘要 prompt、數字驗證與快取鍵使用主文章原始標題，避免讀者顯示翻譯
  污染來源事實；當原始標題與舊顯示標題不同時，只重建對應內容鍵。
- `data/ai-summary-cache.json` 以模型、prompt版本、標題與來源摘要的內容雜湊為鍵，最多保留500筆。10/31正式版v3按金額／幣別／百分比與支援的數量單位驗證，不用數字子字串判斷；v2成功快取通過完整新驗證後可沿用。提示目標50～90個總字元，硬性30～120，包含英文、數字、空白與標點。
- 10/31正式版先排除只重述標題／媒體名稱的摘要。長度、數字、版本、語言與格式拒收最多補試一次；最終內容拒收（含資訊不足與安全拒收）同鍵冷卻六小時，期間仍不展示被拒摘要，使用既有來源摘要回退。資訊不足／安全拒收直接冷卻，暫時provider故障不套六小時內容冷卻；材料更新會改鍵立即可試。補試只加入固定允許的原因提示，不引用失敗回應。failed仍計每次失敗嘗試，可與補試成功generated同時增加。
- 維護者暫緩第五項逐項健康紀錄與新增總請求上限，本輪不新增事件紀錄、監控或例行報告；保留現行彙總狀態、20候選／6則成功新增限制。未來健康盤點有更多證據時再評估額外處理能力是否值得。
- Provider timeout、額度或輸出驗證失敗只記錄公開安全的錯誤類型；本地
  驗證失敗另以 allowlist `last_error_detail` 標示長度、語言、數字事實、
  必要版本名、格式或安全 gate，絕不寫入 provider 回覆或來源原文。狀態位於
  `source-status.json.ai_summaries`，不阻斷其餘資料檔寫入。
- 外部來源一律視為不可信資料；prompt 禁止遵循或逐字重現內嵌指令，
  本地驗證器會拒絕超長、非中文、指令片段與疑似密鑰輸出。

離線驗證不需要 key：

```bash
python -m pytest -q tests/test_ai_summary_eval.py tests/test_news_summaries.py \
  tests/test_feed_summaries.py tests/test_news_summary_ui.py
```

手動 live 評估只使用合成 fixture，不讀排程快照或文章全文：

```bash
GROQ_API_KEY='...' python scripts/evaluate_ai_summaries.py \
  --providers groq --require-live
```

### Gemini API 串接保留；新聞摘要備援已移除

2026-10-27 維護者裁決刪除 Gemini 新聞摘要備援設計，T04 結案。
不保留候選開關、摘要專用 Gemini provider、備援快取或待驗 gate，也不再
建議未來重測本案。Groq 是新聞摘要 provider；既有 Gemini 讀者翻譯另行維護。

只保留下列手動工具，沒有排程或自動呼叫入口：

- `scripts/gemini_api.py`：呼叫端指定用途、prompt、JSON schema 與輸出上限的 API 串接。
- `scripts/diagnose_gemini.py`：為另外明確指定的新用途保留 API 分層診斷。
- `scripts/provider_diagnostics.py`：共用的錯誤分類與密鑰遮罩。
- `scripts/workflow_result_email.py` 與既有 TLS SMTP adapter：其他工作可明確配置的結果通知與收據。

原 T04 合成摘要 workflow、deadline watchdog、站外心跳 dispatch hook 均移除；
本地一次性自動化先前已刪除。保留工具不構成新用途的啟用或資料送出授權。
現行裁決見[T04退役紀錄](T04_GEMINI_SUMMARY_RETIREMENT_20261027.md)，
介面說明見[通用 Gemini 手動串接](guides/gemini-diagnostic-flow.md)。

## Schedule (cron) health

### Rule: verify every cron edit actually starts firing

**After any change to `on.schedule.cron` in `update-news.yml`, confirm a
schedule-triggered run appears within 30-60 minutes of the push:**

```sh
gh run list --workflow=update-news.yml -L 8 --json event,createdAt,conclusion,status
```

If no `event=="schedule"` run shows up in that window, GitHub has not
re-registered the new cron definition (a known platform quirk, not specific
to this repo). Fix: make one more substantive touch to the workflow file
(e.g. append an explanatory comment - not whitespace-only, some editors
diff-suppress those) and commit + push to force GitHub to re-read the
schedule. This is an infrastructure fix and does not need to wait for
feature-branch review.

**Case on record (2026-07-17):** the cron was changed to
`"7,22,37,52 * * * *"` at `03:12:29Z` (commit `30417f0`). By `05:47Z` (2.5h
later, ~10 expected ticks) zero schedule runs had fired, while every other
health signal was clean: workflow `state == "active"`, no `queued`/
`in_progress` runs stuck in the `concurrency` group, `actionlint` reported 0
issues on the file, and githubstatus.com showed Actions `operational` (no
platform incident). That combination - everything green except the schedule
itself - is the signature of the re-registration issue. A touch-only commit
(`65e4111`) was pushed at `05:47Z`; the first schedule run after it fired at
`05:58:04Z` (`success`), confirming the fix.

### Baseline: what "normal" drop looks like vs. an actual outage

GitHub's `schedule` trigger drops (not just delays) a meaningful fraction of
ticks under platform load - this is expected background behavior, not a bug
to chase every time a tick is late. Measured baseline (`gh run list`
filtered to `event=="schedule"`, see the cron comment in `update-news.yml`
for the underlying numbers): nominal spacing is 15 minutes (4 ticks/hour),
but the **actual observed median interval is ~45-91 minutes**, with P90 in
the 90-135 minute range. Individual gaps in that range are normal drop, not
an incident - don't page/investigate on a single late tick.

**Escalation threshold: 3 consecutive hours with zero schedule runs.** That
is roughly 4-6x the observed median gap and well outside normal drop
variance - treat it as an actual stall and work through the diagnosis in
"Rule: verify every cron edit actually starts firing" above (workflow state
→ stuck queued/in_progress runs → `actionlint` → githubstatus.com → schedule
re-registration touch), in that order, before assuming a code-level cause.

### 2026-07-18 深度診斷複測：看門狗上線後的排程間隔改善幅度

看門狗（12:49:44Z 07-17 上線）之後約 13 小時（至 01:52Z 07-18）的
唯讀複測：schedule 間隔中位數從基線 91-147 分鐘降到 **69 分鐘**
（9 個間隔，max 92.2 分鐘），且期間**零次**需要看門狗代觸發——主
排程每次都在 90 分鐘門檻內自行恢復，看門狗當時僅作為未觸發的安全
網。同時查核：無 queued/in_progress 幽靈 run 卡在 concurrency
group；`update-news.yml` 與 `watchdog.yml` 的 workflow state 均為
`active`；githubstatus.com 近 48 小時事故史與兩次衰變窗口完全不
重合。結論：病因維持「無外因、schedule 註冊反覆靜默衰變」，touch
重註冊（見上方「Rule: verify every cron edit actually starts
firing」）仍是唯一已知處方。附帶發現：看門狗自身的 hourly schedule
也曾出現過同型態丟包（單次 113 分鐘未見新 tick，未造成主排程失
覆蓋）——這個「連兩層 schedule 可能同時衰變」的風險後續在
2026-07-19 真的被觀察到（見下方「External heartbeat」章節背景），
是外部心跳最終被接入的直接原因。

### 看門狗首次實測代觸發事件（2026-07-18）

`watchdog.yml`（獨立 schedule 註冊，每小時整點檢查 update-news.yml
最後一筆 schedule run，超過 90 分鐘未出現則 `workflow_dispatch`
代觸發）上線後第一次真正該出手的案例：

**事件經過**：update-news.yml 於 `01:02:23Z→04:10:23Z` 出現 188
分鐘寬間隔。看門狗 `03:21:10Z` 那筆 schedule run **正確偵測**到
138 分鐘缺口（已超過 90 分鐘門檻），log 也正確印出代觸發告警，
但緊接著執行 `gh workflow run update-news.yml` 時**崩潰**——該行
未帶 `-R` 旗標，job 又沒有 `actions/checkout` 步驟建立 `.git`
目錄，`gh` CLI 嘗試從本地 git 環境推斷 repo 失敗，`fatal: not a
git repository`，job exit 1。代觸發從未真正送出。最終是主排程
自己在 `04:10:23Z` 靠下一個 schedule tick 恢復（event 仍是
`schedule`，不是 `workflow_dispatch`）——不是被看門狗救援回來的。

**修法**：commit `387d27c`，單行補 `-R "${{ github.repository
}}"`，讓 `gh` 不需依賴本地 git context 即可指定目標 repo。
actionlint 0 issues。

**現況判準（修好 ≠ 驗證過）**：這個修法上線當下**尚未實測過任何一次
成功的代觸發案例**——看門狗上線至今的實戰成功率是 0/1（唯一一次
真正觸發即失敗）。驗證標準：

```sh
gh run list --workflow=update-news.yml --event=workflow_dispatch \
  --json createdAt,conclusion,databaseId
```

要看到一筆時間點對得上看門狗告警的 `workflow_dispatch` run，才算
驗證通過；在那之前，不能只看「主排程有沒有恢復」就認定看門狗有效
——本次事件正是「主排程自己晚到恢復、看門狗其實沒起作用」的活生
生反例。

**2026-07-19 驗證更新**：修法之後又觀察到 2 次看門狗真正代觸發，
皆成功——`03:40:35Z`（watchdog run）→ `03:40:42Z`（update-news.yml
`workflow_dispatch`，時間點幾乎重合，確認因果）、`09:07:06Z`（同型
態代觸發，`freshness-check` 正確放行全量執行）。**累計實戰戰績
2/3**（1 次因 `-R` 缺漏失敗、已修正；之後 2 次成功），符合上方驗證
標準，判定通過。

**裁決記錄**：
- cron 密度維持 4 tick/hr（`7,22,37,52 * * * *`）不變：本次的零
  觸發是看門狗**執行邏輯**的 bug，與 cron 密度無關，調密度修不到
  這個洞。
- 外部心跳（第三方 ping 服務代觸發等）降級為觀察項、非立即必要：
  本次事件證明「兩層獨立 schedule 註冊」設計**部分生效**——看門狗
  確實正確偵測到了異常，兩層排程並未同時全滅；問題出在偵測之後的
  執行環節，而非偵測機制本身。優先把現有兩層的執行正確性修好、
  實測驗證，比起再疊一層外部觸發機制更划算。
  - **2026-07-19 裁決更新**：實測到 watchdog.yml **自身**的 hourly
    schedule 也曾缺口 147.7 分鐘（見下方「External heartbeat」章節
    背景），證明兩層防線都是用 GitHub `schedule` 觸發器建的，並非
    真正結構獨立——兩層同時（或先後）衰變的機率比原先估計的高。
    因此把外部心跳從觀察項升級為正式接入，見下方新章節。

## External heartbeat

### 背景

`update-news.yml`（4 tick/hr 內部 cron）與 `watchdog.yml`（每小時檢查
`update-news.yml` 是否逾 90 分鐘未跑、逾時則 `workflow_dispatch` 代
觸發）兩層防線都依賴 GitHub 的 `schedule` 觸發器。2026-07-19 實測發現
watchdog.yml **自身**的 hourly tick 也缺口達 147.7 分鐘（超出正常
週期兩倍以上）——代表兩層防線共享同一個底層失效模式（GitHub
schedule 註冊不定期靜默丟包），並非真正結構獨立。

裁決：接入 cron-job.org（免費第三方 cron 服務）作為第三層心跳，完全
脫離 GitHub 的 schedule 註冊機制，每 30 分鐘透過 GitHub REST API 呼叫
`workflow_dispatch` 觸發 `update-news.yml`。

### 機制圖

```
cron-job.org（每 30 分鐘，GitHub schedule 機制之外）
    │  POST .../actions/workflows/update-news.yml/dispatches
    │  body: {"inputs":{"source":"heartbeat"}}
    ▼
update-news.yml: freshness-check job
    │  只在 inputs.source == "heartbeat" 時查詢
    │  「任何觸發來源」最近一次成功 run 距今幾分鐘
    │
    ├─ < 25 分鐘（內部排程健康）──▶ should_run=false
    │                              update job 整個跳過（needs+if）
    │                              心跳這次只留一筆輕量 run 足跡
    │
    └─ ≥ 25 分鐘（內部排程疑似衰變）──▶ should_run=true
                                       update job 全量執行，等同
                                       接管一次排程 tick
```

`schedule` 觸發、一般手動 `workflow_dispatch`（不帶 `source` 或帶
`source=manual`）、watchdog.yml 的代觸發（同樣不帶 `source`，見該檔
案內註解）一律落在 `!= "heartbeat"` 分支，`freshness-check` 直接
`should_run=true`、完全不查 API，行為與心跳接入前完全相同。

### 使用者交接材料

以下由使用者人工完成（repo 端已備妥、無需再改程式碼）。

**1. 建立 PAT（fine-grained personal access token）**

- Repository access：**僅限** `seisyuku/ai-news-radar_zhtw`（不要選
  「All repositories」）
- Permissions：**Actions → Read and write**（觸發 workflow_dispatch
  所需的最小權限；不要多勾其他權限）
- Expiration：**90 天**
- **到期提醒**：建立時把到期日記在自己的行事曆/提醒工具（GitHub 對
  fine-grained PAT 到期前會寄信到帳號 email，但不要只依賴這封信——
  心跳失效不會立刻造成資料錯誤，只會讓「第三道防線」悄悄失能，很
  容易被忽略）。到期前需重新產生新 PAT 並更新 cron-job.org 的
  Authorization header。

**2. cron-job.org 設定模板**（登入後新增一個 cron job，逐欄照抄）

> **UI 對應**：cron-job.org 的建立表單預設在「Common」分頁，只有
> Title/URL/排程；**Method、Headers、Request body 這三個欄位要切到
> 「Advanced」分頁才看得到**，別在 Common 分頁裡找。排程也不要用
> 「Common」分頁的「Every 30 minutes」預設選項——那個選項不保證會
> 落在特定分鐘數，無法確保跟內部 cron 錯開；要在排程設定裡選
> **Custom**，勾選 **Minutes: 5 和 35**（其餘 Hours/Days/Months 全選
> 「every」），才能精確對到下面表格建議的 `:05`/`:35`。

| 欄位 | 值 |
|---|---|
| URL | `https://api.github.com/repos/seisyuku/ai-news-radar_zhtw/actions/workflows/update-news.yml/dispatches` |
| Method | `POST` |
| Headers | `Authorization: Bearer <PAT>`<br>`Accept: application/vnd.github+json`<br>`X-GitHub-Api-Version: 2022-11-28` |
| Body（raw JSON） | `{"ref":"master","inputs":{"source":"heartbeat"}}` |
| 排程 | 每 30 分鐘，建議錯開內部 cron 的整點分鐘數（內部 cron 落在
`:07/:22/:37/:52`，心跳建議設在 `:05` 與 `:35`，兩者不互相卡在同一
分鐘觸發） |
| 成功判定 | HTTP **204**（GitHub 對 workflow_dispatch 的標準成功
回應，沒有回應 body） |

`<PAT>` 是佔位符——把上一步產生的 PAT 貼進去，**絕對不要把 PAT 貼進
本文件、commit、issue 或任何 repo 內的檔案**，只填在 cron-job.org 的
表單欄位裡。

**3. 設定完成後驗證速查**（cron-job.org 表單內通常有「Test run」
按鈕，設定完直接點一次，看回應碼判斷）：

| 回應碼 | 意義 | 排查方向 |
|---|---|---|
| **204** | 成功，dispatch 已送達 GitHub | 正常，不用管 |
| **401** | 未授權 | 檢查 Authorization header 格式是不是
`Bearer <PAT>`（`Bearer` 後面一個空格，PAT 本體不要多貼到空白或
換行） |
| **403** | 授權格式對但權限不夠 | PAT 的 Permissions 是否確實勾了
`Actions: Read and write`；90 天效期是否已過期 |
| **404** | 找不到資源 | URL 有沒有打錯；PAT 的 Repository access
是否包含 `seisyuku/ai-news-radar_zhtw` |
| **422** | 請求格式錯誤 | Body 是否為合法 JSON、`ref`/`inputs` 拼字
是否正確（照抄上面模板即可） |

**4. 失效排查順序**（上線一段時間後心跳看起來沒作用時，依序檢查）

1. **cron-job.org 執行紀錄**：登入該服務看這個 cron job 的執行歷史，
   確認排程本身有沒有按時觸發、有沒有連續失敗
2. **API 回應碼**：執行紀錄裡看 GitHub API 回的 HTTP 狀態碼，對照
   上面「設定完成後驗證速查」表格排查
3. **guard 行為**：確認 API 有成功送達後，去
   `gh run list --workflow=update-news.yml -L 10 --json event,createdAt,conclusion`
   看有沒有出現 `workflow_dispatch` 的 run；如果有 run 但
   `freshness-check` job 一直判定 `should_run=false`（因為內部排程
   剛好一直健康），這是**設計上的正常行為**，不是故障——心跳本來
   就只在內部排程衰變時才接管

**5. PAT 到期續期操作**（90 天到期前）

1. 到 GitHub Settings → Developer settings → Fine-grained tokens
   重新產生一個新 PAT，範圍設定同「1. 建立 PAT」（僅限本 repo、僅
   `Actions: Read and write`、效期再設 90 天）
2. 到 cron-job.org 該 cron job 的 Advanced 分頁，把 Headers 裡
   `Authorization: Bearer <PAT>` 的 `<PAT>` 換成新 token，儲存
3. 點一次「Test run」確認回應碼是 204
4. 舊 PAT 可以直接在 GitHub 上撤銷（Revoke）
5. **repo 端（workflow YAML、docs）完全不用改**——PAT 只存在
   cron-job.org 的表單欄位裡，跟 repo 程式碼無關

## 翻譯管線（title_zh / summary_zh 產生機制）

英文標題的 zh-TW 顯示值（`title_zh`）與已有 RSS `summary`／`description`
的顯示翻譯（`summary_zh`）都由 `scripts/update_news.py` 的
`add_bilingual_fields()` 產生。唯一 provider 是 Gemini Developer API 的
`gemini-3.5-flash-lite`，透過單輪 `generateContent` endpoint 與 GitHub Actions
的 `GEMINI_API_KEY` 使用；未設定
時安全跳過，保留英文顯示，絕不讓翻譯失敗中斷快照更新。翻譯結果再經
`CANONICAL_NAMES` 正典名稱表處理。`summary` 原文會保留作 AI 摘要的事實依據；
前端優先顯示 `summary_zh`。沒有 RSS 摘要的條目會跳過此步驟，不新增抓取或猜測內容。完整規格與程式碼註解在
`scripts/update_news.py` 內 `CANONICAL_NAMES` 定義上方，這裡只記操作面
摘要（新增詞條、除錯時該看哪裡）。

2026-10-28 依維護者要求補修 Hugging Face 閱讀內容：該站 RSS 只有標題，
標題翻譯本來正常；僅針對已在當期 AI 閱讀池、缺 RSS 簡介的該站文章，
補讀固定 HTTPS 官方 `/blog/` 網址 `.blog-content` 中第一個完整實質段落。
每輪最多 6 篇、啟動新請求前檢查 20 秒預算、單頁上限 1 MiB、不跟隨轉址，
失敗安全略過。當期首段快取於 `reader-excerpt-cache.json`，用 `reader_summary`
提供既有 Gemini 翻譯與「來源首段譯文」顯示；原始 RSS `summary`／archive
保持，首段不參與相關度、事件資格、選題或 Groq 摘要。健康另記
`source-status.json.reader_excerpts`。其他來源仍不補讀文章。

### Provider 與失效界線

- 每輪最多處理 `--translate-max-new`（預設 80）個候選；每個請求最多 30
  段、4,800 字元，單次逾時 45 秒，整個翻譯階段最多 120 秒與 6 次請求。
  請求依序執行。429 只會在 `Retry-After` 落在剩餘預算內時重試，重試仍計入
  六次上限；否則保留英文且不寫入六小時拒絕快取。Gemini endpoint 使用獨立的
  no-retry adapter，避免共用 feed session 把一次 POST transport timeout 暗中重試三次、
  吃完整輪預算；是否重試只由這裡的明確上限控制。
- 失敗候選會寫入 `data/translation-state.json` 的短期拒絕快取：暫時性
  provider 故障保留 30 分鐘，無效譯文保留六小時；期間只保留英文，不重送
  相同內容。成功後會自動移除該記錄。429 限流例外，避免正常額度恢復後
  仍被快取壓住。這個檔案不含 API key。
- Provider 變更會提升該狀態檔版本並捨棄舊 provider 的短期拒絕，避免先前
  的 credential 或 endpoint 故障阻止新 provider 嘗試。2026-09-11 從
  Interactions endpoint 切回適合無狀態批次翻譯的 `generateContent`，並修正
  timeout／retry 邊界時，已提升版本以清除故障期間的拒絕快取。
- `data/source-status.json` 的 `translations` 欄位記錄候選數、請求數、實際
  provider、模型、略過原因與拒絕快取命中數，不紀錄文章內容或任何 credential。
- Gemini 只處理公開新聞的讀者顯示翻譯，不改動現有 Groq 新聞摘要 provider、
  私人產稿器或其資料政策。免費層傳送的公開新聞內容可能用於改善 Google 產品；
  不得傳送私密內容、設定或 credential。

啟用服務前，維護者需在 Google AI Studio 建立 Gemini API key，並在 GitHub Actions
建立名稱完全相同的 `GEMINI_API_KEY` Secret。實際 RPM／TPM／RPD 在 AI Studio 依
專案顯示；目前採固定單一模型，沒有自動 provider 或模型 fallback。兩個名稱皆未設定
仍是支援狀態，只是新英文內容不會自動產生繁中顯示。遷移期間 workflow 也會讀取舊的
`GOOGLE_TRANSLATE_API_KEY` 作為同一把 Gemini key 的名稱相容路徑；新增正確名稱後可
撤銷舊 Secret，毋須同時保留兩者。

### 三種作用模式

1. **遮罩回填**（`mask_canonical_names()` / `backfill_canonical_names()`）：
   英文標題送翻譯 provider **之前**，先把 `CANONICAL_NAMES` 命中的
   品牌/產品詞抽出為 `ZXQ<n>QXZ` 佔位符，翻譯完成後再把佔位符換回正典
   zh-TW 寫法。這是主防線——因為 MT 引擎從頭到尾沒看過品牌原文，不受限
   於「已知會被翻錯的樣式」，任意詞條組合都能正確處理。
   `Canon`／`CANON` 會回填為日本佳能「佳能」；小寫 `canon` 是影視、
   書籍與遊戲的正史普通名詞，不遮罩、交由翻譯服務依語境處理。
2. **出口修正**（`_apply_canonical_names_exit_fix()`，掛在
   `repair_zh_title_translation()`）：對翻譯結果做已知錯誤樣式的事後
   修補，命中時**會回寫** `title-zh-cache.json`。主要服務兩種情況：
   舊快取（在遮罩回填上線前翻譯、已存在錯誤譯文的殘留）、以及非品牌類
   的既有修法（Codex/Bug Bounty/repository 等固定字串修正）。
3. **反向修正**（`apply_canonical_reverse_fix()`，Table C）：無條件套用
   於任何 zh-TW 顯示文字（不論是否經過機器翻譯），**只修正顯示值、不
   回寫 cache**，掛在 `add_bilingual_fields()` 每個組裝 `title_zh` 的
   位置、且都在 `to_zh_hant()` 之後執行。用途是把中國用語專名（谷歌→
   Google、英偉達→輝達）與 Claude 子系詞常見誤譯（寓言/神話/十四行詩/
   俳句/傑作 → Fable/Mythos/Sonnet/Haiku/Opus）拉回正典形式；子系詞
   轉換有共現閘門保護（見下）。

### 快取殘留為何不用手動修

`title-zh-cache.json` 內已存在的錯誤譯文**不需要手動修補或跑一次性
腳本**——出口修正與反向修正都掛在「讀快取值之後、組裝顯示值之前」，
每次排程執行都會重新套用，等同 `to_zh_hant()` 既有的「不改寫歷史、
只修正顯示值」設計的延伸。差別只在於：出口修正命中 Table A/B 詞條時
會順手把 cache 也修正掉；反向修正（Table C）則永遠只修顯示值，cache
原始殘留會一直留著（不影響顯示正確性）。遮罩回填只作用於**尚未進
快取**的全新翻譯，快取命中路徑不會重新遮罩。

### `title-zh-cache.json` 成長治理觸發

T06 已於 2026-10-26 完成唯讀量測並依維護者裁決結案；沒有後續觀察或追蹤。本節只約束將來另以明確任務提出的容量治理，不重啟 T06。

只有在**預先定義且已完成的同一觀察窗**中，容量與成長率兩個門檻都成立時，
才可升級為獨立治理提案的候選。指標、觀察窗與數值門檻必須在觀察開始前
定義，不得事後選取有利的期間或指標。

判定至少需要可重現的多時點量測序列，以及可追溯、具體且適用於本 repo 的
執行環境或儲存限制。任何一項證據不足時不得判定門檻命中；只維持觀察並標示
證據缺口。

門檻命中本身不構成寫入、清理或實作授權。先回報完整證據，再由維護者以新的
明確任務授權建立治理提案；該提案只記錄指標定義、觀察窗、量測序列與限制
依據，不預設 prune、壓縮、分割、重建或其他實作方案。

### 高風險詞與共現閘門（誤殺防護）

短英文單字/常見詞彙（Nova、Muse、Wan、Sonar、Genie、o3、o4、裸詞
Moonshot）只在同標題有對應廠商/實驗室詞共現時才觸發遮罩或修正，否則
交給 MT 照常翻譯——避免把「Amazon 之外語境下的 Nova」這類無關內容
誤判成品牌詞。

Claude 的五個子系詞（Sonnet/Opus/Haiku/Fable/Mythos）額外有「非相鄰
共現」通道：即使子系詞沒有緊貼在 "Claude" 後面（例如 "Claude make
Fable 5 permanent"），只要同一句/同一標題裡有 Claude/Anthropic 語境，
遮罩層與反向修正層都會個別處理該子系詞。**這個通道刻意沒有泛化到
Gemini（Pro/Flash/Deep Think）、GPT（Sol/Terra/Luna）等其他家族的
尾綴詞**——那些是語意開放的常見英文單字，若不要求緊鄰家族詞就處理，
會誤傷 MT 本來翻得動的無關句子；Claude 子系詞是封閉、無歧義的專有
名詞集合，且有實測的大量誤譯證據支撐，才值得做這層特殊處理。反向
修正的子系詞轉換一律要求 Claude/Anthropic 語境共現才觸發，純遊戲新聞
（如《神鬼寓言》系列）或一般詞彙用法（神話、傑作）在無共現時不動。

### 日常維護：新增詞條不用開工單

在 `CANONICAL_NAMES`（廠商/家族名）或 Table C 對應字典裡新增一條
entry、並補上對應 pytest 案例，屬於例行維護，不需要為此開工單。只有
匹配演算法本身（吞尾規則、共現閘門邏輯、佔位符格式）的變更才需要走
完整的工單/驗收流程。BRAND_GLOSSARY 舊機制已完全併入 CANONICAL_NAMES
並移除，程式碼內不再有雙軌並存。

## 排程跳過時的來源健康紀錄

來源健康計算與診斷格式由 `scripts/source_health.py` 管理；API、最小型別、
子來源擴充條件及公開診斷邊界見 [來源健康契約](SOURCE_HEALTH.md)。

X API、SocialData 與 TikHub 在憑證已設定但尚未到抓取視窗時，
`source-status.json.sites` 會保留該站的 `skipped: true`、`attempted: false`。
這一輪沒有新抓取結果：`consecutive_failures`、`first_failure_at`、
`last_failure_at` 與 `last_success_at` 都沿用最近一次實際檢查的歷史。
`last_attempt_ok` 是最近一次非跳過檢查的結果；首次即跳過時為 `null`。
若最近一次檢查失敗，跳過輪會標為 `degraded`，但不增加失敗次數，
也不再次發出 persistent failure annotation；下一次真正失敗才延續計數。
真正成功才清除失敗連續次數並更新成功時間。SocialData／TikHub 的
`paid-source-state.json` 亦只在實際嘗試時更新 `last_run_at` 與結果。

這些欄位區分「尚未到視窗」與「本輪成功」，不代表每個排程輪次都曾
對付費來源發出請求。舊狀態若已把跳過誤記為成功，且沒有可用的
付費來源狀態紀錄，過去失去的精確故障次數無法還原。

官方群組、精選媒體與台灣媒體的 `sites[].subsources` 另以固定
`source_id` 分別保留失敗次數與成功／失敗時間。部分失敗時群組仍可保留
成功來源新聞；連續故障達門檻時，`persistent_failures` 會列出
`site_id` 和 `source_id`，Actions warning／job summary 以
`site_id/source_id` 指向實際失效來源。群組全失敗時不再另發一筆重複
的群組警報。跳過輪不增加子來源失敗次數；舊快照若沒有 `subsources`，
新的子來源歷史從首次可辨識的當輪結果開始，不能從群組次數推回。

CyberQ 與 AlphaLab 自 2026-10-25 起列於 `tw_media` 子來源健康；核對
`source_id=cyberq`、`source_id=alphalab` 的 `ok`、`item_count` 及最近成功時間。
兩站只有未審一般池資格，讀者仍限 24 小時。單站誤收或故障時，可撤回該站
正式 RSS 入口與對應政策 scope；保留既有 archive、state 與其他來源。

## Market Sensor 與速報區

`scripts/update_news.py` 每次既有排程都會呼叫
`scripts/market_sensors.py`；沒有新增 workflow、服務或 secret。名義更新
頻率與整站相同為 30 分鐘，實際新鮮度仍受本文件所述 GitHub schedule／
watchdog／external heartbeat 三層排程影響。

產物：

- `data/market-signals.json`：前端公開讀取；價格事件只保留過去 24 小時，
  與主新聞及 LLM 雷達一致。舊 Canary 卡片不再沿用。
- `data/llm-radar.json`：首頁讀者層的 24 小時模型發布雷達；模型僅標示
  偵測證據層級。價格只保留在 `market-signals.json`，不影響新聞排序。
- `data/market-sensor-state.json`：價格比較快照；退役 Canary seen IDs 於首次刷新移除。
  既有免費額度歷史 baseline 仍保留，不含 token、cookies、帳號或個人 quota。
- `data/source-status.json`：只保留價格這一個活躍 Market Sensor 的成功、解析筆數、
  當輪事件數與 exact error；失敗時 fail-soft，不中止新聞主流程。

首頁只呈現 `price` 事件於「價格變更」，以約 3–4 列高的可捲動標題框
保留完整清單，沒有新事件時整區隱藏。前端對舊資料也只接受 `price`，
避免退役的 Usage policy Canary 候選重新顯示。

A04退役`market_free_tier`自動fetch/diff，舊基準保留於state但不是新觀察；頂層`updated_at`
僅代表當輪其他工作，不表示free-tier新鮮。活躍status／failed_sites／persistent_failures不再包含退役分支。
原payload先封存於Downloads；當期payload及舊JSON前端過濾不呈現free-tier卡片，不生成供應商全部退場通知。
回復發布者計數批次時保留免費額度與 Canary 的退役；不得因回復而恢復舊來源。價格的失敗隔離與24小時窗口維持。

「LLM 發布雷達」同樣只在過去 24 小時有事件時顯示，以相同約 3–4 列高的
可捲動標題框保留完整清單。
它是提醒層而非排名層：媒體的 `model_release` 一律標成
「媒體報導」，只有 `official_ai` 可標成「官方公告」。

若要提高速報時效，先量測事件的來源發布延遲；不可只增加 GitHub Actions
cron。現行 30 分鐘輪詢已使抓取成本接近零，品質成本主要是誤報覆核，而非
網路或運算資源。


## Generation duration observations

`source-status.json.metrics.phases` records monotonic wall milliseconds for
input loading, built-in collection, sensors, each paid gate/fetch path, OPML,
reader preparation, translations, story aggregation, summaries, payload assembly
and output. This is observational; retry, timeout, cron, concurrency, provider
policy and six-success summary limits are unchanged. Phase `state` describes
completion, a disabled/skipped gate, or a raised error; returned source/provider
failures still use their existing health/error fields. A fatal exception records
its phase in memory and propagates without publishing a successful snapshot.

Translation `provider_request_count` copies the existing explicit request count.
Summary `provider_enabled` is separate from phase wall time, which includes cache
and candidate work even without a credential. Summary candidate failures are
not interpreted as HTTP attempt counts. Metrics contain no URLs, content,
credentials or exception details.

Grouped children gain current `duration_ms` around their fetch/parse operation;
a skipped child has zero duration and retains its failure history. OPML's legacy
site `duration_ms` remains the sum of feed work; metrics `opml.duration_ms` is the
wall span including concurrent work and is not that sum.

Output wall time covers snapshots, resolvers, states and optional caches.
`source-status.json` is now published after these writes succeed, before resolver
cleanup. Its own serialization/replacement and resolver cleanup are explicitly
excluded from output timing. This does not create a cross-file transaction:
failed later writes can leave earlier complete files from the new generation.
Cleanup still begins only after every file, including source status, succeeds.


## Free-tier catalog input protection

Free-tier input must be a provider list with unique nonempty string IDs and a
list of nonempty string model names (missing/null models still mean an empty
list). Model names are stripped/deduplicated. Known retirement prose such as
`Retired - the model catalog is gone` is rejected as a catalog format error;
it is not converted into model-added/model-removed reader messages. Errors use
fixed validation codes without echoing the upstream payload.

The existing 80% dataset-retention policy now also guards each retained
provider's model count, using the same floor and minimum-one calculation as
provider/price counts. When a catalog is malformed or collapses, the source is
failed for that round, its previous free-tier baseline remains intact, and no
new free-tier differences are published; existing unexpired signals and other
sensors remain available. Normal small changes still publish existing event
shapes. This can suppress a real bulk retirement until maintainer review; it
cannot prove whether an upstream change is genuine. Large same-size replacement
and arbitrary prose detection are not claimed to be solved by a count guard.
No new source, API call, schedule, public schema, UI or scoring policy is added.
