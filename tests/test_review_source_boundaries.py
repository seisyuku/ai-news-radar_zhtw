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
