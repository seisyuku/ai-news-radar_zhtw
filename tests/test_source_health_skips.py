"""Skipped shared source tasks preserve the last real health result."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import sys

import pytest

from scripts import update_news
from scripts.update_news import (
    apply_source_health_history,
)


NOW = datetime(2026, 9, 26, tzinfo=timezone.utc)
LAST_SUCCESS = "2026-09-24T00:00:00Z"
FIRST_FAILURE = "2026-09-25T00:00:00Z"


def site(site_id, *, ok, skipped=False, error=None):
    return {
        "site_id": site_id,
        "site_name": site_id,
        "ok": ok,
        "skipped": skipped,
        "error": error,
    }


def next_run(previous, current, now, *, threshold=3):
    failures = apply_source_health_history(
        [current], {"sites": [previous]} if previous else {}, now, threshold=threshold
    )
    return current, failures


@pytest.mark.parametrize("site_id", ["xapi", "socialdata_x", "tikhub_douyin", "tikhub_xiaohongshu"])
def test_failure_skip_failure_keeps_streak_and_real_timestamps(site_id):
    previous = site(site_id, ok=False, error="provider unavailable")
    previous.update(
        consecutive_failures=2,
        first_failure_at=FIRST_FAILURE,
        last_failure_at="2026-09-25T12:00:00Z",
        last_success_at=LAST_SUCCESS,
    )

    skipped, skipped_alerts = next_run(previous, site(site_id, ok=True, skipped=True), NOW)

    assert skipped_alerts == []
    assert skipped["consecutive_failures"] == 2
    assert skipped["first_failure_at"] == FIRST_FAILURE
    assert skipped["last_failure_at"] == "2026-09-25T12:00:00Z"
    assert skipped["last_success_at"] == LAST_SUCCESS
    assert skipped["last_attempt_ok"] is False
    assert skipped["degraded"] is True

    failed, alerts = next_run(skipped, site(site_id, ok=False, error="provider unavailable"), NOW + timedelta(hours=1))

    assert failed["consecutive_failures"] == 3
    assert failed["first_failure_at"] == FIRST_FAILURE
    assert failed["last_success_at"] == LAST_SUCCESS
    assert failed["last_attempt_ok"] is False
    assert len(alerts) == 1


def test_repeated_skips_do_not_add_failures_or_repeat_persistent_alert():
    previous = site("socialdata_x", ok=False, error="provider unavailable")
    previous.update(consecutive_failures=3, first_failure_at=FIRST_FAILURE,
                    last_failure_at=FIRST_FAILURE, last_success_at=LAST_SUCCESS,
                    persistent_failure=True)

    for hours in (1, 2, 3):
        current, alerts = next_run(previous, site("socialdata_x", ok=True, skipped=True), NOW + timedelta(hours=hours))
        assert alerts == []
        assert current["persistent_failure"] is True
        assert current["consecutive_failures"] == 3
        assert current["last_failure_at"] == FIRST_FAILURE
        assert current["last_success_at"] == LAST_SUCCESS
        previous = deepcopy(current)

    failed, alerts = next_run(previous, site("socialdata_x", ok=False, error="still unavailable"), NOW + timedelta(hours=4))
    assert failed["consecutive_failures"] == 4
    assert len(alerts) == 1


def test_failure_repeated_skips_then_success_resets_only_on_real_success():
    previous = site("tikhub_douyin", ok=False, error="provider unavailable")
    previous.update(consecutive_failures=2, first_failure_at=FIRST_FAILURE,
                    last_failure_at=FIRST_FAILURE, last_success_at=LAST_SUCCESS)
    for hours in (1, 2):
        previous, alerts = next_run(previous, site("tikhub_douyin", ok=True, skipped=True), NOW + timedelta(hours=hours))
        assert alerts == []
        assert previous["consecutive_failures"] == 2

    succeeded, alerts = next_run(previous, site("tikhub_douyin", ok=True), NOW + timedelta(hours=3))
    assert alerts == []
    assert succeeded["consecutive_failures"] == 0
    assert succeeded["first_failure_at"] is None
    assert succeeded["last_success_at"] == "2026-09-26T03:00:00Z"
    assert succeeded["last_attempt_ok"] is True


def test_first_run_skip_has_no_invented_success_or_failure():
    skipped, alerts = next_run(None, site("xapi", ok=True, skipped=True), NOW)
    assert alerts == []
    assert skipped["consecutive_failures"] == 0
    assert skipped["last_attempt_ok"] is None
    assert skipped["last_success_at"] is None
    assert skipped["last_failure_at"] is None
    assert skipped["persistent_failure"] is False


def test_legacy_skipped_snapshot_uses_retained_failure_count():
    previous = site("socialdata_x", ok=True, skipped=True)
    previous.update(consecutive_failures=2, first_failure_at=FIRST_FAILURE,
                    last_failure_at=FIRST_FAILURE, last_success_at=LAST_SUCCESS)

    failed, alerts = next_run(previous, site("socialdata_x", ok=False), NOW)
    assert failed["consecutive_failures"] == 3
    assert len(alerts) == 1


def test_real_success_then_skip_keeps_success_time():
    success, _ = next_run(None, site("xapi", ok=True), NOW)
    skipped, alerts = next_run(success, site("xapi", ok=True, skipped=True), NOW + timedelta(hours=1))
    assert alerts == []
    assert skipped["consecutive_failures"] == 0
    assert skipped["last_attempt_ok"] is True
    assert skipped["last_success_at"] == "2026-09-26T00:00:00Z"
