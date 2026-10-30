"""D+ use selection, with unchanged source admission and event history."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from scripts import brief_events as b, update_news as u, signal_material as m, signal_selection as s
from tests.test_publisher_governance import article, NOW, ready_bundle
from tests.js_bridge import run_js

ROOT = Path(__file__).resolve().parents[1]
USER_CASES = json.loads((ROOT / "tests/fixtures/dplus-user-cases.json").read_text())


def bundle(rows=None, *, now=NOW, previous=None):
    rows = rows if rows is not None else [article(summary="The new AI model adds tool calling and supports enterprise customers using longer context windows.")]
    native = copy.deepcopy(rows)
    items = [u.add_source_tier_fields(u.add_ai_relevance_fields(copy.deepcopy(row))) for row in rows]
    stories = u.merge_story_items(items, now, 24)
    result = u.build_brief_event_payloads(stories, rows, previous or b.StateInput("missing"), now, 24,
        archive_meta=b.ArchiveMeta("valid", u.iso(now)))
    parent, daily = {"generated_at": u.iso(now), "stories": stories}, {"generated_at": u.iso(now)}
    u.apply_brief_event_result(result, daily, parent)
    assert rows == native
    return parent, daily, result


def schema_validator():
    old = json.loads((ROOT / "docs/contracts/publisher-governance-v1.schema.json").read_text())
    new = json.loads((ROOT / "docs/contracts/publisher-governance-v2.schema.json").read_text())
    registry = Registry().with_resource(old["$id"], Resource.from_contents(old))
    return Draft202012Validator(new, registry=registry, format_checker=FormatChecker())


def resign(parent):
    s._hashes(parent["brief_events"], parent["publisher_governance"])


def annotated(title, summary="", **extra):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary, **extra))
    return row, s.material.qualify_core(row, s.legacy.source_material(row))


def supported(q, kind="model_release"):
    return any(e["kind"] == kind and e["status"] == "supported" for e in q["core_evidence"])


def test_default_backend_uses_v2_and_daily_is_a_bound_adapter():
    parent, daily, result = bundle()
    overlay = parent["publisher_governance"]
    assert overlay["schema_version"] == 2 and overlay["selection_policy"] == "impact-v2"
    assert s.validate(overlay, parent["brief_events"])
    schema_validator().validate(overlay)
    assert daily["publisher_governance_meta"] == s.metadata(overlay)
    assert daily["brief_event_meta"] == b.selection_meta(parent["brief_events"])
    assert [r["brief_event_id"] for r in daily["items"]] == overlay["daily_selected_event_ids"]
    assert daily["items"][0]["selection_class"] == "core"
    assert daily["selection_diagnostics"]["score_gate"] is None
    assert daily["selection_diagnostics"]["core_count"] == 1
    assert b.validate_state(result.next_state)


def test_explicit_legacy_fixture_validates_only_in_legacy_backend_and_browser_accepts_dplus():
    old, *_ = ready_bundle()
    assert s.legacy.validate(old["publisher_governance"], old["brief_events"])
    new, *_ = bundle()
    assert not s.legacy.validate(new["publisher_governance"], new["brief_events"])
    result = run_js("const G=require('./assets/publisher-governance.js');"
        + "const parent=" + json.dumps(new) + ";"
        + "console.log(JSON.stringify({valid:G.valid(parent)}));")
    assert result == {"valid": True}
    result = run_js("const G=require('./assets/publisher-governance.js');const parent=" + json.dumps(old)
        + ";console.log(JSON.stringify({valid:G.valid(parent)}));")
    assert result == {"valid": False}


@pytest.mark.parametrize("case", USER_CASES["cases"], ids=lambda c: c["case_id"])
def test_user_nominated_public_development_cases(case):
    now = b.parse(USER_CASES["asof"])
    row = case["record"]
    parent, daily, _ = bundle([row], now=now)
    overlay = parent["publisher_governance"]
    assert overlay["status"] == "ready"
    assert s.validate(overlay, parent["brief_events"])
    schema_validator().validate(overlay)
    decision = next(d for d in overlay["events"] if row["id"] in d["support_article_ids"])
    assert decision["featured_eligible"]
    if case["case_id"] == "unreleased_disclosure":
        assert decision["selection_class"] == "supplement"
        assert decision["eligibility_basis"] == "capability_disclosure"
        assert decision["featured_business_events"] == []
        assert decision["disclosure_flags"] == ["provider_claim", "unreleased"]
        assert not decision["supplement_impact"]["passes"] and daily["items"] == []
    else:
        assert len(daily["items"]) == int(decision["supplement_impact"]["passes"])
        assert decision["selection_class"] == "core"
        assert decision["featured_business_events"] == ["model_release"]
        assert decision["featured_score"] < .72


@pytest.mark.parametrize("score", [0.0, .1, .5754, .7199])
def test_legacy_importance_cannot_override_material_impact_rank(score):
    parent, *_ = bundle()
    event = parent["brief_events"]["events"][0]
    annotations = {a["id"]: a for a in parent["publisher_governance"]["articles"]}
    rows = {r["id"]: s._native_row(r) for r in event["sources"]}
    decision = s.decide(event, annotations, rows, NOW, lambda *_: score)
    assert decision["featured_eligible"]
    expected = s.supplement_impact.rank(decision["supplement_impact"], "core", b.parse(event["effective_at"]), NOW)
    assert decision["featured_score"] == expected
    assert decision["eligibility_basis"] == "supported_core"


@pytest.mark.parametrize("kind,title,summary", [
    ("earnings", "NVIDIA reports Q3 2026 revenue of $10 billion", "Revenue increased this quarter."),
    ("market", "Microsoft acquires OpenAI", "Microsoft signed an acquisition agreement."),
    ("security", "PHP vulnerability permits remote code execution", "Researchers reproduced a use-after-free attack chain causing arbitrary code execution."),
    ("pricing", "OpenAI cuts GPT-6.1 Sol API pricing", "The API input price decreases from $3 to $2 per million tokens."),
    ("benchmark", "GPT-6.1 Sol scores 90% on GPQA", "The evaluation tested the model on the named benchmark."),
    ("model_release", "OpenAI releases GPT-6.1 Sol", "GPT-6.1 Sol is now available."),
])
def test_all_six_media_reported_core_kinds_qualify_below_the_old_gate(kind, title, summary):
    row = article(title=title, summary=summary, url="https://cnbc.com/synthetic",
                  source="CNBC Technology", site_id="curated_media")
    parent, *_ = bundle([row])
    event = parent["brief_events"]["events"][0]
    annotations = {a["id"]: a for a in parent["publisher_governance"]["articles"]}
    rows = {r["id"]: s._native_row(r) for r in event["sources"]}
    decision = s.decide(event, annotations, rows, NOW, lambda *_: .15)
    assert decision["featured_eligible"] and decision["selection_class"] == "core"
    assert kind in decision["featured_business_events"]


@pytest.mark.parametrize("name", ["Aster 7.2 Tiny E3B 4GB", "Cedar 2.1 Nano 1B", "Maple 12 Vision 8GB"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_new_versioned_family_is_not_a_vendor_allowlist(name, language):
    title = f"Acme Releases {name}: An Open Small Language Model for local agents"
    if language == "zh":
        title = f"Acme發布{name}：開源小型語言模型，可用於端側代理"
    row, qualification = annotated(title)
    assert supported(qualification)
    # General qualification and matching retain their original behavior.
    assert b.MODEL_RE.search(name) is None
    assert m.versioned_release(s.legacy.source_material(row)) == name


@pytest.mark.parametrize("title,summary", [
    ("Acme Releases Aster 7.2: An Open Small Language Model documentation", "Only the documentation is new."),
    ("Acme Releases Aster 7.2 AI model training guide", "Only a training guide was published."),
    ("Did Acme release Aster 7.2: an open small language model?", "No launch has been announced."),
    ("If Acme releases Aster 7.2: an open small language model", "This is hypothetical."),
    ("Acme may release Aster 7.2: an open small language model", "No announcement."),
    ("Acme Releases Aster 7.2: An Open Small Language Model", "Aster has not been released."),
    ("Acme recalls Aster 7.2: an open small language model", "Aster was released last year."),
    ("Acme Releases Aster 7.2", "Another vendor's Cedar 9.0 AI model is available."),
    ("Acme Releases Aster 7.2 App", "A phone app using an unrelated language model."),
])
def test_generic_release_extension_keeps_complete_object_and_assertion_guards(title, summary):
    _, qualification = annotated(title, summary)
    assert not supported(qualification)


@pytest.mark.parametrize("summary", [
    "The company believes its AI will be safer and more capable.",
    "AI sales rose 67 percent. A test is planned but has no results.",
    "An evaluation reports 67 percent success without a named method or evaluator.",
    "AISI performed a test, but the results were not disclosed.",
])
def test_says_and_numbers_without_measured_test_material_do_not_grant_disclosure(summary):
    row, q = annotated("Anthropic says its unreleased model is more capable and better aligned", summary)
    assert m.supplement(row, s.legacy.source_material(row), q)["kind"] is None


def test_says_is_allowed_only_for_a_retained_specific_measured_disclosure():
    row, q = annotated("Anthropic says its unreleased model is better aligned",
        "The UK's AISI safety test found success in 7 of 10 runs for an internal AI model.")
    evidence = m.supplement(row, s.legacy.source_material(row), q)
    assert evidence["kind"] == "capability_disclosure"
    assert evidence["qualifiers"] == ["provider_claim", "unreleased"]
    assert not supported(q)


@pytest.mark.parametrize("title,summary", [
    ("How to use Copilot in Teams", "Microsoft announced the workspace integration."),
    ("See what five builders made with Gemini 4", "A showcase of projects."),
    ("Scaling storage for ChatGPT, part two", "OpenAI announced a technical case study."),
    ("OpenAI CEO says AI will escape its sandbox", "Alignment is the only answer."),
    ("Microsoft may launch a Copilot integration", "An unconfirmed prediction."),
    ("OpenAI releases GPT-6.1 Sol documentation", "Only a training guide was published."),
])
def test_supplement_does_not_backfill_genre_noise_or_failed_core(title, summary):
    row, q = annotated(title, summary)
    assert m.supplement(row, s.legacy.source_material(row), q)["kind"] is None


def test_concrete_product_news_can_supply_unbadged_supplement():
    row = article(title="Microsoft announces new Copilot workspace integration",
        summary="Microsoft has added an AI collaboration workspace for business users.",
        url="https://the-decoder.com/synthetic-product", source="The Decoder AI News", site_id="curated_media")
    parent, daily, _ = bundle([row])
    d = parent["publisher_governance"]["events"][0]
    assert d["selection_class"] == "supplement" and d["eligibility_basis"] == "industry_news"
    assert d["supplement_impact"]["passes"] is False and daily["items"] == []


@pytest.mark.parametrize("host", ["unknown.example", "news.google.com"])
@pytest.mark.parametrize("title", ["OpenAI releases GPT-6.1 Sol", "Microsoft announces new Copilot workspace integration"])
def test_unknown_or_unreviewed_publisher_cannot_use_core_or_supplement(host, title):
    row = article(title=title, url=f"https://{host}/synthetic", source="Unreviewed", site_id="curated_media")
    parent, daily, _ = bundle([row])
    assert not parent["publisher_governance"]["featured_event_ids"] and daily["items"] == []


def selection_row(index, *, core=False, score=.5, publisher="one"):
    return {"brief_event_id": f"be1_{index:024x}", "featured_eligible": True,
        "selection_class": "core" if core else "supplement", "featured_score": score,
        "supplement_impact": {"total": 80, "passes": True},
        "featured_primary_item": {"corroboration_key": "publisher:" + publisher,
            "publisher": {"publisher_id": publisher}}}


@pytest.mark.parametrize("core_count", [0, 1, 4, 5, 6, 21])
@pytest.mark.parametrize("supplement_count", [0, 1, 12])
def test_selection_uses_one_bounded_pool_for_both_classes(core_count, supplement_count):
    rows = [selection_row(i, core=True, score=.1) for i in range(core_count)]
    rows += [selection_row(100+i, score=.99) for i in range(supplement_count)]
    selected = s.select(rows)
    assert len(selected) == min(5, core_count + supplement_count)
    assert selected[:min(5,supplement_count)] == [r["brief_event_id"] for r in rows[core_count:core_count+5]]
    assert selected == s.select(list(reversed(rows)))


def test_filtering_precedes_supplementation_and_publisher_decay_is_retained():
    rows = [selection_row(i, core=True) for i in range(6)]
    rows += [selection_row(100, score=.9), selection_row(101, score=.89),
             selection_row(102, score=.88, publisher="other")]
    assert len(s.select(rows)) == 5
    selected = s.select([r for r in rows if r["selection_class"] == "supplement"])
    assert selected == [rows[6]["brief_event_id"], rows[8]["brief_event_id"], rows[7]["brief_event_id"]]


@pytest.mark.parametrize("mutation", ["old_policy", "registry", "generation", "source_span", "source_permission",
    "past_phase", "context_unknown", "withdrawn_key", "core_badge", "summary", "class", "default_limit",
    "duplicate_article", "duplicate_event", "missing_score", "daily_order", "count", "primary", "expired",
    "source_links", "source_site_name", "supplement_forgery", "boolean_count", "numeric_eligibility",
    "boolean_span", "numeric_permission"])
def test_cross_field_mutations_fail_even_when_self_hashes_are_updated(mutation):
    parent, *_ = bundle()
    g, p = parent["publisher_governance"], parent["brief_events"]
    a, d, event = g["articles"][0], g["events"][0], p["events"][0]
    ref = event["sources"][0]
    if mutation == "old_policy": g["selection_policy"] = "legacy-v1"
    elif mutation == "registry": g["registry_revision"] = "f" * 64
    elif mutation == "generation": g["schema_version"] = 1
    elif mutation == "source_span": a["qualification"]["core_evidence"][0]["spans"][0]["text"] = "invented"
    elif mutation == "source_permission": a["source_policy"]["allow_featured"] = False
    elif mutation == "past_phase": ref["role"] = "past_phase"
    elif mutation == "context_unknown": ref["role"] = "context_unknown"
    elif mutation == "withdrawn_key": ref["corroboration_key"] = None
    elif mutation == "core_badge": d["featured_business_events"] = ["security"]
    elif mutation == "summary": d["featured_news_summary"] = "invented"; d["summary_article_id"] = "wrong"
    elif mutation == "class": d["selection_class"] = "supplement"
    elif mutation == "default_limit": g["default_visible_limit"] = 6
    elif mutation == "duplicate_article": g["articles"].append(copy.deepcopy(a))
    elif mutation == "duplicate_event": g["events"].append(copy.deepcopy(d))
    elif mutation == "missing_score": d["support_scores"] = []
    elif mutation == "daily_order": g["daily_selected_event_ids"] = []
    elif mutation == "count": d["qualified_source_count"] += 1
    elif mutation == "primary": d["featured_primary_item"]["url"] = "https://example.com/unrelated"
    elif mutation == "expired": event["expires_at"] = u.iso(NOW)
    elif mutation == "source_links": ref["source_links"] = ["javascript:alert(1)"]
    elif mutation == "source_site_name": ref["source_site_name"] = None
    elif mutation == "supplement_forgery": a["supplement_evidence"]["kind"] = "capability_disclosure"
    elif mutation == "boolean_count": d["qualified_source_count"] = True
    elif mutation == "numeric_eligibility": d["featured_eligible"] = 1
    elif mutation == "boolean_span": a["qualification"]["core_evidence"][0]["spans"][0]["start"] = False
    elif mutation == "numeric_permission": a["source_policy"]["allow_featured"] = 1
    resign(parent)
    assert not s.validate(g, p)


@pytest.mark.parametrize("state", ["unsupported"])
def test_unavailable_projection_is_explicit_versioned_and_preserves_general_stories(state):
    parent, daily, _ = bundle(previous=b.StateInput(state))
    assert parent["stories"]
    assert parent["publisher_governance"]["status"] == "unavailable"
    assert daily["publisher_governance_meta"]["schema_version"] == 2
    assert daily["items"] == []
    assert s.validate(parent["publisher_governance"], parent["brief_events"])
    schema_validator().validate(parent["publisher_governance"])


def test_corrupt_state_follows_existing_engine_recovery_without_new_clocks():
    parent, daily, result = bundle(previous=b.StateInput("corrupt"))
    assert parent["brief_events"]["status"] == "recovered"
    assert parent["publisher_governance"]["status"] == "ready"
    assert b.validate_state(result.next_state) and daily["items"]


def test_legacy_importance_is_unused_and_capacity_fails_closed(monkeypatch):
    parent, *_ = bundle()
    # Legacy scorer no longer controls the impact rank.
    result = s.build(copy.deepcopy(parent["brief_events"]), [article()], now=NOW,
        annotate=u.add_reader_source_policy_fields, scorer=lambda *_: float("nan"), sanitize=u.sanitize_public_payload)
    assert result["status"] == "ready"
    monkeypatch.setattr(s, "MAX_EVENTS", 0)
    result = s.build(copy.deepcopy(parent["brief_events"]), [article()], now=NOW,
        annotate=u.add_reader_source_policy_fields, scorer=lambda *_: .5, sanitize=u.sanitize_public_payload)
    assert result["diagnostics"]["errors"] == ["projection_capacity"]


def test_backend_qualification_requires_no_network_or_provider_calls(monkeypatch):
    import requests
    def forbidden(*args, **kwargs):
        raise AssertionError("D+ must not perform external requests")
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    rows = [c["record"] for c in USER_CASES["cases"]]
    parent, daily, _ = bundle(rows, now=b.parse(USER_CASES["asof"]))
    assert parent["publisher_governance"]["status"] == "ready" and len(daily["items"]) == 1
