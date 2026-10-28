"""Source-audit regressions: purpose, financial evidence and article versions."""
import copy
from datetime import timedelta

import pytest

from scripts import brief_events as b, publisher_governance as g, publisher_material as m, update_news as u
from tests.test_publisher_governance import article, NOW
from tests.test_signal_selection import bundle
from tests.js_bridge import run_js
import json


def qualify(title, summary=""):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary))
    return g.qualify(row, g.source_material(row))


def earnings(title, summary=""):
    return any(e["kind"] == "earnings" and e["status"] == "supported"
               for e in qualify(title, summary)["core_evidence"])


@pytest.mark.parametrize("title,summary", [
    ("AI 偵測 Anthropic IPO 文件：92% 人工撰寫", "Anthropic 的 335 頁 IPO 文件被放進 AI 偵測器。"),
    ("Anthropic founders worth $13 billion after IPO", "The founders own 10% of shares."),
    ("Anthropic 七名創辦人身價全破 130 億美元", "Anthropic IPO 文件揭露，七位共同創辦人各持股約1.4%，以最近一輪募資估值計算，身價均逾130億美元。"),
    ("We ran Acme's IPO prospectus through an AI detector: 92% human", "The document has 300 pages."),
    ("Anthropic IPO 文件 92% 由人工撰寫，營收數字由 AI 校對", "寫作工具檢查 300 頁文件。"),
])
def test_ipo_side_story_numbers_are_not_corporate_financial_evidence(title, summary):
    assert not earnings(title, summary)
    assert "earnings" not in u.business_event_score({"title": title, "summary": summary})


@pytest.mark.parametrize("title,summary", [
    ("Anthropic files S-1 with the SEC for proposed initial public offering", "The price range has not yet been announced."),
    ("Anthropic正式啟動IPO", "公司公開遞交 S-1。"),
    ("Anthropic 向 SEC 公開遞交申請，擬以代碼 ANT 上市", "Anthropic 公開遞交 S-1，價格尚未公布。"),
    ("Acme IPO raises $100 million", "The company announced its IPO proceeds."),
    ("Anthropic公布2026年上半年營收163億美元", "營收增加。"),
])
def test_actual_filings_proceeds_and_financial_metrics_remain_supported(title, summary):
    assert earnings(title, summary)


@pytest.mark.parametrize("title", [
    "【2026 最新】Cursor Computer Use 排錯：五步定位問題",
    "教你 ChatGPT 臨時對話的 3 種用法 - 未來商務",
    "讓 AI 不只回答問題：六個推理型提示詞實戰筆記",
    "4 道 AI 指令帶你檢查明年規劃",
    "用AI工作，如何避免只交出成果卻沒學會？用白板測試檢查",
    "製造業導入 AI，先從這 2 件事下手",
    "AI chip imports documentation – Downloads - Epoch AI",
    "AI chip imports documentation – Changelog - Epoch AI",
    "2026 AIoT全日論壇如何鏈動企業AI新局 - 數位時代",
])
def test_instruction_promotion_and_documentation_landing_pages_are_outside_reader_scope(title):
    assert qualify(title)["scope"] == "out_of_scope"


@pytest.mark.parametrize("title", [
    "Acme releases an AI troubleshooting model",
    "Acme introduces an AI tutorial platform for teachers",
    "AI chip imports rise 20% as Epoch releases a new dataset",
    "Epoch publishes AI chip import research with a downloadable dataset",
    "CyberQ 實測 Qwen 模型：公開方法與條件化實驗的限制",
    "OpenAI發布新模型，附使用指南",
    "Acme公布2026 AI論壇研究成果",
])
def test_reporting_about_products_research_and_measurements_is_retained(title):
    assert qualify(title)["scope"] == "in_scope"


@pytest.mark.parametrize("title,summary", [
    ("Opera推出WebAI標準，支持瀏覽器本地運行AI模型", "Opera推出全新網絡標準WebAI，讓用戶在瀏覽器運行AI模型。"),
    ("Acme releases a standard for local AI models", "Acme releases the WebAgent browser standard, compatible with many models."),
])
def test_trailing_model_noun_cannot_turn_next_field_company_into_released_model(title, summary):
    q = qualify(title, summary)
    assert not any(e["kind"] == "model_release" and e["status"] == "supported" for e in q["core_evidence"])
    assert q["scope"] == "in_scope"


def test_explicit_quoted_model_name_remains_valid_without_cross_field_inference():
    q = qualify('Acme releases "Photon Nova" AI model', 'The new model is available today.')
    assert any(e["kind"] == "model_release" and e["status"] == "supported" for e in q["core_evidence"])


def test_corrected_article_title_uses_latest_seen_copy_deterministically_without_mutation():
    older = article("old", title="AI security report", last_seen_at="2026-10-23T03:05:00Z")
    newer = article("new", title="AI security report: corrected conditions", last_seen_at="2026-10-23T03:25:00Z")
    rows = [older, newer]; before = copy.deepcopy(rows)
    for random_pick in (False, True):
        assert [x["id"] for x in u.dedupe_items_by_title_url(rows, random_pick)] == ["new"]
        assert [x["id"] for x in u.dedupe_items_by_title_url(rows[::-1], random_pick)] == ["new"]
    assert rows == before


def test_rolling_changelog_entries_and_new_publication_evidence_are_not_title_corrections():
    a = article("a", url="https://developers.openai.com/codex/changelog", title="Model announcement")
    c = article("b", url=a["url"], title="CLI version release")
    assert len(u.dedupe_items_by_title_url([a, c], False)) == 2
    c.update(url="https://openai.com/news/synthetic", published_at="2026-10-23T03:15:00Z")
    a["url"] = c["url"]
    assert len(u.dedupe_items_by_title_url([a, c], False)) == 2


def test_36kr_cjk_and_latin_publisher_suffixes_do_not_create_two_articles():
    rows = [article("a", site_id="kr36_ai", source="36Kr", title="AI開源新模型 - 36氪"),
            article("b", site_id="kr36_ai", source="36Kr", title="AI開源新模型 - 36Kr")]
    assert len(u.dedupe_same_publisher_items(rows)) == 1


def filing_rows():
    return [article("filing-a", title="Anthropic files S-1 with the SEC for proposed initial public offering",
                    summary="The company disclosed its financial results.", url="https://anthropic.com/news/filing", source="Anthropic News"),
            article("filing-b", title="Anthropic正式啟動IPO，揭露AI業務高速成長",
                    summary="Anthropic公開遞交S-1，上半年營收163億美元。", url="https://www.ithome.com.tw/news/1", source="iThome", site_id="tw_media"),
            article("filing-c", title="Anthropic 向 SEC 公開遞交申請，擬以代碼 ANT 上市",
                    summary="Anthropic公開遞交S-1，上半年營收163億美元。", url="https://www.inside.com.tw/article/filing", source="INSIDE", site_id="tw_media")]


def test_initial_ipo_filing_combines_publishers_and_browser_accepts_the_result():
    parent, daily, result = bundle(filing_rows())
    assert len(daily["items"]) == 1
    assert set(daily["items"][0]["member_article_ids"]) == {"filing-a", "filing-b", "filing-c"}
    assert daily["items"][0]["corroboration_count"] == 3
    assert b.validate_state(result.next_state)
    assert run_js("const G=require('./assets/publisher-governance.js');const p=" + json.dumps(parent)
                  + ";console.log(JSON.stringify(G.valid(p)));") is True


@pytest.mark.parametrize("title,summary", [
    ("Anthropic may file S-1 for an IPO", "No filing has occurred."),
    ("Anthropic files amended S-1 for IPO", "This is an amended filing."),
    ("Anthropic IPO pricing set at $50", "The price range is new."),
    ("Anthropic IPO 文件：92% 由人撰寫", "A writing detector tested the document."),
    ("Another Labs files S-1 for IPO", "A different company filed."),
    ("Anthropic has not filed S-1 for IPO", "No filing has occurred."),
])
def test_distinct_or_unasserted_ipo_developments_do_not_merge_into_initial_filing(title, summary):
    rows = filing_rows()[:1] + [article("other", title=title, summary=summary, url="https://openai.com/news/other")]
    parent, *_ = bundle(rows)
    assert len(parent["brief_events"]["events"]) == 2


def test_ipo_reposts_preserve_event_and_phase_clocks():
    rows = filing_rows(); _, _, first = bundle(rows[:1])
    rows[1]["published_at"] = rows[1]["first_seen_at"] = u.iso(NOW + timedelta(hours=5))
    _, _, second = bundle(rows[:2], now=NOW + timedelta(hours=6), previous=b.StateInput("valid", first.next_state))
    assert len(second.projection["events"]) == 1
    a, c = first.projection["events"][0], second.projection["events"][0]
    assert a["brief_event_id"] == c["brief_event_id"]
    assert a["initial_effective_at"] == c["initial_effective_at"]
    assert a["effective_at"] == c["effective_at"]


def test_ipo_merge_migrates_existing_separate_roots_without_losing_history(monkeypatch):
    rows = filing_rows()
    with monkeypatch.context() as patch:
        patch.setattr(m, "ipo_filing_entity", lambda *_: None)
        _, _, old = bundle(rows)
    old_ids = {e["brief_event_id"] for e in old.next_state["events"]}
    assert len(old_ids) == 3
    parent, _, new = bundle(rows, now=NOW + timedelta(hours=1), previous=b.StateInput("valid", old.next_state))
    assert b.validate_state(new.next_state)
    assert len(parent["brief_events"]["events"]) == 1
    state = new.next_state["events"]
    assert len(state) == 1
    assert {state[0]["brief_event_id"], *state[0]["alias_event_ids"]} == old_ids
    assert state[0]["initial_effective_at"] == min(e["initial_effective_at"] for e in old.next_state["events"])


def test_ipo_reprint_does_not_make_an_expired_filing_current_again():
    rows = filing_rows(); _, _, first = bundle(rows[:1])
    rows[1]["published_at"] = rows[1]["first_seen_at"] = u.iso(NOW + timedelta(hours=25))
    _, daily, second = bundle(rows[:2], now=NOW + timedelta(hours=26), previous=b.StateInput("valid", first.next_state))
    assert len(second.projection["events"]) == 1
    assert not second.projection["events"][0]["eligible"]
    assert daily["items"] == []


def test_same_investment_amount_actor_and_recipient_join_without_a_vendor_allowlist():
    rows = [article("invest-a", title="Cedar to invest $3 billion in Maple as tech firms deepen AI partnership", summary="An AI infrastructure investment.", url="https://cnbc.com/invest", site_id="curated_media", source="CNBC Technology"),
            article("invest-b", title="Cedar Invests $3000 Million in Maple in Deeper AI Partnership", summary="An AI infrastructure investment.", url="https://theinformation.com/invest", site_id="curated_media", source="The Information (Google News)")]
    parent, *_ = bundle(rows)
    assert len(parent["brief_events"]["events"]) == 1
    assert parent["brief_events"]["events"][0]["corroboration_count"] == 2


@pytest.mark.parametrize("title", [
    "Cedar may invest $3 billion in Maple", "Cedar did not invest $3 billion in Maple",
    "Will Cedar invest $3 billion in Maple?", "Cedar completes its investment in Maple",
])
def test_uncertain_denied_or_new_completion_reports_are_not_investment_duplicates(title):
    assert m.investment_signature(title) is None


def test_different_investment_amounts_and_recipients_stay_separate():
    titles = ["Cedar invests $3 billion in Maple", "Cedar invests $4 billion in Maple", "Cedar invests $3 billion in Aspen"]
    rows = [article(str(i), title=t, url=f"https://openai.com/news/invest-{i}") for i,t in enumerate(titles)]
    parent, *_ = bundle(rows)
    assert len(parent["brief_events"]["events"]) == 3


@pytest.mark.parametrize("site,source", [("curated_media", "AIBASE"), ("aibase", "AIbase"), ("opmlrss", "Private label")])
def test_aibase_downgrade_is_scoped_to_publisher_across_transports(site, source):
    row = article(site_id=site, source=source, url="https://news.aibase.com/tw/news/123")
    out = u.add_reader_source_policy_fields(row)
    assert out["source_tier"] == "advanced" and out["source_tier_rank"] == 4
    assert out["source_policy"]["admission_status"] == "limited"
    assert all(out["source_policy"]["allow_" + use] for use in ("general", "featured", "radar"))
    other = u.add_reader_source_policy_fields(article(site_id="curated_media", source="TechCrunch AI", url="https://techcrunch.com/news/123"))
    assert other["source_tier_rank"] == 2
    assert row.get("source_policy") is None
