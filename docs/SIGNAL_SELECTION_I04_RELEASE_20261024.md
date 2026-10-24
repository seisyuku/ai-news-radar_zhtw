# I04：D+正式發布與線上驗收

狀態：I01～I04正式發布及驗收完成，本案結案。後端、正常刷新、前端、離線CI、資產版本CI、Pages、正式HTTP與真Chrome均通過；本文件在驗收後提交。

## 正式行為

D+核心優先、核心不足五則才補合格產業動態及能力／安全披露；重要性不再作單一來源核心硬門檻。補位保留「產業動態」、廠商宣稱及未發布標示，不增加第七種核心徽章。精選／全部AI入口常駐、數量等於當前篩選下完全展開可讀列，切換保留篩選、清除保留模式，列表固定原綜合排序。

來源准入registry、39入口、AI公式及0.65、一般精選75／82／官方門檻、matcher與21日事件記憶、雷達材料規則、價格及兩canary保持。未重寫去重、啟用封存來源或恢復日報自動化。

## 發布鏈路

- 從遠端`73fc504b5c34f0dab90fbd53a64a9023e8d4a177`開始，完整保留原本9筆data／item bot提交。發布使用隔離worktree，原I03候選24檔先封存且之後另存stash備份，沒有覆蓋或丟棄本機工作。
- 後端`1fbc429cfdfbc9d6973866f26987997d2c162182`採I01封存八檔，本機2,245項通過；正常推送master。GitHub離線CI **40106843717**與Pages **40106843397**成功。
- 既有正常15:35 UTC刷新 **40107644368**採新後端，生成`adcdd06ff42032977e8da57a8a9d760b2e4add7d`，資料Pages **40107761517**成功。助理沒有額外dispatch；沿用既有provider、頻率與排程。
- 先驗正式schema2同代資料及舊事件時鐘，再把前端接在該資料提交之後。本機整合版本2,304項通過；前端`11e79527f20cb9638bf2cda4b5052836c89155e6`正常推送，六資產共同版本`20261024-i02`。
- 前端離線CI **40107902740**及Pages **40107902685**成功；Asset version **40107902751**成功。CI的完整Git歷史checkout較久，未為此修改workflow或略過測試。

## 正式HTTP與讀者驗收

資料時間為2026-10-24 **23:35:28臺北時間**（UTC `2026-10-24T15:35:28.947245Z`）。HTTP八個資料檔與正常刷新資料commit逐bytes相同；schema及跨欄位驗證、同代meta、generation／state revision與daily選集／主文均通過。

當期68篇一般AI、5重點（3核心＋2補位）、1雷達、0價格事件，來源失敗0。數量是當次快照，並非往後固定配額。417個既有事件根全部保留或alias延續，418個舊phase effective_at完全相同，沒有因部署延後事件時間或重設記憶。

index與六份資產正式HTTP bytes均等於前端提交；真Chrome於1440及390寬度均驗：精選20／全部AI68、68列可完全展開、重點不受下方模式影響、核心在補位前、補位沒有核心徽章、披露標示、查詢保留、清除保留模式、時間線及全量延後載入。無page error、HTTP錯誤、請求失敗或水平溢出。未拍真實新聞截圖，不展示歷史新聞內容。

所有workflow狀態與發布前相同；兩來源觀察、兩日報及SMTP驗收仍disabled_manually，free-tier自動分支維持退役。沒有新增來源品質升降級或獨立precision結論，independent_precision仍not_evaluable。

## 本機、限制及回退

canonical `/Users/lordmi/Documents/ai-news-radar_zhtw`已保留原候選並快轉同步；最終文件提交亦納入同步與乾淨工作目錄核查。隔離發布worktree完成後可封存，原I01～I03與I04證據留Downloads；備份stash不得重套到已發布檔案上。

新版schema2與schema1讀者混配時，重點／雷達保守不可用，一般列表可讀；正常刷新與前端切換間曾處於此已驗狀態。正式切換後同代完整資料恢復。輸出仍為逐檔原子替換，非跨檔交易。回退保持archive／state／phase／時鐘及用途gate，成對回復相容程式再正常生成，展示回退使用新共同版本，不回推舊資料或恢復退役工作。

本輪無需再修改I01／I02產品程式。其餘已接受限制與T01～T06保持；本案不自動開下一個案件。

完整證據：Downloads `ai-news-radar-i04-release-20261024/` 的SEAL／MANIFEST、RELEASE、BACKEND_CI／FRONTEND_CI、REFRESH_COMMIT、HTTP_BACKEND／HTTP_FINAL／HTTP_ASSETS、BROWSER_LIVE、RETIRED_WORKFLOWS與CANONICAL_BACKUP。

後續日常維護建議 **GPT-6.1 Sol／Medium**；需要修程式時High。
