"""A group peer must not erase another subsource's health history."""

from datetime import datetime, timedelta, timezone

import pytest

from scripts.update_news import apply_source_health_history, report_persistent_source_failures


NOW = datetime(2026, 9, 26, tzinfo=timezone.utc)


def group(children, *, site_id="official_ai", skipped=False):
    return {
        "site_id": site_id,
        "site_name": "Official AI Updates",
        "ok": any(ok for _, ok in children) if children else True,
        "skipped": skipped,
        "subsources": [
            {"source_id": source_id, "ok": ok, "item_count": 0,
             "error": None if ok else "fetch_failed"}
            for source_id, ok in children
        ],
    }


def advance(previous, current, hours=0, threshold=3):
    now = NOW + timedelta(hours=hours)
    alerts = apply_source_health_history(
        [current], {"sites": [previous]} if previous else {}, now, threshold=threshold
    )
    return current, alerts


def children(status):
    return {row["source_id"]: row for row in status["subsources"]}


def test_interleaved_failures_and_one_recovery_leave_peer_streak_intact():
    first, alerts = advance(None, group([("a", False), ("b", True)]))
    assert alerts == []
    assert children(first)["a"]["consecutive_failures"] == 1
    assert children(first)["b"]["last_success_at"] == "2026-09-26T00:00:00Z"

    second, alerts = advance(first, group([("a", False), ("b", False)]), 1)
    assert alerts == []
    assert children(second)["a"]["consecutive_failures"] == 2
    assert children(second)["b"]["consecutive_failures"] == 1

    third, alerts = advance(second, group([("a", True), ("b", False)]), 2)
    assert alerts == []
    assert children(third)["a"]["consecutive_failures"] == 0
    assert children(third)["a"]["last_success_at"] == "2026-09-26T02:00:00Z"
    assert children(third)["b"]["consecutive_failures"] == 2
    assert children(third)["b"]["last_success_at"] == "2026-09-26T00:00:00Z"

    fourth, alerts = advance(third, group([("a", True), ("b", False)]), 3)
    assert children(fourth)["b"]["consecutive_failures"] == 3
    assert children(fourth)["b"]["first_failure_at"] == "2026-09-26T01:00:00Z"
    assert children(fourth)["b"]["persistent_failure"] is True
    assert [(row["site_id"], row["source_id"]) for row in alerts] == [("official_ai", "b")]


def test_all_failed_reports_children_once_at_threshold_not_group_duplicate():
    first, _ = advance(None, group([("a", False), ("b", False)]), threshold=2)
    second, alerts = advance(first, group([("a", False), ("b", False)]), 1, threshold=2)
    assert second["persistent_failure"] is True
    assert {(row["site_id"], row["source_id"]) for row in alerts} == {
        ("official_ai", "a"), ("official_ai", "b")
    }


def test_skip_preserves_child_history_without_repeating_alerts():
    first, _ = advance(None, group([("a", False), ("b", True)]), threshold=2)
    skipped, alerts = advance(first, group([], skipped=True), 1, threshold=2)
    assert alerts == []
    assert children(skipped)["a"]["consecutive_failures"] == 1
    assert children(skipped)["a"]["last_failure_at"] == "2026-09-26T00:00:00Z"
    assert children(skipped)["a"]["last_attempt_ok"] is False
    assert children(skipped)["a"]["skipped"] is True
    assert children(skipped)["b"]["last_success_at"] == "2026-09-26T00:00:00Z"
    failed, alerts = advance(skipped, group([("a", False), ("b", True)]), 2, threshold=2)
    assert children(failed)["a"]["consecutive_failures"] == 2
    assert [(row["site_id"], row["source_id"]) for row in alerts] == [("official_ai", "a")]


def test_persistent_child_skip_preserves_streak_without_new_alert():
    first, _ = advance(None, group([("a", False)]), threshold=2)
    second, alerts = advance(first, group([("a", False)]), 1, threshold=2)
    assert [(row["site_id"], row["source_id"]) for row in alerts] == [("official_ai", "a")]
    skipped, alerts = advance(second, group([], skipped=True), 2, threshold=2)
    assert alerts == []
    assert children(skipped)["a"]["persistent_failure"] is True
    assert children(skipped)["a"]["consecutive_failures"] == 2
    assert children(skipped)["a"]["last_failure_at"] == "2026-09-26T01:00:00Z"


def test_legacy_skipped_child_keeps_retained_failure_count():
    previous = group([("a", True)], skipped=True)
    previous["subsources"][0].update(
        skipped=True, consecutive_failures=2,
        first_failure_at="2026-09-25T00:00:00Z",
        last_failure_at="2026-09-25T12:00:00Z",
    )
    current, alerts = advance(previous, group([("a", False)]))
    assert children(current)["a"]["consecutive_failures"] == 3
    assert children(current)["a"]["first_failure_at"] == "2026-09-25T00:00:00Z"
    assert [(row["site_id"], row["source_id"]) for row in alerts] == [("official_ai", "a")]


def test_legacy_group_snapshot_does_not_seed_child_history():
    old = {"site_id": "official_ai", "site_name": "Official AI Updates", "ok": False,
           "consecutive_failures": 4, "first_failure_at": "2026-09-20T00:00:00Z"}
    current, alerts = advance(old, group([("new", False)]))
    assert children(current)["new"]["consecutive_failures"] == 1
    assert children(current)["new"]["first_failure_at"] == "2026-09-26T00:00:00Z"
    assert alerts == []


def test_removed_or_renamed_source_does_not_inherit_anothers_history():
    old, _ = advance(None, group([("old", False)]))
    old["subsources"][0]["consecutive_failures"] = 2
    renamed, alerts = advance(old, group([("new", False)]))
    assert set(children(renamed)) == {"new"}
    assert children(renamed)["new"]["consecutive_failures"] == 1
    assert alerts == []


def test_same_child_id_in_another_group_does_not_inherit_history():
    old, _ = advance(None, group([("same", False)]))
    current = group([("same", False)], site_id="tw_media")
    alerts = apply_source_health_history([current], {"sites": [old]}, NOW + timedelta(hours=1))
    assert children(current)["same"]["consecutive_failures"] == 1
    assert alerts == []


def test_alert_output_identifies_subsource(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))
    _, alerts = advance(None, group([("safe_id", False)]), threshold=1)
    report_persistent_source_failures(alerts)
    assert "official_ai/safe_id" in capsys.readouterr().out
    assert "official_ai/safe_id" in (tmp_path / "summary.md").read_text()


@pytest.mark.parametrize("healthy", [True, False])
def test_valid_zero_items_are_real_attempts(healthy):
    current, alerts = advance(None, group([("quiet", healthy)]))
    assert alerts == []
    assert children(current)["quiet"]["last_attempt_ok"] is healthy
    assert children(current)["quiet"]["consecutive_failures"] == (0 if healthy else 1)
