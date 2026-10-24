# I01：D+後端與用途契約

狀態：本機後端完成，待I02前端接線及I03整體驗收。未提交、推送、部署或觸發刷新；正式站仍使用原規則。本文件及Downloads交接記錄取代本案先前「待確認」規格的I01部分，不重開PG05補修或其他擱置案。

## 問題與本輪範圍

使用者已同意D+並指定執行I01。原本合格的單一來源核心事件會被0.72重要性門檻擋住；另外兩則使用者指定報導揭露了新模型型號辨識與具體能力／安全披露的涵蓋缺口。

- 核心仍為財報、市場、資安、價格、評測、模型發布六類；材料supported、合格當期來源、事件對應及既有有效計數鍵保留。重要性只排序，不再作單一來源核心的硬門檻。
- 已符合核心資格者不受舊AI文章分類覆蓋；Kimi案例不能因research_paper標籤失去模型發布資格。
- 核心不足五則，才從當期具體產業動態補位；補位最多填到五則，不壓掉核心。核心超過五則仍保留，後端相容選集上限20。
- Anthropic案例走「能力／安全評估披露」補位，要求原始材料有具體測試、可識別方法／評估者及同段數據；保留provider_claim及unreleased標示，不當作公開模型發布或獨立查證。
- NVIDIA案例以完整、有版本的新名稱＋直接發布動作＋模型名詞說明取得核心資格；不是新增單一品牌白名單。否定、疑問、假設、文件／教學受詞與跨模型借材料仍受限制。

## 實作邊界

`scripts/signal_material.py`是新的用途材料層；`scripts/signal_selection.py`處理版本2資格、選集及一致性驗證。`update_news.py`預設使用版本2；`governance_version=1`只保留舊契約回歸入口，不是對外開關或混版fallback。

下列原模組／行為保持：

- `publisher_governance.py`、`publisher_material.py`及原來源准入registry不變；一般文章與雷達仍使用原資格／分類路徑。
- `brief_events.py`的matcher、事件根、成員、phase、時鐘及21日記憶不變。新用途層不把article根改造成model根，也不宣稱擴充了新型號的跨文章去重。
- AI相關度公式、0.65基礎門檻、一般AI文章與既有來源收集不變。
- 無新網路、跳轉、全文、LLM、摘要、排程或通知工作；補位只能沿用已存在且綁定相同主文的摘要，否則省略。
- 價格、兩Canary及退役日報／觀察保持。tracked `data/`、前端、資產版本與workflow未修改。

## I02必須接收的契約

用途投影仍位於`stories-merged.json.publisher_governance`，但現在是：

- `schema_version: 2`、`selection_policy: "dplus-v1"`、`default_visible_limit: 5`。
- `policy_id`及`registry_revision`仍表示原來源治理，沒有升級來源權限；`generation_id`改為`pg2_…`，仍綁定同代brief generation及state revision。
- JSON schema見[版本2](contracts/publisher-governance-v2.schema.json)。它透過URN引用不可變的[版本1](contracts/publisher-governance-v1.schema.json)身分／來源／材料定義；本機schema驗證須把v1註冊到`referencing.Registry`，不需遠端schema請求。

每個文章annotation保留`qualification`（六類核心），另有`supplement_evidence`：

- `kind`為null、`industry_news`或`capability_disclosure`。
- `spans`與`urls`指向保存的原始標題／摘要，不使用翻譯或生成摘要當證據。
- `qualifiers`可含`provider_claim`、`unreleased`。補位不是第七種核心徽章。

每個事件decision保留原用途欄位，新增：

- `selection_class`為null、`core`或`supplement`。
- `eligibility_basis`為null、`supported_core`、`industry_news`或`capability_disclosure`；版本2沒有`qualified_score`准入。
- `support_scores`記錄用途支持文章的有限重要性分數；`disclosure_flags`綁定選出的主文。
- `featured_business_events`只有核心可有六類徽章；補位必須為空。
- `qualified_source_count`及keys只計同層、當期、已准入且保有引擎有效key的支持文章；不借未審／過期／context引用取票。

**`featured_eligible`及`featured_event_ids`在v2代表完整D+候選，包括核心與補位；不能把它們全當成核心。** 所有可用補位候選都保留，即使首頁已滿五則。`daily_selected_event_ids`與`brief_events.selected_event_ids`是預設選集：先取核心（最多20），核心不足五則再補位。同層沿用重要性與同發布者0.03衰減，穩定事件ID破同分。

原事件reference另保存公開`source_links`與`source_site_name`，供無網路的材料／分類重算。它們不改事件身份或一般列表來源。驗證器會重算原始資格、主文與支持集合，核對keys、分層、分數關係、摘要、選集及hash；容量失敗／錯代回明確unavailable，不能回灌舊池。

`featured_view`另提供`selection_class`、`signal_label`（核心事件／產業動態）及`disclosure_flags`。公開daily-brief使用同一投影，診斷`score_gate`改null，增加核心／補位候選數及selection policy。

## 前端接線要求

1. I01刻意不修改舊browser guard。舊guard拒絕schema2／pg2，已有回歸測試；**不能把本階段單獨推成正式版並期待重點恢復**。先完成I02、I03再安排相容發布。
2. 新guard須驗同代version2、來源許可、原始材料關係、class、徽章及披露標示，不能只把version常數改成2。
3. 查詢、分類、來源及明示訊號條件先過濾完整候選，再選核心及所需補位。精選／全部AI模式只控制下方列表，不再把75／82門檻套到上方D+。
4. 熱點／時間線共用D+資格，維持核心在前；補位不因無徽章或單一來源無故消失。原熱點10／時間線20展開上限保持。
5. 接續實作常駐「精選N／全部AI M」、查看全部入口、保留模式的清除、固定綜合排序並移除四個排序按鈕。本階段這些介面尚未完成。

## 驗證與證據

Downloads根目錄：`/Users/lordmi/Downloads/ai-news-radar-i01-20261024/`。先核對`SEAL.sha256`、`MANIFEST.json`及`HANDOFF.md`，不以本文件中的數量替代精確產物版本。

- 新增95項D+測試，涵蓋六類低分核心、三則具名開發回歸、未知新名稱的正反例、量測披露、補位0／1／4／5／超過5、來源及phase、容量／故障、型別與跨欄位偽造拒收、無網路運作。
- 最終完整2,245項測試通過，三個受影響Python模組編譯通過。舊v1相容測試保留，新增測試明確驗證舊browser guard拒絕v2；這不代表I02介面已驗收。
- 3個固定快照（10/24 18:35、19:05、19:35）均為2核心＋3補位，完整候選及預設選集均保存；一般AI數量分別80／77／77，內容不變。NVIDIA與Kimi是核心，Anthropic是帶兩個標示的補位。
- 14日同輸入／state／asof回放，1,914事件窗口、2,002一般AI輸入列次；state、事件語意與既有一般輸出一致。公開daily從1增至57事件列次，是資格改變的結果，不是新增採樣或品質精確率。
- 三快照v2用途投影約169–172KB（canonical JSON），原約138–141KB，仍低於8MiB。完整時間與大小以`FIXED_SNAPSHOTS.json`及`HISTORY.json`為準；不把單機量測當服務SLA。
- 固定材料已依使用者要求曝光，只作開發回歸；其他歷史回放只做機械核對，不展示未授權新聞材料，不宣稱獨立自然新聞precision。
- 全部測試需以Downloads作basetemp，舊日報工具的本機保護不允許系統tmp；初次預設tmp失敗不修改產品來繞過，調整驗收環境後重跑。

## 階段出口

I01僅交付後端、契約、測試與離線證據。I02接線及桌面／手機互動、I03整體／正式版本相容性驗收尚未執行；沒有commit／push授權。

下一階段I02：**GPT-6.1 Sol／High**。I02結束交接I03，同模型／High；保留所有固定輸入、版本、測試紀錄及不變邊界，不重開來源觀察或PG05修補。
