# S03隔離部署與退役驗證（2026-10-22）

**S03進行中：D00日報退役已驗收；來源觀察程式已推送，啟用待必要資料。**
使用者本輪指令為「執行s03」，授權依既定交接落實退役／推送與隔離部署。
目前沒有來源准入、實驗排程、影子來源採樣、寄信或外部heartbeat修改。

入口：[來源治理總計畫](SOURCE_GOVERNANCE_PLAN_20261021.md)、
[D00退役](DIGEST_RETIREMENT_HANDOFF_20261021.md)、
[評估契約v1](SOURCE_EVALUATION_CONTRACT_20261021.md)。
完整外部證據／私人設定讀回／檢查點／續接在
`/Users/lordmi/Downloads/ai-news-radar-source-governance-s03-20261022/`。

## 已部署批次

| 批次 | 版本與實際狀態 |
| --- | --- |
| D00入口退役 | `7b2f8e1f256f0bf28625d07c66c4069816de7d00`，已推送master。兩個workflow移除自動觸發與生成／派送步驟，手動也永久跳過；一般CI保留。 |
| GitHub停用 | `digest-generation.yml`、`digest-validation.yml`均讀回`disabled_manually`。查核queued／in_progress／waiting／pending／requested皆0，未取消其他工作。 |
| 私人開關 | 以原設定Doc revision保護，只替換1處`automation_enabled: true`為false；讀回JSON為false，其他設定／檔案位置保留。私人ID與連結只留Downloads。 |
| 觀察程式 | `d4bfa7d693e31cbe2acd9254f7305249e3a97107`，已推送master。五支程式、三份測試與四份停用範例完整提交；正式workflow目錄沒有新增實驗檔案。 |
| 部署候選 | Downloads內有引用上述code SHA的兩份候選workflow及指紋，actionlint通過；activation plan仍disabled、notification disabled、日期／experiment_id空白。候選檔不等於已部署。 |

原本機HEAD為`3ac92d087586`；先fetch並核對遠端14個提交只改data／item，再快轉至
`4cf3119c6b18`；249個非資料起始檔案hash均保持，沒有覆蓋未提交成果。
後續日報退役與觀察程式分開提交，不能為撤回觀察而重新開啟日報。

## 驗收與限制

- 最新快照基準上完整離線回歸1495項通過（6.95s）。D00與觀察code的GitHub
  Offline tests／Pages均成功；部署候選兩份workflow的actionlint通過。
- D00 CI：[39632826040](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39632826040)；
  Pages：[39632824997](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39632824997)。
  觀察code CI：[39633276821](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39633276821)；
  Pages：[39633275069](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39633275069)。
- 日報停用後執行一次既有公開刷新：[39634002083](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39634002083)
  成功，為一次性S03驗真，沒有新增排程，非自然cron驗收。
  快照`87ddec84b4a0`生成於臺北2026-10-22 00:21:39，一般列表223則、公開精選18則，
  brief_selection保留；[Pages 39634179730](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39634179730)
  成功，公開source-status與daily-brief的HTTP讀回均吻合新快照。
  停用後兩個日報workflow均零新增run，既有update／watchdog仍active。
  原驗證cron的未來時段不另等待；以已移除cron的遠端版本、disabled狀態與刷新後
  無接續共同驗收，沒有再為日報生成或寄送。
- D7容量預演以7415筆、約5.20MB公開archive及每日250筆合成有效文章，模擬
  7日14個主補slot：結案展開97,955,612 bytes、ZIP 22,986,120 bytes、75檔，
  均低於既定140MB／110MB／150檔限制；35列來源矩陣、1750列待核候選。
  D1本機比對約51.16秒，結案建置／校驗約0.84秒；後六日僅沿用合成報告形狀作
  大小測試，不是七次完整效能量測，也不是GitHub API／artifact／SMTP真實延遲。
  首次預演因合成資料漏matches欄位失敗，修正預演fixture後通過，正式程式未改。
  容量結果、原失敗log及成功／失敗信件預覽保存Downloads。首日仍須量runner、
  API與artifact負荷，5分鐘報告逾時不足時先審查重複讀取，不直接放寬上限。
- 正式來源fetcher／排序／公開schema未改。data／item僅同步遠端現有機器人提交，
  本輪未手動生成或重寫snapshot；公開daily-brief與歷史稿件保留。
- 專用Drive secrets保留，沒有刪除OAuth授權或共用憑證；這是退役後另案清理，
  不再是日報自動化必須完成的目標。

## 來源觀察啟用前尚缺

1. 使用者已指定Gmail與收件人；採smtp.gmail.com、465、SSL/TLS，寄件帳號先預設
   同收件人，實際地址僅留私人交接。尚缺Gmail應用程式密碼與
   `TW_SOURCE_EMAIL_SETTINGS`，目前secret名稱清單仍無此項。
   本機TLSv1.3／EHLO250通過，但未認證／寄信，不代表GitHub runner連線已驗。
   Downloads備妥只經stdin上傳secret的隱藏輸入工具，不保存本機密碼、不寄信。
   [Google應用程式密碼說明](https://support.google.com/accounts/answer/185833?hl=en)
   要求兩步驟驗證；工具不替使用者修改帳號安全設定。
2. 成功與失敗通知範例各一封的真實實收驗證；SMTP接受不等於進收件匣。
   前述兩封只作明確驗收，不提前執行日常採樣。
3. **已確認：由使用者本人接手**D7結束核查與最晚D8臺北08:00異常停用。
   不再列待決、不重問。自停仍需結案包及其接受
   receipt；通知不明／拒收時要人工異常中止，不能無限延長或新增監督排程。
4. 前三項完成後，才固定下一個完整臺北採樣日為D1及D1～D7日曆、experiment_id。
   不使用S01／S02的文件日期當開始日，不回補前幾天，也不從半天算完整D1。

S03部署工作已由當次指令授權，不因歷史文件寫「待核准」而重問相同權限。
目前實際缺少寄信憑證與實收證據；停止責任已確認。未具備時不啟動實驗。

## 恢復S03的第一個動作

先讀Downloads/HANDOFF、READINESS.json與本文件，再核對master、兩個退役workflow
狀態及secret是否新增。不要重做D00或寄送歷史日報。
接手者已確認；取得寄信憑證後先完成一次性實收驗證，再核對候選workflow的確切byte/hash、
引用的code SHA與評估契約指紋。修改候選檔須重算plan指紋，不能沿用舊hash。

完成啟用後，S03還要交付首日真run／artifact／Email實收與實際日期；尚無首日
證據時不能標S03 done或轉S04。若使用者暫緩實驗，保留程式與停用狀態並記新決策。

**續接S03：GPT-6.1 Sol（`gpt-6.1-sol`）／High。**
完成S03才交接S04，同樣建議GPT-6.1 Sol／High。
