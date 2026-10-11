"""C08 offline coordinator: trusted intents and claims before generation.

This memory adapter proves orchestration rules. A deployed coordinator must
persist the same intent/claim/receipt operations and authenticate its issuers.
"""

from copy import deepcopy
from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
import re

from .digest_cloud_prepare import prepare_generation, _validate_intent, PreparationError
from .digest_cloud_mock import DeliveryRequest, MockDeliveryError
from .digest_window import TAIPEI


SLOTS = {"primary": (7, 15), "second": (8, 15), "final": (8, 45)}
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
REASONS = {"invalid_request", "unauthorized", "missed_issue", "immutable_conflict", "integrity_error",
           "revision_conflict", "idempotency_conflict", "payload_limit", "generation_failed",
           "storage_failed", "attempt_limit", "in_progress", "already_delivered", "archive_as_of_unknown",
           "archive_from_future", "archive_before_cutoff", "archive_stale", "ready"}


def public_job_summary(outcome):
    """Rebuild a log record; never serialize the private runner outcome."""
    if not isinstance(outcome, dict):
        return {"status": "failed", "reason_code": "storage_failed"}
    statuses = {"failed", "missed_issue", "already_delivered", "in_progress", "committed", "receipt"}
    status = outcome.get("status")
    safe = {"status": status if isinstance(status, str) and status in statuses else "failed"}
    reason = outcome.get("reason_code")
    if reason is not None:
        safe["reason_code"] = reason if isinstance(reason, str) and reason in REASONS else "storage_failed"
    receipt = outcome.get("result")
    if isinstance(receipt, dict):
        date = receipt.get("issue_date")
        try:
            from .digest_window import window_for_date
            if isinstance(date, str):
                window_for_date(date)
                safe["issue_date"] = date
        except ValueError:
            pass
        commit = receipt.get("source_commit")
        if isinstance(commit, str) and COMMIT.fullmatch(commit):
            safe["source_commit"] = commit
        for key in ("pair_verified", "rerun_identical"):
            if type(receipt.get(key)) is bool:
                safe[key] = receipt[key]
        count = receipt.get("selected_count")
        if type(count) is int and 0 <= count <= 20:
            safe["count"] = count
        for key, allowed in {"quality": {"ready-for-review", "review-only"},
                             "timeliness": {"on_time", "late", "historical"}}.items():
            if isinstance(receipt.get(key), str) and receipt[key] in allowed:
                safe[key] = receipt[key]
        as_of = receipt.get("archive_as_of")
        if isinstance(as_of, str):
            try:
                from .digest_cloud_prepare import _timestamp
                _timestamp(as_of)
                safe["as_of"] = as_of
            except PreparationError:
                pass
    return safe


def _wire(now):
    return now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _uuid(value):
    from uuid import UUID
    try:
        if not isinstance(value, str) or str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError):
        raise PreparationError("invalid_request") from None


class MemoryJobCoordinator:
    def __init__(self, delivery, clock, *, issuer_id="simulated-scheduler",
                 owner_policy=None, owner_id=None):
        self.delivery, self.clock = delivery, clock
        self.issuer_id = issuer_id
        self.owner_policy, self.owner_id = owner_policy, owner_id
        self.owner_issuer = "owner:" + owner_id if isinstance(owner_id, str) else None
        self.trusted_issuers = frozenset({issuer_id, self.owner_issuer} - {None})
        # This simulation shares the delivery control's lock. Separate locks
        # would invert claim(read-control) and commit(check-claim) lock order.
        self._lock = delivery.control._lock
        self._slots, self._jobs, self._notifications = {}, {}, {}

    def _now(self):
        now = self.clock()
        if not isinstance(now, datetime) or now.utcoffset() is None:
            raise PreparationError("invalid_request")
        return now.astimezone(timezone.utc)

    def issue_slot(self, slot):
        """Trusted server clock creates the date; callers cannot supply a date."""
        if slot not in SLOTS:
            raise PreparationError("invalid_request")
        now = self._now()
        local = now.astimezone(TAIPEI)
        date = local.date().isoformat()
        with self._lock:
            key = (date, slot)
            if key in self._slots:
                return deepcopy(self._jobs[self._slots[key]]["intent"])
            scheduled = datetime.combine(local.date(), time(*SLOTS[slot]), TAIPEI).astimezone(timezone.utc)
            if not scheduled <= now <= scheduled + timedelta(minutes=15):
                raise PreparationError("invalid_request")
            request_id = str(uuid4())
            intent = {"schema_version": 1, "request_id": request_id, "issue_date": date,
                      "mode": "scheduled", "scheduled_for": _wire(scheduled), "issued_at": _wire(now),
                      "issuer_id": self.issuer_id, "owner_authorized": False}
            _validate_intent(intent, now, self.trusted_issuers)
            self._jobs[request_id] = {"intent": intent, "attempt_id": str(uuid4()),
                                     "state": "pending", "source_commit": None, "executions": {},
                                     "current_execution": None, "result": None}
            self._slots[key] = request_id
            return deepcopy(intent)  # Persisted in this adapter before a dispatcher receives it.

    def issue_manual(self, principal, issue_date, request_id, *, historical=False):
        if self.owner_policy is None or not self.owner_id or type(historical) is not bool:
            raise PreparationError("unauthorized")
        if self.owner_policy.require(principal, self.owner_id, "digest:retry") != self.owner_id:
            raise PreparationError("unauthorized")
        _uuid(request_id)
        now = self._now()
        mode = "manual_historical" if historical else "manual_current"
        intent = {"schema_version": 1, "request_id": request_id, "issue_date": issue_date,
                  "mode": mode, "scheduled_for": None, "issued_at": _wire(now),
                  "issuer_id": self.owner_issuer, "owner_authorized": True}
        _validate_intent(intent, now, self.trusted_issuers)
        with self._lock:
            existing = self._jobs.get(request_id)
            if existing:
                if (existing["intent"]["mode"] != mode or
                        existing["intent"]["issue_date"] != issue_date):
                    raise PreparationError("idempotency_conflict")
                return deepcopy(existing["intent"])
            if sum(job["intent"]["issue_date"] == issue_date and job["intent"]["scheduled_for"] is None
                   for job in self._jobs.values()) >= 3:
                raise PreparationError("attempt_limit")
            self._jobs[request_id] = {"intent": intent, "attempt_id": str(uuid4()),
                                     "state": "pending", "source_commit": None,
                                     "executions": {}, "current_execution": None, "result": None}
            return deepcopy(intent)

    def _receipt(self, job):
        state = self.delivery.control.get_issue(job["intent"]["issue_date"])
        row = state["request_receipts"].get(job["intent"]["request_id"])
        return deepcopy(row["result"]) if row else None

    def _has_ready(self, date):
        state = self.delivery.control.get_issue(date)
        for row in state["deliveries"].values():
            if row["quality"] == "ready-for-review":
                try:
                    self.delivery.read_base(date, row["base_identity"])
                    return True
                except MockDeliveryError:
                    pass
        return False

    def claim(self, request_id, execution_id, candidate_commit):
        _uuid(request_id)
        _uuid(execution_id)
        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                raise PreparationError("unauthorized")
            now = self._now()
            intent = job["intent"]
            receipt = self._receipt(job)
            if receipt is not None:
                job["state"], job["result"] = "committed", receipt
                return {"action": "receipt", "result": receipt}
            if job["state"] in {"failed", "missed_issue", "already_delivered"}:
                return {"action": job["state"], "reason_code": job.get("reason_code", "attempt_limit")}
            try:
                _validate_intent(intent, now, self.trusted_issuers)
            except PreparationError as exc:
                if exc.code == "missed_issue":
                    job["state"], job["reason_code"] = "missed_issue", exc.code
                raise
            if intent["mode"] == "scheduled" and self._has_ready(intent["issue_date"]):
                job["state"], job["reason_code"] = "already_delivered", "already_delivered"
                return {"action": "already_delivered", "reason_code": "already_delivered"}
            active = job["executions"].get(job["current_execution"])
            if active and active["state"] == "running":
                if now < active["lease_until"]:
                    return {"action": "in_progress", "reason_code": "in_progress"}
                active["state"], active["reason_code"] = "failed", "storage_failed"
            if execution_id in job["executions"]:
                return {"action": "failed", "reason_code": job["executions"][execution_id]["reason_code"]}
            if len(job["executions"]) >= 3:
                job["state"], job["reason_code"] = "failed", "attempt_limit"
                return {"action": "failed", "reason_code": "attempt_limit"}
            if job["source_commit"] is None:
                if not isinstance(candidate_commit, str) or not COMMIT.fullmatch(candidate_commit):
                    raise PreparationError("invalid_request")
                job["source_commit"] = candidate_commit
            count = len(job["executions"]) + 1
            lease = now + timedelta(minutes=10)
            job["executions"][execution_id] = {"state": "running", "lease_until": lease,
                                                "reason_code": None, "count": count}
            job["current_execution"], job["state"] = execution_id, "running"
            return {"action": "generate", "intent": deepcopy(intent), "attempt_id": job["attempt_id"],
                    "execution_id": execution_id, "execution_count": count,
                    "source_commit": job["source_commit"], "lease_until": _wire(lease)}

    def authorize_commit(self, claim, now):
        with self._lock:
            job = self._jobs[claim["intent"]["request_id"]]
            if claim["intent"] != job["intent"] or claim["attempt_id"] != job["attempt_id"]:
                raise MockDeliveryError("invalid_request")
            if (job["intent"]["mode"] != "manual_historical" and
                    now.astimezone(TAIPEI).date().isoformat() != job["intent"]["issue_date"]):
                raise MockDeliveryError("missed_issue")
            active = job["executions"].get(claim["execution_id"])
            if (job["state"] != "running" or job["current_execution"] != claim["execution_id"] or
                    active is None or active["state"] != "running" or
                    active["count"] != claim["execution_count"] or
                    job["source_commit"] != claim["source_commit"]):
                raise MockDeliveryError("attempt_limit")
            if now >= active["lease_until"]:
                raise MockDeliveryError("storage_failed")

    def _finish(self, claim, result=None, code=None):
        with self._lock:
            job = self._jobs[claim["intent"]["request_id"]]
            if job["current_execution"] != claim["execution_id"]:
                return
            execution = job["executions"][claim["execution_id"]]
            if result is not None:
                execution["state"], job["state"], job["result"] = "committed", "committed", deepcopy(result)
                return
            execution["state"], execution["reason_code"] = "failed", code
            resumable = code in {"storage_failed", "integrity_error", "revision_conflict"}
            job["state"] = "pending" if resumable and len(job["executions"]) < 3 else (
                "missed_issue" if code == "missed_issue" else "failed")
            job["reason_code"] = code
            if job["state"] in {"failed", "missed_issue"}:
                request = DeliveryRequest(1, claim["intent"]["request_id"], claim["attempt_id"],
                                          claim["intent"]["issue_date"], claim["execution_count"])
                self.delivery.control.record_failure(request, code, terminal=True)

    def run_job(self, request_id, execution_id, candidate_commit, load_pins, workspace):
        """Only a generate claim can reach the injected fixed-commit loader."""
        try:
            claim = self.claim(request_id, execution_id, candidate_commit)
        except PreparationError as exc:
            return {"status": "failed", "reason_code": exc.code}
        except Exception:
            return {"status": "failed", "reason_code": "storage_failed"}
        if claim["action"] != "generate":
            return {"status": claim["action"], "reason_code": claim.get("reason_code"),
                    "result": claim.get("result")}
        try:
            self.authorize_commit(claim, self._now())
            pins = load_pins(claim["source_commit"])
            if pins.source_commit != claim["source_commit"]:
                raise PreparationError("invalid_request")
            prepared = prepare_generation(claim["intent"], pins, self.clock, workspace,
                                          trusted_issuer_ids=self.trusted_issuers)
            self.authorize_commit(claim, self._now())
            request = DeliveryRequest(1, request_id, claim["attempt_id"],
                                      claim["intent"]["issue_date"], claim["execution_count"])
            result = self.delivery.commit_delivery(
                prepared, request, authorize_commit=lambda now: self.authorize_commit(claim, now))
        except (PreparationError, MockDeliveryError) as exc:
            code = exc.code if exc.code in REASONS else "storage_failed"
            try:
                self._finish(claim, code=code)
            except Exception:
                code = "storage_failed"
            return {"status": "failed", "reason_code": code}
        except Exception:
            try:
                self._finish(claim, code="storage_failed")
            except Exception:
                pass
            return {"status": "failed", "reason_code": "storage_failed"}
        recorded = True
        try:
            self._finish(claim, result=result)
        except Exception:
            recorded = False  # The delivery receipt is already authoritative.
        return {"status": "committed", "result": result, "coordination_recorded": recorded}

    def notification_plan(self, issue_date):
        """Return a deduplicated safe notification plan; never send a message."""
        with self._lock:
            now = self._now().astimezone(TAIPEI)
            if now.date().isoformat() != issue_date:
                return None
            ready = self._has_ready(issue_date)
            phase = "delivered" if ready else "failed" if now.time() >= time(9) else None
            if phase is None or self._notifications.get(issue_date) == phase:
                return None
            self._notifications[issue_date] = phase
            return {"issue_date": issue_date, "status": phase, "sent": False,
                    "meets_daily_target": self.delivery.get_issue(issue_date)["meets_daily_target"]}
