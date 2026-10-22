# S03隔離部署與實際鏈路驗收（2026-10-22）

**S03技術鏈路驗收通過：主補取樣、artifact、真SMTP及自然喚醒去重均已驗；僅待使用者確認今天D1郵件實收，仍in_progress。**
D00日報退役維持完成；兩封SMTP範例已實收，不重寄驗收信。

## 目前唯一啟用版本

- code SHA：`51551fdf695249547c7db4e6a4d67ed8b47212ea`；workflow／config分批釘選發布，精確版本與讀回保存Downloads。
- experiment_id：`twso-20261022-0800-v3-20261022t001200z`，D1～D7為2026-10-22、23、24、25、26、27、28。
- Asia/Taipei主08:00／補08:30，補採樣開始截止08:50；報告期限09:05、備援核對至09:20。
  UTC cron為`0 0 * * *`／`30 0 * * *`／`5 1 * * *`。主已完成不重抓，通知仍先存intent後送。
- 使用者本人接手10/28 D7結束核查及最晚10/29 D8臺北08:00異常停用。
- 觀察workflow SHA256：`e6f1c23aa58874a1250c45d7c134cca223855117d8a149dec0d71199bb233d23`。
- 報告workflow SHA256：`04ab26e523df4fba51d5341dfc4ff0ddb9e056970913794d9b6b87b378034ed6`。
- [評估契約v2](SOURCE_EVALUATION_CONTRACT_20261022.md) SHA256：`2bc257cb705807160f5b4a31415a25a8f9f8f6513a57df4902475a4e5bdce6a1`；
  v1原文保留，品質／抽樣／分母不變，只改時窗與日曆。
- 手動報告可在09:05後恢復；建立時間也必須在09:05後，避免排隊跨窗。
  歷史查詢從本實驗首日08:00起，保留後續延遲手動恢復，不混入先前07點D0紀錄。

## 08:00首次真實 run 發現的 API 誤擋

主run39696990768在採樣intent之前被invalid_api_path擋下；報告39697041697亦未進通知intent。
兩份真run的intent／採樣／SMTP步驟全部skipped，已保存證據，來源請求為零。
另外核查08:12之前兩份workflow共5個run：效果步驟均skipped或不存在，artifact只有核對診斷或無artifact；
完整metadata／jobs／artifacts另存Downloads的live-api-fix/SUPERSEDED_ZERO_EFFECT；啟用點前的外部效果已逐run查明為零。
原因為安全檢查將合法created時間區間中的`..`誤判路徑穿越；現改為只檢查URL路徑，
真正的跨路徑／外部URL仍拒絕，並以未覆寫get的正式API adapter驗證查詢成功。

新版本明定history_start_at=`2026-10-22T00:12:00Z`（臺北08:12），與實驗ID後綴綁定。
此前run保留為舊零效果版本，不混入新workflow指紋；改同一實驗的啟用點會被拒絕。
08:12後仍使用08:00～08:30主slot，保留實際起時，不回填08:00、不重跑舊run_attempt。
日期、08:30補slot、每日最多兩個真採樣slot與七日期間不變。

## D1主跑真實證據（08:14核對）

[主run39698261767](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39698261767)
於08:12:17正常手動建立，未見合格自然主run；非舊run重跑，無force／日期覆寫。
intent上傳後才取樣，manifest／artifact digest／plan與code釘選驗證通過。
CyberQ10、網管人10、DIGITIMES30筆feed列；資安人兩個feed回HTML，記parse_error；
Meet站外轉址被拒，記host_redirect_blocked，不追轉址。邏輯partial，Actions綠燈不等於五站健康。

baseline於08:05:32生成，採樣完成時約7.43分鐘，7,374筆；與Git提交
`2b5c624f9b97e8c5934b45b677a5ced90bde594e`完整JSON內容相符，13個新聞任務、
16官方／11媒體／4臺灣子來源、10個私人OPML別名均保存。相同generated_at的
AI192／全列表238／公開精選20／故事183筆。原artifact為排序序列化JSON，
補接工具以完整canonical JSON相等確認，不以檔案byte格式差異誤判異版。

主runner46秒，兩份artifact ZIP1,645,600 bytes／展開5,279,714 bytes；
16次collector操作／18個HTTP hop，未請求文章頁。操作計時含巢狀robots，不當獨立牆鐘相加。
正式workflow精確GH API次數未埋點，保留未知；本機驗證讀取次數另列，不冒充工作負荷。
[自動報告39698357742](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39698357742)
成功保存pending_recovery診斷，未建立郵件intent或寄信。08:30只補資安人；三站有效feed與
Meet終態必須沿用原hash／時點。11筆候選尚待人工核對，不能宣稱新增事件。

## D1補跑、當日報告與真SMTP接受（08:33核對）

[補run39700071160](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39700071160)
於08:30:15正常手動建立，當時未見自然補run；主、補均保留實際觸發方式，不宣稱自然cron準點。
補slot只抓資安人；其餘四站capture、hash、retrieved_at與origin_slot均沿用主證據，
合併報告仍有五站、11筆待核候選。兩個真採樣slot均已封存，不再追加第三slot。
資安人仍parse_error，Meet仍host_redirect_blocked，當日觀察結果為**unmet／未達標**；
這不等於三站可用feed失敗，也不能當五站准入通過。

[自動報告39700148524](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39700148524)
依序保存daily-report、mail-intent，再實寄一次`[TW來源觀察][D1/7][未達標] 2026-10-22`。
回執於08:31:31保存，status=provider_accepted、phase=data、smtp_code=250、attempt_no=1，
涵蓋日期只有10/22，report hash／payload hash與manifest綁定驗證通過。
**當日郵件實收已發問、仍待使用者確認**；舊兩封SMTP範例不作當日實收證據。

截至08:32:50四個新版執行合計139秒runner；九個artifact ZIP共3,285,637 bytes，
其中七份經scope／manifest驗證的採樣與通知artifact共3,283,461 bytes、展開10,519,999 bytes；
另兩份為reconciliation診斷。主46秒、補33秒、待補報告24秒、實寄報告36秒。
skipped停用job無runner成本；API回傳其開始比結束晚一秒，不計成負成本。
API精確runtime請求數維持未知，本機只讀驗證API次數另存；完整技術驗收負荷及後續去重見下節。

## 自然旁接與去重、正式Radar驗收（08:38）

既有[刷新39700565137](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39700565137)
於08:35:06自行以workflow_dispatch啟動，成功後自然喚醒
[觀察39700684076](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39700684076)。
觀察mode=skip／reason=slot_already_claimed，採樣intent、來源抓取與bundle步驟均skipped，artifact為零。
這是既有刷新完成事件的真實旁接驗收；來源請求仍只有主、補兩slot，共20次collector操作／24個HTTP hop。

接續[報告39700732599](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39700732599)
成功保存already_accepted／mail_due=false核對診斷；通知intent與寄信均skipped。
再次完整讀驗所有scope／manifest／receipt後仍只有兩個取樣slot、一個daily-final通知鍵、一次DATA250。
七個新版run合計190秒實際runner（skipped無runner成本），十個artifact ZIP共3,286,734 bytes；
七份採樣／通知artifact展開10,519,999 bytes，其餘三份是核對診斷。以上不計既有公開刷新成本。

08:38公開HTTP讀回最新08:35:27快照：13新聞任務均正常且未degraded、公開精選20、全列表235則；
已知market_free_tier感測器故障獨立保留為S05待決。兩份日報及一次性SMTP驗收workflow仍disabled_manually，
兩份實驗及公開update／watchdog仍active。沒有新增來源准入、變更排序或恢復私人日報。

08:32已請使用者確認當日D1信，迄今尚無回覆，不能將SMTP接受或舊範例實收當成這一封實收。
最後接續只需取得該事實、更新S03狀態；不要重抓來源、重寄或另開新實驗。確認後交接S04，
依10/22～10/28七日資料與契約v2評估，模型GPT-6.1 Sol／High。D7結案與自停仍須當時另驗。

## 新時窗驗收與接續

完整離線1507項通過（6.66s）、相關259項通過；包含新UTC日界線、舊D0排除、
晚間手動恢復保留及排隊不能越窗。actionlint／契約品質條款比較通過。
今天08:00後須核對真intent／capture／<=2h baseline與同版source-status、manifest、
來源限制與主補去重、report／郵件intent／provider receipt及使用者實收，記實際負荷。
沒有這些證據不可宣稱已完成S03；採樣失敗照實保存，不回補或繞過限制。

主／補／報告實際run與最終交接在
`/Users/lordmi/Downloads/ai-news-radar-source-governance-s03-20261022/schedule-0800-20261022/`。
目前模型建議GPT-6.1 Sol／High；S03完成後才交接S04，同樣Sol／High。

## 下列為08:00改版前的部署與D0歷史紀錄

下方舊code／指紋、06:00時窗、10/23起日與10/30停止日已由上節取代；
只保留故障／退役／SMTP證據，不作現在的啟用設定。

## 已部署批次

| 批次 | 版本與實際狀態 |
| --- | --- |
| D00入口退役 | `7b2f8e1f256f0bf28625d07c66c4069816de7d00`，已推送master。兩個workflow移除自動觸發與生成／派送步驟，手動也永久跳過；一般CI保留。 |
| GitHub停用 | `digest-generation.yml`、`digest-validation.yml`均讀回`disabled_manually`。查核queued／in_progress／waiting／pending／requested皆0，未取消其他工作。 |
| 私人開關 | 以原設定Doc revision保護，只替換1處`automation_enabled: true`為false；讀回JSON為false，其他設定／檔案位置保留。私人ID與連結只留Downloads。 |
| 觀察程式初版 | `d4bfa7d693e31cbe2acd9254f7305249e3a97107`，已推送master。五支程式、三份測試與四份停用範例完整提交；當時只提交停用範例，後續啟用與修復另列。 |
| SMTP驗收 | `3c876099504127520353ea85a2e19e8c9768cb39`新增獨立手動驗收入口；[39644939363](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39644939363)成功，兩封皆DATA250／provider_accepted，使用者確認「兩封都收到」。該入口已讀回disabled_manually。 |
| 七日啟用版 | `.github/workflows/tw-source-observation.yml`、`tw-source-report.yml`及`config/tw-source-observation.json`獨立批次推送master；引用固定code SHA，日期／指紋見下節。遠端版本與active狀態讀回保存Downloads。 |
| 啟動前修復 | code `f341a1157207254d953022881f23229146cd678c`：在D1前先驗空觀察列並正常返回before_experiment，避免查詢未來ledger；實驗期間仍拒絕缺列或不可讀通知歷史。兩份workflow及plan另批重釘此SHA，不變更日期、實驗ID或採樣／寄信規則。 |

原本機HEAD為`3ac92d087586`；先fetch並核對遠端14個提交只改data／item，再快轉至
`4cf3119c6b18`；249個非資料起始檔案hash均保持，沒有覆蓋未提交成果。
後續日報退役與觀察程式分開提交，不能為撤回觀察而重新開啟日報。

## 驗收與限制

- 啟動前修復完整離線回歸1499項通過（6.32s），相關129項通過；新增4例先重現失敗再通過。
  D00與觀察初版code的GitHub
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

## 寄信驗收與七日日曆

- 本機工具v3已完成真實Gmail認證235；`TW_SOURCE_EMAIL_SETTINGS` metadata時間為
  2026-10-21T17:30:39Z。密碼未寫入本機檔案或repo，實際寄件帳號只留私人回執。
- 獨立GitHub驗收於臺北10/22 01:34成功，成功／失敗範例各一封；兩筆去敏receipt
  均provider_accepted、phase=data、smtp_code=250。使用者已明確確認兩封實收。
  驗收入口只有手動觸發、先保存一次性intent，完成後已停用，沒有採樣。
- experiment_id：`twso-20261023-01`。D1～D7依序為2026-10-23、24、25、26、27、28、29，
  均Asia/Taipei；06:00主採樣、06:30有條件補採樣，06:50截止，07:05核對報告。
  不回補10/22，不延長七個日曆日湊成功樣本。
- **使用者本人接手**10/29 D7結束核查，最晚10/30 D8臺北08:00異常停用。
  自停仍需結案包及其接受receipt；通知不明／拒收時人工異常中止，不新增監督排程。
- 初版啟用workflow SHA256：觀察`d223c930324ed043cfa91854793c185637b5c9e7188921f88dff5b76d9dea6ef`；
  報告初版`b774d73421ac0567e36b6b7f09173e7446ab770eaff2d2e0691cc0521e773100`，已由下列修復指紋取代。
  **目前觀察**`9d406fe9672e94f5be6d50f5ff087aa912e448e3b35270b11058450deb41fb7b`；
  **目前報告**`01023ed038f89f8fce53f8cbadb230acede5cc7211819f0da50ceed96e5c60e7`。
  評估契約SHA256維持`bcd7918d528c9256d56b0bbaefbce9b538b11c975a38a071d541cfa16ea074b2`。
  修改workflow任何byte須重算plan指紋。

S03部署工作已由「執行s03」授權，憑證、實收及停止責任三項門檻均已具備。

## 10/22啟動前實際故障與修復

臺北06:06及06:36的報告run
[39684000876](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39684000876)、
[39687749310](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39687749310)
在尚無D1日期時先讀通知ledger，因起日10/23晚於當日而blocked。
同日採樣run [39687701234](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39687701234)
正確返回outside_experiment，沒有採樣。兩份故障artifact均只有核對診斷，沒有郵件intent／receipt；
這些是啟動前錯誤，不算D1缺測或來源失敗，不回補資料。

修復只改日期檢查順序並拒絕不合理空列：D1前rows必須空，返回before_experiment、
mail_due=false、stop=false；D1起rows不得空，真ledger故障仍封鎖通知。
重播涵蓋真實workflow_run喚醒、schedule、假造啟動前列及實驗期間缺列。
修復證據／確切差異／新pin與部署讀回存Downloads的`prestart-fix-20261022/`。
發布後手動核對僅驗證D0正常結束、不採樣／不寄信，不能當首日實驗驗收。

## 恢復S03的第一個動作

先讀Downloads/HANDOFF、READINESS.json與本文件，再核對master、兩個退役workflow
狀態及七日啟用版遠端版本。不要重做D00、重寄驗收信或寄送歷史日報。
SMTP與實收已完成；核對正式workflow、config的確切byte/hash、固定code SHA及評估契約指紋。
10/23首日以前不製造假D1或提早採樣。首次真run後核對主／補去重、baseline時效、
來源capture、artifact及Email實收，並量測runner時間、API與artifact負荷。

10/29結束後由使用者核對七日日曆、結案artifact、最終郵件receipt及兩份觀察workflow
是否disabled_manually；失敗或不明不能以補造成功回執結案。若自停未完成，最晚10/30
08:00於GitHub Actions分別停用「TW source shadow observation」及「TW source shadow report」。
CLI等效操作如下，只影響實驗，不恢復日報或停用公開刷新：

```bash
gh workflow disable tw-source-observation.yml --repo seisyuku/ai-news-radar_zhtw
gh workflow disable tw-source-report.yml --repo seisyuku/ai-news-radar_zhtw
```

完成啟用後，S03還要交付首日真run／artifact／Email實收與實際日期；尚無首日
證據時不能標S03 done或轉S04。若使用者暫緩實驗，保留程式與停用狀態並記新決策。

**續接S03：GPT-6.1 Sol（`gpt-6.1-sol`）／High。**
完成S03才交接S04，同樣建議GPT-6.1 Sol／High。
