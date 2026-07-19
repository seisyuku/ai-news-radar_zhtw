# Operations Notes

## Front-end asset cache busting

`index.html` references `assets/styles.css`, `assets/motion.js`, and
`assets/app.js` with a `?v=<tag>` query parameter, e.g.:

```html
<link rel="stylesheet" href="./assets/styles.css?v=taste-ui-0716a" />
<script src="./assets/motion.js?v=taste-ui-0716a" defer></script>
<script src="./assets/app.js?v=taste-ui-0716a" defer></script>
```

**Rule: any PR that changes `assets/app.js`, `assets/styles.css`, or
`assets/motion.js` must bump the `?v=` tag on every reference to that file in
`index.html`, in the same PR, and say why in the PR description.**

This rule is enforced by `tests/test_asset_versions.py`, backed by
`tests/asset_manifest.json` (a `{tag: {file: sha256}}` record of what each
asset looked like at each released tag). `pytest` fails red if the three
assets' content doesn't match the manifest entry for the `?v=` tag currently
referenced in `index.html` - whether because a file changed without a version
bump, or a version was bumped without updating the manifest. There is no way
to silently violate the rule and still pass CI.

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
reference in `index.html` (`styles.css`, `motion.js`, `app.js` - keep them in
sync even if only one file actually changed, so there is only ever one tag to
reason about). The existing convention is `taste-ui-MMDDx` (month, day, and a
letter suffix for same-day revisions, e.g. `taste-ui-0715a`, then
`taste-ui-0716a` for a second bump the same day) - keep using it unless there
is a reason to switch.

Standard workflow, in order: **1) change the asset file(s) → 2) bump the
`?v=` tag in `index.html` → 3) add a new entry to
`tests/asset_manifest.json` with the sha256 of each of the three asset files
at their new content → 4) run `pytest tests/test_asset_versions.py`** to
confirm it's green before committing. Compute the hashes with:

```sh
python3 -c "
import hashlib
for name in ('app.js', 'styles.css', 'motion.js'):
    print(name, hashlib.sha256(open(f'assets/{name}', 'rb').read()).hexdigest())
"
```

### What NOT to do

Do not automate this (e.g. a workflow step that rewrites `index.html`'s `?v=`
tag on every scheduled run). The scheduled `update-news.yml` workflow already
commits `data/*.json` every ~30 minutes; having it also touch `index.html`
would pull a source file into that same automated commit and create merge
conflicts between the bot's commits and any concurrent front-end PR touching
the same line. Bump the tag by hand, as part of the PR that changes the
asset, same as any other source change.

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

## 翻譯管線（title_zh 產生機制）

英文標題的 zh-TW 顯示值（`title_zh`）由 `scripts/update_news.py` 的
`add_bilingual_fields()` 產生，經過 Google Translate（`translate_to_zh_cn()`）
與 `CANONICAL_NAMES` 正典名稱表兩層機制共同組成。完整規格與程式碼註解在
`scripts/update_news.py` 內 `CANONICAL_NAMES` 定義上方，這裡只記操作面
摘要（新增詞條、除錯時該看哪裡）。

### 三種作用模式

1. **遮罩回填**（`mask_canonical_names()` / `backfill_canonical_names()`）：
   英文標題送 Google Translate **之前**，先把 `CANONICAL_NAMES` 命中的
   品牌/產品詞抽出為 `QCANON<n>Q` 佔位符，翻譯完成後再把佔位符換回正典
   zh-TW 寫法。這是主防線——因為 MT 引擎從頭到尾沒看過品牌原文，不受限
   於「已知會被翻錯的樣式」，任意詞條組合都能正確處理。
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
