"""GitHub validation: ephemeral drafts, public status only, no publication."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

if __package__:
    from . import deliver_digest as delivery
    from .digest_document import build_digest_document
    from .digest_input import load_digest_input
    from .digest_window import TAIPEI, parse_published_at, window_for_date
    from .generate_digest import verify_digest_pair, write_digest
else:
    import deliver_digest as delivery
    from digest_document import build_digest_document
    from digest_input import load_digest_input
    from digest_window import TAIPEI, parse_published_at, window_for_date
    from generate_digest import verify_digest_pair, write_digest


SAFE_REASONS = {
    "archive_recent_after_cutoff", "archive_as_of_unknown", "archive_as_of_future",
    "archive_before_cutoff", "archive_stale", "not_found", "download_failed",
    "download_too_large", "invalid_remote_commit", "existing_delivery_mismatch",
    "delivery_failed", "validation_failed", "missed_issue",
}


def github_get(url):
    """Use only the runner's read-only GitHub token; no token in argv/output."""
    prefix = "https://api.github.com/"
    if not url.startswith(prefix):
        raise delivery.DeliveryError("download_failed")
    try:
        result = subprocess.run([
            "gh", "api", "--method", "GET", url[len(prefix):],
            "--header", "Accept: application/vnd.github.raw+json",
        ], capture_output=True, timeout=50)
    except Exception:
        raise delivery.DeliveryError("download_failed") from None
    if result.returncode:
        if b"HTTP 404" in result.stderr:
            raise delivery.DeliveryError("not_found")
        raise delivery.DeliveryError("download_failed")
    if len(result.stdout) > delivery.MAX_BYTES:
        raise delivery.DeliveryError("download_too_large")
    return result.stdout


def issue_date(explicit, created_at, now):
    """A scheduled run keeps its creation-date issue across queue delay."""
    if explicit:
        return window_for_date(explicit).date, False
    created = parse_published_at(created_at) if created_at else now
    date = created.astimezone(TAIPEI).date().isoformat()
    return date, date != now.astimezone(TAIPEI).date().isoformat()


def validate(date, *, get=delivery.public_get, clock=lambda: datetime.now(timezone.utc), parent=None):
    window = window_for_date(date)
    report = {"date": date, "status": "failed", "reason": "validation_failed",
              "pair_verified": False, "rerun_identical": False}
    try:
        with TemporaryDirectory(prefix="digest-validation-", dir=parent) as directory:
            root = Path(directory)
            manifest, pair, attempt = delivery.deliver(root / "delivery", window, get=get, clock=clock)
            # Never expose the draft, original payload, warnings, local path or raw exception.
            status = manifest.get("status")
            reason = manifest.get("reason")
            report.update(status=status if status in {"ready-for-review", "review-only", "failed"} else "failed",
                          reason=reason if reason in SAFE_REASONS else "validation_failed")
            commit = manifest.get("source_commit")
            if isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit):
                report["source_commit"] = commit
            as_of = manifest.get("archive_as_of")
            if as_of:
                report["archive_as_of"] = parse_published_at(as_of).isoformat()
            if pair:
                md = pair / f"digest-{date}.md"
                meta = pair / f"digest-{date}.meta.json"
                document = verify_digest_pair(md, meta)
                rerun = build_digest_document(load_digest_input(attempt / "inputs"), window)
                repeated = write_digest(rerun, root / "rerun")
                if [md.read_bytes(), meta.read_bytes()] != [p.read_bytes() for p in repeated]:
                    raise ValueError("rerun_mismatch")
                report.update(pair_verified=True, rerun_identical=True,
                              selected_count=document["selection_counts"]["selected_count"])
    except Exception:
        report.update(status="failed", reason="validation_failed", pair_verified=False, rerun_identical=False)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a digest without retaining or uploading drafts.")
    parser.add_argument("--date", help="explicit Taipei issue date for manual verification")
    args = parser.parse_args(argv)
    if args.date:
        try:
            args.date = window_for_date(args.date).date
        except ValueError:
            parser.error("date must be a valid YYYY-MM-DD calendar date")
    now = datetime.now(timezone.utc)
    report = {"status": "failed", "reason": "validation_failed"}
    try:
        get = github_get if os.environ.get("GH_TOKEN") else delivery.public_get
        created = None
        if os.environ.get("GITHUB_EVENT_NAME") == "schedule":
            run = os.environ.get("GITHUB_RUN_ID", "")
            if not re.fullmatch(r"[0-9]+", run):
                raise ValueError("invalid_run")
            payload = json.loads(get(f"https://api.github.com/repos/{delivery.REPO}/actions/runs/{run}"))
            created = payload["created_at"]
        date, missed = issue_date(args.date, created, now)
        report = ({"date": date, "status": "review-only", "reason": "missed_issue",
                   "pair_verified": False, "rerun_identical": False} if missed else
                  validate(date, get=get, parent=os.environ.get("RUNNER_TEMP")))
    except Exception:
        pass
    report["checked_at"] = datetime.now(timezone.utc).isoformat()
    safe = json.dumps(report, sort_keys=True)
    print(safe)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## Daily digest validation\n\n```json\n" + safe + "\n```\n")
    return {"ready-for-review": 0, "review-only": 3, "failed": 1}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
