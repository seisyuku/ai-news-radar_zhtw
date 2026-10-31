"""Admission is scoped, current, and separate from identity, votes and state."""
import copy
import json
from pathlib import Path
import sys

import pytest
from jsonschema import Draft202012Validator

from scripts import corroboration as c, publisher_policy as p, update_news as u


def row(url="https://reuters.com/news/example", **extra):
    return {"id": "synthetic-policy", "site_id": "curated_media", "source": "Example ingress",
            "title": "Synthetic AI model release", "url": url,
            "published_at": "2026-10-23T03:00:00Z", **extra}


def google(host="reuters.com", name="Reuters", source="DeepSeek (Google News)", site_id="curated_media"):
    item = row("https://news.google.com/rss/articles/synthetic", source=source, site_id=site_id)
    return {**item, **u.publisher_identity.fields(item, feeds=u.publisher_feed_configs(),
            rss_source={"title": name, "href": "https://" + host + "/"})}


def output(item):
    return u.add_reader_source_policy_fields(item)


def policy(item):
    return output(item)["source_policy"]


@pytest.mark.parametrize("url,scope,rank", [
    ("https://www.ithome.com.tw/news/1", "ithome", 1),
    ("https://the-decoder.com/example", "the_decoder", 1),
    ("https://bnext.com.tw/article/1", "bnext", 4),
    ("https://runtimewire.com/article/1", "runtimewire", 4),
    ("https://cnbc.com/a", "cnbc", 2),
    ("https://theinformation.com/a", "the_information", 2),
    ("https://blog.modelcontextprotocol.io/example", "mcp_blog", 0),
    ("https://mistral.ai/news/example", "mistral", 0),
    ("https://developers.openai.com/codex/changelog/example", "openai", 0),
    ("https://github.com/openai/skills/commit/abc", "openai", 0),
])
def test_existing_scoped_decisions_and_pg01_errata_are_preserved(url, scope, rank):
    got = policy(row(url))
    assert (got["scope_id"], got["source_tier_rank"]) == (scope, rank)
    assert got["admission_status"] == "limited"
    assert got["allow_general"] and got["allow_featured"]


@pytest.mark.parametrize("host", ["latintimes.com", "androidheadlines.com", "theaiinsider.tech",
    "nypost.com", "wccftech.com", "fedagent.com", "scmp.com", "computing.co.uk"])
def test_eight_dynamic_publishers_stay_unreviewed_without_new_votes(host):
    original = google(host, "Synthetic returned publisher")
    out = output(original)
    assert out["publisher"]["status"] == "reported"
    assert out["source_policy"]["admission_status"] == "unreviewed"
    assert out["source_tier"] == "watchlist" and out["source_tier_rank"] == 6
    assert out["source_policy"]["allow_general"]
    assert not out["source_policy"]["allow_featured"] and not out["source_policy"]["allow_radar"]
    assert c.identity(out)[0] is None


def test_same_publisher_has_same_scope_and_tier_across_public_and_private_transports():
    variants = [row(), google(), row(site_id="opmlrss", source="Private label")]
    policies = [policy(x) for x in variants]
    assert {x["scope_id"] for x in policies} == {"reuters"}
    assert {x["source_tier_rank"] for x in policies} == {2}
    private = output(variants[-1])
    assert private["ingress"]["source_id"] is None and private["ingress"]["feed_url"] is None
    assert private["ingress"]["name"] == "RSS/OPML"


@pytest.mark.parametrize("url", ["https://meet.bnext.com.tw/article/1", "https://fc.bnext.com.tw/a",
    "https://new.bnext.com.tw/a", "https://unknown.reuters.com/a", "https://reuters.com.evil.org/a",
    "https://github.com/openai/skills-extra/a", "https://github.com/another/repo/a",
    "https://developers.openai.com/other", "https://reuters.com:8443/a",
    "https://user:pass@reuters.com/a", "https://reuters.com/a/../news",
    "https://github.com/openai/skills/%2e%2e/other", "https://github.com/openai%2fskills/a",
    "https://github.com/openai/skills%252fother", "javascript:alert(1)"])
def test_editions_unknown_subdomains_and_ambiguous_paths_do_not_inherit(url):
    got = policy(row(url))
    assert got["admission_status"] == "unreviewed"
    assert got["source_tier_rank"] == 6
    assert not got["allow_featured"] and not got["allow_radar"]


def test_known_legacy_suffix_without_edition_evidence_is_not_admission():
    item = row("https://news.google.com/a", source="數位時代 (Google News)", site_id="tw_media",
               title="Synthetic AI release - 未來商務")
    assert u.add_publisher_identity_fields(item)["publisher"]["status"] == "identified"
    assert policy(item)["admission_status"] == "unreviewed"
    assert policy(google("bnext.com.tw", "數位時代", "數位時代 (Google News)", "tw_media"))["scope_id"] == "bnext"


def test_known_suffix_only_publisher_is_not_quality_approved():
    item = row("https://news.google.com/a", source="Meta AI (Google News)",
               title="Synthetic AI release - Bloomberg")
    assert u.add_publisher_identity_fields(item)["publisher"]["status"] == "identified"
    assert policy(item)["admission_status"] == "unreviewed"


def test_conflicting_fixed_bridge_withdraws_vote_and_never_gets_source_policy_grant():
    item = google("cnbc.com", "CNBC", "Reuters AI (Google News)")
    out = output(item)
    assert out["publisher"]["status"] == "conflict"
    assert out["source_policy"]["admission_status"] == "unreviewed"
    assert "identity_conflict" in out["source_policy"]["reason_codes"]
    assert c.identity(out) == (None, "conflict")


def test_cached_grants_and_forged_publisher_are_rebuilt_without_mutating_input():
    item = google("wccftech.com", "Synthetic publisher")
    item["source_policy"] = policy(row())
    item["publisher"].update(publisher_id="reuters", status="identified")
    before = copy.deepcopy(item)
    out = output(item)
    assert item == before
    assert out["source_policy"]["admission_status"] == "unreviewed"
    assert out["publisher"]["publisher_id"] is None
    assert all(out[k] == before[k] for k in ["id", "source", "site_id", "url", "published_at"])


def test_cn_aggregator_remains_one_vote_and_limited_uses_are_distinct():
    a = output(row("https://aibase.com/news/1", source="AIBASE"))
    k = output(row("https://36kr.com/p/1", source="36Kr", site_id="kr36_ai"))
    assert c.count([a, k]) == 1
    assert a["source_policy"]["allow_featured"] and not k["source_policy"]["allow_featured"]
    assert k["source_tier_rank"] == 6


def test_model_discovery_and_manual_control_do_not_acquire_featured_permission():
    stats = output(row("https://llm-stats.com/models/synthetic", site_id="llm_stats_models",
                       source="LLM Stats Model Releases"))
    control = output(row("https://daily.juya.uk/example", site_id="juya_daily", source="橘鴉AI早報"))
    rumors = output(row("https://llmrumors.com/example", site_id="llm_rumors", source="LLM Rumors"))
    assert stats["source_policy"]["allow_radar"] and not stats["source_policy"]["allow_featured"]
    assert not any(control["source_policy"][k] for k in p.PERMISSIONS)
    assert "control_only" in control["source_policy"]["reason_codes"]
    assert not rumors["source_policy"]["allow_radar"]
    assert policy(row("https://llm-stats.com/ai-news"))["admission_status"] == "unreviewed"
    assert not policy(row("https://llm-stats.com/models/"))["allow_radar"]


def test_archive_overlay_preserves_legacy_ranking_fields_and_excluded_history():
    item = row("https://example.org/a", source_tier="ai_media", source_tier_rank=2)
    before = copy.deepcopy(item)
    archived = u.add_reader_source_policy_fields(item, effective_tier=False)
    reader = output(item)
    assert item == before and archived["source_tier_rank"] == 2
    assert archived["source_policy"]["source_tier_rank"] == reader["source_tier_rank"] == 6
    raw = json.loads(p.REGISTRY_PATH.read_text())
    scope = next(s for s in raw["scopes"] if s["scope_id"] == "reuters")
    scope.update(admission_status="excluded", **{k: False for k in p.PERMISSIONS})
    raw["revision"] = p.registry_revision(raw)
    removed = p.annotate(row(), registry=p.Registry(raw))
    assert removed["id"] and removed["source_policy"]["admission_status"] == "excluded"
    assert not any(removed["source_policy"][k] for k in p.PERMISSIONS)


def test_registry_revision_is_canonical_and_changes_are_read_without_old_grants(tmp_path):
    raw = json.loads(p.REGISTRY_PATH.read_text())
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(raw))
    old = p.load_registry(path)
    scope = next(s for s in raw["scopes"] if s["scope_id"] == "reuters")
    scope.update(admission_status="unreviewed", source_tier="watchlist", source_tier_rank=6,
                 allow_featured=False, allow_radar=False)
    raw["revision"] = p.registry_revision(raw)
    path.write_text(json.dumps(raw, sort_keys=True, indent=4))
    current = p.load_registry(path)
    assert current.revision != old.revision
    assert p.annotate(row(), registry=current)["source_policy"]["admission_status"] == "unreviewed"
    assert current.revision == p.registry_revision(raw)


def test_each_generation_pins_one_revision_and_next_generation_reads_new_policy(monkeypatch):
    first = p.load_registry()
    raw = json.loads(p.REGISTRY_PATH.read_text())
    scope = next(s for s in raw["scopes"] if s["scope_id"] == "reuters")
    scope.update(admission_status="unreviewed", source_tier="watchlist", source_tier_rank=6,
                 allow_featured=False, allow_radar=False)
    raw["revision"] = p.registry_revision(raw)
    second = p.Registry(raw)
    selected = [first]
    monkeypatch.setattr(p, "load_registry", lambda: selected[0])
    with p.generation():
        assert policy(row())["registry_revision"] == first.revision
        selected[0] = second
        assert policy(row())["admission_status"] == "limited"
    with p.generation():
        assert policy(row())["registry_revision"] == second.revision
        assert policy(row())["admission_status"] == "unreviewed"


@pytest.mark.parametrize("change", ["revision", "version", "unknown_grant", "duplicate_scope", "wildcard_host", "path_escape", "control_grant"])
def test_invalid_registry_is_rejected_instead_of_using_cached_permissions(change):
    raw = json.loads(p.REGISTRY_PATH.read_text())
    if change == "revision": raw["revision"] = "0" * 64
    elif change == "version": raw["schema_version"] = 2
    elif change == "unknown_grant": raw["default"]["allow_featured"] = True
    elif change == "duplicate_scope": raw["scopes"].append(copy.deepcopy(raw["scopes"][0]))
    elif change == "wildcard_host": raw["scopes"][0]["hosts"][0]["host"] = "*.reuters.com"
    elif change == "path_escape": raw["scopes"][0]["hosts"][0]["path_prefix"] = "/a/../b"
    elif change == "control_grant": next(s for s in raw["scopes"] if s["scope_id"] == "juya")["allow_general"] = True
    if change != "revision": raw["revision"] = p.registry_revision(raw)
    with pytest.raises(ValueError): p.Registry(raw)


def test_policy_output_matches_frozen_schema_and_no_qualification_overlay_is_emitted():
    schema = json.loads((Path(__file__).resolve().parents[1] / "docs/contracts/publisher-governance-v1.schema.json").read_text())
    validator = Draft202012Validator({**schema, "$ref": "#/$defs/source_policy"})
    for item in [row(), google("example.org", "Unknown"), google(), row("https://meet.bnext.com.tw/a")]:
        got = output(item)
        validator.validate(got["source_policy"])
        assert "qualification" not in got and "publisher_governance" not in got


def test_story_output_overlay_leaves_original_scores_selection_and_inputs_unchanged():
    now = u.parse_iso("2026-10-23T03:35:27Z")
    article = google("example.org", "Unknown")
    story = u.build_story_record("synthetic-story", [article], now, 24)
    before = copy.deepcopy(story)
    merged = u.build_stories_payload([story], u.iso(now), 24)
    daily = u.build_daily_brief_payload([story], u.iso(now), 24)
    assert story == before
    shown = merged["stories"][0]
    assert shown["score"] == before["score"]
    assert shown["primary_item"]["source_tier_rank"] == 6
    assert shown["sources"][0]["source_policy"]["admission_status"] == "unreviewed"
    assert daily["total_items"] == int(u.story_passes_brief_gate(story))


def test_offline_generation_filters_forbidden_general_scopes_but_retains_archive_and_event_evidence(tmp_path, monkeypatch):
    now = u.parse_iso("2026-10-23T03:35:27Z")
    raw_policy = json.loads(p.REGISTRY_PATH.read_text())
    scope = next(s for s in raw_policy["scopes"] if s["scope_id"] == "the_verge")
    scope.update(admission_status="excluded", **{k: False for k in p.PERMISSIONS})
    raw_policy["revision"] = p.registry_revision(raw_policy)
    registry = p.Registry(raw_policy)
    monkeypatch.setattr(p, "load_registry", lambda: registry)
    raws = [u.RawItem(site_id="curated_media", site_name="精選媒體", source=source,
             title=f"OpenAI releases GPT-6.1 Sol AI model for {suffix}", url=url,
             published_at=now, meta={}) for source, url, suffix in [
                 ("Reuters AI (Google News)", "https://reuters.com/synthetic", "developers"),
                 ("The Verge", "https://theverge.com/synthetic", "researchers")]]
    raws.append(u.RawItem(site_id="juya_daily", site_name="對照源", source="橘鴉AI早報",
        title="OpenAI releases GPT-6.1 Sol AI model overview", url="https://daily.juya.uk/synthetic",
        published_at=now, meta={}))
    archive = {}
    u.merge_raw_items_into_archive(archive, raws, now)
    out = tmp_path / "data"; out.mkdir()
    (out / "archive.json").write_text(json.dumps({"generated_at": u.iso(now), "items": list(archive.values())}))
    monkeypatch.setattr(u, "utc_now", lambda: now)
    monkeypatch.setattr(u, "create_session", lambda: object())
    monkeypatch.setattr(u, "collect_all", lambda *_: (raws, [
        {"site_id": "curated_media", "site_name": "精選媒體", "ok": True, "item_count": 2},
        {"site_id": "juya_daily", "site_name": "對照源", "ok": True, "item_count": 1}]))
    monkeypatch.setattr(u, "run_market_sensors", lambda *_: ({"generated_at": u.iso(now), "signals": []}, {}, []))
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_TRANSLATE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("requests.sessions.Session.request", lambda *_a, **_k: pytest.fail("network forbidden"))
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(out), "--translate-max-new", "0"])
    assert u.main() == 0
    read = lambda name: json.loads((out / name).read_text())
    public_archive = read("archive.json")["items"]
    assert len(public_archive) == 3
    assert {r["id"] for r in public_archive} == set(archive)
    for name in ["latest-24h.json", "latest-24h-all.json"]:
        payload = read(name)
        for key in ["items", "items_ai", "items_all", "items_all_raw"]:
            assert all(r["source"] == raws[0].source for r in payload.get(key, []))
        assert payload["total_items_raw"] == 1
    assert all(r["source_policy"]["registry_revision"] == registry.revision for r in public_archive)
    excluded = next(r for r in public_archive if r["source"] == "The Verge")
    assert excluded["source_policy"]["admission_status"] == "excluded"
    assert (out / "items" / (excluded["id"] + ".json")).exists()
    assert all(s["ok"] for s in read("source-status.json")["sites"])
    assert read("stories-merged.json")["publisher_governance"]["status"] == "ready"
