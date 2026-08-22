<div align="center">

# AI 商業情報雷達

**每 30 分鐘自動更新的 AI 產業商業事件儀表板 · 繁體中文特化 · 排除噪音看清事實**

[![直接使用](https://img.shields.io/badge/📡_直接使用-AI新聞儀表板-2d8f8f?style=for-the-badge)](https://seisyuku.github.io/ai-news-radar_zhtw/) 
[![GitHub stars](https://img.shields.io/github/stars/seisyuku/ai-news-radar_zhtw?style=for-the-badge&logo=github&color=f5b942)](https://github.com/seisyuku/ai-news-radar_zhtw/stargazers)

[English](README.en.md) · [維運文件](docs/OPERATIONS.md) · [來源治理](docs/SOURCE_COVERAGE.md)

</div>

---

## 這裡提供什麼

本站自動彙整全球 AI 廠商公告與產業媒體報導，並以**六類商業事件**為核心訊號，命中的條目會標上類別徽章、優先出現在「今日重點訊號」區：

| 徽章 | 涵蓋範圍 |
|---|---|
| 財報營收 | AI 相關企業的財務數字、營收里程碑、IPO 動態 |
| 市佔格局 | 市場份額變化、併購案、反壟斷調查 |
| 資安漏洞 | AI 產品與服務的重大漏洞與資安事件 |
| 價格方案 | 模型與服務的定價調整、方案異動、優惠 |
| 評測基準 | 新模型 benchmark 成績、排行榜變動 |
| 模型發布 | 主要 AI 實驗室發布/開源新模型 |

重點區以下的一般列表收錄範圍較廣，涵蓋 AI 產業的產品發布、研究進展與趨勢報導，供延伸瀏覽。所有條目點擊即導回原始出處。

價格、免費額度與 rate limit 另由結構化資料快照比對；Claude／Codex
usage policy 的時效型線索放在獨立「額度與政策速報」區。速報只表示公開
第三方監測工具出現相關變更，會明確標示「待確認」，不等同官方公告。

首頁另有事件式「LLM 發布雷達」：只在過去 24 小時偵測到新模型時顯示，
並明示是官方公告、模型追蹤或媒體報導，不會把單一報導偽裝成官方發布。
模型價格與免費額度異動則集中在「價格與免費額度變更」區。

## 這裡不提供什麼

- 程式開發教學、prompt 技巧、工具使用心得
- 社群論壇的討論串與意見風向
- 個別開發者的實作分享

一句話：這裡關注「**AI 產業發生了什麼商業事件**」，不是「怎麼用 AI 寫程式」。

## 資訊來源與可信度

來源分層治理，頁面上的來源徽章反映其層級：

- **官方一手**：OpenAI、Anthropic、Google DeepMind／Gemini、NVIDIA、Microsoft、AWS 等廠商官方頻道
- **國際財經與產業媒體**：Reuters、CNBC、The Information、TechCrunch 等
- **台灣媒體**：iThome、TechNews 科技新報、數位時代
- **評測第三方**：LMArena 等 benchmark 機構
- **觀察名單**：訊噪比評估中的來源，權重較低並明確標示
- **對照源**：人工策展日報，用於查漏比對，不參與重點排序

**已知非本專案導致的外部失效問題**：
- 部分廠商新聞（Meta AI、DeepSeek、xAI）動態來自第三方報導而非官方一手可能出錯，請自行驗證可信度
- 簡體來源經 Google翻譯自動轉換為繁體，偶有中文字轉換瑕疵
- GitHub actions bot最近不穩定，每30分鐘的排程無法保證隨時都會正常觸發，請隨時注意頁首時間軸及更新失效警示

## 運作方式

全站為純靜態網頁，由排程自動化驅動：每 30 分鐘抓取新聞與公開 Sensor、過濾 AI 相關性、識別商業事件、統一轉換為臺灣繁體中文後發布。重點卡片在來源有提供摘要時，會以 Groq 上的 `qwen/qwen3.6-27b` 產生短篇 AI 新聞摘要；無憑證、額度不足或服務失效時會沿用快取或省略該區塊，不影響新聞更新。無伺服器、無資料庫、無追蹤，你看到的就是全部。

## 回饋（內測期間）

發現分類錯誤、不該出現的內容、或你認為漏掉的重大事件，歡迎回報。**回報時請附上頁面最底部的版號**（如 `taste-ui-0716a`），這能幫助快速判斷問題成因。
> 回報管道：[提交 Issue](https://github.com/seisyuku/ai-news-radar_zhtw/issues/new?template=feedback.md)

> [!TIP]
> **覺得這個儀表板有用？點顆 ⭐ 讓我知道！**
> Star 數是我判斷「該不該投入更多維護與新功能」的主要訊號——
> 你的一顆星，直接影響台灣媒體源擴充與 LLM 智慧排序的開發優先序。

## 致謝與授權

本專案 fork 自 [LearnPrompt/ai-news-radar](https://github.com/LearnPrompt/ai-news-radar)（MIT License），在其基礎上重新自主設計了情報源結構、商業事件識別、虛假買榜排除與文章排序演算法，並對全站繁體中文化及加強資訊安全防護。感謝原作者的開源貢獻。

維運與協作細節見 [docs/OPERATIONS.md](docs/OPERATIONS.md)。
