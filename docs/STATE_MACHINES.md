# 狀態機與恢復契約

生成器、瀏覽器與 Actions 各自擁有狀態。這裡記錄跨操作會被沿用的資料、由誰更新，以及如何恢復。資料欄位以既有 [事件 schema](contracts/brief-events-v1.schema.json)、[治理 schema](contracts/publisher-governance-v2.schema.json) 和各領域契約為準。分數、主題、來源資格與精選候選是當輪投影結果。

## 生成、發布與讀回

| 觸發 | 下一步 | 保留與恢復 |
| --- | --- | --- |
| 開始生成 | `update_news.main` 讀前一輪檔案，固定本輪時鐘與發布者政策修訂，再收件、投影、寫入。 | archive 缺失可初始化；既有 archive 損壞時停止。各快取與事件歷史依下表個別恢復。 |
| 生成有效事件歷史 | 先寫 archive 和一般列表，再寫事件歷史、合併投影與 daily brief，最後完成 resolver、其他公開資料、快取及來源狀態。 | 每檔以同目錄暫存檔替換。檔案群可能暫時混代，讀者端驗證治理版本。 |
| 事件歷史寫入失敗 | 保留舊歷史，輸出 `state_write_failed`。當輪一般新聞和價格照常發布，重點與雷達不可用。來源狀態使用降級後的選稿診斷。 | 當輪保留舊 JSON／HTML resolver。下一輪成功完成相關寫入後，按當輪 archive 清理。 |
| 事件產生不可用投影，且未嘗試寫事件歷史 | 繼續一般新聞及價格，發布不可用投影。 | 此分支沿用既有清理規則。不可用投影本身不等於寫檔失敗。 |
| 其他未處理的寫入錯誤 | 中止生成，保留已替換的完整檔案；尚未執行舊 resolver 清理。 | 已替換的檔案由下一輪生成接續。工作流在生成失敗時不進入提交。 |
| 生成完成 | 完成來源狀態寫入後，按 archive 清理過期 JSON／HTML resolver。Actions 有差異才提交、推送。 | 清理本身逐檔執行。推送失敗可 rebase，前提是遠端事件歷史 blob 仍等於生成前讀到的 blob；最多推送三次。blob 已變則停止，交由下一次正常刷新。 |
| 頁面取得資料 | 相符的治理修訂與 generation 可顯示重點／雷達。混代、衝突、明示不可用時拒收治理區塊。 | 一般新聞保持可讀。修正或回退依 [OPERATIONS](OPERATIONS.md) 保留當前歷史，以正常刷新重建相容資料，讀回核對 Pages 資產與公開 JSON。 |

實作入口為 [生成器](../scripts/update_news.py)、[單檔替換及 resolver](../scripts/archive_output.py)、[發布 workflow](../.github/workflows/update-news.yml) 與 [讀者守門](../assets/publisher-governance.js)。故障驗收見 [寫檔與清理](../tests/test_atomic_output.py)、[跨層投影](../tests/test_signal_integration.py) 與 [Git 歷史守門](../tests/test_brief_state_guard.py)。

## 跨輪資料

| 狀態與負責模組 | 轉移、保留與恢復 | 驗收 |
| --- | --- | --- |
| **新聞封存** · `archive.json` · [生成器](../scripts/update_news.py) | 首見建立 ID 與初見時間，再見更新最後見到時間。預設依最後見到時間保留 21 天。舊不合格證據可留存但退出閱讀投影。官方文件補收成功後，archive URL 使後續輪次跳過已收錄文件。 | [封存與清理](../tests/test_atomic_output.py) |
| **文章版本與 AIBASE** · archive 紀錄 · [版本模組](../scripts/article_versions.py)、[AIBASE](../scripts/aibase_source.py) | 同 ID 內容修訂保留最多 16 份舊內容。符合修訂條件的同 URL 文章在投影中指向新版，舊 ID 仍可解析。AIBASE 沿用既有 Radar ID，英文只補未取得繁中的欄位。 | [AIBASE 封存](../tests/test_aibase_archive.py) |
| **事件身分、階段與恢復** · `brief-event-state.json` · [事件模組](../scripts/brief_events.py) | 新證據可補入既有事件、合併別名或形成新階段。重述同一階段不延後其有效時間；實質新階段才可能重開 24 小時讀者窗口。歷史保留 21 天。有效狀態續用，缺失或損壞且 archive 具足夠證據才重建；不支援版本、未來異常、容量或證據不足時輸出不可用。 | [事件回歸](../tests/test_brief_events.py) |
| **來源健康** · `source-status.json` · [健康模組](../scripts/source_health.py) | 依來源及其子來源身分延續。成功清零，失敗累加，預設第 3 次進入持續故障；跳過保留最後實際結果與連敗，不重發故障紀錄。舊格式只用既有連敗、成功時間或 `ok` 補足上次結果。 | [健康契約](SOURCE_HEALTH.md) · [跳過回歸](../tests/test_source_health_skips.py) |
| **價格基線與訊號** · `market-sensor-state.json`、`market-signals.json` · [價格模組](../scripts/market_sensors.py) | 首次成功建立基線；後續成功才比對並前進。失敗或基線資料量跌破安全門檻時沿用舊基線。已偵測的價格訊號保留 24 小時。 | [價格回歸](../tests/test_market_sensors.py) |
| **讀者翻譯** · `title-zh-cache.json`、`translation-state.json` · [生成器](../scripts/update_news.py) | 通過驗證存正快取；內容拒絕保留 6 小時，供應商不可用保留 30 分鐘。標題有一次有界修復，若本輪未送出，可在條件滿足時補做。429 依 `Retry-After` 與剩餘預算決定，限流本身不留下拒絕項。 | [翻譯恢復](../tests/test_reader_translation_recovery.py) |
| **Groq 摘要** · `ai-summary-cache.json` · [摘要模組](../scripts/news_summaries.py) | 正快取重驗後可使用；適用的驗證錯誤修復一次，特定拒絕 6 小時後到期。供應商 JSON 模式的格式重試仍屬同一供應商。 | [摘要回歸](../tests/test_news_summaries.py) |
| **導言快取** · `reader-excerpt-cache.json` · [導言模組](../scripts/reader_excerpts.py) | 符合條件才命中舊導言或在本輪預算內擷取。只保存當輪用到的導言，失敗可於後續符合條件時再試。 | [讀者補讀回歸](../tests/test_reader_translation_gaps.py) |

## 頁面生命週期

| 狀態與負責模組 | 轉移與邊界 |
| --- | --- |
| **主快照與輔助請求** · [載入模組](../assets/loader.js)、[app](../assets/app.js) | 主快照成功後渲染清單，五份輔助資料各自完成或失敗。請求逾時會取消；單一輔助檔失敗由各區塊處理。 |
| **閱讀模式、全量請求及清單** · [app](../assets/app.js) | 精選、全部 AI、全部收錄各自套用現行篩選。首次全量請求共用同一 Promise，失敗清 Promise，重點擊可再試。僅當仍在全量模式且請求編號相符，回應才可改畫面。載入中和錯誤提示與清單走同一渲染入口，任何新渲染都會使舊動畫影格失效。 |
| **治理版本與頁內快取** · [治理模組](../assets/publisher-governance.js) | 保存見過的最新時間與政策修訂；同一時間不同修訂會保持衝突，直到出現更新時間。通過同代檢查才採用或更新快取；相容快取僅在新投影缺席時沿用有效主要精選。有效零則與資料不可用分開處理。 |
| **重點與模型到期** · [app](../assets/app.js) | 重點排序可在重要性與時間線切換；候選不足時切時間線。時效由計時器及分頁恢復可見時重算。陳舊快照橫幅在首頁載入時判斷。 |
| **局部介面** · [app](../assets/app.js)、[動效](../assets/motion.js)、[首頁](../index.html) | 清除篩選重設查詢、分區及展開，保留閱讀模式。局部發布者及文章的展開隨 DOM 重建歸零；原生面板由 `details` 持有。複製按鈕成功或失敗後重設，動效以頁面事件、動畫完成與解除觀察結束。 |

驗收使用 [載入與競態](../tests/test_frontend_loader.py)、[版本不相容](../tests/test_publisher_governance_ui.py) 和 [空白候補](../tests/test_empty_fallback_ui.py)。資產變更沿用 [共同版本檢查](../tests/test_asset_versions.py)。

## 排程、短期狀態與獨立入口

| 範圍 | 所有者與邊界 |
| --- | --- |
| **定時刷新與補跑** | [Heartbeat](../.github/workflows/update-news.yml) 查最近成功 run，未滿 25 分鐘跳過；[watchdog](../.github/workflows/watchdog.yml) 查最近排程 run，超過 90 分鐘代觸發，沒有歷史時跳過本次。 |
| **單輪或程序內部** | [生成器](../scripts/update_news.py) 的 HTTP 退避、生成階段紀錄、轉換器延遲初始化及失敗旗標；[摘要模組](../scripts/news_summaries.py) 的轉換器旗標；[政策模組](../scripts/publisher_policy.py) 的每輪固定修訂與按內容快取。這些狀態不新增跨輪檔案。 |
| **臺灣來源觀察與探測** | 觀察計畫停用。[觀察決策](../scripts/tw_source_observation.py) 由 [run 與 artifacts](../scripts/tw_source_actions.py) 還原未認領、意圖、進行中、完成或結果未知；主採不完整才可能補採。[探測器](../scripts/evaluate_tw_source_admission.py) 在單次 client 保留 robots 結果、抓取節奏和停止主機名單。 |
| **觀察報告、SMTP 與結案** | [報告帳本](../scripts/tw_source_reporting.py) 先封存內容和意圖，再由 [SMTP 階段](../scripts/tw_source_email.py) 產生接受、未接受或未知收據。只有確定未接受且可重試才重送；結案需驗證結案包與對應的接受收據。[一次性驗收](../.github/workflows/tw-source-mail-check.yml) 的既有意圖及未知結果會阻止再次驗收寄送。 |
| **私人校稿與手動工具** | [私人校稿前端](../private_preview/preview.js) 的草稿、版本衝突與讀回屬歷史介面。Gemini 診斷、工作結果通知與 free-tier 比較維持獨立入口。舊 `paid-source-state.json` 保留於歷史資料，公開生成器不讀寫。 |

## 變更驗收

先使用固定的公開快照、時間及模擬回應做至少兩輪離線比較。比較 ID、事件時間、來源資格、排序、各 JSON 內容和 resolver，排除實測耗時等非決定性欄位。重跑、亂序與部分寫入用現有測試入口補對應情境。共享生成及發布行為改動時，執行完整 Python 測試、JS 語法與資產版本檢查。發布與回退依 [OPERATIONS](OPERATIONS.md)，由正常刷新產出正式資料。
