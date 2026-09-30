"""Current-run subsource health for the three aggregate source groups."""

from datetime import datetime, timezone
import re

import pytest

from scripts import update_news


NOW = datetime(2026, 9, 26, tzinfo=timezone.utc)
RECENT = "Fri, 25 Sep 2026 10:00:00 GMT"
OLD = "Fri, 01 Jan 2021 10:00:00 GMT"


def rss(date=RECENT, *, valid=True):
    if not valid:
        return b"<html>private token=do-not-report</html>"
    return (f"<rss><channel><title>News</title><item><title>AI model release</title>"
            f"<link>https://example.com/story</link><pubDate>{date}</pubDate>"
            "</item></channel></rss>").encode()


class Response:
    def __init__(self, content):
        self.content = content
        self.text = content.decode()

    def raise_for_status(self):
        pass


class Session:
    def __init__(self, responses):
        self.responses = responses

    def get(self, url, **kwargs):
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return Response(value)


@pytest.mark.parametrize("group,fetch_name,config_name", [
    ("official_ai", "fetch_official_ai_updates_with_status", "OFFICIAL_AI_FEEDS"),
    ("curated_media", "fetch_curated_ai_media_with_status", "CURATED_AI_MEDIA_FEEDS"),
    ("tw_media", "fetch_tw_media_with_status", "TW_MEDIA_FEEDS"),
])
@pytest.mark.parametrize("scenario", ["all_success", "partial", "all_failed", "valid_zero"])
def test_group_reports_each_subsource_without_losing_items(monkeypatch, group, fetch_name, config_name, scenario):
    feeds = (
        {"source_id": "first", "title": "First", "xml_url": "https://example.com/first"},
        {"source_id": "second", "title": "Second", "xml_url": "https://example.com/second"},
    )
    monkeypatch.setattr(update_news, config_name, feeds)
    responses = {feed["xml_url"]: rss(OLD if scenario == "valid_zero" else RECENT)
                 for feed in feeds}
    if scenario in {"partial", "all_failed"}:
        responses[feeds[1]["xml_url"]] = RuntimeError("secret=do-not-report")
    if scenario == "all_failed":
        responses[feeds[0]["xml_url"]] = rss(valid=False)
    if group == "official_ai":
        responses.update({
            "https://www.anthropic.com/news": b'<a href="/news/old"><h2>Old AI news</h2><time datetime="2021-01-01"></time></a>',
            update_news.TENCENT_NEWSROOM_URL: b'<article class="tc-blog-grid"><h2 class="blog-title"><a href="/old">Old AI news</a></h2><span class="tc-blogpost-date">2021-01-01</span></article>',
            "https://developers.openai.com/codex/changelog": b'<li id="old"><h3>Old AI news</h3><time datetime="2021-01-01"></time></li>',
        })
        if scenario == "all_failed":
            for url in list(responses)[2:]:
                responses[url] = RuntimeError("secret=do-not-report")
    items, details = getattr(update_news, fetch_name)(Session(responses), NOW)
    rows = {row["source_id"]: row for row in details["subsources"]}
    assert len(rows) == (5 if group == "official_ai" else 2)
    assert all(row["ok"] for row in rows.values()) == (scenario in {"all_success", "valid_zero"})
    assert details["ok"] == (scenario != "all_failed")
    assert details["degraded"] == (scenario == "partial")
    assert len(items) == (0 if scenario in {"all_failed", "valid_zero"} else (1 if scenario == "partial" else 2))
    assert "do-not-report" not in str(details)


@pytest.mark.parametrize("group,fetch_name,config_name", [
    ("official_ai", "fetch_official_ai_updates_with_status", "OFFICIAL_AI_FEEDS"),
    ("curated_media", "fetch_curated_ai_media_with_status", "CURATED_AI_MEDIA_FEEDS"),
    ("tw_media", "fetch_tw_media_with_status", "TW_MEDIA_FEEDS"),
])
def test_invalid_item_fields_are_failure_not_valid_zero(monkeypatch, group, fetch_name, config_name):
    feed = {"source_id": "bad_fields", "title": "Bad", "xml_url": "https://example.com/bad"}
    monkeypatch.setattr(update_news, config_name, (feed,))
    content = b'<rss><channel><item><title>Missing link and date</title></item></channel></rss>'
    responses = {feed["xml_url"]: content}
    if group == "official_ai":
        responses.update({
            "https://www.anthropic.com/news": RuntimeError("down"),
            update_news.TENCENT_NEWSROOM_URL: RuntimeError("down"),
            "https://developers.openai.com/codex/changelog": RuntimeError("down"),
        })
    items, details = getattr(update_news, fetch_name)(Session(responses), NOW)
    assert items == []
    assert details["ok"] is False
    assert details["subsources"][0]["ok"] is False


def test_configured_subsource_ids_are_stable_and_secret_safe():
    ids = [feed["source_id"] for group in (
        update_news.OFFICIAL_AI_FEEDS,
        update_news.CURATED_AI_MEDIA_FEEDS,
        update_news.TW_MEDIA_FEEDS,
    ) for feed in group]
    ids += ["anthropic_news", "tencent_newsroom", "openai_codex_changelog"]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", source_id) for source_id in ids)


def test_valid_empty_rss_is_healthy_but_malformed_rss_fails():
    empty = b"<rss version='2.0'><channel><title>Quiet feed</title></channel></rss>"
    assert update_news.parse_group_feed_entries(empty, NOW) == []
    with pytest.raises(ValueError):
        update_news.parse_group_feed_entries(b"<html>not a feed</html>", NOW)


def test_collect_all_preserves_group_health_details(monkeypatch):
    group_details = {
        "official_ai": {"ok": True, "degraded": True, "degraded_reason": "partial_subsource_failure",
                        "error": None, "subsources": [{"source_id": "one", "ok": False, "item_count": 0, "error": "fetch_failed"}]},
        "curated_media": {"ok": False, "degraded": False, "degraded_reason": None,
                          "error": "all_subsources_failed", "subsources": [{"source_id": "two", "ok": False, "item_count": 0, "error": "invalid_source"}]},
        "tw_media": {"ok": True, "degraded": False, "degraded_reason": None,
                     "error": None, "subsources": [{"source_id": "three", "ok": True, "item_count": 0, "error": None}]},
    }
    for site_id, fn in (
        ("official_ai", "fetch_official_ai_updates_with_status"),
        ("curated_media", "fetch_curated_ai_media_with_status"),
        ("tw_media", "fetch_tw_media_with_status"),
    ):
        monkeypatch.setattr(update_news, fn, lambda *_args, site_id=site_id: ([], group_details[site_id]))
    for fn in (
        "fetch_mistral_news", "fetch_mcp_blog", "fetch_arc_prize",
        "fetch_llm_stats_model_releases", "fetch_llm_rumors", "fetch_runtimewire_models",
        "fetch_kr36_ai", "fetch_juya_daily",
    ):
        monkeypatch.setattr(update_news, fn, lambda *_: [])
    monkeypatch.setattr(update_news, "fetch_aibase_with_status", lambda *_: ([], {}))
    _, statuses = update_news.collect_all(object(), NOW)
    by_id = {status["site_id"]: status for status in statuses}
    for site_id, details in group_details.items():
        assert all(by_id[site_id][field] == value for field, value in details.items())
