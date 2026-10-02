"""F04/F05/F08/F09/F13-F15: evidence must be isolated before merging."""

from copy import deepcopy
from itertools import permutations
import json
from types import MappingProxyType

import pytest

from scripts.digest_input import DigestInput, load_digest_input
from scripts.digest_pipeline import build_digest_stories
from scripts.digest_window import window_for_date
from scripts import update_news as news


WINDOW = window_for_date("2026-10-02")


def row(item_id, **changes):
    record = {
        "id": item_id, "site_id": "official_ai", "site_name": "Official AI",
        "source": "OpenAI News", "title": "OpenAI releases a new Codex cloud agent",
        "url": f"https://example.invalid/{item_id}",
        "published_at": "2026-10-01T10:00:00Z",
        "summary": "OpenAI released the new Codex cloud agent for teams.",
    }
    record.update(changes)
    return record


def snapshot(rows):
    return DigestInput({r["id"]: deepcopy(r) for r in rows}, {}, None, (), (), "fixture", MappingProxyType({}))


def counts(result):
    return {d.code: d.count for d in result.diagnostics}


@pytest.mark.parametrize("published_at,include", [
    ("2026-10-01T05:59:59+08:00", False),
    ("2026-10-01T06:00:00+08:00", True),
    ("2026-10-02T05:59:59.999999+08:00", True),
    ("2026-10-02T06:00:00+08:00", False),
    ("2026-10-02T07:00:00+08:00", False),
])
def test_publish_window_has_no_reader_future_tolerance(published_at, include):
    result = build_digest_stories(snapshot([row("one", published_at=published_at)]), WINDOW)
    assert bool(result.stories) is include
    assert counts(result) == ({} if include else {"outside_window": 1})


@pytest.mark.parametrize("timestamp,code", [
    (None, "missing_timestamp"), ("", "missing_timestamp"), ("bad", "invalid_timestamp"),
    ("2026-10-01", "date_only"), ("2026-10-01T10:00:00", "naive_timestamp"),
])
def test_first_seen_does_not_rescue_invalid_publish_time(timestamp, code):
    result = build_digest_stories(snapshot([row("bad", published_at=timestamp, first_seen_at="2026-10-01T21:00:00Z", last_seen_at="2026-10-01T21:00:00Z")]), WINDOW)
    assert not result.stories and not result.items
    assert counts(result) == {code: 1}


def test_late_discovery_is_admitted_but_outside_evidence_never_merges():
    inside = row("inside", published_at="2026-10-01T21:59:59Z", first_seen_at="2026-10-02T02:00:00Z")
    before = row("before", published_at="2026-09-30T21:59:59Z", site_id="curated_media")
    after = row("after", published_at="2026-10-01T22:00:00Z", site_id="curated_media")
    for item in [before, after]:
        item["url"] = inside["url"]
        item["summary"] = "Outside-window evidence must not enter the story."
    result = build_digest_stories(snapshot([inside, before, after]), WINDOW)
    assert len(result.stories) == 1
    assert [s["id"] for s in result.stories[0]["sources"]] == ["inside"]
    assert result.stories[0]["source_count"] == 1
    assert counts(result) == {"outside_window": 2}


def test_aliases_are_excluded_for_all_sites_and_ids_stay_unchanged():
    result = build_digest_stories(snapshot([row("real"), row("alias", duplicate_of="real")]), WINDOW)
    assert {item["id"] for item in result.items} == {"real"}
    assert result.stories[0]["primary_item"]["id"] == "real"
    assert counts(result) == {"duplicate_alias": 1}


@pytest.mark.parametrize("changes,code", [
    ({"title": " "}, "invalid_title"), ({"title": ["bad"]}, "invalid_title"),
    ({"url": None}, "invalid_url"), ({"url": "ftp://example.invalid/news"}, "invalid_url"),
    ({"url": "https://"}, "invalid_url"), ({"url": "https://example.invalid/a b"}, "invalid_url"),
    ({"url": "http://[bad"}, "invalid_url"),
])
def test_missing_title_and_unusable_evidence_link_are_counted(changes, code):
    result = build_digest_stories(snapshot([row("bad", **changes)]), WINDOW)
    assert not result.stories
    assert counts(result) == {code: 1}


@pytest.mark.parametrize("rows", [[], [row("old", published_at="2026-09-01T10:00:00Z")], [row("noise", site_id="test_source", site_name="Local News", source="Local News", title="City council approves new local park", summary="New trees in the local park.")]])
def test_empty_outside_or_non_ai_inputs_are_valid_empty_days(rows):
    result = build_digest_stories(snapshot(rows), WINDOW)
    assert result.stories == () and result.items == ()
    if rows and rows[0]["id"] == "noise":
        assert counts(result) == {"not_ai_related": 1}


def test_unknown_publisher_is_not_invented_from_url():
    result = build_digest_stories(snapshot([row("one", source=None)]), WINDOW)
    assert result.stories[0]["source"] == "未標示來源"


def test_same_url_tracking_duplicates_keep_existing_reader_winner_policy():
    rows = [row("a", url="https://example.invalid/event?utm_source=rss"), row("b", site_id="curated_media", source="Some Media", url="https://example.invalid/event?ref=feed")]
    result = build_digest_stories(snapshot(rows), WINDOW)
    assert len(result.items) == 1 and len(result.stories) == 1
    assert result.items[0]["id"] == "a"
    assert result.items[0]["url"] == "https://example.invalid/event"
    assert counts(result) == {"reader_dedup_or_limit": 1}


def test_same_event_different_sources_merge_but_model_versions_do_not():
    rows = [
        row("a", title="OpenAI launches GPT-5 model for coding agents"),
        row("b", site_id="curated_media", source="Some Media", title="OpenAI launches GPT-5 models for coding agents"),
        row("c", site_id="tw_media", source="iThome", title="OpenAI launches GPT-6 model for coding agents"),
    ]
    result = build_digest_stories(snapshot(rows), WINDOW)
    assert len(result.stories) == 2
    groups = {frozenset(s["id"] for s in story["sources"]) for story in result.stories}
    assert groups == {frozenset({"a", "b"}), frozenset({"c"})}
    assert next(s for s in result.stories if s["source_count"] == 2)["primary_item"]["id"] == "a"


def test_archive_permutations_cannot_change_equal_time_story_anchor():
    rows = [row("a", site_id="curated_media", source="Media A"), row("b", site_id="tw_media", source="Media B"), row("c", site_id="opmlrss", source="Media C")]
    results = [build_digest_stories(snapshot(list(order)), WINDOW) for order in permutations(rows)]
    assert all(result == results[0] for result in results)
    assert len(results[0].stories) == 1
    assert results[0].stories[0]["story_id"] == news.story_id_for_item(rows[0])


def test_duplicate_quality_ties_use_fixed_id_order():
    rows = [row("b", url="https://example.invalid/event"), row("a", url="https://example.invalid/event")]
    result = build_digest_stories(snapshot(rows), WINDOW)
    assert result.items[0]["id"] == "a"
    assert result == build_digest_stories(snapshot(list(reversed(rows))), WINDOW)


def test_reader_source_cap_and_publisher_dedup_are_reused():
    rows = [row(str(i), site_id="kr36_ai", source="36Kr", title=f"AI 新聞 {i}", published_at=f"2026-10-01T{10+i:02d}:00:00Z") for i in range(8)]
    result = build_digest_stories(snapshot(rows), WINDOW)
    assert len(result.items) == news.KR36_AI_READER_MAX_ITEMS
    assert counts(result) == {"reader_dedup_or_limit": 3}
    publisher_rows = [row("a", site_id="kr36_ai", source="36Kr", title="即夢AI測評：大模型使用體驗 | 36氪AI測評 - 36 Kr"), row("b", site_id="kr36_ai", source="36Kr", title="即夢AI測評：大模型使用體驗 | 36氪AI測評 - m-ai.36kr.com")]
    assert len(build_digest_stories(snapshot(publisher_rows), WINDOW).items) == 1


def test_near_duplicate_suppression_keeps_distinct_vendor_events():
    rows = [row("a", title="OpenAI launches GPT-6 models for coding agents"), row("b", title="OpenAI launches GPT-6 model for coding agents"), row("c", title="Anthropic launches Claude 6 model for coding agents")]
    result = build_digest_stories(snapshot(rows), WINDOW)
    assert len(result.items) == 2
    assert len(result.stories) == 2
    assert any(item["id"] == "c" for item in result.items)


def test_clock_randomness_network_and_translator_cannot_affect_result(monkeypatch):
    data = snapshot([row("a", metadata={"nested": ["original"]})])
    baseline_records = deepcopy(data.records)
    expected = build_digest_stories(data, WINDOW)
    def forbidden(*args, **kwargs):
        raise AssertionError("clock, randomness or provider used")
    import requests
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(requests.Session, "request", forbidden)
    monkeypatch.setattr(news, "utc_now", forbidden)
    monkeypatch.setattr(news.random, "choice", forbidden)
    monkeypatch.setattr(news, "add_bilingual_fields", forbidden)
    monkeypatch.setattr(news, "summarize_stories", forbidden)
    result = build_digest_stories(data, WINDOW)
    assert result == expected
    assert result.stories == tuple(news.merge_story_items(list(result.items), now=WINDOW.end_utc, window_hours=24))
    assert data.records == baseline_records
    result.items[0]["metadata"]["nested"].append("changed")
    assert data.records == baseline_records


def test_changed_snapshot_adds_late_story_without_promising_historical_id():
    original = row("later", published_at="2026-10-01T11:00:00Z")
    discovered = row("earlier", site_id="curated_media", source="Some Media", published_at="2026-10-01T10:00:00Z", first_seen_at="2026-10-02T03:00:00Z")
    first = build_digest_stories(snapshot([original]), WINDOW)
    second = build_digest_stories(snapshot([original, discovered]), WINDOW)
    assert len(first.stories) == len(second.stories) == 1
    assert second.stories[0]["source_count"] == 2
    assert first.stories[0]["story_id"] != second.stories[0]["story_id"]


def test_loader_integration_preserves_input_and_stale_health_diagnostics(tmp_path):
    (tmp_path / "archive.json").write_text(json.dumps({"generated_at": "2026-10-02T01:00:00Z", "items": [row("inside"), row("outside", published_at="2026-10-01T22:00:00Z")]}))
    data = load_digest_input(tmp_path)
    result = build_digest_stories(data, WINDOW)
    assert {item["id"] for item in result.items} == {"inside"}
    assert any(d.code == "health_unverifiable" for d in data.diagnostics)
    assert counts(result) == {"outside_window": 1}
