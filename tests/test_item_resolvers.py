import json
from datetime import datetime, timedelta, timezone

from scripts.update_news import (
    make_item_id,
    prune_archive_records,
    write_item_html_adapters,
    write_item_resolvers,
)


UTC = timezone.utc
NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)


def archive_item(item_id: str, *, last_seen_at: datetime, url: str) -> dict:
    return {
        "id": item_id,
        "site_id": "official_ai",
        "site_name": "官方更新",
        "source": "Example Newsroom",
        "title": "Example AI announcement",
        "summary": "Existing Radar source summary.",
        "url": url,
        "published_at": "2026-09-07T10:00:00Z",
        "first_seen_at": "2026-09-07T10:00:00Z",
        "last_seen_at": last_seen_at.isoformat().replace("+00:00", "Z"),
    }


def test_40_char_item_id_writes_matching_public_resolver(tmp_path):
    source_url = "https://example.com/news/ai-announcement"
    item_id = make_item_id("official_ai", "Example Newsroom", "Example AI announcement", source_url)
    assert len(item_id) == 40

    item = archive_item(item_id, last_seen_at=NOW, url=source_url)
    assert write_item_resolvers(tmp_path, {item_id: item}) == 1

    resolver = json.loads((tmp_path / "items" / f"{item_id}.json").read_text(encoding="utf-8"))
    assert resolver["id"] == item_id
    assert resolver["url"] == item["url"]
    assert resolver["summary"] == item["summary"]


def test_resolver_is_removed_when_its_archive_record_exceeds_retention(tmp_path):
    fresh_id = make_item_id("official_ai", "Example Newsroom", "Fresh", "https://example.com/fresh")
    expired_id = make_item_id("official_ai", "Example Newsroom", "Expired", "https://example.com/expired")
    archive = {
        fresh_id: archive_item(fresh_id, last_seen_at=NOW - timedelta(days=20), url="https://example.com/fresh"),
        expired_id: archive_item(expired_id, last_seen_at=NOW - timedelta(days=22), url="https://example.com/expired"),
    }

    write_item_resolvers(tmp_path, archive)
    retained = prune_archive_records(archive, NOW, archive_days=21)
    write_item_resolvers(tmp_path, retained)

    assert (tmp_path / "items" / f"{fresh_id}.json").exists()
    assert not (tmp_path / "items" / f"{expired_id}.json").exists()


def test_html_adapter_uses_archive_record_and_escapes_content(tmp_path):
    item_id = make_item_id("official_ai", "Example Newsroom", "HTML", "https://example.com/news/123")
    item = archive_item(item_id, last_seen_at=NOW, url="https://example.com/news/123?x=1&y=2")
    item["title"] = 'Title <tag> & "quote"'
    item["summary"] = "Summary <unsafe> & 'quote'"
    archive = {item_id: item}

    assert write_item_resolvers(tmp_path / "data", archive) == 1
    assert write_item_html_adapters(tmp_path / "data", archive) == 1

    page = (tmp_path / "item" / item_id / "index.html").read_text(encoding="utf-8")
    assert f"Radar ID</dt>\n    <dd>{item_id}</dd>" in page
    assert "Title &lt;tag&gt; &amp; &quot;quote&quot;" in page
    assert "Source</dt>\n    <dd>Example Newsroom</dd>" in page
    assert "Published</dt>\n    <dd>2026-09-07T10:00:00Z</dd>" in page
    assert "Summary &lt;unsafe&gt; &amp; &#x27;quote&#x27;" in page
    assert 'href="https://example.com/news/123?x=1&amp;y=2"' in page
    assert (tmp_path / "data" / "items" / f"{item_id}.json").exists()


def test_html_adapter_is_removed_when_its_archive_record_exceeds_retention(tmp_path):
    fresh_id = make_item_id("official_ai", "Example Newsroom", "Fresh HTML", "https://example.com/fresh-html")
    expired_id = make_item_id("official_ai", "Example Newsroom", "Expired HTML", "https://example.com/expired-html")
    archive = {
        fresh_id: archive_item(fresh_id, last_seen_at=NOW - timedelta(days=20), url="https://example.com/fresh-html"),
        expired_id: archive_item(expired_id, last_seen_at=NOW - timedelta(days=22), url="https://example.com/expired-html"),
    }

    output_dir = tmp_path / "data"
    write_item_html_adapters(output_dir, archive)
    retained = prune_archive_records(archive, NOW, archive_days=21)
    write_item_html_adapters(output_dir, retained)

    assert (tmp_path / "item" / fresh_id / "index.html").exists()
    assert not (tmp_path / "item" / expired_id / "index.html").exists()
