"""C03 synthetic offline contract cases; no private inputs or live source calls."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import socket
import subprocess
from uuid import uuid4

import pytest

from scripts import digest_cloud_prepare as prep
from scripts.digest_input import INPUT_NAMES
from scripts.digest_window import window_for_date


D = "2026-10-09"
COMMIT = "a" * 40
NOW = datetime(2026, 10, 8, 23, 45, tzinfo=timezone.utc)
ISSUERS = frozenset({"simulated-scheduler", "simulated-owner"})


def intent(**changes):
    value = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": D,
             "mode": "scheduled", "scheduled_for": "2026-10-08T23:15:00Z",
             "issued_at": "2026-10-08T23:15:03Z", "issuer_id": "simulated-scheduler",
             "owner_authorized": False}
    value.update(changes)
    return value


def pins(*, archive=None, cache=b"{}", health=None, commit=COMMIT):
    if archive is None:
        archive = json.dumps({"items": [], "generated_at": "2026-10-09T00:30:00Z"}).encode()
    if health is None:
        health = json.dumps({"generated_at": "2026-10-09T00:30:00Z", "sites": []}).encode()
    content = {"archive.json": archive, "title-zh-cache.json": cache, "source-status.json": health}
    return prep.PinnedInputs(commit, content,
                             {name: hashlib.sha256(raw).hexdigest() if raw is not None else None
                              for name, raw in content.items()},
                             {name: commit for name in INPUT_NAMES})


def run(tmp_path, request=None, source=None, clock=None):
    return prep.prepare_generation(request or intent(), source or pins(),
                                   clock or (lambda: NOW), tmp_path, trusted_issuer_ids=ISSUERS)


def test_f01_f03_window_frozen_despite_late_start(tmp_path):
    window = window_for_date(D)
    assert window.start_utc.isoformat() == "2026-10-07T22:00:00+00:00"
    assert window.end_utc.isoformat() == "2026-10-08T22:00:00+00:00"
    assert window.contains(window.start_utc) and not window.contains(window.end_utc)
    result = run(tmp_path)
    assert result.issue_date == D and result.selected_count == 0
    assert result.pair_verified and result.rerun_identical
    assert result.source_commit == COMMIT and result.prepared_at == NOW.isoformat().replace("+00:00", "Z")
    assert not list(tmp_path.glob("c03-*"))


@pytest.mark.parametrize("changes", [
    {"issue_date": None}, {"issue_date": "2026-02-30"},
    {"scheduled_for": "2026-10-09T07:15:00"},
    {"scheduled_for": "2026-10-08T23:15:00+00:00"},
    {"scheduled_for": "2026-10-08T23:16:00Z"},
    {"scheduled_for": None}, {"issued_at": "2026-10-08T23:30:00.000001Z"},
    {"scheduled_for": "2026-10-09T00:15:00Z", "issued_at": "2026-10-09T00:15:01Z"},
    {"issue_date": "2026-10-08"}, {"schema_version": True}, {"extra": "ignored"},
])
def test_f02_f06_invalid_intent_has_no_output(tmp_path, changes):
    with pytest.raises(prep.PreparationError) as exc:
        run(tmp_path, request=intent(**changes))
    assert exc.value.code == "invalid_request"
    assert not list(tmp_path.iterdir())


def test_f04_cross_day_before_or_after_generation(tmp_path):
    next_day = datetime(2026, 10, 9, 16, tzinfo=timezone.utc)
    with pytest.raises(prep.PreparationError, match="missed_issue"):
        run(tmp_path, clock=lambda: next_day)
    assert not list(tmp_path.iterdir())
    ticks = iter((NOW, next_day))
    with pytest.raises(prep.PreparationError, match="missed_issue"):
        run(tmp_path, clock=lambda: next(ticks))
    assert not list(tmp_path.glob("c03-*"))


def test_f05_historical_requires_owner_and_explicit_date(tmp_path):
    later = NOW + timedelta(days=2)
    historical = intent(mode="manual_historical", scheduled_for=None,
                        issuer_id="simulated-owner", owner_authorized=True,
                        issued_at="2026-10-10T00:00:00Z")
    with pytest.raises(prep.PreparationError, match="unauthorized"):
        run(tmp_path, request={**historical, "owner_authorized": False}, clock=lambda: later)
    result = run(tmp_path, request=historical, clock=lambda: later)
    assert result.mode == "manual_historical" and result.issue_date == D


def test_f06_unknown_issuer_is_rejected(tmp_path):
    with pytest.raises(prep.PreparationError, match="unauthorized"):
        run(tmp_path, request=intent(issuer_id="forged-scheduler"))


def test_f07_same_bytes_and_identity_f08_changed_input(tmp_path):
    first = run(tmp_path)
    second = run(tmp_path)
    assert (first.markdown, first.metadata, first.base_identity) == (
        second.markdown, second.metadata, second.base_identity)
    changed = pins(cache=b'{"unused":"translation"}')
    third = run(tmp_path, source=changed)
    assert third.base_identity != first.base_identity
    assert first.markdown == second.markdown


def test_f09_missing_archive_bad_hash_and_mixed_commit(tmp_path):
    base = pins()
    for source in (
        prep.PinnedInputs(COMMIT, {**base.content, "archive.json": None},
                          {**base.sha256, "archive.json": None}, base.source_commits),
        prep.PinnedInputs(COMMIT, base.content, {**base.sha256, "archive.json": "b" * 64}, base.source_commits),
        prep.PinnedInputs(COMMIT, base.content, base.sha256,
                          {**base.source_commits, "source-status.json": "b" * 40}),
    ):
        with pytest.raises(prep.PreparationError):
            run(tmp_path, source=source)
    assert not list(tmp_path.iterdir())


def test_f10_optional_missing_and_invalid_are_diagnostic(tmp_path):
    missing = run(tmp_path, source=pins(cache=None))
    invalid = run(tmp_path, source=pins(cache=b"invalid-json"))
    assert missing.input_sha256["title-zh-cache.json"] is None
    assert "optional_missing" in missing.diagnostic_codes
    assert invalid.input_sha256["title-zh-cache.json"] == hashlib.sha256(b"invalid-json").hexdigest()
    assert "optional_invalid" in invalid.diagnostic_codes


def test_f34_workspace_outside_downloads_and_unknown_pin_fields_rejected(tmp_path):
    with pytest.raises(prep.PreparationError, match="invalid_request"):
        prep.prepare_generation(intent(), pins(), lambda: NOW, Path("/private/tmp/c03-outside-downloads"),
                                trusted_issuer_ids=ISSUERS)
    source = pins()
    with pytest.raises(prep.PreparationError, match="invalid_request"):
        run(tmp_path, source=prep.PinnedInputs(COMMIT, {**source.content, "extra": b"secret"},
                                              source.sha256, source.source_commits))


def test_f35_exception_text_is_not_exposed(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("SECRET fake-token private-path draft-text")
    monkeypatch.setattr(prep, "build_digest_document", broken)
    with pytest.raises(prep.PreparationError) as exc:
        run(tmp_path)
    assert str(exc.value) == "generation_failed"
    assert not list(tmp_path.glob("c03-*"))


def test_f36_network_and_subprocess_attempts_fail_hard(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network_or_subprocess_called")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "check_output", forbidden)
    assert run(tmp_path).pair_verified


def test_prepared_pair_is_not_delivery_receipt(tmp_path):
    prepared = run(tmp_path)
    assert not hasattr(prepared, "quality")
    assert not hasattr(prepared, "timeliness")
    assert not hasattr(prepared, "delivery_id")
