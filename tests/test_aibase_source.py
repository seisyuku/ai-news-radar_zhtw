import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from scripts.aibase_source import AIBASE_INDEXES, aibase_article_key, fetch_aibase_payload
from scripts.update_news import fetch_aibase_with_status

NOW = datetime(2026, 9, 8, tzinfo=timezone.utc)


def page(rows):
    # Nuxt serializes nested data as references into one JSON table.
    table = []
    def ref(value):
        index = len(table)
        table.append(None)
        table[index] = ({k: ref(v) for k, v in value.items()} if isinstance(value, dict)
                        else [ref(v) for v in value] if isinstance(value, list) else value)
        return index
    ref({"getAINewsList": {"code": 200, "data": {"list": rows}}})
    return '<script id="__NUXT_DATA__" type="application/json">' + json.dumps(table) + '</script>'


def row(oid=1, title="原生繁中標題", description="來源摘要", createTime="2026-09-08 08:00:00"):
    return dict(oid=oid, title=title, description=description, createTime=createTime)


class Session:
    def __init__(self, tw, en):
        self.responses = dict(zip(AIBASE_INDEXES.values(), (tw, en)))
    def get(self, url, **kwargs):
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(text=value, raise_for_status=lambda: None)


def test_native_fields_and_link_win_and_summary_reaches_raw_item():
    items, status = fetch_aibase_with_status(Session(page([row()]), page([row(title="English")])), NOW)
    assert len(items) == 1
    assert items[0].title == "原生繁中標題"
    assert items[0].url == "https://news.aibase.com/tw/news/1"
    assert items[0].meta["summary"] == "來源摘要"
    assert items[0].published_at.astimezone(timezone.utc) == NOW
    assert status["language_mode"] == "traditional_chinese"


def test_missing_fields_and_english_only_article_are_supplemented():
    items, status = fetch_aibase_payload(Session(
        page([row(description="", createTime="")]),
        page([row(title="English", description="English summary"), row(2, "Only English")]),
    ), NOW)
    assert len(items) == 2
    assert items[0]["title"] == "原生繁中標題"
    assert items[0]["meta"]["summary"] == "English summary"
    assert items[0]["meta"]["field_languages"]["summary"] == "en"
    assert items[1]["url"] == "https://news.aibase.com/news/2"
    assert status["english_supplemented_count"] == 2


@pytest.mark.parametrize("failed", ["tw", "en"])
def test_one_failed_language_keeps_other_language(failed):
    responses = {"tw": page([row()]), "en": page([row(title="English")])}
    responses[failed] = RuntimeError("offline")
    items, status = fetch_aibase_payload(Session(**responses), NOW)
    assert len(items) == 1
    assert status["degraded"]
    assert status["language_status"][failed]["status"] == "failed"
    assert status["language_mode"] == ("english_fallback" if failed == "tw" else "traditional_chinese")


def test_landing_page_and_empty_payload_are_failures():
    with pytest.raises(ValueError, match="both language indexes failed"):
        fetch_aibase_payload(Session("<html>Newsletter</html>", page([])), NOW)


def test_missing_dates_are_not_replaced_with_now():
    items, status = fetch_aibase_payload(Session(page([row(createTime="")]), page([row(createTime="just now")])), NOW)
    assert items[0]["published_at"] is None
    assert status["undated_count"] == 1


def test_article_key_matches_old_and_current_language_routes_only():
    urls = ["https://www.aibase.com/news/16460", "https://news.aibase.com/tw/news/16460",
            "https://news.aibase.com/news/16460?utm_source=test"]
    assert [aibase_article_key(url) for url in urls] == ["16460"] * 3
    assert aibase_article_key("https://example.com/news/16460") is None
