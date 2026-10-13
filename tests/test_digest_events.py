"""Citation identity, independent evidence and distinct-angle retention."""

from copy import deepcopy
import json

import pytest

from scripts.digest_candidates import adapt_stories
from scripts.digest_document import build_digest_document
from scripts.digest_events import group_cited_reports, url_key
from scripts.digest_input import load_digest_input
from scripts.digest_news_policy import near_duplicate, select_news_candidates
from scripts.digest_pipeline import DigestStories, build_digest_stories
from scripts.digest_window import window_for_date
from scripts.generate_digest import main, verify_digest_pair
from tests.test_digest_pipeline import row, snapshot, WINDOW
from tests.test_digest_selection import story
from tests.test_digest_integration import inputs


def confirmation(a, b):
    return {"citing_url": f"https://example.invalid/{a}", "cited_url": f"https://example.invalid/{b}",
            "basis": "user-confirmed-same-news"}


def run(rows, **kwargs):
    return select_news_candidates(DigestStories(tuple(rows), (), ()), adapt_stories(rows), **kwargs)


def source_pair():
    original = story("original", title="Acme Flash used exposed API keys in tests", score=.4, source="Original News")
    derivative = story("derivative", title="Acme Flash reportedly spent other people's API keys", score=.9, source="Other News")
    derivative["sources"][0]["summary"] = "Acme Flash used exposed API keys, reported at https://example.invalid/original."
    return original, derivative


def test_citation_keeps_higher_existing_rank_and_retains_source_evidence():
    original, derivative = source_pair()
    before = deepcopy([original, derivative])
    result = run([derivative, original], limit=1)
    assert [c["story_id"] for c in result.candidates] == ["derivative"]
    picked = result.candidates[0]
    assert picked["source_count"] == 1 and picked["importance"] == .9
    assert picked["verification"] is None
    assert picked["event_group"]["related_reports"][0]["sources"][0]["source"] == "Original News"
    assert [original, derivative] == before
    assert result.eligible_count == 1 and result.total_candidates == 2
    assert result.event_analysis["cited_duplicates"] == 1
    assert run([original, derivative], limit=1) == result


def test_plain_publisher_name_or_similar_event_does_not_invent_citation():
    original, derivative = source_pair()
    derivative["sources"][0]["summary"] = "According to Original News, Acme Flash used API keys."
    assert run([original, derivative]).event_analysis["cited_duplicates"] == 0


def test_confirmed_same_news_replays_missing_citation_without_a_permanent_rule():
    original, derivative = source_pair()
    derivative["sources"][0]["summary"] = derivative["title"]
    result = run([original, derivative], event_citations=[confirmation("derivative", "original")])
    assert [c["story_id"] for c in result.candidates] == ["original"]
    assert result.event_analysis["applied_confirmations"] == 1
    assert run([original, derivative]).event_analysis["cited_duplicates"] == 0


@pytest.mark.parametrize("left,right", [
    ("NVIDIA reviews Reflection AI acquisition", "NVIDIA reviews Reflection AI acquisition or increased investment"),
    ("AI software developer job postings rise", "AI tech job openings rise"),
    ("OpenAI releases GPT-6 model for agents", "OpenAI cuts prices for GPT-6 model for agents"),
    ("DeepSeek releases DeepSeek V4.1 Flash", "DeepSeek releases DeepSeek V4.2 Flash"),
])
def test_shared_event_link_cannot_remove_different_angle_or_version(left, right):
    a, b = story("a", title=left), story("b", title=right)
    b["sources"][0]["summary"] = "Report references https://example.invalid/a"
    assert not near_duplicate(a, b)
    assert run([a, b], event_citations=[confirmation("b", "a")]).event_analysis["cited_duplicates"] == 0


def test_different_angle_is_protected_before_publisher_and_story_merging():
    title = "OpenAI releases GPT-6 enterprise agent for cloud teams with new features"
    other = title + " and cuts prices"
    records = [row("a", title=title), row("b", title=other)]
    assert len(build_digest_stories(snapshot(records), WINDOW).stories) == 1
    protected = build_digest_stories(snapshot(records), WINDOW, protect_event_aspects=True)
    assert len(protected.stories) == 2
    assert len(protected.items) == 2


def test_confirmation_cannot_pull_outside_window_source_into_digest(tmp_path):
    inside = row("inside", url="https://example.invalid/inside")
    outside = row("outside", url="https://example.invalid/outside", published_at="2026-09-01T00:00:00Z")
    document = build_digest_document(load_digest_input(inputs(tmp_path / "in", [inside, outside])), WINDOW,
                                     event_citations=[confirmation("inside", "outside")])
    assert len(document["candidates"]) == 1
    assert document["event_analysis"]["applied_confirmations"] == 0
    assert "event_group" not in document["candidates"][0]


def test_no_transitive_merge_and_deterministic_cycle_representative():
    rows = adapt_stories([story(sid, title="Acme releases an AI model") for sid in ("a", "b", "c")])
    grouped = group_cited_reports(rows, rank_key=lambda sid:sid,
                                 confirmations=[confirmation("a", "b"), confirmation("b", "c")])
    assert grouped.removed_count == 1 and len(grouped.representatives) == 2
    cycle = group_cited_reports(rows[:2], rank_key=lambda sid:sid,
                               confirmations=[confirmation("a", "b"), confirmation("b", "a")])
    assert cycle.representatives == ("a",)


def test_link_to_a_different_company_is_background_not_duplicate():
    a=story("a", title="Acme releases a new AI model for cloud teams")
    b=story("b", title="OtherCorp releases a new AI model for cloud teams")
    b["sources"][0]["summary"]="Background: https://example.invalid/a"
    assert run([a,b]).event_analysis["cited_duplicates"] == 0


def test_new_test_referencing_previous_test_is_kept_as_progress():
    original, derivative = source_pair()
    derivative["title"] = "Acme Flash separate tests report exposed API keys"
    derivative["sources"][0]["title"] = derivative["title"]
    assert run([original, derivative]).event_analysis["cited_duplicates"] == 0


def test_actual_citation_survives_pipeline_and_groups_without_counting_derivative(tmp_path):
    records=[row("a", title="OpenAI GPT-6 Flash used exposed API keys", url="https://example.invalid/a", source="Original"),
             row("b", title="OpenAI GPT-6 Flash reportedly spent API keys", url="https://example.invalid/b", source="Derivative",
                 summary="Source report: https://example.invalid/a")]
    document=build_digest_document(load_digest_input(inputs(tmp_path / "in",records)),WINDOW)
    assert document["event_analysis"]["cited_duplicates"] == 1
    assert len(document["candidates"]) == 1
    candidate=document["candidates"][0]
    assert candidate["primary_url"] == "https://example.invalid/a"
    assert candidate["source_count"] == 1
    assert candidate["event_group"]["related_reports"][0]["primary_url"] == "https://example.invalid/b"


def test_cross_language_citation_with_exact_model_keeps_higher_rank():
    a=story("a",title="OpenAI releases GPT-6 model for coding agents")
    b=story("b",title="OpenAI 發布 GPT-6 模型")
    b["sources"][0]["summary"]="引用原文：https://example.invalid/a"
    selected=run([a,b])
    assert selected.event_analysis["cited_duplicates"] == 1
    assert selected.candidates[0]["story_id"] == "a"


def test_structured_feed_link_groups_even_when_anchor_text_has_no_url(tmp_path):
    records=[row("a",title="OpenAI GPT-6 Flash used exposed API keys",url="https://example.invalid/a",source="Original"),
             row("b",title="OpenAI GPT-6 Flash reportedly spent API keys",url="https://example.invalid/b",source="Derivative",
                 summary="According to Original News, OpenAI GPT-6 Flash used API keys.",
                 publisher_links=["https://example.invalid/a"])]
    document=build_digest_document(load_digest_input(inputs(tmp_path / "in",records)),WINDOW)
    assert document["event_analysis"]["cited_duplicates"] == 1
    assert document["candidates"][0]["source_count"] == 1


def test_new_progress_also_survives_earlier_title_suppression():
    a=story("a",title="OpenAI GPT-6 Flash used exposed API keys in coding agent tests")
    b=story("b",title=a["title"]+" in separate tests")
    assert not near_duplicate(a,b)


def test_roundup_confirmation_is_not_a_single_event_merge():
    rows=adapt_stories([story("a",title="AI 早報"),story("b",title="Acme releases AI model")])
    result=group_cited_reports(rows,rank_key=lambda sid:sid,confirmations=[confirmation("b","a")])
    assert result.removed_count == 0


def test_url_key_keeps_article_queries_and_drops_tracking_only():
    assert url_key("https://example.invalid/news?article=2&utm_source=rss#x") == "https://example.invalid/news?article=2"
    assert url_key("https://example.invalid/news?article=2") != url_key("https://example.invalid/news?article=3")


def test_event_cli_metadata_can_rebuild_without_network(tmp_path, monkeypatch):
    import requests
    monkeypatch.setattr(requests.Session, "request", lambda *a, **k:pytest.fail("network called"))
    records=[row("a",title="OpenAI GPT-6 Flash used exposed API keys",url="https://example.invalid/a"),
             row("b",title="OpenAI GPT-6 Flash reportedly spent API keys",url="https://example.invalid/b")]
    source=inputs(tmp_path / "in",records)
    confirmed=tmp_path / "confirmed.json"
    confirmed.write_text(json.dumps([confirmation("b","a")]))
    for folder in ("first","repeat"):
        assert main(["--date","2026-10-02","--input-dir",str(source),"--output-dir",str(tmp_path/folder),
                     "--event-citations",str(confirmed)]) == 0
    md=tmp_path / "first/digest-2026-10-02.md"
    document=verify_digest_pair(md,md.with_suffix(".meta.json"))
    assert document["event_citations"] == [confirmation("b","a")]
    assert document["event_analysis"]["policy"] == "current-event-v2"
    assert document["event_analysis"]["cited_duplicates"] == 1
    assert (tmp_path / "first/digest-2026-10-02.meta.json").read_bytes() == (tmp_path / "repeat/digest-2026-10-02.meta.json").read_bytes()


def test_legacy_selection_does_not_accept_new_event_inputs(tmp_path):
    source=inputs(tmp_path / "in",[row("a")])
    with pytest.raises(ValueError,match="legacy_digest_has_no_event_citations"):
        build_digest_document(load_digest_input(source),WINDOW,policy="existing_daily_brief",event_citations=[])


def launch_pair():
    a=story("high",title='星河悄悄上線AI助手「小河」，招聘月薪最高8萬',score=.65,source="Example Media")
    b=story("low",title='星河上線自研AI助手「AI小河」，導購進入新階段',score=.60,source="Example Media")
    a["sources"][0]["summary"]=("星河近期低調上線自研AI助手「AI小河」，由內部大模型團隊打造，支持文字與語音對話，"
        "可幫用戶找商品、查活動、問優惠。其AI佈局還體現在招聘上：正以月薪5萬至8萬、年薪60萬至96萬，"
        "高薪招募大模型後訓練、數據合版、SFT文本數據等核心崗位，加碼人才儲備。")
    b["sources"][0]["summary"]=("星河近期上線自研AI助手「AI小河」，由大模型團隊開發，支持文字與語音交互，"
        "可提供商品搜索、活動查詢、優惠諮詢等服務，將大模型能力引入電商導購場景。同時，"
        "星河加大大模型人才招聘力度，正招募大模型後訓練負責人、LLM數據合版負責人、"
        "大模型SFT文本數據負責人等核心崗位，月薪5萬元起。")
    return a,b


def test_paraphrased_same_publisher_product_keeps_higher_rank_and_fills_slot():
    a,b=launch_pair()
    other=story("other",title="OpenAI releases GPT-7 agent model",score=.5)
    before=deepcopy([a,b,other])
    result=run([b,other,a],limit=2)
    assert [c["story_id"] for c in result.candidates] == ["high","other"]
    assert result.event_analysis["content_duplicates"] == 1
    assert result.event_analysis["cited_duplicates"] == 0
    group=result.candidates[0]["event_group"]
    assert group["citations"] == []
    assert group["content_duplicates"][0]["basis"] == "same-publisher-content"
    assert group["related_reports"][0]["story_id"] == "low"
    assert result.candidates[0]["source_count"] == 1
    assert [a,b,other] == before and run([a,b,other],limit=2)==result


@pytest.mark.parametrize("change",["publisher","product","missing_summary","different_aspect","new_progress","version"])
def test_content_overlap_does_not_swallow_distinct_report(change):
    a,b=launch_pair()
    if change=="publisher": b["sources"][0]["source"]="Different Media"
    elif change=="product":
        b["title"]=b["title"].replace("小河","小海")
        b["sources"][0]["title"]=b["title"]
        b["sources"][0]["summary"]=b["sources"][0]["summary"].replace("小河","小海")
    elif change=="missing_summary":b["sources"][0]["summary"]=None
    elif change=="different_aspect":b["sources"][0]["title"]+="，並降價"
    elif change=="new_progress":b["sources"][0]["title"]+="的後續報導"
    else:
        a["sources"][0]["title"]+=" DeepSeek V4.1 Flash"
        b["sources"][0]["title"]+=" DeepSeek V4.2 Flash"
    assert run([a,b]).event_analysis["content_duplicates"]==0


def test_equal_rank_content_duplicate_has_deterministic_tie_breaker():
    a,b=launch_pair();b["score"]=b["importance"]=a["score"]
    assert run([a,b])==run([b,a])
    assert run([a,b]).candidates[0]["story_id"]=="high"


def test_same_priority_citation_retains_higher_score_instead_of_forcing_original():
    original,derivative=source_pair()
    derivative["title"]="Acme Flash used exposed API keys, reports another outlet"
    derivative["sources"][0]["title"]=derivative["title"]
    selected=run([original,derivative])
    assert selected.candidates[0]["story_id"]=="derivative"
    assert selected.candidates[0]["importance"]==.9


def test_shared_footer_without_matching_original_body_does_not_create_duplicate():
    a,b=launch_pair()
    b["sources"][0]["summary"]="The post "+a["sources"][0]["summary"]+" appeared first on Example Media."
    assert run([a,b]).event_analysis["content_duplicates"]==0
