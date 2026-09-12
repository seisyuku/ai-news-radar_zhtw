from __future__ import annotations

from datetime import datetime, timedelta, timezone

from scripts.update_news import (
    KR36_AI_READER_MAX_ITEMS,
    add_source_tier_fields,
    apply_reader_source_limits,
    dedupe_same_publisher_items,
    is_within_reader_window,
    source_tier_for_record,
    source_tier_for_site,
)


NOW = datetime(2026, 9, 12, 8, 30, tzinfo=timezone.utc)


def item(
    idx: int,
    *,
    site_id: str,
    source: str,
    title: str,
    hours_from_now: int = 0,
) -> dict:
    return {
        "id": str(idx),
        "site_id": site_id,
        "site_name": site_id,
        "source": source,
        "title": title,
        "url": f"https://example.com/{idx}",
        "published_at": (NOW + timedelta(hours=hours_from_now)).isoformat().replace("+00:00", "Z"),
    }


def test_publisher_level_tiers_split_shared_fetch_groups() -> None:
    decoder = source_tier_for_record(
        {"site_id": "curated_media", "source": "The Decoder AI News"}
    )
    ithome = source_tier_for_record({"site_id": "tw_media", "source": "iThome"})
    bnext = source_tier_for_record(
        {"site_id": "tw_media", "source": "數位時代 (Google News)"}
    )

    assert decoder == {
        "source_tier": "ai_vertical",
        "source_tier_label": "AI垂直專業媒體",
        "source_tier_rank": 1,
    }
    assert ithome == {
        "source_tier": "professional_media",
        "source_tier_label": "專業科技媒體",
        "source_tier_rank": 1,
    }
    assert bnext == {
        "source_tier": "advanced",
        "source_tier_label": "台灣媒體觀察源",
        "source_tier_rank": 4,
    }


def test_runtimewire_moves_one_level_above_watchlist() -> None:
    assert source_tier_for_site("runtimewire") == {
        "source_tier": "advanced",
        "source_tier_label": "次級AI媒體",
        "source_tier_rank": 4,
    }
    assert source_tier_for_site("llm_rumors")["source_tier"] == "watchlist"


def test_aibase_keeps_existing_curated_media_scoring() -> None:
    enriched = add_source_tier_fields(
        {"site_id": "curated_media", "source": "AIBASE"}
    )
    assert enriched["source_tier"] == "ai_media"
    assert enriched["source_tier_rank"] == 2


def test_known_google_news_suffix_variants_dedupe_within_publisher() -> None:
    rows = [
        item(
            1,
            site_id="kr36_ai",
            source="36Kr",
            title="即夢AI測評：大模型使用體驗 | 36氪AI測評 - 36 Kr",
            hours_from_now=-2,
        ),
        item(
            2,
            site_id="kr36_ai",
            source="36Kr",
            title="即夢AI測評：大模型使用體驗 | 36氪AI測評 - m-ai.36kr.com",
            hours_from_now=-1,
        ),
        item(
            3,
            site_id="tw_media",
            source="數位時代 (Google News)",
            title="ChatGPT 圖像提示詞完整教學 - bnext.com.tw",
            hours_from_now=-2,
        ),
        item(
            4,
            site_id="tw_media",
            source="數位時代 (Google News)",
            title="ChatGPT 圖像提示詞完整教學 - 數位時代",
            hours_from_now=-1,
        ),
        item(
            5,
            site_id="tw_media",
            source="TechNews 科技新報",
            title="ChatGPT 圖像提示詞完整教學 - 數位時代",
            hours_from_now=-1,
        ),
    ]

    deduped = dedupe_same_publisher_items(rows)

    assert {row["id"] for row in deduped} == {"2", "4", "5"}


def test_36kr_reader_output_is_capped_after_multiple_fetch_cycles() -> None:
    rows = [
        item(idx, site_id="kr36_ai", source="36Kr", title=f"AI 新聞 {idx}", hours_from_now=-idx)
        for idx in range(8)
    ]
    rows.append(item(20, site_id="official_ai", source="OpenAI News", title="Official update"))

    limited = apply_reader_source_limits(rows)

    assert sum(row["site_id"] == "kr36_ai" for row in limited) == KR36_AI_READER_MAX_ITEMS == 5
    assert any(row["site_id"] == "official_ai" for row in limited)


def test_reader_window_rejects_far_future_dates_but_allows_clock_skew() -> None:
    within = item(1, site_id="official_ai", source="OpenAI News", title="Within", hours_from_now=6)
    future = item(2, site_id="official_ai", source="OpenAI News", title="Future", hours_from_now=7)
    old = item(3, site_id="official_ai", source="OpenAI News", title="Old", hours_from_now=-25)

    assert is_within_reader_window(within, NOW, 24)
    assert not is_within_reader_window(future, NOW, 24)
    assert not is_within_reader_window(old, NOW, 24)
