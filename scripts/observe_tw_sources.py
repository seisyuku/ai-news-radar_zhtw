"""Isolated observation/report Actions entry point. Deployment requires approval.

prepare -> upload immutable intent -> collect -> upload bundle. reconcile reads
evidence only; notify sends a previously persisted email intent. audit-stop only
authorizes the two fixed experimental workflows; it performs no remote mutation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, time, timezone
import json
import os
from pathlib import Path
import subprocess
import zipfile

try:
    from . import tw_source_actions as actions
    from . import tw_source_observation as core
except ImportError:
    import tw_source_actions as actions
    import tw_source_observation as core


ROOT = Path(__file__).resolve().parents[1]


def external_root(path):
    root = Path(path).expanduser().resolve()
    actions.require(root != ROOT and ROOT not in root.parents, "output_must_be_outside_repository")
    root.mkdir(parents=True, exist_ok=True)
    return root


def metadata(plan, context, day, slot, kind):
    return {"experiment_id": plan["experiment_id"], "date": day, "slot": slot, "kind": kind,
            "run_id": context["run_id"], "run_attempt": 1, "code_sha": plan["code_sha"], "plan_hash": core.digest(plan)}


def prepare(api, plan, context, output, now):
    firing = core.trigger(context, now)
    if core.before_activation(plan, context["created_at"]):
        return {"mode": "skip", "reason": "before_activation"}
    index = (datetime.fromisoformat(firing["date"]).date() - datetime.fromisoformat(plan["start_date"]).date()).days
    if not 0 <= index < 7:
        return {"mode": "skip", "reason": "outside_experiment"}
    history, evidence = actions.restore(api, plan, firing["date"], now, context["run_id"])
    decision = core.decide(plan, context, history, now)
    if decision["mode"] != "prepare_attempt":
        return decision
    # Exact same slot has one durable name across all runs; Actions concurrency
    # serializes this entire job, not just this process. Never overwrite artifacts.
    slot, day = firing["slot"], firing["date"]
    intent = {"slot": slot, "state": "intent", "started_at": now.isoformat()}
    intent_files = actions.seal({"intent.json": actions.encoded(intent)}, metadata(plan, context, day, slot, "intent"))
    actions.write_files(output / "intent", intent_files)
    for prior_slot, files in evidence.items():
        actions.write_files(output / f"reuse-{prior_slot}", files)
    state = {"plan": plan, "context": context, "decision": decision, "intent": intent,
             "history": history, "prepared_at": now.isoformat()}
    (output / "state.json").write_bytes(actions.encoded(state))
    return {**decision, "mode": "collect", "intent_artifact_name": actions.artifact_name(plan, day, slot, "intent"),
            "intent_path": str(output / "intent"), "daily_artifact_name": actions.artifact_name(plan, day, slot, "bundle"),
            "daily_bundle_path": str(output / "bundle")}


def collect(api, state, output, baseline_path, clock, collector=None):
    plan, context, decision = state["plan"], state["context"], state["decision"]
    now = clock()
    actions.validate_activation(plan)
    firing = core.trigger(context, now)
    actions.require(firing["slot"] == decision["slot"] and firing["date"] == decision["date"], "stale_preparation")
    run = api.run(context["run_id"])
    actions.verify_run(api, run, plan)
    # Confirm GitHub actually persisted the exact local intent, not only a green
    # preceding step. On transient visibility/API failure, stop without requests.
    name = actions.artifact_name(plan, decision["date"], decision["slot"], "intent")
    artifacts = [a for a in api.artifacts(run["id"]) if a["name"] == name]
    actions.require(len(artifacts) == 1, "persisted_intent_required")
    files, _ = actions.verify_artifact(api, artifacts[0], run, plan, decision["date"], decision["slot"], "intent")
    actions.require(files == {"intent.json": actions.encoded(state["intent"])}, "persisted_intent_mismatch")
    # Re-read previous runs immediately before collection. Matching plan and
    # history forbid modified local decisions or newly discovered competing claims.
    history, evidence = actions.restore(api, plan, decision["date"], now, run["id"])
    fresh_decision = core.decide(plan, context, history, now)
    actions.require(fresh_decision == decision, "history_changed_after_prepare")
    # API/download time counts against the start window as well.
    core.trigger(context, clock())
    actions.require(core.LocalIntentStore(output / "collection-guard").claim(decision), "collection_already_started")
    try:
        from . import evaluate_tw_source_admission as shadow
    except ImportError:
        import evaluate_tw_source_admission as shadow
    collector = collector or shadow.collect_source
    by_source = {row["source_id"]: row for row in shadow.SOURCES}
    own_sources, outcomes = [], {}
    for sid in decision["fetch_source_ids"]:
        try:
            source = collector(by_source[sid])
        except Exception as error:
            # Preserve successful peers; never store exception text or headers.
            source = {**by_source[sid], "status": "collection_error", "articles": [],
                      "requests": [], "feed_results": [], "error_type": type(error).__name__}
        actions.require(source.get("source_id") == sid, "collector_source_mismatch")
        retrieved = clock().isoformat()
        outcomes[sid] = actions.source_outcome(source, retrieved)
        own_sources.append(source)
    baseline, baseline_error = None, None
    try:
        if not decision["refresh_baseline"] and "primary" in evidence:
            baseline = json.loads(evidence["primary"]["baseline.json"])
        else:
            actions.require(baseline_path.stat().st_size <= actions.MAX_ARCHIVE, "baseline_too_large")
            baseline = json.loads(baseline_path.read_bytes())
        actions.require(isinstance(baseline.get("items"), list), "invalid_baseline_items")
        actions.require(core.timestamp(baseline["generated_at"]) <= clock(), "future_baseline")
    except (OSError, ValueError, KeyError, TypeError):
        baseline, baseline_error = None, "baseline_unavailable_or_invalid"
    finished = clock()
    attempt = {"slot": decision["slot"], "state": "finished", "started_at": state["intent"]["started_at"],
               "finished_at": finished.isoformat(), "sources": outcomes,
               "baseline_at": baseline["generated_at"] if baseline else None, "baseline_error": baseline_error}
    own_capture = {"generated_at": finished.isoformat(), "sources": own_sources}
    files = {"attempt.json": actions.encoded(attempt), "capture.json": actions.encoded(own_capture)}
    if baseline:
        files["baseline.json"] = actions.encoded(baseline)
        merged = {}
        for sid, origin in decision["reuse_sources"].items():
            prior = json.loads(evidence[origin["origin_slot"]]["capture.json"])
            merged[sid] = next(row for row in prior["sources"] if row["source_id"] == sid)
        merged.update({row["source_id"]: row for row in own_sources})
        try:
            report = shadow.evaluate({"generated_at": finished.isoformat(), "sources": list(merged.values())}, baseline, days=7)
            files["report.json"] = actions.encoded(report)
            files["REPORT.md"] = shadow.markdown(report).encode()
        except (ValueError, KeyError, TypeError, AttributeError):
            # Public baseline schema/evaluation errors must not discard healthy
            # publisher evidence or be called a complete observation.
            attempt["baseline_at"] = None
            attempt["baseline_error"] = baseline_error = "baseline_comparison_failed"
            files["attempt.json"] = actions.encoded(attempt)
    # Reject invalid/future baseline and malformed outcomes before sealing.
    combined = {**history, "attempts": history["attempts"] + [{**attempt, "verified": True}]}
    core.validate_history(combined, plan, decision["date"], finished)
    assessment = core.assess(combined["attempts"])
    actions.write_files(output / "bundle", actions.seal(files, metadata(plan, context, decision["date"], decision["slot"], "bundle")))
    return {"mode": "collected", "observation_status": assessment["observation_status"],
            "source_requests_planned": decision["fetch_source_ids"], "baseline_error": baseline_error}


def reconcile(api, plan, context, output, now):
    rows, evidence = [], {}
    for day in actions.reconciliation(context, plan, now):
        error = None
        pending, candidates = None, None
        try:
            history, evidence[day] = actions.restore(api, plan, day, now)
            assessment = core.assess(history["attempts"])
            for slot in core.SLOTS:
                files = evidence[day].get(slot, {})
                if "report.json" in files:
                    comparison = json.loads(files["report.json"])
                    candidates = sum(s["metrics"]["candidate_articles"] for s in comparison["sources"])
                    pending = sum(s["metrics"]["unresolved_articles"] for s in comparison["sources"])
        except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile, actions.requests.RequestException):
            # Failed observation evidence is not an empty successful day. Email
            # can still report it IF the independent notification ledger is sound.
            history = {"attempts": []}
            assessment = {"observation_status": "unavailable", "sources": {}}
            error = "history_unavailable_or_unverified"
        status = assessment["observation_status"]
        deadline = (day < now.astimezone(core.TAIPEI).date().isoformat()
                    or now.astimezone(core.TAIPEI).time() >= time(9, 5))
        if status not in {"complete", "unavailable"} and deadline:
            status = "unmet" if assessment["sources"] or status == "in_progress" else "missing"
        rows.append({"date": day, "status": status, "attempts": history["attempts"],
                     "collection_state": assessment["observation_status"],
                     "deadline_exceeded": deadline and status != "complete",
                     "error": error,
                     "candidate_articles": candidates, "pending_review_articles": pending,
                     "source_summary": assessment["sources"]})
    report = {"schema_version": 1, "mode": "shadow_read_only", "generated_at": now.isoformat(),
              "experiment_id": plan["experiment_id"], "days": rows, "email_implemented": True}
    (output / "reconciliation.json").write_bytes(actions.encoded(report))
    try:
        from . import tw_source_reporting as reporting
    except ImportError:
        import tw_source_reporting as reporting
    try:
        notification = reporting.prepare(api, plan, context, output, now, rows, evidence)
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile, actions.requests.RequestException):
        report["notification"] = {"status": "notification_ledger_unavailable_or_unverified"}
        (output / "reconciliation.json").write_bytes(actions.encoded(report))
        return {"mode": "blocked", "reason": "notification_ledger_unavailable_or_unverified",
                "reconciliation_ready": "true", "mail_due": "false", "stop": "false"}
    report["notification"] = notification
    (output / "reconciliation.json").write_bytes(actions.encoded(report))
    return {"mode": "reconciled", "reconciliation_ready": "true", "days_checked": len(rows), **notification}


def outputs(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            for key, value in result.items():
                if isinstance(value, (str, int)):
                    actions.require("\n" not in str(value) and "\r" not in str(value), "invalid_action_output")
                    handle.write(f"{key}={value}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "collect", "reconcile", "notify", "audit-stop"))
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--event-file", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_bytes())
        core.validate_plan(plan)
        if not plan["enabled"]:
            outputs({"mode": "skip", "reason": "disabled"})
            return 0
        actions.validate_activation(plan)
        try:
            from . import tw_source_reporting as reporting
        except ImportError:
            import tw_source_reporting as reporting
        reporting.validate_notification(plan)
        actions.require(plan["notification"]["enabled"], "live_observation_requires_email_enabled")
        code_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        actions.require(code_sha == plan["code_sha"], "code_checkout_pin_mismatch")
        api = actions.GitHub(os.environ.get("GH_TOKEN"))
        event = json.loads(args.event_file.read_bytes())
        role = "report" if args.command in {"reconcile", "notify", "audit-stop"} else "observe"
        context = actions.normalize_context(api, plan, event, int(os.environ["GITHUB_RUN_ID"]), os.environ["GITHUB_EVENT_NAME"], role)
        if core.before_activation(plan, context["created_at"]):
            outputs({"mode": "skip", "reason": "before_activation"})
            return 0
        output = external_root(args.output_root)
        now = datetime.now(timezone.utc)
        if args.command == "prepare":
            result = prepare(api, plan, context, output, now)
        elif args.command == "collect":
            actions.require(args.baseline is not None, "baseline_path_required")
            state = json.loads((output / "state.json").read_bytes())
            actions.require(state["plan"] == plan and state["context"] == context, "prepared_context_mismatch")
            result = collect(api, state, output, args.baseline, lambda: datetime.now(timezone.utc))
        elif args.command == "reconcile":
            result = reconcile(api, plan, context, output, now)
        else:
            if args.command == "notify":
                result = reporting.notify(api, plan, context, output, now, os.environ.get("TW_SOURCE_EMAIL_SETTINGS", ""),
                                          clock=lambda: datetime.now(timezone.utc))
            else:
                result = reporting.audit_stop(api, plan, context, now)
        outputs(result)
        return 2 if (result.get("mode") == "blocked" or result.get("notification_status") in {"delivery_unknown", "notification_failed"}
                     or result.get("mode") == "notified"
                     and result.get("notification_status") != "provider_accepted") else 0
    except (ValueError, KeyError, TypeError, AttributeError, OSError, zipfile.BadZipFile, actions.requests.RequestException,
            subprocess.CalledProcessError) as error:
        # Never print HTTP response bodies, signed download URLs or credentials.
        outputs({"mode": "blocked", "reason": str(error) if isinstance(error, ValueError) else type(error).__name__})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
