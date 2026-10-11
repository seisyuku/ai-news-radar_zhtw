"""C08 generation-before guards, trusted dates, pinned commits and bounded retries."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.digest_cloud_jobs import MemoryJobCoordinator, public_job_summary
from scripts.digest_cloud_mock import MemoryControl, MemoryObjectStore, MockDeliveryService, MockDeliveryError
from scripts.digest_cloud_prepare import PinnedInputs, PreparationError
from scripts.digest_cloud_editorial import SimulatedOwnerPolicy, EditorialError
from test_digest_cloud_editorial import OWNER, two_story_items
from test_digest_cloud_mock import D, prepared, service, attempt


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 8, 23, 15, 1, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


def setup(tmp_path):
    clock = Clock()
    delivery = MockDeliveryService(MemoryObjectStore(), MemoryControl(clock), tmp_path)
    jobs = MemoryJobCoordinator(delivery, clock, owner_policy=SimulatedOwnerPolicy(), owner_id="owner")
    as_of = clock.now.isoformat().replace("+00:00", "Z")
    content = {"archive.json": json.dumps({"items": two_story_items(), "generated_at": as_of}).encode(),
               "source-status.json": json.dumps({"sites": [], "generated_at": as_of}).encode(),
               "title-zh-cache.json": b"{}"}

    def load(commit):
        return PinnedInputs(commit, content, {k: hashlib.sha256(v).hexdigest() for k, v in content.items()},
                            {k: commit for k in content})

    return clock, delivery, jobs, load


def test_issued_slot_is_fixed_and_duplicate_wakeup_reuses_persisted_intent(tmp_path):
    clock, _, jobs, _ = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    clock.now += timedelta(minutes=20)
    assert jobs.issue_slot("primary") == intent
    assert intent["issue_date"] == D and intent["scheduled_for"] == "2026-10-08T23:15:00Z"
    with pytest.raises(PreparationError, match="invalid_request"):
        jobs.issue_slot("final")


def test_unknown_request_and_cross_day_never_reach_loader(tmp_path):
    clock, _, jobs, _ = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    clock.now += timedelta(days=1)

    def forbidden(commit):
        pytest.fail("guard did not run before loader")

    assert jobs.run_job(str(uuid4()), str(uuid4()), "a" * 40, forbidden, tmp_path)["reason_code"] == "unauthorized"
    assert jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, forbidden, tmp_path)["reason_code"] == "missed_issue"


def test_success_skips_later_slot_before_loading_and_notification_is_once(tmp_path):
    clock, delivery, jobs, load = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    first = jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, load, tmp_path)
    assert first["status"] == "committed" and first["result"]["timeliness"] == "on_time"
    before = deepcopy(delivery.control.get_issue(D))
    assert jobs.notification_plan(D)["status"] == "delivered"
    assert jobs.notification_plan(D) is None
    clock.now += timedelta(hours=1)
    second = jobs.issue_slot("second")

    def forbidden(commit):
        pytest.fail("already ready still generated")

    assert jobs.run_job(second["request_id"], str(uuid4()), "b" * 40, forbidden, tmp_path)["status"] == "already_delivered"
    assert delivery.control.get_issue(D) == before


def test_active_claim_and_fourth_execution_are_rejected_before_generation(tmp_path):
    clock, _, jobs, _ = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    first_id = str(uuid4())
    first = jobs.claim(intent["request_id"], first_id, "a" * 40)
    assert jobs.claim(intent["request_id"], first_id, "b" * 40)["action"] == "in_progress"
    for count in (2, 3):
        clock.now += timedelta(minutes=11)
        claim = jobs.claim(intent["request_id"], str(uuid4()), "b" * 40)
        assert claim["execution_count"] == count and claim["source_commit"] == "a" * 40
    with pytest.raises(MockDeliveryError, match="attempt_limit"):
        jobs.authorize_commit(first, clock.now)
    clock.now += timedelta(minutes=11)

    def forbidden(commit):
        pytest.fail("fourth execution reached generation")

    assert jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, forbidden, tmp_path)["reason_code"] == "attempt_limit"


def test_resume_after_partial_upload_regenerates_same_bytes_with_pinned_commit(tmp_path):
    clock, delivery, jobs, load = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    delivery.objects.before_put = lambda key, _: (_ for _ in ()).throw(RuntimeError("PRIVATE")) if key.endswith("meta.json") else None
    first = jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, load, tmp_path)
    assert first == {"status": "failed", "reason_code": "storage_failed"}
    assert delivery.get_issue(D)["latest_attempt"]["state"] == "running"
    delivery.objects.before_put = None
    clock.now += timedelta(minutes=1)
    commits = []

    def resumed(commit):
        commits.append(commit)
        return load(commit)

    second = jobs.run_job(intent["request_id"], str(uuid4()), "b" * 40, resumed, tmp_path)
    assert second["status"] == "committed" and commits == ["a" * 40]
    assert delivery.get_issue(D)["latest_attempt"]["execution_count"] == 2
    assert len(delivery.objects._objects) == 2
    replay = jobs.run_job(intent["request_id"], str(uuid4()), "c" * 40,
                          lambda commit: pytest.fail("settled request loaded again"), tmp_path)
    assert replay["status"] == "receipt" and replay["result"] == second["result"]


def test_expired_during_upload_cannot_commit_and_can_resume_within_budget(tmp_path):
    clock, delivery, jobs, load = setup(tmp_path)
    intent = jobs.issue_slot("primary")

    def slow_upload(key, data):
        if key.endswith("meta.json"):
            clock.now += timedelta(minutes=11)

    delivery.objects.before_put = slow_upload
    failed = jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, load, tmp_path)
    assert failed["reason_code"] == "storage_failed"
    assert not delivery.control.get_issue(D)["delivery_ids"]
    delivery.objects.before_put = None
    assert jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, load, tmp_path)["status"] == "committed"


def test_manual_requests_need_owner_and_have_three_attempt_limit(tmp_path):
    _, _, jobs, _ = setup(tmp_path)
    with pytest.raises(EditorialError, match="unauthorized"):
        jobs.issue_manual(None, D, str(uuid4()))
    request_id = str(uuid4())
    first = jobs.issue_manual(OWNER, D, request_id)
    assert jobs.issue_manual(OWNER, D, request_id) == first
    for _ in range(2):
        jobs.issue_manual(OWNER, D, str(uuid4()))
    with pytest.raises(PreparationError, match="attempt_limit"):
        jobs.issue_manual(OWNER, D, str(uuid4()))
    with pytest.raises(PreparationError):
        jobs.issue_manual(OWNER, D, str(uuid4()), historical=True)


def test_failure_notification_waits_until_deadline_and_never_sends(tmp_path):
    clock, _, jobs, _ = setup(tmp_path)
    assert jobs.notification_plan(D) is None
    clock.now = datetime(2026, 10, 9, 1, 0, tzinfo=timezone.utc)
    planned = jobs.notification_plan(D)
    assert planned == {"issue_date": D, "status": "failed", "sent": False, "meets_daily_target": False}
    assert jobs.notification_plan(D) is None


def test_delivery_terminal_failure_cannot_restart_or_accept_fresh_preparation_time(tmp_path):
    pair = prepared(tmp_path)
    delivery = service(tmp_path)
    request = attempt(pair)
    delivery.objects.before_put = lambda *args: (_ for _ in ()).throw(RuntimeError("failure"))
    for count in (1, 2, 3):
        with pytest.raises(MockDeliveryError, match="storage_failed"):
            delivery.commit_delivery(pair, replace(request, execution_count=count))
    assert delivery.get_issue(D)["latest_attempt"]["state"] == "failed"
    delivery.objects.before_put = None
    with pytest.raises(MockDeliveryError, match="attempt_limit"):
        delivery.commit_delivery(replace(pair, started_at="2026-10-09T00:46:00Z"),
                                 replace(request, execution_count=3))


def test_simultaneous_claims_have_one_active_execution_and_forgery_is_denied(tmp_path):
    clock, _, jobs, _ = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: jobs.claim(intent["request_id"], str(uuid4()), "a" * 40), range(2)))
    assert sorted(x["action"] for x in claims) == ["generate", "in_progress"]
    claim = next(x for x in claims if x["action"] == "generate")
    claim["intent"]["mode"] = "manual_historical"
    with pytest.raises(MockDeliveryError, match="invalid_request"):
        jobs.authorize_commit(claim, clock.now)


def test_explicit_historical_manual_run_is_not_daily_success(tmp_path):
    clock, delivery, jobs, load = setup(tmp_path)
    clock.now += timedelta(days=1)
    intent = jobs.issue_manual(OWNER, D, str(uuid4()), historical=True)
    result = jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, load, tmp_path)
    assert result["status"] == "committed" and result["result"]["timeliness"] == "historical"
    assert not delivery.get_issue(D)["meets_daily_target"] and jobs.notification_plan(D) is None


def test_public_summary_is_rebuilt_without_private_outcome_fields(tmp_path):
    _, _, jobs, load = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    outcome = jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, load, tmp_path)
    outcome["private_exception"] = "SECRET /private/path full draft"
    outcome["result"]["objects"]["md"]["key"] = "SECRET_PRIVATE_URL"
    safe = public_job_summary(outcome)
    assert safe["status"] == "committed" and safe["issue_date"] == D
    assert safe["pair_verified"] and safe["rerun_identical"]
    assert "SECRET" not in json.dumps(safe) and "objects" not in safe


def test_job_receipt_survives_coordinator_response_record_failure(tmp_path, monkeypatch):
    _, delivery, jobs, load = setup(tmp_path)
    intent = jobs.issue_slot("primary")
    with monkeypatch.context() as patcher:
        patcher.setattr(jobs, "_finish", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("PRIVATE")))
        outcome = jobs.run_job(intent["request_id"], str(uuid4()), "a" * 40, load, tmp_path)
    assert outcome["status"] == "committed" and not outcome["coordination_recorded"]
    replay = jobs.run_job(intent["request_id"], str(uuid4()), "b" * 40,
                          lambda c: pytest.fail("saved receipt generated again"), tmp_path)
    assert replay["status"] == "receipt" and replay["result"] == outcome["result"]
    assert len(delivery.control.get_issue(D)["delivery_ids"]) == 1
