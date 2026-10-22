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
def test_bad_or_shrunken_models_still_fail_offline_safety_guard(models):
    old_free = sensors.build_free_tier_snapshot([provider([f"model-{i}" for i in range(10)])])
    previous = {"free_tier": old_free}
    original = deepcopy(previous)
    with pytest.raises(ValueError, match="free_tier_"):
        current = sensors.build_free_tier_snapshot([provider(models)])
        sensors.validate_free_tier_retention(old_free, current)
    assert previous == original


def test_offline_normal_small_model_change_still_emits_candidate_difference():
    models = [f"model-{i}" for i in range(10)]
    previous = {"free_tier": sensors.build_free_tier_snapshot([provider(models)])}
    current = sensors.build_free_tier_snapshot([provider(models[1:])])
    sensors.validate_free_tier_retention(previous["free_tier"], current)
    signals = sensors.diff_free_tier_snapshots(previous["free_tier"], current, NOW.isoformat())
    assert [s["event_type"] for s in signals] == ["FREE_MODEL_REMOVED"]
