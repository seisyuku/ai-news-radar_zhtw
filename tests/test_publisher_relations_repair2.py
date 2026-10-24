"""PG05 recheck counterexamples: transaction state, release object, finance actor."""
import pytest

from scripts import publisher_governance as g, update_news as u, brief_events as b
from tests.test_publisher_governance import article, NOW
from tests.test_publisher_material_repair import qualification, status


RECHECK_CASES = [('R01_not_acquiring', 'market', 'OpenAI is not acquiring Cedar Labs', 'There is no deal.', 'not_supported'),
 ('R01_considers',
  'market',
  'OpenAI considers acquiring Cedar Labs',
  'A decision has not been made.',
  'not_supported'),
 ('R01_hopes',
  'market',
  'OpenAI hopes to acquire Cedar Labs',
  'The companies have not signed an agreement.',
  'not_supported'),
 ('R01_cjk_negation', 'market', 'OpenAI不會收購Cedar Labs', '公司表示沒有這項交易。', 'not_supported'),
 ('control_talks',
  'market',
  'OpenAI is in talks to acquire Cedar Labs',
  'Negotiations are ongoing.',
  'not_supported'),
 ('control_agreement',
  'market',
  'OpenAI announces acquisition of Cedar Labs',
  'OpenAI signed an acquisition agreement; closing awaits regulatory approval.',
  'supported'),
 ('control_shutdown',
  'market',
  'ExampleCloud announces permanent shutdown',
  'ExampleCloud will permanently cease operations next month.',
  'supported'),
 ('R02_known_docs',
  'model_release',
  'OpenAI releases GPT-6.1 Sol documentation',
  'The guide explains how to use the existing model.',
  'not_supported'),
 ('R02_new_docs',
  'model_release',
  'OpenAI releases Photon Nova AI model documentation',
  'Only the technical documentation was published today.',
  'not_supported'),
 ('control_docs_for',
  'model_release',
  'OpenAI releases documentation for the Photon Nova AI model',
  'Only the documentation is new.',
  'not_supported'),
 ('control_known_release',
  'model_release',
  'OpenAI releases GPT-6.1 Sol',
  'GPT-6.1 Sol is now available to developers.',
  'supported'),
 ('control_new_release',
  'model_release',
  'OpenAI releases Photon Nova AI model',
  'Photon Nova AI model is now available to developers.',
  'supported'),
 ('control_history',
  'model_release',
  'Photon Nova AI model retrospective',
  'Photon Nova was released last year.',
  'not_supported'),
 ('R03_unknown_rival',
  'earnings',
  'OpenAI earnings discussion',
  'ExampleCloud reports Q3 revenue of $2 billion.',
  'not_supported'),
 ('R03_both_unknown',
  'earnings',
  'Acme earnings discussion',
  'Cedar reports Q3 revenue of $2 billion.',
  'not_supported'),
 ('control_known_rival',
  'earnings',
  'OpenAI earnings discussion',
  'Microsoft reports Q3 revenue of $2 billion.',
  'not_supported'),
 ('control_own_finance',
  'earnings',
  'OpenAI reports Q3 revenue of $2 billion',
  'Revenue rose 20 percent this quarter.',
  'supported'),
 ('control_new_company_finance',
  'earnings',
  'ExampleCloud reports Q3 revenue of $2 billion',
  'Revenue rose 20 percent this quarter.',
  'supported'),
 ('control_cjk_money', 'earnings', 'OpenAI公布2026年第三季營收168億美元', '本季營收為168億美元。', 'supported'),
 ('control_tutorial',
  'scope',
  'Copilot for Beginners: How to teach Copilot about your codebase',
  'Learn how to add instructions.',
  'out_of_scope'),
 ('control_ticket',
  'scope',
  'Save 50% on your AI conference ticket',
  'Register now and buy a ticket.',
  'out_of_scope'),
 ('control_release_howto',
  'scope',
  'Acme launches Photon Nova: benchmarks, pricing and how to use it',
  'Acme released its new AI model today.',
  'in_scope')]


@pytest.mark.parametrize("case,kind,title,summary,expected", RECHECK_CASES, ids=[x[0] for x in RECHECK_CASES])
def test_frozen_recheck_relations(case, kind, title, summary, expected):
    q = qualification(title, summary)
    actual = q["scope"] if kind == "scope" else status(q, kind)
    if expected == "not_supported":
        assert actual != "supported"
    else:
        assert actual == expected


@pytest.mark.parametrize("predicate", [
    "does not plan to acquire", "has never intended to acquire", "isn't acquiring",
    "is exploring acquiring", "wants to acquire", "proposes to acquire",
    "has no intention of acquiring", "has no current plans to acquire", "ruled out acquiring",
    "考慮收購", "不打算收購", "計劃收購", "沒有打算收購",
])
def test_transaction_predicate_state_composes_with_auxiliaries(predicate):
    assert status(qualification(f"OpenAI {predicate} Cedar Labs"), "market") != "supported"


@pytest.mark.parametrize("title,summary", [
    ("OpenAI signed an agreement to acquire Cedar Labs", "The deal closes next year after regulatory approval."),
    ("OpenAI will acquire Cedar Labs", "The companies signed a definitive agreement today."),
    ("OpenAI not only acquired Cedar Labs but also invested in Aspen", ""),
    ("OpenAI agrees to acquire Cedar Labs", "Completion awaits regulatory approval."),
    ("OpenAI is not profitable but acquired Cedar Labs", ""),
    ("OpenAI未獲監管核准便收購Cedar Labs", ""),
    ("OpenAI已簽署收購Cedar Labs協議", "交易預計年底完成，仍待監管核准。"),
])
def test_announced_transactions_keep_future_effective_and_affirmative_controls(title, summary):
    assert status(qualification(title, summary), "market") == "supported"


@pytest.mark.parametrize("name", ["GPT-6.1 Sol", "Photon Nova"])
@pytest.mark.parametrize("tail", ["AI model documentation", "technical report", "'s system card", "模型的技術報告",
                                  "model's technical report", "weights documentation", "benchmark results", "white paper"])
def test_model_name_modifying_an_artifact_is_not_the_release_object(name, tail):
    summary = f"{name} is an AI model. Only the document is new."
    assert status(qualification(f"OpenAI releases {name} {tail}", summary), "model_release") != "supported"


@pytest.mark.parametrize("suffix", [", with documentation", " and its technical report", ": pricing and how to use it"])
def test_actual_model_release_can_include_artifacts_as_additional_objects(suffix):
    q = qualification("OpenAI releases Photon Nova AI model" + suffix, "Photon Nova AI model is now available.")
    assert status(q, "model_release") == "supported"


@pytest.mark.parametrize("title,summary", [
    ("OpenAI earnings discussion", "Cedar reports Q3 revenue of $2 billion. Its revenue grew 45 percent this quarter."),
    ("Orchid Labs earnings discussion", "Aspen Cloud reports Q3 revenue of $2 billion. Revenue grew 45 percent this quarter."),
    ("OpenAI earnings discussion", "Revenue from ExampleCloud is $2 billion this quarter."),
    ("OpenAI earnings discussion", "OpenAI says ExampleCloud reported Q3 revenue of $2 billion."),
])
def test_foreign_financial_actor_and_its_ellipsis_do_not_borrow_headline_identity(title, summary):
    assert status(qualification(title, summary), "earnings") != "supported"


@pytest.mark.parametrize("title,summary", [
    ("OpenAI earnings report", "Revenue reached $2 billion this quarter."),
    ("Orchid Labs earnings report", "Revenue reached $2 billion this quarter."),
    ("OpenAI earnings report", "OpenAI reported Q3 revenue of $2 billion, while Cedar reported $1 billion."),
    ("OpenAI earnings report", "Cedar reported Q3 revenue of $1 billion. OpenAI reported Q3 revenue of $2 billion."),
    ("OpenAI and Cedar earnings report", "OpenAI reported Q3 revenue of $2 billion. Cedar reported Q3 revenue of $1 billion."),
    ("鯨雲科技財報", "本季營收12億元，年增20%。"),
    ("Orchid earnings report", "Orchid announced Q3 revenue of $2 billion on Tuesday, fueled by its Cedar division."),
    ("Orchid and Cedar stocks fall on Aspen revenue report", "Aspen reached $2 billion in annualized revenue, Quartz confirmed."),
    ("Orchid raises capital to challenge Zircon with AI", "Orchid's annualized revenue has tripled to $200 million as it eyes U.S. expansion."),
    ("OpenAI earnings report", "Revenue reached $2 billion this quarter, CNBC confirmed."),
    ("估值10億！Orchid年化營收成長", "Quartz等外媒稱，Orchid年化營收約20億美元。"),
])
def test_financial_actor_binding_preserves_clear_ellipsis_and_explicit_comparisons(title, summary):
    assert status(qualification(title, summary), "earnings") == "supported"


@pytest.mark.parametrize("title,summary", [
    ("OpenAI is not acquiring Cedar Labs", "There is no deal."),
    ("OpenAI releases Photon Nova AI model documentation", "Only the technical documentation was published today."),
    ("OpenAI earnings discussion", "ExampleCloud reports Q3 revenue of $2 billion."),
])
def test_wrong_material_cannot_pass_real_producer_or_radar_despite_official_identity(title, summary):
    row = article(title=title, summary=summary)
    row["business_events"] = u.business_event_score(row)
    row = u.add_ai_relevance_fields(row)
    assert row["ai_is_related"]
    ann = u.add_reader_source_policy_fields(row)
    assert g.admitted(ann, "featured")
    story = u.build_story_record("relation-negative", [row], NOW, 24)
    result = u.build_brief_event_payloads([story], [row], b.StateInput("missing"), NOW, 24,
        archive_meta=b.ArchiveMeta("valid", u.iso(NOW)))
    assert result.publisher_governance["status"] == "ready"
    assert len(result.projection["events"]) == 1
    assert not result.publisher_governance["featured_event_ids"]
    assert not u.build_llm_radar_payload([row], NOW, raw_records={row["id"]: row})["events"]
