"""Read-only Actions adapter for the isolated Taiwan-source experiment.

No publisher fetching, email, git mutation or workflow dispatch. All API errors
propagate: an unavailable or incomplete history must never become empty history.
"""
from __future__ import annotations

import base64
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import stat
from urllib.parse import quote, urlsplit
import zipfile

import requests

try:
    from . import tw_source_observation as core
except ImportError:
    import tw_source_observation as core


WORKFLOWS = {"observe": ("tw-source-observation.yml", "TW source shadow observation"),
             "report": ("tw-source-report.yml", "TW source shadow report")}
MAX_ARCHIVE = 25_000_000
MAX_EXPANDED = 35_000_000
MAX_FINAL_ARCHIVE = 110_000_000
MAX_FINAL_EXPANDED = 140_000_000
ACTIVE = {"queued", "in_progress", "waiting", "pending", "requested"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(content):
    return hashlib.sha256(content).hexdigest()


def source_status(source):
    feeds, requests = source.get("feed_results", []), source.get("requests", [])
    valid = next((row["status"] for row in feeds if row["status"] in core.SUCCESS), None)
    if source.get("status") == "verified_native_feed" and valid:
        return valid
    # The probe does not retain Retry-After. Do not turn a rate-limit response
    # into an automatic same-day retry with an invented safe delay.
    for code in (403, 401, 429):
        if any(row.get("http_status") == code for row in requests):
            return f"http_{code}"
    if any(row.get("status") == "outside_publisher_hosts" for row in requests):
        return "host_redirect_blocked"
    if any(row.get("status") == "crawl_delay_requires_manual_run" for row in requests):
        return "manual_required"
    if any(row.get("status") == "robots_blocked_or_unavailable" for row in requests):
        # The probe's combined diagnostic cannot prove an explicit robots ban.
        return "robots_unavailable"
    if any("Timeout" in row.get("status", "") for row in requests):
        return "timeout"
    if any((row.get("http_status") or 0) >= 500 for row in requests):
        return "http_5xx"
    if (source.get("status") == "collection_error" or any(row.get("status") in
            {"ConnectionError", "SSLError", "ProxyError"} for row in requests)):
        return "transport_error"
    return "parse_error" if feeds else "no_native_feed"


def source_outcome(source, retrieved_at):
    status = source_status(source)
    result = {"status": status, "retrieved_at": retrieved_at, "evidence_sha256": sha(encoded(source))}
    if status in core.SUCCESS:
        result["item_count"] = len(source["articles"])
    return result


def artifact_name(plan, day, slot, kind):
    require(slot in core.SLOTS and kind in {"intent", "bundle"}, "invalid_artifact_kind")
    require(date.fromisoformat(day).isoformat() == day, "invalid_artifact_day")
    return f"twso-{plan['experiment_id']}-{day}-{slot}-{kind}"


def validate_activation(plan):
    core.validate_plan(plan)
    require(plan["enabled"], "disabled")
    require(plan.get("lookback_days") == 7 and plan.get("artifact_retention_days") == 30,
            "invalid_experiment_bounds")
    pins = plan.get("workflow_sha256", {})
    require(set(pins) == {value[0] for value in WORKFLOWS.values()}, "workflow_pins_required")
    require(all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) for value in pins.values()),
            "invalid_workflow_pin")


class GitHub:
    """GET-only API; token never follows signed artifact redirects."""
    def __init__(self, token, session=None):
        require(bool(token), "github_token_required")
        self.session = session or requests.Session()
        self.session.trust_env = False
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"}
        self.prefix = f"https://api.github.com/repos/{core.REPOSITORY}/"
        self.content_cache = {}

    def get(self, path):
        require(not path.startswith(("/", "http")) and ".." not in path, "invalid_api_path")
        response = self.session.get(self.prefix + path, headers=self.headers, timeout=(8, 20), allow_redirects=False)
        require(response.status_code == 200, "github_api_failed")
        return response.json()

    def pages(self, path, field):
        result = []
        for page in range(1, 11):
            separator = "&" if "?" in path else "?"
            payload = self.get(f"{path}{separator}per_page=100&page={page}")
            rows = payload[field]
            require(isinstance(rows, list), "invalid_api_page")
            result.extend(rows)
            require(len(result) <= 1000 and payload.get("total_count", 0) <= 1000, "history_page_limit")
            if len(rows) < 100:
                require(len(result) == payload["total_count"], "incomplete_api_history")
                return result
        raise ValueError("history_page_limit")

    def run(self, run_id):
        require(type(run_id) is int and run_id > 0, "invalid_run_id")
        return self.get(f"actions/runs/{run_id}")

    def workflow_content(self, run, filename):
        key = (run["head_sha"], filename)
        if key not in self.content_cache:
            data = self.get(f"contents/.github/workflows/{filename}?ref={run['head_sha']}")
            require(data.get("encoding") == "base64" and data.get("type") == "file", "invalid_workflow_content")
            self.content_cache[key] = base64.b64decode(data["content"], validate=False)
        return self.content_cache[key]

    def archive(self, artifact):
        require(type(artifact.get("id")) is int and artifact["id"] > 0, "invalid_artifact_id")
        response = self.session.get(self.prefix + f"actions/artifacts/{artifact['id']}/zip",
                                    headers=self.headers, timeout=(8, 20), allow_redirects=False)
        require(response.status_code == 302, "artifact_download_failed")
        target = response.headers.get("Location", "")
        parsed = urlsplit(target)
        host = parsed.hostname or ""
        require(parsed.scheme == "https" and not parsed.username and not parsed.password
                and parsed.port in {None, 443} and any(host.endswith(suffix) for suffix in
                (".blob.core.windows.net", ".actions.githubusercontent.com", ".githubusercontent.com")),
                "untrusted_artifact_redirect")
        # Separate request without the GitHub bearer token, ambient .netrc or proxy.
        with self.session.get(target, headers={}, timeout=(8, 20), allow_redirects=False, stream=True) as download:
            require(download.status_code == 200, "artifact_download_failed")
            chunks, size = [], 0
            for chunk in download.iter_content(65536):
                size += len(chunk)
                limit = MAX_FINAL_ARCHIVE if artifact.get("name", "").endswith("-final") else MAX_ARCHIVE
                require(size <= limit, "artifact_too_large")
                chunks.append(chunk)
        return b"".join(chunks)

    def runs(self, day):
        # Pinned collector code cannot claim outside these created/start windows.
        # Skip the many heartbeat runs whose jobs never sampled; reading every
        # hourly run for seven days would exhaust the supervisor's time budget.
        start = datetime.combine(date.fromisoformat(day), time(6), core.TAIPEI).astimezone(timezone.utc)
        end = datetime.combine(date.fromisoformat(day), time(6, 50), core.TAIPEI).astimezone(timezone.utc) - timedelta(seconds=1)
        bounds = quote(f"{start.isoformat()}..{end.isoformat()}", safe="")
        filename = WORKFLOWS["observe"][0]
        return self.pages(f"actions/workflows/{filename}/runs?branch=master&created={bounds}", "workflow_runs")

    def artifacts(self, run_id):
        return self.pages(f"actions/runs/{run_id}/artifacts", "artifacts")

    def report_runs(self, start, end):
        days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
        # The ledger depends on artifacts retained for 30 days. Beyond that
        # horizon, do not scan an ever-growing range or infer an empty ledger.
        require(1 <= days <= 30, "history_outside_retention_window")
        result = {}
        for offset in range(days):
            day = date.fromisoformat(start) + timedelta(days=offset)
            first = datetime.combine(day, time(6), core.TAIPEI).astimezone(timezone.utc)
            last = datetime.combine(day, time(7, 20), core.TAIPEI).astimezone(timezone.utc) - timedelta(seconds=1)
            bounds = quote(f"{first.isoformat()}..{last.isoformat()}", safe="")
            rows = self.pages(f"actions/workflows/{WORKFLOWS['report'][0]}/runs?branch=master&created={bounds}", "workflow_runs")
            result.update({row["id"]: row for row in rows})
        # Manual delayed reconciliation is allowed after the morning window.
        first = datetime.combine(date.fromisoformat(start), time(), core.TAIPEI).astimezone(timezone.utc)
        last = datetime.combine(date.fromisoformat(end) + timedelta(days=1), time(), core.TAIPEI).astimezone(timezone.utc) - timedelta(seconds=1)
        bounds = quote(f"{first.isoformat()}..{last.isoformat()}", safe="")
        rows = self.pages(f"actions/workflows/{WORKFLOWS['report'][0]}/runs?branch=master&event=workflow_dispatch&created={bounds}", "workflow_runs")
        result.update({row["id"]: row for row in rows})
        return list(result.values())

    def jobs(self, run_id):
        return self.pages(f"actions/runs/{run_id}/jobs?filter=all", "jobs")


def verify_run(api, run, plan, role="observe"):
    filename, name = WORKFLOWS[role]
    require(type(run.get("id")) is int and run["id"] > 0, "invalid_run_id")
    require(run.get("repository", {}).get("full_name") == core.REPOSITORY
            and run.get("head_repository", {}).get("full_name") == core.REPOSITORY
            and run.get("head_branch") == "master" and run.get("name") == name,
            "untrusted_workflow_run")
    require(run.get("path", "").split("@")[0] == f".github/workflows/{filename}", "wrong_workflow_path")
    require(type(run.get("run_attempt")) is int and run["run_attempt"] == 1, "rerun_not_collectible")
    require(re.fullmatch(r"[0-9a-f]{40}", run.get("head_sha", "")), "invalid_run_sha")
    require(run.get("event") in {"schedule", "workflow_dispatch", "workflow_run"}, "untrusted_run_event")
    require(sha(api.workflow_content(run, filename)) == plan["workflow_sha256"][filename], "workflow_pin_mismatch")


def normalize_context(api, plan, event, run_id, event_name, role="observe"):
    run = api.run(run_id)
    verify_run(api, run, plan, role)
    require(run["event"] == event_name and event.get("repository", {}).get("full_name") == core.REPOSITORY,
            "event_metadata_mismatch")
    context = {"repository": core.REPOSITORY, "branch": "master", "run_id": run_id,
               "created_at": run["created_at"], "event_name": event_name}
    if event_name == "schedule":
        context["schedule"] = event["schedule"]
    if event_name == "workflow_run":
        pulse = event["workflow_run"]
        upstream = api.run(pulse["id"])
        for field in ("id", "name", "event", "head_branch", "head_sha", "created_at", "updated_at", "conclusion"):
            require(pulse.get(field) == upstream.get(field), "stale_or_changed_pulse")
        require(event.get("action") == "completed" and upstream.get("status") == "completed",
                "pulse_not_completed")
        require(upstream.get("repository", {}).get("full_name") == core.REPOSITORY
                and upstream.get("head_repository", {}).get("full_name") == core.REPOSITORY,
                "untrusted_pulse_repository")
        if upstream["name"] == WORKFLOWS["observe"][1]:
            verify_run(api, upstream, plan)
        context.update(action="completed", workflow_run={
            "id": upstream["id"], "name": upstream["name"], "event": upstream["event"],
            "repository": core.REPOSITORY, "branch": upstream["head_branch"],
            "conclusion": upstream["conclusion"], "created_at": upstream["created_at"],
            # Run REST payload has updated_at, not a guaranteed completed_at field.
            # Use this completed-event timestamp, checked against current API state.
            "completed_at": upstream["updated_at"],
        })
    return context


def seal(files, metadata):
    require("manifest.json" not in files, "reserved_manifest")
    manifest = {"schema_version": 1, **metadata, "files": {name: sha(content) for name, content in files.items()}}
    return {**files, "manifest.json": encoded(manifest)}


def unpack(content, artifact, *, final=False):
    require(len(content) <= (MAX_FINAL_ARCHIVE if final else MAX_ARCHIVE), "artifact_too_large")
    require(artifact.get("expired") is False, "artifact_expired")
    require(artifact.get("digest") == "sha256:" + sha(content), "artifact_digest_mismatch")
    files = {}
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        expanded = 0
        for item in archive.infolist():
            require(re.fullmatch(r"[a-zA-Z0-9_.-]+", item.filename) and not item.is_dir()
                    and not stat.S_ISLNK(item.external_attr >> 16) and not item.flag_bits & 1,
                    "unsafe_archive_member")
            require(item.filename not in files, "duplicate_archive_member")
            expanded += item.file_size
            require(expanded <= (MAX_FINAL_EXPANDED if final else MAX_EXPANDED)
                    and len(files) < (150 if final else 20), "expanded_artifact_too_large")
            files[item.filename] = archive.read(item)
    manifest = json.loads(files.pop("manifest.json"))
    require(manifest.get("schema_version") == 1 and manifest.get("files") == {k: sha(v) for k, v in files.items()},
            "manifest_hash_mismatch")
    return files, manifest


def verify_artifact(api, artifact, run, plan, day, slot, kind):
    require(artifact.get("name") == artifact_name(plan, day, slot, kind), "artifact_name_mismatch")
    files, manifest = unpack(api.archive(artifact), artifact)
    expected = {"experiment_id": plan["experiment_id"], "date": day, "slot": slot, "kind": kind,
                "run_id": run["id"], "run_attempt": 1, "code_sha": plan["code_sha"], "plan_hash": core.digest(plan)}
    require(all(manifest.get(k) == value for k, value in expected.items()), "manifest_scope_mismatch")
    require(artifact.get("workflow_run", {}).get("id") == run["id"], "artifact_run_mismatch")
    return files, manifest


def restore(api, plan, day, now, current_run_id=None):
    """Restore a complete daily ledger plus raw verified evidence for reuse.

    Enumerating runs as well as artifacts detects deletion of an uploaded intent.
    A prior active run without visible intent blocks; it cannot silently vanish.
    """
    validate_activation(plan)
    attempts, evidence, seen = [], {}, set()
    runs = api.runs(day)
    current = api.run(current_run_id) if current_run_id else None
    require(len({r["id"] for r in runs}) == len(runs), "duplicate_history_run")
    for summary in runs:
        if summary["id"] == current_run_id:
            continue
        run = api.run(summary["id"])
        if current and (core.timestamp(run["created_at"]), run["id"]) > (core.timestamp(current["created_at"]), current_run_id):
            continue  # Later queued runs cannot have executed under concurrency.
        verify_run(api, run, plan)
        require(core.timestamp(run["created_at"]).astimezone(core.TAIPEI).date().isoformat() == day,
                "history_run_date_mismatch")
        artifacts = api.artifacts(run["id"])
        prefix = f"twso-{plan['experiment_id']}-{day}-"
        relevant = [a for a in artifacts if a["name"].startswith(prefix)]
        if not relevant:
            if run["status"] in ACTIVE:
                raise ValueError("prior_run_active_without_intent")
            jobs = api.jobs(run["id"])
            require(bool(jobs), "missing_run_jobs")
            for job in jobs:
                for step in job.get("steps", []):
                    if step.get("name") == "Persist sampling intent" and step.get("conclusion") not in {"skipped", None}:
                        raise ValueError("intent_missing_after_upload_attempt")
                    if step.get("name") == "Collect shadow sources" and step.get("conclusion") != "skipped":
                        raise ValueError("intent_missing_after_collection")
            continue
        names = [a["name"] for a in relevant]
        require(len(set(names)) == len(names), "duplicate_artifact")
        for slot in core.SLOTS:
            intent_name = artifact_name(plan, day, slot, "intent")
            bundle_name = artifact_name(plan, day, slot, "bundle")
            intent_art = next((a for a in relevant if a["name"] == intent_name), None)
            bundle_art = next((a for a in relevant if a["name"] == bundle_name), None)
            if not intent_art:
                require(bundle_art is None, "orphan_bundle")
                continue
            require(slot not in seen, "duplicate_slot_claim")
            seen.add(slot)
            files, _ = verify_artifact(api, intent_art, run, plan, day, slot, "intent")
            require(set(files) == {"intent.json"}, "invalid_intent_files")
            intent = json.loads(files["intent.json"])
            require(intent.get("slot") == slot and intent.get("state") == "intent", "invalid_intent")
            if bundle_art:
                files, _ = verify_artifact(api, bundle_art, run, plan, day, slot, "bundle")
                attempt = json.loads(files["attempt.json"])
                require(attempt.get("slot") == slot and attempt.get("state") == "finished"
                        and attempt.get("started_at") == intent.get("started_at"), "attempt_intent_mismatch")
                allowed = {"attempt.json", "capture.json", "baseline.json", "report.json", "REPORT.md"}
                require(set(files) <= allowed and {"attempt.json", "capture.json"} <= set(files), "invalid_bundle_files")
                captures = json.loads(files["capture.json"])
                by_id = {row["source_id"]: row for row in captures["sources"]}
                require(len(by_id) == len(captures["sources"]) and set(by_id) == set(attempt["sources"]),
                        "capture_source_mismatch")
                for sid, outcome in attempt["sources"].items():
                    require(outcome == source_outcome(by_id[sid], outcome["retrieved_at"]), "source_evidence_mismatch")
                baseline_at = attempt.get("baseline_at")
                if baseline_at:
                    require("baseline.json" in files and json.loads(files["baseline.json"])["generated_at"] == baseline_at,
                            "baseline_metadata_mismatch")
                    require({"report.json", "REPORT.md"} <= set(files), "comparison_report_missing")
                    report = json.loads(files["report.json"])
                    require(report.get("mode") == "shadow_only" and report.get("baseline_generated_at") == baseline_at,
                            "comparison_report_mismatch")
                attempt["verified"] = True
                attempt["origin_run_id"] = run["id"]
                attempt["origin_artifact_id"] = bundle_art["id"]
                attempts.append(attempt)
                evidence[slot] = files
            else:
                attempts.append({"slot": slot, "started_at": intent["started_at"],
                                 "origin_run_id": run["id"], "origin_artifact_id": intent_art["id"],
                                 "state": "running" if run["status"] in ACTIVE else "intent"})
        require(set(names) <= {artifact_name(plan, day, s, k) for s in core.SLOTS for k in ("intent", "bundle")},
                "unknown_experiment_artifact")
    snapshot = {"available": True, "experiment_id": plan["experiment_id"], "date": day,
                "plan_hash": core.digest(plan), "attempts": attempts}
    core.validate_history(snapshot, plan, day, now)
    return snapshot, evidence


def reconciliation(context, plan, now):
    """Read-only supervisor gate, including delayed manual reconciliation of D7."""
    require(context["repository"] == core.REPOSITORY and context["branch"] == "master", "untrusted_origin")
    created = core.timestamp(context["created_at"])
    require(created <= now and created.astimezone(core.TAIPEI).date() == now.astimezone(core.TAIPEI).date(),
            "cross_day_trigger")
    local = now.astimezone(core.TAIPEI)
    event = context["event_name"]
    if event == "workflow_run":
        run = context["workflow_run"]
        require(context["action"] == "completed" and run["repository"] == core.REPOSITORY
                and run["branch"] == "master", "untrusted_pulse")
        completed = core.timestamp(run["completed_at"]).astimezone(core.TAIPEI)
        upstream_created = core.timestamp(run["created_at"]).astimezone(core.TAIPEI)
        require(upstream_created <= completed <= created and upstream_created.date() == completed.date() == local.date(),
                "cross_day_trigger")
        if run["name"] == WORKFLOWS["observe"][1]:
            require(run["event"] in {"schedule", "workflow_dispatch", "workflow_run"}
                    and time(6) <= completed.time() < time(7, 20) and local.time() < time(7, 20),
                    "outside_reconcile_window")
        else:
            require(run["name"] == "Update AI News Snapshot" and run["event"] in {"schedule", "workflow_dispatch"}
                    and time(7, 5) <= completed.time() < time(7, 20)
                    and time(7, 5) <= local.time() < time(7, 20), "outside_reconcile_window")
    elif event == "schedule":
        require(context["schedule"] == "5 23 * * *" and time(7, 5) <= local.time() < time(7, 20)
                and time(7, 5) <= created.astimezone(core.TAIPEI).time() < time(7, 20),
                "outside_reconcile_window")
    else:
        require(event == "workflow_dispatch" and local.time() >= time(7, 5), "outside_reconcile_window")
    start = date.fromisoformat(plan["start_date"])
    end = min(local.date(), start + timedelta(days=6))
    return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]


def write_files(root: Path, files):
    root.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        require(re.fullmatch(r"[a-zA-Z0-9_.-]+", name), "unsafe_output_name")
        (root / name).write_bytes(content)
