import copy
import json
import sys
from datetime import datetime, timezone

import pytest

from scripts import reader_excerpts as r, update_news as u, brief_events as b
from scripts.news_summaries import summarize_stories, story_source_context, build_story_summary_prompt, summary_cache_key, DEFAULT_GROQ_MODEL


LEAD = "Today we release a benchmark to evaluate whether language models can assess the novelty of scientific research ideas."
URL = "https://huggingface.co/blog/allenai/novelty-bench"
FINANCE_URL = "https://huggingface.co/blog/nvidia/nemotron-personas-finance-japan"
FINANCE_TITLE = "Nemotron-Personas-Finance-Japan: A Synthetic Dataset Capturing Japan's Demographics and Financial Context"
FINANCE_JA_TITLE = "Nemotron-Personas-Finance-Japan: 日本の人口分布と金融コンテキストを捉える合成ペルソナデータセット"
FINANCE_ZH_TITLE = "Nemotron-Personas-Finance-Japan：捕捉日本人口統計與金融背景的合成資料集"


def test_hugging_face_language_editions_merge_only_with_matching_english_article():
    english = {"url": FINANCE_URL, "title": FINANCE_TITLE}
    japanese = {"url": FINANCE_URL + "-ja", "title": FINANCE_JA_TITLE}
    separate = {"url": FINANCE_URL + "-follow-up-ja", "title": FINANCE_JA_TITLE}
    lookalike = {**japanese, "url": japanese["url"].replace("huggingface.co", "example.org")}
    english_ja_slug = {**japanese, "title": "A different English article"}
    assert u.dedupe_same_publisher_items([japanese, english]) == [english]
    assert u.dedupe_same_publisher_items([japanese]) == [japanese]
    assert u.dedupe_same_publisher_items([english, english_ja_slug]) == [english_ja_slug, english]
    assert len(u.dedupe_same_publisher_items([english, separate, lookalike])) == 3


@pytest.mark.parametrize("provider_result", ["translated", "missing", "still_japanese"])
def test_japanese_reader_copy_is_never_labeled_as_chinese_without_translation(monkeypatch, provider_result):
    title = "日本向けの合成データセットを公開"
    lead = "金融業界での研究に向けて合成データを公開します。"
    row = {"url": FINANCE_URL + "-ja", "title": title, "summary": "", "reader_summary": lead}
    expected = {title: "公開面向日本的合成資料集", lead: "為金融產業研究公開合成資料。"}

    def translate(_session, texts, _key, _timeout, **_kwargs):
        assert texts[0] in expected
        if provider_result == "still_japanese":
            return [text + "です" for text in texts]
        assert provider_result == "translated"
        return [expected[text] for text in texts]

    monkeypatch.setattr(u, "_translate_gemini_batch", translate)
    ai, all_rows, cache = u.add_bilingual_fields([row], [row], None, {}, 10,
        gemini_api_key="" if provider_result == "missing" else "test")
    assert ai == all_rows
    assert ai[0]["title_original"] == title and ai[0]["title_en"] is None
    assert ai[0]["reader_summary"] == lead and ai[0]["summary"] == ""
    if provider_result == "translated":
        assert ai[0]["title_zh"] == expected[title]
        assert ai[0]["summary_zh"] == expected[lead]
        assert cache == {title: expected[title], f"summary::{lead}": expected[lead]}
    else:
        assert ai[0]["title_zh"] is None and "summary_zh" not in ai[0]
        assert not cache


def test_offline_generation_merges_hugging_face_editions_but_keeps_archive_and_raw_view(tmp_path, monkeypatch):
    output = tmp_path / "data"
    output.mkdir()
    now = datetime(2026, 11, 10, 2, 16, tzinfo=timezone.utc)
    rows = [
        {"id": item_id * 40, "site_id": "official_ai", "site_name": "Official AI",
         "source": "Hugging Face Blog", "url": url, "title": title, "summary": "",
         "published_at": published, "first_seen_at": u.iso(now), "last_seen_at": u.iso(now)}
        for item_id, url, title, published in [
            ("a", FINANCE_URL, FINANCE_TITLE, "2026-11-09T15:05:57Z"),
            ("b", FINANCE_URL + "-ja", FINANCE_JA_TITLE, "2026-11-09T15:04:52Z"),
        ]
    ]
    (output / "archive.json").write_text(json.dumps({"generated_at": u.iso(now), "items": rows}))
    (output / "title-zh-cache.json").write_text(json.dumps({FINANCE_TITLE: FINANCE_ZH_TITLE}))
    (output / "reader-excerpt-cache.json").write_text(json.dumps({FINANCE_URL: LEAD}))
    monkeypatch.setattr(u, "utc_now", lambda: now)
    monkeypatch.setattr(u, "create_session", lambda: object())
    monkeypatch.setattr(u, "collect_all", lambda *_: ([], []))
    monkeypatch.setattr(u, "run_market_sensors", lambda *_: ({"generated_at": u.iso(now), "signals": []}, {}, []))
    monkeypatch.setattr(r, "fetch_lead", lambda *_: pytest.fail("unexpected excerpt fetch"))
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(output), "--translate-max-new", "0"])

    assert u.main() == 0
    latest = json.loads((output / "latest-24h.json").read_text())
    all_rows = json.loads((output / "latest-24h-all.json").read_text())
    stories = json.loads((output / "stories-merged.json").read_text())["stories"]
    archive = json.loads((output / "archive.json").read_text())["items"]
    for merged in (latest["items"], latest["items_ai"], all_rows["items_all"],
                   [story["primary_item"] for story in stories]):
        assert [(row["url"], row["title_zh"]) for row in merged] == [(FINANCE_URL, FINANCE_ZH_TITLE)]
    assert {row["title"] for row in archive} == {FINANCE_TITLE, FINANCE_JA_TITLE}
    raw_japanese = next(row for row in all_rows["items_all_raw"] if row["url"].endswith("-ja"))
    assert raw_japanese["title_original"] == FINANCE_JA_TITLE and raw_japanese["title_zh"] is None


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
    assert status["failed"] == 2 and status["last_error_detail"] == "validation_numeric_grounding"
