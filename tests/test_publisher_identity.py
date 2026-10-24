"""Publisher provenance must survive output without granting admission or votes."""
import copy
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts import brief_events as b, corroboration as c, publisher_identity as p, update_news as u


NOW = u.parse_iso("2026-10-23T03:35:27Z")
RSS = b'''<rss version="2.0"><channel><title>Example query</title>
<item><title>Example AI model release - Example News</title>
<link>https://news.google.com/rss/articles/example</link>
<pubDate>Fri, 23 Oct 2026 03:00:00 GMT</pubDate>
<source url="https://example.org/">Example News</source>
<description>Example AI model announcement.</description></item></channel></rss>'''


def row(source="DeepSeek (Google News)", url="https://news.google.com/rss/articles/example", **extra):
    return {"id": "a" * 40, "site_id": "curated_media", "source": source,
            "title": "Example AI model release", "url": url,
            "published_at": u.iso(NOW), **extra}


def annotated(record=None, name="Example News", href="https://example.org/"):
    record = row() if record is None else record
    return {**record, **p.fields(record, feeds=u.publisher_feed_configs(),
                               rss_source={"title": name, "href": href})}


def validate_components(record):
    schema = json.loads((Path(__file__).resolve().parents[1] /
                         "docs/contracts/publisher-governance-v1.schema.json").read_text())
    for key in ("publisher", "ingress"):
        Draft202012Validator({**schema, "$ref": f"#/$defs/{key}"},
                             format_checker=FormatChecker()).validate(record[key])


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("namespaced", [False, True])
def test_both_rss_parsers_preserve_source_through_archive_and_public_fields(monkeypatch, fallback, namespaced):
    if fallback:
        monkeypatch.setattr(u, "feedparser", None)
    rss = RSS.replace(b'<rss version="2.0">', b'<rss version="2.0" xmlns="urn:example:rss">') if namespaced else RSS
    feed = next(f for f in u.CURATED_AI_MEDIA_FEEDS if f["source_id"] == "deepseek_news")
    raws = u.parse_curated_ai_media_feed_items(rss, feed, NOW)
    assert len(raws) == 1
    assert raws[0].meta["rss_source"] == {"title": "Example News", "href": "https://example.org/"}
    archive = {}
    u.merge_raw_items_into_archive(archive, raws, NOW)
    item = next(iter(archive.values()))
    assert item["source"] == "DeepSeek (Google News)"
    assert item["publisher"]["name"] == "Example News"
    assert item["publisher"]["status"] == "reported"
    assert item["publisher"]["evidence"]["article_url"] is None
    assert item["ingress"]["source_id"] == "deepseek_news"
    assert c.identity(item) == (None, "unknown")
    assert "source_policy" not in item
    validate_components(item)


@pytest.mark.parametrize("fallback", [False, True])
def test_atom_source_namespace_metadata_is_preserved(fallback):
    atom = b'''<feed xmlns="http://www.w3.org/2005/Atom">
    <entry><title>Example AI</title><link href="https://example.org/a"/>
    <updated>2026-10-23T03:00:00Z</updated><source><title>Original Feed</title>
    <link href="https://example.org/"/></source></entry></feed>'''
    entries = u.parse_feed_entries_via_xml(atom) if fallback else u.feedparser.parse(atom).entries
    assert p.feed_source(entries[0]) == {"title": "Original Feed", "href": "https://example.org/"}


def test_public_non_google_source_provenance_is_retained_without_overriding_article_host():
    item = annotated(row(site_id="official_ai", source="OpenAI News", url="https://openai.com/news/a"))
    assert item["publisher"]["name"] == "OpenAI"
    assert item["publisher"]["domain"] == "openai.com"
    assert item["publisher"]["evidence"]["rss_source_name"] == "Example News"
    assert c.identity(item)[0] == "publisher:openai"


def test_known_rss_host_can_be_identified_without_creating_a_new_vote():
    item = annotated(name="Reuters", href="https://www.reuters.com/")
    assert item["publisher"]["publisher_id"] == "reuters"
    assert item["publisher"]["status"] == "identified"
    assert item["publisher"]["basis"] == ["google_rss_source"]
    assert c.identity(item) == (None, "unknown")  # Same bounded legacy key set.
    validate_components(item)


@pytest.mark.parametrize("name,href", [("CNBC", "https://cnbc.com/"),
                                       ("Example News", "https://example.org/")])
def test_fixed_bridge_contradiction_withdraws_old_vote(name, href):
    original = row(source="Reuters AI (Google News)")
    assert c.identity(original) == ("publisher:reuters", "identified")
    item = annotated(original, name, href)
    assert item["publisher"]["status"] == "conflict"
    assert item["publisher"]["publisher_id"] is None
    assert c.identity(item) == (None, "conflict")
    validate_components(item)


def test_name_and_host_conflict_is_not_hidden_by_unknown_legacy_identity():
    item = annotated(name="Reuters", href="https://www.cnbc.com/")
    assert item["publisher"]["status"] == "conflict"
    assert c.identity(item) == (None, "conflict")


@pytest.mark.parametrize("bad", ["javascript:alert(1)", "https://user:pass@reuters.com/",
                                "https://127.0.0.1/", "https://localhost/", "https://a.local/",
                                "https://a.internal/", "https://a.invalid/", "https://[::1]/",
                                "https://reuters.com:99999/", "https://reuters.com\\@evil.org/",
                                "https://reuters.com/\nsecret"])
def test_invalid_or_private_source_urls_cannot_create_identity(bad):
    item = annotated(href=bad)
    assert item["publisher"]["status"] == "unknown"
    assert item["publisher"]["evidence"]["rss_source_url"] is None
    assert c.identity(item)[0] is None


def test_lookalike_host_does_not_inherit_reuters():
    item = annotated(name="Reuters", href="https://reuters.com.evil.example/")
    assert item["publisher"]["status"] == "reported"
    assert item["publisher"]["publisher_id"] is None
    assert c.identity(item)[0] is None


def test_private_opml_labels_and_forged_bridge_metadata_are_not_authority():
    item = annotated(row(site_id="opmlrss", source="Private Person Secret Feed"),
                     "Reuters", "https://reuters.com/")
    assert item["ingress"] == {"kind": "private_opml", "site_id": "opmlrss", "source_id": None,
                               "name": "RSS/OPML", "feed_url": None}
    assert item["publisher"]["name"] is None
    assert item["publisher"]["evidence"]["rss_source_url"] is None
    assert "Private Person" not in json.dumps({k: item[k] for k in ("ingress", "publisher")})
    validate_components(item)


def test_private_opml_known_public_article_host_still_identifies_publisher():
    item = annotated(row(site_id="opmlrss", source="Private label", url="https://reuters.com/a"))
    assert item["publisher"]["name"] == "Reuters"
    assert item["publisher"]["evidence"]["article_url"] == "https://reuters.com/a"
    assert c.identity(item)[0] == "publisher:reuters"


@pytest.mark.parametrize("url,name", [("https://aibase.com/a", "AIBASE"),
                                      ("https://36kr.com/a", "36Kr")])
def test_cn_group_identity_displays_actual_publisher_on_other_ingresses(url, name):
    item = annotated(row(site_id="opmlrss", source="Private label", url=url))
    assert item["publisher"]["name"] == name
    assert c.identity(item)[0] == "cn_aggregator"


@pytest.mark.parametrize("source,url,key", [
    ("AIBASE", "https://aibase.com/a", "cn_aggregator"),
    ("Reuters AI (Google News)", "https://news.google.com/a", "publisher:reuters"),
    ("CNBC Technology", "https://cnbc.com/a", "publisher:cnbc"),
])
def test_old_records_keep_ids_dates_urls_tiers_and_votes_without_new_metadata(source, url, key):
    original = row(source=source, url=url, source_tier="ai_media", source_tier_rank=2)
    before = copy.deepcopy(original)
    item = u.add_publisher_identity_fields(original)
    assert original == before
    assert all(item[k] == value for k, value in original.items())
    assert c.identity(item)[0] == key
    assert item["publisher"]["status"] == "identified"
    validate_components(item)


def test_epoch_configured_identity_does_not_add_a_corroboration_key():
    item = annotated(row(source="Epoch AI (Google News)"), "Epoch AI", "https://epoch.ai/")
    assert item["publisher"]["publisher_id"] == "epoch"
    assert c.identity(item)[0] is None


def test_epoch_fixed_bridge_cannot_silently_accept_another_publisher():
    item = annotated(row(source="Epoch AI (Google News)"), "Reuters", "https://reuters.com/")
    assert item["publisher"]["status"] == "conflict"
    assert c.identity(item) == (None, "conflict")


def test_openai_skills_host_and_path_are_direct_article_evidence():
    item = u.add_publisher_identity_fields(row(site_id="official_ai", source="OpenAI Skills",
        url="https://github.com/openai/skills/commit/example"))
    assert item["publisher"]["basis"] == ["article_host"]
    assert item["publisher"]["evidence"]["article_url"] == item["url"]


def test_withdrawn_vote_does_not_reinterpret_event_phases_or_history():
    original = row(source="Reuters AI (Google News)",
                   title="OpenAI releases GPT-6.1 Sol AI model for developers")
    conflicting = annotated(original)
    before, after = b.extract_claim(original, NOW), b.extract_claim(conflicting, NOW)
    assert c.identity(original)[0] == "publisher:reuters"
    assert c.identity(conflicting) == (None, "conflict")
    assert (before.key, before.phase, before.effective, before.unknown_update) == (
        after.key, after.phase, after.effective, after.unknown_update)
    results = []
    for item in (original, conflicting):
        story = u.build_story_record("same-story", [item], NOW, 24)
        results.append(u.build_brief_event_payloads([story], [item], b.StateInput("missing"),
                       NOW, 24, archive_meta=b.ArchiveMeta("valid", u.iso(NOW))))
    assert results[0].next_state == results[1].next_state
    assert results[0].next_state is not None
    assert results[0].projection["events"][0]["corroboration_count"] == 1
    assert results[1].projection["events"][0]["corroboration_count"] == 0


def test_names_are_bounded_plain_text_and_hosts_are_idna_normalized():
    item = annotated(name="<b>Example</b>\n" + "X" * 250, href="https://B\u00dcCHER.example./")
    assert item["publisher"]["name"].startswith("Example X")
    assert len(item["publisher"]["name"]) == 160
    assert item["publisher"]["domain"] == "xn--bcher-kva.example"


def test_mcp_and_mistral_use_actual_official_ingress_not_collector_status_id():
    for source, sid, url in [("MCP Blog", "mcp_blog", "https://blog.modelcontextprotocol.io/a"),
                             ("Mistral News", "mistral_news", "https://mistral.ai/news/a")]:
        item = u.add_publisher_identity_fields(row(site_id="official_ai", source=source, url=url))
        assert item["ingress"]["source_id"] == sid
        assert u.source_tier_for_record(item)["source_tier_rank"] == 0


def test_story_and_radar_serialization_keep_actual_publisher():
    item = c.annotate(annotated())
    item.update(ai_is_related=True, ai_score=.8, business_events=["model_release"])
    story = u.build_story_record("example-story", [item], NOW, 24)
    for ref in [story["primary_item"], *story["sources"]]:
        assert ref["publisher"]["name"] == "Example News"
        assert ref["source"] == item["source"]
    radar = u.build_llm_radar_payload([item], NOW)
    assert radar["events"] == []  # Reported names are visible in general news, not admitted to radar.


def test_resolver_outputs_keep_identity_and_original_archive_unmodified(tmp_path):
    item = annotated()
    original = copy.deepcopy(item)
    output = tmp_path / "data"
    output.mkdir()
    u.write_item_resolvers(output, {item["id"]: item})
    u.write_item_html_adapters(output, {item["id"]: item})
    saved = json.loads((output / "items" / f'{item["id"]}.json').read_text())
    assert saved["publisher"]["name"] == "Example News"
    page = (tmp_path / "item" / item["id"] / "index.html").read_text()
    assert "Example News" in page and "DeepSeek (Google News)" in page
    assert item == original


def test_offline_main_propagates_fresh_rss_source_to_all_outputs(tmp_path, monkeypatch):
    feed = next(f for f in u.CURATED_AI_MEDIA_FEEDS if f["source_id"] == "deepseek_news")
    rss = RSS.replace(b"Example AI model release - Example News", b"OpenAI releases GPT-6.1 Sol AI model - Example News")
    raw = u.parse_curated_ai_media_feed_items(rss, feed, NOW)[0]
    output = tmp_path / "data"
    output.mkdir()
    previous = {}
    u.merge_raw_items_into_archive(previous, [raw], NOW)
    (output / "archive.json").write_text(json.dumps({"generated_at": u.iso(NOW), "items": list(previous.values())}))
    monkeypatch.setattr(u, "utc_now", lambda: NOW)
    monkeypatch.setattr(u, "create_session", lambda: object())
    monkeypatch.setattr(u, "collect_all", lambda *_: ([raw], [
        {"site_id": "curated_media", "site_name": "精選媒體", "ok": True, "item_count": 1}]))
    monkeypatch.setattr(u, "run_market_sensors", lambda *_: ({"generated_at": u.iso(NOW), "signals": []}, {}, []))
    for name in ("maybe_fetch_x_api_updates", "maybe_fetch_socialdata_updates", "maybe_fetch_tikhub_updates"):
        monkeypatch.setattr(u, name, lambda *_: ([], {"enabled": False}))
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_TRANSLATE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("requests.sessions.Session.request", lambda *_a, **_k: pytest.fail("network forbidden"))
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(output), "--translate-max-new", "0"])
    assert u.main() == 0
    archive = json.loads((output / "archive.json").read_text())["items"]
    latest = json.loads((output / "latest-24h.json").read_text())["items_ai"]
    merged = json.loads((output / "stories-merged.json").read_text())
    assert archive and latest and merged["brief_events"]["events"]
    refs = [*archive, *latest, *merged["stories"][0]["sources"],
            merged["stories"][0]["primary_item"], *merged["brief_events"]["events"][0]["sources"],
            merged["brief_events"]["events"][0]["primary_item"]]
    for item in refs:
        assert item["publisher"]["name"] == "Example News"
        assert item["source"] == raw.source
        assert item["source_policy"]["admission_status"] == "unreviewed"
        assert not item["source_policy"]["allow_featured"]
        validate_components(item)
