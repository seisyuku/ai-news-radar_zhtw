"""Daily V2 eligibility, cheap ranking, captured reads and legacy preservation."""

from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from scripts.digest_candidates import adapt_stories
from scripts.digest_pipeline import DigestStories
from scripts.digest_news_policy import select_news_candidates, classify
from scripts.digest_document import build_digest_document
from scripts.digest_input import load_digest_input
from scripts.digest_window import window_for_date
from scripts.digest_render import render_digest
from scripts.digest_drive_delivery import native_content
from scripts import generate_digest_job as job
from scripts.generate_digest import verify_digest_pair, write_digest
from tests.test_digest_selection import story
from tests.test_digest_integration import inputs, pair


def run(rows, **settings):
    return select_news_candidates(DigestStories(tuple(rows), (), ()), adapt_stories(rows), **settings)


def test_single_source_below_old_gate_is_selected_and_has_no_fake_verification():
    row = story("a", title="Acme releases a new AI model", score=.4)
    selected = run([row])
    assert len(selected.candidates) == 1
    assert selected.settings.policy == "daily-news-v2" and selected.settings.brief_score_gate is None
    assert selected.candidates[0]["editorial_selection"]["level"] == "Full"
    assert selected.candidates[0]["verification"] is None


@pytest.mark.parametrize("title", ["Save on TechCrunch tickets", "Grok predicts meme coin to hit $2",
                                  "Five prompt tips for coding", "AI 早報 2026-10-11",
                                  "CEO says we should assume all AI models are compromised"])
def test_high_old_score_or_multiple_sources_do_not_admit_noise(title):
    assert not run([story("noise", title=title, score=.99, count=2)]).candidates


def test_relative_top_ten_no_minimum_and_stable_permutations():
    rows = [story(f"s{i}", title=f"OpenAI releases GPT-{i+1} model for coding agents", score=.3) for i in range(13)]
    before = deepcopy(rows)
    selected = run(rows, limit=50)
    assert len(selected.candidates) == selected.settings.limit == 10
    assert run(list(reversed(rows)), limit=50) == selected
    assert rows == before
    assert run(rows[:2]).eligible_count == len(run(rows[:2]).candidates) == 2
    assert run([], limit=10).candidates == ()


def test_practical_cost_news_competes_with_industry_news():
    practical = story("practical", title="Local AI costs 5x less in hardware tests", score=.65)
    industry = story("industry", title="Acme releases an AI model", score=.9)
    assert run([industry, practical], limit=1).candidates[0]["story_id"] == "practical"


def test_source_diversity_preserves_importance_and_distinct_model_versions():
    rows = [story("a", title="OpenAI releases GPT-1 model for coding agents", score=.7, source="A"),
            story("b", title="OpenAI releases GPT-2 model for coding agents", score=.69, source="A"),
            story("c", title="OpenAI releases GPT-3 model for coding agents", score=.68, source="B")]
    assert [c["story_id"] for c in run(rows).candidates] == ["a", "c", "b"]
    assert [c["importance"] for c in run(rows).candidates] == [.7, .68, .69]


def test_announcement_is_concrete_but_political_rebrand_is_not_a_release():
    assert classify({"title_original": "OpenAI announces a new agent"}).eligible
    assert not classify({"title_original": "Silicon Valley is falling in line with Trump's attempt to rename AI",
                         "summary_original": "Trump announced his plans to rebrand artificial intelligence as super intelligence."}).eligible


def test_default_document_and_native_output_are_compact_and_title_only_is_allowed(tmp_path):
    source = inputs(tmp_path / "in", pair(summary=None))
    document = build_digest_document(load_digest_input(source), window_for_date("2026-10-02"))
    assert document["pipeline_version"] == "daily-digest-v2"
    assert len(document["candidates"]) == 1
    assert "review_candidates" not in document
    markdown = render_digest(document)
    _, text, styles = native_content(document, False)
    for output in (markdown, text):
        assert "共 1 則" in output and "來源：" in output
        assert "沒有可用的出版者摘要" not in output
        assert "待人工挑選" not in output
    assert any("updateTextStyle" in s for s in styles)


def test_job_captures_selected_article_once_and_rebuilds_without_network(tmp_path):
    url = "https://technews.tw/2026/10/01/ai-lab/"
    rows = pair(summary="公司推出 AI 自動實驗室 […]", title="公司推出 AI 自動實驗室")[:1]
    rows[0].update(url=url, source="TechNews 科技新報", site_id="tw_media")
    source = inputs(tmp_path / "in", rows)
    calls = []
    paragraph = "公司推出 AI 自動實驗室，改善抗體開發流程，預計明年初擴大運作。"
    def fetch(value):
        calls.append(value)
        return paragraph
    now = datetime(2026, 10, 1, 23, 0, tzinfo=timezone.utc)
    result = job.generate("2026-10-02", source, tmp_path / "out", clock=lambda: now, excerpt_fetcher=fetch)
    assert result["pair_verified"] and result["rerun_identical"] and calls == [url]
    meta = verify_digest_pair(tmp_path / "out/pair/digest-2026-10-02.md", tmp_path / "out/pair/digest-2026-10-02.meta.json")
    assert meta["candidates"][0]["summary"] == paragraph
    assert meta["candidates"][0]["sources"][0]["summary_original"].endswith("[…]")
    assert meta["article_excerpts"]["entries"][url]["text"] == paragraph
    assert meta["selection_counts"]["selected_count"] == 1


def test_failed_article_read_does_not_cancel_other_news(tmp_path):
    rows = pair(summary="公司發布新模型 […]")[:1]
    rows[0].update(url="https://technews.tw/2026/10/01/model/", source="TechNews 科技新報", site_id="tw_media")
    source = inputs(tmp_path / "in", rows)
    def fail(url): raise TimeoutError("private error")
    result = job.generate("2026-10-02", source, tmp_path / "out", clock=lambda: datetime(2026,10,1,23,tzinfo=timezone.utc), excerpt_fetcher=fail)
    assert result["status"] == "generated" and result["selected_count"] == 1
    meta = verify_digest_pair(tmp_path / "out/pair/digest-2026-10-02.md", tmp_path / "out/pair/digest-2026-10-02.meta.json")
    assert meta["candidates"][0]["summary"] is None
    assert "private error" not in json.dumps(meta)


def test_legacy_saved_delivery_survives_new_policy_without_regeneration(tmp_path):
    from scripts import digest_daily_job as daily
    from tests.test_digest_daily_job import enabled, source, PRIMARY, BACKUP, DATE, TARGET, event
    client = enabled()
    input_dir = source(tmp_path)
    def legacy_generator(date, input_dir, output_dir, **kwargs):
        document = build_digest_document(load_digest_input(input_dir), window_for_date(date), policy="existing_daily_brief")
        write_digest(document, output_dir / "pair")
        return {"status":"generated", "pair_verified":True, "rerun_identical":True, "selected_count":len(document["candidates"])}
    first = daily.run_daily(daily.trigger_plan(event(), PRIMARY), client, TARGET, input_dir,
                            tmp_path / "out", clock=lambda:PRIMARY, generator=legacy_generator)
    assert first["delivery_verified"]
    from scripts import digest_drive_delivery as drive
    folder = drive.issue_location(client, "root", DATE, "current")[2]
    receipt = json.loads(client.download(client.find(folder["id"], "delivery.json")["id"]))
    client.docs[receipt["file_ids"]["review"]] = "人工校稿必須保留"
    writes = deepcopy(client.writes)
    def forbidden(*a, **k): pytest.fail("saved issue was regenerated")
    second = daily.run_daily(daily.trigger_plan(event(BACKUP), BACKUP), client, TARGET, tmp_path / "missing",
                             tmp_path / "other", clock=lambda:BACKUP, generator=forbidden)
    assert second["reason"] == "already_delivered" and client.writes == writes
    assert client.docs[receipt["file_ids"]["review"]] == "人工校稿必須保留"
