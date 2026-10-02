"""Private delivery: pinned reads, freshness, process lock and failure isolation."""

from datetime import datetime, timedelta, timezone
import json
import stat
import subprocess
from types import SimpleNamespace

import pytest

from scripts import deliver_digest as delivery
from scripts.digest_window import window_for_date
from scripts.generate_digest import verify_digest_pair


WINDOW = window_for_date("2026-10-03")
NOW = datetime(2026, 10, 2, 23, 15, tzinfo=timezone.utc)
AS_OF = "2026-10-02T22:05:00Z"
COMMIT = "c" * 40


def remote(*, as_of=AS_OF, optional=True, bad_archive=False):
    calls = []
    def get(url):
        calls.append(url)
        if url.endswith("/git/ref/heads/master"):
            return json.dumps({"object": {"sha": COMMIT}}).encode()
        assert url.endswith(f"?ref={COMMIT}")
        name = url.split("?", 1)[0].rsplit("/", 1)[-1]
        if name == "archive.json":
            return b"bad SECRET" if bad_archive else json.dumps({"items": [], "generated_at": as_of}).encode()
        if not optional:
            raise delivery.DeliveryError("not_found")
        return b"{}" if name == "title-zh-cache.json" else json.dumps({"generated_at": as_of, "sites": []}).encode()
    return get, calls


def run(base, **kwargs):
    get, calls = remote(**kwargs)
    return delivery.deliver(base, WINDOW, get=get, clock=lambda: NOW), calls


def test_pinned_public_reads_empty_day_and_private_files(tmp_path):
    (manifest, pair, attempt), calls = run(tmp_path / "delivery")
    assert len(calls) == 4 and calls[0].endswith("/heads/master")
    assert manifest["status"] == "ready-for-review"
    assert manifest["source_commit"] == COMMIT and manifest["selected_count"] == 0
    assert pair.parent.name == WINDOW.date
    verified = verify_digest_pair(pair / "digest-2026-10-03.md", pair / "digest-2026-10-03.meta.json")
    assert verified["input_identity"] == pair.name
    assert len(manifest["input_sha256"]) == 3
    assert (attempt / "inputs/archive.json").exists()
    assert not (pair / "archive.json").exists()
    for path in (tmp_path / "delivery").rglob("*"):
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == (0o700 if path.is_dir() else 0o600), path


@pytest.mark.parametrize("as_of,reason", [
    (None, "archive_as_of_unknown"),
    ("2026-10-02T21:59:59Z", "archive_before_cutoff"),
    ("2026-10-02T23:15:01Z", "archive_as_of_future"),
])
def test_review_only_does_not_publish_normal_issue(tmp_path, as_of, reason):
    (manifest, pair, attempt), _ = run(tmp_path / "delivery", as_of=as_of)
    assert manifest["status"] == "review-only" and manifest["reason"] == reason
    assert pair == attempt / "pair"
    assert not (tmp_path / "delivery" / WINDOW.date).exists()


def test_freshness_boundary_and_end_of_generation_clock():
    as_of = "2026-10-02T22:00:00Z"
    at90 = WINDOW.end_utc + timedelta(minutes=90)
    assert delivery.readiness(as_of, WINDOW, at90)[0] == "ready-for-review"
    assert delivery.readiness(as_of, WINDOW, at90 + timedelta(microseconds=1)) == ("review-only", "archive_stale")


def test_download_and_generation_time_can_expire_snapshot(tmp_path):
    get, _ = remote()
    times = iter([NOW, NOW + timedelta(hours=1)])
    manifest, pair, attempt = delivery.deliver(tmp_path / "delivery", WINDOW, get=get, clock=lambda: next(times))
    assert manifest["reason"] == "archive_stale"
    assert pair == attempt / "pair"


def test_optional_missing_degrades_but_transport_failure_is_fatal(tmp_path):
    (manifest, _, _), _ = run(tmp_path / "missing", optional=False)
    assert manifest["status"] == "ready-for-review"
    assert "optional_missing" in manifest["warnings"]
    get, _ = remote()
    def broken(url):
        if "/source-status.json?" in url:
            raise delivery.DeliveryError("download_failed")
        return get(url)
    manifest, pair, attempt = delivery.deliver(tmp_path / "broken", WINDOW, get=broken, clock=lambda: NOW)
    assert manifest["status"] == "failed" and pair is None
    assert (attempt / "attempt.json").exists()


def test_rerun_preserves_human_review_and_existing_manifest(tmp_path):
    (first, pair, _), _ = run(tmp_path / "delivery")
    review = pair / "review.md"
    review.write_text("human edits")
    old_manifest = (pair / "delivery.json").read_bytes()
    (second, again, _), _ = run(tmp_path / "delivery")
    assert pair == again and first["identity"] == second["identity"]
    assert review.read_text() == "human edits"
    assert (pair / "delivery.json").read_bytes() == old_manifest


def test_tampered_existing_pair_is_not_overwritten(tmp_path):
    (_, pair, _), _ = run(tmp_path / "delivery")
    md = pair / "digest-2026-10-03.md"
    md.write_text("human changed original")
    (manifest, target, attempt), _ = run(tmp_path / "delivery")
    assert manifest["status"] == "failed" and target is None
    assert md.read_text() == "human changed original"
    assert not (attempt / "pair/delivery.json").exists()


def test_same_issue_locked_before_any_network(tmp_path):
    base = tmp_path / "delivery"
    def forbidden(url):
        pytest.fail("network while locked")
    with delivery.issue_lock(base, WINDOW.date):
        with pytest.raises(delivery.DeliveryError, match="delivery_busy"):
            delivery.deliver(base, WINDOW, get=forbidden)
    # inode remains available after release
    assert run(base)[0][0]["status"] == "ready-for-review"


def test_second_pair_write_failure_preserves_success_and_hides_error(tmp_path, monkeypatch):
    (_, pair, _), _ = run(tmp_path / "delivery")
    old = (pair / "digest-2026-10-03.md").read_bytes()
    from scripts import generate_digest
    original = generate_digest.atomic_write_text
    def fail(path, text):
        if str(path).endswith(".meta.json"):
            raise OSError("SECRET credentials")
        original(path, text)
    monkeypatch.setattr(generate_digest, "atomic_write_text", fail)
    (manifest, target, attempt), _ = run(tmp_path / "delivery")
    assert manifest["status"] == "failed" and target is None
    assert "SECRET" not in (attempt / "attempt.json").read_text()
    assert (pair / "digest-2026-10-03.md").read_bytes() == old


def test_bad_archive_or_remote_commit_fails_safely(tmp_path):
    (manifest, pair, attempt), _ = run(tmp_path / "archive", bad_archive=True)
    assert manifest["status"] == "failed" and pair is None
    assert "SECRET" not in (attempt / "attempt.json").read_text()
    manifest, _, _ = delivery.deliver(tmp_path / "ref", WINDOW, get=lambda _: b'{"object":{"sha":"../bad"}}', clock=lambda: NOW)
    assert manifest["reason"] == "invalid_remote_commit"


def test_cli_explicit_date_and_downloads_boundary_before_get(tmp_path, monkeypatch):
    monkeypatch.setattr(delivery.Path, "home", lambda: tmp_path)
    with pytest.raises(SystemExit) as result:
        delivery.main([])
    assert result.value.code == 2
    with pytest.raises(SystemExit) as result:
        delivery.main(["--date", WINDOW.date, "--output-dir", str(tmp_path / "other")])
    assert result.value.code == 2


@pytest.mark.parametrize("status,exit_code", [("ready-for-review", 0), ("review-only", 3), ("failed", 1)])
def test_cli_status_codes(tmp_path, monkeypatch, status, exit_code):
    monkeypatch.setattr(delivery.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(delivery, "deliver", lambda *a: ({"status": status, "reason": "safe"}, None, tmp_path))
    assert delivery.main(["--date", WINDOW.date]) == exit_code


@pytest.mark.parametrize("stdout,returncode,expected", [
    (b"payload200", 0, b"payload"), (b"404", 22, "not_found"),
    (b"SECRET403", 22, "download_failed"), (b"redirect301", 0, "download_failed"),
])
def test_public_get_bounds_and_http_errors(monkeypatch, stdout, returncode, expected):
    def fake(argv, **kwargs):
        assert argv[:2] == ["curl", "--disable"]  # no user curlrc credentials/options
        assert "--max-time" in argv and "--max-filesize" in argv
        assert kwargs["timeout"] == 50
        return SimpleNamespace(stdout=stdout, returncode=returncode)
    monkeypatch.setattr(delivery.subprocess, "run", fake)
    if isinstance(expected, bytes):
        assert delivery.public_get("https://example.invalid") == expected
    else:
        with pytest.raises(delivery.DeliveryError, match=expected):
            delivery.public_get("https://example.invalid")


def test_public_get_hard_deadline_sanitizes_exception(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("SECRET", 50)
    monkeypatch.setattr(delivery.subprocess, "run", timeout)
    with pytest.raises(delivery.DeliveryError, match="^download_failed$"):
        delivery.public_get("https://example.invalid")
