"""Phase 01 shadow-observation coordinator; no network, email or production imports.

``decide`` consumes a normalized, verified history snapshot. The Phase 02 adapter
obtains that snapshot from immutable Actions evidence and run metadata, under serialized
execution. A JSON fixture's ``verified`` flag is NOT artifact authentication.
The CLI is an offline simulator only; it cannot collect or deploy anything.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")
REPOSITORY = "seisyuku/ai-news-radar_zhtw"
SOURCES = ("informationsecurity", "cyberq", "netadmin", "digitimes_tw", "meet")
SLOTS = ("primary", "recovery")
CRONS = {"0 0 * * *": "primary", "30 0 * * *": "recovery"}
TERMINAL = {"robots_denied", "robots_unavailable", "manual_required", "http_401", "http_403", "http_429",
            "paywall", "no_native_feed", "host_redirect_blocked"}
RETRYABLE = {"timeout", "http_5xx", "parse_error", "transport_error"}
SUCCESS = {"valid_feed", "valid_empty"}


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_plan(plan: dict) -> None:
    """Validate the collection boundary, including disabled draft placeholders."""
    fixed = {
        "schema_version": 2, "timezone": "Asia/Taipei", "duration_days": 7,
        "primary_local_time": "08:00", "recovery_local_time": "08:30",
        "recovery_start_before": "08:50", "max_sampling_attempt_slots_per_day": 2,
        "daily_reconcile_local_time": "09:05",
        "max_baseline_age_hours": 2,
        "allow_production_mutation": False, "allow_source_promotion": False,
    }
    for key, expected in fixed.items():
        if type(plan.get(key)) is not type(expected) or plan[key] != expected:
            raise ValueError(f"invalid_plan:{key}")
    if type(plan.get("enabled")) is not bool or plan.get("source_ids") != list(SOURCES):
        raise ValueError("invalid_plan:enabled_or_sources")
    expected_heartbeat = {
        "mode": "workflow_run", "upstream_workflow": "Update AI News Snapshot",
        "recovery_window": ["08:30", "08:50"], "reconcile_window": ["09:05", "09:20"],
        "modify_existing_heartbeat": False,
    }
    if plan.get("heartbeat") != expected_heartbeat or plan["heartbeat"].get("modify_existing_heartbeat") is not False:
        raise ValueError("invalid_plan:heartbeat")
    if plan["enabled"]:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", plan.get("experiment_id") or ""):
            raise ValueError("invalid_plan:experiment_id")
        if not re.fullmatch(r"[0-9a-f]{40}", plan.get("code_sha") or ""):
            raise ValueError("invalid_plan:code_sha")
        if date.fromisoformat(plan["start_date"]).isoformat() != plan["start_date"]:
            raise ValueError("invalid_plan:start_date")
        if plan.get("history_start_at") is not None:
            if not isinstance(plan["history_start_at"], str):
                raise ValueError("invalid_plan:activation_identity")
            boundary = timestamp(plan["history_start_at"])
            if (boundary.astimezone(TAIPEI).date().isoformat() != plan["start_date"]
                    or slot_at(boundary) is None
                    or not plan["experiment_id"].endswith(boundary.strftime("-%Y%m%dt%H%M%Sz"))):
                raise ValueError("invalid_plan:activation_identity")


def before_activation(plan: dict, created_at: str) -> bool:
    """An explicit new experiment version cannot inherit pre-activation runs.

    The timestamp is bound to the experiment ID by validate_plan; moving it
    cannot silently hide an unknown attempt within the same experiment.
    """
    return (plan.get("history_start_at") is not None
            and timestamp(created_at) < timestamp(plan["history_start_at"]))


def slot_at(instant: datetime) -> str | None:
    local = instant.astimezone(TAIPEI).time()
    if time(8) <= local < time(8, 30):
        return "primary"
    if time(8, 30) <= local < time(8, 50):
        return "recovery"
    return None


def trigger(context: dict, now: datetime) -> dict:
    """Context must come from the current run API and original event, not inputs.

    created_at is this observer's run creation time. For a pulse, upstream
    timestamps additionally freeze the observation date and recovery window.
    Failed upstream conclusions are intentionally eligible as wake-up signals.
    """
    if now.tzinfo is None:
        raise ValueError("timezone_required")
    if context.get("repository") != REPOSITORY or context.get("branch") != "master":
        raise ValueError("untrusted_origin")
    if type(context.get("run_id")) is not int or context["run_id"] <= 0:
        raise ValueError("invalid_run_id")
    created = timestamp(context["created_at"])
    if created > now:
        raise ValueError("invalid_chronology")
    scheduled = context.get("event_name")
    anchor = created
    if scheduled == "schedule":
        slot = CRONS.get(context.get("schedule"))
        if slot is None:
            raise ValueError("unknown_schedule")
    elif scheduled == "workflow_dispatch":
        slot = slot_at(created)
    elif scheduled == "workflow_run":
        run = context["workflow_run"]
        if (context.get("action") != "completed" or run.get("name") != "Update AI News Snapshot"
                or run.get("repository") != REPOSITORY or run.get("branch") != "master"
                or run.get("event") not in {"schedule", "workflow_dispatch"}
                or type(run.get("id")) is not int or run["id"] <= 0
                or run.get("conclusion") not in {"success", "failure", "cancelled", "timed_out",
                                                      "neutral", "skipped", "action_required", "stale"}):
            raise ValueError("untrusted_pulse")
        upstream_created = timestamp(run["created_at"])
        anchor = timestamp(run["completed_at"])
        if not upstream_created <= anchor <= created:
            raise ValueError("invalid_chronology")
        if upstream_created.astimezone(TAIPEI).date() != anchor.astimezone(TAIPEI).date():
            raise ValueError("cross_day_trigger")
        slot = "recovery"
        if slot_at(anchor) != slot:
            raise ValueError("outside_trigger_window")
    else:
        raise ValueError("unsupported_event")
    day = anchor.astimezone(TAIPEI).date()
    if any(value.astimezone(TAIPEI).date() != day for value in (created, now)):
        raise ValueError("cross_day_trigger")
    if slot is None or slot_at(created) != slot or slot_at(now) != slot:
        raise ValueError("outside_trigger_window")
    return {"date": day.isoformat(), "slot": slot, "run_id": context["run_id"]}


def validate_history(history: dict, plan: dict, day: str, now: datetime) -> list[dict]:
    """Fail closed; unavailable, ambiguous or mismatched history is never empty.

    Each finished attempt's evidence must have been hash/schema verified by the
    Actions persistence adapter. Partial evidence may still be verified. An intent
    with unknown outcome is distinct from a run confirmed to be still running.
    """
    if history.get("available") is not True:
        raise ValueError("history_unavailable")
    if (history.get("experiment_id") != plan["experiment_id"] or history.get("date") != day
            or history.get("plan_hash") != digest(plan)):
        raise ValueError("history_scope_mismatch")
    attempts = history["attempts"]
    if not isinstance(attempts, list) or len(attempts) > 2:
        raise ValueError("invalid_attempts")
    seen = set()
    for attempt in attempts:
        slot = attempt["slot"]
        if slot not in SLOTS or slot in seen:
            raise ValueError("duplicate_or_unknown_slot")
        seen.add(slot)
        started = timestamp(attempt["started_at"])
        if started > now or started.astimezone(TAIPEI).date().isoformat() != day or slot_at(started) != slot:
            raise ValueError("invalid_attempt_time")
        if attempt["state"] not in {"intent", "running", "finished"}:
            raise ValueError("invalid_attempt_state")
        if attempt["state"] != "finished":
            if attempt.get("sources") or attempt.get("baseline_at"):
                raise ValueError("unsealed_evidence")
            continue
        if attempt.get("verified") is not True:
            raise ValueError("unverified_evidence")
        finished = timestamp(attempt["finished_at"])
        if not started <= finished <= now:
            raise ValueError("invalid_attempt_time")
        outcomes = attempt["sources"]
        if not isinstance(outcomes, dict) or not set(outcomes) <= set(SOURCES):
            raise ValueError("invalid_source_ids")
        for outcome in outcomes.values():
            if outcome["status"] not in SUCCESS | TERMINAL | RETRYABLE:
                raise ValueError("unknown_source_status")
            retrieved = timestamp(outcome["retrieved_at"])
            if not started <= retrieved <= finished:
                raise ValueError("invalid_retrieval_time")
            if not re.fullmatch(r"[0-9a-f]{64}", outcome["evidence_sha256"]):
                raise ValueError("invalid_evidence_hash")
            if outcome["status"] in SUCCESS:
                count = outcome["item_count"]
                if type(count) is not int or not 0 <= count <= 50:
                    raise ValueError("invalid_item_count")
                if (count == 0) != (outcome["status"] == "valid_empty"):
                    raise ValueError("invalid_empty_status")
        if attempt.get("baseline_at") and timestamp(attempt["baseline_at"]) > finished:
            raise ValueError("future_baseline")
    primary = next((a for a in attempts if a["slot"] == "primary"), None)
    recovery = next((a for a in attempts if a["slot"] == "recovery"), None)
    if primary and recovery:
        if primary["state"] == "running":
            raise ValueError("overlapping_attempts")
        primary_end = primary.get("finished_at", primary["started_at"])
        if timestamp(primary_end) > timestamp(recovery["started_at"]):
            raise ValueError("overlapping_attempts")
        if primary["state"] == recovery["state"] == "finished":
            reusable = {sid for sid, value in primary["sources"].items() if value["status"] in SUCCESS | TERMINAL}
            if reusable & set(recovery["sources"]):
                raise ValueError("recovery_refetched_reusable_source")
    return attempts


def assess(attempts: list[dict]) -> dict:
    """Assess verified attempts in slot order, preserving original source evidence.

    No live-clock freshness reevaluation of an already finished observation. The
    latest finished attempt's time is used; a failed baseline refresh may reuse
    the preceding baseline only while it remains within the two-hour bound.
    The report supervisor will separately classify deadline-based missing days.
    """
    sources = {}
    baseline = None
    finished = None
    for slot in SLOTS:
        attempt = next((a for a in attempts if a["slot"] == slot), None)
        if not attempt or attempt["state"] != "finished":
            continue
        for sid, value in attempt["sources"].items():
            sources[sid] = {**value, "origin_slot": slot}
        baseline = attempt.get("baseline_at") or baseline
        finished = timestamp(attempt["finished_at"])
    fresh = bool(baseline and finished and timedelta(0) <= finished - timestamp(baseline) <= timedelta(hours=2))
    complete = (set(sources) == set(SOURCES) and fresh
                and all(s["status"] in SUCCESS | TERMINAL for s in sources.values())
                and any(s["status"] in SUCCESS for s in sources.values()))
    state = "complete" if complete else "partial" if finished else "missing"
    if any(a["state"] == "running" for a in attempts):
        state = "in_progress"
    elif not complete and any(a["slot"] == "recovery" and a["state"] == "finished" for a in attempts):
        state = "unmet"
    return {"observation_status": state, "sources": sources, "baseline_at": baseline,
            "baseline_fresh_at_finish": fresh}


def decide(plan: dict, context: dict, history: dict, now: datetime) -> dict:
    """Return a plan only. ``claim_required`` must succeed before any requests.

    A completed primary is judged using its own finish time, not recovery's clock.
    A partial primary's baseline must still be fresh when recovery starts.
    """
    result = {"mode": "skip", "reason": "disabled", "claim_required": False,
              "fetch_source_ids": [], "reuse_sources": {}, "refresh_baseline": False}
    try:
        validate_plan(plan)
        if not plan["enabled"]:
            return result
        if before_activation(plan, context.get("created_at")):
            return result | {"reason": "before_activation"}
        firing = trigger(context, now)
        result.update(firing)
        day = date.fromisoformat(firing["date"])
        day_index = (day - date.fromisoformat(plan["start_date"])).days + 1
        result["day_index"] = day_index
        if not 1 <= day_index <= 7:
            return result | {"reason": "outside_experiment"}
        attempts = validate_history(history, plan, firing["date"], now)
        assessment = assess(attempts)
        result["observation_status"] = assessment["observation_status"]
        if any(a["state"] == "running" for a in attempts):
            return result | {"reason": "attempt_running"}
        primary = next((a for a in attempts if a["slot"] == "primary"), None)
        if assessment["observation_status"] == "complete":
            recovered = any(a["slot"] == "recovery" for a in attempts)
            return result | {"reason": "day_complete" if recovered else "primary_complete"}
        if any(a["slot"] == firing["slot"] for a in attempts):
            return result | {"reason": "slot_already_claimed"}
        # An existing recovery intent prevents any late primary from reopening a day.
        if any(a["slot"] == "recovery" for a in attempts):
            return result | {"reason": "recovery_already_claimed"}
        reuse = {}
        if primary and primary["state"] == "finished":
            reuse = {sid: {**outcome, "origin_slot": "primary"}
                     for sid, outcome in primary["sources"].items() if outcome["status"] in SUCCESS | TERMINAL}
        baseline = primary.get("baseline_at") if primary and primary["state"] == "finished" else None
        baseline_fresh = bool(baseline and timedelta(0) <= now - timestamp(baseline) <= timedelta(hours=2))
        reason = "primary_due"
        if firing["slot"] == "recovery":
            reason = ("missed_primary" if primary is None else
                      "primary_outcome_unknown" if primary["state"] == "intent" else "partial_primary")
        key = {"experiment_id": plan["experiment_id"], "date": firing["date"], "slot": firing["slot"]}
        return result | {"mode": "prepare_attempt", "reason": reason, "claim_required": True,
                         "intent_key": key, "plan_hash": digest(plan),
                         "fetch_source_ids": [sid for sid in SOURCES if sid not in reuse],
                         "reuse_sources": reuse, "refresh_baseline": not baseline_fresh}
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as error:
        # Never turn malformed or unavailable state into permission to collect.
        reason = str(error) if isinstance(error, ValueError) else "malformed_input"
        return result | {"mode": "blocked", "reason": reason, "claim_required": False}


class LocalIntentStore:
    """Offline atomic claim reference, NOT a cross-run Actions persistence store.

    Persist a claim before any collection. An I/O failure never authorizes requests;
    an ambiguous leftover file remains claimed. No overwrite, expiry or force mode.
    Production requires serialized jobs plus durable artifact upload confirmation.
    """

    def __init__(self, root: Path):
        self.root = root

    def claim(self, decision: dict) -> bool:
        if decision.get("mode") != "prepare_attempt" or decision.get("claim_required") is not True:
            raise ValueError("decision_not_collectible")
        key = decision["intent_key"]
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{digest(key)}.intent.json"
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return False
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"key": key, "plan_hash": decision["plan_hash"]}, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        directory = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 01 offline decision simulator; no fetch or deployment")
    parser.add_argument("--simulate", action="store_true", required=True)
    parser.add_argument("--scenario", type=Path, required=True,
                        help="JSON containing plan, context, history and timezone-aware now")
    args = parser.parse_args()
    try:
        scenario = json.loads(args.scenario.read_text(encoding="utf-8"))
        result = decide(scenario["plan"], scenario["context"], scenario["history"], timestamp(scenario["now"]))
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {"mode": "blocked", "reason": type(error).__name__}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 2 if result["mode"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
