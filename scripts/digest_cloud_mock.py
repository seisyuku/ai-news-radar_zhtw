"""C04 in-process delivery simulation; deliberately makes no cloud durability claim."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, time, timezone
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from threading import RLock
from typing import Callable
from uuid import UUID, uuid4

from .deliver_digest import readiness
from .digest_cloud_prepare import PreparedPair
from .digest_document import canonical_json
from .digest_cloud_editorial_rules import IssueDecision
from .digest_cloud_ports import OriginalReadError
from .digest_window import TAIPEI, window_for_date
from .generate_digest import verify_digest_pair


_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_KEY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}/[0-9a-f]{64}/(?:original\.md|original\.meta\.json)\Z")


class MockDeliveryError(OriginalReadError):
    """Fixed safe code. Raw storage, document, and actor text is never returned."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _fail(code):
    raise MockDeliveryError(code)


def _uuid(value):
    if not isinstance(value, str):
        _fail("invalid_request")
    try:
        if str(UUID(value)) != value:
            _fail("invalid_request")
    except ValueError:
        _fail("invalid_request")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _utc(clock):
    value = clock()
    if not isinstance(value, datetime) or value.utcoffset() is None:
        _fail("storage_failed")
    return value.astimezone(timezone.utc)


def _wire(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class DeliveryRequest:
    schema_version: int
    request_id: str
    attempt_id: str
    issue_date: str
    execution_count: int


class MemoryObjectStore:
    """Immutable object behavior inside one process, with an injectable failure hook."""

    def __init__(self):
        self._lock = RLock()
        self._objects: dict[str, bytes] = {}
        self.before_put: Callable[[str, bytes], None] | None = None
        self.before_get: Callable[[str], None] | None = None

    def put_if_absent(self, key: str, data: bytes):
        if not isinstance(key, str) or not _KEY.fullmatch(key) or not isinstance(data, bytes):
            _fail("invalid_request")
        with self._lock:
            try:
                if self.before_put:
                    self.before_put(key, data)
            except Exception:
                _fail("storage_failed")
            previous = self._objects.get(key)
            if previous is None:
                self._objects[key] = data
            elif previous != data:
                _fail("immutable_conflict")
            return {"key": key, "sha256": _sha(data), "size": len(data)}

    def get(self, key: str) -> bytes:
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            _fail("invalid_request")
        with self._lock:
            try:
                if self.before_get:
                    self.before_get(key)
                return self._objects[key]
            except Exception:
                _fail("integrity_error")


class MemoryControl:
    """One process lock simulates a linearizable per-issue control record."""

    def __init__(self, clock: Callable[[], datetime]):
        self._clock = clock
        self._lock = RLock()
        self._issues: dict[str, dict] = {}
        self.fail_next_commit = False

    @staticmethod
    def _empty(issue_date):
        return {"schema_version": 1, "issue_date": issue_date, "control_version": 0,
                "selected_base": None, "delivery_ids": [], "deliveries": {},
                "attempts": {}, "request_receipts": {}, "review_heads": {}, "reviews": {},
                "edit_receipts": {}, "selection_receipts": {}}

    def get_issue(self, issue_date):
        if not isinstance(issue_date, str):
            _fail("invalid_request")
        try:
            window_for_date(issue_date)
        except ValueError:
            _fail("invalid_request")
        with self._lock:
            return deepcopy(self._issues.get(issue_date, self._empty(issue_date)))

    def transact_issue(self, issue_date, decide: Callable[[dict, datetime], IssueDecision]) -> IssueDecision:
        """Commit a returned decision; exceptions leave the issue untouched.

        A durable adapter can wrap the same callback in one database transaction.
        Business rejections return a state and are raised only by the caller
        after this method returns.
        """
        if not isinstance(issue_date, str):
            _fail("invalid_request")
        try:
            window_for_date(issue_date)
        except ValueError:
            _fail("invalid_request")
        with self._lock:
            current = deepcopy(self._issues.get(issue_date, self._empty(issue_date)))
            version = current["control_version"]
            decision = decide(current, _utc(self._clock))
            if not isinstance(decision, IssueDecision):
                _fail("storage_failed")
            if decision.state is not None:
                if (decision.state["issue_date"] != issue_date or
                        decision.state["control_version"] != version + 1):
                    _fail("storage_failed")
                self._issues[issue_date] = deepcopy(decision.state)
            return decision

    def request_result(self, issue_date, request_id, payload_sha256):
        with self._lock:
            row = self._issues.get(issue_date, {}).get("request_receipts", {}).get(request_id)
            if row is None:
                return None
            if row["payload_sha256"] != payload_sha256:
                _fail("idempotency_conflict")
            return deepcopy(row["result"])

    def begin_attempt(self, prepared: PreparedPair, request: DeliveryRequest, payload_sha256: str,
                      expected_control_version: int | None = None):
        with self._lock:
            current = self._issues.get(request.issue_date, self._empty(request.issue_date))
            if (expected_control_version is not None and
                    (type(expected_control_version) is not int or
                     current["control_version"] != expected_control_version)):
                _fail("revision_conflict")
            if request.request_id in current["request_receipts"]:
                return current["control_version"]
            previous = current["attempts"].get(request.attempt_id)
            if previous:
                if (previous["request_id"] != request.request_id or
                        previous["payload_sha256"] != payload_sha256 or
                        previous["source_commit"] != prepared.source_commit or
                        request.execution_count < previous["execution_count"]):
                    _fail("idempotency_conflict")
                if previous["state"] in {"failed", "missed_issue", "committed"}:
                    _fail("attempt_limit")
            else:
                attempts = list(current["attempts"].values())
                if any(row["request_id"] == request.request_id for row in attempts):
                    _fail("idempotency_conflict")
                if (prepared.mode == "scheduled" and any(
                    row["scheduled_for"] == prepared.scheduled_for for row in attempts
                )) or (prepared.mode != "scheduled" and sum(
                    row["scheduled_for"] is None for row in attempts
                ) >= 3):
                    _fail("attempt_limit")
            state = deepcopy(current)
            state["attempts"][request.attempt_id] = {
                "request_id": request.request_id, "state": "running", "reason_code": None,
                "execution_count": request.execution_count, "source_commit": prepared.source_commit,
                "payload_sha256": payload_sha256, "scheduled_for": prepared.scheduled_for,
                "started_at": previous["started_at"] if previous else prepared.started_at, "finished_at": None}
            state["control_version"] += 1
            self._issues[request.issue_date] = state
            return state["control_version"]

    def record_failure(self, request: DeliveryRequest, reason: str, *, terminal=False):
        if reason not in {"storage_failed", "integrity_error", "immutable_conflict",
                          "missed_issue", "revision_conflict"}:
            reason = "storage_failed"
        with self._lock:
            current = self._issues.get(request.issue_date, self._empty(request.issue_date))
            state = deepcopy(current)
            if request.request_id in state["request_receipts"]:
                return
            previous = state["attempts"].get(request.attempt_id)
            if previous and (previous["state"] in {"committed", "failed", "missed_issue"} or
                             previous["execution_count"] != request.execution_count):
                return
            if previous is None:
                return
            can_resume = (not terminal and request.execution_count < 3 and
                          reason in {"storage_failed", "integrity_error", "revision_conflict"})
            state["attempts"][request.attempt_id]["state"] = (
                "missed_issue" if reason == "missed_issue" else "running" if can_resume else "failed")
            state["attempts"][request.attempt_id]["reason_code"] = reason
            state["attempts"][request.attempt_id]["finished_at"] = None if can_resume else _wire(_utc(self._clock))
            state["control_version"] += 1
            self._issues[request.issue_date] = state

    def commit_delivery(self, prepared: PreparedPair, request: DeliveryRequest, objects: dict,
                        verified: dict, payload_sha256: str, expected_control_version: int,
                        authorize_commit=None):
        with self._lock:
            current = self._issues.get(request.issue_date, self._empty(request.issue_date))
            state = deepcopy(current)
            previous = state["request_receipts"].get(request.request_id)
            if previous:
                if previous["payload_sha256"] != payload_sha256:
                    _fail("idempotency_conflict")
                return deepcopy(previous["result"])
            if state["control_version"] != expected_control_version:
                _fail("revision_conflict")
            attempt = state["attempts"].get(request.attempt_id)
            if not attempt or attempt["request_id"] != request.request_id or attempt["payload_sha256"] != payload_sha256:
                _fail("invalid_request")
            if self.fail_next_commit:
                self.fail_next_commit = False
                _fail("storage_failed")
            now = _utc(self._clock)  # The simulated transaction decision clock.
            if authorize_commit is not None:
                authorize_commit(now)
            local_date = now.astimezone(TAIPEI).date().isoformat()
            if prepared.mode != "manual_historical" and local_date != request.issue_date:
                result = {"schema_version": 1, "status": "missed_issue", "issue_date": request.issue_date,
                          "reason_code": "missed_issue", "attempt_id": request.attempt_id}
                state["attempts"][request.attempt_id] = {
                    "request_id": request.request_id, "state": "missed_issue",
                    "reason_code": "missed_issue", "execution_count": request.execution_count,
                    "source_commit": prepared.source_commit, "payload_sha256": payload_sha256,
                    "scheduled_for": prepared.scheduled_for, "started_at": prepared.started_at,
                    "finished_at": _wire(now)}
                state["request_receipts"][request.request_id] = {
                    "schema_version": 1, "principal": "system", "operation_family": "delivery",
                    "issue_date": request.issue_date, "request_id": request.request_id,
                    "payload_sha256": payload_sha256, "result_code": "missed_issue",
                    "result": deepcopy(result), "committed_at": _wire(now)}
                state["control_version"] += 1
                self._issues[request.issue_date] = state
                return result
            window = window_for_date(request.issue_date)
            quality, reason = readiness(prepared.archive_as_of, window, now)
            deadline = datetime.combine(now.astimezone(TAIPEI).date(), time(9), TAIPEI).astimezone(timezone.utc)
            if prepared.mode == "manual_historical":
                deadline = datetime.combine(datetime.fromisoformat(request.issue_date).date(), time(9), TAIPEI).astimezone(timezone.utc)
            timeliness = ("historical" if prepared.mode == "manual_historical" else
                          "on_time" if now <= deadline else "late")
            delivery_id = str(uuid4())
            receipt = {
                "schema_version": 1, "delivery_id": delivery_id, "attempt_id": request.attempt_id,
                "request_id": request.request_id, "issue_date": request.issue_date,
                "base_identity": prepared.base_identity, "source_commit": prepared.source_commit,
                "input_sha256": dict(prepared.input_sha256), "objects": deepcopy(objects),
                "archive_as_of": prepared.archive_as_of, "pair_verified": True,
                "rerun_identical": True, "checked_at": prepared.prepared_at,
                "committed_at": _wire(now), "deadline_at": _wire(deadline),
                "quality": quality, "reason_code": reason, "timeliness": timeliness,
                "selected_count": prepared.selected_count}
            if prepared.base_identity not in state["reviews"]:
                ordered = [candidate["story_id"] for candidate in verified["candidates"]]
                if len(ordered) != len(set(ordered)):
                    _fail("integrity_error")
                entries = {story_id: {"included": True, "title_override": None,
                                       "summary_override": None} for story_id in ordered}
                content = {"ordered_story_ids": ordered, "entries": entries}
                state["reviews"][prepared.base_identity] = [{"schema_version": 1,
                    "issue_date": request.issue_date, "base_identity": prepared.base_identity,
                    "revision": 0, "parent_revision": None, "content": content,
                    "content_sha256": _sha(canonical_json(content).encode()),
                    "actor_id": "system", "created_at": _wire(now), "request_id": None}]
                state["review_heads"][prepared.base_identity] = 0
            if state["selected_base"] is None and quality == "ready-for-review":
                state["selected_base"] = prepared.base_identity
            state["delivery_ids"].append(delivery_id)
            state["deliveries"][delivery_id] = deepcopy(receipt)
            state["attempts"][request.attempt_id] = {
                "request_id": request.request_id, "state": "committed", "reason_code": reason,
                "execution_count": request.execution_count, "delivery_id": delivery_id,
                "source_commit": prepared.source_commit, "payload_sha256": payload_sha256,
                "scheduled_for": prepared.scheduled_for, "started_at": prepared.started_at,
                "finished_at": _wire(now)}
            state["request_receipts"][request.request_id] = {
                "schema_version": 1, "principal": "system", "operation_family": "delivery",
                "issue_date": request.issue_date, "request_id": request.request_id,
                "payload_sha256": payload_sha256, "result_code": "committed",
                "result": deepcopy(receipt), "committed_at": _wire(now)}
            state["control_version"] += 1
            self._issues[request.issue_date] = state
            return deepcopy(receipt)


class MockDeliveryService:
    """C04 facade. Both stores are process-local and injected for fault testing."""

    def __init__(self, objects: MemoryObjectStore, control: MemoryControl, workspace: Path):
        self.objects = objects
        self.control = control
        self.workspace = Path(workspace).resolve()
        if (Path.home() / "Downloads").resolve() not in self.workspace.parents:
            _fail("invalid_request")

    @staticmethod
    def _keys(issue_date, base_identity):
        prefix = f"{issue_date}/{base_identity}"
        return {"md": prefix + "/original.md", "meta": prefix + "/original.meta.json"}

    @staticmethod
    def _validate(prepared, request):
        if not isinstance(prepared, PreparedPair) or not isinstance(request, DeliveryRequest):
            _fail("invalid_request")
        if type(request.execution_count) is int and request.execution_count > 3:
            _fail("attempt_limit")
        if (type(request.schema_version) is not int or request.schema_version != 1 or
                type(request.execution_count) is not int or request.execution_count < 1 or
                request.issue_date != prepared.issue_date or request.request_id != prepared.request_id or
                prepared.mode not in {"scheduled", "manual_current", "manual_historical"}):
            _fail("invalid_request")
        _uuid(request.attempt_id)
        _uuid(request.request_id)
        try:
            window_for_date(request.issue_date)
        except ValueError:
            _fail("invalid_request")
        if (not isinstance(prepared.base_identity, str) or not _SHA.fullmatch(prepared.base_identity) or
                not isinstance(prepared.source_commit, str) or not _COMMIT.fullmatch(prepared.source_commit) or
                not isinstance(prepared.markdown, bytes) or not isinstance(prepared.metadata, bytes) or
                _sha(prepared.markdown) != prepared.markdown_sha256 or
                _sha(prepared.metadata) != prepared.metadata_sha256 or
                not prepared.pair_verified or not prepared.rerun_identical):
            _fail("invalid_request")

    def _verify(self, md: bytes, meta: bytes, expected_identity: str):
        try:
            self.workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
            with TemporaryDirectory(prefix="c04-verify-", dir=self.workspace) as directory:
                first = Path(directory) / "original.md"
                second = Path(directory) / "original.meta.json"
                first.write_bytes(md)
                second.write_bytes(meta)
                first.chmod(0o600)
                second.chmod(0o600)
                verified = verify_digest_pair(first, second)
                if verified["input_identity"] != expected_identity:
                    _fail("integrity_error")
                return verified
        except MockDeliveryError:
            raise
        except Exception:
            _fail("integrity_error")

    def commit_delivery(self, prepared: PreparedPair, request: DeliveryRequest,
                        expected_control_version: int | None = None, *, authorize_commit=None):
        self._validate(prepared, request)
        payload = _sha(canonical_json({"request": {"schema_version": request.schema_version,
                                                    "request_id": request.request_id,
                                                    "attempt_id": request.attempt_id,
                                                    "issue_date": request.issue_date},
                                       "base_identity": prepared.base_identity,
                                       "mode": prepared.mode, "scheduled_for": prepared.scheduled_for,
                                       "issued_at": prepared.issued_at, "issuer_id": prepared.issuer_id,
                                       "md": prepared.markdown_sha256, "meta": prepared.metadata_sha256,
                                       "input_sha256": dict(prepared.input_sha256),
                                       "archive_as_of": prepared.archive_as_of,
                                       "selected_count": prepared.selected_count,
                                       "source_commit": prepared.source_commit}).encode())
        prior = self.control.request_result(request.issue_date, request.request_id, payload)
        if prior is not None:
            return prior
        begun_version = self.control.begin_attempt(prepared, request, payload, expected_control_version)
        keys = self._keys(request.issue_date, prepared.base_identity)
        try:
            objects = {"md": self.objects.put_if_absent(keys["md"], prepared.markdown),
                       "meta": self.objects.put_if_absent(keys["meta"], prepared.metadata)}
            md = self.objects.get(keys["md"])
            meta = self.objects.get(keys["meta"])
            if _sha(md) != objects["md"]["sha256"] or _sha(meta) != objects["meta"]["sha256"]:
                _fail("integrity_error")
            verified = self._verify(md, meta, prepared.base_identity)
            if verified["selection_counts"]["selected_count"] != prepared.selected_count:
                _fail("integrity_error")
            for _ in range(3):
                version = (self.control.get_issue(request.issue_date)["control_version"] if
                           expected_control_version is None else begun_version)
                try:
                    return self.control.commit_delivery(prepared, request, objects, verified, payload, version,
                                                        authorize_commit)
                except MockDeliveryError as exc:
                    if exc.code != "revision_conflict" or expected_control_version is not None:
                        raise
            _fail("storage_failed")
        except MockDeliveryError as exc:
            if exc.code in {"storage_failed", "integrity_error", "immutable_conflict",
                            "missed_issue", "revision_conflict"}:
                self.control.record_failure(request, exc.code,
                                            terminal=expected_control_version is not None and
                                            exc.code == "revision_conflict")
            raise
        except Exception:
            self.control.record_failure(request, "storage_failed")
            raise MockDeliveryError("storage_failed") from None

    def read_base(self, issue_date: str, base_identity: str):
        state = self.control.get_issue(issue_date)
        candidates = [state["deliveries"][ident] for ident in state["delivery_ids"]
                      if state["deliveries"][ident]["base_identity"] == base_identity]
        if not candidates:
            _fail("invalid_request")
        receipt = candidates[0]
        try:
            md = self.objects.get(receipt["objects"]["md"]["key"])
            meta = self.objects.get(receipt["objects"]["meta"]["key"])
            if (_sha(md) != receipt["objects"]["md"]["sha256"] or
                    _sha(meta) != receipt["objects"]["meta"]["sha256"]):
                _fail("integrity_error")
            self._verify(md, meta, base_identity)
            return {"receipt": receipt, "markdown": md, "metadata": meta, "integrity": "verified"}
        except MockDeliveryError:
            _fail("integrity_error")

    def get_issue(self, issue_date: str):
        state = self.control.get_issue(issue_date)
        selected = state["selected_base"]
        integrity = "verified"
        if selected:
            try:
                self.read_base(issue_date, selected)
            except MockDeliveryError:
                integrity = "integrity_error"
        achieved = any(row["quality"] == "ready-for-review" and row["timeliness"] == "on_time"
                       for row in state["deliveries"].values()) and integrity == "verified"
        return {"issue_date": issue_date, "selected_base": selected,
                "delivery_count": len(state["delivery_ids"]),
                "latest_attempt": deepcopy(next(reversed(state["attempts"].values()))) if state["attempts"] else None,
                "meets_daily_target": achieved, "integrity": integrity,
                "control_version": state["control_version"]}
