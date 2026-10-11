"""Editorial service over explicit storage and trusted identity ports."""

from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
import hashlib
import json
import re
from typing import Mapping
from uuid import UUID

from .digest_cloud_editorial_rules import (IssueDecision, edit_issue, prior_edit,
                                           prior_selection, reject_existing, select_issue)
from .digest_cloud_ports import IssueControlPort, OriginalReadError, OriginalReadPort, OwnerPolicy
from .digest_json import canonical_json
from .digest_window import window_for_date


_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_REQUEST = 1024 * 1024
_MAX_TITLE = 4096
_MAX_SUMMARY = 32768
_BASE_FIELDS = {"schema_version", "request_id", "issue_date", "base_identity",
                "expected_revision", "operation"}


class EditorialError(ValueError):
    """Fixed safe code; current_revision is numeric and safe to return."""

    def __init__(self, code: str, *, current_revision: int | None = None):
        self.code = code
        self.current_revision = current_revision
        super().__init__(code)


def _fail(code: str, *, current_revision=None):
    raise EditorialError(code, current_revision=current_revision)


def _safe_public(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except EditorialError:
            raise
        except Exception:
            raise EditorialError("storage_failed") from None
    return wrapped


@dataclass(frozen=True)
class SimulatedPrincipal:
    principal_id: str
    owner_authorized: bool


def _owner(principal, owner_id):
    if (not isinstance(principal, SimulatedPrincipal) or
            type(principal.owner_authorized) is not bool or not principal.owner_authorized or
            not isinstance(principal.principal_id, str) or principal.principal_id != owner_id):
        _fail("unauthorized")


class SimulatedOwnerPolicy:
    def require(self, principal, owner_id: str, permission: str) -> str:
        _owner(principal, owner_id)
        return principal.principal_id


def _uuid(value):
    if not isinstance(value, str):
        _fail("invalid_request")
    try:
        if str(UUID(value)) != value:
            _fail("invalid_request")
    except ValueError:
        _fail("invalid_request")


def _identity(value):
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        _fail("invalid_request")


def _date(value):
    if not isinstance(value, str):
        _fail("invalid_request")
    try:
        window_for_date(value)
    except ValueError:
        _fail("invalid_request")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("invalid_request")
        result[key] = value
    return result


def _no_constant(_):
    _fail("invalid_request")


def _request_dict(raw):
    if isinstance(raw, bytes):
        if len(raw) > _MAX_REQUEST:
            _fail("payload_limit")
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                               parse_constant=_no_constant)
        except (UnicodeError, ValueError, TypeError):
            _fail("invalid_request")
    elif isinstance(raw, Mapping):
        try:
            encoded = canonical_json(raw).encode("utf-8")
        except (TypeError, ValueError, OverflowError):
            _fail("invalid_request")
        if len(encoded) > _MAX_REQUEST:
            _fail("payload_limit")
        value = deepcopy(dict(raw))
    else:
        _fail("invalid_request")
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        _fail("invalid_request")
    return value


def _edit_request(raw):
    value = _request_dict(raw)
    operation = value.get("operation")
    if not isinstance(operation, str) or operation not in {"patch", "restore"}:
        _fail("invalid_request")
    expected = (_BASE_FIELDS | {"updates", "ordered_story_ids"} if operation == "patch" else
                _BASE_FIELDS | {"restore_revision"} if operation == "restore" else set())
    if (set(value) != expected or type(value["schema_version"]) is not int or
            value["schema_version"] != 1 or type(value["expected_revision"]) is not int or
            value["expected_revision"] < 0):
        _fail("invalid_request")
    _uuid(value["request_id"])
    _date(value["issue_date"])
    _identity(value["base_identity"])
    if operation == "patch":
        order = value["ordered_story_ids"]
        if (order is not None and (not isinstance(order, list) or len(order) > 20 or
                                   any(not isinstance(item, str) or not item for item in order) or
                                   len(order) != len(set(order)))):
            _fail("invalid_request")
        updates = value["updates"]
        if not isinstance(updates, dict) or len(updates) > 20:
            _fail("invalid_request")
        for story_id, fields in updates.items():
            if not isinstance(story_id, str) or not story_id or not isinstance(fields, dict) or not fields:
                _fail("invalid_request")
            if not set(fields) <= {"included", "title_override", "summary_override"}:
                _fail("invalid_request")
            for field, item in fields.items():
                if field == "included":
                    if type(item) is not bool:
                        _fail("invalid_request")
                elif (item is not None and not isinstance(item, str)):
                    _fail("invalid_request")
                elif isinstance(item, str) and len(item) > (_MAX_TITLE if field == "title_override" else _MAX_SUMMARY):
                    _fail("payload_limit")
    elif type(value["restore_revision"]) is not int or value["restore_revision"] < 0:
        _fail("invalid_request")
    return value, hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class EditorialService:
    """One set of review rules for callers with a trusted identity policy."""

    def __init__(self, delivery: OriginalReadPort, *, owner_id: str,
                 control: IssueControlPort | None = None, policy: OwnerPolicy):
        if (not callable(getattr(delivery, "read_base", None)) or
                not isinstance(owner_id, str) or not owner_id):
            _fail("invalid_request")
        control = control if control is not None else getattr(delivery, "control", None)
        if (not callable(getattr(control, "get_issue", None)) or
                not callable(getattr(control, "transact_issue", None)) or
                not callable(getattr(policy, "require", None))):
            _fail("invalid_request")
        self.delivery = delivery
        self.control: IssueControlPort = control
        self.owner_id = owner_id
        self.policy = policy

    def _actor(self, principal, permission):
        actor = self.policy.require(principal, self.owner_id, permission)
        if not isinstance(actor, str) or not actor or actor != self.owner_id:
            _fail("unauthorized")
        return actor

    def _base(self, issue_date, base_identity):
        try:
            return self.delivery.read_base(issue_date, base_identity)
        except OriginalReadError as exc:
            _fail("base_mismatch" if exc.code == "invalid_request" else "integrity_error")
        except Exception:
            _fail("integrity_error")

    def _remember_error(self, actor, request, payload_hash, family, code):
        decision = self.control.transact_issue(
            request["issue_date"],
            lambda current, now: reject_existing(current, actor,
                                                 request, payload_hash, family, code, now))
        return self._resolve(decision)

    @staticmethod
    def _resolve(decision: IssueDecision):
        if decision.error_code is not None:
            _fail(decision.error_code, current_revision=decision.current_revision)
        return deepcopy(decision.result)

    @_safe_public
    def read_review(self, principal, issue_date: str, base_identity: str, revision: int | None = None):
        self._actor(principal, "digest:read")
        _date(issue_date)
        _identity(base_identity)
        if revision is not None and (type(revision) is not int or revision < 0):
            _fail("invalid_request")
        base = self._base(issue_date, base_identity)
        state = self.control.get_issue(issue_date)
        history = state["reviews"].get(base_identity)
        if not history:
            _fail("base_mismatch")
        head = state["review_heads"][base_identity]
        selected = head if revision is None else revision
        if selected >= len(history):
            _fail("invalid_request")
        row = deepcopy(history[selected])
        content = row["content"]
        try:
            if hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest() != row["content_sha256"]:
                _fail("integrity_error")
            originals = {candidate["story_id"]: candidate
                         for candidate in json.loads(base["metadata"])["candidates"]}
            stories = []
            for ordinal, story_id in enumerate(content["ordered_story_ids"], 1):
                original = originals[story_id]
                changes = content["entries"][story_id]
                stories.append({"ordinal": ordinal, "story_id": story_id,
                                "included": changes["included"],
                                "title": original["title"] if changes["title_override"] is None else changes["title_override"],
                                "summary": original["summary"] if changes["summary_override"] is None else changes["summary_override"],
                                "sources": deepcopy(original["sources"])})
        except Exception:
            _fail("integrity_error")
        return {"issue_date": issue_date, "base_identity": base_identity,
                "revision": selected, "current_revision": head,
                "content_sha256": row["content_sha256"], "content": content,
                "ordinal_map": {str(item["ordinal"]): item["story_id"] for item in stories},
                "stories": stories, "selected_base": state["selected_base"]}

    @_safe_public
    def apply_edit(self, principal, raw_request):
        actor = self._actor(principal, "digest:edit")
        request, payload_hash = _edit_request(raw_request)
        date = request["issue_date"]
        prior = prior_edit(self.control.get_issue(date), actor, request, payload_hash)
        if prior is not None:
            return self._resolve(prior)
        try:
            self._base(date, request["base_identity"])
        except EditorialError as exc:
            if exc.code == "base_mismatch":
                return self._remember_error(actor, request, payload_hash, "edit", exc.code)
            raise
        decision = self.control.transact_issue(
            date, lambda current, now: edit_issue(current, actor,
                                                  request, payload_hash, now))
        return self._resolve(decision)

    @_safe_public
    def select_base(self, principal, request: Mapping):
        actor = self._actor(principal, "digest:edit")
        value = _request_dict(request)
        if (set(value) != {"schema_version", "request_id", "issue_date", "base_identity", "expected_control_version"}
                or type(value["schema_version"]) is not int or value["schema_version"] != 1 or
                type(value["expected_control_version"]) is not int or value["expected_control_version"] < 0):
            _fail("invalid_request")
        _uuid(value["request_id"])
        _date(value["issue_date"])
        _identity(value["base_identity"])
        payload_hash = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
        date = value["issue_date"]
        prior = prior_selection(self.control.get_issue(date), actor, value, payload_hash)
        if prior is not None:
            return self._resolve(prior)
        try:
            self._base(date, value["base_identity"])
        except EditorialError as exc:
            if exc.code == "base_mismatch":
                return self._remember_error(actor, value, payload_hash, "selection", exc.code)
            raise
        decision = self.control.transact_issue(
            date, lambda current, now: select_issue(current, actor,
                                                    value, payload_hash, now))
        return self._resolve(decision)

    @_safe_public
    def export_review(self, principal, issue_date: str, base_identity: str, revision: int):
        snapshot = self.read_review(principal, issue_date, base_identity, revision)
        base = self._base(issue_date, base_identity)
        payload = {"schema_version": 1, "issue_date": issue_date,
                   "base_identity": base_identity, "revision": revision,
                   "original_markdown_sha256": base["receipt"]["objects"]["md"]["sha256"],
                   "content_sha256": snapshot["content_sha256"], "content": snapshot["content"],
                   "stories": snapshot["stories"]}
        raw = (canonical_json(payload) + "\n").encode("utf-8")
        return {"filename": f"digest-{issue_date}-{base_identity[:12]}-r{revision}.review.json",
                "content_type": "application/json; charset=utf-8", "bytes": raw,
                "sha256": hashlib.sha256(raw).hexdigest()}


class MockEditorialService(EditorialService):
    """C05-compatible wrapper; injected simulation identity is not a login."""

    def __init__(self, delivery: OriginalReadPort, *, owner_id: str,
                 control: IssueControlPort | None = None):
        super().__init__(delivery, owner_id=owner_id, control=control,
                         policy=SimulatedOwnerPolicy())
