"""D05: nullable legacy mapping and traceable exact-cache display fields."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.digest_candidates import CandidateError, adapt_story, adapt_stories
from scripts.digest_input import load_digest_input
from scripts.digest_pipeline import build_digest_stories
from scripts.digest_window import window_for_date


def source(item_id="a", **changes):
    row = {"id": item_id, "title": "OpenAI releases a Codex update", "url": f"https://example.invalid/{item_id}", "source": "Publisher", "site_id": "official_ai", "published_at": "2026-10-02T05:00:00+08:00", "summary": "Publisher says the update costs $10."}
    row.update(changes)
    return row


def story(**changes):
    row = {"story_id": "story-original", "title": "Story title", "primary_item": {"id": "a", "title": "Primary title"}, "sources": [source()], "importance": 0.8, "business_events": ["pricing"], "reasons": ["official_source"], "latest_at": "2026-10-02T09:00:00Z"}
    row.update(changes)
    return row


def test_single_source_candidate_keeps_identity_and_primary_evidence():
    candidate = adapt_story(story())
    assert candidate["schema_version"] == 1
    assert candidate["story_id"] == "story-original"
    assert candidate["primary_item_id"] == "a"
    assert candidate["primary_url"] == "https://example.invalid/a"
    assert candidate["primary_published_at"] == "2026-10-01T21:00:00Z"
    assert candidate["title"] == source()["title"]
    assert candidate["summary"] == source()["summary"]
    assert candidate["summary_kind"] == "publisher"
    assert candidate["summary_source_item_id"] == "a"
    assert candidate["verification"] is None
    assert candidate["importance"] == 0.8
    json.dumps(candidate, allow_nan=False)


def test_multi_source_primary_is_matched_by_id_not_list_order_or_latest_time():
    rows = [source("b", summary="Another publisher's different claim.", published_at="2026-10-01T21:59:00Z"), source("a")]
    candidate = adapt_story(story(sources=rows, source_count=999, verification={"verified": True}))
    assert candidate["source_count"] == 2
    assert candidate["summary"] == rows[1]["summary"]
    assert candidate["primary_published_at"] == "2026-10-01T21:00:00Z"
    assert candidate["sources"][0]["summary"] == rows[0]["summary"]
    assert candidate["verification"] is None


def test_exact_cache_hits_keep_original_and_unversioned_provenance():
    ref = source()
    cache = {ref["title"]: "OpenAI 發布 Codex 更新", "summary::" + ref["summary"]: "出版者稱更新費用為 $10。"}
    candidate = adapt_story(story(), title_cache=cache)
    assert candidate["title"] == cache[ref["title"]]
    assert candidate["title_original"] == ref["title"]
    assert candidate["summary_original"] == ref["summary"]
    assert candidate["summary_kind"] == "publisher_translation"
    assert candidate["summary_translation"] == {"input": "title-zh-cache.json", "key": "summary::" + ref["summary"], "alignment": "unversioned"}
    assert candidate["sources"][0]["title_translation"] == candidate["title_translation"]


@pytest.mark.parametrize("key_change", [str.lower, lambda x: x + " ", lambda x: " " + x, lambda x: x + " extra"])
def test_cache_lookup_has_no_fuzzy_or_case_or_whitespace_matching(key_change):
    ref = source()
    cache = {key_change(ref["title"]): "不應命中", "summary::" + key_change(ref["summary"]): "不應命中"}
    candidate = adapt_story(story(), title_cache=cache)
    assert candidate["title"] == ref["title"]
    assert candidate["summary_kind"] == "publisher"
    assert candidate["summary_translation"] is None


@pytest.mark.parametrize("value", ["", " ", None, {}, 0])
def test_invalid_or_empty_translation_values_fall_back(value):
    ref = source()
    candidate = adapt_story(story(), title_cache={ref["title"]: value, "summary::" + ref["summary"]: value})
    assert candidate["summary"] == ref["summary"]
    assert candidate["summary_kind"] == "publisher"


def test_missing_primary_summary_does_not_borrow_other_source_or_ai_summary():
    rows = [source("a", summary=None, summary_zh="Stale or generated summary"), source("b")]
    candidate = adapt_story(story(sources=rows, news_summary="AI claim", primary_item={"id": "a", "summary": "Wrong copied claim"}))
    assert candidate["summary"] is None
    assert candidate["summary_kind"] == "none"
    assert candidate["summary_source_item_id"] is None
    assert candidate["sources"][1]["summary"] == rows[1]["summary"]


@pytest.mark.parametrize("timestamp", [None, "bad", "2026-10-01", "2026-10-01T21:00:00"])
def test_missing_or_invalid_source_date_stays_null_even_with_latest_at(timestamp):
    candidate = adapt_story(story(sources=[source(published_at=timestamp)]))
    assert candidate["primary_published_at"] is None
    assert candidate["sources"][0]["published_at"] is None


@pytest.mark.parametrize("rows", [[source("b")], [source("a"), source("a", summary="Conflicting ID")]])
def test_unresolved_or_ambiguous_primary_does_not_invent_summary_or_date(rows):
    candidate = adapt_story(story(sources=rows))
    assert candidate["primary_item_id"] == "a"
    assert candidate["summary"] is None and candidate["primary_published_at"] is None
    assert candidate["title_origin"] == "primary_item"


def test_legacy_items_shape_and_optional_fields_are_explicitly_nullable():
    candidate = adapt_story({"story_id": "legacy", "items": [{"id": "a"}], "score": 0.6})
    assert candidate["importance"] == 0.6
    assert candidate["primary_item_id"] is None
    assert candidate["title"] is None and candidate["primary_url"] is None
    assert candidate["summary"] is None
    assert candidate["business_events"] == candidate["reasons"] == []
    assert candidate["sources"][0]["source"] is None
    assert candidate["sources"][0]["site_id"] is None
    assert candidate["verification"] is None


@pytest.mark.parametrize("importance", [None, "0.9", True, float("nan"), float("inf"), 10**400])
def test_missing_or_unusable_importance_is_nullable(importance):
    candidate = adapt_story(story(importance=importance))
    assert candidate["importance"] is None
    json.dumps(candidate, allow_nan=False)


def test_adapter_does_not_mutate_input_or_cache_and_preserves_story_order():
    stories = [story(story_id="first"), story(story_id="second", importance=0.99)]
    cache = {source()["title"]: "既有譯文"}
    original, original_cache = deepcopy(stories), deepcopy(cache)
    candidates = adapt_stories(stories, title_cache=cache)
    assert [c["story_id"] for c in candidates] == ["first", "second"]
    candidates[0]["sources"][0]["title_translation"]["key"] = "changed"
    candidates[0]["reasons"].append("changed")
    assert stories == original and cache == original_cache
    assert adapt_stories([]) == []


def test_missing_identity_is_a_safe_error():
    with pytest.raises(CandidateError, match="^missing_story_id$"):
        adapt_story({"story_id": None, "title": "not an identity"})


def test_legacy_id_strings_are_preserved_without_trimming():
    candidate = adapt_story(story(story_id=" legacy-story ", primary_item={"id": " legacy-item "}, sources=[source(" legacy-item ")]))
    assert candidate["story_id"] == " legacy-story "
    assert candidate["primary_item_id"] == candidate["sources"][0]["item_id"] == " legacy-item "
    assert candidate["summary_source_item_id"] == " legacy-item "


def test_current_pipeline_adapter_integration_uses_only_exact_cache(tmp_path):
    ref = source(site_name="Official AI")
    (tmp_path / "archive.json").write_text(json.dumps({"items": [ref]}))
    (tmp_path / "title-zh-cache.json").write_text(json.dumps({ref["title"]: "Codex 更新", "summary::" + ref["summary"]: "更新費用 $10。"}))
    data = load_digest_input(tmp_path)
    stage = build_digest_stories(data, window_for_date("2026-10-02"))
    candidate = adapt_stories(stage.stories, title_cache=data.title_cache)[0]
    assert candidate["story_id"] == stage.stories[0]["story_id"]
    assert candidate["title"] == "Codex 更新"
    assert candidate["summary"] == "更新費用 $10。"
    assert candidate["primary_published_at"] == "2026-10-01T21:00:00Z"


def test_adapter_has_no_generator_or_network_dependencies_in_both_import_modes():
    root = Path(__file__).resolve().parents[1]
    script = """
import importlib, importlib.abc, sys
class Reject(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'requests','scripts.update_news','update_news','dateutil','bs4'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, Reject())
sys.path.insert(0, sys.argv[1])
adapter = importlib.import_module(sys.argv[2])
assert adapter.adapt_story({'story_id':'legacy'})['verification'] is None
"""
    for path, module in [(root, "scripts.digest_candidates"), (root / "scripts", "digest_candidates")]:
        result = subprocess.run([sys.executable, "-B", "-c", script, str(path), module], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stdout + result.stderr
