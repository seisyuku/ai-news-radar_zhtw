"""Structured official index only; fixed sample trimmed from 2026-11-03 HTTP data."""
import copy
import json
from pathlib import Path

import pytest

from scripts import update_news as u


NOW = u.parse_iso("2026-11-02T12:00:00Z")
PAYLOAD = json.loads((Path(__file__).parent / "fixtures/claude-product-announcements-message-threads.json").read_text())
ROW = PAYLOAD["curated"]["items"][0]


def page(rows=None, *, payload=None, split=False):
    props = copy.deepcopy(PAYLOAD if payload is None else payload)
    if rows is not None:
        props["curated"] = {"items": rows, "total": len(rows)}
    record = '42:' + json.dumps(["$", "$L44", None, props], ensure_ascii=False) + '\n'
    chunks = [record[:len(record)//2], record[len(record)//2:]] if split else [record]
    return '<html><script>self.__next_f.push([0])</script>' + ''.join(
        '<script>self.__next_f.push(' + json.dumps([1, chunk], ensure_ascii=False) + ')</script>'
        for chunk in chunks) + '</html>'


def parse(rows=None, **kwargs):
    return u.parse_claude_product_announcements_items(page(rows, **kwargs), NOW, require_valid=True)


@pytest.mark.parametrize("split", [False, True])
def test_official_message_threads_sample_keeps_utf8_and_date_precision(split):
    items = parse(split=split)
    assert len(items) == 1
    item = items[0]
    assert item.title == ROW["title"]
    assert item.url == "https://claude.com/resources/articles/message-threads"
    assert item.published_at == u.parse_iso("2026-11-02T00:00:00Z")
    assert item.source == "Claude Product Announcements" and item.site_id == "official_ai"
    assert item.meta["summary"] == ROW["excerpt"] and "what’s" in item.meta["summary"]
    assert item.meta["source_published_date"] == "2026-11-02"
    assert item.meta["source_time_precision"] == "date"
    assert u.is_within_reader_window({"published_at": u.iso(item.published_at)}, NOW, 24)
    assert not u.is_within_reader_window({"published_at": u.iso(item.published_at)}, u.parse_iso("2026-11-03T00:46:04Z"), 24)


@pytest.mark.parametrize("field,value", [
    ("categorySlugs", "product-announcements"),
    ("slug", "../message-threads"), ("slug", "https://example.com/a"), ("slug", "message-threads.pdf"),
    ("slug", "message-threads?format=pdf"), ("slug", "message%2fthreads"), ("slug", ""),
    ("title", ""), ("title", {"text": "Invented"}), ("date", "2026-02-30"), ("date", "November 2"),
    ("date", "2026-11-02T08:00:00Z"), ("date", None), ("excerpt", {"text": "Invented"}),
])
def test_invalid_article_fields_cannot_become_articles(field, value):
    bad = dict(ROW, **{field: value})
    with pytest.raises(ValueError, match="invalid_claude_index_fields"):
        parse([bad])
    assert len(parse([bad, ROW])) == 1


@pytest.mark.parametrize("change", [
    {"_type": "video"}, {"categorySlugs": ["best-practices"]},
    {"externalUrl": "https://example.com/story"},
    {"externalUrl": "https://claude.com/resources/articles/message-threads"},
])
def test_valid_filtered_index_is_healthy_zero_without_admitting_excluded_material(change):
    excluded = dict(ROW, **change)
    items, status = u._group_subsource_status("claude_product_announcements", lambda: parse([excluded]))
    assert items == [] and status["ok"] and status["item_count"] == 0
    assert len(parse([excluded, ROW])) == 1


def test_excluded_entries_do_not_hide_unusable_in_scope_article_fields():
    with pytest.raises(ValueError, match="invalid_claude_index_fields"):
        parse([dict(ROW, externalUrl="https://example.com/announcement"), dict(ROW, date=None)])


def test_filter_and_dedupe_precede_cap_and_results_are_latest_first():
    invalid = [dict(ROW, slug=f"guide-{i}", categorySlugs=["best-practices"]) for i in range(30)]
    valid = [dict(ROW, slug=f"announcement-{i}", date=f"2026-10-{i+1:02d}") for i in range(25)]
    items = parse(invalid + valid + valid + [ROW])
    assert len(items) == 20 and len({x.url for x in items}) == 20
    assert items[0].url.endswith("/message-threads")
    assert items[-1].url.endswith("/announcement-6")
    assert [x.published_at for x in items] == sorted((x.published_at for x in items), reverse=True)


@pytest.mark.parametrize("rows", [[], [dict(ROW, date="2021-01-01")], [dict(ROW, date="2026-11-03")]])
def test_valid_empty_old_or_future_only_index_is_healthy_zero(rows):
    items, status = u._group_subsource_status("claude_product_announcements", lambda: parse(rows))
    assert items == [] and status["ok"] and status["item_count"] == 0


def test_future_day_inside_shared_clock_tolerance_still_stays_out():
    now = u.parse_iso("2026-11-02T23:00:00Z")
    assert u.is_within_reader_window({"published_at": "2026-11-03T00:00:00Z"}, now, 24)
    assert u.parse_claude_product_announcements_items(page([dict(ROW, date="2026-11-03")]), now, require_valid=True) == []


@pytest.mark.parametrize("props", [
    {"scope": {"kind": "type", "value": "product-announcements"}, "curated": {"items": [ROW], "total": 1}},
    {"scope": {"kind": "category", "value": "best-practices"}, "curated": {"items": [ROW], "total": 1}},
    {**PAYLOAD, "curated": {"items": [], "total": 162}},
    {**PAYLOAD, "curated": {"items": [ROW], "total": True}},
    {**PAYLOAD, "curated": {"items": ["not a row"], "total": 1}},
    {**PAYLOAD, "curated": None},
])
def test_changed_index_contract_is_failure(props):
    with pytest.raises(ValueError, match="invalid_claude_index"):
        parse(payload=props)


@pytest.mark.parametrize("html", [
    '<h1>Product announcements</h1><a href="/resources/articles/message-threads">2026-11-02 Message threads</a>',
    '<article><h1>Message threads</h1><p>Now available in Claude</p></article>',
    '<script src="https://example.com/index.js"></script>',
    '<script>self.__next_f.push(not_json)</script>',
    '<script type="application/ld+json">{"datePublished":"2026-11-02"}</script>',
])
def test_no_prose_dom_or_script_execution_fallback(html):
    with pytest.raises(ValueError, match="invalid_claude_index"):
        u.parse_claude_product_announcements_items(html, NOW, require_valid=True)
    assert u.parse_claude_product_announcements_items(html, NOW) == []


def test_ambiguous_category_payload_is_failure_and_bad_source_status_is_safe():
    html = page() + page()
    _, status = u._group_subsource_status("claude_product_announcements", lambda:
        u.parse_claude_product_announcements_items(html, NOW, require_valid=True))
    assert not status["ok"] and status["error"] == "invalid_source"


class Response:
    def __init__(self, body=None, mime="text/html; charset=utf-8", status=200):
        self.body = page().encode() if body is None else body
        self.headers = {"Content-Type": mime}
        self.status_code = status
        self.closed = False
        self.body_reads = 0

    def raise_for_status(self):
        if self.status_code >= 400:
            raise u.requests.HTTPError("private diagnostic must not appear")

    def iter_content(self, size):
        self.body_reads += 1
        for start in range(0, len(self.body), size):
            yield self.body[start:start+size]

    def close(self):
        self.closed = True


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_fetch_uses_only_fixed_index_and_preserves_same_id_across_repeated_reads():
    response = Response()
    session = Session(response)
    items = u.fetch_claude_product_announcements(session, NOW)
    assert session.calls == [(u.CLAUDE_PRODUCT_ANNOUNCEMENTS_URL,
                              {"timeout": 20, "stream": True, "allow_redirects": False})]
    assert response.closed and len(items) == 1
    archive = {}
    u.merge_raw_items_into_archive(archive, items, NOW)
    before = copy.deepcopy(archive)
    u.merge_raw_items_into_archive(archive, items, NOW + u.timedelta(hours=3))
    assert len(archive) == 1 and archive.keys() == before.keys()
    item_id = next(iter(archive))
    assert archive[item_id]["url"] == items[0].url
    assert archive[item_id]["published_at"] == before[item_id]["published_at"]


@pytest.mark.parametrize("mime", ["application/pdf", "image/png", "audio/mpeg", "video/mp4", "application/zip"])
def test_attachment_mime_is_rejected_before_body_read(mime):
    response = Response(mime=mime)
    with pytest.raises(ValueError, match="unsupported_evidence_format"):
        u.fetch_claude_product_announcements(Session(response), NOW)
    assert response.closed and response.body_reads == 0


@pytest.mark.parametrize("body", [b"%PDF-not-html", b"PK\x03\x04not-html", b"\x89PNGnot-html", b"\xffnot-utf8"])
def test_binary_body_cannot_masquerade_as_text(body):
    response = Response(body)
    with pytest.raises(ValueError):
        u.fetch_claude_product_announcements(Session(response), NOW)
    assert response.closed


def test_oversize_and_redirect_are_rejected_without_followup_requests():
    for response in [Response(b"x" * (u.CLAUDE_PRODUCT_ANNOUNCEMENTS_MAX_BYTES + 1)), Response(status=302)]:
        session = Session(response)
        with pytest.raises(ValueError):
            u.fetch_claude_product_announcements(session, NOW)
        assert len(session.calls) == 1 and response.closed


def test_missing_summary_stays_empty_instead_of_borrowing_other_text():
    items = parse([dict(ROW, excerpt=None)])
    assert items[0].meta["summary"] == ""
