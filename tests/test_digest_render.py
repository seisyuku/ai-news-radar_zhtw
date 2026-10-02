import json
from copy import deepcopy

import pytest

from scripts.digest_render import RenderError, render_digest


WINDOW = {"date": "2026-10-02", "start_utc": "2026-09-30T22:00:00Z", "end_utc": "2026-10-01T22:00:00Z"}


def candidate(**overrides):
    row = {
        "story_id": "s-1", "title": "AI *突破* [測試]", "title_original": "AI *突破* [測試]",
        "primary_url": "https://example.com/a_(1)", "primary_published_at": "2026-10-01T12:00:00Z",
        "summary": "摘要含 # 標記與 `code`。", "summary_kind": "publisher", "sources": [{"title": "原始 [標題]", "url": "https://example.com/source", "source": "Publisher", "published_at": "2026-10-01T12:00:00Z"}],
    }
    row.update(overrides)
    return row


def doc(candidates=None, health=None, diagnostics=None):
    return {"window": WINDOW, "candidates": [] if candidates is None else candidates, "health": health, "diagnostics": diagnostics or []}


def test_render_is_deterministic_and_keeps_window_title_summary_evidence():
    document = doc([candidate()], {"notices": ["health_not_window_coverage", "archive_not_new_fetch"]})
    first = render_digest(document)
    assert first == render_digest(deepcopy(document))
    assert "# AI 新聞日報｜2026\\-10\\-02" in first
    assert "涵蓋窗口：2026-10-01 06:00 至 2026-10-02 06:00（Asia/Taipei；起點含、終點不含）" in first
    assert "AI \\*突破\\* \\[測試\\]" in first and "摘要含 \\# 標記" in first
    assert "[原始 \\[標題\\]](https://example.com/source)" in first
    assert "來源：" in first and "Publisher" in first


def test_empty_day_is_valid_and_does_not_invent_story():
    output = render_digest(doc(health={"notices": ["health_missing"]}))
    assert "本期沒有符合既有選題條件" in output
    assert "來源健康資料缺失" in output


def test_missing_summary_and_source_are_explicit():
    output = render_digest(doc([candidate(title="Only title", summary=None, sources=[])]))
    assert "沒有可用的出版者摘要" in output
    assert "來源：未標示來源" in output


@pytest.mark.parametrize("code,text", [
    ("health_mismatched", "不是同一時間快照"), ("health_unverifiable", "無法核對"),
    ("input_before_cutoff", "早於本期截止"), ("source_failures", "部分來源本輪失敗"),
])
def test_health_uses_only_controlled_notice_text(code, text):
    output = render_digest(doc(health={"alignment": code.removeprefix("health_"), "notices": [code], "error": "secret-token", "site_id": "private@example.com"}))
    assert text in output
    assert "secret-token" not in output and "private@example.com" not in output


def test_unknown_notice_and_raw_diagnostics_are_not_rendered():
    output = render_digest(doc(health={"notices": ["unknown_raw_error", "health_not_window_coverage"]}, diagnostics=[{"code": "internal", "count": 1}]))
    assert "unknown_raw_error" not in output and "internal" not in output
    assert "生成備註" in output


@pytest.mark.parametrize("bad", [None, {}, {"window": {"date": "x", "start_utc": "a", "end_utc": "b"}}])
def test_invalid_document_or_window_fails_safely(bad):
    with pytest.raises(RenderError):
        render_digest(bad)


def test_invalid_urls_are_not_link_targets():
    output = render_digest(doc([candidate(primary_url="javascript:alert(1)", sources=[{"title": "bad", "url": "javascript:alert(1)"}])]))
    assert "javascript:" not in output
    assert "bad" in output


@pytest.mark.parametrize("candidate_override", [{"title": None, "title_original": None}, "bad"])
def test_bad_candidate_fails_without_fallback_invention(candidate_override):
    with pytest.raises(RenderError):
        render_digest(doc([candidate(**candidate_override) if isinstance(candidate_override, dict) else candidate_override]))


def test_output_is_json_safe_input_and_does_not_mutate():
    document = doc([candidate()], {"notices": []})
    before = deepcopy(document)
    result = render_digest(document)
    assert document == before
    json.dumps(result, ensure_ascii=False)


def test_parentheses_url_and_html_multiline_cannot_break_markdown():
    output = render_digest(doc([candidate(title="<script>\n# injected", summary="hello\n<script>alert(1)</script>")]))
    assert "https://example.com/a_%281%29" in output
    assert "<script>" not in output and "\n# injected" not in output
    assert "&lt;script&gt;" in output


@pytest.mark.parametrize("changes", [{"date": "2026-02-30"},
    {"start_utc": "2026-10-01T22:00:00Z", "end_utc": "2026-10-02T22:00:00Z"}])
def test_invalid_calendar_or_wrong_issue_window_is_rejected(changes):
    document = doc()
    document["window"] = {**WINDOW, **changes}
    with pytest.raises(RenderError):
        render_digest(document)


@pytest.mark.parametrize("kind", [None, "ai", "unknown"])
def test_untyped_summary_is_not_claimed_to_be_publisher_content(kind):
    with pytest.raises(RenderError, match="unsupported_summary_kind"):
        render_digest(doc([candidate(summary_kind=kind)]))
