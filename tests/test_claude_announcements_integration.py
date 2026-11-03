"""Collector, scoped governance and public contracts for Claude announcements."""
import copy
import json
import sys

import pytest

from scripts import brief_events as b, corroboration as c, publisher_policy as p
from scripts import signal_selection, update_news as u
from tests.js_bridge import run_js
from tests.test_claude_product_announcements import NOW, ROW, page
from tests.test_group_source_status import Session


SOURCE_ID = "claude_product_announcements"
URL = "https://claude.com/resources/articles/message-threads"


def session(index=None, *, anthropic=None):
    return Session({
        u.CLAUDE_PRODUCT_ANNOUNCEMENTS_URL: page().encode() if index is None else index,
        "https://www.anthropic.com/news": (
            b'<a href="/news/previous"><h3>Previous Anthropic announcement</h3>'
            b'<time datetime="2026-11-02"></time></a>' if anthropic is None else anthropic),
        u.TENCENT_NEWSROOM_URL: (
            b'<article class="tc-blog-grid"><h2 class="blog-title"><a href="/old">Old AI news</a></h2>'
            b'<span class="tc-blogpost-date">2021-01-01</span></article>'),
        "https://developers.openai.com/codex/changelog":
            b'<li id="old"><h3>Old AI news</h3><time datetime="2021-01-01"></time></li>',
    })


def article():
    archive = {}
    u.merge_raw_items_into_archive(archive, u.parse_claude_product_announcements_items(page(), NOW, require_valid=True), NOW)
    return next(iter(archive.values()))


@pytest.mark.parametrize("index,error", [
    (RuntimeError("secret must not be published"), "fetch_failed"),
    (b"<html>index structure changed</html>", "invalid_source"),
])
def test_new_child_failure_keeps_anthropic_news_and_has_its_own_history(monkeypatch, index, error):
    monkeypatch.setattr(u, "OFFICIAL_AI_FEEDS", ())
    items, details = u.fetch_official_ai_updates_with_status(session(index), NOW)
    assert len(items) == 1 and items[0].source == "Anthropic News"
    assert details["ok"] and details["degraded_reason"] == "partial_subsource_failure"
    rows = {s["source_id"]: s for s in details["subsources"]}
    assert rows["anthropic_news"]["ok"]
    assert not rows[SOURCE_ID]["ok"] and rows[SOURCE_ID]["error"] == error
    sites = [{"site_id": "official_ai", **details}]
    u.apply_source_health_history(sites, {}, NOW)
    previous = {"sites": copy.deepcopy(sites)}
    items, recovered = u.fetch_official_ai_updates_with_status(session(), NOW + u.timedelta(minutes=30))
    recovered_sites = [{"site_id": "official_ai", **recovered}]
    u.apply_source_health_history(recovered_sites, previous, NOW + u.timedelta(minutes=30))
    child = next(s for s in recovered["subsources"] if s["source_id"] == SOURCE_ID)
    assert child["consecutive_failures"] == 0 and child["last_success_at"]
    assert not recovered["degraded"] and "secret" not in json.dumps(sites)


def test_new_child_keeps_working_when_old_anthropic_endpoint_fails(monkeypatch):
    monkeypatch.setattr(u, "OFFICIAL_AI_FEEDS", ())
    items, details = u.fetch_official_ai_updates_with_status(session(anthropic=RuntimeError("down")), NOW)
    assert len(items) == 1 and items[0].url == URL
    assert details["ok"] and details["degraded"]
    assert next(s for s in details["subsources"] if s["source_id"] == SOURCE_ID)["ok"]


@pytest.mark.parametrize("rows", [
    [], [dict(ROW, date="2021-01-01")], [dict(ROW, date="2026-11-03")],
    [dict(ROW, _type="video")], [dict(ROW, externalUrl="https://www.anthropic.com/news/example")],
])
def test_valid_zero_child_does_not_degrade_the_group(monkeypatch, rows):
    monkeypatch.setattr(u, "OFFICIAL_AI_FEEDS", ())
    _, details = u.fetch_official_ai_updates_with_status(session(page(rows).encode()), NOW)
    child = next(s for s in details["subsources"] if s["source_id"] == SOURCE_ID)
    assert child["ok"] and child["item_count"] == 0 and not details["degraded"]


@pytest.mark.parametrize("site_id,source", [
    ("official_ai", "Claude Product Announcements"),
    ("official_ai", "Anthropic News"),
    ("opmlrss", "Private feed label"),
])
def test_known_article_is_official_across_transports_without_an_extra_publisher_vote(site_id, source):
    row = dict(article(), site_id=site_id, source=source)
    out = u.add_reader_source_policy_fields(row)
    assert out["publisher"]["publisher_id"] == "anthropic"
    assert out["publisher"]["status"] == "identified"
    policy = out["source_policy"]
    assert policy["scope_id"] == "anthropic" and policy["admission_status"] == "limited"
    assert policy["source_tier_rank"] == 0 and all(policy[k] for k in p.PERMISSIONS)
    peer = dict(row, source="Anthropic News", site_id="official_ai", url="https://www.anthropic.com/news/message-threads")
    assert c.identity(out) == c.identity(peer) == ("publisher:anthropic", "identified")
    assert c.count([out, peer]) == 1
    if site_id == "official_ai" and source == "Claude Product Announcements":
        assert out["ingress"]["source_id"] == SOURCE_ID and out["ingress"]["kind"] == "public_adapter"


@pytest.mark.parametrize("url", [
    "https://claude.com/resources/guides/example",
    "https://claude.com/resources/articles",
    "https://claude.com/resources/articles/",
    "https://claude.com/resources/articles-extra/example",
    "https://claude.com/blog/example",
    "https://claude.com/",
    "https://www.claude.com/resources/articles/example",
    "https://unknown.claude.com/resources/articles/example",
    "https://claude.com.evil.example/resources/articles/example",
    "https://claude.com:8443/resources/articles/example",
    "https://user:pass@claude.com/resources/articles/example",
    "https://claude.com/resources/articles/../guides/example",
    "https://claude.com/resources/articles%2fexample",
])
def test_article_scope_does_not_grant_whole_site_subdomains_or_lookalikes(url):
    out = u.add_reader_source_policy_fields(dict(article(), url=url))
    assert out["source_policy"]["admission_status"] == "unreviewed"
    assert not out["source_policy"]["allow_featured"] and not out["source_policy"]["allow_radar"]


def test_source_label_alone_cannot_grant_identity_and_other_publishers_conflict():
    assert c.identity(dict(article(), url="https://example.com/article")) == (None, "unknown")
    out = u.add_reader_source_policy_fields(dict(article(), url="https://openai.com/index/example"))
    assert out["publisher"]["status"] == "conflict"
    assert not out["source_policy"]["allow_featured"]


def test_anthropic_scope_retains_existing_permissions_and_records_the_new_transport():
    registry = p.load_registry()
    row = dict(article(), source="Anthropic News", url="https://www.anthropic.com/news/example")
    out = u.add_reader_source_policy_fields(row)
    assert out["source_policy"]["scope_id"] == "anthropic"
    assert all(out["source_policy"][key] for key in p.PERMISSIONS)
    scope = next(s for s in registry.scopes if s["scope_id"] == "anthropic")
    assert {"official_ai/anthropic_news", "official_ai/" + SOURCE_ID} <= set(scope["retained_source_keys"])
    assert not {"source_published_date", "source_time_precision"} & u.story_item_link({k:v for k,v in row.items()
        if k not in {"source_published_date", "source_time_precision"}}).keys()


@pytest.mark.parametrize("changed_url,reworded,expected", [
    (False, False, 1), (False, True, 1), (True, False, 1), (True, True, 2),
])
def test_duplicate_boundaries_and_publisher_count_stay_explicit(changed_url, reworded, expected):
    first = article()
    second = dict(first, source="Anthropic News",
        title="Introducing message threads on the Claude Platform" if reworded else first["title"],
        url="https://www.anthropic.com/news/message-threads" if changed_url else first["url"])
    second["id"] = u.make_item_id(second["site_id"], second["source"], second["title"], second["url"])
    rows = [first, second]
    dedup = u.dedupe_items_by_title_url(rows, random_pick=False)
    scored = [c.annotate(u.add_source_tier_fields(u.add_ai_relevance_fields(r))) for r in dedup]
    stories = u.merge_story_items(scored, NOW, 24)
    result = u.build_brief_event_payloads(stories, rows, b.StateInput("missing"), NOW, 24,
                                         archive_meta=b.ArchiveMeta("valid", u.iso(NOW)))
    assert len(result.projection["events"]) == expected
    assert all(e["corroboration_count"] == 1 for e in result.projection["events"])
    assert signal_selection.validate(result.publisher_governance, result.projection)


@pytest.mark.parametrize("expired", [False, True])
def test_full_generator_preserves_precision_resolvers_and_window_without_live_network(tmp_path, monkeypatch, expired):
    now = u.parse_iso("2026-11-03T00:46:04Z") if expired else NOW
    monkeypatch.setattr(u, "OFFICIAL_AI_FEEDS", ())
    fake = session(anthropic=b'<a href="/news/old"><h3>Old announcement</h3><time datetime="2021-01-01"></time></a>')
    monkeypatch.setattr(u, "create_session", lambda: fake)
    monkeypatch.setattr(u, "utc_now", lambda: now)
    def collect(s, clock):
        raws, detail = u.fetch_official_ai_updates_with_status(s, clock)
        return raws, [{"site_id": "official_ai", "site_name": "Official AI Updates", "item_count": len(raws), **detail}]
    monkeypatch.setattr(u, "collect_all", collect)
    monkeypatch.setattr(u, "run_market_sensors", lambda *_: ({"generated_at": u.iso(now), "signals": []}, {}, []))
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_TRANSLATE_API_KEY"):
        monkeypatch.setenv(key, "")
    monkeypatch.setattr("requests.sessions.Session.request", lambda *_a, **_k: pytest.fail("live network forbidden"))
    out = tmp_path / "data"
    out.mkdir()
    legacy = dict(article(), id="a" * 40, source="Anthropic News", url="https://www.anthropic.com/news/legacy",
                  published_at="2026-10-28T00:00:00Z")
    legacy.pop("source_time_precision"); legacy.pop("source_published_date")
    (out / "archive.json").write_text(json.dumps({"generated_at": u.iso(now), "items": [legacy]}))
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(out), "--translate-max-new", "0"])
    assert u.main() == 0
    read = lambda filename: json.loads((out / filename).read_text())
    archive = read("archive.json")["items"]
    row = next(r for r in archive if r["url"] == URL)
    assert row["id"] == article()["id"] and row["published_at"] == "2026-11-02T00:00:00Z"
    refs = [row, read("items/" + row["id"] + ".json")]
    previous = next(r for r in archive if r["id"] == legacy["id"])
    assert all(previous[k] == legacy[k] for k in ("id", "url", "published_at", "first_seen_at"))
    assert "source_time_precision" not in previous
    all_data, latest, merged, daily = (read(name) for name in
        ("latest-24h-all.json", "latest-24h.json", "stories-merged.json", "daily-brief.json"))
    for payload, keys in [(latest, ("items", "items_ai")), (all_data, ("items_all", "items_all_raw"))]:
        for key in keys:
            assert len(payload[key]) == (0 if expired else 1)
            refs.extend(payload[key])
    assert not daily["items"]  # No score/selection override for this announcement.
    if not expired:
        for event in merged["brief_events"]["events"]:
            refs.extend(event["sources"])
        trace = next(r for r in read("source-status.json")["news_quality"]["articles"] if r["url"] == URL)
        assert trace["in_raw_pool"] and trace["in_ai_pool"]
    for ref in refs:
        assert ref["source_published_date"] == "2026-11-02" and ref["source_time_precision"] == "date"
        assert ref["publisher"]["publisher_id"] == "anthropic"
    assert merged["publisher_governance"]["status"] == "ready"
    valid = run_js("const G=require('./assets/publisher-governance.js');const parent=" + json.dumps(merged)
                   + ";console.log(JSON.stringify({valid:G.valid(parent,Date.parse(parent.generated_at))}));")
    assert valid["valid"]
    child = next(s for s in read("source-status.json")["sites"][0]["subsources"] if s["source_id"] == SOURCE_ID)
    assert child["ok"] and child["item_count"] == 1
