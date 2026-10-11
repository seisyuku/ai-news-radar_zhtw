"""Fixed issue, two durable attempts, first delivery and human-review preservation."""

from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from scripts import digest_daily_job as daily
from scripts import digest_drive_delivery as drive
from tests.test_digest_drive_delivery import MemoryDrive, TARGET, SETTINGS
from tests.test_generate_digest_job import inputs


PRIMARY = datetime(2026, 10, 9, 23, 35, tzinfo=timezone.utc)
BACKUP = datetime(2026, 10, 10, 0, 35, tzinfo=timezone.utc)
DATE = "2026-10-10"


def event(now=PRIMARY):
    return {"action": "completed", "repository": {"full_name": daily.REPOSITORY},
            "workflow_run": {"id": 123, "name": "Update AI News Snapshot", "conclusion": "success",
                             "head_branch": "master", "head_repository": {"full_name": daily.REPOSITORY},
                             "event": "workflow_dispatch", "created_at": now.isoformat(),
                             "updated_at": now.isoformat()}}


def enabled():
    client = MemoryDrive()
    client.docs["settings"] = json.dumps({**SETTINGS, "automation_enabled": True})
    return client


def source(tmp_path):
    row = {"title": "OpenAI announces a synthetic agent", "site_id": "official_ai", "source": "OpenAI News",
           "published_at": "2026-10-10T05:30:00+08:00", "id": "a", "url": "https://example.invalid/a"}
    return inputs(tmp_path / "input", rows=[row])


def test_issue_frozen_from_upstream_created_date_and_cross_day_rejected():
    assert daily.trigger_plan(event(), PRIMARY)["date"] == DATE
    tomorrow = datetime(2026, 10, 10, 23, 35, tzinfo=timezone.utc)
    assert daily.trigger_plan(event(), tomorrow)["reason"] == "missed_issue"
    changed = event()
    changed["workflow_run"]["created_at"] = "2026-10-09T15:59:00Z"
    assert daily.trigger_plan(changed, PRIMARY)["reason"] == "missed_issue"


@pytest.mark.parametrize("hour,minute,slot", [(23, 14, None), (23, 15, "primary"),
                                            (0, 14, "primary"), (0, 15, "backup"),
                                            (0, 44, "backup"), (0, 45, None)])
def test_exact_approved_attempt_windows(hour, minute, slot):
    day = 9 if hour == 23 else 10
    now = datetime(2026, 10, day, hour, minute, tzinfo=timezone.utc)
    result = daily.trigger_plan(event(now), now)
    assert result["eligible"] == (slot is not None)
    assert result.get("slot") == slot


@pytest.mark.parametrize("field,value", [("head_branch", "untrusted"), ("event", "pull_request"),
                                        ("conclusion", "failure"), ("name", "Other workflow"),
                                        ("id", "123"), ("created_at", "2026-10-10T07:35:00")])
def test_other_workflows_branches_events_and_naive_date_rejected(field, value):
    data = event()
    data["workflow_run"][field] = value
    assert daily.trigger_plan(data, PRIMARY)["reason"] == "untrusted_trigger"


def test_wrong_repository_future_completion_and_expired_slot_rejected():
    data = event()
    data["workflow_run"]["head_repository"]["full_name"] = "other/fork"
    assert not daily.trigger_plan(data, PRIMARY)["eligible"]
    data = event()
    data["workflow_run"]["updated_at"] = BACKUP.isoformat()
    assert not daily.trigger_plan(data, PRIMARY)["eligible"]
    assert daily.trigger_plan(event(), BACKUP)["reason"] == "outside_attempt_window"


def test_disabled_setting_or_ineligible_trigger_has_no_writes(tmp_path):
    client = MemoryDrive()
    plan = daily.trigger_plan(event(), PRIMARY)
    assert daily.run_daily(plan, client, TARGET, tmp_path, tmp_path / "out", clock=lambda: PRIMARY)["reason"] == "automation_disabled"
    assert not client.writes
    assert daily.run_daily({"eligible": False, "reason": "missed_issue"}, client,
                           TARGET, tmp_path, tmp_path / "out")["status"] == "missed_issue"
    assert daily.run_daily({"eligible": False, "reason": "untrusted_trigger"}, client,
                           TARGET, tmp_path, tmp_path / "out")["status"] == "skipped"
    assert not client.writes


def test_first_delivery_recorded_duplicate_skips_changed_inputs_and_keeps_human_review(tmp_path):
    client = enabled()
    report = daily.run_daily(daily.trigger_plan(event(), PRIMARY), client, TARGET, source(tmp_path),
                             tmp_path / "out", clock=lambda: PRIMARY)
    assert report["status"] == "generated" and report["delivery_verified"]
    folder = client.find("root", DATE + "｜current")
    saved = json.loads(client.download(client.find(folder["id"], "delivery.json")["id"]))
    client.docs[saved["file_ids"]["review"]] = "人工口述校稿已保存"
    writes = deepcopy(client.writes)
    def forbidden(*a, **k):
        pytest.fail("must not regenerate or read new input once delivered")
    duplicate = daily.run_daily(daily.trigger_plan(event(BACKUP), BACKUP), client, TARGET,
                                tmp_path / "missing-new-input", tmp_path / "new", clock=lambda: BACKUP,
                                generator=forbidden)
    assert duplicate["reason"] == "already_delivered" and duplicate["delivery_verified"]
    assert duplicate["storage_saved_at"] == report["storage_saved_at"]
    assert client.docs[saved["file_ids"]["review"]] == "人工口述校稿已保存"
    assert client.writes == writes
    client.bytes[saved["file_ids"]["markdown"]] = b"PRIVATE changed original"
    rejected = daily.run_daily(daily.trigger_plan(event(BACKUP), BACKUP), client, TARGET,
                               tmp_path, tmp_path / "new", clock=lambda: BACKUP, generator=forbidden)
    assert rejected["status"] == "failed" and not rejected["delivery_verified"]
    assert client.writes == writes and "PRIVATE" not in json.dumps(rejected)


def test_stale_snapshot_does_not_deliver_and_each_slot_runs_once(tmp_path):
    client = enabled()
    input_dir = inputs(tmp_path / "input", as_of="2026-10-09T22:00:00Z")
    plan = daily.trigger_plan(event(), PRIMARY)
    report = daily.run_daily(plan, client, TARGET, input_dir, tmp_path / "out", clock=lambda: PRIMARY)
    assert report["reason"] == "archive_stale" and not report["delivery_verified"]
    assert not client.find("root", DATE + "｜current")
    again = daily.run_daily(plan, client, TARGET, input_dir, tmp_path / "again", clock=lambda: PRIMARY)
    assert again["reason"] == "attempt_already_recorded" and not (tmp_path / "again").exists()
    (input_dir / "archive.json").write_text(json.dumps({"generated_at": "2026-10-10T00:30:00Z", "items": []}))
    backup = daily.run_daily(daily.trigger_plan(event(BACKUP), BACKUP), client, TARGET,
                             input_dir, tmp_path / "backup", clock=lambda: BACKUP)
    assert backup["delivery_verified"] and backup["selected_count"] == 0


def test_partial_save_stops_backup_without_replacing_base(tmp_path):
    client = enabled()
    original = client.write_document
    def interrupted(*a, **k):
        raise OSError("PRIVATE failed write")
    client.write_document = interrupted
    daily.run_daily(daily.trigger_plan(event(), PRIMARY), client, TARGET, source(tmp_path),
                    tmp_path / "out", clock=lambda: PRIMARY)
    folder = client.find("root", DATE + "｜current")
    assert folder and not client.find(folder["id"], "delivery.json")
    writes = deepcopy(client.writes)
    client.write_document = original
    backup = daily.run_daily(daily.trigger_plan(event(BACKUP), BACKUP), client, TARGET,
                             tmp_path / "missing", tmp_path / "backup", clock=lambda: BACKUP)
    assert backup["reason"] == "existing_issue_incomplete" and not backup["delivery_verified"]
    assert client.writes == writes and "PRIVATE" not in json.dumps(backup)


def test_date_rollover_after_generation_never_starts_private_issue(tmp_path):
    client = enabled()
    times = iter([PRIMARY, datetime(2026, 10, 10, 16, tzinfo=timezone.utc)])
    def generator(*args, **kwargs):
        return {"status": "generated", "pair_verified": True, "rerun_identical": True}
    result = daily.run_daily(daily.trigger_plan(event(), PRIMARY), client, TARGET, tmp_path,
                             tmp_path / "out", clock=lambda: next(times), generator=generator)
    assert result["status"] == "missed_issue" and not client.find("root", DATE + "｜current")


def test_unknown_exception_not_in_public_report(tmp_path):
    client = enabled()
    def broken(*a, **k):
        raise RuntimeError("PRIVATE secret or URL")
    result = daily.run_daily(daily.trigger_plan(event(), PRIMARY), client, TARGET,
                             tmp_path, tmp_path / "out", clock=lambda: PRIMARY, generator=broken)
    assert result["reason"] == "automatic_delivery_failed" and "PRIVATE" not in json.dumps(result)
