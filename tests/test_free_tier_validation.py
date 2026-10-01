"""Malformed catalogs must preserve the previous baseline and avoid false alerts."""
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from scripts import market_sensors as sensors


NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def provider(models):
    return {"id": "example", "name": "Example", "models": models}


@pytest.mark.parametrize("payload", [
    {"providers": [provider(["model-1"])]}, [None],
    [{"name": "missing identity"}],
    [provider("model-1")], [provider([123])],
    [provider(["Retired — the model catalog is gone"])],
    [provider(["model-1"]), provider(["model-2"])],
])
def test_invalid_free_catalog_is_rejected_without_echoing_payload(payload):
    with pytest.raises(ValueError, match="free_tier_"):
        sensors.build_free_tier_snapshot(payload)


def test_free_model_names_allow_real_ids_spaces_and_deduplicate_without_mutation():
    payload = [provider(["Qwen 3.8 27B", "meta-llama/Llama-4 (free)", "Retired-v1", "Qwen 3.8 27B"])]
    original = deepcopy(payload)
    snapshot = sensors.build_free_tier_snapshot(payload)
    assert snapshot["providers"]["example"]["models"] == [
        "Qwen 3.8 27B", "Retired-v1", "meta-llama/Llama-4 (free)"]
    assert payload == original


@pytest.mark.parametrize("models", [
    "model-1", ["Retired — the model catalog is gone"], ["model-0"], []])
def test_bad_or_shrunken_models_keep_state_and_do_not_emit_false_model_changes(monkeypatch, models):
    old_free = sensors.build_free_tier_snapshot([provider([f"model-{i}" for i in range(10)])])
    previous = {"free_tier": old_free}
    original = deepcopy(previous)
    monkeypatch.setattr(sensors, "_fetch_json", lambda session, url: [provider(models)] if url == sensors.FREE_TIER_URL else {"models": []})
    monkeypatch.setattr(sensors, "_fetch_canary", lambda *_: [])
    payload, state, statuses = sensors.run_market_sensors(object(), NOW, previous, {})
    assert state["free_tier"] == old_free and previous == original
    assert not [s for s in payload["signals"] if s["category"] == "free_tier"]
    status = next(s for s in statuses if s["site_id"] == "market_free_tier")
    assert status["ok"] is False and status["signal_count"] == 0


def test_normal_small_model_change_still_emits_candidate_difference(monkeypatch):
    models = [f"model-{i}" for i in range(10)]
    previous = {"free_tier": sensors.build_free_tier_snapshot([provider(models)])}
    monkeypatch.setattr(sensors, "_fetch_json", lambda session, url: [provider(models[1:])] if url == sensors.FREE_TIER_URL else {"models": []})
    monkeypatch.setattr(sensors, "_fetch_canary", lambda *_: [])
    payload, state, statuses = sensors.run_market_sensors(object(), NOW, previous, {})
    assert state["free_tier"]["providers"]["example"]["models"] == models[1:]
    assert [s["event_type"] for s in payload["signals"]] == ["FREE_MODEL_REMOVED"]
    assert next(s for s in statuses if s["site_id"] == "market_free_tier")["ok"] is True
