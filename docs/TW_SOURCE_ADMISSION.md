# 台灣媒體來源准入影子測試

<!-- task-ledger-history: v1 -->
> **2026-10-24狀態：該批候選已封存／工具參考。** 此批五站與其餘三候選共八站已not_admitted_closed，沒有准入或持續觀察待辦。工具可供另案明確指定使用，本頁命令不構成本次live重測授權。見[A03裁決](SOURCE_GOVERNANCE_A03_DECISIONS_20261022.md)及[A06結案](SOURCE_GOVERNANCE_A06_RELEASE_20261022.md)。
> 現行任務見[TASK_LEDGER](TASK_LEDGER.md)，方向見[ROADMAP](ROADMAP.md)。
<!-- /task-ledger-history -->

本輪僅建立可移除的維護者工具，五站仍未正式准入。工具不被
`update_news.py` 匯入，不寫公開新聞池、來源健康、排名或私人日報，
沒有排程、LLM、憑證、付費 API 或新依賴。

## 執行與重播

在 repo 根目錄使用既有 Python 環境：

```bash
.venv/bin/python scripts/evaluate_tw_source_admission.py \
  --live --baseline data/archive.json --lookback-days 7 \
  --output-dir /Users/lordmi/Downloads/ai-news-radar-tw-source-admission-20261021/new-capture
```

只有明示 `--live` 才連網；五站固定 host 清單不開放任意 URL。
每站讀 robots、首頁、至多一頁官方 RSS 目錄及六個候選 feed；每個
feed 最多留 50 筆。非官方 host 的轉址不跟隨，401/403/429 停止該站，
robots 不可確認就不抓內容。robots 404/410 視為未宣告規則；尊重
crawl-delay/request-rate，超過 30 秒要求另作人工安排。每次請求間隔
至少一秒、連線／讀取 timeout 8/12 秒、單次回應最多 2 MB、最多四跳，
無重試、全文讀頁或翻頁。禁用環境 `.netrc` 認證。

輸出必須在 repo 外，連同指向 repo 的 symlink 也會拒絕。依本機政策
使用 Downloads。每次請用新的子目錄，保留之前採樣：

- `capture.json`：原生 feed 的標題、連結、發布時間、最多 800 字短摘要，
  HTTP 狀態、每跳 URL、content type、回應 hash、耗時、探測方法及解析狀態。
- `baseline.json`：當次唯讀比較池的副本，避免後續自然刷新使重播失真。
- `report.json`、`REPORT.md`：篩選、逐篇比對、待查連結、欄位具備數及成本。

不保存首頁全文、文章全文、`content:encoded` 或 Atom `content`；
原生摘要可能截斷，不自行補全文。回應 hash 是原 HTTP body 的 hash，
不是所保留短摘要的 hash。離線重播重做篩選／比較，不假裝重新驗證網路：

```bash
.venv/bin/python scripts/evaluate_tw_source_admission.py \
  --replay /Users/lordmi/Downloads/ai-news-radar-tw-source-admission-20261021/probe-2/capture.json \
  --baseline /Users/lordmi/Downloads/ai-news-radar-tw-source-admission-20261021/probe-2/baseline.json \
  --output-dir /Users/lordmi/Downloads/ai-news-radar-tw-source-admission-20261021/replay
```

採樣中的 `canonical_url` 是移除追蹤參數／片段的 feed alternate link；
`canonical_method=feed_alternate_link_unverified` 明示沒有讀頁驗證 HTML
canonical。保留原 feed URL、時間原文與 entry index，不將 updated
當 published，不以抓取時間補缺失或無時區的日期。

## 判定與分母

這是獨立、保守、待驗證的篩選假說，不改正式 AI relevance。先排除
彙整、教學、常青指南、硬體開箱、明示廣編／新聞稿及未定案提議／預測，
再查 AI 關聯與已發生事件線索。過關僅代表 `candidate_requires_review`，
不證明原創、事實正確、獨立證據或可發布。產品宣傳與教學式實測仍可能誤入，
短摘要不足也可能漏收，逐篇保留原因供修正假說。

- `fetched_articles`：具標題、有效 HTTP(S) 連結、帶時區發布日期的文章數；
  不等於觀察窗內文章數。重複 entry 只在候選階段去重。
- `candidate_articles`：觀察窗內、篩選通過並排除 feed 內相同 URL 後的篇數。
  超過觀察時點的文章排除；下界包含，最多回看 30 日。
- `duplicate_url_count`：候選與基準池 URL 相同的篇數，僅去追蹤參數。
  不移除 DIGITIMES 的 `id` 等有意義 query。
- `matches`：最多三個不同基準 URL 的疑似事件。以三日時間差、標題字元
  相似度，或共享產品／實體及事件類型提出線索；中英報導可配對。相同產品
  不同版本、事件、角度仍需複核，沒有配對也不等於新增。
- `duplicate_event_count`、`novel_event_count`：僅計已裁決的獨立 `event_id`；
  相同事件多篇不重計。`new_evidence_count` 是經裁決的新增證據文章數。
- `false_positive_count`：人工確認的候選誤收數，分母為
  `reviewed_articles`；無人工樣本為 `null`，不寫成零誤收率。
- `metadata_quality`：所有採樣 entries 為分母，列四欄具備數。零樣本
  不推論 100% 完整。`feed_reliability` 是當次解析結果計數，不是長期可用率。
- `cost_and_risk`：實際 HTTP 跳數、操作數、等待／解析前讀取耗時、無重試與
  零文章請求。不將 robots 內嵌在首頁操作的耗時重複相加。

### 人工裁決檔

`--reviews /absolute/path/reviews.json` 可重播明確裁決，例如以下為
**合成示例**，不是本輪量測結果：

```json
[
  {
    "canonical_url": "https://candidate.example/independent-test",
    "decision": "new_evidence",
    "baseline_url": "https://official.example/model-release",
    "reason": "同一發布事件；已查核此稿另附原始測試資料，而非轉述官方成績。"
  }
]
```

另可用 `duplicate_event`、`novel_event`、`false_positive`；前兩者須提供
`event_id`，同事件／新證據須引用基準池實際 URL，所有裁決必須有理由。
不能把同 URL 算新證據；重複或不在當次候選池的裁決會報錯，避免誤用舊檔。

確認新事件還需 `--baseline-start ... --baseline-end ...`，兩者均帶時區，
表示操作者已核查基準池在此期間的完整性。工具不從最早／最晚一篇自行
推論完整覆蓋，不把七天候選與 24h 最新池比較就宣稱漏報。基準缺失、
過濾遺漏與無收件時間仍須人工查證。未給時窗時可找 URL 與事件線索，
但沒有配對一律標 `baseline_window_unverified`，禁止裁決為新事件。

Meet 固定標 `publisher_group=bnext_media`，與數位時代同出版群組；工具
沒有任何 corroboration 加分功能，也不因不同網域或作者斷定獨立性。

## 2026-10-21 初步證據與逐站建議

兩次有限探測於臺北約 01:18、01:21 開始；正式比較池版本為
`2026-10-20T17:05:30.908253Z`，archive 有 7,465 筆。最後報告使用第二次
採樣 `2026-10-20T17:21:51.014602Z` 離線重播，候選窗口七天，但 feed 實際
僅涵蓋 10/16～10/21，**沒有七天連續觀察，也未核實 archive 全窗完整性**。
兩次接近時間的成功不代表 Actions 可用率或長期可靠。

| 來源 | 入口及結果 | 有效文章／候選 | 欄位品質 | 第二次 HTTP 請求 | 本輪建議 |
| --- | --- | --- | --- | ---: | --- |
| 資安人 | 首頁 200；`/rss.xml` 200 HTML、`/rss.aspx` 轉 error.htm，皆非 XML | 0／0 | 無可用 feed 樣本 | 6 | 暫緩；本輪未找到可用 feed，先取得站方穩定入口，不開發爬蟲。 |
| CyberQ | `https://cyberq.tw/feed/` 200 RSS；慣例路徑探測，非首頁宣告 | 10／5 | 四欄各 10/10 | 3 | 優先續做影子觀察；實測可能補證據，教學／彙整密度需長窗量測。 |
| 網管人 | `https://www.netadmin.com.tw/feed/` 200 RSS；慣例路徑探測 | 10／3 | 四欄各 10/10 | 3 | 暫維持影子；本次候選偏廠商產品稿，獨立事件收益未證實。 |
| DIGITIMES | 官網 RSS 目錄連到 `https://www.digitimes.com.tw/tech/rss/xml/xmlrss_10_0.xml`，200 XML | 30／4 | 四欄各 30/30 | 4 | 僅續驗公開 RSS 短摘要；付費原文與授權未解，不繞付費牆。 |
| Meet | 官方內容站 `https://meet.bnext.com.tw/` 302 到另一 host 的 `/cm/gcfs`，工具停止跟隨 | 0／0 | 未取得文章／feed | 2 | 受限未確認；不繞轉接、不開額外 adapter，先釐清官方可用 feed。 |

資安人兩個路徑是有限慣例探測，不能據此斷言全站沒有 RSS。
Meet 的內容網域與同集團關係由
[巨思官方介紹](https://www.bnextmedia.com.tw/meet/index.html)確認；轉址目的為
`sn-myalb.bnextmedia.com.tw`。未把轉址解讀為帳號登入要求或永久封鎖。
DIGITIMES 的
[官方 RSS 目錄](https://www.digitimes.com.tw/tech/rss/rss.asp)存在多種訂閱入口，
本輪只採第一個有效綜合 feed，沒有窮盡分類 feed 或做歷史 backfill。
其 robots 對 GPTBot 另有全站禁止；工具以使用者委託的來源閱讀用途與
明示 RadarSourceAdmission UA 讀公開 RSS，不用作模型訓練。
所有 robots／RSS 可讀性均不等於重製授權，原始摘要保留在本機，不上傳 repo。

當次 50 篇有效樣本有 12 篇候選，與基準池相同 URL 為 0。
CyberQ 4 篇、網管人 1 篇、DIGITIMES 1 篇有疑似事件線索；其餘也不能直接
當新事件。沒有人工裁決樣本，所以已確認同事件／新事件／新證據均為
0，意義是**尚無確認數**，不是實測零重疊或零新增；誤收率未知。
尚未給正式 tier 或每輪配額；應在 7～14 日對齊資料及人工抽核後另作准入裁決。

可抽核的例子：

- CyberQ 的 [OpenCode／Zeabur 對照](https://cyberq.tw/2026/10/18/hackers-target-ai-agent-opencode/)
  取得候選資格，已有 [INSIDE 同一入侵線索](https://www.inside.com.tw/article/42669-opencode-console-breach-1-4-percent-distillation-attack-provider-keys)
  及 [iThome 報導](https://www.ithome.com.tw/news/179796)；不能因稿件比較兩家公司就稱兩個新事件。
- CyberQ 的 [DeepSeek 雙機實測](https://cyberq.tw/2026/10/18/deepseek-v41-flash-1017-dual-machine-dgx/)
  可列新增證據待查；基準已有模型發現紀錄，但需另核方法與原始資料，
  不把標題有「實測」自動算原創。
- [求職流程文章](https://cyberq.tw/2026/10/20/ai-job-search/)以使用教學排除，
  產業精選整期彙整亦排除，不拆成多則。
- 網管人的 [Sophos 產品稿](https://www.netadmin.com.tw/3496/)因摘要有產品推出
  通過初篩，但不代表獨立採訪或已發生事故；這是應優先抽核的宣傳誤收風險。
- DIGITIMES 的 [ChatGPT 廣告業務稿](https://www.digitimes.com.tw/tech/dt/n/shwnws.asp?id=0000771788_C5K8DI9O7XDBR49H1Q6TR)
  是商業事件候選，已有 AIbase 相關標題；摘要不足以確認哪一項新數據獨立新增。

P2 僅列候選：EE Times Taiwan、TechOrange、Cool3c、TechNice，
本輪不探測／開發。電腦王阿達依使用者既有明確裁決排除，不列候選；
T客邦、電腦玩物不加入事件來源；商傳媒只留人工查漏，
恆遠數位只作案例佐證，均無自動抓取或正式配額。

## 驗收與清理

### 2026-10-21 08:58 真實採樣及逐事件複核

使用者要求再執行一次實際測試。以 `6415ed93ae4a` 的最新資料，
對照 08:55 臺北時間生成的 7,403 筆 archive，08:58:37～08:58:56
執行五站探測，18 次 HTTP 請求、19.161 秒，結果為：CyberQ 10 篇／4 候選、
網管人 10／3、DIGITIMES 30／5；資安人與 Meet 仍無可用樣本。
與先前不同的篇數是最新 feed 的採樣結果，沒有調整過濾器。

Codex 對 12 篇候選二次審閱：2 篇事件已覆蓋、3 篇可能新增實測證據、
3 篇廠商公告待驗、3 篇範圍排除、1 篇基準未見待核。這不是人工已批准的
裁決，未填入工具的人工統計或正式新聞池。

- 是方虎尾資料中心動土與五成簽約率，已有 iThome／科技新報，不能列新增。
  自動標題比對漏配，需中文公司名與事件詞擴搜。
- LX Semicon 的 AI 設計採用是本輪唯一優先核對的基準未見事件；
  [DIGITIMES 原稿](https://www.digitimes.com.tw/tech/dt/n/shwnws.asp?id=0000771952_IW3LSO4O4Q1MHF3PHJQQW)
  的原採訪索引日期為 10/16，不能當成 10/21 新發生。80% 是特定模組
  benchmark 的工作時間聲稱，不能泛化成所有晶片開發效率；原採訪直接
  讀取 403，未繞過，尚待原始簡報／人工核對。
- CyberQ 的 FLUX、MiniMax H3 與 DeepSeek GSM8K 是三篇新實測證據待核稿，
  不重算模型發布事件；未重跑作者實驗或核准教學型內容。
- 初篩誤收包括非 AI 跑車評論、租約解說與未定案收購評估；泛詞
  labs／image／prompt／agentic 也會產生無關事件提示。本輪只記錄測試
  發現，未改正式規則或以模糊 matches 宣告同事件。

本次離線驗收 **56 passed in 0.10s**；真實採樣離線重播四個輸出檔案
位元組一致；12 個正式程式／資料／workflow 保護檔案前後 hash 相同。
沒有程式修改，未重跑全套，不把前輪 1240 項當本次紀錄。
完整逐站報告、13 筆事件 CSV（12 候選＋1 篇邊界樣本）、原文／基準連結、
命令／時間／exit code 與 hashes 在本機 Downloads：
`ai-news-radar-tw-source-admission-20261021/acceptance-01/ACCEPTANCE_REPORT.md`。

```bash
.venv/bin/python -m py_compile scripts/evaluate_tw_source_admission.py scripts/update_news.py
.venv/bin/python -m pytest -q -p no:cacheprovider \
  --basetemp /Users/lordmi/Downloads/ai-news-radar-tw-source-admission-20261021/pytest \
  tests/test_tw_source_admission.py
git diff --check
```

fixtures 是明確標示的合成 RSS/Atom，不是新聞量測母體。涵蓋同 URL、
跨語言同事件提示、人工新證據、事件計數去重、教學／非 AI、空／壞 feed、
無時間／時區、窗口邊界、robots／轉址／timeout／回應上限與離線重播。
測試鎖定正式 `TW_MEDIA_FEEDS` 四個 ID，確保候選未接入。

本輪最終完整離線回歸 **1240 passed in 5.64s**；本機 `node` 原未在 PATH，
加入既有內建 Node 路徑後通過，未安裝套件。正式
`source-status.json` 唯讀檢視仍為四站成功；沒有運行正式生成或重寫快照。
新工具獨立且不匯入正式產生器，因此未以全站網路刷新代替隔離驗收。

完整 HTTP 診斷、短摘要、基準副本及重播報告在本機 Downloads 的
`ai-news-radar-tw-source-admission-20261021/`，最終版本在 `final/`。
刪除對應本機輸出即可清理採樣；移除獨立 script、fixtures、測試及本頁即可
撤回工具，正式來源與排程沒有遷移需要。正式准入仍是下一次獨立決策。
