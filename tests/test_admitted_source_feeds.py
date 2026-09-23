from datetime import datetime, timezone

import pytest

from scripts.update_news import (
    ADMITTED_SOURCE_FEEDS,
    _llm_radar_model_verification,
    business_event_score,
    fetch_feed_as_source_items,
    source_tier_for_record,
)


NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


class FeedSession:
    def __init__(self, content: bytes):
        self.content = content

    def get(self, _url, **_kwargs):
        return self

    def raise_for_status(self):
        return None


def test_mistral_keeps_announcements_and_excludes_customer_case_studies():
    xml = b"""<rss><channel>
      <item><title>Mistral raises funding for open models</title>
        <link>https://mistral.ai/news/funding</link>
        <pubDate>Tue, 22 Sep 2026 10:00:00 GMT</pubDate>
        <description>New funding for open-weight AI.</description></item>
      <item><title>Modernizing legacy code with AI agents</title>
        <link>https://mistral.ai/news/customer-case</link>
        <pubDate>Tue, 22 Sep 2026 09:00:00 GMT</pubDate>
        <description>Learn how the customer migrated its code.</description></item>
      <item><title>Mistral announcement relayed elsewhere</title>
        <link>https://example.com/relayed</link>
        <pubDate>Tue, 22 Sep 2026 08:00:00 GMT</pubDate></item>
    </channel></rss>"""
    items = fetch_feed_as_source_items(FeedSession(xml), ADMITTED_SOURCE_FEEDS["mistral_news"], NOW)

    assert [item.title for item in items] == ["Mistral raises funding for open models"]
    assert items[0].site_id == "official_ai"
    assert items[0].meta["summary"] == "New funding for open-weight AI."


def test_mcp_explainer_is_excluded_but_a_valid_empty_run_is_healthy():
    xml = b"""<rss><channel>
      <item><title>The New MCP Roadmap</title><link>https://blog.modelcontextprotocol.io/roadmap</link>
        <pubDate>Tue, 22 Sep 2026 10:00:00 GMT</pubDate></item>
      <item><title>Understanding MCP Extensions</title><link>https://blog.modelcontextprotocol.io/explainer</link>
        <pubDate>Tue, 22 Sep 2026 09:00:00 GMT</pubDate></item>
    </channel></rss>"""
    feed = ADMITTED_SOURCE_FEEDS["mcp_blog"]
    items = fetch_feed_as_source_items(FeedSession(xml), feed, NOW)
    assert [item.title for item in items] == ["The New MCP Roadmap"]
    assert items[0].site_id == "official_ai"

    old_xml = xml.replace(b"2026", b"2025")
    assert fetch_feed_as_source_items(FeedSession(old_xml), feed, NOW) == []


def test_arc_prize_is_a_third_party_benchmark_not_a_model_vendor():
    xml = b"""<feed xmlns="http://www.w3.org/2005/Atom">
      <entry><title>OpenAI's GPT-6 Astra on ARC-AGI-3</title>
        <link href="https://arcprize.org/blog/gpt-6-astra"/>
        <published>2026-09-22T10:00:00Z</published><summary>Benchmark result.</summary></entry>
      <entry><title>ARC Prize Foundation Statement on the AI Action Plan</title>
        <link href="https://arcprize.org/blog/policy"/>
        <published>2026-09-22T09:00:00Z</published></entry>
    </feed>"""
    items = fetch_feed_as_source_items(FeedSession(xml), ADMITTED_SOURCE_FEEDS["arc_prize"], NOW)

    assert len(items) == 1
    assert items[0].site_id == "arc_prize"
    assert source_tier_for_record({"site_id": items[0].site_id, "source": items[0].source}) == {
        "source_tier": "benchmark", "source_tier_label": "評測第三方", "source_tier_rank": 2,
    }
    assert _llm_radar_model_verification({"site_id": items[0].site_id}) == ("reported", "第三方評測")
    assert business_event_score({
        "site_id": items[0].site_id, "title": items[0].title,
        "summary": items[0].meta["summary"],
    }) == ["benchmark"]


def test_admitted_feed_reports_malformed_xml_as_a_failure():
    with pytest.raises(ValueError, match="Malformed feed|No parseable feed entries"):
        fetch_feed_as_source_items(
            FeedSession(b"<html><body>not a feed</body></html>"),
            ADMITTED_SOURCE_FEEDS["arc_prize"],
            NOW,
        )


@pytest.mark.parametrize("link,date", [
    ("https://mistral.ai/news/missing-date", ""),
    ("https://example.com/relayed", "<pubDate>Tue, 22 Sep 2026 10:00:00 GMT</pubDate>"),
])
def test_admitted_feed_reports_lost_first_party_date_fields(link, date):
    xml = f"""<rss><channel><item><title>Mistral announcement</title>
      <link>{link}</link>{date}</item></channel></rss>""".encode()
    with pytest.raises(ValueError, match="No dated first-party entries"):
        fetch_feed_as_source_items(FeedSession(xml), ADMITTED_SOURCE_FEEDS["mistral_news"], NOW)
