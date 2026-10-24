"""PG05 contract counterexamples and unrelated synthetic controls."""
import pytest

from scripts import publisher_governance as g, update_news as u
from tests.test_publisher_governance import article, NOW


def qualification(title, summary=""):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary))
    return g.qualify(row, g.source_material(row))


def status(q, kind):
    return next((e["status"] for e in q["core_evidence"] if e["kind"] == kind), "not_core")


@pytest.mark.parametrize("kind,title,summary", [
    ("earnings", "OpenAI 公布 2026 年第三季營收 168 億美元", "本季營收為168億美元。"),
    ("market", "OpenAI收購Example Bio", "OpenAI宣布已完成收購Example Bio。"),
    ("model_release", "Meta releases Muse Wonder", "Meta releases its Muse Wonder AI model, now available to developers."),
    ("market", "ExampleCloud announces permanent shutdown", "ExampleCloud will permanently cease operations on December 31, 2026."),
])
def test_pg05_frozen_positive_material_counterexamples(kind, title, summary):
    assert status(qualification(title, summary), kind) == "supported"


@pytest.mark.parametrize("title,summary", [
    ("Copilot for Beginners: How to teach Copilot about your codebase", "Learn how to add instructions to your repository."),
    ("Save 50% on your AI conference ticket", "Register now and buy a ticket for the AI developer conference."),
])
def test_pg05_frozen_scope_counterexamples(title, summary):
    assert qualification(title, summary)["scope"] == "out_of_scope"


def test_pg05_frozen_acquisition_talks_are_not_a_confirmed_action():
    q = qualification("OpenAI 擬收購 Example Security，談判正在進行中", "消息人士稱交易仍未敲定，雙方拒絕證實。")
    assert status(q, "market") != "supported"


@pytest.mark.parametrize("title,summary", [
    ("ExampleCloud reports Q3 revenue of $2 billion", "Revenue rose 30 percent this quarter."),
    ("Orchid Labs reports annualized revenue of $2 billion", "The annualized revenue run rate reached $2 billion."),
    ("OpenAI公布2026年第三季營收168億美元", "本季營收為168億美元。"),
    ("鯨雲科技公布第三季營收12.5億元", "第三季營收年增20%。"),
    ("Anthropic 營收季增45%", "公司在第三季業績說明會公布數據。"),
])
def test_financial_names_boundaries_and_units_are_not_a_closed_list(title, summary):
    assert status(qualification(title, summary), "earnings") == "supported"


def test_another_companys_ipo_cannot_supply_a_missing_financial_period():
    q = qualification("Acme faces a market shakeout", "Cedar cancelled its IPO; Acme customers account for 45 percent of revenue.")
    assert status(q, "earnings") != "supported"
    assert status(qualification("Acme IPO raises $100 million", "Acme announced its IPO proceeds."), "earnings") == "supported"


@pytest.mark.parametrize("name", ["Photon Nova", "Juniper 8", "Cedar Audio Pro"])
def test_unseen_complete_model_names_need_explicit_model_context_and_release_state(name):
    q = qualification(f"Acme releases {name}", f"Acme releases the {name} AI model, now available to developers.")
    assert status(q, "model_release") == "supported"


@pytest.mark.parametrize("title,summary", [
    ("Photon Nova model discussion", "Acme may release Photon Nova next month."),
    ("Photon Nova AI model discussion", "Acme launches a new office."),
    ("Acme releases a travel app", "The application uses AI to book holidays."),
    ("Photon Nova AI model retrospective", "Photon Nova was released last year."),
    ("Photon Nova AI model benchmark comparison", "Photon Nova is compared with GPT-4, which scores 90% on GPQA."),
])
def test_new_names_do_not_bypass_action_rumor_history_or_cross_subject_guards(title, summary):
    q = qualification(title, summary)
    assert not any(e["status"] == "supported" for e in q["core_evidence"])


def test_unlisted_benchmark_has_named_model_method_and_result():
    q = qualification("Photon 7 scores 94% on RiverBench", "The Photon 7 AI model was evaluated on the RiverBench benchmark.")
    assert status(q, "benchmark") == "supported"
    assert status(qualification("Photon 7 benchmark discussion", "A leader in AI evaluation."), "benchmark") != "supported"


def test_new_component_needs_risk_mechanism_and_method_even_when_its_name_is_new():
    q = qualification("CedarServer vulnerability allows remote code execution", "Researchers reproduced a use-after-free attack chain permitting arbitrary code.")
    assert status(q, "security") == "supported"
    assert status(qualification("CedarServer vulnerability", "A social post shows a possible problem."), "security") != "supported"


@pytest.mark.parametrize("title,summary", [
    ("ExampleCloud announces acquisition of Cedar Labs", "ExampleCloud signed an acquisition agreement; closing awaits regulatory approval."),
    ("鯨雲科技宣布年底永久停運", "公司已公告將於2026年12月31日停止營運。"),
    ("ExampleCloud announces permanent shutdown", "The service will permanently cease operations next month."),
])
def test_announced_commitments_can_take_effect_in_the_future(title, summary):
    assert status(qualification(title, summary), "market") == "supported"


@pytest.mark.parametrize("title,summary", [
    ("ExampleCloud may acquire Cedar Labs", "The transaction is unconfirmed."),
    ("ExampleCloud is in talks to acquire Cedar Labs", "Negotiations are ongoing."),
    ("鯨雲科技擬收購新創公司", "收購仍在談判，尚未敲定。"),
])
def test_planned_or_rumored_transactions_do_not_supply_market_support(title, summary):
    assert status(qualification(title, summary), "market") != "supported"


@pytest.mark.parametrize("title,summary", [
    ("Acme raises capital to remain independent", "Acme previously drew acquisition interest but remains independent."),
    ("Acme announces a share class to fund AI", "The funds can support future acquisitions and employee compensation."),
    ("Acme reviews Cedar Labs acquisition", "Acquisition negotiations are ongoing."),
    ("OpenAI收購傳聞", "交易尚未定案。"),
    ("Acme reports Q3 revenue of $2 billion", "Revenue rose in 2026 due to a recent acquisition; the target was not named."),
])
def test_acquisition_as_background_or_an_unnamed_object_is_not_a_transaction(title, summary):
    assert status(qualification(title, summary), "market") != "supported"


@pytest.mark.parametrize("title,summary", [
    ("Acme announced no acquisition of Cedar Labs", "There is no acquisition agreement."),
    ("Acme denies reports it acquired Cedar Labs", "The company denied the transaction."),
    ("Acme acquired Cedar Labs?", "Acme has not acquired Cedar Labs."),
])
def test_explicit_transaction_denials_cannot_supply_supported_market_material(title, summary):
    assert status(qualification(title, summary), "market") == "conflict"


@pytest.mark.parametrize("title,summary", [
    ("Cedar Developer Guide: How to configure AI agents", "Follow these steps to install the software."),
    ("Photon for Beginners", "Learn how to use the API."),
    ("AI safety event passes", "Register now for the AI conference and buy a ticket."),
    ("企業如何防止AI代理做錯事：四大治理建議", ""),
])
def test_instruction_and_sales_purpose_is_excluded_with_or_without_a_prefix(title, summary):
    assert qualification(title, summary)["scope"] == "out_of_scope"


@pytest.mark.parametrize("title,summary", [
    ("Acme announces a tutorial platform for teachers", "The company released a platform supporting AI education."),
    ("Acme publishes a new guide to AI safety", "The publisher announced the public guide today."),
    ("Researchers announce results from an AI safety conference", "The conference presented a new evaluation method."),
    ("AI conference ticket prices rose 50%", "Organizers reported attendance statistics."),
    ("Acme launches Photon Nova: benchmarks, pricing and how to use it", "Acme released its new AI model today."),
])
def test_news_about_teaching_products_and_events_is_not_an_instruction_or_sales_call(title, summary):
    assert qualification(title, summary)["scope"] == "in_scope"


def test_supported_material_does_not_grant_an_unknown_publisher_featured_or_radar_access():
    row = article(title="Acme releases Photon Nova", summary="Photon Nova AI model is now available.",
                  site_id="curated_media", source="Unreviewed publisher", url="https://unreviewed.example/story")
    row = u.add_reader_source_policy_fields(row)
    assert status(g.qualify(row, g.source_material(row)), "model_release") == "supported"
    assert not g.admitted(row, "featured") and not g.radar_allowed(row, NOW)
