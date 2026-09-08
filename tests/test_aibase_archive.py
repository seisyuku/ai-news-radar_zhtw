"""Archive integration contract for AIBASE's bilingual source records."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from scripts.update_news import (
    RawItem,
    event_time,
    iso,
    make_item_id,
    merge_raw_items_into_archive,
    prune_archive_records,
    write_item_resolvers,
)


NOW = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
PUBLISHED = NOW - timedelta(hours=2)


def aibase_raw(language="en", *, published_at=PUBLISHED, summary=None):
    meta = {
        "aibase_article_id": "16460",
        "content_language": language,
        "field_languages": {"title": language, "url": language},
    }
    if summary is not None:
        meta["summary"] = summary
        meta["field_languages"]["summary"] = language
    return RawItem(
        site_id="curated_media",
        site_name="精選媒體",
        source="AIBASE",
        title="新模型正式發布" if language == "tw" else "New model released",
        url=f"https://news.aibase.com/{'tw/' if language == 'tw' else ''}news/16460",
        published_at=published_at,
        meta=meta,
    )


def legacy_record(*, site_id="aibase", language="en", age_days=1):
    raw = aibase_raw(language)
    url = f"https://www.aibase.com/{'tw/' if language == 'tw' else ''}news/16460"
    item_id = make_item_id(site_id, "AIbase", raw.title, url)
    return item_id, {
        "id": item_id,
        "site_id": site_id,
        "site_name": "AIbase",
        "source": "AIbase",
        "title": raw.title,
        "url": url,
        "published_at": iso(PUBLISHED),
        "first_seen_at": iso(NOW - timedelta(days=age_days)),
        "last_seen_at": iso(NOW - timedelta(days=age_days)),
    }


@pytest.mark.parametrize("site_id", ["aibase", "curated_media"])
def test_legacy_english_article_keeps_public_id_when_traditional_version_arrives(site_id):
    old_id, old = legacy_record(site_id=site_id)
    archive = {old_id: old}

    seen = merge_raw_items_into_archive(archive, [aibase_raw("tw")], NOW)

    assert seen == {old_id}
    assert set(archive) == {old_id}
    assert archive[old_id]["id"] == old_id
    assert archive[old_id]["title"] == "新模型正式發布"
    assert archive[old_id]["url"].endswith("/tw/news/16460")
    assert archive[old_id]["first_seen_at"] == iso(NOW - timedelta(days=1))


def test_english_then_traditional_refresh_updates_same_record_and_resolver(tmp_path):
    archive = {}
    first_seen = merge_raw_items_into_archive(archive, [aibase_raw()], NOW)
    item_id = next(iter(first_seen))
    write_item_resolvers(tmp_path, archive)

    seen = merge_raw_items_into_archive(
        archive, [aibase_raw("tw", summary="繁中摘要")], NOW + timedelta(hours=1)
    )
    write_item_resolvers(tmp_path, archive)

    assert seen == first_seen
    assert len(archive) == 1
    resolver = json.loads((tmp_path / "items" / f"{item_id}.json").read_text())
    assert resolver["id"] == item_id
    assert resolver["title"] == "新模型正式發布"
    assert resolver["summary"] == "繁中摘要"


def test_english_fallback_does_not_downgrade_existing_traditional_fields():
    archive = {}
    seen = merge_raw_items_into_archive(archive, [aibase_raw("tw", summary="繁中摘要")], NOW)
    item_id = next(iter(seen))
    later = NOW + timedelta(hours=1)

    assert merge_raw_items_into_archive(
        archive, [aibase_raw("en", summary="English summary")], later
    ) == seen
    assert archive[item_id]["title"] == "新模型正式發布"
    assert archive[item_id]["url"].endswith("/tw/news/16460")
    assert archive[item_id]["summary"] == "繁中摘要"
    assert archive[item_id]["last_seen_at"] == iso(later)


def test_english_can_fill_missing_summary_without_replacing_traditional_title():
    archive = {}
    seen = merge_raw_items_into_archive(archive, [aibase_raw("tw")], NOW)
    item_id = next(iter(seen))

    merge_raw_items_into_archive(archive, [aibase_raw("en", summary="English summary")], NOW)

    assert archive[item_id]["title"] == "新模型正式發布"
    assert archive[item_id]["summary"] == "English summary"


def test_field_language_allows_later_traditional_summary_to_replace_english_fill():
    mixed = aibase_raw("tw", summary="English fallback summary")
    mixed.meta["field_languages"]["summary"] = "en"
    archive = {}
    seen = merge_raw_items_into_archive(archive, [mixed], NOW)
    item_id = next(iter(seen))

    merge_raw_items_into_archive(archive, [aibase_raw("tw", summary="原生繁中摘要")], NOW)
    merge_raw_items_into_archive(archive, [mixed], NOW + timedelta(hours=1))

    assert archive[item_id]["summary"] == "原生繁中摘要"


@pytest.mark.parametrize("site_id", ["aibase", "curated_media"])
def test_undated_aibase_is_archived_without_fetch_time_becoming_event_time(site_id):
    raw = aibase_raw(published_at=None)
    raw.site_id = site_id
    archive = {}
    seen = merge_raw_items_into_archive(archive, [raw], NOW)

    assert len(seen) == 1
    record = archive[next(iter(seen))]
    assert not record.get("published_at")
    assert record["first_seen_at"] == iso(NOW)
    assert event_time(record) is None


def test_known_publish_time_survives_undated_fallback():
    archive = {}
    seen = merge_raw_items_into_archive(archive, [aibase_raw("tw")], NOW)
    merge_raw_items_into_archive(archive, [aibase_raw(published_at=None)], NOW)
    assert event_time(archive[next(iter(seen))]) == PUBLISHED


def test_legacy_duplicate_ids_keep_resolvers_but_only_one_visible_record(tmp_path):
    english_id, english = legacy_record(age_days=20)
    traditional_id, traditional = legacy_record(language="tw", age_days=19)
    original_last_seen = {english_id: english["last_seen_at"], traditional_id: traditional["last_seen_at"]}
    archive = {english_id: english, traditional_id: traditional}

    seen = merge_raw_items_into_archive(archive, [aibase_raw("tw")], NOW)

    assert len(seen) == 1
    canonical_id = next(iter(seen))
    alias_id = next(item_id for item_id in archive if item_id != canonical_id)
    assert set(archive) == {english_id, traditional_id}
    assert archive[alias_id]["duplicate_of"] == canonical_id
    assert event_time(archive[alias_id]) is None
    assert event_time(archive[canonical_id]) == PUBLISHED
    assert archive[alias_id]["last_seen_at"] == original_last_seen[alias_id]
    assert write_item_resolvers(tmp_path, archive) == 2
    assert (tmp_path / "items" / f"{alias_id}.json").exists()

    retained = prune_archive_records(archive, NOW + timedelta(days=3), archive_days=21)
    write_item_resolvers(tmp_path, retained)
    assert canonical_id in retained
    assert alias_id not in retained
    assert not (tmp_path / "items" / f"{alias_id}.json").exists()


def test_existing_legacy_traditional_duplicate_is_used_during_english_only_refresh():
    english_id, english = legacy_record(age_days=2)
    traditional_id, traditional = legacy_record(language="tw", age_days=1)
    traditional["summary"] = "已存檔的繁中摘要"
    archive = {english_id: english, traditional_id: traditional}

    seen = merge_raw_items_into_archive(archive, [aibase_raw("en", summary="English summary")], NOW)

    assert seen == {english_id}
    assert archive[english_id]["title"] == "新模型正式發布"
    assert archive[english_id]["url"].endswith("/tw/news/16460")
    assert archive[english_id]["summary"] == "已存檔的繁中摘要"
    assert archive[traditional_id]["duplicate_of"] == english_id

    assert merge_raw_items_into_archive(archive, [aibase_raw("tw")], NOW + timedelta(hours=1)) == seen
    assert archive[traditional_id]["duplicate_of"] == english_id


def test_non_aibase_keeps_existing_id_and_fetch_time_policy():
    raw = RawItem("official_ai", "官方更新", "Example", "Release", "https://example.com/news/16460", None, {})
    archive = {}

    seen = merge_raw_items_into_archive(archive, [raw], NOW)

    expected_id = make_item_id(raw.site_id, raw.source, raw.title, raw.url)
    assert seen == {expected_id}
    assert event_time(archive[expected_id]) == NOW
