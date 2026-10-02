# O01 GitHub 驗證與三日觀察

2026-10-03 使用者將O01後續驗證改在GitHub進行。私人日報交付仍由本機入口執行；
GitHub跑的是生成／時效／配對驗證，沒有草稿下載交付或自動發布。

## 驗證流程

Workflow：`.github/workflows/digest-validation.yml`，名稱Daily digest validation。

- 每日臺北07:15／08:15（UTC23:15／00:15）兩次獨立驗證，並可手動指定期別。
  第二次仍執行以觀察後續快照，不宣稱已完成本機自動備援／交付。
- 先跑日報離線邊界／故障測試，再固定遠端master SHA，取同commit三檔。
- 產物只存在runner暫存目錄；生成／pair核對後以固定bytes重跑，比較MD/meta完全一致。
  完成或失敗後清除暫存目錄；runner被強制終止時依賴GitHub暫存runner回收。
- archive已達本期06:00截止，非未來且距核對完成≤90分鐘才ready；過舊／未知／
  未達截止為review-only，workflow失敗，不宣告健康空日。真正新快照空日可通過。
- schedule用run created_at的臺北日期；跨臺北日期才開始的排程標missed_issue，
  不默默換期。手動指定期別供補驗，不算成缺失的scheduled run。
- token只有contents/actions讀取權限，僅用於GitHub GET；沒有provider／LLM憑證。
  不觸發新聞刷新，也不更動現有update-news／Pages工作流程。

## 公開紀錄與私人稿

Actions log／Step Summary只記期別、受控狀態／原因、source commit、archive as-of、
檢查時間、題數、pair／重跑結果。沒有原始payload、題目／摘要、草稿、任意exception或token。
不使用upload-artifact、不提交日報或輸入。公開repo的驗證狀態可以被讀取；
本機私人校稿副本仍在Downloads，不會由GitHub寫入Mac。

## 手動驗證

```bash
gh workflow run digest-validation.yml --repo seisyuku/ai-news-radar_zhtw \
  --ref master -f date=2026-10-03
gh run list --repo seisyuku/ai-news-radar_zhtw --workflow digest-validation.yml \
  --json databaseId,event,status,conclusion,createdAt,url
```

每次確認run的head SHA與已發布程式、source commit／as-of、pair與rerun均通過，
且run沒有artifact；run success不替代新聞校稿、完整coverage或來源健康查證。

## 三日驗收條件

先完成一筆真正workflow_dispatch驗證，再觀察連續三個完整臺北日。
若10/3完成發布，預定第一組完整觀察為10/4、10/5、10/6；實際以schedule出現日為準。

| 每日檢查 | 通過條件 |
| --- | --- |
| 觸發 | 07:15與08:15兩種cron均有event=schedule記錄；手動補跑不填補缺失 |
| 時效 | 至少一筆當期ready且pair/rerun通過，記兩筆實際開始／完成及as-of |
| 上午可用 | 至少一筆在09:00臺北前完成；延遲／漏觸發需記，不宣稱嚴格SLA |
| 私人邊界 | artifact數為0，沒有原始稿／輸入／來源刷新／repo寫入 |

一日不達標，留下原因，修正後重新累積三日；不要將單次手動成功標成O01整項done。
驗證持續保留在Actions歷史，不設三日後自動停用。首次schedule仍需實際出現才證明註冊有效。
[GitHub schedule限制](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

O01狀態為github_observing；下一階段建議GPT-6.1 Sol／Medium，整理三日run證據與時效。
若要將私人日報交付也改至雲端，需另定私人儲存／下載方案，不能用這份驗證摘要當交付物。
