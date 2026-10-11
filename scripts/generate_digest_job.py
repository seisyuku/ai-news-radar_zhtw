"""Generate from checked-out data; optional private Drive delivery, no publication.

The pair is private runner output. Generation success is not durable delivery.
"""

import argparse
from datetime import datetime, time, timezone
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

if __package__:
    from .deliver_digest import readiness
    from .digest_document import build_digest_document
    from .digest_input import load_digest_input
    from .digest_window import TAIPEI, window_for_date
    from .generate_digest import verify_digest_pair, write_digest
else:
    from deliver_digest import readiness
    from digest_document import build_digest_document
    from digest_input import load_digest_input
    from digest_window import TAIPEI, window_for_date
    from generate_digest import verify_digest_pair, write_digest


def _now(clock):
    value = clock()
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("invalid_clock")
    return value.astimezone(timezone.utc)


def generate(date, input_dir, output_dir, *, historical=False,
             clock=lambda: datetime.now(timezone.utc)):
    """Leave one verified pair in a new Downloads directory, or no pair.

    Read the checkout once. Rebuild independently from the captured input bytes;
    no remote SHA lookup, code hash inventory or source refresh is performed.
    """
    report = {"status": "failed", "reason": "generation_failed", "pair_verified": False,
              "rerun_identical": False, "delivery_verified": False}
    try:
        if not isinstance(date, str) or type(historical) is not bool:
            raise ValueError()
        window = window_for_date(date)
        report.update(date=window.date, mode="manual_historical" if historical else "manual_current")
        started = _now(clock)
        if not historical and started.astimezone(TAIPEI).date().isoformat() != date:
            report.update(status="missed_issue", reason="missed_issue")
            return report
        base = Path(output_dir).resolve()
        source_dir = Path(input_dir).resolve()
        if ((Path.home() / "Downloads").resolve() not in base.parents or
                base == source_dir or source_dir in base.parents):
            report["reason"] = "invalid_output_directory"
            return report
        # Never reuse an earlier job's original or an existing human review.
        if base.exists():
            report["reason"] = "output_exists"
            return report
        snapshot = load_digest_input(source_dir)
        base.mkdir(parents=True, mode=0o700, exist_ok=False)
        with TemporaryDirectory(prefix="generation-", dir=base) as scratch:
            scratch = Path(scratch)
            source = scratch / "inputs"
            source.mkdir(mode=0o700)
            for name, raw in snapshot.captured_bytes.items():
                if raw is not None:
                    path = source / name
                    path.write_bytes(raw)
                    path.chmod(0o600)
            document = build_digest_document(snapshot, window)
            first = write_digest(document, scratch / "first")
            verify_digest_pair(*first)
            repeated = write_digest(build_digest_document(load_digest_input(source), window), scratch / "repeat")
            verify_digest_pair(*repeated)
            if [p.read_bytes() for p in first] != [p.read_bytes() for p in repeated]:
                report["reason"] = "rerun_mismatch"
                return report
            checked = _now(clock)
            if not historical and checked.astimezone(TAIPEI).date().isoformat() != date:
                report.update(status="missed_issue", reason="missed_issue")
                return report
            as_of = snapshot.inputs[0].producer_as_of
            quality, reason = readiness(as_of, window, checked)
            for path in first:
                path.chmod(0o600)
            first[0].parent.chmod(0o700)
            deadline = datetime.combine(checked.astimezone(TAIPEI).date(), time(9), TAIPEI)
            completed = dict(
                status="generated" if quality == "ready-for-review" and not historical else "review-only",
                reason="historical_review" if historical else reason,
                quality=quality, pair_verified=True, rerun_identical=True,
                selected_count=document["selection_counts"]["selected_count"], archive_as_of=as_of,
                checked_at=checked.isoformat(),
                generation_timeliness="historical" if historical else (
                    "on_time" if checked <= deadline else "late"),
            )
            first[0].parent.rename(base / "pair")
            report.update(completed)
    except Exception:
        # No raw input, private paths or exception details in public output.
        report.update(status="failed", reason="generation_failed", pair_verified=False,
                      rerun_identical=False)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate and verify a private digest from checkout data.")
    parser.add_argument("--date", required=True, help="explicit Taipei issue YYYY-MM-DD")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True, help="new directory beneath Downloads")
    parser.add_argument("--historical", action="store_true", help="manual historical review; never daily success")
    parser.add_argument("--deliver-drive", action="store_true", help="save verified pair to private Drive")
    args = parser.parse_args(argv)
    try:
        window_for_date(args.date)
    except ValueError:
        parser.error("date must be a valid YYYY-MM-DD calendar date")
    report = generate(args.date, args.input_dir, args.output_dir, historical=args.historical)
    if args.deliver_drive and report["pair_verified"] and report["rerun_identical"]:
        try:
            if __package__:
                from .digest_drive_delivery import DriveClient, deliver_pair
            else:
                from digest_drive_delivery import DriveClient, deliver_pair
            client = DriveClient(json.loads(os.environ["GOOGLE_DRIVE_OAUTH_CREDENTIALS"]))
            target = json.loads(os.environ["GOOGLE_DRIVE_DIGEST_TARGET"])
            pair = args.output_dir / "pair"
            delivered = deliver_pair(client, target, (pair / f"digest-{args.date}.md").read_bytes(),
                                     (pair / f"digest-{args.date}.meta.json").read_bytes(),
                                     historical=args.historical)
            # The private result never goes into public Actions output/summary.
            result_file = args.output_dir / "private-delivery.json"
            fd = os.open(result_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(delivered, stream, ensure_ascii=False, indent=2)
            report.update(delivery_verified=True, storage_saved_at=delivered["saved_at"],
                          storage_quality=delivered["storage_quality"], storage_reason=delivered["storage_reason"],
                          storage_timeliness=delivered["storage_timeliness"])
            if not args.historical and delivered["storage_quality"] != "ready-for-review":
                report.update(status="review-only", reason=delivered["storage_reason"])
        except Exception:
            report.update(status="failed", reason="private_delivery_failed", delivery_verified=False)
    safe = json.dumps(report, sort_keys=True, allow_nan=False)
    print(safe)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            label = "Private storage verified." if report["delivery_verified"] else "Private storage not verified."
            stream.write("## Digest generation check\n\n" + label + "\n\n```json\n" + safe + "\n```\n")
    if args.historical and report["delivery_verified"]:
        return 0  # Explicit historical storage check, never a current daily success.
    return {"generated": 0, "review-only": 3, "failed": 1, "missed_issue": 3}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
