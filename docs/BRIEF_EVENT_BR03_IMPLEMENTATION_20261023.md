# BR03：Brief事件後端實作與回歸

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：階段歷史／已結案。** BR01～BR06已正式發布；舊階段下一步不續跑。技術契約、驗收限制與回復依[BR06](BRIEF_EVENT_BR06_RELEASE_20261023.md)及最新操作文件使用，不重開本輪已接受的去重限制。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

狀態：完成本機後端候選；依使用者自動續行授權接BR04～BR06。正式推送留待前端與發布前複核通過。

`scripts/brief_events.py`新增無provider的事件匹配／phase／有限狀態；`update_news.py`沿用原importance係數與發布者解析器接入，產生自足`brief_events`、相容daily適配器及`brief-event-state.json`。普通stories、文章時間、一般列表與來源選擇保持；只有事件importance使用事件時間及當期phase票數。公開校驗碼在既有資料清理後計算，避免清理後的JSON與hash不符。

模型完整型號與動作分開；參數數值正規化、同網址跨入口、同CVE批次、明確觀察與修補／地區擴大等phase均有回歸。弱脈絡附件不能擴展anchor；風險、否定、PoC與未知發布者不授予實質更新。支援的有界規則之外維持unresolved，沒有全語意改寫去重保證。

既有workflow只加輸入state Git blob捕捉及重試前遠端比較；遠端已更新就停止重試，不讓`-X theirs`覆蓋新記憶。缺檔使用`--verify`，避免Git把未解析路徑印進多行環境值。原排程／concurrency及退役workflow不變。

## 實作澄清

- 未知單例的canonical URL用SHA256作有界subject，保持精確URL身份且避免長Google News網址突破identity容量；不是按題目猜測。
- `record_builder`／`ranker`為注入的純adapter，係數仍由原生成器擁有，避免循環import及複製評分規則。
- 同phase主文保留於有界evidence IDs首位；優先現行stories內有資格的phase成員，避免以archive繞過來源限額。僅相同代表稿可沿用既有生成摘要，不增加模型呼叫。
- 額外公開`effective_basis`／`effective_reported_day`供BR04標示日期不明；屬v1允許的附加欄位，不改凍結schema必填介面。date-only上界不冒充精確發生時刻。
- 明確不同scope的擴大可保留多個同kind phase；同條件重述仍沿用原時間。修補只有已知未修補→已可用才作更新，同一披露已包含的修補不多造phase。

## 已驗證

完整Python **1,586項通過**；新增52項行為／本機Git競爭回歸。py_compile、actionlint與git diff --check通過。首次完整套件缺Node runtime的41項環境失敗，補入既有Node路徑後重跑，沒有為環境錯誤改產品行為。

BR01五個固定窗口都通過公開schema及相同asof的狀態／事件重跑一致；原普通AI ID、stories與輸入未變。當期179故事→172事件根、171個在有效窗口；PHP六篇指定披露及保留的相關引用共用一根，首次報導實際攻擊觀察仍保留。內部brief數量11→11不代表讀者卡片完全不變，前端下一階段核對。

固定7,427列archive的當期處理約0.4秒；state **163,904 bytes**、事件投影約**954 KB**，各低於8MiB上限。五窗口state約86～179KB、處理約0.23～0.4秒；單機離線測量不是Actions SLA或來源穩定性驗收。

候選與REPORT／BACKEND_REPLAY／CHECKPOINT／HANDOFF／MANIFEST在Downloads `ai-news-radar-brief-event-br03-20261023/`。sealed含保護資料，只做機械讀取；BR02替代13群73篇仍未展開或調參。來源／schema契約之外的未知保留，沒有獨立品質通過宣稱。

**下一步BR04：GPT-6.1 Sol／High**，接入前端所有brief路徑、盲標候選、十四日離線與Chrome桌面／手機驗證；依使用者指示自動接續。
