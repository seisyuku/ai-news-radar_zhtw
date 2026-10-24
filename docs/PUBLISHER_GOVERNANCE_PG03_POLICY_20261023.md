# PG03：來源分級與有範圍准入（2026-10-23）

**PG03本機候選完成；下一步PG04：GPT-6.1 Sol／High。** 未提交、推送或部署；完整首頁資格投影與用途選稿仍待PG04。本階段接續[PG02身分鏈](PUBLISHER_GOVERNANCE_PG02_IMPLEMENTATION_20261023.md)，遵守[PG01契約](PUBLISHER_GOVERNANCE_PG01_CONTRACT_20261023.md)。

## 政策與實作

[config/publisher-policy.json](../config/publisher-policy.json)是唯一准入表，包含41個明確host／path範圍：31個limited、10個unreviewed。另記39個既有新聞入口、OPML池與橘鴉人工對照入口、8個封存候選及原sensor清冊；這些清冊不產生collector或准入，free-tier維持退役。

`scripts/publisher_policy.py`驗證版本、canonical SHA256 revision、唯一scope、精確host／路徑與權限。不同子網域不自動繼承；路徑依segment邊界取最具體規則，拒絕userinfo、非標準port與模糊編碼／dot路徑。Google必須具已配置路由的RSS發布者證據，query名稱、標題尾綴或來源首頁不代替子站／路徑證據。沒有足夠範圍證據的舊橋接稿保持未審。

每次公開輸出重建PG02身分並依目前registry重算 `source_policy`，不信任archive裡的過期許可。一次main刷新固定同一registry revision，下次刷新重新讀取；不在同次輸出拼接不同政策。registry內容改動即換revision；版本／雜湊／範圍無效即在刷新開始前拒絕載入，不能沿用舊grant。私人OPML標籤仍無權威，已知公開文章host可取得和其他入口相同的有範圍政策。

已核既有裁決保留：iThome／The Decoder rank1、數位時代主站／RuntimeWire rank4、Reuters／CNBC／The Information rank2；MCP／Mistral按PG02更正保留實際official／rank0。OpenAI Skills只允許確切GitHub路徑，Codex changelog補列既有adapter的確切developers.openai.com路徑；不把任意GitHub或OpenAI子網域整批放行。

八家新見媒體（Latin Times、Android Headlines、AI Insider、New York Post、Wccftech、FEDagent、SCMP、Computing UK）維持unreviewed：watchlist／rank6，一般列表仍須通過文章及時效規則，精選／雷達預設false。沒有新增canonical身分、正向計票鍵或整站品質通過結論。Meet／未來商務同樣獨立未審。

LLM Stats保留模型追蹤與雷達許可，不取得一般精選許可；36Kr／LLM Rumors保留原有限用途，橘鴉只作人工對照。AIBASE／36Kr／橘鴉仍受原 `cn_aggregator` 一票限制。

## 輸出與讀者行為

來源政策傳至archive／resolver、latest／all-mode、普通故事、事件refs／primary、daily相容投影、模型發布與雷達。一般列表套effective tier並移除allow_general=false的範圍；archive及解析頁保留原文、ID、URL與歷史tier，另附目前政策。事件的完整引用也保留。

新tier只在公開輸出副本套用。事件配對、同源選版、原主文、分數、選集、state及時效仍使用既有輸入；政策annotation加入後重算公開brief generation_id，state revision不變。普通故事與daily也在原選稿後附政策。這是刻意保留的階段邊界，**PG03尚未以allow_featured／allow_radar產生新首頁選集**。

前端消費後端政策分組，未審不再以父層入口宣稱專業／官方；一般卡片顯示「未審來源」，故事計數提示「含未審來源」。發布者名稱、現有票數及CNBC單枚徽章保持。舊JSON有相容顯示，資產版本為 `20261023-pg03`；此fallback不是PG04未來的資格fallback。

## 驗證與影響

- 完整 **1,727項** 回歸通過；Python編譯、JavaScript語法與diff檢查通過。
- 五組同claim／state／asof成對歷史重播，事件根172／168／121／92／190；state完全一致，除新增政策／公開tier及generation_id外投影一致，原分數、成員、phase、主文、時間與daily選集不變。
- 11:35臺北固定PG02顯示fixture：195篇中1篇橘鴉人工對照稿退出一般列表，仍可在archive／resolver追溯；其餘194篇為152 limited／42 unreviewed。42篇tier annotation變更中，37篇rank改為6、5篇僅更新未審標示。包括8篇新見Google媒體，以及無法核對範圍的舊橋接／OPML／子站；沒有文章ID或內容改寫。
- 原TechNews主站規則不自動延伸至finance／infosecu子站，固定快照11篇因此未審；Wired的已知身分／票數也不代表OPML整站品質已准入。這些稿仍在一般列表，未判為低品質或刪站。
- 7,466個archive輸出副本的publisher／ingress／source_policy通過凍結schema components；215筆以封存RSS精確URL配對。來源健康檔位元組不變，固定快照16個site、0失敗；離線producer另驗收source-status，沒有重新測試即時端點穩定性。
- 真Chrome 1440／390，PG02基線、PG03候選、候選讀舊資料共6contexts／12views通過。預設熱點／時間線事件ID順序不變、CNBC一枚、名稱搜尋與未審標示正常，無JS錯誤或橫向溢位。

固定顯示fixture沿用11:35公開JSON與09:35精確RSS證據，沒有混用不同代local state；producer／state另由歷史成對重播及合成離線main測試驗證。後者驗禁止範圍離開一般列表但保留archive／resolver，來源健康不受政策影響。舊72保護ID、448預留ID、6個CN家族隔離不變；只做機械比較，不讀保護內容。independent precision維持not_evaluable。

逐筆tier變更／一般列表移除理由、測試log、瀏覽器結果、精確階段patch及完整交接封存在Downloads `ai-news-radar-publisher-governance-pg03-20261023/`。原PG01／PG02封存只讀，未新增觀察、日報、Email、排程、來源抓取、逐篇跳轉或LLM請求。

## PG04交接

先驗PG03 MANIFEST／HANDOFF，再依凍結契約產生stories頂層 `publisher_governance`。以本階段source_policy核一般／精選／雷達用途，加入當期合格來源、核心材料、合格計數及用途主文／分數；不得拿原事件score或未審引用冒充新資格。

PG04須一併套模型雷達／model_releases_24h用途許可，修正只按ingress site_id作官方標籤的舊捷徑；不能因PG03已攜帶allow_radar就誤認雷達gate已生效。維持LLM Stats原模型allowlist及追蹤標示。daily須和最終同政策選集／meta一致，再綁完整治理投影；根、phase與state仍不變。

缺／錯版／跨代投影保守停用精選，普通列表仍可用；完整混版、到期、回復與14日影響驗收依序接PG04／PG05。PG03沒有獨立品質通過結論，PG04不得把identified或limited直接視為核心事件證據。
