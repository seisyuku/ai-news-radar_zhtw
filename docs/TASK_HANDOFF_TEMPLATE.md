# 小任務檢查點與交接模板

配合 [DIGEST_PLAN](DIGEST_PLAN.md)。專案持久狀態記在該臺帳與
[HANDOVER](HANDOVER.md) 最新節；本模板填寫後的執行紀錄、log、patch、
樣本日報放 `/Users/lordmi/Downloads/` 的唯一任務目錄。

## 使用方式

開始任務即填 CHECKPOINT；每個完成的小步與長命令前後更新。
正常完成時填 HANDOFF 並更新 repo 的最新續接位置。硬中斷後讀最後落檔版本，
不假設尚未落檔的工作完成。檢查點以同目錄 temporary write＋replace 更新。

`done` 只在任務自身驗收通過且交接已落檔時使用；未完成用 `in_progress`，
有具體外部阻塞才用 `blocked`。不同 task 狀態不要靠對話中的「完成」推測。

## CHECKPOINT.md（任務開始就寫）

```markdown
# <task-id> — <名稱>

- updated_at: <Asia/Taipei ISO timestamp>
- project_root: /Users/lordmi/Documents/ai-news-radar_zhtw
- task_state: planned | in_progress | blocked | done
- stage: inspect | implement | validate | handoff
- branch / start_HEAD / current_HEAD: <實際讀取，不猜>
- evidence_dir: <絕對路徑>
- authorization: <已同意的本機範圍；未核准的外部操作>
- existing_changes: <開始前已有的修改；不能覆蓋>
- changed_by_this_task: <檔案與目的；含 untracked>
- source_inputs: <版本、as-of、schema；不列私人內容>

## Last verified step

<已確定完成的小步、實際證據與相對於哪份差異>

## Pending action

<下一次命令／編輯要做什麼；開始前寫，結果出來再更新>
- command / cwd / safety: <命令與工作目錄；離線／有外部影響>
- output / log path: <絕對路徑或尚無>
- process / session: <若仍執行中的 tool session ID；不保證跨聊天可用>
- observed_result: pending | unknown | succeeded | failed
- retry_policy: <可直接重試／先核對外部結果；是否可能重複計費>

## Tests already run

| Exact command | Result / count | Evidence | Still applicable? |
| --- | --- | --- | --- |
| <實際命令> | <通過／失敗／未完成> | <log路徑> | <有無後續程式變更> |

## Decisions / limits / remaining work

<已決定的取捨、原因、不可變約束；具體尚缺項目>

## Resume action

<一個可直接接續的動作；不要寫「繼續完成」這類空泛指示>
- next_task_id: <若本任務未完成，仍是本 ID>
- recommended_model: <實際可用的模型名稱>
- reasoning_effort: <Low / Medium / High / Extra high 等>
- reason: <下一步的複雜度／風險；何時可調低或應調高>
```

## HANDOFF.md（任務完成或停止時）

```markdown
# <task-id> 交接

## Task and authorization

<ID、目標、範圍、未授權的外部操作；停止不等於已完成>

## Baseline and current state

<project_root、branch、起始／目前 HEAD、既有修改、此次新增或修改檔案>
<本機文件／程式／生成資料／commit／push／部署的實際狀態>

## Deliverable and acceptance

<可直接開啟的絕對路徑、接口或 schema、完成／未完成的驗收項>
<每項主張對應的測試／輸出；不能以 stub 宣稱 API 實際可用>

## Decisions preserved

<不能丟的語意、取捨、證據限制、外部檔案／來源版本>

## Commands and results

<確切重現命令、工作目錄、離線或外部呼叫、結果數、log路徑>
<尚未驗證的部分；後續改碼是否使較早測試過期>

## Failure and recovery

<未完成 command／session、結果是否 unknown、如何先查再重試>
<保留 diff；回滾僅針對此任務檔案，不 reset 使用者工作>

## Next stage

- task_id: <下一個可執行任務；若中斷則本任務>
- dependencies: <已滿足／仍缺哪項>
- first_action: <一個具體且可恢復的動作>
- recommended_model / reasoning_effort: <模型／強度>
- rationale: <理由、降級／升級條件>
- external_gate: <如無則明示無；不要重問已同意的本機工作>

## Repo updates

<DIGEST_PLAN 臺帳狀態、HANDOVER 的最新續接入口是否已更新>
```

## 給使用者的交接回覆

```text
完成：<成果與驗收>
交接：<可點開的文件與證據目錄>
未完成：<重要剩餘範圍>
下一任務：<ID與目標>
建議模型／思考：<名稱／強度>；<理由>
```

不得輸出 credential 值、私人 OPML、未清理的私人 provider payload。
不自動 commit／push，也不為保存檢查點另建資料庫、服務或排程。
