"""Offline phase 01 contracts; no GitHub, SMTP, source HTTP or production writes."""

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import tw_source_observation as coordinator


ROOT = Path(__file__).resolve().parents[1]


def instant(clock="08:00:00", day="2026-10-21"):
    return coordinator.timestamp(f"{day}T{clock}+08:00")


def plan():
    config = json.loads((ROOT / "docs/examples/tw-source-observation.plan.json.example").read_text())
    return config | {"enabled": True, "experiment_id": "offline-01", "start_date": "2026-10-21", "code_sha": "a" * 40}


def context(clock="08:00:00", event="schedule", slot="primary", day="2026-10-21"):
    return {"repository": coordinator.REPOSITORY, "branch": "master", "run_id": 101,
            "created_at": instant(clock, day).isoformat(), "event_name": event,
            "schedule": next(key for key, value in coordinator.CRONS.items() if value == slot)}


def pulse(conclusion="success"):
    return context("08:35:00", "workflow_run") | {"action": "completed", "workflow_run": {
        "name": "Update AI News Snapshot", "repository": coordinator.REPOSITORY,
        "branch": "master", "event": "workflow_dispatch", "id": 99, "conclusion": conclusion,
        "created_at": instant("08:31:00").isoformat(), "completed_at": instant("08:34:00").isoformat()}}


def history(config=None, attempts=None, day="2026-10-21"):
    config = config or plan()
    return {"available": True, "experiment_id": config["experiment_id"], "date": day,
            "plan_hash": coordinator.digest(config), "attempts": attempts or []}


def outcome(status="valid_feed", count=1):
    return {"status": status, "item_count": count, "retrieved_at": instant("08:02:00").isoformat(),
            "evidence_sha256": "b" * 64}


def primary(state="finished", sources=None, baseline="07:50:00"):
    result = {"slot": "primary", "state": state, "started_at": instant().isoformat()}
    if state == "finished":
        result.update(verified=True, finished_at=instant("08:05:00").isoformat(),
                      baseline_at=instant(baseline).isoformat() if baseline else None,
                      sources={sid: outcome("no_native_feed" if sid in {"informationsecurity", "meet"} else "valid_feed")
                               for sid in coordinator.SOURCES} if sources is None else sources)
    return result


def recovery(sources=None, baseline="08:30:00"):
    return {"slot": "recovery", "state": "finished", "verified": True,
            "started_at": instant("08:30:00").isoformat(), "finished_at": instant("08:33:00").isoformat(),
            "baseline_at": instant(baseline).isoformat() if baseline else None,
            "sources": {sid: value | {"retrieved_at": instant("08:31:00").isoformat()}
                        for sid, value in (sources or {}).items()}}


def decide(attempts=None, clock="08:30:00", config=None, event=None):
    config = config or plan()
    event = event or context(clock, slot="recovery")
    return coordinator.decide(config, event, history(config, attempts), instant(clock))


def test_primary_requires_durable_claim_and_five_diagnostics():
    result = decide(clock="08:00:00", event=context())
    assert result["mode"] == "prepare_attempt"
    assert result["claim_required"] is True
    assert result["fetch_source_ids"] == list(coordinator.SOURCES)
    assert result["refresh_baseline"] is True
    assert result["day_index"] == 1


def test_disabled_checked_without_history_or_trigger_or_activation_placeholders():
    config = json.loads((ROOT / "docs/examples/tw-source-observation.plan.json.example").read_text())
    assert coordinator.decide(config, {}, {}, instant())["reason"] == "disabled"


@pytest.mark.parametrize(("field", "value"), [
    ("allow_production_mutation", True), ("allow_source_promotion", True),
    ("duration_days", 8), ("duration_days", True), ("enabled", 1),
    ("max_sampling_attempt_slots_per_day", 3), ("primary_local_time", "09:00"),
    ("recovery_local_time", "08:35"), ("recovery_start_before", "09:00"),
    ("daily_reconcile_local_time", "10:05"), ("heartbeat", {}),
    ("max_baseline_age_hours", 24), ("timezone", "UTC"), ("source_ids", ["other"]),
    ("code_sha", "master"), ("experiment_id", "../escape"), ("start_date", "20261021"),
])
def test_invalid_plan_never_prepares_requests(field, value):
    result = decide(config=plan() | {field: value})
    assert result["mode"] == "blocked"
    assert result["fetch_source_ids"] == []


@pytest.mark.parametrize(("field", "value"), [
    ("mode", "external"), ("upstream_workflow", "Other workflow"),
    ("recovery_window", ["08:00", "09:00"]), ("reconcile_window", ["09:00", "10:00"]),
    ("modify_existing_heartbeat", True), ("modify_existing_heartbeat", 0),
])
def test_misleading_heartbeat_configuration_blocks_before_sampling(field, value):
    config = plan()
    config["heartbeat"][field] = value
    result = decide(config=config)
    assert result["mode"] == "blocked" and result["fetch_source_ids"] == []


@pytest.mark.parametrize(("clock", "slot", "expected"), [
    ("07:59:59", "primary", False), ("08:00:00", "primary", True),
    ("08:29:59", "primary", True), ("08:30:00", "primary", False),
    ("08:29:59", "recovery", False), ("08:30:00", "recovery", True),
    ("08:49:59", "recovery", True), ("08:50:00", "recovery", False),
    ("09:05:00", "recovery", False),
])
def test_exact_windows(clock, slot, expected):
    result = decide(clock=clock, event=context(clock, slot=slot))
    assert (result["mode"] == "prepare_attempt") is expected


def test_delayed_primary_cannot_change_into_recovery():
    result = decide(event=context("08:29:00"), clock="08:35:00")
    assert result["reason"] == "outside_trigger_window"


@pytest.mark.parametrize("conclusion", ["success", "failure", "cancelled", "timed_out"])
def test_upstream_failure_is_still_a_valid_recovery_pulse(conclusion):
    result = decide(clock="08:35:00", event=pulse(conclusion))
    assert result["mode"] == "prepare_attempt"
    assert result["slot"] == "recovery"
    assert result["reason"] == "missed_primary"


@pytest.mark.parametrize(("field", "value"), [
    ("repository", "attacker/fork"), ("branch", "feature"), ("name", "Other job"),
    ("event", "pull_request"), ("id", True), ("conclusion", None),
    ("completed_at", "2026-10-21T00:29:59Z"),
    ("created_at", "2026-10-20T00:31:00Z"),
    ("completed_at", "2026-10-21T00:40:00Z"),
])
def test_bad_pulse_never_collects(field, value):
    event = pulse()
    event["workflow_run"][field] = value
    assert decide(clock="08:35:00", event=event)["mode"] == "blocked"


@pytest.mark.parametrize(("field", "value"), [
    ("repository", "attacker/fork"), ("branch", "feature"), ("run_id", True),
    ("run_id", 0), ("schedule", "5 22 * * *"), ("event_name", "pull_request"),
    ("created_at", "2026-10-21T08:30:00"),
    ("created_at", "2026-10-21T08:31:00+08:00"),
])
def test_bad_current_run_origin_and_metadata_blocked(field, value):
    assert decide(event=context("08:30:00", slot="recovery") | {field: value})["mode"] == "blocked"


def test_pulse_requires_completed_action():
    assert decide(clock="08:35:00", event=pulse() | {"action": "requested"})["mode"] == "blocked"


@pytest.mark.parametrize("clock", ["08:00:00", "08:30:00"])
def test_manual_dispatch_has_no_date_or_force_bypass(clock):
    result = decide(clock=clock, event=context(clock, "workflow_dispatch") | {"inputs": {"force": True, "date": "2026-10-20"}})
    assert result["date"] == "2026-10-21"
    assert result["slot"] == coordinator.slot_at(instant(clock))


def test_cross_day_rerun_cannot_backfill_or_become_today():
    result = coordinator.decide(plan(), context(), history(), instant(day="2026-10-22"))
    assert result["reason"] == "cross_day_trigger"


@pytest.mark.parametrize(("day", "expected"), [("2026-10-20", False), ("2026-10-21", True), ("2026-10-27", True), ("2026-10-28", False)])
def test_fixed_seven_calendar_days(day, expected):
    config = plan()
    result = coordinator.decide(config, context(day=day), history(config, day=day), instant(day=day))
    assert (result["mode"] == "prepare_attempt") is expected


def test_complete_primary_with_known_restrictions_skips_recovery():
    assert decide([primary()])["reason"] == "primary_complete"


def test_valid_empty_sources_are_completed_observations():
    sources = {sid: outcome("valid_empty", 0) for sid in coordinator.SOURCES}
    assert decide([primary(sources=sources)])["reason"] == "primary_complete"


def test_missing_primary_is_labeled_not_assumed_failed():
    assert decide()["reason"] == "missed_primary"


def test_running_primary_never_cancelled_or_concurrently_recovered():
    result = decide([primary("running")])
    assert result["reason"] == "attempt_running"
    assert result["fetch_source_ids"] == []


def test_unknown_primary_outcome_uses_only_recovery_slot():
    assert decide([primary("intent")])["reason"] == "primary_outcome_unknown"
    same_slot = decide([primary("intent")], clock="08:01:00", event=context())
    assert same_slot["reason"] == "slot_already_claimed"


def test_partial_primary_only_retries_transient_and_missing_sources():
    evidence = primary()
    evidence["sources"]["cyberq"] = outcome("timeout")
    del evidence["sources"]["netadmin"]
    result = decide([evidence])
    assert result["fetch_source_ids"] == ["cyberq", "netadmin"]
    assert result["reuse_sources"]["digitimes_tw"]["origin_slot"] == "primary"
    assert result["reuse_sources"]["digitimes_tw"]["retrieved_at"] == instant("08:02:00").isoformat()
    assert result["refresh_baseline"] is False


@pytest.mark.parametrize("status", sorted(coordinator.TERMINAL))
def test_terminal_restriction_never_retried(status):
    evidence = primary()
    evidence["sources"]["meet"] = outcome(status)
    evidence["sources"]["cyberq"] = outcome("timeout")
    assert "meet" not in decide([evidence])["fetch_source_ids"]


@pytest.mark.parametrize("baseline", [None, "05:59:59"])
def test_baseline_only_failure_does_not_refetch_healthy_sources(baseline):
    result = decide([primary(baseline=baseline)])
    assert result["mode"] == "prepare_attempt"
    assert result["fetch_source_ids"] == []
    assert result["refresh_baseline"] is True


def test_primary_baseline_judged_at_original_finish_not_later_clock():
    assert decide([primary(baseline="06:05:00")])["reason"] == "primary_complete"


def test_partial_baseline_must_still_be_fresh_at_recovery():
    evidence = primary(baseline="06:05:00")
    evidence["sources"]["cyberq"] = outcome("timeout")
    assert decide([evidence])["refresh_baseline"] is True


def test_all_sources_restricted_is_not_success():
    evidence = primary(sources={sid: outcome("http_403") for sid in coordinator.SOURCES})
    result = decide([evidence])
    assert result["reason"] == "partial_primary"
    assert result["fetch_source_ids"] == []
    assert result["observation_status"] == "partial"


def test_recovery_merges_source_evidence_without_rewriting_retrieval_time():
    first = primary()
    first["sources"]["cyberq"] = outcome("timeout")
    second = recovery({"cyberq": outcome("valid_empty", 0)})
    result = decide([first, second], clock="08:35:00")
    assert result["reason"] == "day_complete"
    assert result["observation_status"] == "complete"
    combined = coordinator.assess([second, first])
    assert combined["sources"]["cyberq"]["origin_slot"] == "recovery"
    assert combined["sources"]["cyberq"]["retrieved_at"] == instant("08:31:00").isoformat()
    assert combined["sources"]["netadmin"]["retrieved_at"] == instant("08:02:00").isoformat()


def test_recovery_can_only_refresh_baseline_and_complete_without_source_requests():
    result = decide([primary(baseline=None), recovery()], clock="08:35:00")
    assert result["observation_status"] == "complete"
    assert result["mode"] == "skip"


@pytest.mark.parametrize("baseline", [None, "05:00:00"])
def test_recovery_with_bad_baseline_is_unmet_not_zero_result_success(baseline):
    result = decide([primary(baseline=baseline), recovery(baseline=baseline)], clock="08:35:00")
    assert result["observation_status"] == "unmet"
    assert result["reason"] == "slot_already_claimed"


def test_recovery_with_all_feasible_feeds_failed_is_unmet():
    first = primary()
    for sid in ("cyberq", "netadmin", "digitimes_tw"):
        first["sources"][sid] = outcome("timeout")
    second = recovery({sid: outcome("http_5xx") for sid in ("cyberq", "netadmin", "digitimes_tw")})
    assert decide([first, second], clock="08:35:00")["observation_status"] == "unmet"


def test_complete_recovery_after_primary_missing_does_not_need_primary_evidence():
    result = decide([recovery({sid: outcome() for sid in coordinator.SOURCES})], clock="08:35:00")
    assert result["reason"] == "day_complete"


def test_missing_and_unknown_intent_never_count_as_empty_success():
    assert decide()["observation_status"] == "missing"
    assert decide([primary("intent")])["observation_status"] == "missing"


def test_refetching_a_reusable_source_is_invalid_history():
    result = decide([primary(baseline=None), recovery({"cyberq": outcome()})], clock="08:35:00")
    assert result["reason"] == "recovery_refetched_reusable_source"


def test_overlapping_persisted_attempts_fail_closed():
    first = primary() | {"finished_at": instant("08:32:00").isoformat()}
    result = decide([first, recovery()], clock="08:35:00")
    assert result["reason"] == "overlapping_attempts"


def test_running_primary_with_recovery_already_recorded_is_invalid():
    result = decide([primary("running"), recovery()], clock="08:35:00")
    assert result["reason"] == "overlapping_attempts"


def test_two_slots_claimed_cannot_create_third_attempt_or_rerun_recovery():
    recovery = {"slot": "recovery", "state": "intent", "started_at": instant("08:30:00").isoformat()}
    result = decide([primary("intent"), recovery], clock="08:35:00")
    assert result["reason"] == "slot_already_claimed"


@pytest.mark.parametrize(("field", "value"), [
    ("available", False), ("available", None), ("experiment_id", "other"),
    ("date", "2026-10-20"), ("plan_hash", "0" * 64), ("attempts", {}),
    ("attempts", [primary("intent"), primary("intent")]),
])
def test_unavailable_or_ambiguous_history_fails_closed(field, value):
    result = coordinator.decide(plan(), context("08:30:00", slot="recovery"), history() | {field: value}, instant("08:30:00"))
    assert result["mode"] == "blocked"
    assert result["fetch_source_ids"] == []


@pytest.mark.parametrize(("field", "value"), [
    ("verified", False), ("state", "unknown"), ("slot", "third"),
    ("started_at", "2026-10-20T00:00:00Z"), ("finished_at", "2026-10-21T00:40:00Z"),
    ("baseline_at", "2026-10-21T00:06:00Z"),
])
def test_bad_persisted_attempt_fails_closed(field, value):
    assert decide([primary() | {field: value}])["mode"] == "blocked"


@pytest.mark.parametrize(("field", "value"), [
    ("status", "unknown"), ("item_count", -1), ("item_count", True), ("item_count", 51),
    ("item_count", 0), ("evidence_sha256", "unverified"),
    ("retrieved_at", "2026-10-20T23:00:00Z"),
])
def test_bad_source_evidence_fails_closed(field, value):
    evidence = primary()
    evidence["sources"]["cyberq"][field] = value
    assert decide([evidence])["mode"] == "blocked"


def test_unsealed_partial_evidence_cannot_be_silently_reused():
    evidence = primary("intent") | {"sources": {"cyberq": outcome()}}
    assert decide([evidence])["reason"] == "unsealed_evidence"


def test_same_slot_concurrent_claim_is_durable_and_exactly_one_wins(tmp_path):
    decision = decide()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: coordinator.LocalIntentStore(tmp_path).claim(decision), range(16)))
    assert results.count(True) == 1
    assert coordinator.LocalIntentStore(tmp_path).claim(decision) is False
    marker = next(tmp_path.glob("*.intent.json"))
    assert json.loads(marker.read_text())["key"] == decision["intent_key"]
    assert marker.stat().st_mode & 0o777 == 0o600


def test_both_slots_have_distinct_claims_but_config_changes_do_not_reset_claim(tmp_path):
    store = coordinator.LocalIntentStore(tmp_path)
    main = decide(clock="08:00:00", event=context())
    backup = decide([primary("intent")])
    assert store.claim(main) is True
    assert store.claim(backup) is True
    assert store.claim(backup | {"plan_hash": "c" * 64}) is False
    assert len(list(tmp_path.glob("*.intent.json"))) == 2


def test_failed_durable_write_never_grants_claim_and_leaves_marker(monkeypatch, tmp_path):
    store = coordinator.LocalIntentStore(tmp_path)
    def fail(_):
        raise OSError("synthetic fsync failure")
    monkeypatch.setattr(coordinator.os, "fsync", fail)
    with pytest.raises(OSError, match="synthetic fsync failure"):
        store.claim(decide())
    assert store.claim(decide()) is False


def test_skipped_or_blocked_decision_cannot_claim(tmp_path):
    with pytest.raises(ValueError, match="decision_not_collectible"):
        coordinator.LocalIntentStore(tmp_path).claim(decide([primary()]))
    assert not list(tmp_path.iterdir())


def test_inputs_not_mutated_and_cli_is_only_offline_simulation(tmp_path):
    scenario = {"plan": plan(), "context": pulse("failure"), "history": history(),
                "now": instant("08:35:00").isoformat()}
    original = copy.deepcopy(scenario)
    result = coordinator.decide(scenario["plan"], scenario["context"], scenario["history"], instant("08:35:00"))
    assert scenario == original
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(scenario))
    process = subprocess.run([sys.executable, str(ROOT / "scripts/tw_source_observation.py"),
                              "--simulate", "--scenario", str(path)], capture_output=True, text=True, check=True)
    assert json.loads(process.stdout) == result
    assert sorted(p.name for p in tmp_path.iterdir()) == ["scenario.json"]


def test_cli_reports_blocked_as_failure(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text("{}")
    process = subprocess.run([sys.executable, str(ROOT / "scripts/tw_source_observation.py"),
                              "--simulate", "--scenario", str(path)], capture_output=True, text=True)
    assert process.returncode == 2
    assert json.loads(process.stdout)["mode"] == "blocked"
