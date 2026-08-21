from datetime import datetime, timedelta, timezone

from scripts.update_news import build_llm_radar_payload


NOW = datetime(2026, 8, 22, 0, 0, tzinfo=timezone.utc)


def model_item(*, site_id, model_id, hours_ago, title, score=0.8):
    occurred = NOW - timedelta(hours=hours_ago)
    return {
        "id": f"{site_id}-{model_id}",
        "site_id": site_id,
        "site_name": "官方更新" if site_id == "official_ai" else "精選媒體",
        "source": "Test source",
        "title": title,
        "title_zh": title,
        "summary_zh": "測試用模型釋出內容。",
        "url": f"https://example.com/{site_id}/{model_id}",
        "model_id": model_id,
        "model_name": model_id,
        "published_at": occurred.isoformat().replace("+00:00", "Z"),
        "first_seen_at": occurred.isoformat().replace("+00:00", "Z"),
        "business_events": ["model_release"],
        "ai_score": score,
    }


def test_llm_radar_keeps_recent_model_release_and_exact_price_change():
    payload = build_llm_radar_payload(
        [
            model_item(
                site_id="official_ai",
                model_id="qwen3.9",
                hours_ago=1,
                title="Qwen 發布 Qwen3.9",
            ),
            model_item(
                site_id="curated_media",
                model_id="qwen3.9",
                hours_ago=2,
                title="媒體報導 Qwen3.9 發布",
            ),
            model_item(
                site_id="official_ai",
                model_id="old-model",
                hours_ago=25,
                title="Old Model 發布",
            ),
        ],
        {
            "signals": [
                {
                    "id": "price-1",
                    "category": "price",
                    "verification_status": "reported",
                    "title": "Qwen Qwen3.9：輸入價格異動",
                    "old_value": 1.0,
                    "new_value": 0.5,
                    "unit": "USD / 1M tokens",
                    "detected_at": "2026-08-21T23:30:00Z",
                    "effective_at": "2026-08-21T23:00:00Z",
                    "source_name": "LLM Price Tracker",
                    "source_url": "https://example.com/prices",
                    "evidence_url": "https://example.com/prices",
                }
            ]
        },
        NOW,
    )

    assert payload["window_hours"] == 24
    assert payload["total_events"] == 2
    model, price = payload["events"]
    assert model["kind"] == "model_release"
    assert model["verification_status"] == "official"
    assert model["verification_label"] == "官方公告"
    assert price["kind"] == "price_change"
    assert (price["old_value"], price["new_value"], price["unit"]) == (1.0, 0.5, "USD / 1M tokens")


def test_llm_radar_is_empty_without_a_recent_release_or_price_event():
    payload = build_llm_radar_payload(
        [model_item(site_id="official_ai", model_id="old-model", hours_ago=30, title="Old Model 發布")],
        {"signals": []},
        NOW,
    )

    assert payload["total_events"] == 0
    assert payload["events"] == []
