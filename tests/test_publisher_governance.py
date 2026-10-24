"""Use eligibility must never rewrite event identity, history or source votes."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts import brief_events as b, update_news as u, publisher_governance as g, publisher_policy as p

NOW = u.parse_iso("2026-10-23T03:35:27Z")


def article(id="a", *, url="https://openai.com/news/synthetic", source="OpenAI News", site_id="official_ai", **extra):
    return {"id": id, "url": url, "source": source, "site_id": site_id,
        "title": "OpenAI releases GPT-6.1 Sol for developers", "summary": "GPT-6.1 Sol is now available to developers.",
        "published_at": "2026-10-23T03:00:00Z", "first_seen_at": "2026-10-23T03:00:00Z",
        "business_events": ["model_release"], "ai_score": 1.0, **extra}


def ready_bundle():
    # Frozen v1 contract/old-browser fixture. New default-generation behavior
    # is exercised separately in test_signal_selection.py.
    rows = [article(), article("b", url="https://cnbc.com/synthetic", source="CNBC Technology", site_id="curated_media")]
    story = u.build_story_record("synthetic-story", rows, NOW, 24)
    story["news_summary"] = "Synthetic summary bound to the original primary."
    result = u.build_brief_event_payloads([story], rows, b.StateInput("missing"), NOW, 24,
        archive_meta=b.ArchiveMeta("valid", u.iso(NOW)), governance_version=1)
    merged = {"generated_at": u.iso(NOW), "stories": [story]}; daily = {"generated_at": u.iso(NOW)}
    u.apply_brief_event_result(result, daily, merged)
    assert result.publisher_governance["status"] == "ready"
    assert any(d["featured_eligible"] for d in result.publisher_governance["events"])
    return merged, daily, result, rows


@pytest.mark.parametrize("kind,title,summary", [
    ("earnings", "NVIDIA reports Q3 2026 revenue of $10 billion", "Revenue increased 20 percent this quarter."),
    ("market", "Microsoft acquires OpenAI", "Microsoft acquired the company for $10 billion."),
    ("security", "PHP vulnerability permits remote code execution", "Unauthenticated attackers can execute arbitrary code."),
    ("pricing", "OpenAI cuts GPT-6.1 Sol API pricing", "The API input price decreases from $3 to $2 per million tokens."),
    ("benchmark", "GPT-6.1 Sol scores 90% on GPQA", "The evaluation tested the model on the named benchmark."),
    ("model_release", "OpenAI releases GPT-6.1 Sol", "GPT-6.1 Sol is now available to developers."),
])
def test_core_material_has_exact_native_spans_for_all_six_kinds(kind, title, summary):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary))
    material = g.source_material(row); q = g.qualify(row, material)
    e = next(x for x in q["core_evidence"] if x["kind"] == kind)
    assert e["status"] == "supported"
    assert e["spans"] and all(material[s["field"]][s["start"]:s["end"]] == s["text"] for s in e["spans"])


@pytest.mark.parametrize("kind,title,summary", [
    ("earnings", "OpenAI growth advice", "Revenue strategies for companies."),
    ("market", "OpenAI market share discussion", "A popular product with no population or time-bound data."),
    ("pricing", "GPT-6.1 Sol costs $3 per million tokens", "The article mentions a price but no change."),
    ("benchmark", "GPT-6.1 Sol previously scored 90% on GPQA last year", "A historical ranking recap."),
    ("model_release", "Rumor: OpenAI may launch GPT-6.1 Sol", "A prediction with no announcement."),
    ("security", "PHP vulnerability could permit remote code execution", "A social post demonstrates a possible issue, with no technical method retained."),
])
def test_names_numbers_and_badges_alone_do_not_supply_core_material(kind, title, summary):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary,
        url="https://cnbc.com/synthetic", source="CNBC Technology", site_id="curated_media"))
    assert not any(x["kind"] == kind and x["status"] == "supported" for x in g.qualify(row, g.source_material(row))["core_evidence"])


def test_security_report_needs_method_and_technical_detail_but_official_material_needs_no_cve():
    row = article(title="PHP vulnerability permits remote code execution", summary="Researchers reproduced a use-after-free attack chain causing unauthorized execution.",
        url="https://the-decoder.com/synthetic", source="The Decoder AI News", site_id="curated_media")
    annotated = u.add_reader_source_policy_fields(row)
    assert next(x for x in g.qualify(annotated, g.source_material(row))["core_evidence"] if x["kind"] == "security")["status"] == "supported"
    row["summary"] = "A user posted an example."
    row["publisher_links"] = ["https://openai.com/security/"]
    assert not any(x["status"] == "supported" for x in g.qualify(annotated, g.source_material(row))["core_evidence"])


def test_official_host_cannot_turn_a_secondhand_social_demo_into_primary_technical_material():
    row = u.add_reader_source_policy_fields(article(title="PHP vulnerability permits unauthenticated remote code execution",
        summary="According to a Reddit post, an unconfirmed demo shows this behavior."))
    assert not any(e["kind"] == "security" and e["status"] == "supported" for e in g.qualify(row,g.source_material(row))["core_evidence"])


def test_original_material_precedes_translations_generated_summaries_and_related_links():
    row = u.add_reader_source_policy_fields(article(title="Original general AI commentary", title_zh="OpenAI 發布 GPT-6.1 Sol",
        summary="General commentary. Related articles: OpenAI releases GPT-6.1 Sol.", news_summary="OpenAI releases GPT-6.1 Sol."))
    assert not any(x["kind"] == "model_release" and x["status"] == "supported" for x in g.qualify(row, g.source_material(row))["core_evidence"])


@pytest.mark.parametrize("kind,title,summary", [
    ("benchmark", "GPT-6.1 Sol benchmark evaluation", "GPT-4 scores 90% on GPQA."),
    ("pricing", "GPT-6.1 Sol API pricing discussion", "OpenAI cuts GPT-4 API pricing from $3 to $2 per million tokens."),
    ("security", "PHP vulnerability report", "Researchers reproduced a WordPress use-after-free attack chain causing remote code execution."),
])
def test_another_models_or_products_details_cannot_supply_the_headlines_evidence(kind, title, summary):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary))
    assert not any(e["kind"] == kind and e["status"] == "supported" for e in g.qualify(row,g.source_material(row))["core_evidence"])


@pytest.mark.parametrize("kind,title,summary", [
    ("model_release", "OpenAI discusses GPT-6.1 Sol", "OpenAI may launch GPT-6.1 Sol next year."),
    ("model_release", "OpenAI newsletter mentions GPT-6.1 Sol", "OpenAI launches a new office in London."),
    ("model_release", "OpenAI recalls GPT-6.1 Sol", "GPT-6.1 Sol was released last year."),
    ("model_release", "GPT-6.1 Sol discussion", "OpenAI will release GPT-6.1 Sol next week."),
    ("model_release", "GPT-6.1 Sol 相關消息", "OpenAI 可能推出 GPT-6.1 Sol。"),
    ("benchmark", "GPT-6.1 Sol benchmark comparison", "GPT-6.1 Sol is compared with GPT-4, which scores 90% on GPQA."),
    ("pricing", "GPT-6.1 Sol API pricing discussion", "Unlike GPT-6.1 Sol, GPT-4 cuts its API input price from $3 to $2 per million tokens."),
])
def test_pg05_release_state_and_same_clause_subject_must_support_the_actual_claim(kind, title, summary):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary))
    q = g.qualify(row, g.source_material(row))
    assert not any(e["kind"] == kind and e["status"] == "supported" for e in q["core_evidence"])
    if kind == "model_release":
        assert not g.radar_allowed(row, NOW, u.LLM_STATS_MODEL_ORG_IDS)


@pytest.mark.parametrize("title,summary", [
    ("OpenAI releases GPT-6.1 Sol", "GPT-6.1 Sol is now available to developers."),
    ("OpenAI introduces its new GPT-6.1 Sol", "Available now."),
    ("GPT-6.1 Sol is now available", "OpenAI opens access for developers."),
    ("OpenAI 推出了全新模型 GPT-6.1 Sol", "今日正式開放 API。"),
    ("GPT-6.1 Sol 正式發布", "開發者可立即使用。"),
])
def test_pg05_explicit_current_model_releases_remain_supported(title, summary):
    row = u.add_reader_source_policy_fields(article(title=title, summary=summary))
    assert any(e["kind"] == "model_release" and e["status"] == "supported"
               for e in g.qualify(row, g.source_material(row))["core_evidence"])


@pytest.mark.parametrize("title", ["如何使用 GPT-6.1 Sol：完整教學", "立即報名 AI 商業講座", "How to use OpenAI APIs", "Sponsored: AI productivity tips", "AI時代，企業如何提升效率與成長", "提升AI工作效率的五個實用建議"])
def test_article_scope_excludes_promotions_and_tutorials_without_url_blacklists(title):
    row = u.add_reader_source_policy_fields(article(title=title))
    assert g.qualify(row, g.source_material(row))["scope"] == "out_of_scope"


def test_conflicting_material_does_not_gain_support_and_platform_share_is_not_global_share():
    for row in [article(title="OpenAI releases GPT-6.1 Sol", summary="GPT-6.1 Sol has not been released."),
                article(title="OpenAI global market share reaches 90% in 2026", summary="The data only measures traffic share on OpenRouter, a single platform.")]:
        row = u.add_reader_source_policy_fields(row)
        assert "evidence_conflict" in g.qualify(row, g.source_material(row))["reason_codes"]


def test_end_to_end_uses_single_policy_summary_binding_and_original_state():
    parent, daily, result, rows = ready_bundle()
    overlay = parent["publisher_governance"]; projection = parent["brief_events"]
    assert g.validate(overlay, projection)
    schema = json.loads((Path(__file__).resolve().parents[1] / "docs/contracts/publisher-governance-v1.schema.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(overlay)
    assert b.validate_state(result.next_state)
    assert daily["brief_event_meta"] == b.selection_meta(projection)
    assert [e["brief_event_id"] for e in daily["items"]] == overlay["daily_selected_event_ids"]
    assert daily["items"][0]["news_summary"] == overlay["events"][0]["featured_news_summary"]
    assert overlay["registry_revision"] == p.current_registry().revision
    assert all(r["url"] == next(x for x in rows if x["id"] == r["id"])["url"] for e in projection["events"] for r in e["sources"])


def mutate(parent, name):
    g0 = parent["publisher_governance"]; p0 = parent["brief_events"]; d = g0["events"][0]; e = p0["events"][0]
    a = g0["articles"][0]; rid = d["featured_primary_article_id"]
    if name == "duplicate_article_id": g0["articles"].append(copy.deepcopy(a))
    elif name == "duplicate_event_id": g0["events"].append(copy.deepcopy(d))
    elif name == "brief_generation_mismatch": g0["brief_generation_id"] = "bg1_" + "0" * 24
    elif name == "state_revision_mismatch": g0["brief_state_revision"] = "0" * 64
    elif name == "generated_at_mismatch": g0["generated_at"] = "2026-10-22T03:35:27Z"
    elif name == "registry_revision_mismatch": g0["registry_revision"] = "0" * 64
    elif name == "event_missing_from_overlay": g0["events"] = []
    elif name == "article_reference_missing": g0["articles"] = []
    elif name in {"support_from_past_phase", "support_from_context_unknown"}:
        e["sources"][0]["role"] = "past_phase" if name.endswith("past_phase") else "context_unknown"
    elif name == "support_unreviewed_or_forbidden": a["source_policy"]["allow_featured"] = False
    elif name == "count_not_unique_keys": d["qualified_corroboration_keys"] *= 2
    elif name == "key_not_existing_active_key": d["qualified_corroboration_keys"] = ["publisher:invented"]; d["qualified_source_count"] = 1
    elif name == "featured_id_not_eligible": d["featured_eligible"] = False
    elif name == "daily_id_not_featured": g0["daily_selected_event_ids"] = ["be1_" + "0" * 24]
    elif name == "primary_not_in_support": d["support_article_ids"] = []
    elif name == "primary_item_id_mismatch": d["featured_primary_item"]["id"] = "invented"
    elif name == "primary_url_or_title_mismatch": d["featured_primary_item"]["url"] = "https://example.com/unrelated"
    elif name == "summary_article_mismatch": d["summary_article_id"] = "another"
    elif name == "span_not_matching_source_field": a["qualification"]["core_evidence"][0]["spans"][0]["text"] = "invented"
    elif name == "source_evidence_not_same_event":
        for ref in [*e["sources"], *e["items"], e["primary_item"]]:
            ref["source_material"]["title"] = "OpenAI releases GPT-9.9 for developers"
            ref["source_material"]["summary"] = "GPT-9.9 is now available."
        for annotation in g0["articles"]:
            ref = next(r for r in e["sources"] if r["id"] == annotation["id"])
            annotation["qualification"] = g.qualify(annotation, ref["source_material"])
        d["featured_primary_item"]["source_material"] = copy.deepcopy(next(r for r in e["sources"] if r["id"] == rid)["source_material"])
    elif name == "unsupported_policy": g0["policy_id"] = "future-policy"
    elif name == "projection_over_8mib": g0["diagnostics"]["errors"] = ["x" * (8 * 1024 * 1024)]
    else: raise AssertionError(name)
    # Re-sign self checks so rejection exercises relationships, not just hashes.
    if name not in {"brief_generation_mismatch", "state_revision_mismatch", "generated_at_mismatch"}:
        p0["generation_id"] = "bg1_" + b.digest({k:v for k,v in p0.items() if k != "generation_id"})[:24]
        g0["brief_generation_id"] = p0["generation_id"]
    g0["generation_id"] = "pg1_" + b.digest({k:v for k,v in g0.items() if k != "generation_id"})[:24]


CROSS_CASES = ["duplicate_article_id", "duplicate_event_id", "brief_generation_mismatch", "state_revision_mismatch", "generated_at_mismatch", "registry_revision_mismatch", "event_missing_from_overlay", "article_reference_missing", "support_from_past_phase", "support_from_context_unknown", "support_unreviewed_or_forbidden", "count_not_unique_keys", "key_not_existing_active_key", "featured_id_not_eligible", "daily_id_not_featured", "primary_not_in_support", "primary_item_id_mismatch", "primary_url_or_title_mismatch", "summary_article_mismatch", "span_not_matching_source_field", "source_evidence_not_same_event", "unsupported_policy", "projection_over_8mib"]


@pytest.mark.parametrize("name", CROSS_CASES)
def test_cross_field_contract_rejects_incoherent_eligibility_even_with_updated_self_hash(name):
    parent, *_ = ready_bundle(); mutate(parent, name)
    assert not g.validate(parent["publisher_governance"], parent["brief_events"])


def test_projection_capacity_and_invalid_engine_result_are_explicitly_unavailable(monkeypatch):
    parent, *_ = ready_bundle(); projection = parent["brief_events"]
    unavailable = g.unavailable(projection, p.current_registry().revision, "projection_capacity")
    assert unavailable["status"] == "unavailable" and not projection["selected_event_ids"]
    assert not any(unavailable[k] for k in ["events", "articles", "featured_event_ids", "daily_selected_event_ids"])


def test_unreviewed_reference_and_unknown_updates_do_not_poison_qualified_current_primary():
    row = article("unknown", site_id="curated_media", source="DeepSeek (Google News)", url="https://news.google.com/a")
    rows = [article(), row]
    story = u.build_story_record("synthetic", rows, NOW, 24)
    result = u.build_brief_event_payloads([story], rows, b.StateInput("missing"), NOW, 24,
        archive_meta=b.ArchiveMeta("valid", u.iso(NOW)))
    decision = next(d for d in result.publisher_governance["events"] if d["featured_eligible"])
    assert decision["support_article_ids"] == ["a"]
    assert decision["qualified_source_count"] == 1


def test_radar_requires_scoped_permission_and_expiry_and_never_labels_query_media_official():
    native = u.add_reader_source_policy_fields(article())
    assert g.radar_allowed(native, NOW)
    assert not g.radar_allowed({**native, "published_at": "2026-10-22T03:35:27Z"}, NOW)
    fake = article(url="https://example.org/a")
    assert not u.build_llm_radar_payload([fake], NOW)["events"]
    media = article(url="https://cnbc.com/a", site_id="official_ai", source="CNBC Technology")
    assert u._llm_radar_model_verification(media) == ("reported", "媒體報導")


CASES = json.loads((Path(__file__).parent / "fixtures/publisher-governance-cases.json").read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["case_id"])
def test_pg01_gate_cases_execute_the_real_runtime_decision(case):
    rows, refs, annotations = {}, [], {}
    keys = case["qualified_keys"] or [None]
    for index, key in enumerate(keys):
        rid = str(index)
        if key == "cn_aggregator":
            row = article(rid, url="https://aibase.com/news/" + rid, source="AIBASE", site_id="curated_media")
        elif key is None:
            row = article(rid, url="https://news.google.com/a", source="Epoch AI (Google News)", site_id="curated_media")
            row.update(u.publisher_identity.fields(row, feeds=u.publisher_feed_configs(), rss_source={"title":"Epoch AI", "href":"https://epoch.ai/"}))
        elif case["official_primary"]:
            row = article(rid)
        else:
            host = "cnbc.com" if key.endswith(":b") or "cnbc" in key else "reuters.com"
            row = article(rid, url="https://" + host + "/" + rid, source="CNBC Technology" if host == "cnbc.com" else "Reuters AI (Google News)", site_id="curated_media")
        row = u.add_reader_source_policy_fields(row); rows[rid] = row
        q = g.qualify(row, g.source_material(row)); q["scope"] = case["scope"]
        if not case["core_supported"] or case["evidence_conflict"]:
            for evidence in q["core_evidence"]: evidence["status"] = "conflict" if case["evidence_conflict"] else "insufficient"
        if case["identity_conflict"]: row["publisher"]["status"] = "conflict"
        if not case["active_qualified_articles"]:
            row["source_policy"].update(admission_status="unreviewed", allow_featured=False)
        annotations[rid] = {"id":rid, **{k:row[k] for k in ("publisher","ingress","source_policy")}, "qualification":q}
        refs.append({**row, "corroboration_key":u.corroboration.identity(row)[0], "role":"active_phase", "phase_id":"phase"})
    event = {"brief_event_id":"synthetic", "active_phase_id":"phase", "eligible":case["time_valid"],
        "effective_at":"2026-10-23T03:00:00Z", "expires_at":"2026-10-24T03:00:00Z",
        "identity":{"subject":"article:synthetic","action":"article"}, "sources":refs,
        "business_events":["model_release"], "primary_item":{"id":"0" if case["summary_same_article"] else "old-primary"}, "news_summary":"Synthetic summary"}
    if not case["projection_valid"]:
        decision = {"featured_eligible":False,"qualified_source_count":0,"eligibility_basis":None,"featured_news_summary":None}
        assert g.unavailable({"generated_at":u.iso(NOW),"state_revision":None,"selected_event_ids":[]},p.current_registry().revision,"invalid_projection")["status"] == "unavailable"
    else:
        decision = g.decide(event, annotations, rows, NOW, lambda *_:case["score"])
    expected = case["expected"]
    assert decision["featured_eligible"] == expected["featured_eligible"]
    assert decision["qualified_source_count"] == expected["qualified_source_count"]
    assert decision["eligibility_basis"] == expected["eligibility_basis"]
    assert bool(decision["featured_news_summary"]) == expected["summary_reused"]


def test_use_badge_comes_from_native_material_without_rewriting_legacy_classification():
    row = article(business_events=[])
    story = u.build_story_record("synthetic", [row], NOW, 24)
    result = u.build_brief_event_payloads([story], [row], b.StateInput("missing"), NOW, 24,
        archive_meta=b.ArchiveMeta("valid",u.iso(NOW)))
    assert result.projection["events"][0]["business_events"] == []
    assert result.publisher_governance["events"][0]["featured_business_events"] == ["model_release"]


def test_unsupported_engine_state_keeps_general_news_and_explicitly_disables_use_overlay():
    row = article(); story = u.build_story_record("synthetic", [row], NOW, 24)
    result = u.build_brief_event_payloads([story], [row], b.StateInput("unsupported"), NOW, 24,
        archive_meta=b.ArchiveMeta("valid",u.iso(NOW)))
    daily, merged = {}, {"stories":[story]};u.apply_brief_event_result(result,daily,merged)
    assert merged["stories"] == [story]
    assert merged["publisher_governance"]["status"] == "unavailable"
    assert daily["items"] == [] and daily["publisher_governance_meta"]["status"] == "unavailable"
