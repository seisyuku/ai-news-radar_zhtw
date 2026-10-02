"""Pre-push regressions for feed validity, unknown counts and bounded reads."""

from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from scripts import update_news as news


NOW = datetime(2026, 10, 3, 0, tzinfo=timezone.utc)
EMPTY = b'<rss version="2.0"><channel><title>Empty</title></channel></rss>'
GOOD = b'<rss version="2.0"><channel><title>Good</title><item><title>AI launch</title><link>https://example.test/news</link><pubDate>Fri, 02 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("invalid", [b'<html><body>Not a feed</body></html>', b'<rss>', b'<rss version="2.0"><channel><item><title>No link or date</title></item></channel></rss>'])
def test_opml_invalid_peer_fails_but_valid_empty_and_news_survive(tmp_path, monkeypatch, fallback, invalid):
    if fallback:
        monkeypatch.setattr(news, "feedparser", None)
    feeds = [{"title": name, "xml_url": f"https://example.test/{name}", "html_url": ""}
             for name in ("invalid", "empty", "good")]
    monkeypatch.setattr(news, "parse_opml_subscriptions", lambda _: feeds)
    bodies = {"invalid": invalid, "empty": EMPTY, "good": GOOD}
    monkeypatch.setattr(news.requests, "get", lambda url, **_: SimpleNamespace(
        content=bodies[url.rsplit('/', 1)[-1]], raise_for_status=lambda: None))
    items, summary, statuses = news.fetch_opml_rss(NOW, tmp_path / "input.opml")
    by_name = {row["feed_title"]: row for row in statuses}
    assert by_name["invalid"]["ok"] is False
    assert by_name["empty"]["ok"] is True and by_name["empty"]["item_count"] == 0
    assert by_name["good"]["ok"] is True and len(items) == 1
    assert summary["partial_failures"] == 1 and summary["ok"] is True
    # Inspect a temporary health artifact, never the checked-in snapshot.
    output = tmp_path / "source-status.json"
    output.write_text(json.dumps({"sites": [summary], "feeds": statuses}))
    assert json.loads(output.read_text())["sites"][0]["failed_feed_count"] == 1


@pytest.mark.parametrize("platform", ["douyin", "xiaohongshu"])
def test_missing_counts_do_not_invent_zero(platform):
    assert news.normalize_creator_metrics(platform, {}) == dict.fromkeys(("likes", "comments", "collects", "shares"))
    assert news.normalize_creator_metrics(platform, {"like_count": 0})["likes"] == 0
    assert news.normalize_creator_metrics(platform, {"like_count": "1,234"})["likes"] == 1234


@pytest.mark.parametrize("value", [None, "", "unknown", "NaN", "inf", -1, -0.5, True])
def test_invalid_count_stays_unknown_and_valid_alias_can_recover(value):
    assert news.creator_metric_count(value) is None
    assert news.creator_metric_count(value, 0) == 0


class Pages:
    def __init__(self, factory):
        self.factory = factory
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        payload = self.factory(self.calls)
        def read():
            if isinstance(payload, Exception):
                raise payload
            return payload
        return SimpleNamespace(raise_for_status=lambda: None, json=read)


def search(session):
    return news.fetch_socialdata_search(session, "test", "AI", NOW, 20)


def test_empty_changing_cursors_stop_at_page_cap():
    session = Pages(lambda n: {"tweets": [], "next_cursor": str(n)})
    items, diagnostics = search(session)
    assert not items and session.calls == news.SOCIALDATA_SEARCH_MAX_PAGES
    assert diagnostics["hit_page_cap"] is True


def test_raw_threshold_stops_even_when_none_map_and_counts_whole_page():
    session = Pages(lambda n: {"tweets": [{}] * 60, "next_cursor": str(n)})
    items, diagnostics = search(session)
    assert not items and session.calls == 2
    assert diagnostics["raw_tweet_count"] == 120  # page overshoot is reported, not hidden
    assert diagnostics["hit_raw_read_threshold"] is True


def test_bad_later_json_retains_usable_first_page():
    session = Pages(lambda n: {"tweets": [{"id": "one", "text": "AI release"}], "next_cursor": "next"}
                    if n == 1 else ValueError("malformed"))
    items, diagnostics = search(session)
    assert len(items) == 1 and session.calls == 2
    assert diagnostics["pagination_error"] == "ValueError"


def test_bad_first_page_fails():
    with pytest.raises(ValueError, match="invalid_socialdata_page"):
        search(Pages(lambda _: {"tweets": 42}))
