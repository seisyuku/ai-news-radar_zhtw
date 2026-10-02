"""Manual private delivery from a pinned public snapshot; no source refresh."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

if __package__:
    from .digest_document import build_digest_document
    from .digest_input import INPUT_NAMES, load_digest_input
    from .digest_window import DigestTimeError, parse_published_at, window_for_date
    from .generate_digest import verify_digest_pair, write_digest
else:
    from digest_document import build_digest_document
    from digest_input import INPUT_NAMES, load_digest_input
    from digest_window import DigestTimeError, parse_published_at, window_for_date
    from generate_digest import verify_digest_pair, write_digest


REPO = "seisyuku/ai-news-radar_zhtw"
MAX_BYTES = 64 * 1024 * 1024


class DeliveryError(ValueError):
    pass


def public_get(url):
    """Unauthenticated GET only; bounded bytes/time, no arbitrary error replay."""
    try:
        response = subprocess.run([
            "curl", "--disable", "--silent", "--fail", "--proto", "=https",
            "--connect-timeout", "10", "--max-time", "45",
            "--max-filesize", str(MAX_BYTES), "--write-out", "%{http_code}",
            "--header", "Accept: application/vnd.github.raw+json",
            "--user-agent", "ai-news-radar-local-digest", url,
        ], capture_output=True, timeout=50)
    except Exception:
        raise DeliveryError("download_failed") from None
    if response.returncode:
        if response.stdout[-3:] == b"404":
            raise DeliveryError("not_found")
        raise DeliveryError("download_failed")
    raw = response.stdout[:-3]
    if response.stdout[-3:] != b"200":
        raise DeliveryError("download_failed")
    if len(raw) > MAX_BYTES:
        raise DeliveryError("download_too_large")
    return raw


def resolve_commit(get):
    try:
        payload = json.loads(get(f"https://api.github.com/repos/{REPO}/git/ref/heads/master"))
        commit = payload["object"]["sha"]
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError
        return commit
    except DeliveryError:
        raise
    except Exception:
        raise DeliveryError("invalid_remote_commit") from None


def private_write(path, raw):
    # Only newly created attempt files; never replace a previous delivery/review.
    with Path(path).open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(raw)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


@contextmanager
def issue_lock(base, date):
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(base, 0o700)
    # Keep the lock inode; unlinking it permits another process to lock a new inode.
    with (base / f".lock-{date}").open("a") as stream:
        os.chmod(stream.name, 0o600)
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise DeliveryError("delivery_busy") from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def readiness(as_of, window, now):
    try:
        timestamp = parse_published_at(as_of)
    except DigestTimeError:
        return "review-only", "archive_as_of_unknown"
    if timestamp > now:
        return "review-only", "archive_as_of_future"
    if timestamp < window.end_utc:
        return "review-only", "archive_before_cutoff"
    if now - timestamp > timedelta(minutes=90):
        return "review-only", "archive_stale"
    return "ready-for-review", "archive_recent_after_cutoff"


def code_provenance():
    root = Path(__file__).resolve().parents[1]
    names = sorted(root.glob("scripts/digest_*.py")) + [
        root / "scripts/generate_digest.py", root / "scripts/deliver_digest.py",
        root / "scripts/update_news.py", root / "scripts/archive_output.py",
    ]
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    return {"local_head": head, "entrypoint_module_sha256": hashes}


def deliver(base, window, *, get=public_get, clock=lambda: datetime.now(timezone.utc)):
    """Serialize one issue, verify staging, publish a new immutable version dir.

    Failed/review-only attempts remain private diagnostics. A crash before the
    directory rename cannot expose a new normal delivery. No durability claim.
    """
    base = Path(base)
    with issue_lock(base, window.date):
        attempt = base / ".attempts" / uuid4().hex
        attempt.mkdir(parents=True, mode=0o700)
        os.chmod(attempt.parent, 0o700)
        inputs = attempt / "inputs"
        inputs.mkdir(mode=0o700)
        manifest = {"date": window.date, "status": "failed", "reason": "delivery_failed",
                    "started_at": clock().isoformat(), "source_repository": REPO,
                    "input_sha256": {}}
        result_path = None
        try:
            manifest["code"] = code_provenance()
            commit = resolve_commit(get)
            manifest["source_commit"] = commit
            for name in INPUT_NAMES:
                try:
                    raw = get(f"https://api.github.com/repos/{REPO}/contents/data/{name}?ref={commit}")
                except DeliveryError as exc:
                    if name != "archive.json" and str(exc) == "not_found":
                        manifest["input_sha256"][name] = None
                        continue
                    raise
                private_write(inputs / name, raw)
                manifest["input_sha256"][name] = hashlib.sha256(raw).hexdigest()
            snapshot = load_digest_input(inputs)
            document = build_digest_document(snapshot, window)
            staging = attempt / "pair"
            staging.mkdir(mode=0o700)
            pair = write_digest(document, staging)
            for path in pair:
                os.chmod(path, 0o600)
            verified = verify_digest_pair(*pair)
            as_of = snapshot.inputs[0].producer_as_of
            now = clock()
            status, reason = readiness(as_of, window, now)
            manifest.update(status=status, reason=reason, archive_as_of=as_of,
                            completed_at=now.isoformat(), identity=verified["input_identity"],
                            selected_count=verified["selection_counts"]["selected_count"],
                            warnings=[diagnostic.code for diagnostic in snapshot.diagnostics])
            if status == "ready-for-review":
                issue = base / window.date
                issue.mkdir(mode=0o700, exist_ok=True)
                os.chmod(issue, 0o700)
                target = issue / verified["input_identity"]
                if target.exists():
                    previous = verify_digest_pair(target / pair[0].name, target / pair[1].name)
                    if previous != verified:
                        raise DeliveryError("existing_delivery_mismatch")
                    # Do not touch a previous manifest or any human review file.
                else:
                    private_write(staging / "delivery.json", json_bytes(manifest))
                    staging.rename(target)
                result_path = target
            else:
                private_write(staging / "delivery.json", json_bytes(manifest))
                result_path = staging
        except Exception as exc:
            # Fixed allowlist only, no filesystem/payload/network text in reports.
            allowed = {"not_found", "download_failed", "download_too_large",
                       "invalid_remote_commit", "existing_delivery_mismatch"}
            reason = str(exc) if isinstance(exc, DeliveryError) and str(exc) in allowed else "delivery_failed"
            manifest.update(status="failed", reason=reason, completed_at=clock().isoformat())
        private_write(attempt / "attempt.json", json_bytes(manifest))
        return manifest, result_path, attempt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Privately deliver a digest from pinned public GitHub data.")
    parser.add_argument("--date", required=True, help="explicit Taipei issue date YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path,
                        default=Path.home() / "Downloads" / "ai-news-radar-digests")
    args = parser.parse_args(argv)
    try:
        window = window_for_date(args.date)
    except DigestTimeError:
        parser.error("date must be a valid YYYY-MM-DD calendar date")
    base = args.output_dir.resolve()
    downloads = (Path.home() / "Downloads").resolve()
    if downloads not in base.parents:
        parser.error("private delivery directory must be a subdirectory of Downloads")
    try:
        manifest, result, attempt = deliver(base, window)
    except Exception:
        print("digest_delivery_failed: busy or private output unavailable", file=sys.stderr)
        return 1
    print(f"digest_delivery: {window.date} {manifest['status']} {manifest['reason']}")
    print(f"attempt: {attempt}")
    if result:
        print(f"pair: {result}")
    return {"ready-for-review": 0, "review-only": 3, "failed": 1}[manifest["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
