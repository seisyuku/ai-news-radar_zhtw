from copy import deepcopy
from datetime import datetime, timezone

from scripts.market_sensors import (
    _kept_signals,
    build_free_tier_snapshot,
    build_price_snapshot,
    diff_free_tier_snapshots,
    diff_price_snapshots,
    is_usage_policy_candidate,
    parse_canary_atom,
)


NOW = "2026-08-21T08:00:00Z"


def price_payload(**overrides):
    model = {
        "provider": "Example AI",
        "model_id": "example-1",
        "model_name": "Example 1",
        "input_per_1m_usd": 1.5,
        "output_per_1m_usd": 6.0,
        "batch_input_per_1m_usd": None,
        "batch_output_per_1m_usd": None,
        "cache_read_per_1m_usd": None,
        "cache_write_per_1m_usd": None,
    }
    model.update(overrides)
    return {"last_updated": "2026-08-21", "models": [model]}


def free_provider(**overrides):
    value = {
        "id": "example",
        "name": "Example AI",
        "category": "provider-free-tier",
        "models": ["example-1"],
        "limits": {"requests_per_minute": 20, "requests_per_day": 100},
        "availability": {"status": "active", "accepting_new_users": True},
        "source_checked_at": "2026-08-21",
        "official_sources": [{"title": "Limits", "url": "https://example.com/limits"}],
    }
    value.update(overrides)
    return value


def test_price_bootstrap_does_not_emit_existing_catalog():
    current = build_price_snapshot(price_payload())
    assert diff_price_snapshots({}, current, NOW) == []


def test_price_numeric_change_emits_exact_old_and_new_values():
    previous = build_price_snapshot(price_payload())
    current = build_price_snapshot(price_payload(input_per_1m_usd=1.0))
    signals = diff_price_snapshots(previous, current, NOW)
    assert len(signals) == 1
    assert signals[0]["event_type"] == "API_PRICE_CHANGE"
    assert signals[0]["old_value"] == 1.5
    assert signals[0]["new_value"] == 1.0
    assert signals[0]["verification_status"] == "reported"


def test_price_metadata_only_change_does_not_emit_signal():
    previous_payload = price_payload()
    current_payload = deepcopy(previous_payload)
    current_payload["models"][0]["notes"] = "formatting only"
    assert diff_price_snapshots(
        build_price_snapshot(previous_payload), build_price_snapshot(current_payload), NOW
    ) == []


def test_price_model_add_and_remove_are_distinct_events():
    previous = build_price_snapshot(price_payload())
    added_payload = price_payload()
    added_payload["models"].append(
        {**added_payload["models"][0], "model_id": "example-2", "model_name": "Example 2"}
    )
    added = build_price_snapshot(added_payload)
    assert [signal["event_type"] for signal in diff_price_snapshots(previous, added, NOW)] == [
        "MODEL_PRICE_ADDED"
    ]
    assert [signal["event_type"] for signal in diff_price_snapshots(added, previous, NOW)] == [
        "MODEL_PRICE_REMOVED"
    ]


def test_free_tier_rate_limit_change_links_official_evidence():
    previous = build_free_tier_snapshot([free_provider()])
    changed = free_provider(limits={"requests_per_minute": 30, "requests_per_day": 100})
    signals = diff_free_tier_snapshots(previous, build_free_tier_snapshot([changed]), NOW)
    assert len(signals) == 1
    assert signals[0]["event_type"] == "RATE_LIMIT_CHANGE"
    assert signals[0]["old_value"] == 20
    assert signals[0]["new_value"] == 30
    assert signals[0]["evidence_url"] == "https://example.com/limits"


def test_free_model_add_and_remove_are_detected_without_summary_noise():
    previous = build_free_tier_snapshot([free_provider()])
    changed = free_provider(models=["example-1", "example-2"])
    current = build_free_tier_snapshot([changed])
    assert [signal["event_type"] for signal in diff_free_tier_snapshots(previous, current, NOW)] == [
        "FREE_MODEL_ADDED"
    ]
    assert [signal["event_type"] for signal in diff_free_tier_snapshots(current, previous, NOW)] == [
        "FREE_MODEL_REMOVED"
    ]


def test_free_tier_provider_add_and_remove_are_candidates_with_provenance():
    previous = build_free_tier_snapshot([free_provider()])
    second = free_provider(id="second", name="Second AI")
    current = build_free_tier_snapshot([free_provider(), second])
    added = diff_free_tier_snapshots(previous, current, NOW)
    removed = diff_free_tier_snapshots(current, previous, NOW)
    assert [(signal["field"], signal["new_value"]) for signal in added] == [("provider", "listed")]
    assert [(signal["field"], signal["new_value"]) for signal in removed] == [("provider", "absent")]
    assert removed[0]["verification_status"] == "candidate"


def test_canary_requires_strong_policy_language():
    assert is_usage_policy_candidate({"title": "support new weekly quota field", "content": ""})
    assert is_usage_policy_candidate({"title": "double limits for one week", "content": ""})
    assert not is_usage_policy_candidate({"title": "refresh usage data after account switch", "content": ""})
    assert not is_usage_policy_candidate({"title": "change tray icon and dependency", "content": ""})


def test_canary_atom_parser_preserves_commit_identity_and_evidence_link():
    xml = b"""<?xml version='1.0'?>
    <feed xmlns='http://www.w3.org/2005/Atom'>
      <entry><id>commit-1</id><title>support weekly quota</title>
      <updated>2026-08-21T07:00:00Z</updated>
      <link href='https://github.com/example/commit/1'/>
      <content type='html'>&lt;p&gt;model-specific weekly limit&lt;/p&gt;</content></entry>
    </feed>"""
    entries = parse_canary_atom(xml)
    assert entries == [{
        "id": "commit-1",
        "title": "support weekly quota",
        "url": "https://github.com/example/commit/1",
        "updated": "2026-08-21T07:00:00Z",
        "content": "model-specific weekly limit",
    }]


def test_public_market_signals_use_the_same_24_hour_window_for_every_urgency():
    now = datetime(2026, 8, 26, 12, tzinfo=timezone.utc)
    payload = {
        "signals": [
            {"id": "at-boundary", "urgency": "standard", "detected_at": "2026-08-25T12:00:00Z"},
            {"id": "expired-standard", "urgency": "standard", "detected_at": "2026-08-25T11:59:59Z"},
            {"id": "expired-breaking", "urgency": "breaking", "detected_at": "2026-08-25T11:59:59Z"},
        ]
    }

    kept = _kept_signals(payload, now)

    assert [signal["id"] for signal in kept] == ["at-boundary"]
