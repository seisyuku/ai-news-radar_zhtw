# T06：翻譯快取容量量測與結案（2026-10-26）

## 範圍與現時裁決

只讀取 Git 已保存的 `data/title-zh-cache.json` 及本機 Git 物件；沒有執行新聞刷新、呼叫翻譯 provider、修改快取或設定清理。**T06 結案，維持現況；不提容量治理案、不實作 prune，也不安排後續追蹤。** 現有快取為 8,471,344 bytes（8.08 MiB），距離適用的 GitHub 單檔 50 MiB 警告仍遠。歷史快照僅描述已發生的增長，不作為治理觸發判定。

## 已保存快照的唯讀量測

每個日期取臺北時間 23:59:59 以前、在當前分支祖先中最後一筆改動該檔的 commit；10/26 尚未過完，取當時最新保存版本。原始位元組數由 Git blob 量得，筆數由 JSON object key 計算，`summary::` 前綴另計。未讀取或列出任何翻譯內容。

| 臺北日期與提交時間 | Commit | bytes | MiB | 總筆數 | `summary::` 筆數 |
| --- | --- | ---: | ---: | ---: | ---: |
| 10/01 23:36 | `b9ee53abe55a` | 7,417,348 | 7.07 | 37,707 | 4,165 |
| 10/08 23:36 | `df6ad107a7d4` | 7,742,750 | 7.38 | 38,854 | 4,738 |
| 10/15 23:36 | `3d108a58bb6c` | 8,044,526 | 7.67 | 39,882 | 5,251 |
| 10/22 23:36 | `f1129e8b0614` | 8,352,070 | 7.97 | 41,051 | 5,834 |
| 10/26 12:31 | `db5055a98e04` | 8,471,344 | 8.08 | 41,450 | 6,033 |

10/01 至 10/26 最近保存版本淨增 1,053,996 bytes、3,743 筆；前三個完整七日區段各增 325,402、301,776、307,544 bytes。這是選定時間點間的**淨變化**，不是每日或每輪單調增長證明；最後區段不足七日，不能與前三段直接比較。10/01 另有較早的本地 O06 樣本 7,352,921 bytes／37,441 筆，採樣時間與本表不同，不混入本表速率。

重現方式（從含上述祖先的 checkout 執行，輸出只含統計）：

```bash
python3 - <<'PY'
import json, subprocess
path = 'data/title-zh-cache.json'
for day in ('2026-10-01', '2026-10-08', '2026-10-15', '2026-10-22', '2026-10-26'):
    commit = subprocess.check_output(
        ['git', 'rev-list', '-1', f'--before={day}T23:59:59+08:00', 'HEAD', '--', path],
        text=True,
    ).strip()
    blob = subprocess.check_output(['git', 'rev-parse', f'{commit}:{path}'], text=True).strip()
    raw = subprocess.check_output(['git', 'cat-file', 'blob', blob])
    obj = json.loads(raw)
    print(day, commit[:12], len(raw), len(obj), sum(k.startswith('summary::') for k in obj))
PY
```

## 適用限制與結案裁決

`update-news.yml` 每次刷新會提交 `data/`，故此檔是 Git 一般檔案，受 [GitHub 單檔 50 MiB 警告、100 MiB 阻擋](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)約束。GitHub 建議 repository 盡量小於 1 GB、強烈建議小於 5 GB，但這是整個 repository 的建議，不能以單檔量測判定。當前 checkout 的 `git count-objects -vH` 顯示本機 pack 1.96 GiB，包含所有本地 refs 的歷史，**不能歸因於本快取**，亦不等於遠端預設分支的 repository 容量。GitHub Pages 的[已發布網站 1 GB 上限](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)也是整站限制；本檔目前只佔其中小部分。沒有已知的本專案更低單檔儲存硬限。

目前 8.08 MiB；歷史完整七日增量約 0.29～0.31 MiB。這些證據不足以支持現在清理或改變快取格式。維護者已明確裁決 **T06 到此結案，無後續追蹤**；原擬的 14 日前瞻觀察、15 個日樣本及 25 MiB／2 MiB 預警門檻均不啟動、不保留為待辦。公開讀者窗口、翻譯及摘要 provider、排程與資料格式均不變。若將來出現新的具體容量問題，須以新任務重新定義證據與門檻，不從 T06 自動續行。
