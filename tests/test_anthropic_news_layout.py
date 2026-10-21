"""Newsroom dates must stay paired with their own article across layouts."""

from datetime import datetime, timezone

import pytest

from scripts.update_news import parse_anthropic_news_items


NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)


def test_featured_card_and_table_row_dates_are_paired_and_deduplicated():
    html = """
    <article><header><time>Oct 18, 2026</time></header>
      <a href="/news/first"><h3>First announcement</h3></a></article>
    <div class="TableView-module-scss-module__newHash__summary">
      <div><a href="/news/first"><h3>First announcement</h3></a></div>
      <div><time>Oct 18, 2026</time></div></div>
    <div class="TableView-module-scss-module__newHash__summary">
      <div><a href="/news/second"><h3>Second announcement</h3></a></div>
      <a href="/news/announcements">Announcements</a>
      <div><time>Oct 15, 2026</time></div></div>
    """
    items = parse_anthropic_news_items(html, NOW, require_valid=True)
    assert [(item.url.rsplit("/", 1)[-1], item.published_at.day) for item in items] == [
        ("first", 18), ("second", 15)]
    assert all(item.source == "Anthropic News" for item in items)


def test_incomplete_duplicate_does_not_hide_later_dated_article():
    html = """
    <a href="/news/first"><h3>First announcement</h3></a>
    <article><time>Oct 18, 2026</time>
      <a href="/news/first"><h3>First announcement</h3></a></article>
    """
    items = parse_anthropic_news_items(html, NOW, require_valid=True)
    assert len(items) == 1 and items[0].published_at.day == 18


@pytest.mark.parametrize("html", [
    '<main><time>Oct 18, 2026</time><a href="/news/missing"><h3>No date</h3></a></main>',
    '<article><a href="/news/missing"><h3>No date</h3></a></article>'
    '<article><time>Oct 18, 2026</time><a href="/news/other">Other</a></article>',
    '<article><time>Oct 18, 2026</time><time>Oct 19, 2026</time>'
    '<a href="/news/ambiguous"><h3>Two dates</h3></a></article>',
    '<article><time>Oct 18, 2026</time><a href="/news/first"><h3>First</h3></a>'
    '<a href="/news/second"><h3>Second</h3></a></article>',
    '<article><time>not a date</time><a href="/news/invalid"><h3>Invalid</h3></a></article>',
])
def test_missing_or_ambiguous_article_dates_remain_source_failures(html):
    with pytest.raises(ValueError, match="invalid_page_fields"):
        parse_anthropic_news_items(html, NOW, require_valid=True)


def test_old_dated_card_is_healthy_zero_and_legacy_layout_still_works():
    old = '<article><time>Jan 1, 2021</time><a href="/news/old"><h3>Old</h3></a></article>'
    assert parse_anthropic_news_items(old, NOW, require_valid=True) == []
    legacy = '<a href="/news/legacy"><h2>Legacy</h2><time datetime="2026-10-20"></time></a>'
    items = parse_anthropic_news_items(legacy, NOW, require_valid=True)
    assert len(items) == 1 and items[0].published_at.day == 20
