"""Editorial review cases run through the real D+ event and selection pipeline.

All headlines and summaries are synthetic analogues of observed patterns.
"""

import pytest

from scripts import signal_selection
from tests.test_publisher_governance import article
from tests.test_signal_selection import bundle


CASES = [
    pytest.param(
        "confirmed_model_release",
        "Acme releases Photon 7: an open language model",
        "Photon 7 is now available to developers.",
        "https://the-decoder.com/synthetic-model-release", "The Decoder AI News",
        "core", "model_release", id="confirmed model release"),
    pytest.param(
        "confirmed_shutdown",
        "ExampleCloud announces permanent shutdown",
        "ExampleCloud will permanently cease operations on December 31, 2026.",
        "https://techcrunch.com/synthetic-shutdown", "TechCrunch AI",
        "core", "market", id="confirmed company shutdown"),
    pytest.param(
        "concrete_product_update",
        "Microsoft announces new Copilot workspace integration",
        "Microsoft added an AI collaboration workspace for business users.",
        "https://the-decoder.com/synthetic-product", "The Decoder AI News",
        "supplement", "industry_news", id="concrete product update"),
    pytest.param(
        "specific_funding",
        "Cedar AI raises $50 million to expand AI chip production",
        "Cedar AI closed a $50 million investment round and will expand chip production.",
        "https://techcrunch.com/synthetic-funding", "TechCrunch AI",
        "supplement", "industry_news", id="specific company funding"),
    pytest.param(
        "named_summary_shutdown",
        "ExampleCloud announces service changes",
        "ExampleCloud will permanently cease operations next month.",
        "https://techcrunch.com/synthetic-service-change", "TechCrunch AI",
        "core", "market", id="named shutdown in summary"),
    pytest.param(
        "release_rumor",
        "Microsoft may launch a new Copilot workspace next year",
        "An unconfirmed report predicts a future release.",
        "https://the-decoder.com/synthetic-rumor", "The Decoder AI News",
        None, None, id="release rumor"),
    pytest.param(
        "instructional_guide",
        "How to use Copilot in Teams",
        "Step by step instructions for business users.",
        "https://the-decoder.com/synthetic-guide", "The Decoder AI News",
        None, None, id="instructional guide"),
    pytest.param(
        "funding_concerns",
        "AI investors raise concerns about model funding",
        "Investors discuss valuation risks without announcing a financing transaction.",
        "https://cnbc.com/synthetic-funding-concerns", "CNBC Technology",
        None, None, id="raises concerns is not funding"),
    pytest.param(
        "chinese_funding_commentary",
        "OpenAI融資疑慮升溫，投資人重新檢視AI產業",
        "本文討論估值風險，沒有宣布具體交易。",
        "https://techcrunch.com/synthetic-funding-opinion-zh", "TechCrunch AI",
        None, None, id="Chinese funding noun is not a transaction"),
    pytest.param(
        "chinese_funding_close",
        "鯨雲科技完成新一輪AI融資",
        "鯨雲科技已完成本輪募資，將擴充AI推論服務。",
        "https://techcrunch.com/synthetic-funding-close-zh", "TechCrunch AI",
        "supplement", "industry_news", id="Chinese completed funding"),
    pytest.param(
        "named_roundup",
        "Apple AI project retrospective",
        "Several unrelated AI projects shut down over the years, while Apple delayed an assistant update.",
        "https://techcrunch.com/synthetic-project-retrospective", "TechCrunch AI",
        None, None, id="named roundup without tied shutdown"),
    pytest.param(
        "shutdown_discussion",
        "ExampleCloud discusses permanent shutdown",
        "Management is weighing several options without an announced decision.",
        "https://techcrunch.com/synthetic-shutdown-discussion", "TechCrunch AI",
        None, None, id="shutdown discussion is not confirmed"),
    pytest.param(
        "paper_about_tool",
        "Nvidia releases a research paper about Flora",
        "The research paper describes the Flora AI data engine, but no software was released.",
        "https://the-decoder.com/synthetic-tool-paper", "The Decoder AI News",
        None, None, id="paper about tool is not tool release"),
    pytest.param(
        "shutdown_roundup",
        "The AI graveyard: a running list of projects and startups that did not make it",
        "From Apple's delayed Siri AI to OpenAI's troubled app launch, here is a look at AI projects that shut down or missed expectations.",
        "https://techcrunch.com/synthetic-roundup", "TechCrunch AI",
        None, None, id="shutdown roundup"),
    pytest.param(
        "portfolio_commentary",
        "AI funding fears rattle Wall Street. Here is how we are adjusting our portfolio",
        "The rotation out of AI stocks benefited several defensive holdings.",
        "https://cnbc.com/synthetic-portfolio", "CNBC Technology",
        None, None, id="portfolio commentary"),
    pytest.param(
        "open_source_data_tool",
        "Nvidia open-sources Flora to make robot video labeling 125x cheaper than GPT-6 Astra",
        "Nvidia's new AI data engine Flora labels one hour of robot video for 72 cents instead of $88 with GPT-6 Astra. The open system uses fine-tuned Qwen3.5 models.",
        "https://the-decoder.com/synthetic-data-tool", "The Decoder AI News",
        "supplement", "industry_news", id="open source AI data tool"),
]


@pytest.mark.parametrize("case_id,title,summary,url,source,expected_class,expected_kind", CASES)
def test_editorial_selection_expectations(case_id, title, summary, url, source,
                                          expected_class, expected_kind):
    row = article(case_id, title=title, summary=summary, url=url, source=source,
                  site_id="curated_media", business_events=[])
    parent, daily, _ = bundle([row])
    projection = parent["brief_events"]
    overlay = parent["publisher_governance"]
    assert overlay["status"] == "ready"
    assert signal_selection.validate(overlay, projection)
    assert len(overlay["events"]) == 1
    assert len(overlay["articles"]) == 1
    assert overlay["articles"][0]["source_policy"]["allow_featured"]

    decision = overlay["events"][0]
    assert decision["selection_class"] == expected_class
    assert decision["featured_eligible"] is (expected_class is not None)
    assert len(daily["items"]) == int(expected_class is not None)
    if expected_class == "core":
        assert expected_kind in decision["featured_business_events"]
    elif expected_class == "supplement":
        assert decision["eligibility_basis"] == expected_kind
        assert decision["featured_business_events"] == []
