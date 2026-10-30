import copy
from datetime import datetime, timezone

import pytest

from scripts import reader_excerpts as r, update_news as u, brief_events as b
from scripts.news_summaries import summarize_stories, story_source_context, build_story_summary_prompt, summary_cache_key, DEFAULT_GROQ_MODEL


LEAD = "Today we release a benchmark to evaluate whether language models can assess the novelty of scientific research ideas."
URL = "https://huggingface.co/blog/allenai/novelty-bench"


def test_excerpt_extracts_only_first_substantive_paragraph():
    page = f'<nav><p>{LEAD}</p></nav><div class="blog-content"><script>bad</script><p>Paper | Code</p><p>{LEAD}</p><p>Later body.</p></div>'
    assert r.lead_paragraph(page) == LEAD
    with pytest.raises(ValueError):
        r.lead_paragraph(f'<main><p>{LEAD}</p></main>')


@pytest.mark.parametrize("url", ["http://huggingface.co/blog/a", "https://huggingface.co.evil.test/blog/a", "https://huggingface.co@evil.test/blog/a", "https://huggingface.co/blog/a?target=x", "https://huggingface.co/api/a"])
def test_excerpt_fetch_rejects_non_article_urls(url):
    assert r.article_url(url) is None


def test_display_excerpt_is_cached_shared_and_does_not_change_native_summary():
    rows = [{"id": "a", "url": URL, "title": "Research benchmark", "summary": "", "ai_score": .99}]
    before = copy.deepcopy(rows)
    calls = []
    ai, all_rows, cache, status = r.enrich(rows, rows, None, {}, fetcher=lambda url: calls.append(url) or LEAD)
    assert rows == before and calls == [URL]
    assert ai == all_rows
    assert ai[0]["summary"] == "" and ai[0]["reader_summary"] == LEAD
    assert story_source_context({"sources": ai}) == ""
    ai2, _, _, status2 = r.enrich(rows, rows, None, cache, fetcher=lambda url: pytest.fail("cached"))
    assert ai2 == ai and status2["cache_hits"] == 1
    translated, _, _ = u.add_bilingual_fields(ai, all_rows, None,
        {"summary::" + LEAD: "今天我們發布基準測試，評估語言模型是否能判斷科學研究構想的新穎性。", "Research benchmark": "研究基準"}, 0, gemini_api_key="")
    assert translated[0]["summary_zh"].startswith("今天")
    assert translated[0]["summary"] == ""


def test_excerpt_failure_and_per_run_cap_keep_original_rows():
    rows = [{"url": f"https://huggingface.co/blog/test-{i}"} for i in range(10)]
    calls = []
    def fail(url):
        calls.append(url)
        raise ValueError("unavailable")
    ai, _, _, status = r.enrich(rows, rows, None, {}, fetcher=fail)
    assert ai == rows and len(calls) == 6 and status["failed"] == 6


def test_visible_primary_precedes_higher_scoring_ordinary_stories_without_reordering():
    stories = [{"story_id": str(i), "score": 1-i/100, "title": "模型更新", "primary_item": {"id": str(i)},
                "sources": [{"source": "Official", "summary": "模型新功能已向所有開發者開放，官方公告說明新版本的使用方式與適用範圍。"}]} for i in range(30)]
    calls = []
    result, status, _ = summarize_stories(stories, candidate_limit=20, max_new=1,
        priority_article_ids=["29"], generate_fn=lambda prompt, s: calls.append(s["story_id"]) or "模型新功能已向所有開發者開放，官方公告說明新版本的使用方式與適用範圍。")
    assert calls == ["29"] and status["generated"] == 1
    assert [s["story_id"] for s in result] == [s["story_id"] for s in stories]


def test_event_projection_keeps_native_and_translated_primary_summary():
    now = datetime(2026, 10, 28, 9, tzinfo=timezone.utc)
    row = {"id":"a", "title":"OpenAI releases GPT-6.1 Sol", "url":"https://openai.com/index/synthetic",
           "source":"OpenAI News", "site_id":"official_ai", "summary":"GPT-6.1 Sol adds tool calling and supports enterprise customers using longer context windows.",
           "summary_zh":"GPT-6.1 Sol 現已開放開發者使用。", "published_at":"2026-10-28T08:00:00Z", "first_seen_at":"2026-10-28T08:00:00Z"}
    stories = u.merge_story_items([u.add_source_tier_fields(u.add_ai_relevance_fields(row))], now, 24)
    result = u.build_brief_event_payloads(stories, [row], b.StateInput("missing"), now, 24, archive_meta=b.ArchiveMeta("valid", u.iso(now)))
    assert result.publisher_governance["status"] == "ready"
    primary = result.daily_items[0]["primary_item"]
    assert primary["summary"] == row["summary"] and primary["summary_zh"] == row["summary_zh"]


@pytest.mark.parametrize("source,translation,expected", [
    ("Company raises $100 million", "公司獲得 1,000 萬美元", "公司獲得 1 億美元"),
    ("Company raises $1.5 billion", "公司獲得 1.5 億美元", "公司獲得 15 億美元"),
    ("Company raises $12 million", "公司獲得 120 萬美元", "公司獲得 1200 萬美元"),
    ("Company raises $100 million and $10 million", "公司獲得 1,000 萬美元", "公司獲得 1,000 萬美元"),
    ("Company raises A$100 million", "公司獲得 1,000 萬美元", "公司獲得 1,000 萬美元"),
    ("Company raises $100 million CAD", "公司獲得 1,000 萬美元", "公司獲得 1,000 萬美元"),
])
def test_cached_title_usd_scale_repair_is_unambiguous_and_idempotent(source, translation, expected):
    assert u.repair_zh_title_translation(source, translation) == expected
    assert u.repair_zh_title_translation(source, expected) == expected


def test_summary_uses_original_title_and_does_not_reuse_display_based_cache():
    wrong = "公司融資 1,000 萬美元 / Company raises $100 million"
    original = "Company raises $100 million"
    story = {"title": wrong, "primary_item": {"title_original": original},
             "sources": [{"summary": "The company uses inference chips outside Nvidia's ecosystem."}]}
    context = story_source_context(story)
    assert wrong not in build_story_summary_prompt(story, context)
    assert original in build_story_summary_prompt(story, context)
    assert summary_cache_key(story, context, DEFAULT_GROQ_MODEL) != summary_cache_key({"title":wrong}, context, DEFAULT_GROQ_MODEL)
    _, status, _ = summarize_stories([story], max_new=1, generate_fn=lambda p,s:
        "該公司融資1,000萬美元，並採用不同於輝達生態系統的推論晶片，公告未揭露其他資訊。")
    assert status["failed"] == 1 and status["last_error_detail"] == "validation_numeric_grounding"
