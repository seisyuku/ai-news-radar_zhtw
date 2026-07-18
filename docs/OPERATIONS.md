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

**現況判準（修好 ≠ 驗證過）**：這個修法目前**尚未實測過任何一次
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

**裁決記錄**：
- cron 密度維持 4 tick/hr（`7,22,37,52 * * * *`）不變：本次的零
  觸發是看門狗**執行邏輯**的 bug，與 cron 密度無關，調密度修不到
  這個洞。
- 外部心跳（第三方 ping 服務代觸發等）降級為觀察項、非立即必要：
  本次事件證明「兩層獨立 schedule 註冊」設計**部分生效**——看門狗
  確實正確偵測到了異常，兩層排程並未同時全滅；問題出在偵測之後的
  執行環節，而非偵測機制本身。優先把現有兩層的執行正確性修好、
  實測驗證，比起再疊一層外部觸發機制更划算。
