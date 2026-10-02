"""D06: existing gate/diversity rules plus exact evidence mapping."""

from copy import deepcopy
from itertools import permutations

import pytest

from scripts.digest_candidates import adapt_stories
from scripts.digest_pipeline import DigestStories
from scripts.digest_selection import SelectionError, select_digest_candidates
from scripts import update_news as news


def story(story_id, *, score=0.8, source="Publisher", title=None, count=1):
    refs = [{"id": story_id + "-item", "title": title or story_id, "url": f"https://example.invalid/{story_id}", "published_at": "2026-10-01T21:00:00Z", "source": source, "summary": "Publisher states a fact."}]
    if count > 1:
        refs.append({**refs[0], "id": story_id + "-item2", "source": "Other Publisher"})
    return {"story_id": story_id, "score": score, "importance": score, "title": title or story_id, "source": source, "source_count": count, "sources": refs, "primary_item": {"id": refs[0]["id"]}, "reasons": ["official_source"]}


def run(rows, **settings):
    return select_digest_candidates(DigestStories(tuple(rows), (), ()), adapt_stories(rows), **settings)


@pytest.mark.parametrize("score,count,selected", [(0.7199, 1, False), (0.72, 1, True), (0.9, 1, True), (0.1, 2, True)])
def test_existing_brief_gate_is_reused(score, count, selected):
    row = story("one", score=score, count=count)
    result = run([row])
    assert bool(result.candidates) is selected
    assert bool(result.candidates) == news.story_passes_brief_gate(row)
    assert result.settings.brief_score_gate == 0.72


def test_quiet_empty_and_single_story_days_do_not_get_padded():
    assert run([]).candidates == ()
    row = story("low", score=0.2)
    row["business_events"] = ["pricing"]
    assert run([row]).candidates == ()  # No new business-event gate exception.
    result = run([story("one"), row])
    assert [c["story_id"] for c in result.candidates] == ["one"]
    assert result.total_candidates == 2 and result.eligible_count == 1


def test_default_twenty_cap_with_no_minimum_quota():
    rows = [story(f"topic-{i:02d}") for i in range(25)]
    result = run(rows)
    assert len(result.candidates) == 20
    assert result.settings.limit == 20
    assert run(rows, limit=0).candidates == ()
    assert len(run(rows, limit=3).candidates) == 3


def test_existing_source_penalty_reorders_without_changing_importance():
    rows = [story("a", score=0.9, source="Prolific"), story("b", score=0.89, source="Prolific"), story("c", score=0.88, source="Alternative")]
    result = run(rows, limit=3)
    assert [c["story_id"] for c in result.candidates] == ["a", "c", "b"]
    assert [c["importance"] for c in result.candidates] == [0.9, 0.88, 0.89]
    assert result.settings.same_source_penalty == 0.03
    assert [c["story_id"] for c in run(rows, same_source_penalty=0).candidates] == ["a", "b", "c"]


def test_same_event_reposts_get_one_slot_but_distinct_model_versions_survive():
    rows = [story("a", title="OpenAI launches GPT-5 model for coding agents"), story("b", title="OpenAI launches GPT-5 model for coding agents"), story("c", title="OpenAI launches GPT-6 model for coding agents")]
    result = run(rows)
    assert [c["story_id"] for c in result.candidates] == ["a", "c"]
    assert result.diagnostics[0].code == "diversity_or_limit"


def test_equal_score_title_ties_and_candidate_order_are_deterministic():
    rows = [story("b", title="Short title"), story("a", title="Short title"), story("c", title="Short title")]
    expected = run(rows)
    assert [c["story_id"] for c in expected.candidates] == ["a", "b", "c"]
    for order in permutations(rows):
        candidates = list(reversed(adapt_stories(order)))
        assert select_digest_candidates(DigestStories(tuple(order), (), ()), candidates) == expected


def test_selection_uses_original_story_scores_and_titles_not_translated_candidates():
    rows = [story("a", score=0.8), story("b", score=0.9)]
    candidates = adapt_stories(rows)
    candidates[0]["importance"] = 1.0
    candidates[0]["title"] = "AAA translated title"
    candidates[1]["importance"] = None
    result = select_digest_candidates(DigestStories(tuple(rows), (), ()), candidates)
    assert [c["story_id"] for c in result.candidates] == ["b", "a"]
    assert result.candidates[0]["importance"] is None


def test_evidence_provenance_and_missing_summary_are_preserved_without_mutation():
    rows = [story("a"), story("b", score=0.9)]
    rows[1]["sources"][0]["summary"] = None
    cache = {"a": "既有題目譯文", "summary::Publisher states a fact.": "出版者指出事實。"}
    candidates = adapt_stories(rows, title_cache=cache)
    original_rows, original_candidates = deepcopy(rows), deepcopy(candidates)
    result = select_digest_candidates(DigestStories(tuple(rows), (), ()), candidates)
    assert result.candidates[0]["summary"] is None
    assert result.candidates[1] == original_candidates[0]
    assert result.candidates[1]["summary_kind"] == "publisher_translation"
    assert result.candidates[1]["verification"] is None
    result.candidates[1]["sources"][0]["summary_translation"]["key"] = "changed"
    assert rows == original_rows and candidates == original_candidates


@pytest.mark.parametrize("settings,code", [
    ({"limit": -1}, "invalid_limit"), ({"limit": 1.0}, "invalid_limit"), ({"limit": True}, "invalid_limit"),
    ({"same_source_penalty": -0.1}, "invalid_source_penalty"), ({"same_source_penalty": float("nan")}, "invalid_source_penalty"),
    ({"same_source_penalty": float("inf")}, "invalid_source_penalty"), ({"same_source_penalty": True}, "invalid_source_penalty"),
    ({"same_source_penalty": 10**400}, "invalid_source_penalty"),
])
def test_invalid_selection_settings_fail_safely(settings, code):
    with pytest.raises(SelectionError, match="^" + code + "$"):
        run([], **settings)


@pytest.mark.parametrize("case,code", [
    ("missing_candidate", "candidate_story_mismatch"), ("extra_candidate", "candidate_story_mismatch"),
    ("duplicate_story", "duplicate_story_id"), ("duplicate_candidate", "duplicate_candidate_id"),
    ("missing_story_id", "invalid_story_id"), ("missing_candidate_id", "invalid_candidate_id"),
])
def test_mixed_or_ambiguous_inputs_do_not_silently_backfill(case, code):
    rows = [story("a")]
    candidates = adapt_stories(rows)
    if case == "missing_candidate": candidates = []
    elif case == "extra_candidate": candidates += adapt_stories([story("other")])
    elif case == "duplicate_story": rows *= 2
    elif case == "duplicate_candidate": candidates *= 2
    elif case == "missing_story_id": rows[0]["story_id"] = None
    elif case == "missing_candidate_id": candidates[0]["story_id"] = None
    with pytest.raises(SelectionError, match="^" + code + "$"):
        select_digest_candidates(DigestStories(tuple(rows), (), ()), candidates)


@pytest.mark.parametrize("score", ["bad", float("nan"), float("inf"), True])
def test_malformed_scores_fail_instead_of_creating_a_new_rank(score):
    with pytest.raises(SelectionError, match="^invalid_story_score$"):
        run([story("a", score=score)])


def test_selection_has_no_clock_provider_or_random_calls(monkeypatch):
    import requests
    def forbidden(*args, **kwargs): raise AssertionError("provider/clock/random called")
    monkeypatch.setattr(requests.Session, "request", forbidden)
    monkeypatch.setattr(news, "utc_now", forbidden)
    monkeypatch.setattr(news.random, "choice", forbidden)
    monkeypatch.setattr(news, "summarize_stories", forbidden)
    assert run([story("a")]).candidates


def test_selection_matches_existing_brief_policy_for_distinct_stories():
    rows = [story("a", score=0.9), story("b", score=0.85), story("c", score=0.3)]
    expected = news.build_daily_brief_payload(rows, "not-used", 24, max_items=2)["items"]
    assert [c["story_id"] for c in run(rows, limit=2).candidates] == [s["story_id"] for s in expected]
