import copy
import json
from pathlib import Path

import pytest
import requests

from scripts import evaluate_tw_source_admission as shadow

FIXTURES = Path(__file__).parent / "fixtures" / "tw_source_admission"
NOW = shadow.timestamp("2026-10-21T00:00:00Z")
SOURCE = shadow.SOURCES[1]
COVERAGE = ("2026-10-14T00:00:00Z", "2026-10-21T00:00:00Z")


def articles():
    return shadow.parse_feed((FIXTURES / "rss.xml").read_bytes(), SOURCE, SOURCE["home"] + "feed/")[0]


def capture(items=None):
    return {"generated_at": shadow.iso(NOW), "sources": [{**SOURCE,
            "status": "verified_native_feed", "requests": [], "articles": articles() if items is None else items}]}


def baseline():
    return {"generated_at": shadow.iso(NOW), "items": [{
        "title": "OpenAI 發布測試模型", "url": "https://official.example/release",
        "published_at": "2026-10-20T10:00:00Z", "source": "OpenAI"}]}


def test_rss_normalizes_dates_and_tracking_but_keeps_native_evidence_only():
    rows = articles()
    assert len(rows) == 9
    assert rows[0]["published_at"] == rows[1]["published_at"] == "2026-10-20T10:00:00Z"
    assert rows[0]["canonical_url"] == "https://cyberq.tw/synthetic-release"
    assert rows[0]["summary_if_provided"] == "AI 模型正式發布。"
    assert "FULL BODY" not in json.dumps(rows)
    assert rows[-1]["retrieval_status"] == rows[-2]["retrieval_status"] == "invalid_metadata"
    assert rows[0]["canonical_method"] == "feed_alternate_link_unverified"


def test_atom_uses_alternate_link_and_publication_not_updated():
    rows, status = shadow.parse_feed((FIXTURES / "atom.xml").read_bytes(), SOURCE, SOURCE["home"])
    assert status["status"] == "valid_feed"
    assert rows[0]["canonical_url"] == "https://cyberq.tw/synthetic-atom"
    assert rows[0]["published_at"] == "2026-10-20T10:00:00Z"
    assert rows[1]["published_at"] is None
    assert not rows[1]["summary_if_provided"]


@pytest.mark.parametrize("xml", [b"broken", b"<rss>", b"<html/>", b"<rss/>"])
def test_broken_feed_is_failure(xml):
    with pytest.raises(ValueError):
        shadow.parse_feed(xml, SOURCE, SOURCE["home"])


@pytest.mark.parametrize("xml", [b"<rss><channel/></rss>", b'<feed xmlns="http://www.w3.org/2005/Atom"/>'])
def test_valid_empty_feed_is_success(xml):
    rows, status = shadow.parse_feed(xml, SOURCE, SOURCE["home"])
    assert rows == []
    assert status["status"] == "valid_empty"


def test_all_unusable_entries_fail_but_missing_fields_are_retained_for_diagnosis():
    rows, status = shadow.parse_feed(b"<rss><channel><item><title>AI release</title></item></channel></rss>", SOURCE, SOURCE["home"])
    assert status["status"] == "invalid_fields"
    assert rows[0]["filter_reason"] == "missing_url"


def test_sample_cap_is_explicit():
    rows, status = shadow.parse_feed((FIXTURES / "rss.xml").read_bytes(), SOURCE, SOURCE["home"], max_entries=2)
    assert len(rows) == 2
    assert status == {"status": "valid_feed", "entry_count": 9, "sampled_entries": 2, "truncated": True}


@pytest.mark.parametrize("date", ["October 2026 10:00 UTC", "2026-10 10:00 UTC", "2026-10-20T10:00:00"])
def test_partial_or_naive_date_never_invents_a_day_or_timezone(date):
    assert shadow.timestamp(date) is None


@pytest.mark.parametrize("url", ["https://not a host/path", "https://cyberq.tw:invalid/path", "https://cyberq.tw:99999/path"])
def test_unusable_url_cannot_be_counted_as_valid_article_metadata(url):
    assert not shadow.canonical_url(url)


def test_invalid_entry_does_not_hide_a_later_usable_entry_with_same_url():
    valid = articles()[0]
    invalid = valid | {"published_at": None, "retrieval_status": "invalid_metadata", "filter_reason": "missing_or_ambiguous_time"}
    s = shadow.evaluate(capture([invalid, valid]), baseline())["sources"][0]
    assert s["metrics"]["candidate_articles"] == 1
    assert s["articles"][0]["filter_reason"] == "missing_or_ambiguous_time"


@pytest.mark.parametrize(("title", "reason"), [
    ("如何部署 AI Agent 教學", "tutorial_or_evergreen"),
    ("AI 產業精選 10.20", "roundup"),
    ("AI 路由器開箱", "hardware_review"),
    ("AI 模型發布新聞稿", "sponsored"),
    ("AI 新創計畫募資", "proposal_or_forecast"),
    ("銀行發布財報", "no_ai_relation"),
    ("AI 治理觀點", "no_concrete_event_signal"),
    ("AI Agent 金鑰遭駭外洩", "candidate_requires_review"),
    ("AI 晶片供應鏈獲得訂單", "candidate_requires_review"),
    ("OpenAI 產品降價生效", "candidate_requires_review"),
    ("OpenAI降價搶市", "candidate_requires_review"),
    ("AI伺服器獲得供應鏈訂單", "candidate_requires_review"),
    ("ChatGPT廣告主增加", "no_concrete_event_signal"),
    ("MiniMax H3 獨立實測", "candidate_requires_review"),
    ("新Agentic RAG功能推出", "candidate_requires_review"),
    ("中國擬管制AI大模型出口，參數列入門檻", "proposal_or_forecast"),
    ("AI股票在NASDAQ上市", "candidate_requires_review"),
])
def test_shadow_only_filter(title, reason):
    a = articles()[0] | {"title": title, "summary_if_provided": ""}
    assert shadow.filter_article(a, NOW, 7) == reason


@pytest.mark.parametrize(("value", "allowed"), [
    ("2026-10-14T00:00:00Z", True), ("2026-10-13T23:59:59Z", False),
    ("2026-10-21T00:00:00Z", True), ("2026-10-21T00:00:01Z", False),
])
def test_time_window_boundaries(value, allowed):
    a = articles()[0] | {"published_at": value}
    assert (shadow.filter_article(a, NOW, 7) == "candidate_requires_review") == allowed


def test_no_matching_url_or_similar_title_is_never_automatically_novel_or_duplicate_event():
    report = shadow.evaluate(capture(), baseline(), coverage=COVERAGE)
    s = report["sources"][0]
    assert s["metrics"]["candidate_articles"] == 3
    assert s["metrics"]["novel_event_count"] == s["metrics"]["duplicate_event_count"] == 0
    assert s["metrics"]["false_positive_count"] is None
    assert s["articles"][0]["matches"][0]["status"] == "possible_event_manual_review"
    assert s["articles"][1]["possible_new_evidence"] is True
    assert s["articles"][2]["comparison"] == "needs_event_review"


def test_same_url_duplicate_and_duplicate_feed_entries_do_not_inflate_events():
    a = articles()[0]
    b = baseline()
    b["items"][0]["url"] = a["canonical_url"] + "?utm_source=x"
    s = shadow.evaluate(capture([a, a]), b)["sources"][0]
    assert s["metrics"]["duplicate_url_count"] == 1
    assert s["metrics"]["candidate_articles"] == 1
    assert s["articles"][1]["filter_reason"] == "duplicate_within_feed"


def test_bilingual_entity_and_event_hint_finds_same_incident_without_declaring_duplicate():
    a = articles()[0] | {"title": "AI Agent 金鑰失守，OpenCode 遇駭", "summary_if_provided": ""}
    b = baseline()
    b["items"][0]["title"] = "OpenCode warns users after legacy-system intrusion"
    # Same baseline URL can have multiple translated/archive variants.
    b["items"].append(dict(b["items"][0]))
    s = shadow.evaluate(capture([a]), b, coverage=COVERAGE)["sources"][0]
    assert len(s["articles"][0]["matches"]) == 1
    assert s["articles"][0]["matches"][0]["shared_entities"] == ["opencode"]
    assert s["articles"][0]["comparison"] == "needs_event_review"
    assert s["metrics"]["duplicate_event_count"] == 0


def review(a, decision, **kwargs):
    return {"canonical_url": a["canonical_url"], "decision": decision, "reason": "Synthetic manual adjudication only", **kwargs}


def test_review_distinguishes_duplicate_event_new_evidence_and_novel_event():
    aa = articles()
    reviews = [review(aa[0], "duplicate_event", baseline_url=baseline()["items"][0]["url"], event_id="model-release"),
               review(aa[1], "new_evidence", baseline_url=baseline()["items"][0]["url"]),
               review(aa[2], "novel_event", event_id="funding")]
    m = shadow.evaluate(capture(), baseline(), coverage=COVERAGE, reviews=reviews)["sources"][0]["metrics"]
    assert m["duplicate_event_count"] == m["new_evidence_count"] == m["novel_event_count"] == 1
    assert m["reviewed_articles"] == 3
    assert m["unresolved_articles"] == 0


def test_multiple_articles_about_same_reviewed_event_count_once():
    aa = articles()[:2]
    reviews = [review(a, "novel_event", event_id="one-event") for a in aa]
    m = shadow.evaluate(capture(aa), baseline(), coverage=COVERAGE, reviews=reviews)["sources"][0]["metrics"]
    assert m["novel_event_count"] == 1


def test_false_positive_denominator_is_reviewed_sample_not_all_fetched():
    reviews = [review(articles()[0], "false_positive")]
    m = shadow.evaluate(capture(), baseline(), reviews=reviews)["sources"][0]["metrics"]
    assert m["false_positive_count"] == m["reviewed_articles"] == 1
    assert m["fetched_articles"] == 7


def test_missing_or_short_baseline_cannot_prove_novelty():
    a = articles()[0]
    for coverage in [None, ("2026-10-21T00:00:00Z", "2026-10-21T00:00:00Z")]:
        report = shadow.evaluate(capture([a]), baseline(), coverage=coverage)
        assert report["sources"][0]["articles"][0]["comparison"] == "baseline_window_unverified"
        with pytest.raises(ValueError, match="aligned_coverage"):
            shadow.evaluate(capture([a]), baseline(), coverage=coverage, reviews=[review(a, "novel_event", event_id="x")])


def test_review_must_reference_baseline_and_cannot_be_silently_stale():
    a = articles()[0]
    with pytest.raises(ValueError, match="existing_baseline_url"):
        shadow.evaluate(capture(), baseline(), reviews=[review(a, "new_evidence", baseline_url="https://wrong.example/")])
    with pytest.raises(ValueError, match="not_in_current_candidate"):
        shadow.evaluate(capture(), baseline(), reviews=[review(a | {"canonical_url": "https://wrong.example/"}, "false_positive")])


def test_same_article_cannot_be_claimed_as_independent_evidence():
    a = articles()[0]
    b = baseline()
    b["items"][0]["url"] = a["canonical_url"]
    with pytest.raises(ValueError, match="not_independent_evidence"):
        shadow.evaluate(capture(), b, reviews=[review(a, "new_evidence", baseline_url=a["canonical_url"])])


def test_meet_shares_publisher_group_and_not_formal_source():
    from scripts.update_news import TW_MEDIA_FEEDS
    assert next(s for s in shadow.SOURCES if s["source_id"] == "meet")["group"] == "bnext_media"
    assert {s["source_id"] for s in TW_MEDIA_FEEDS} == {"inside", "ithome", "technews_tw", "bnext_news"}
    assert not set(s["source_id"] for s in shadow.SOURCES) & {s["source_id"] for s in TW_MEDIA_FEEDS}
    assert "evaluate_tw_source_admission" not in (shadow.ROOT / "scripts/update_news.py").read_text()


class Response:
    def __init__(self, body=b"", code=200, headers=None):
        self.body, self.status_code, self.headers = body, code, headers or {}
        self.is_redirect = code in {301, 302, 303, 307, 308}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_content(self, size):
        yield self.body


class Session:
    def __init__(self, responses):
        self.responses, self.calls, self.headers = iter(responses), [], {}

    def get(self, url, **kwargs):
        self.calls.append(url)
        assert kwargs["allow_redirects"] is False
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def client(*responses):
    s = Session(responses)
    return shadow.ProbeClient(["cyberq.tw"], session=s, pause=lambda _: None), s


def test_robots_denial_or_failure_stops_content_fetch():
    for response in [Response(b"User-agent: *\nDisallow: /"), Response(code=503), Response(b"<!DOCTYPE html><html>Error</html>")]:
        c, s = client(response)
        _, row = c.request("https://cyberq.tw/feed/")
        assert row["status"] == "robots_blocked_or_unavailable"
        assert s.calls == ["https://cyberq.tw/robots.txt"]


def test_robots_404_permits_and_cross_host_redirect_is_not_followed():
    c, s = client(Response(code=404), Response(code=302, headers={"Location": "https://bridge.example/feed"}))
    _, row = c.request("https://cyberq.tw/feed/")
    assert row["status"] == "outside_publisher_hosts"
    assert s.calls == ["https://cyberq.tw/robots.txt", "https://cyberq.tw/feed/"]


@pytest.mark.parametrize("status", [401, 403, 429])
def test_access_control_stops_further_requests(status):
    c, s = client(Response(code=404), Response(code=status))
    c.request("https://cyberq.tw/feed/")
    _, row = c.request("https://cyberq.tw/feed.xml")
    assert row["status"] == "origin_stopped"
    assert len(s.calls) == 2


def test_timeout_is_reported_without_exception_details_and_size_is_bounded():
    c, _ = client(requests.Timeout("private exception details"))
    _, row = c.request("https://cyberq.tw/robots.txt", robots=True)
    assert row["status"] == "Timeout"
    assert "private" not in json.dumps(row)
    c, _ = client(Response(code=404), Response(b"x" * 2_000_001))
    body, row = c.request("https://cyberq.tw/feed/")
    assert body == b""
    assert row["status"] == "response_too_large"


def test_output_cannot_touch_project_even_through_symlink(tmp_path):
    with pytest.raises(ValueError, match="outside_repository"):
        shadow.external_output(shadow.ROOT / "data")
    (tmp_path / "project").symlink_to(shadow.ROOT, target_is_directory=True)
    with pytest.raises(ValueError, match="outside_repository"):
        shadow.external_output(tmp_path / "project" / "data")


def test_replay_cli_is_offline_and_reproducible_without_mutating_inputs(tmp_path, monkeypatch):
    original, b = capture(), baseline()
    frozen = copy.deepcopy(original)
    cap, base = tmp_path / "input.json", tmp_path / "baseline.json"
    cap.write_text(json.dumps(original))
    base.write_text(json.dumps(b))
    output = tmp_path / "out"

    def no_network(*args, **kwargs):
        pytest.fail("offline replay attempted network")

    monkeypatch.setattr(requests.Session, "get", no_network)
    monkeypatch.setattr("sys.argv", ["admission", "--replay", str(cap), "--baseline", str(base), "--output-dir", str(output)])
    shadow.main()
    report = (output / "report.json").read_bytes()
    shadow.main()
    assert report == (output / "report.json").read_bytes()
    assert json.loads(cap.read_text()) == frozen
    assert (output / "REPORT.md").read_text().startswith("# 台灣來源影子准入評估")
