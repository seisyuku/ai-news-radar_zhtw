# S01來源與正式狀態基準（2026-10-21）

## 固定版本與證據邊界

- 正式專案：`/Users/lordmi/Documents/ai-news-radar_zhtw`，本機分支`master`。
- 本機HEAD／本機origin/master：`3ac92d087586afd1fc2dec7f6c2b3d69c8177074`。
- 本次唯讀GitHub master：`72d20f0195764ed40223c52455685c716e6fea4f`，領先11個提交。
- 完整頂層Git tree只有`data`、`item`不同，其餘路徑相同；七份workflow blob亦逐一相同。
- compare API只回傳300個檔案，未用截斷清單斷言程式相同，以完整頂層tree確認。
- 正式來源／AI讀者資料時間：`2026-10-21T14:58:04.963406Z`，臺北10/21 22:58:04。
- 這是固定時點證據；沒有重抓出版者來源、執行生成器、七日觀察或逐篇品質查核。
- 近期正式刷新及此版本Pages部署成功；本步未另開瀏覽器作實際畫面驗收。
- 原始安全摘要／AST盤點／hash在Downloads `ai-news-radar-source-governance-s01-20261021/`。

## 實際收件名冊

依`collect_all`、群組fetch實作、tuple之外的頁面、main後接感測器及條件式路徑盤點。
12個內建收件任務展開為40個邏輯收件列，另有4個感測器與OPML。這不是40個
獨立出版者、URL或HTTP請求數：AIBASE含兩種語言列表，OPML亦可能重疊。
每列URL與實作入口保存在Downloads的`SOURCE_INVENTORY.json`，未讀私人OPML。

| 任務 | source_id | 入口類型 | 本次健康 | 來源窗口內篇數 |
| --- | --- | --- | --- | ---: |
| official_ai | openai_news | 原生RSS | 成功 | 102 |
| official_ai | google_deepmind | 原生RSS | 成功 | 13 |
| official_ai | google_ai_blog | 原生RSS | 成功 | 18 |
| official_ai | google_gemini_blog | 原生RSS | 成功 | 20 |
| official_ai | hugging_face_blog | 原生RSS | 成功 | 28 |
| official_ai | github_ai_ml | 原生RSS | 成功 | 10 |
| official_ai | github_changelog | 原生RSS | 成功 | 10 |
| official_ai | openai_skills | commit Atom | 成功 | 0 |
| official_ai | thinking_machines_lab | 原生RSS | 成功 | 0 |
| official_ai | nvidia_blog | 原生RSS | 成功 | 18 |
| official_ai | microsoft_blog | 原生RSS | 成功 | 8 |
| official_ai | aws_news | 原生RSS | 成功 | 100 |
| official_ai | google_cloud_blog_news | Google News生成feed | 成功 | 3 |
| official_ai | anthropic_news | 固定公開頁面 | 成功 | 13 |
| official_ai | tencent_newsroom | 固定公開頁面 | 成功 | 8 |
| official_ai | openai_codex_changelog | 固定公開頁面 | 成功 | 22 |
| mistral_news | mistral_news | 原生RSS | 成功 | 8 |
| mcp_blog | mcp_blog | 原生RSS | 成功 | 0 |
| arc_prize | arc_prize | 原生RSS | 成功 | 0 |
| curated_media | the_decoder | 原生RSS | 成功 | 10 |
| curated_media | techcrunch_ai | 原生RSS | 成功 | 8 |
| curated_media | the_verge | 原生RSS／嚴格標題篩選 | 成功 | 1 |
| curated_media | marktechpost | 原生RSS／研究篩選 | 成功 | 6 |
| curated_media | cnbc_technology | 原生RSS／嚴格標題篩選 | 成功 | 6 |
| curated_media | reuters_ai_news | Google News生成feed | 成功 | 10 |
| curated_media | the_information_news | Google News生成feed | 成功 | 10 |
| curated_media | meta_ai_news | 第三方報導查詢 | 成功 | 8 |
| curated_media | deepseek_news | 第三方報導查詢 | 成功 | 8 |
| curated_media | xai_grok_news | 第三方報導查詢 | 成功 | 8 |
| curated_media | epoch_ai_news | Google News生成feed | 成功 | 8 |
| llm_stats_models | llm_stats_models | 公開頁面結構化資料 | 成功 | 6 |
| llm_rumors | llm_rumors | 原生RSS | 成功 | 6 |
| runtimewire | runtimewire | 原生RSS／只收文章 | 成功 | 1 |
| aibase | aibase | 公開列表資料／繁中＋英文 | 成功 | 40 |
| tw_media | inside | 原生RSS | 成功 | 5 |
| tw_media | ithome | 原生RSS | 成功 | 8 |
| tw_media | technews_tw | 原生RSS | 成功 | 8 |
| tw_media | bnext_news | Google News生成feed | 成功 | 8 |
| kr36_ai | kr36_ai | Google News生成feed | 成功 | 5 |
| juya_daily | juya_daily | 原生RSS／整期對照源 | 成功 | 5 |

13個official feed之外，另有Anthropic、Tencent及Codex Changelog三個頁面，不能漏算。
Google Cloud位於official群組，但運輸是Google News，須分開判斷文章發布者。
Mistral／MCP／ARC已是正式任務；ARC仍是第三方評測身分。
AIBASE任務健康獨立列示，但RawItem沿用`curated_media`／AIBASE身分。
36Kr正式路徑為Google News，保留直接feed常數不代表每輪先抓直接站。

來源窗口內篇數不等於24小時新事件數；零則成功可為有效空feed／低頻，不視為故障。

## 感測器與可選路徑

| 路徑 | 本次狀態 | 盤點邊界 |
| --- | --- | --- |
| LLM Price Tracker | 成功，64個模型 | 第三方結構化價格，不是一般新聞；不保證完整市場覆蓋。 |
| Free LLM APIs | 失敗，free_tier_model_description_not_identifier | 連續991次嘗試失敗，不是991個唯一排程；修復／移除尚未裁決。 |
| Usage4Claude／Claude Usage Monitor | 各成功20筆來源紀錄 | commit Atom候選線索，不是20則已確認政策變更。 |
| OPML | enabled，10個有效入口／10成功 | workflow從secret或公開example取得；本步未讀私人內容或辨識secret來源。 |
| X API／SocialData／TikHub | 本次均disabled | main內有條件式路徑，保留能力不代表當期啟用；未讀憑證。 |
| Telegram／Jike | OPML可路由的公開頁面adapter | 未核實10個OPML的逐項類型，不聲稱當期有啟用bridge。 |

OPML身分與內容仍未審查；正式規則評估前須凍結當時啟用名冊，未知部分明列，
不得用本表聲稱全站內容母體已完整人工驗證。

## 已部署變更的本次確認

- curated_media列不含已移除的VentureBeat AI、Artificial Intelligence News及LMArena。
- INSIDE成功5篇，182篇AI列表內有4篇；代表進入讀者資料，不代表逐篇事實已審。
- RuntimeWire成功1篇；本次`items`及`items_ai`沒有`/models/`。未驗全部列表與跨日期品質。
- Anthropic成功13篇，對應45日收件窗口，非24小時新增13篇。
- AI列表與來源健康同一generated_at，未把其他時點archive混稱同輪基準。

## 本機差異與未部署成果

起始差異只有HANDOVER既有77行增加，以及觀察工具／測試／說明／docs examples等
未追蹤檔案。確切清單及起始diff保存在INITIAL_STATUS.txt／INITIAL_DIFF.patch。
這些內容本輪保留；准入工具已在HEAD，七日協調／Actions／Email工作只在本機。
plan仍disabled，日期／code SHA／workflow指紋未指定，草稿jobs仍硬性false；
兩個TW觀察workflow不在固定遠端workflow目錄。本步不重新驗收先前測試數。

## 日報與遠端查核限制

- 生成workflow仍有workflow_run，驗證workflow仍有兩個cron；線上workflow檔blob相同。
- 近期日報run `39622821628`為workflow_run／skipped，不能作停用或當期派送成功證據。
- connector拒絕workflow狀態目錄與單一workflow狀態端點，未取得全部active／disabled清單。
- 私人Drive設定未讀；歷史true不等於本次讀回。在途run及私人設定須在D00實作時查核。
- [D00退役範圍](DIGEST_RETIREMENT_HANDOFF_20261021.md)與[整體台帳](SOURCE_GOVERNANCE_PLAN_20261021.md)為下一步入口。

## 受保護項目

S01不改scripts、tests、既有workflow、data、item、assets、index、私人OPML或設定。
以起始15077個tracked／非忽略untracked檔案hash核對，既有未提交觀察工具亦納入。
正式快照不因驗證覆寫；本機origin/master不因本次遠端讀取更新。
公開daily-brief／brief_selection屬Radar精選，日報退役時仍保留。

## 證據連結

- [固定遠端版本](https://github.com/seisyuku/ai-news-radar_zhtw/commit/72d20f0195764ed40223c52455685c716e6fea4f)。
- [固定正式來源健康](https://github.com/seisyuku/ai-news-radar_zhtw/blob/72d20f0195764ed40223c52455685c716e6fea4f/data/source-status.json)。
- [固定AI讀者資料](https://github.com/seisyuku/ai-news-radar_zhtw/blob/72d20f0195764ed40223c52455685c716e6fea4f/data/latest-24h.json)。
- [Pages部署成功](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39621718565)。
- [既有正式刷新成功](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39622529978)。
- [日報仍有自動觸發紀錄](https://github.com/seisyuku/ai-news-radar_zhtw/actions/runs/39622821628)。
