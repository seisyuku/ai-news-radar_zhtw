# I04：D+正式發布與線上驗收

狀態：發布進行中，使用者已指定驗收後提交並推送GitHub；正式前端尚未切換，待同代資料及線上驗收。

## 已完成檢查

- 核對I03封存24份候選，隔離發布副本從最新master開始，保留9筆data／item bot提交。
- 後端提交`1fbc429cfdfbc9d6973866f26987997d2c162182`採I01封存八檔，本機完整2,245項通過；正常推送master，未force。
- GitHub離線CI `40106843717`及Pages `40106843397`成功。前端副本完整2,304項通過，24份實作仍與I03一致，另同步中英文README。
- 依I03順序等既有正常刷新取得schema2，核正式HTTP同代、選集、state revision及舊phase時鐘後才推前端。無新增排程、來源、provider或觀察工作。

## 待完成

正常新版刷新與資料commit、HTTP後端核對、前端提交／CI／Pages、HTTP資產與真Chrome桌面／手機、發布後紀錄及canonical同步。完成前不宣稱正式新版已驗收。

完整證據在Downloads `ai-news-radar-i04-release-20261024/`。原I01～I03封存保留；不公開歷史新聞文本或真新聞截圖，independent_precision保持not_evaluable。
