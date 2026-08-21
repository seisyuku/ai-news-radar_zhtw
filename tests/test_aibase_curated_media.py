from __future__ import annotations

from scripts.ai_relevance import score_ai_relevance
from scripts.update_news import normalize_reader_source_identity, source_tier_for_site


def test_legacy_aibase_records_render_as_curated_media_with_canonical_name():
    normalized = normalize_reader_source_identity(
        {
            "site_id": "aibase",
            "site_name": "AIbase",
            "source": "AIbase",
            "title": "Qwen 發布新模型",
        }
    )

    assert normalized["site_id"] == "curated_media"
    assert normalized["site_name"] == "精選媒體"
    assert normalized["source"] == "AIBASE"
    assert source_tier_for_site("aibase")["source_tier"] == "ai_media"


def test_aibase_uses_curated_media_scoring_instead_of_default_source_floor():
    result = score_ai_relevance(
        {
            "site_id": "curated_media",
            "site_name": "精選媒體",
            "source": "AIBASE",
            "title": "阿里釋出 Qwen-UI-Agent，開放 GUI 智慧體功能",
            "url": "https://www.aibase.com/zh/news/example",
        }
    )

    assert result["is_ai_related"] is True
    assert result["reason"] == "curated_media_source_filter"
    assert result["score"] < 1.0
