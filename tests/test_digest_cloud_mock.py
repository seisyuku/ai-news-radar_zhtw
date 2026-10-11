"""C04 fault and concurrency tests for the local-only cloud delivery simulation."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import socket
import subprocess
from threading import Barrier, Lock
from uuid import uuid4

import pytest

from scripts.digest_cloud_prepare import PinnedInputs, prepare_generation
from scripts.digest_cloud_mock import (DeliveryRequest, MemoryControl, MemoryObjectStore,
                                       MockDeliveryError, MockDeliveryService)
from scripts.digest_input import INPUT_NAMES


D = "2026-10-09"
COMMIT = "a" * 40
PREPARE_AT = datetime(2026, 10, 9, 0, 45, tzinfo=timezone.utc)
ISSUERS = frozenset({"simulated-scheduler", "simulated-owner"})


def prepared(workspace, *, as_of="2026-10-09T00:30:00Z", cache=b"{}", items=(),
             slot="2026-10-08T23:15:00Z", mode="scheduled", prepare_started_at=None):
    archive = json.dumps({"items": list(items), "generated_at": as_of}).encode()
    health = json.dumps({"generated_at": as_of, "sites": []}).encode()
    content = {"archive.json": archive, "title-zh-cache.json": cache, "source-status.json": health}
    source = PinnedInputs(COMMIT, content,
                          {name: hashlib.sha256(raw).hexdigest() if raw is not None else None
                           for name, raw in content.items()},
                          {name: COMMIT for name in INPUT_NAMES})
    request = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": D, "mode": mode,
               "scheduled_for": slot if mode == "scheduled" else None,
               "issued_at": (datetime.fromisoformat(slot.replace("Z", "+00:00")) + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
               if mode == "scheduled" else "2026-10-08T23:15:01Z", "issuer_id": "simulated-scheduler"
               if mode == "scheduled" else "simulated-owner", "owner_authorized": mode != "scheduled"}
    times = iter((prepare_started_at or PREPARE_AT, PREPARE_AT))
    return prepare_generation(request, source, lambda: next(times), workspace,
                              trusted_issuer_ids=ISSUERS)


def attempt(pair, *, execution_count=1):
    return DeliveryRequest(1, pair.request_id, str(uuid4()), pair.issue_date, execution_count)


def service(tmp_path, now=PREPARE_AT):
    objects = MemoryObjectStore()
    control = MemoryControl(lambda: now)
    return MockDeliveryService(objects, control, tmp_path)


class RacingControl(MemoryControl):
    def __init__(self):
        super().__init__(lambda: PREPARE_AT)
        self.barrier = Barrier(2)
        self.calls_lock = Lock()
        self.calls = 0

    def commit_delivery(self, *args):
        with self.calls_lock:
            self.calls += 1
            synchronize = self.calls <= 2
        if synchronize:
            self.barrier.wait(timeout=3)
        return super().commit_delivery(*args)


def test_f11_f20_new_delivery_and_repeat_same_base_keep_single_revision(tmp_path):
    pair = prepared(tmp_path)
    target = service(tmp_path)
    first = target.commit_delivery(pair, attempt(pair))
    assert first["quality"] == "ready-for-review" and first["timeliness"] == "on_time"
    assert first["selected_count"] == 0 and first["pair_verified"] and first["rerun_identical"]
    assert target.get_issue(D)["meets_daily_target"]
    read = target.read_base(D, pair.base_identity)
    assert read["markdown"] == pair.markdown and read["integrity"] == "verified"
    second = prepared(tmp_path, slot="2026-10-09T00:15:00Z")
    target.commit_delivery(second, attempt(second))
    state = target.control.get_issue(D)
    assert len(state["delivery_ids"]) == 2
    assert len(state["reviews"][pair.base_identity]) == 1
    assert state["selected_base"] == pair.base_identity
    assert state["review_heads"][pair.base_identity] == 0


def test_f11_two_synthetic_stories_create_addressable_revision_zero(tmp_path):
    originals = [
        {"id": "one", "site_id": "official_ai", "source": "OpenAI News",
         "title": "OpenAI releases new Codex model for developers",
         "url": "https://example.invalid/one", "published_at": "2026-10-08T10:00:00Z",
         "summary": "OpenAI released a new Codex model for developers."},
        {"id": "two", "site_id": "curated_media", "source": "Other Publisher",
         "title": "Anthropic releases new Claude model for business",
         "url": "https://example.invalid/two", "published_at": "2026-10-08T11:00:00Z",
         "summary": "Anthropic released a new Claude model for business."},
    ]
    items = originals + [{**row, "id": row["id"] + "-corroboration",
                          "site_id": "curated_media" if row["site_id"] == "official_ai" else "official_ai",
                          "source": "Independent Publisher",
                          "url": row["url"] + "/corroboration"} for row in originals]
    pair = prepared(tmp_path, items=items)
    target = service(tmp_path)
    row = target.commit_delivery(pair, attempt(pair))
    review = target.control.get_issue(D)["reviews"][pair.base_identity][0]["content"]
    assert row["selected_count"] == 2
    assert len(review["ordered_story_ids"]) == 2
    assert len(set(review["ordered_story_ids"])) == 2


def test_f12_f13_f14_f16_freshness_is_decided_at_transaction(tmp_path):
    at90 = datetime(2026, 10, 9, 1, 30, tzinfo=timezone.utc)
    for idx, (as_of, committed, quality, reason) in enumerate((
        ("2026-10-09T00:00:00Z", at90, "ready-for-review", "archive_recent_after_cutoff"),
        ("2026-10-09T00:00:00Z", at90 + timedelta(microseconds=1), "review-only", "archive_stale"),
        ("2026-10-09T01:30:01Z", at90, "review-only", "archive_as_of_future"),
        ("2026-10-08T21:59:59Z", at90, "review-only", "archive_before_cutoff"),
        (None, at90, "review-only", "archive_as_of_unknown"),
        ("2026-10-09T00:30:00Z", datetime(2026, 10, 9, 1, 1, tzinfo=timezone.utc),
         "ready-for-review", "archive_recent_after_cutoff"),
    )):
        pair = prepared(tmp_path / str(idx), as_of=as_of)
        target = service(tmp_path / str(idx), committed)
        row = target.commit_delivery(pair, attempt(pair))
        assert (row["quality"], row["reason_code"]) == (quality, reason)
        assert row["checked_at"] != row["committed_at"]
        assert target.get_issue(D)["meets_daily_target"] is False


def test_f15_deadline_exact_and_one_microsecond_late(tmp_path):
    for idx, (clock, expected) in enumerate((
        (datetime(2026, 10, 9, 1, tzinfo=timezone.utc), "on_time"),
        (datetime(2026, 10, 9, 1, 0, 0, 1, tzinfo=timezone.utc), "late"),
    )):
        pair = prepared(tmp_path / str(idx), as_of="2026-10-09T00:30:00Z")
        target = service(tmp_path / str(idx), clock)
        row = target.commit_delivery(pair, attempt(pair))
        assert row["quality"] == "ready-for-review" and row["timeliness"] == expected
        assert target.get_issue(D)["meets_daily_target"] == (expected == "on_time")


def test_f16_early_start_but_0901_commit_is_stale_and_late(tmp_path):
    pair = prepared(tmp_path, as_of="2026-10-08T23:30:00Z",
                    prepare_started_at=datetime(2026, 10, 8, 23, 15, 2, tzinfo=timezone.utc))
    target = service(tmp_path, datetime(2026, 10, 9, 1, 1, tzinfo=timezone.utc))
    row = target.commit_delivery(pair, attempt(pair))
    assert row["checked_at"] == "2026-10-09T00:45:00Z"
    assert target.control.get_issue(D)["attempts"][row["attempt_id"]]["started_at"] == "2026-10-08T23:15:02Z"
    assert (row["quality"], row["reason_code"], row["timeliness"]) == (
        "review-only", "archive_stale", "late")
    assert not target.get_issue(D)["meets_daily_target"]


def test_f04_commit_crosses_issue_day_without_delivery(tmp_path):
    pair = prepared(tmp_path)
    target = service(tmp_path, datetime(2026, 10, 9, 16, tzinfo=timezone.utc))
    result = target.commit_delivery(pair, attempt(pair))
    assert result["status"] == "missed_issue"
    assert target.control.get_issue(D)["delivery_ids"] == []
    assert target.get_issue(D)["latest_attempt"]["state"] == "missed_issue"


def test_f17_second_upload_failure_then_recover_same_attempt(tmp_path):
    pair = prepared(tmp_path)
    target = service(tmp_path)
    request = attempt(pair)
    def fail_meta(key, _):
        if key.endswith("meta.json"):
            raise RuntimeError("SECRET_PRIVATE_DRAFT")
    target.objects.before_put = fail_meta
    with pytest.raises(MockDeliveryError, match="storage_failed"):
        target.commit_delivery(pair, request)
    assert target.control.get_issue(D)["delivery_ids"] == []
    assert len(target.objects._objects) == 1
    assert target.get_issue(D)["latest_attempt"]["state"] == "running"
    assert target.get_issue(D)["latest_attempt"]["reason_code"] == "storage_failed"
    target.objects.before_put = None
    with pytest.raises(MockDeliveryError, match="idempotency_conflict"):
        target.commit_delivery(pair, attempt(pair))
    result = target.commit_delivery(pair, replace(request, execution_count=2))
    assert result["quality"] == "ready-for-review" and len(target.objects._objects) == 2


def test_f18_readback_corruption_and_control_failure_preserve_old(tmp_path):
    first = prepared(tmp_path)
    target = service(tmp_path)
    initial = target.commit_delivery(first, attempt(first))
    second = prepared(tmp_path, cache=b'{"unused":"new"}', slot="2026-10-09T00:15:00Z")
    target.objects.before_get = lambda key: (_ for _ in ()).throw(RuntimeError("SECRET")) if key.endswith("meta.json") else None
    retry = attempt(second)
    with pytest.raises(MockDeliveryError, match="integrity_error"):
        target.commit_delivery(second, retry)
    assert target.control.get_issue(D)["delivery_ids"] == [initial["delivery_id"]]
    target.objects.before_get = None
    target.control.fail_next_commit = True
    with pytest.raises(MockDeliveryError, match="storage_failed"):
        target.commit_delivery(second, replace(retry, execution_count=2))
    assert target.control.get_issue(D)["selected_base"] == first.base_identity
    assert target.control.get_issue(D)["delivery_ids"] == [initial["delivery_id"]]


def test_f19_immutable_conflict_never_overwrites(tmp_path):
    pair = prepared(tmp_path)
    target = service(tmp_path)
    key = target._keys(D, pair.base_identity)["md"]
    target.objects.put_if_absent(key, b"another original")
    with pytest.raises(MockDeliveryError, match="immutable_conflict"):
        target.commit_delivery(pair, attempt(pair))
    assert target.objects.get(key) == b"another original"
    assert target.control.get_issue(D)["delivery_ids"] == []


def test_f20_two_runners_same_base_concurrent(tmp_path):
    target = MockDeliveryService(MemoryObjectStore(), RacingControl(), tmp_path)
    pairs = [prepared(tmp_path), prepared(tmp_path, slot="2026-10-09T00:15:00Z")]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda pair: target.commit_delivery(pair, attempt(pair)), pairs))
    state = target.control.get_issue(D)
    assert len({row["delivery_id"] for row in results}) == 2
    assert len(state["reviews"][pairs[0].base_identity]) == 1


def test_f21_different_base_does_not_switch_selection(tmp_path):
    first = prepared(tmp_path)
    second = prepared(tmp_path, cache=b'{"unused":"new"}', slot="2026-10-09T00:15:00Z")
    target = service(tmp_path)
    target.commit_delivery(first, attempt(first))
    target.commit_delivery(second, attempt(second))
    state = target.control.get_issue(D)
    assert state["selected_base"] == first.base_identity
    assert set(state["review_heads"]) == {first.base_identity, second.base_identity}
    assert len(state["delivery_ids"]) == 2


def test_f21_two_different_bases_concurrently_select_only_one(tmp_path):
    first = prepared(tmp_path)
    second = prepared(tmp_path, cache=b'{"unused":"new"}', slot="2026-10-09T00:15:00Z")
    target = MockDeliveryService(MemoryObjectStore(), RacingControl(), tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda pair: target.commit_delivery(pair, attempt(pair)), (first, second)))
    state = target.control.get_issue(D)
    assert len(rows) == 2 and state["selected_base"] in {first.base_identity, second.base_identity}
    assert len(state["review_heads"]) == 2


def test_explicit_control_version_checks_before_beginning_and_at_commit(tmp_path):
    first = prepared(tmp_path)
    target = service(tmp_path)
    row = target.commit_delivery(first, attempt(first), expected_control_version=0)
    assert row["quality"] == "ready-for-review"
    second = prepared(tmp_path, slot="2026-10-09T00:15:00Z")
    before = target.control.get_issue(D)
    with pytest.raises(MockDeliveryError, match="revision_conflict"):
        target.commit_delivery(second, attempt(second), expected_control_version=0)
    assert target.control.get_issue(D) == before

    fresh = service(tmp_path / "race")
    pair = prepared(tmp_path / "race")
    request = attempt(pair)
    changed = False
    def simulate_other_writer(_):
        nonlocal changed
        if not changed:
            changed = True
            with fresh.control._lock:
                fresh.control._issues[D]["control_version"] += 1
    fresh.objects.before_get = simulate_other_writer
    with pytest.raises(MockDeliveryError, match="revision_conflict"):
        fresh.commit_delivery(pair, request, expected_control_version=0)
    state = fresh.control.get_issue(D)
    assert state["delivery_ids"] == []
    assert state["attempts"][request.attempt_id]["state"] == "failed"


def test_f22_lost_response_replay_uses_original_clock_and_receipt(tmp_path):
    pair = prepared(tmp_path)
    calls = iter([PREPARE_AT])
    target = MockDeliveryService(MemoryObjectStore(), MemoryControl(lambda: next(calls)), tmp_path)
    request = attempt(pair)
    first = target.commit_delivery(pair, request)
    second = target.commit_delivery(pair, request)
    assert first == second
    assert len(target.control.get_issue(D)["delivery_ids"]) == 1
    with pytest.raises(MockDeliveryError, match="idempotency_conflict"):
        target.commit_delivery(replace(pair, source_commit="b" * 40), request)


def test_f23_later_failure_does_not_erase_ready_or_review(tmp_path):
    first = prepared(tmp_path)
    target = service(tmp_path)
    target.commit_delivery(first, attempt(first))
    second = prepared(tmp_path, cache=b'{"unused":"new"}', slot="2026-10-09T00:15:00Z")
    target.objects.before_put = lambda key, _: (_ for _ in ()).throw(RuntimeError("SECRET"))
    with pytest.raises(MockDeliveryError):
        target.commit_delivery(second, attempt(second))
    assert target.get_issue(D)["meets_daily_target"]
    assert target.control.get_issue(D)["selected_base"] == first.base_identity
    assert len(target.control.get_issue(D)["reviews"][first.base_identity]) == 1


def test_f24_corrupt_read_is_not_exposed_as_ready(tmp_path):
    pair = prepared(tmp_path)
    target = service(tmp_path)
    target.commit_delivery(pair, attempt(pair))
    target.objects._objects[target._keys(D, pair.base_identity)["md"]] = b"tampered"
    with pytest.raises(MockDeliveryError, match="integrity_error"):
        target.read_base(D, pair.base_identity)
    assert target.get_issue(D)["integrity"] == "integrity_error"
    assert not target.get_issue(D)["meets_daily_target"]


def test_f25_duplicate_slot_and_fourth_execution_rejected(tmp_path):
    first = prepared(tmp_path)
    target = service(tmp_path)
    target.commit_delivery(first, attempt(first))
    duplicate = prepared(tmp_path)
    with pytest.raises(MockDeliveryError, match="attempt_limit"):
        target.commit_delivery(duplicate, attempt(duplicate))
    newer = prepared(tmp_path, slot="2026-10-09T00:15:00Z")
    with pytest.raises(MockDeliveryError, match="attempt_limit"):
        target.commit_delivery(newer, attempt(newer, execution_count=4))
    assert len(target.control.get_issue(D)["delivery_ids"]) == 1


def test_f34_f35_f36_invalid_request_safe_error_and_no_network(tmp_path, monkeypatch):
    pair = prepared(tmp_path)
    target = service(tmp_path)
    request = attempt(pair)
    with pytest.raises(MockDeliveryError, match="invalid_request"):
        target.commit_delivery(pair, replace(request, schema_version=True))
    assert target.control.get_issue(D)["delivery_ids"] == []
    def forbidden(*args, **kwargs):
        raise AssertionError("network_or_subprocess_called")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "check_output", forbidden)
    assert target.commit_delivery(pair, request)["quality"] == "ready-for-review"
