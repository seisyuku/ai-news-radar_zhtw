"""The adopted impact threshold applies only to 24-hour D+ supplements."""

import copy

import pytest

from scripts import signal_selection, supplement_impact
from tests.js_bridge import run_js
from tests.test_publisher_governance import article
from tests.test_signal_selection import bundle, resign, selection_row
from tests.test_publisher_governance_ui import harness


@pytest.mark.parametrize("title,summary,expected", [
    ("Meta launches $35 billion stock offering to fund AI expansion",
     "Meta launches $35 billion stock offering to fund AI expansion.", (40, 20, 10, 20, 90, True)),
    ("Cedar AI secures $800 million funding for cybersecurity",
     "Cedar AI secures $800 million funding for cybersecurity.", (30, 20, 10, 20, 80, True)),
    ("OpenAI audit reveals monitoring gap",
     "The audit found that 25% of agent traffic went unmonitored across its deployed AI services.", (30, 0, 20, 20, 70, True)),
    ("Nvidia open-sources Flora to make robot video labeling 125x cheaper than GPT-6 Astra",
     "Flora labels one hour of robot video for 72 cents instead of $88 with GPT-6 Astra, while scoring higher on quality and catching errors in robot actions.", (15, 10, 20, 20, 65, False)),
    ("Honeywell deploys AI platform at refinery", "Honeywell deploys AI platform at refinery.", (15, 10, 10, 10, 45, False)),
    ("Grok releases an AI-generated Odyssey clip", "The footage looks okay, without an announced product or commercial effect.", (0, 0, 10, 0, 10, False)),
])
def test_native_material_scores(title, summary, expected):
    got = supplement_impact.score({"title_original": title, "summary": summary}, "industry_news")
    assert tuple(got.values()) == expected


def test_unit_cost_needs_comparable_quality_and_never_implies_realized_savings():
    title = "Nvidia open-sources Flora AI data tool"
    summary = "The tool labels one hour of robot video for 72 cents instead of $88 with GPT-6 Astra."
    material = {"title_original": title, "summary": summary}
    assert supplement_impact.score(material, "industry_news")["i"] == 5
    material["summary"] += " It achieved comparable quality in the labeling benchmark."
    assert supplement_impact.score(material, "industry_news")["i"] == 15


def test_selection_uses_impact_before_old_importance_and_keeps_core():
    rows = [selection_row(1, core=True, score=.1), selection_row(2, score=.99),
            selection_row(3, score=.2, publisher="other")]
    rows[1]["supplement_impact"] = {"total": 65, "passes": False}
    rows[2]["supplement_impact"] = {"total": 80, "passes": True}
    assert signal_selection.select(rows) == [rows[0]["brief_event_id"], rows[2]["brief_event_id"]]


def test_backend_and_browser_reject_forged_impact_score():
    row = article("funded", title="Cedar AI secures $150 million funding for inference infrastructure",
        summary="Cedar AI closed the round and plans to expand its inference infrastructure.",
        site_id="curated_media", source="The Decoder AI News", url="https://the-decoder.com/synthetic-funding")
    parent, daily, _ = bundle([row])
    decision = parent["publisher_governance"]["events"][0]
    assert decision["supplement_impact"]["passes"] and len(daily["items"]) == 1
    forged = copy.deepcopy(parent)
    forged_decision = forged["publisher_governance"]["events"][0]
    forged_decision["supplement_impact"]["i"] = 40
    forged_decision["supplement_impact"]["total"] += 10
    resign(forged)
    assert not signal_selection.validate(forged["publisher_governance"], forged["brief_events"])
    assert run_js(harness(forged, daily) + "console.log(JSON.stringify({valid:G.valid(parent)}));") == {"valid": False}


def test_chinese_supply_chain_release_keeps_pypi_boundary_and_browser_score():
    title = "LiteLLM公布供應鏈攻擊後續調查，5月外洩金鑰讓駭客操控官方發布流程"
    summary = "開源AI模型串接工具LiteLLM公布1.107.0版供應鏈攻擊的調查結果，發現攻擊者利用5月外洩後未撤銷的AI代理平臺主金鑰，取得GitHub組織擁有者的存取權杖。攻擊者隨後竊取另外兩名維護者的憑證，最終操控官方發布流程，讓含有竊密程式的版本上架PyPI及容器映像檔儲存庫。"
    native = {"title": title, "summary": summary}
    assert supplement_impact.score(native, "industry_news") == {
        "i": 40, "p": 20, "e": 20, "c": 20, "total": 100, "passes": True}
    row = article("chain", title=title, title_original="", summary=summary,
        site_id="tw_media", source="iThome", url="https://www.ithome.com.tw/news/179955", business_events=[])
    parent, daily, _ = bundle([row])
    d = parent["publisher_governance"]["events"][0]
    assert d["selection_class"] == "supplement" and d["supplement_impact"]["total"] == 100
    assert run_js(harness(parent, daily) + "console.log(JSON.stringify({valid:G.valid(parent)}));") == {"valid": True}
