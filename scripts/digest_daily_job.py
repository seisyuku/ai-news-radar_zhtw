"""Daily Drive delivery from a trusted upstream completion, never publication."""

import argparse
from datetime import datetime, time, timezone
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")
REPOSITORY = "seisyuku/ai-news-radar_zhtw"


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("timezone_required")
    return result.astimezone(timezone.utc)


def slot_at(value):
    value = value.astimezone(TAIPEI).time().replace(tzinfo=None)
    if time(7, 15) <= value < time(8, 15):
        return "primary"
    if time(8, 15) <= value < time(8, 45):
        return "backup"
    return None


def trigger_plan(event, now):
    """Freeze issue from GitHub's upstream created_at, not runner start date."""
    try:
        run = event["workflow_run"]
        if (event.get("action") != "completed" or run["name"] != "Update AI News Snapshot"
                or run["conclusion"] != "success" or run["head_branch"] != "master"
                or run["head_repository"]["full_name"] != REPOSITORY
                or event["repository"]["full_name"] != REPOSITORY
                or run["event"] not in {"schedule", "workflow_dispatch"}
                or type(run["id"]) is not int or run["id"] <= 0):
            raise ValueError()
        created, completed = timestamp(run["created_at"]), timestamp(run["updated_at"])
        if now.utcoffset() is None or not created <= completed <= now:
            raise ValueError()
        date = created.astimezone(TAIPEI).date().isoformat()
        result = {"eligible": False, "date": date, "source_run_id": run["id"]}
        if (completed.astimezone(TAIPEI).date().isoformat() != date
                or now.astimezone(TAIPEI).date().isoformat() != date):
            return {**result, "reason": "missed_issue"}
        slot = slot_at(completed)
        if slot is None or slot_at(now) != slot:
            return {**result, "reason": "outside_attempt_window"}
        return {**result, "eligible": True, "slot": slot, "reason": "eligible"}
    except Exception:
        return {"eligible": False, "reason": "untrusted_trigger"}


def existing_delivery(client, folder, date, now):
    """Verify saved originals; a human review can differ without being replaced."""
    if __package__:
        from . import digest_drive_delivery as drive
        from .digest_integrity import verify_digest_bytes
        from .deliver_digest import readiness
        from .digest_window import window_for_date
    else:
        import digest_drive_delivery as drive
        from digest_integrity import verify_digest_bytes
        from deliver_digest import readiness
        from digest_window import window_for_date
    receipt_file = client.find(folder["id"], "delivery.json")
    if receipt_file is None:
        raise drive.DriveDeliveryError("existing_issue_incomplete")
    drive.private(client.metadata(receipt_file["id"]), folder["id"], "application/json")
    try:
        receipt = json.loads(client.download(receipt_file["id"]))
        if (receipt["schema_version"] != 1 or receipt["date"] != date
                or receipt["storage_quality"] != "ready-for-review"):
            raise ValueError()
        saved = timestamp(receipt["saved_at"])
        if saved > now or saved.astimezone(TAIPEI).date().isoformat() != date:
            raise ValueError()
        ids = receipt["file_ids"]
        for role, mime in (("markdown", "text/markdown"), ("metadata", "application/json"),
                           ("original", drive.DOC_MIME), ("review", drive.DOC_MIME)):
            drive.private(client.metadata(drive.file_id(ids[role])), folder["id"], mime)
        metadata = verify_digest_bytes(client.download(ids["markdown"]), client.download(ids["metadata"]))
        if (metadata["window"]["date"] != date or metadata["input_identity"] != receipt["base"]
                or folder.get("appProperties", {}).get("digest_base") != receipt["base"]):
            raise ValueError()
        as_of = next(i.get("producer_as_of") for i in metadata["inputs"] if i["name"] == "archive.json")
        if readiness(as_of, window_for_date(date), saved)[0] != "ready-for-review":
            raise ValueError()
        _, expected, _ = drive.native_content(metadata, False)
        if drive.document_text(client.document(ids["original"])).strip() != expected.strip():
            raise ValueError()
        timeliness = "on_time" if saved.astimezone(TAIPEI).time().replace(tzinfo=None) <= time(9) else "late"
        return {"delivery_verified": True, "storage_saved_at": saved.isoformat(),
                "storage_quality": "ready-for-review", "storage_timeliness": timeliness,
                "pair_verified": True, "selected_count": metadata["selection_counts"]["selected_count"]}
    except Exception:
        raise drive.DriveDeliveryError("existing_delivery_invalid") from None


def run_daily(plan, client, target, input_dir, output_dir, *, clock=None, generator=None):
    if __package__:
        from . import digest_drive_delivery as drive
        from .generate_digest_job import generate
    else:
        import digest_drive_delivery as drive
        from generate_digest_job import generate
    clock = clock or (lambda: datetime.now(timezone.utc))
    generator = generator or generate
    report = {"mode": "automatic_daily", "status": "skipped", "reason": plan["reason"],
              "delivery_verified": False, "pair_verified": False, "rerun_identical": False}
    if not plan["eligible"]:
        if plan["reason"] == "missed_issue":
            report["status"] = "missed_issue"
        return report
    date, slot = plan["date"], plan["slot"]
    report.update(date=date, slot=slot)
    try:
        now = clock()
        if now.astimezone(TAIPEI).date().isoformat() != date:
            report.update(status="missed_issue", reason="missed_issue")
            return report
        if slot_at(now) != slot:
            report["reason"] = "outside_attempt_window"
            return report
        parent = drive.file_id(target["folder_id"])
        drive.private(client.metadata(parent), mime=drive.FOLDER_MIME)
        drive.private(client.metadata(target["settings_id"]), mime=drive.DOC_MIME)
        if not drive.read_settings(client, target["settings_id"])["automation_enabled"]:
            report["reason"] = "automation_disabled"
            return report
        folder = client.find(parent, date + "｜current")
        if folder:
            drive.private(client.metadata(folder["id"]), parent, drive.FOLDER_MIME)
            verified = existing_delivery(client, folder, date, now)
            report.update(verified, reason="already_delivered")
            return report
        control = client.find(parent, date + "｜automation")
        if control is None:
            control = client.create(parent, date + "｜automation", drive.FOLDER_MIME)
        drive.private(client.metadata(control["id"]), parent, drive.FOLDER_MIME)
        marker_name = slot + "-attempt.json"
        if client.find(control["id"], marker_name):
            report["reason"] = "attempt_already_recorded"
            return report
        marker = json.dumps({"date": date, "slot": slot, "source_run_id": plan["source_run_id"],
                             "recorded_at": now.isoformat()}, sort_keys=True).encode()
        # An uncertain create consumes this slot; backup may proceed only without a current issue folder.
        client.create(control["id"], marker_name, "application/json", raw=marker)
        report.update(generator(date, input_dir, output_dir, clock=clock))
        report.update(mode="automatic_daily", slot=slot)
        if report["status"] != "generated":
            return report  # No diagnostic/review-only draft is delivered automatically.
        now = clock()
        if now.astimezone(TAIPEI).date().isoformat() != date:
            report.update(status="missed_issue", reason="missed_issue")
            return report
        if slot_at(now) != slot:
            report.update(status="review-only", reason="outside_attempt_window")
            return report
        pair = Path(output_dir) / "pair"
        md, meta = [(pair / ("digest-" + date + ext)).read_bytes() for ext in (".md", ".meta.json")]
        delivered = drive.deliver_pair(client, target, md, meta, clock=clock)
        report.update(delivery_verified=True, storage_saved_at=delivered["saved_at"],
                      storage_quality=delivered["storage_quality"], storage_reason=delivered["storage_reason"],
                      storage_timeliness=delivered["storage_timeliness"])
        folder = client.find(parent, date + "｜current")
        receipt = {"schema_version": 1, "date": date, "base": json.loads(meta)["input_identity"],
                   "saved_at": delivered["saved_at"], "storage_quality": delivered["storage_quality"],
                   "file_ids": delivered["file_ids"]}
        raw = json.dumps(receipt, sort_keys=True).encode()
        file = client.create(folder["id"], "delivery.json", "application/json", raw=raw)
        drive.private(client.metadata(file["id"]), folder["id"], "application/json")
        if client.download(file["id"]) != raw:
            raise drive.DriveDeliveryError("receipt_readback_failed")
        if clock().astimezone(TAIPEI).date().isoformat() != date:
            raise drive.DriveDeliveryError("missed_issue")
        if delivered["storage_quality"] != "ready-for-review":
            report.update(status="review-only", reason=delivered["storage_reason"])
    except Exception as exc:
        reason = str(exc) if isinstance(exc, drive.DriveDeliveryError) else "automatic_delivery_failed"
        allowed = {"existing_issue_incomplete", "existing_delivery_invalid", "missed_issue",
                   "private_destination_required", "invalid_drive_settings", "receipt_readback_failed"}
        report.update(status="failed", reason=reason if reason in allowed else "automatic_delivery_failed",
                      delivery_verified=False)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    plan = trigger_plan(json.loads(args.event_file.read_text()), datetime.now(timezone.utc))
    if args.preflight:
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as out:
            out.write("eligible=" + str(plan["eligible"]).lower() + "\n")
        print(json.dumps(plan, sort_keys=True))
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as out:
                out.write("## Daily trigger eligibility\n\n```json\n" + json.dumps(plan, sort_keys=True) + "\n```\n")
        return 3 if plan["reason"] == "missed_issue" else 0
    if not args.input_dir or not args.output_dir:
        parser.error("input and output directories are required")
    if not plan["eligible"]:
        report = {"status": "missed_issue" if plan["reason"] == "missed_issue" else "skipped",
                  "reason": plan["reason"], "delivery_verified": False}
    else:
        try:
            if __package__:
                from .digest_drive_delivery import DriveClient
            else:
                from digest_drive_delivery import DriveClient
            client = DriveClient(json.loads(os.environ["GOOGLE_DRIVE_OAUTH_CREDENTIALS"]))
            target = json.loads(os.environ["GOOGLE_DRIVE_DIGEST_TARGET"])
            report = run_daily(plan, client, target, args.input_dir, args.output_dir)
        except Exception:
            report = {"status": "failed", "reason": "automatic_delivery_unavailable", "delivery_verified": False}
    safe = json.dumps(report, sort_keys=True, allow_nan=False)
    print(safe)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as out:
            out.write("## Daily private digest\n\n```json\n" + safe + "\n```\n")
    return {"generated": 0, "skipped": 0, "review-only": 3, "missed_issue": 3, "failed": 1}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
