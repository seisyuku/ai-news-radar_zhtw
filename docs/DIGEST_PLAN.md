# 日報與後續訊號工作：小任務與續接計畫

更新日期：2026-10-02（Asia/Taipei）。本文件是維護者工作計畫，不是新公開產品說明。
最新執行位置見 [HANDOVER](HANDOVER.md)；交接格式見
[TASK_HANDOFF_TEMPLATE](TASK_HANDOFF_TEMPLATE.md)。

## 已同意的設計與執行邊界

- D 日報只收錄臺北時間 `[D-1 06:00, D 06:00)` 發布的新聞。
  恰好 D 日 06:00 發布的新聞歸下一期。每天的窗口恰為 24 小時。
- 不加 8 小時消息擴散等待、跨截止時間的補充證據例外或其他新時間規則。
- 06:00 是內容截止時間，不是已設定的排程。截止後生成初稿，上午人工校稿，
  約 11:30 人工發布是工作目標；未承諾準時自動出刊。
- 日報是維護者可審閱的繁中 Markdown；Pulse 維持新聞身分與證據來源。
  公開網站、六類商業事件、現有排序、24h 讀者窗口與 archive 語意保持不變。
- 主線先完成無新 LLM、無網路呼叫的本機日報。候選使用現有資料與產生邏輯，
  不新增爬蟲、一般重要性評分或 story 去重系統。
- 使用者已同意上述設計並要求任務切割及持久交接。本輪交付文件與交接機制，
  沒有開始產品程式實作。後續主線依本計畫做小步本機實作，無須逐任務
  重問同一個已裁決設計；若遇到真正未定產品取捨，再指出具體選項。
- LLM 真實呼叫、新增平臺或付費來源、排程啟用、commit、push、部署不由
  此次任務切割自動授權。只準備到可審閱的結果，再依人類指示啟用。
- 人工審閱是終點；不建立自動發文、帳號管理、發布後 analytics 或 growth 系統。
- 補充交接檔記載 velocity 已取消；本計畫不含 metrics history、delta、
  高頻 polling、長期 social time-series state。既有新聞、健康、付費間隔 state 保留。

## 已查核基線與重要限制

本輪起始工作區乾淨；分支 `master`；HEAD
`541e493957e01168434dd8eb22de414f11045096`。後續以實際工作區重新核對，
不假設 HEAD 永遠不變，不做雜湊掃描。

| 現況 | 實際位置／限制 |
| --- | --- |
| 混合 transport 已存在 | `update_news.collect_all()` 同時收 RSS、HTML 與頁面內 JSON；付費 adapter 與 sensors 在 `main()` 另外執行。`feedparser` 不是主流程的唯一入口。 |
| archive 與原子寫入 | `scripts/archive_output.py`：`load_archive()`、`atomic_write_text()`；archive 壞檔會拒絕，不應改成靜默空檔。原子替換僅限單檔。 |
| 日期與保存 | `event_time()` 通常用 publish time，部分既有路徑可 fallback 到 first seen；`prune_archive_records()` 使用 last-seen retention，不能宣稱 archive 精確保存「所有發布於最近 21 日的新聞」。 |
| story／選題 | `merge_story_items()`、`build_story_record()`、`select_diverse_stories()`、`story_passes_brief_gate()` 可重用；`daily-brief.json` 與 `stories-merged.json` 只有滾動窗口。 |
| story ID | `story_id_for_item()` 由 URL／標題衍生；晚發現較早的同事件文章可改變羣組的 story ID。單份輸入可以確定性重建，不保證歷史跨輪永久身分。 |
| 證據欄位 | story 有 sources、item ID、URL、來源日期、重要性與事件；top-level 沒有 published_at 或 verification，primary_item 也沒有發布日期。不能臆造完整查證狀態。 |
| 來源健康 | `scripts/source_health.py` 已有 group／child failure、degraded、skip 與故障歷史。`successful_sites` 是 group-level 計數，不能直接當 leaf coverage 或實際嘗試成功數。 |
| 摘要 | `scripts/news_summaries.py` 有 publisher context、Groq boundary、內容快取與格式／數字／版本檢查；不是完整語義查證器，也不是日報 generator。 |
| 社羣 | X API、SocialData search／list、TikHub Douyin／Xiaohongshu 已存在。X 的 post_id、public_metrics、lang 不會全保留到公開 archive；文字會截短，list 排除 replies／retweets。 |
| RSSHub | 部分 OPML URL 已改接原生 feed，Telegram／Jike 轉直接頁面。不是公開主流程的必要 runtime；其他私人 OPML 不作公開證據。 |

離線 fixture 曾執行現有 `main()`，封鎖 requests 並清空憑證環境：

| 情境 | exit | 本輪抓取 | 24h 文章 | story | 失敗任務 |
| --- | --- | --- | --- | --- | --- |
| RSS 全失效、非 RSS fixture 可用 | 0 | 5 | 5 | 4 | 14 |
| 全來源失敗、無 archive | 0 | 0 | 0 | 0 | 17 |
| 全來源失敗、archive 有近期新聞 | 0 | 0 | 1 | 1 | 17 |
| 全來源失敗、archive 已過期 | 0 | 0 | 0 | 0 | 17 |

這是離線程式行為證據，不是上游 availability、coverage 或 production 驗收。
生成時間新不等於當輪有取得新內容。早先暫存輸出已清除；數值源自本聊天的
工具結果。往後每個任務需保存命令與結果，不假稱這輪已有原始 log 檔。

10 個相關既有測試檔在本聊天已執行：112 passed（非完整 suite）。範圍為
group source status、source health module、paid health history、story merge、
daily brief、news summaries、atomic output、archive output module、private bridge、
TikHub parsers。此結果不涵蓋尚未實作的日報。

## 任務臺帳

狀態：`done` 完成且交接已落檔；`planned` 排定但未開始；`conditional` 有另案
需求／外部啟用條件；`in_progress` 已開始；`blocked` 需具體外部條件。
依賴未完成不叫 blocked。任務存在本身不授權其外部操作。

| ID | 小任務／交付物 | 依賴 | 狀態 | 建議模型／思考 |
| --- | --- | --- | --- | --- |
| H00 | 建立規格、臺帳、交接模板與初始檢查點 | 無 | done | GPT-6.1 Sol／Medium |
| D01 | 日報輸入契約與 fixture 清單 | H00 | done | GPT-6.1 Sol／Medium |
| D02 | 06:00 日期窗口純函式與邊界測試 | D01 | done | GPT-6.1 Sol／Medium |
| D03 | 唯讀 archive／cache／health 輸入快照 | D01 | done | GPT-6.1 Sol／Medium |
| D04 | 按窗口挑選原始新聞，再重用 story 生成 | D02、D03 | done | GPT-6.1 Sol／High |
| D05 | story → EditorialCandidate 薄 adapter | D04 | done | GPT-6.1 Sol／Medium |
| D06 | 日報選題與來源證據整理 | D05 | done | GPT-6.1 Sol／Medium |
| D07 | 給日報的來源健康／資料時效摘要 | D03 | done | GPT-6.1 Sol／Medium |
| D08 | 繁中 Markdown renderer | D06、D07 | done | GPT-6 Luna／Medium |
| D09 | CLI、日期檔名、原子寫入與重跑行為 | D08 | done | GPT-6.1 Sol／Medium |
| D10 | 失敗、空日與兼容性整合驗收 | D09 | done | GPT-6.1 Sol／High |
| D11 | 本機樣本、人工審閱交付與使用說明 | D10 | done | GPT-6.1 Sol／Medium |
| L01 | 可選 daily synthesis boundary＋離線 stub | D11 | conditional | GPT-6.1 Sol／Medium |
| L02 | 逐故事歸因、數字／版本與失敗測試 | L01 | conditional | GPT-6.1 Sol／High |
| L03 | 小樣本真實 provider 評估與成本報告 | L02、真實呼叫授權 | conditional | GPT-6.1 Sol／Medium |
| O01 | 日報生成排程提案與正式啟用驗收 | D11、排程／部署授權 | github_observing | GPT-6.1 Sol／Medium；實作 High |
| B01 | OPML 非 feed HTML 被判健康零則 | H00 | done | GPT-6.1 Sol／Medium |
| B02 | TikHub missing metrics 與 0 的區分 | H00 | done | GPT-6.1 Sol／Medium |
| B03 | SocialData search 分頁／讀取成本上界 | H00 | done | GPT-6.1 Sol／High |
| S01 | 最小 social contract 與平臺身分 fixtures | H00 | conditional | GPT-6.1 Sol／High |
| S02 | X API／SocialData 跨 provider 正規化 | S01 | conditional | GPT-6.1 Sol／High |
| S03 | TikHub 當下 snapshot 正規化 | S01、B02 | conditional | GPT-6.1 Sol／Medium |
| S04 | Social Editor 候選證據包匯出 | S02、consumer 契約 | conditional | GPT-6.1 Sol／Medium |
| S05 | Threads 實際需求與官方 read API 查核 | S01、監看用途 | conditional | GPT-6.1 Sol／High |
| S06 | Threads 小 adapter、fixture 與健康隔離 | S05 通過、來源接入授權 | conditional | GPT-6.1 Sol／Medium |
| M01 | 實際模型 alias 錯配與 consumer 缺口量測 | H00 | conditional | GPT-6.1 Sol／Medium |
| M02 | 少量 alias resolver＋單一 consumer 驗證 | M01 證明收益 | conditional | GPT-6.1 Sol／High |
| E01 | 單一候選來源增益／RSSHub route 評估 | 指定候選來源 | conditional | GPT-6.1 Sol／Medium |

共 28 項：交接機制 1、無新 LLM 日報 11、可選 LLM 3、排程 1、獨立 bug 3、
社羣 6、model registry 2、來源評估 1。H00 完成不代表其他任務已實作。

主線：`D01 → D02/D03 → D04 → D05 → D06/D07 → D08 → D09 → D10 → D11`。
實際執行預設一個任務一個檢查點，逐項進行；斜線表示依賴獨立，並非要求
啟動 subagent 或另建聊天。B 任務獨立，不必捆入日報 patch。

## 主線任務卡

### D01 — 輸入契約與測例

- 範圍：在本文件記下 `--date`、input snapshot、輸入 as-of、輸出位置、
  缺發布日期、晚發現與 same-date rerun 的工程處理。日報資料源優先使用 retained
  archive；不能只讀當下 stories-merged 而宣稱取得完整指定窗口。
- 原則：按原文發布日期歸期。缺日期不得使用 first_seen 偽造日期；排除並計數。
  晚發現但發布於窗口內可收錄；窗口外不作本期補充證據。歷史重跑使用目前
  指定快照能提供的資料，不承諾復原已退場內容或當時 coverage。
- 查碼：`event_time()`、`merge_raw_items_into_archive()`、`build_story_record()`、
  archive/cache loader、summary context。僅補定必要工程語意，不添加新的新聞准入規則。
- 交付：輸入／輸出小型 schema 與至少跨 06:00、UTC、缺日期、晚發現、空日、
  壞檔、不同快照重跑 fixtures 清單；標明候選新檔案路徑與測試目標。
- 完成：後續 D02/D03 不需猜日期、輸入或錯誤語意；若實際取捨會改已同意設計，
  列出具體選項與建議再討論。此次不做新的全 repo 盤點。

### D01 已定契約（2026-10-02）

本節是 D02～D11 的實作依據。D01 交付的是規格與測例設計；目前實作進度依
臺帳及下方已完成接口，不能視為已有整套日報 generator。
下列工程診斷不新增新聞時間准入條件。

#### CLI 與時間

- 候選 CLI：`scripts/generate_digest.py --date YYYY-MM-DD --input-dir PATH --output-dir PATH`。
  這是待實作命令，現在不可執行。`--date` 是期別日期，不是生成時刻；省略時只取
  啟動當刻的 Asia/Taipei 日期一次。重現與歷史重跑必須明示日期。
- `--input-dir` 預設專案 `data/`，只讀下表三個檔案，不接受遠端 URL。
  `--output-dir` 預設 `/Users/lordmi/Downloads/ai-news-radar-digests/`。
  測試使用獨立 fixture 目錄；不覆寫正式快照、不在讀取時保存或修復輸入。
- D 期窗口為 `[D-1 06:00+08:00, D 06:00+08:00)`，轉為 UTC aware datetime 比較。
  排序／重要性計算固定 `now=window.end_utc`、`window_hours=24`，不使用生成牆鐘。
- 發布日期只接受帶時區的 ISO 8601 datetime（含 Z 或 offset）。缺值、非法字串、
  只有日期、沒有時區各有診斷；排除該筆，不用 first_seen、last_seen 或檔案 mtime 補。
  日報不直接用 `parse_iso()` 的「naive 當 UTC」或 `event_time()` 的 first-seen fallback。
- 未到當天 06:00 就執行仍使用指定日期，不默默改期或等待。輸入 as-of 早於截止時
  標記 `input_before_cutoff`；資料不完整的提示不是另一個收錄窗口。
- 晚發現且原發布時間在窗口內的新聞，若出現在指定快照則可收錄。不同快照重跑
  同一期可能改變故事集合／ID／摘要，這是新版草稿；不保證還原當時新聞全貌。

#### 三個輸入檔與快照語意

| 邏輯輸入 | 最低 wire shape | 缺失／不合法的行為 |
| --- | --- | --- |
| `archive.json`（必要） | object，`items: list[record]` 或 legacy `dict[id, record]`；可選 `generated_at: string`、`total_items: int` | 不存在／不可讀／壞 JSON／既有 loader 結構或 ID 驗證失敗：fatal，不輸出正常日報；不能把 loader 的缺檔 `{}` 當空日。`items: []` 或 `{}` 才是合法空輸入。 |
| `title-zh-cache.json`（可選） | `dict[str, str]`；title 原文 key、`summary::<原摘要>` key；現有格式無生成時間 | 缺檔：`missing`；不可讀／壞 JSON／非 object：`invalid`，停用此快取，原文仍可用。非字串／空白 value 逐項略過並計數，不沿用舊 loader 任意 `str()` 的 coercion。 |
| `source-status.json`（可選） | object，`generated_at: string`、`sites: list[object]`；只保留 D07 需要的健康欄位 | 缺檔／壞檔／缺必要 shape：`missing`／`invalid`，健康未知；不能解讀為來源全成功或全失敗。 |

- archive 重用 `archive_output.load_archive(..., normalize_record=normalize_reader_source_identity)`
  的 ID／legacy 驗證與 AIBASE identity policy；在呼叫前檢查存在性，讀到的內容須是本輪
  捕捉的 bytes。D03 可用小型共用 decode 邊界或受控 snapshot 副本銜接現有 path API，
  不為此改掉公開 loader 的缺檔語意。選型時避免重複一套 archive validator。
- record 至少有 loader 驗證的非空字串 `id`；可選 `title`、`url`、`source`、`site_id`、
  `site_name`、`summary`、`published_at`、`first_seen_at`、`last_seen_at`、`duplicate_of`、
  語言欄位與 extensions。legacy key 為 ID；未知欄位不改原檔。
- 日報必須有非空 title 與 http(s) 原文 URL，否則略過並計數，避免輸出無證據的題目。
  `duplicate_of` alias 不參與選題；缺來源名稱可顯示「未標示來源」，不臆造出版者。
  其餘相關性、來源分級、business events、去重與選題沿用既有規則，不新增評分。
- `generated_at` 是檔案 producer as-of，不是「完整涵蓋到這時間」的保證。缺失或不能
  解析時記 `null`／`unknown_as_of`；不借用 mtime。`total_items` 不作收錄或完整性依據。
- 比較已解析的 archive／health UTC 時刻：相同為 `matched`，不同為 `mismatched`，
  任一未知為 `unverifiable`。後兩者保留各自 as-of 與提示，但不把健康計數帶入日報的
  同輪健康摘要。title cache 一律 `unversioned`，無法判定同輪；有命中才保留譯文來源。
- 本輪每檔只讀一次並保存獨立 immutable bytes，後續純函式只讀記憶體資料副本。
  活躍 `data/` 的多檔讀取不是交易，不能承諾一致捕捉；需精確重現時指定預先保存的
  唯讀輸入副本。同輪時間相等也不是多檔交易證明。
- 只對這三個明確輸入計算 bytes SHA-256，記 logical filename、presence/status、
  producer as-of 與 digest；不掃描其他檔案或 repo。缺檔有固定 missing marker。
  input identity 由這些 fingerprint、期別、schema／pipeline 版本與選題設定確定性衍生。
  不納入絕對路徑、mtime 或執行牆鐘；執行時間只放非產品 execution log。
- 第一期不用 `ai-summary-cache.json`：現有 key 是 title＋source context＋model＋
  prompt version 的 hash，不是 story ID；archive 不保存完整已生成 story AI 摘要。
  不靠相似標題借用快取。先輸出 publisher summary／其既有譯文，沒有則只保留標題
  和證據；AI 摘要 cache 的精確接合留給 L01。這不改既有網站摘要功能。
- 不呼叫 `main()`、fetchers、`merge_raw_items_into_archive()`、prune、translator 或
  `summarize_stories()`；即使環境已有 provider key，也不得發出網路或模型請求。

#### 最小內部 schema 與輸出

這是日報內部 contract v1，不是修改 archive 或公開 story 的 schema。

| 型別／欄位 | 型別與語意 |
| --- | --- |
| `DigestWindow` | `date: YYYY-MM-DD`、`timezone: "Asia/Taipei"`、`start_utc/end_utc: aware datetime`；start inclusive、end exclusive。 |
| `DigestInput` | `records: dict[id, ArchiveRecord]`、`title_cache: dict[str,str]`、`health: object|null`、`inputs: list[InputDescriptor]`、`diagnostics: list[Diagnostic]`；loader 不篩時間、不選題。 |
| `InputDescriptor` | `name: str`、`status: loaded|missing|invalid`、`sha256: str|null`、`producer_as_of: UTC ISO|null`、`alignment: matched|mismatched|unverifiable|unversioned`；digest 是 bytes 身分，不是假定 generation ID。 |
| `Diagnostic` | `code: str`、`count: int`、可選邏輯 input／item ID；不抄原始 payload、credential 或未清理錯誤。多個原因可重疊，不能加總冒稱獨立文章數。 |
| `EditorialCandidate`（D05） | `schema_version: 1`、`story_id: str`、`primary_item_id/title/primary_url: str|null`、`sources: list[SourceRef]`、`summary: str|null`、`summary_kind: publisher|publisher_translation|none`、`importance: float|null`、`business_events/reasons: list[str]`、`verification: null`；舊 optional 欄位 nullable，不是完整查證結果。 |
| `SourceRef` | `item_id/title/url/source/site_id: str|null`、`published_at: UTC ISO|null`；缺值不臆造。primary 的發布時間由 ID 回查 sources，不能猜 story.latest_at。實際新增的摘要／譯文 provenance 見 D05 接口。 |
| `DigestDocument` | `schema_version: 1`、window、`input_identity: str`、inputs、`candidates: list[EditorialCandidate]`、diagnostics、health summary（未知可 null）；零 candidates 合法。 |

- `summary` 第一版來自 primary source 的 publisher 摘要，優先其已命中譯文；其他來源
  摘要仍保留於證據，不拼接成未經支持的綜合論述。沒有摘要的值為 null。
- D04 先嚴格篩原始發布時間與可用 record，再做現有 deterministic preprocessing、
  AI relevance／source tier、去重、`merge_story_items()`；同一時刻以 item ID 加入固定
  tie-break，避免 archive list 順序決定 story anchor。不要走 random_pick=True。
- D09 產物候選：`digest-YYYY-MM-DD.md`、`digest-YYYY-MM-DD.meta.json`。
  sidecar 保存上述 metadata／候選證據，不重複發布整份 archive 或 cache。
  相同三檔 bytes、date、設定與程式版本應產生完全相同內容；MD／sidecar 記相同
  input identity。每檔原子替換；兩檔不保證交易，人工交付前核對 identity。
- 同日新版覆寫前須完成建構／驗證，fatal 不動既有成功文件；合法空日可生成空日草稿。
  exit 0：成功（含空日／可選輸入降級）；exit 2：日期／參數錯誤；exit 1：必要輸入、
  建構或寫入失敗。這是 D09 待實作約定，不宣稱目前已有 CLI 行為。
- D07 的 source health 必須標 as-of／aligned 狀態；只有 matched 才附當輪健康摘要，
  即使 matched 仍不宣稱這份狀態涵蓋整個日報窗口。

#### Fixture 清單與責任

全部為手工合成公開形狀，用 `example.invalid`，不複製私人 feed 或真實付費 payload。
D01 只設計矩陣，實際 fixture 與測試由下列任務建立。

| ID | 最小輸入／變化 | 預期結果 | 負責任務／測試群 |
| --- | --- | --- | --- |
| F01 | 10/2 期：前日 05:59:59、06:00、當日 05:59:59、06:00 | 只有中間兩筆收錄；UTC 9/30 22:00～10/1 22:00 | D02／window |
| F02 | 同一 instant 分別 Z、+08:00、-04:00 | 相同歸期與 UTC 結果 | D02／window |
| F03 | 跨年、閏日、非法／非 YYYY-MM-DD 日期；注入固定啟動時刻 | 精確 24h；非法拒絕；預設只解析臺北日期一次 | D02／window |
| F04 | published_at null、missing、bad、date-only、naive；first_seen 在窗內 | 不以 first_seen 補，分類計數與排除；舊 reader 不改 | D02、D04／window、pipeline |
| F05 | 發布窗內、first_seen／snapshot 在截止後；發布窗外同事件證據 | 前者收錄，後者不混入 sources／merge | D04／pipeline |
| F06 | missing archive、壞 JSON、items 非 list/object、缺 ID、重複 ID | fatal；不寫正常日報；既有成功文件保留 | D03、D09／input、CLI |
| F07 | list archive、legacy keyed archive、AIBASE alias、未知 extension | ID policy 一致；alias 排除；不改輸入 | D03、D04／input、pipeline |
| F08 | 合法空 archive／全部窗外／全部非 AI | 成功空日，與 missing input 明確不同 | D04、D08、D09／pipeline、render、CLI |
| F09 | 缺 title／非 http(s) URL／缺 publisher | 無 title/link 逐筆略過；缺 publisher 不造來源 | D04、D05／pipeline、candidate |
| F10 | cache missing／broken／混合 value／exact hit／miss | 正確降級；只用 exact string hit；原文不丟 | D03、D05／input、candidate |
| F11 | archive／health as-of equal、different、unknown；cache 無 as-of | UTC 比較；不同／未知不附同輪健康；cache unversioned | D03、D07／input、health |
| F12 | archive as-of 在截止前；當期尚未到 06:00 | 標 input_before_cutoff；不換期、不擴窗、不等待 | D03、D07／input、health |
| F13 | 同 bytes 與設定，改執行牆鐘／輸入目錄／record 順序 | bytes 不變時輸出 identity／內容一致；只改 record 順序時故事一致、bytes identity 可不同 | D04、D09／pipeline、CLI |
| F14 | 同 date，不同 snapshot 增入晚發現文章／變更摘要 | identity 與相應草稿改變；不宣稱永久 story ID | D04、D09／pipeline、CLI |
| F15 | 多源同事件、同 URL tracking params、不同模型版本、同時間 tie | 現有 merge 語意與固定 tie-break；不誤合不同版本 | D04／pipeline |
| F16 | primary 缺日期欄位、單／多源、缺摘要、已有譯文 | 日期回查 SourceRef；nullable verification；摘要來源可追溯 | D05、D08／candidate、render |
| F17 | matched health 全失效但 archive 有窗內新聞；skip／partial／disabled | 新聞仍可用；健康不說新採集，不混算 leaf/group | D07／health |
| F18 | Markdown 特殊字元、空日、缺翻譯 | 可閱讀與點證據，英文原文誠實保留 | D08／render |
| F19 | 無 key、有假 key、封鎖 requests/provider；replace 失敗、sidecar identity 不同 | 全程零網路／LLM；單檔保留舊值；多檔不一致拒絕當完成交付 | D09、D10／CLI、integration |

#### 候選檔案與接口（後續小任務才新增）

- D02：`scripts/digest_window.py`，`window_for_date(date: str) -> DigestWindow`、
  strict aware timestamp parser；`tests/test_digest_window.py`。模組只依賴標準庫。
- D03：`scripts/digest_input.py`，`load_digest_input(input_dir: Path) -> DigestInput`；
  `tests/test_digest_input.py`。重用 archive loader，讀取／診斷與 display cache 分離。
- D04～D07：`scripts/digest_pipeline.py` 與需要時的 `scripts/digest_types.py`，
  `build_digest_document(snapshot, window, settings) -> DigestDocument`；
  `tests/test_digest_pipeline.py`、`tests/test_digest_candidates.py`、`tests/test_digest_health.py`。
  內部預處理邊界只抽取必要純函式，不開第二套新聞 schema／評分／來源流程。
- D08：`scripts/digest_render.py`，`render_digest(document) -> str`；
  `tests/test_digest_render.py`。
- D09／D10：`scripts/generate_digest.py`；`tests/test_generate_digest.py`。
  fixtures 優先由 test helper 建立；共用 wire JSON 若必要放 `tests/fixtures/digest/`，
  不把預期正式輸出寫進 `data/`。接口與檔案可因實際重用情況微調，但須交接理由。
- D01 驗收：已定日期、輸入形狀、as-of、空日／fatal、快取降級、確定性、輸出與
  測例責任；尚未寫 fixture、實作新函式或驗證新日報。下一步 D02，D03 亦已可開始。

### D02 — 時間窗口

- 範圍：新增小型純函式，`--date` 預設臺北當天；計算半開區間並轉 UTC 比對。
  不修改 `event_time()` 或現有網站窗口。
- 完成：前一天 05:59:59／06:00、當天 05:59:59／06:00、跨年、UTC 對照、
  非法日期測例通過。10/2 期的 UTC 界線為 9/30 22:00～10/1 22:00。
- 交接：函式 signature、具體測試、D03 所需時間型別。

#### D02 已實作接口與驗收（2026-10-02）

- `scripts/digest_window.py` 僅依賴標準庫，不載入生成器、來源或網路套件。
- `window_for_date(value: str | None = None, *, now: datetime | None = None) -> DigestWindow`：
  明示日期用嚴格 `YYYY-MM-DD`，忽略 now；省略時捕捉一次 aware clock，取臺北當天。
  在 06:00 前不改期。日期非法／不能表示前一天 UTC 窗口時 raise `DigestTimeError("invalid_date")`；
  注入 naive clock 為 `invalid_now`。
- frozen `DigestWindow` 欄位：`date`、`timezone="Asia/Taipei"`、`start_utc`、`end_utc`。
  UTC 欄位是 aware datetime；`contains(published_at: datetime) -> bool` 採半開比較，
  naive timestamp 拒絕。D03 可以直接重用 parser 解析 producer as-of。
- `parse_published_at(value: object) -> datetime`：回傳 UTC aware datetime；失敗 raise
  `DigestTimeError`，`.code` 為 `missing_timestamp`、`date_only`、`naive_timestamp` 或
  `invalid_timestamp`。錯誤訊息只含 code，不抄輸入。D04 負責捕捉、排除與計數，
  這個函式不讀 record，也不接 first_seen。
- wire 格式：calendar `YYYY-MM-DD`、T 或空格、`HH:MM`／`HH:MM:SS`（可含 1～6 位
  小數秒）、Z／`±HH:MM`／`±HHMM`。offset 分鐘須 00～59，不接受只有 offset 小時、
  date-only、naive、非空前後空白或非法日曆值。這是既有 archive timestamp 的日報解析邊界。
- `tests/test_digest_window.py`：F01～F04 的日期／發布時間部分共 49 項通過；包含
  06:00 與微秒邊界、等價 offsets、跨年／閏日、非法日期、臺北午夜／截止前的預設日期、
  clock 只取一次、錯誤代碼、不可變窗口與隔離 import。F04 record fallback 排除仍待 D04。
- 新模組與既有 `update_news.py` 語法檢查、`git diff --check` 通過。
  無共享 generation/schema/scoring 行為變更，未跑 full suite；不當作 D03 或整套日報驗收。
- 證據與 task-only patch：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D02-20261002-192502/`。下一步 D03，先保存起始檢查點，再做只讀 archive/cache/health。

### D03 — 唯讀輸入快照

- 範圍：讀 archive 與必要的既有顯示快取／來源健康；不抓新聞、不翻譯、
  不呼叫模型，不改輸入檔。重用 validated archive loader。
- 完成：缺主輸入、壞 archive、舊 schema、cache 缺失、snapshot generation
  不一致有明確結果。保存實際輸入 as-of；不同檔 generation 不一致不能默認同輪。
- 交接：輸入檔名、payload 型別、缺檔與不一致策略；一份 fixture 可供 D04/D07。

#### D03 已實作接口與驗收（2026-10-02）

- `scripts/digest_input.py`：`load_digest_input(input_dir: Path, *, normalize_record=None)`
  回傳 frozen `DigestInput`。預設延遲載入既有 reader identity 純函式，不執行
  generator、來源、翻譯或模型；可注入 normalization policy，讓輸入模組隔離使用。
- `archive_output.archive_from_payload(payload, *, normalize_record, label="archive")`
  共用原 loader 的結構／ID 驗證。path loader 的缺檔／解碼與錯誤語意保留；
  日報把必要 archive missing/unreadable/invalid 轉為安全 `DigestInputError.code`。
  詳見 [archive I/O contract](ARCHIVE_OUTPUT.md)。沒有受控副本／新文件寫入。
- snapshot 包含 `records`、`title_cache`、sanitized `health`、tuple `inputs/diagnostics`、
  `fingerprint`，以及不出現在 repr 的 `captured_bytes`（不可修改的 mapping of bytes）。
  records/cache/health 為本輪獨立 decoded dictionaries；下游 enrichment 應 copy，
  frozen container 並不代表深層 dict 不可修改。
- descriptor 欄位 name/status/sha256/producer_as_of/alignment；診斷欄位 code/count/input。
  三個 logical names 固定且每檔 read_bytes 一次；fingerprint 只含 name/status/raw bytes
  digest，不含 path/mtime/牆鐘。完整日報 identity（加 date/settings/version）留 D09。
- optional cache/health 缺失或不可用會降級；cache 僅接受非空字串 exact entries。
  health 只保留必要狀態欄位、subsources 與 x_api/socialdata/tikhub/rss_opml 的安全
  disabled/skip/count metadata；原始 error、credential presence、URL/path 欄位不帶入 health。
  這是欄位 allowlist，不是任意字串的私密內容掃描；D07 應使用受控狀態文案，不能直接披露
  不明 source_id／reason 文字。
  原始三檔 bytes 僅供本輪內部身份與重現，不能直接序列化到日報／公開證據。
- 已解析 as-of 以 D02 strict parser 轉 UTC 比較；matched/mismatched/unverifiable 與
  cache unversioned 明示。sanitized health 證據仍保留；D07 負責僅在 matched 時
  附同輪摘要及 input_before_cutoff 提示，loader 不知道日報日期、不做時間篩選。
- `tests/test_digest_input.py` 覆蓋 missing/corrupt/legacy/empty/ID、cache shape與混合值、
  as-of／UTC offsets、不可讀、三檔讀一次、更新中捕捉、不改輸入、跨目錄 fingerprint、
  disabled/skip metadata、無 provider 呼叫、policy injection 下兩種 import mode。
- 初版聚焦 88 passed；完整 suite 首次 39 failed/570 passed，全為 PATH 缺 node。
  補入 bundled Node 後 609 passed；再補 provider disabled/skip metadata 測例後，
  最終完整 suite 610 passed。最終語法與差異格式檢查通過，失敗 log 保留。
- 證據／本任務增量 patch：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D03-20261002-193322/`。D04 和 D07 依賴已滿足，預設下一項 D04。

### D04 — 篩選後重建故事

- 範圍：先按新聞 published_at 挑出窗口，再重用現有相關性、來源分級、
  確定性去重與 `merge_story_items()`；不能直接按 story.latest_at 隨意歸期。
  排序使用固定窗口截止或已約定 as-of，不能讓牆鐘 now 改變相同輸入結果。
- 完成：窗口外文章不混入；空窗口合法；同一輸入快照、date、設定產生相同
  story 集合；相同網址、多來源與不同模型版本仍符合既有 merge 語意。
- 交接：實際重用 symbols、與現有 producer 的差異、story ID 限制；不改公開 IDs。

#### D04 已實作接口與驗收（2026-10-02）

- `scripts/digest_pipeline.py`：`build_digest_stories(snapshot: DigestInput, window: DigestWindow)`
  回傳 frozen `DigestStories(stories, items, diagnostics)`，前三者皆為 tuple；story/item
  仍是既有形狀的本輪工作 dict。`items` 是實際傳入 merge 的去重後證據，不是所有
  原始新聞。stage diagnostics 只含本階段計數；D07／composer 另合併 input diagnostics。
- 尚不實作 `build_digest_document()`：先提供 D04 stage 接口，待 D05～D07 schema／選題／
  metadata 齊備後組裝；不提前建立 EditorialCandidate 或人工選題規則。
- 先排除所有站別的 `duplicate_of` alias，再用 D02 strict parser 篩原始發布窗口，
  缺值／date-only／naive／非法格式不以 first_seen 補；窗口外文章在預處理／merge 前排除。
  非空字串 title、http(s)＋hostname 且無空白的原文 URL 才能形成候選證據。
- 通過者 deep-copy，ID 維持 archive key，published_at 正規為 UTC ISO；依發布時間
  降序／ID 預排序後重用 title/summary 繁中顯示修復、來源名 alias、business_event_score、
  add_ai_relevance_fields、add_source_tier_fields。缺出版者用「未標示來源」，不猜 URL host。
  不使用 add_bilingual_fields、快取翻譯、AI 摘要或 provider；D05 才接可用 exact cache。
- 接著依現有次序重用 dedupe_same_publisher_items、apply_reader_source_limits、
  dedupe_items_by_title_url(random_pick=False)、suppress_near_duplicate_items 與再次 source limits。
  reader 去重／上限會移除重複文章，因此 source_count 不是全部 raw records 或獨立查證數。
- pre-merge 依 `(published_at, item_id)` 升序，呼叫原 merge_story_items，固定
  `now=window.end_utc, window_hours=24`。story 排序保留現有 score/latest/title 順序，
  只增最後 story_id tie-break。既有 ID 算法不改，同時刻／同品質固定 ID 作選擇。
  新快照晚加入更早同事件來源，story ID 仍可能改變；沒有跨快照永久 ID 保證。
- 診斷 code：duplicate_alias、D02 日期拒絕 codes、outside_window、invalid_title、
  invalid_url、not_ai_related、reader_dedup_or_limit。按 code 排序並彙總 count，不抄原始資料。
- `tests/test_digest_pipeline.py` 共 32 項；包含 F04/F05/F08/F09/F13～F15、source cap／
  publisher/near-duplicate、等時 permutation、變更快照、D03 loader 接合與 deep-copy。
  已封鎖 clock/random choice/network/translator/summary provider，檢查既有 merge 結果。
- 最終聚焦 50 passed、完整 Python suite 642 passed、兩檔語法與 diff check 通過。
  首次兩個新測例保留 AI site_name／未達既有 title merge 門檻；已修正 fixture 假設，
  未修改 scoring 或 merge。失敗紀錄保留。這不是 D05／D06 或日報 CLI 整合驗收。
- 證據／task-only patch：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D04-20261002-194958/`。下一步 D05／GPT-6.1 Sol／Medium。

### D05 — 候選 adapter

- 範圍：story ID、primary item ID／URL、sources、原始時間、摘要、既有重要性、
  business events、reasons、schema version。缺欄位 explicit nullable。
- 完成：單源／多源／缺摘要／舊 fixture 通過；不修改輸入物件、不臆造 verification；
  sources 數量不能被描述為已獨立查證次數。
- 交接：schema 與欄位來源表；candidate ID 僅承諾指定快照中的穩定衍生身分。

#### D05 已實作接口與驗收（2026-10-02）

- 新增 `scripts/digest_candidates.py`，獨立於 generator/provider，只依賴標準庫及 D02。
  `adapt_story(story, *, title_cache=None) -> EditorialCandidate`、
  `adapt_stories(stories, *, title_cache=None) -> list[EditorialCandidate]`；保持故事順序與 ID，
  不選題、不重排、不另造 candidate ID。無有效 story_id raise `CandidateError("missing_story_id")`。
- 定義 schema v1 的 EditorialCandidate／SourceRef／TranslationRef TypedDict；除了可用
  story ID，舊 optional 欄位明示 null／空 list。非標準 legacy ID 字串原樣保留，不 trim。
  importance 沿用 importance/importance_score/score，缺失、非法／非有限值為 null，不補評分。
- 來源列表優先用 sources（缺 list 才用 legacy items）；非 mapping entry 略過。
  primary_item.id 只有唯一命中 SourceRef.item_id 時，才採其日期與摘要。缺或歧義不猜來源；
  日期嚴格轉 UTC，非法／缺值為 null，不以 primary/latest_at／first_seen 替代。
- 每個來源保留 title/title_original、url/source/site_id/published_at、publisher summary。
  candidate primary_url 先取主來源 URL，再用明示 primary/top URL metadata fallback；
  candidate title 無可用主來源時保留 primary/story metadata並標 title_origin，不借用其譯文。
- 摘要只來自主來源 publisher summary；primary 缺摘要時為 null，其他來源摘要仍留 sources，
  不借用其他來源、primary 複製文字、news_summary 或 summary_zh。verification 永遠 null，
  source_count 由 refs 長度衍生，不沿用輸入宣稱次數，也不是獨立查證數。
- title 以原字串、summary 以 `summary::<原字串>` 精確查 cache；無 fuzzy/case/whitespace
  matching。命中用 publisher_translation，否則原文／none；保留 original 與 translation ref
  的 input/key/alignment=unversioned，不猜生成時間、翻譯模型或語義查證結果。
  此處 original 是 D04 顯示正規化後、尚未套譯文的出版者文字，不宣稱是抓取原始 bytes。
- candidate 另有 primary_published_at、summary_source_item_id、title_origin/title_translation、
  summary_original/summary_translation；每份 SourceRef 也保留原文字與譯文來源。
  外部 dict/cache 不修改；結果只含明確欄位，不搬移 arbitrary raw payload。
- `tests/test_digest_candidates.py` 31 項，加 D04 32 項，最終聚焦 **63 passed**；
  新模組語法與 diff check 通過。包含單／多源、精確cache／miss／非法值、legacy/缺欄位、
  primary ID 歧義、缺日期／摘要、拒絕AI摘要借用、JSON有限數值、ID原樣、不改輸入與
  D03/D04接合、兩種隔離 import。無共享 generation/schema/scoring 修改，未重跑 full suite。
- 證據／本任務增量 patch：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D05-20261002-211348/`。下一項 D06／GPT-6.1 Sol／Medium。

### D06 — 選題與證據

- 範圍：重用既有選題邏輯與重要性，保留來源連結與 publisher 摘要；
  有限候選數用於閱讀／後續呼叫上界，不強制湊足 5～8 題，不新增最低來源配額。
- 完成：排序與選題確定性、同事件不重複、少量／零則合法；
  沒有摘要時保留標題與來源，不憑記憶補寫文章內容。
- 交接：有效選題參數、每個欄位的證據來源、D08 renderer 輸入。

#### D06 已實作接口與驗收（2026-10-02）

- 新增 `scripts/digest_selection.py`；`select_digest_candidates(stage, candidates,
  *, limit=20, same_source_penalty=0.03)` 接 D04 DigestStories 與 D05 同批候選。
  原 story 通過既有 brief gate（score >= 0.72 或 source_count >= 2）後，重用
  select_diverse_stories 的來源降權、同事件抑制與上限；不改 scoring，不新增配額。
- 選題只讀原 story 的 score/title，cache 譯文與候選 importance 不影響排序。
  同 score/title 先以原 story ID 固定 tie 順序；按相同 ID 對回並 deep-copy 完整候選，
  保留原文、來源 URL、日期、publisher 摘要與 cache provenance；缺摘要不補寫。
- 故事／候選 ID 必須各自唯一且集合一致，缺漏或混批報安全 SelectionError；
  此檢查不是快照 provenance 的密碼學驗證。limit 必須非負整數，penalty 非負有限值，
  story score 若提供須能轉為有限數值；不借候選分數補原 story。
- DigestSelection 回傳 candidates tuple、total_candidates、eligible_count、settings、
  diagnostics。SelectionSettings 記錄 limit、same_source_penalty、brief_score_gate 與
  policy=existing_daily_brief；D09 應納入生成 identity。D08 取 candidates 作 renderer 輸入。
- diagnostics 僅此階段：below_brief_gate、diversity_or_limit；後者合併去重與上限計數，
  不假造逐題淘汰原因。input／pipeline diagnostics 留各階段供 composer 合併。
  空／單題合法，limit=0 可空報；20 為預設可調上限，不強湊題數。
- 最終聚焦 **107 passed**，覆蓋 D06、D05、D04、既有 daily brief 與 quality fixes；
  語法及差異格式通過。隔離新模組未改共享生成／schema／scoring，未重跑完整 suite。
  無 provider、網路、clock、隨機選題；無正式資料／來源／workflow 修改。
- 交接與命令證據：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D06-20261002-213319/`。
  下一項 D07／GPT-6.1 Sol／Medium；health、renderer、CLI 尚未實作。

### D07 — 健康與時效摘要

- 範圍：從既有 health 產生薄的 document metadata／必要限制提示；區分成功、
  健康零則、失敗、部分失敗、skip、disabled；不做 dashboard。
- 完成：leaf/group 不重複混算；失敗不叫零討論；本輪抓取 0 但 archive 有新聞
  不叫全新採集；health as-of 與 archive as-of 明示。當下 health 不是歷史日 coverage。
- 交接：狀態欄位與對應來源、missing/mismatched health 行為、D08 文案界線。

#### D07 已實作接口與驗收（2026-10-02）

- 新增 `scripts/digest_health.py`；純函式 `summarize_digest_health(snapshot, window)`
  回傳 frozen DigestHealth：archive_as_of、health_as_of（UTC ISO/null）、health_status、
  alignment、input_before_cutoff（bool/null）、current_round（RoundHealth/null）、notices。
  不重算／更改 source health history，不讀檔、不抓取、不呼叫 provider 或 clock。
- as-of 取 D03 InputDescriptor，重新比較已解析 UTC 時刻，不信任呼叫端 alignment 字串；
  missing／invalid health 或 mismatched／unverifiable 不附 current_round。各自合法 as-of
  仍保留；未知不借 mtime。loaded 卻缺 sites shape 亦不產生統計。
- archive as-of < window.end_utc 才 input_before_cutoff=true，未知為 null；
  不換期、不擴窗、不加等待。即使 matched 也不是多檔交易或歷史日 coverage 證明。
- RoundHealth 的 site_counts（群組／獨立來源觀測）、child_counts（子來源觀測）分開；
  groups_with_children 記有子列的群組數，不將二層數量相加冒稱來源總數。
  每組計數七個互斥狀態：successful、healthy_zero、failed、partial、skipped、disabled、unknown。
  healthy_zero 須 ok=true 且非負整數 item_count=0；缺／非法 count 不假定零則。
  partial 為 ok=true 搭配 degraded／正 partial_failures 或失敗子來源。
- disabled／skip 優先於歷史 ok/degraded；attempted=false 無明確 skip/disabled 為 unknown。
  父群組 skip/disabled/未嘗試會覆蓋其子列，避免舊子列成功被當成本輪成功。
  沒有重放 last_attempt_ok／persistent_failure 等历史；空 sites 表示零個觀測，非全成功。
- provider_states 僅固定 x_api/socialdata/tikhub/rss_opml 四鍵的 availability：
  disabled/skipped/enabled/unknown。enabled 不代表成功；此層不再加到 site_counts。
  不匯出來源 ID/name、原始 reason/error/path 或任意輸入字串；不加總 item_count 冒稱
  fetched_raw_items 或獨立文章數（D03 沒有保留頂層 fetched_raw_items）。
- notices 為 D08 映射受控文案的代碼：永遠包含 health_not_window_coverage、
  archive_not_new_fetch；視情況包含 input_before_cutoff、archive_as_of_unknown、
  health_missing/invalid/mismatched/unverifiable/shape_unknown、source_failures、source_status_unknown。
  前兩者表示「健康為單次觀測，非整日覆蓋率」與「留存新聞不代表本輪新抓取」。
  其餘分別提示截止前快照、未知時間、健康不可用／不同輪、部分或完全失敗、狀態未知。
  D08 不自行增添查證／覆蓋率／新採集保證；input diagnostics 留 composer 合併。
- 聚焦 **77 passed**（D07、D03 loader、既有 source_health）；新模組與生成器語法、
  差異格式通過。隔離新接口未修改共享 schema/生成/scoring，未重跑完整 suite。
  正式資料／來源／workflow 未改。交接證據：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D07-20261002-224029/`。
- 下一項 D08／GPT-6 Luna／Medium：candidate、selection 與 health 接口已明確，
  可做純 Markdown renderer、必要文案及 escaping；不接 fetch/LLM/CLI。

### D08 — Markdown

- 範圍：繁中日期／窗口標示、入選新聞、現有可用摘要、可點原文與必要限制。
  記錄出版者摘要與 AI 摘要的來源型別；不產生未支持的評論或查證結論。
- 完成：空日、單則、多源、缺摘要、來源文字含 Markdown 特殊字元可讀且可追溯；
  英文無既有譯文時如實保留，不能宣稱無網路第一版可補齊所有繁中翻譯。
- 交接：render signature、樣本、來源連結檢查、D09 所需錯誤／metadata。

#### D08 已實作接口與驗收（2026-10-02）

- 新增 `scripts/digest_render.py`；`render_digest(document) -> str` 接受 JSON-safe
  mapping，讀 `window`、D06 `candidates`、D07 `health` 與可選 `diagnostics`，回傳
  繁中 Markdown。renderer 純格式化，不抓取、不呼叫模型／翻譯、不排序、不補摘要。
- 窗口必須有日期與 aware、遞增的 `start_utc/end_utc`；輸出期別與 UTC 範圍。候選依輸入
  順序保留，標題缺失報 `RenderError`；空候選合法並輸出空日文案。
- 標題、摘要、來源名稱及健康文案做 Markdown inline escaping；原文連結只接受
  `http://`／`https://`，其他 URL 不產生 link target。缺摘要明示沒有可用 publisher
  摘要，缺來源明示未標示來源；不創作新聞內容。日期無法解析顯示日期未知。
- 來源證據逐 ref 保留 title、URL、publisher、日期；沒有合法 URL 仍保留文字，不輸出
  `javascript:` 等 scheme。health 僅映射 D07 allowlisted notice code 到固定繁中句子，
  不把原始 error、site ID、path 或未知 code 帶入；mismatched／unverifiable 明示未附統計。
  diagnostics 只顯示固定生成備註標題，不顯示 raw code/count。
- `RenderError` 對無效 document/window/candidate 安全失敗；輸入不變且同一 JSON-safe
  輸入確定輸出。D09 可直接組合 candidate／health 並將 renderer 輸出寫入日報 Markdown；
  renderer 不負責 sidecar identity、原子寫入或 CLI exit code。
- 聚焦 **115 passed**（D08、D07、D05、D06）；`py_compile` 與 `git diff --check`
  通過。新增模組未改共享生成／schema／scoring，未重跑完整 suite；正式資料、來源、
  workflow 未改。交接證據：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D08-20261002-225500/`。
- 下一項 D09／GPT-6.1 Sol／Medium：CLI、日期參數、文件 identity、原子雙檔寫入與重跑
  行為；須保持 renderer 純函式與 D07 受控文案界線。

### D09 — 本機 CLI 與輸出

- 範圍：獨立日報 entrypoint，`--date`、明確 input/output 參數、日期檔名；
  預設生成文件與過程產物寫 Downloads，不寫 `data/`／`item/`。
  使用現有 atomic writer，不在現有 news main() 加強制日報分支。
- 完成：固定輸入同日重跑一致；寫入／replace 失敗保留舊文件；
  provider／輸入失敗不發布正常完成文件。若輸出多檔，明示單檔原子性並檢查共同
  generation identity，不聲稱跨檔交易。無 key、無網路也能產生基本日報。
- 交接：可直接執行的命令、exit codes、目標檔案清單、失敗恢復與重跑規則。

#### D09 已實作接口與驗收（2026-10-02）

- 新增 `scripts/digest_document.py` composer 與 `scripts/generate_digest.py` 離線 CLI。
  `build_digest_document(snapshot, window, *, limit=20, same_source_penalty=0.03)`
  依序接 D04 stories、D05 adapter、D06 selection、D07 health；輸出 JSON-safe dict，
  含 schema_version=1、pipeline_version=daily-digest-v1、render_version=markdown-v2、
  window、inputs/fingerprint、settings、selection_counts、candidates、各階段 diagnostics、health。
- `input_identity` 為 canonical JSON SHA-256：包含三檔 bytes fingerprint、期別、版本、
  有效選題設定及完整衍生 document，排除 input_identity/markdown_sha256 本身；
  不含路徑、mtime、執行 clock 或 Git HEAD。不同快照即使沒有候選變化仍可改 identity。
  pipeline/render 行為演進需更新版本；衍生内容亦納入 identity，不能借既有身份保證新版本。
- CLI 必填 `--input-dir`；`--date` 預設臺北當天（一次捕捉 clock）、
  `--output-dir` 預設 `~/Downloads/ai-news-radar-digests`；可傳 `--limit` 與
  `--same-source-penalty`。輸出不得位於輸入目錄樹或本專案 data/item；resolve 後檢查。
  exit 0 成功含空日／optional 降級，2 日期／CLI 參數錯誤，1 輸入／建構／寫入／核對失敗。
  stdout 只記期別／identity，stderr 固定安全錯誤，不披露原始 exception。
- `write_digest(document, output_dir)` 先驗 identity／日期、render 與 JSON serialization，
  再重用 archive_output.atomic_write_text，依序寫 digest-YYYY-MM-DD.md／.meta.json。
  Markdown 頂端 HTML comment 與 sidecar 含相同 identity，sidecar 另記完整 Markdown SHA-256。
  `verify_digest_pair(md_path, meta_path)` 同時檢查兩檔身份、Markdown hash 與 metadata 身份重算。
- 單檔 replace 失敗保留該檔舊值並清掉本次 temporary file；第二檔失敗時第一檔可能已更新，
  這不是跨檔交易，CLI 不宣告成功。核對拒絕不一致，重跑完整兩檔恢復。
  render／必要 input／serialization 失敗發生在寫入前，既有成功配對保留。
  沒有多 writer 鎖、簽章或人為編輯回寫機制；人工校稿後原 SHA 不再匹配，正式交付另存副本。
- 發現並修正 D08 的確定 bug：含括號 URL 改 percent-encode 避免破壞 destination；
  顯示文字 collapse 換行並 escape HTML，避免原文 HTML／換行插入頁面結構；URL 須有 host。
  新增回歸測例，D08 歷史交接維持當時結果。沒有修改公開 reader／原生成器程式。
- 聚焦 **209 passed**（D09 與 D03～D08 相關模組）；新 composer/CLI/renderer 與
  原生成器語法、diff check 通過。隔離日報路徑，未重跑完整公開 suite；D10 留完整整合複核。
  正式資料／來源／workflow 未改；無 provider／網路／commit／push／部署。
- 實際命令、環境、起點與交接：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D09-20261002-232821/`。
  下一項 D10／GPT-6.1 Sol／High：獨立複核端到端失敗、晚發現、證據窗口、
  HTML/Markdown、可重現性與公開相容性，不能只以本次聚焦結果當整體交付驗收。

### D10 — 整合驗收

- 範圍：日期窗口、空日、晚發現、壞輸入、health 不一致、來源全失效、
  證據連結、重跑、中斷寫入與公開相容性；只用離線 fixtures。
- 完成：聚焦測試通過；共享 generation/schema 行為有改動則完整 Python suite；
  合適的語法檢查與 `git diff --check`。正式 JSON／來源設定／workflow 未改。
- 交接：實際命令與結果、未測外部行為、回滾所需檔案；不要以現有測試通過
  代替新日報的行為證據。

#### D10 已實作與整合驗收（2026-10-02）

- 新增 `tests/test_digest_integration.py`，串真實 loader/composer/renderer/writer/verify/CLI，
  只用 example.invalid 合成資料。F01～F19 對照與確切 test entry 保存於交接目錄
  `ACCEPTANCE_MATRIX.md`，區分原單元證據與新增端到端證據，不將既有公開測試代替日報驗收。
- 端到端涵蓋起點含／終點不含、窗外同事件不混入、截止後發現的窗內新聞、同日價格摘要
  與新增事件改稿、空／窗外／非 AI、健康全失效或不同輪仍保留可用新聞、截止前快照與
  單次預設日期、record 順序改變證據不變而 bytes identity 改變、CLI 真實 exit 1/2。
- 無 key／假 key 都封鎖 requests、socket.create_connection、news main/collect_all/
  add_bilingual_fields/summarize_stories，真實非空題可生成且輸入 bytes 不變。
  模擬程序在第一次 atomic replace 完成後直接 exit 73：不報成功、保留舊 sidecar、
  核對拒絕不一致，重跑恢復。stream.write 故障保留兩份舊成功檔並清理 temporary file，
  CLI 固定錯誤不暴露 exception 私密字串；D09 原 replace/tamper 回歸亦通過。
- 首次兩個新端到端測例重現 renderer 缺口：臺北凌晨日期顯示成前日 UTC；快取摘要
  缺稿面 provenance 標示。修正新聞／來源日期為臺北日期、窗口顯示本地 06:00～06:00、
  出版者摘要／既有快取譯文標示與段落分隔。renderer 亦核對期別真正固定窗口，拒絕錯一日／
  非法日期；非空摘要缺 publisher/publisher_translation kind 安全失敗，不冒稱出版者內容。
- render_version 更新 `markdown-v3`，身份隨版本改變；schema/pipeline 仍 1/daily-digest-v1。
  D08 renderer fixture 原把 10/2 窗口錯放晚一日，已改實際契約日期；歷史交接不改寫。
- 最終日報聚焦 **281 passed**、完整 Python suite **809 passed**；全部日報模組與
  原生成器 py_compile、diff check 通過。使用 bundled Node PATH 完成既有前端測試。
  首次刻意重現的 **2 failed** 與後續完整成功 log 全保留；無未處理失敗或待續程序。
- 僅日報 renderer/版本、其測試與交接文件改動，無公開生成器、source settings、正式 JSON、
  workflow、LLM、排程、commit/push/deploy。本驗收未測 live source/API 可用性、真 provider、
  斷電持久性、多 writer 交易或使用者人工校稿；這些不由離線測例保證。
- 證據與本階段六檔增量：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D10-20261002-233733/`。
  下一項 D11／GPT-6.1 Sol／Medium：指定實際一期、固定输入副本、生成配對核對、人工校稿
  與空日樣本／操作說明；D10 通過不代表已交付使用者的真實新聞稿。

### D11 — 人工交付

- 範圍：指定一期的本機日報、空日 fixture、使用說明、重跑說明。
  暫存及可審閱產物放 Downloads，專案內只保存穩定接口／操作文件。
- 完成：使用者能開啟文件校稿，每題可點回證據；明確列出仍未啟用的 LLM、
  排程與部署。正常日報可供人工發布，不自動發到平臺。
- 交接：可開啟的日報與命令；下一步依實際剩餘缺口推薦 L01、B 任務或 O01，
  不自動將所有 optional 功能推進。

#### D11 本機交付與驗收（2026-10-03）

- 使用者未指定期別，按 D10 交接先交 2026-10-02 真實資料草稿，另交客戶日期
  2026-10-03 當期結果。三檔固定副本與 manifest 在 Downloads；沒有修改正式 input。
  archive/health as-of 為 2026-10-01T15:11:39.533997Z（臺北10/1 23:11），
  早於兩期截止；cache unversioned，副本非多檔交易證明。
- 10/2 草稿 89 個故事候選、8 題過門檻／入選；摘要 5 題 publisher_translation、
  2 題 publisher、1 題 none。10/3 當期無窗內題目，依過舊輸入呈現空日，
  不能推論當天沒有 AI 新聞。另有獨立 synthetic 空日（as-of 到截止），不混當真實新聞。
- MD/meta 三組共同 identity/hash 核對、期別／來源發布窗口／主來源摘要 provenance、
  URL 格式與 renderer 對應驗收；同固定輸入重跑檔案 bytes 不變。
  生成配對保留，另存 10/2 校稿副本與 REVIEW_NOTES；尚未替使用者完成人工校稿或發布。
- 校稿發現第6題為提示詞教學，建議人工移除；第4～8題多個 refs 都指向各自同一
  出版者／URL，不是獨立查證。部分摘要等同標題／缺摘要；Google News 連結可能跳轉。
  本階段不改評分、選題或來源去重，缺口列作後续產品討論，不以8題宣稱全部刊出合格。
- 新增穩定操作文件 [DIGEST_USAGE](DIGEST_USAGE.md)：專案 Python、生成／核對／重跑／
  失敗恢復、資料時效及校稿副本；系統 Python 3.9 初次 import 失敗已記錄，改 .venv 恢復。
  程式碼無變動，沿用 D10 全套 809 passed，不冒稱 D11 重跑全套；正式 data/feeds/workflow
  未動，未呼叫 provider/抓取/commit/push/deploy。
- 交付與證據：
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261003/D11-20261003-061422/`。
  D01～D11 基本離線流程完成；下一項建議 O01／GPT-6.1 Sol／Medium，先評估資料更新、
  上午生成與人工交付的提案。O01 仍 conditional，沒有授權啟用排程／部署；
  LLM 與其他來源不自動推進，B01～B03 未修。

## 獨立與條件任務卡

| ID | 最小範圍與驗收；交接給下一項的必要資訊 |
| --- | --- |
| L01 | 小型 replaceable synthesis callable，先 stub。候選／token／呼叫上界明確；不重新摘要每篇。輸出草稿＋狀態，failure 不覆蓋成功文件。交付 provider interface 與 prompt version。 |
| L02 | schema、來源逐題對應、數字／版本／供應商歸因、prompt injection、timeout／malformed 輸出 fixtures。規則檢查不宣稱完整事實查證。交付失敗矩陣與未涵蓋語義風險。 |
| L03 | 另行核准真實 provider／模型／token與費用上限後才呼叫；少量樣本逐題比對來源。交付輸入條件、用量、結果及禁用／啟用建議；不憑 stub 宣稱 provider 合格。 |
| O01 | 先提出生成時點、上午審閱交付、失敗處理、Downloads／CI artifact 或其他保存路徑。現有 Actions 不保證準時，GitHub runner 也沒有本機 Downloads。核准後才改／啟用生成排程或部署；11:30 仍為人工發布目標。 |
| B01 | `fetch_opml_rss()` 已重現 HTTP 200 非 feed HTML 被判 healthy zero。辨識有效空 feed 與不可用文件，沿用健康契約；回歸 malformed／empty／missing fields／成功 peer，勿把正常低頻變失敗。 |
| B02 | `normalize_creator_metrics()` 已重現 `{}` → 四項 0。界定 missing／0／平臺原始欄位，檢查 public consumers 相容性；不要將既有 0 值猜回 missing，也不改新聞評分。 |
| B03 | `fetch_socialdata_search()` 在空頁＋不同 cursor fixture 已走過 12 頁，直到 harness 第 13 次強制停止；不是 live cost。限制 page／raw reads，成本不以 retained item cap 冒充 hard ceiling；保留可用結果與 truncation 診斷。 |
| S01 | 只定義 snapshot contract；`platform + external_id` 身分、content／URL／發布與取得時間、nullable current metrics、providers provenance。欄位僅來自實際 payload，與新聞 ID 分開，無 velocity state。 |
| S02 | 在 X payload 資訊被截斷／丟棄前正規化，API＋SocialData 同 post 合一、provider provenance 皆保留；RawItem 與公開新聞輸出兼容。Fixture 驗證跨 provider、缺字段、同數字不同平臺不碰撞。 |
| S03 | Douyin／Xiaohongshu current metrics、推定日期標示、URL 與來源保留；跨平臺計數不可共用熱度尺度，missing 不轉 0；不存 raw 長期 payload。 |
| S04 | 先取得既有 Social Editor 輸入契約；匯出 news/social refs、證據、選擇理由、限制，不復制 Full/Brief/Drop 編輯邏輯。沒有完整正文／replies 要標示；檔案可直接人工消費。 |
| S05 | 先明確帳號／關鍵字／討論等用途，再查官方 endpoints、權限、審查、metrics 範圍、quota／token／保存限制。本輪 Meta 文件曾 429／無法讀取，不能以第三方描述當核准結論。交付 capability 表與可行／缺口。 |
| S06 | S05 可行才做 disabled-by-default read adapter；pagination caps、health isolation、auth／429／schema fixtures，無 publishing scopes；missing key 不影響日報或 core news。 |
| M01 | 以真實近期 records 找 provider/model alias 錯配，列出有影響的具體 consumer；不只數不同拼字。交付最小 aliases／歧義樣本與預期收益。 |
| M02 | 只實作 M01 證明需要的 aliases；exact／normalized／ambiguous／unknown；先接一個低風險 consumer，不改 archive 與既有發布 ID。 |
| E01 | 逐來源增益、日期、來源身分、重疊、terms與單輪上界；RSSHub route 若有用才評估，區分代理 RSS 與 API／HTML。此任務不部署 RSSHub，也不自動註冊來源。 |

## 交接協定

### 2026-10-03 O01 後續改在GitHub驗證

- 使用者明確要求O01之後在GitHub繼續驗證，覆蓋先前本機排程後續安排。
- 新增Daily digest validation與安全驗證入口：07:15／08:15兩次獨立觀察，固定SHA、
  時效／pair核對與同bytes重跑；草稿與輸入在runner暫存，用完清除、不upload artifact。
- 公開只留受控Step Summary；私人交付仍由本機手動入口執行，沒有本機automation或自動發文。
- github_observing表示流程已轉GitHub並待三日schedule證據；不能以workflow_dispatch取代。
  [驗收條件](DIGEST_GITHUB_VALIDATION.md)，下一階段GPT-6.1 Sol／Medium。
- 交接：`/Users/lordmi/Downloads/ai-news-radar-digest-20261003/O01-GITHUB-20261003-073958/`。


### 2026-10-03 提交前全專案複查

- 使用者授權全專案複查、既定範圍修正與準備commit/push；無新來源、選題門檻或排程擴充。
- B01～B03已修正：OPML沿用既有feed驗證；TikHub缺值null／真零保留；SocialData
  搜尋最多10頁，觀測raw reads達100停止下一請求（整頁可超過），不冒稱保留數為帳單上限。
- 新增來源邊界回歸；本機交付失敗也不再留下ready標記的staging manifest。
- 全專案證據：`/Users/lordmi/Downloads/ai-news-radar-digest-20261003/PREPUSH-20261003-072022/`。
- O01仍為local_manual_ready；本機排程／3日觀察是下一項，GPT-6.1 Sol／Medium。


### O01 本機方案已選、手動入口實作（2026-10-03）

- 使用者「本機私人交付」授權採用本機路徑；新增deliver_digest手動入口與故障測試。
  固定遠端commit三輸入，不pull或改正式data；私人attempt／版本交付、截止／90分鐘gate、
  pair核對與同期flock，保留人工稿。不改離線generator的exit0／選題契約。
- 下載具45秒curl／50秒外層硬逾時；初次urllib真實下載卡住已停止並修正，證據保留。
- local_manual_ready不表示排程已啟用；尚無automation／通知／LLM／push／公開artifact。
  下一階段GPT-6.1 Sol／Medium：手動交付審閱後，設定本機時刻與執行權限、觀察3日。
  交接目錄：`/Users/lordmi/Downloads/ai-news-radar-digest-20261003/O01-LOCAL-20261003-065944/`。

### O01 提案完成、啟用待核准（2026-10-03）

- `run o01` 完成唯讀現況診斷與 [具體交付提案](DIGEST_OPERATIONS_PROPOSAL.md)，未啟用
  排程或部署。proposal_ready 表示提案已可審閱；O01整項尚未done，實作／3日啟用驗收待核准。
- 本機data as-of臺北10/1 23:11，遠端固定commit c32d582705a7ea54ca241cfe50afb914753cbdb8
  archive/health同為臺北10/3 06:05:32；這次D11空日源於本機落後，非遠端停止抓取。
  日報CLI在該遠端commit尚不存在，CI須先另核准日報程式發布，不可直接依賴未提交本機檔。
- 建議CI獨立唯讀生成：07:15主、08:15備援、09:00人工檢查、11:30人工發布；
  固定commit三輸入／安全manifest，不pull dirty worktree。資料門檻屬交付guard，不改06～06收錄窗口。
  artifact只保存MD/meta/manifest7天；公開repo草稿可見性須接受，否則選本機私人交付。
- 本輪只改proposal／operations／plan／handover文件，證據在
  `/Users/lordmi/Downloads/ai-news-radar-digest-20261003/O01-20261003-062352/`。
  未fetch/pull、刷新來源、dispatch、修改workflow、建立automation、commit/push或部署。
  下一階段O01實作／GPT-6.1 Sol／High，須先核准渠道、時效／時刻與CI程式發布。

### 每一小任務的起點與終點

1. 依序讀 `AGENTS.md`、HANDOVER 最新檢查點、本任務卡及必要模塊權威。
   只讀當前範圍，不重新做全 repo 或 hash sweep。
2. 核對 branch／HEAD／工作區，記下既有修改；在 Downloads 建唯一的任務證據
   目錄並寫 `CHECKPOINT.md`，先記 planned action 與 resume action，再開始修改。
3. 一次只做可恢復的小步。每個完成的檔案羣組、驗證結果或取捨後更新檢查點；
   長時間或有外部影響的操作開始前先記命令／目標／是否可重試。
4. 任務完成或需停止時，按模板寫交接。命令、測試與結果須實際保存；
   長 log 引用檔案，repo 內摘要只留必要資訊，不含 tokens、keys或私人 feed。
5. 更新本臺帳狀態；HANDOVER 最新節記本任務、證據目錄、下一個 ID／動作與
   建議模型／思考及理由。完成的 checkpoint 才標為 done。
6. 最終回覆一定顯示：完成什麼、證據位置、仍未完成什麼、下一任務 ID、
   推薦模型／思考及理由。不自動切模型、另建聊天或啟用排程。

例證據目錄：
`/Users/lordmi/Downloads/ai-news-radar-digest-20261002/D02-<唯一時間>/`。
採用 atomic temp-write＋replace 保存 `CHECKPOINT.md`；完成交接檔另存
`HANDOFF.md`，不要覆蓋上一項的證據。不因交接而自動 commit／push。

### 額度中斷、換聊天或 process 非預期結束

- 不承諾能在硬中斷前再補一份完整交接，所以起點就先落檔，每步都增量更新。
- 新聊天入口只需：`依 docs/HANDOVER.md 最新檢查點續接，先恢復未完成任務，
  遵守 docs/DIGEST_PLAN.md 與 docs/TASK_HANDOFF_TEMPLATE.md。`
- 若最後狀態是 in_progress 或 pending command，先查看實際檔案與 diff、
  output／log及仍存在的 session 狀態。未確認結果記 unknown，不能當成功。
- 未完成不代表需重做全部。保留現有 diff，不用 reset、clean、stash 或刪目錄
  來「恢復乾淨」。只從最後已驗證步驟之後續做。
- 有費用／外部影響的呼叫若結果不明，先查是否已執行；不盲目重跑而重複計費。
  未核准的 paid／push／部署／排程操作仍未核准。
- Downloads 若在另一部主機不存在，repo 內的狀態／取捨仍能恢復，但缺原始證據
  的驗收要標未核對；有必要才重跑安全離線檢查，不以記憶補造結果。

## 模型與思考強度選擇

2026-10-02 本機工具提供 GPT-6.1 Sol、GPT-6 Astra、GPT-6 Luna 等選項；
實際可用性以續接時 client 選單為準。
[OpenAI 官方 model selection](https://developers.openai.com/api/docs/guides/model-selection)
將 Sol／Medium 列為複雜技術工作起點，Luna 用於較明確的小範圍工作。
表中是依本專案風險作出的建議，不是官方對此 repo 的 benchmark。

- 一般 adapter、日期、CLI、測試與文件：GPT-6.1 Sol／Medium 起步。
- 已定義接口的 renderer／單純文件整理：GPT-6 Luna／Medium 或 Low。
- 時間、身分、去重、費用上界、schema相容與完整驗收：GPT-6.1 Sol／High。
- 只有跨多模組仍有矛盾、前述模型未能解決的複雜問題，才評估 Astra／Medium
  或提高思考；不預設每個小任務都用最高強度。
- 每次交接重新評估下一個實際剩餘步驟，記原因與可降級條件；不機械沿用表格。
- 這是執行任務的 Codex 模型建議，不改網站 Groq／Gemini 設定或未來日報 provider。

## 參考交接檔與被取代內容

- `/Users/lordmi/Downloads/AI_NEWS_RADAR_CODEX_TASK_BREAKDOWN_2026-10-02.md`：
  原 WP0～WP8 拆解；WP5 與對應 metrics-state patch 已從本計畫移除。
- `/Users/lordmi/Downloads/AI_NEWS_RADAR_SIGNAL_DIGEST_CODEX_SUPPLEMENT_REDDIT_RSS_RESILIENCE_2026-10-02.md`：
  snapshot 方向、RSS-zero 壓力測試與取消 velocity。其引用的 9/30 父檔未在
  本輪提供，不假定取得該檔或 Social Editor 私有規則。
- 本聊天使用者後續明示：06:00～06:00，沒有其他時間規則；設計允許，
  要小任務、持久交接與每階段模型／思考建議。優先於前面 03:00／32h／8h 草案。
