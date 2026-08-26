from datetime import datetime, timezone

from scripts.evaluate_source_overlap import (
    classify_overlap,
    evaluate_source_overlap,
    make_recommendation,
    normalize_title_for_overlap,
    title_similarity,
)


UTC = timezone.utc


def record(site_id, title, url, published_at="2026-05-11T00:00:00Z", source="Example"):
    return {
        "site_id": site_id,
        "site_name": site_id.title(),
        "source": source,
        "title": title,
        "url": url,
        "published_at": published_at,
        "first_seen_at": published_at,
    }


def test_normalize_title_for_overlap_removes_noise_words_and_punctuation():
    assert normalize_title_for_overlap("[Exclusive] Gemini 2.5 Pro: launch! 2026") == "gemini 2 5 pro launch"


def test_title_similarity_handles_reordered_tokens():
    assert title_similarity("OpenAI ships new Codex feature", "New Codex feature ships from OpenAI") >= 0.88


def test_classify_overlap_matches_exact_url_after_normalization():
    candidate = record("candidate", "Different title", "https://openai.com/news/codex?utm_source=x#section")
    existing = record("official_ai", "OpenAI Codex update", "https://openai.com/news/codex")
    match = classify_overlap(candidate, existing)
    assert match is not None
    assert match["match_type"] == "url_exact"
    assert match["matched_site_id"] == "official_ai"


def test_evaluate_source_overlap_counts_duplicates_and_uniques():
    candidate_items = [
        record("candidate", "OpenAI ships a new Codex feature", "https://candidate.example/a"),
        record("candidate", "Anthropic releases Claude workflow", "https://candidate.example/b"),
        record("candidate", "Unique robotics benchmark", "https://candidate.example/c"),
    ]
    baseline_items = [
        record("official_ai", "OpenAI ships new Codex feature", "https://openai.com/news/codex"),
        record("curated_media", "Anthropic releases Claude workflow", "https://media.example/claude"),
        record("opmlrss", "Unrelated AI post", "https://community.example/u"),
    ]
    report = evaluate_source_overlap(
        candidate_items,
        baseline_items,
        candidate={"site_id": "candidate", "site_name": "Candidate", "url": "https://candidate.example/feed.xml"},
        generated_at=datetime(2026, 5, 11, tzinfo=UTC),
        lookback_days=7,
    )
    assert report["overlap"]["duplicate_count"] == 2
    assert report["overlap"]["unique_count"] == 1
    assert report["recommendation"]["decision"] == "watchlist"


def test_make_recommendation_thresholds_and_sample_guard():
    assert make_recommendation(item_count=3, duplicate_rate=1.0)["decision"] == "watchlist"
    assert make_recommendation(item_count=10, duplicate_rate=0.7)["decision"] == "skip_duplicate"
    assert make_recommendation(item_count=10, duplicate_rate=0.5)["decision"] == "watchlist"
    assert make_recommendation(item_count=10, duplicate_rate=0.2)["decision"] == "accept_default"
