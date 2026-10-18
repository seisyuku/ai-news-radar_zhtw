# Radar 來源修正工作入口（2026-10-18）

## 本對話的範圍

使用者指定本對話聚焦完成已部署 Radar 應有的來源架構修正。
日報選題研究另開對話，入口為
[日報選題研究交接](DIGEST_EDITORIAL_HANDOFF_20261018.md)。

Radar 維持 README 的 AI 產業商業事件產品邊界、靜態發布與既有刷新架構。
來源可信度、收件範圍、入口可用性分別判斷；不以 RSS 200、文章數量、
關鍵字命中率或沒有重複，直接認定新聞事實正確率。

## 已完成且已部署程式

- 依使用者明確裁決，移除 VentureBeat AI、Artificial Intelligence News、
  LMArena Blog 的三個固定 RSS 註冊與其 AI 信任捷徑，不投入替代抓法。
- [移除提交](https://github.com/seisyuku/ai-news-radar_zhtw/commit/a4c85b2f3d9a)
  已推送 master；[GitHub CI](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39131377116)
  成功。本機完整 1140 項通過；離線收件驗證剩餘十一個來源健康輸出。
- 既有 archive、resolver 與歷史發布者識別保留；不回寫舊新聞、不改使用者
  OPML、不改日報選題。公開健康資料是否已移除三列，待自然刷新觀察；
  離線合成 `source-status.json` 不是正式線上驗收證據。
- 電腦王阿達明確排除，不因公開 RSS 可讀而重新推薦。

## 來源調整與重審狀態

已整理為[具體修改規格與任務切分](RADAR_SOURCE_CHANGE_PLAN_20261018.md)。
使用者已確認平台停運納入市佔格局的市場退出事件，並授權開始程式實作。
INSIDE、RuntimeWire 與共享平台事件規則已實作並推送，驗證／自然刷新狀態
見主交接。下表保留研究依據，具體預設值與本批範圍以新規格為準。
使用者另澄清：繁中媒體可能只稱雲端平台／雲端部署，不能以無 AI 字樣或
不在既知品牌名單拒收；新規格已有服務類型／用途加重大事件的獨立路徑。
另已確認：排除一般個人相簿與雲端硬碟訂閱，價格／資料存取權限變更嚴格
認定、避免行銷文；臨時中斷須連續超過 72 小時，永久停運公告可直接收錄。

下表是待收斂、審核的修改方向，不代表使用者已逐項批准接入或升降權重。

| 項目 | 現有依據 | 下一步／限制 |
| --- | --- | --- |
| INSIDE 限量准入 | 原生 RSS 實測含 10/17 Zeabur 停運新聞；舊 AI 標題條件會擋該標題。 | 已實作並推送來源與共享平台事件條件、下游 AI 閘門；不接全站所有雲端／教學文章。 |
| RuntimeWire 目錄與新聞分流 | 近 21 日保留 242 筆中，206 為 `/models/`，36 為 `/article/`。 | 已實作並推送目錄不收、文章維持現級與有限平台事件准入；沒有另建目錄查漏路線。 |
| Reuters、CNBC、The Information 的發布者分級 | 後台目前繼承 `ai_media` rank 2，前台為專業媒體。 | 依發布者重審；Google News 是運輸入口，不代表全部結果都能一起加權。尚無新一輪全文正確率驗收。 |
| Cloudflare、Modular、Zed 舊候選 | 9/23 曾因一般工程／工具內容與篩選成本暫不准入。 | 只做有界的新樣本審查，不自動啟用全站。 |
| 來源文件狀態同步 | Mistral、MCP Blog、ARC Prize 已有接入提交及正式任務，舊段落仍寫尚未部署。 | 已同步過期文字，沒有重複接入。 |

## 維持既有決定

- iThome、The Decoder 維持已升級層級；科技新報沒有新的降級依據。
- 數位時代維持觀察層級；近 21 日 216 筆同源折疊剩 160，原始重複不等於
  讀者最終看到的重複，也不等於媒體內容失信。
- 36Kr 維持觀察與每輪／讀者上限五；528 筆折疊剩 360，尚不升級。
- LLM Rumors、LLM Stats、橘鴉維持原定位；AIBASE 維持既有聚合呈現，
  不因本輪討論偷偷更改後台權重。
- YunNEWS、TheAI學院、AIReiter、Look AI、Array 維持人工查漏裁決。
- LM Studio、Google Antigravity 及其他舊候選，不因新範圍自動准入。
- Free LLM APIs 有獨立持續故障，是感測器議題；未因本輪新聞來源移除而修改。

## 證據與接續方式

- GitHub 來源治理：`docs/SOURCE_COVERAGE.md`。
- 私人來源審查：`/Users/lordmi/Downloads/ai-news-radar-source-architecture-review-20261018/REPORT.md`。
- 三來源移除交接：`/Users/lordmi/Downloads/ai-news-radar-source-removal-20261018/HANDOFF.md`。
- 媒體入口探測：`/Users/lordmi/Downloads/ai-news-radar-media-coverage-research-20261018/`。

研究中的內容統計來自 10/18 20:35 臺北的 GitHub archive；健康資料取自 21:05，
不混稱同一輪生成。只代表保留且已收錄的資料，未評估所有媒體全文。

接續處理本批發布／自然刷新驗收，狀態以主交接為準。
不要重新投入已決定移除的三個入口、重做全部來源、增加新的服務，或在這串
改日報讀者定位、權重與編輯策略。不要反覆做提交碼查驗。
