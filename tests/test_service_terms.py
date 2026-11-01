"""Real service-policy cases and counterexamples from the November 1 review."""
import json

import pytest

from scripts import ai_relevance, publisher_material, signal_material as m, signal_selection as s
from tests.test_signal_selection import annotated, supported, bundle
from tests.test_publisher_governance import article
from tests.js_bridge import run_js


PRICING = [
    ("OpenAI's upcoming chat-and-work merger in ChatGPT signals the end of all-you-can-prompt pricing",
     "OpenAI combines the Chat and Work modes into a single interface. Starting in December, Plus, Pro, and Business plans will share a common, token-based quota for ChatGPT and Codex. More complex models consume more of this quota, while simple instant chats do not count toward it."),
    ("OpenAI doubles usage limits on Pro plans as competition with Anthropic heats up",
     "OpenAI is doubling usage limits across its paid plans, from Pro 100 to Pro 500. A planned cut to the Pro 200 quota was reversed after user pushback. More efficient models should push usable capacity higher."),
    ("OpenAI is steering ChatGPT users toward more paid usage",
     "OpenAI is now capping the number of paid ChatGPT accounts per device and payment card. Users who hit the limit can't start new subscriptions, and affected accounts can't be used on that device."),
    ("ChatGPT調整方案額度", "ChatGPT Pro付費方案額度翻倍，適用所有現有訂閱會員，無需重新訂閱。"),
    ("ChatGPT合併計量", "自12月起，ChatGPT Plus與Pro方案將共用Token配額，簡單聊天不計入配額。"),
    ("OpenAI plans to change ChatGPT quota", "Starting in May, ChatGPT Pro plans will share a common quota."),
]


@pytest.mark.parametrize("title,summary", PRICING)
def test_original_service_terms_support_existing_pricing_kind(title, summary):
    row, q = annotated(title, summary)
    assert supported(q, "pricing")
    for e in q["core_evidence"]:
        for span in e["spans"]:
            assert row[span["field"]][span["start"]:span["end"]] == span["text"]


@pytest.mark.parametrize("title,summary", [
    ("OpenAI may double ChatGPT Pro quota", "The company is considering more paid usage."),
    ("OpenAI will double ChatGPT Pro quota", "A future possibility without an effective date."),
    ("OpenAI plans to change ChatGPT quota", "ChatGPT Pro plans will double usage limits from 100 to 200 tokens."),
    ("OpenAI plans to change ChatGPT quota", "On ChatGPT Pro, users will share a common quota of 100 tokens."),
    ("OpenAI does not double ChatGPT Pro quota", "The Pro quota is unchanged."),
    ("OpenAI denies doubling ChatGPT Pro quota", "OpenAI previously doubled Pro usage limits."),
    ("OpenAI may double ChatGPT Pro quota", "Starting December 1, ChatGPT Pro plans will share a common quota."),
    ("ChatGPT quota is unchanged", "Previously OpenAI doubled Pro usage limits."),
    ("How to increase ChatGPT quota", "ChatGPT Pro plans share a common token-based quota."),
    ("ChatGPT quota overview", "ChatGPT Pro includes a token-based quota."),
    ("ChatGPT gains new features", "Anthropic doubles Claude Pro usage limits."),
    ("OpenAI updates ChatGPT", "Claude Pro subscribers share a common token-based quota. Anthropic announced the change."),
])
def test_service_terms_do_not_promote_predictions_denials_guides_or_other_products(title, summary):
    _, q = annotated(title, summary)
    assert not supported(q, "pricing")


def test_translation_and_ai_summary_cannot_supply_missing_terms():
    _, q = annotated("ChatGPT quota overview", "The article has no announced change.",
        title_zh="ChatGPT方案額度翻倍", summary_zh="ChatGPT Pro付費方案額度翻倍。",
        news_summary="ChatGPT Pro付費方案額度翻倍。")
    assert not supported(q, "pricing")


def test_interface_merger_is_not_a_corporate_transaction():
    _, q = annotated(*PRICING[0])
    assert not any(e["kind"] == "market" for e in q["core_evidence"])
    _, q = annotated("Microsoft acquires OpenAI", "Microsoft signed an acquisition agreement for $10 billion.")
    assert supported(q, "market")


def test_unreviewed_source_still_cannot_publish_service_changes():
    parent, daily, _ = bundle([article(title=PRICING[0][0], summary=PRICING[0][1],
        url="https://unreviewed.example/pricing", source="Unreviewed", site_id="curated_media")])
    assert not parent["publisher_governance"]["featured_event_ids"]
    assert daily["items"] == []


@pytest.mark.parametrize("title,summary", [
    ("OpenAI plans to train models on Daybreak Blue cybersecurity session data that was previously off-limits",
     "Starting November 29, OpenAI will use data from Daybreak Blue sessions to train its models, even when users have turned off training. After backlash, a follow-up email promised a separate opt-out."),
    ("Anthropic's watermark rollout leaves a loophole on two older Claude models",
     "Anthropic is expanding its text watermark to four more Claude models. On Claude Opus 4.6 and Sonnet 4.6, developers can bypass the watermark by tweaking a single sampling parameter."),
])
def test_policy_changes_supply_material_without_inventing_a_core_kind_or_impact(title, summary):
    row, q = annotated(title, summary)
    assert not any(e["status"] == "supported" for e in q["core_evidence"])
    assert m.supplement(row, s.legacy.source_material(row), q)["kind"] == "industry_news"
    parent, daily, _ = bundle([article(title=title, summary=summary)])
    decision = parent["publisher_governance"]["events"][0]
    assert decision["featured_eligible"] and decision["selection_class"] == "supplement"
    assert not decision["supplement_impact"]["passes"] and daily["items"] == []
    assert run_js("const G=require('./assets/publisher-governance.js');console.log(JSON.stringify(G.valid("
                  + json.dumps(parent) + ")));") is True


def test_research_stimuli_are_not_reader_tips_and_do_not_gain_core_bonus():
    title = "Beekeeping tips and wrestling advice can train AI models to sabotage oversight"
    summary = "Anthropic used Claude to generate training data that trains smaller models to sabotage oversight. These datasets bypass safety monitors."
    row, q = annotated(title, summary)
    assert not m.genre_noise(title, summary)
    assert m.genre_noise("Five tips for using Claude models", summary)
    assert m.supplement(row, s.legacy.source_material(row), q)["kind"] == "industry_news"
    assert not any(e["status"] == "supported" for e in q["core_evidence"])


@pytest.mark.parametrize("title,summary", [
    ("4 days left: How TechCrunch Founder Summit helps you make more useful connections to scale",
     "Get ready for networking opportunities on November 4. Register before all prices go up at the door."),
    ("AI conference: book your place", "Buy your ticket today for the AI conference."),
    ("AI峰會倒數", "立即購票，參加論壇。"),
])
def test_ticket_promotion_cannot_borrow_a_trusted_feed_score(title, summary):
    row = article(title=title, summary=summary, source="TechCrunch AI", site_id="curated_media",
                  url="https://techcrunch.com/synthetic")
    assert publisher_material.event_promotion(title, summary)
    assert not ai_relevance.score_ai_relevance(row)["is_ai_related"]
    _, q = annotated(title, summary)
    assert q["scope"] == "out_of_scope"


@pytest.mark.parametrize("title,summary", [
    ("OpenAI announces a new model at an AI conference", "Developers can now use the model with tool calling."),
    ("Conference ticket platform introduces an AI agent", "The new agent helps users register for conferences."),
    ("Researchers publish AI conference findings", "The report tested model performance at the conference."),
])
def test_conference_reporting_is_not_ticket_marketing(title, summary):
    assert not publisher_material.event_promotion(title, summary)


@pytest.mark.parametrize("title,summary", PRICING[:3])
def test_service_changes_keep_event_clocks_and_browser_contract(title, summary):
    row = article(title=title, summary=summary)
    parent, daily, result = bundle([row])
    event = parent["brief_events"]["events"][0]
    assert event["effective_at"] == row["published_at"]
    assert "pricing" in parent["publisher_governance"]["events"][0]["featured_business_events"]
    assert s.validate(parent["publisher_governance"], parent["brief_events"])
    assert run_js("const G=require('./assets/publisher-governance.js');console.log(JSON.stringify(G.valid("
                  + json.dumps(parent) + ")));") is True
    _, _, again = bundle([row], previous=s.b.StateInput("valid", result.next_state))
    assert again.projection["events"][0]["effective_at"] == event["effective_at"]
