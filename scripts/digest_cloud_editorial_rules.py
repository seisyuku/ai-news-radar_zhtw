"""Storage-independent C05 review transitions.

Business rejections return a decision containing their receipt. The storage
adapter commits that decision before its caller turns the rejection into an
API error. Unexpected exceptions still abort the transaction.
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib

from .digest_json import canonical_json


@dataclass(frozen=True)
class IssueDecision:
    state: dict | None
    result: dict | None = None
    error_code: str | None = None
    current_revision: int | None = None


def _wire(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _receipt(principal_id, issue_date, request_id, payload_hash, family, code, result, now):
    return {"schema_version": 1, "principal": principal_id,
            "operation_family": family, "issue_date": issue_date,
            "request_id": request_id, "payload_sha256": payload_hash,
            "result_code": code, "result": deepcopy(result), "committed_at": _wire(now)}


def _prior(current, field, key, payload_hash, *, base_identity=None):
    earlier = current[field].get(key)
    if earlier is None:
        return None
    if earlier["payload_sha256"] != payload_hash:
        return IssueDecision(None, error_code="idempotency_conflict")
    result = deepcopy(earlier["result"])
    if earlier["result_code"] not in {"applied", "no_change"}:
        return IssueDecision(None, error_code=earlier["result_code"],
                             current_revision=result.get("current_revision"))
    result["replayed"] = True
    if field == "edit_receipts":
        result["current_revision"] = current["review_heads"].get(base_identity, result["applied_revision"])
    else:
        result["current_selected_base"] = current["selected_base"]
    return IssueDecision(None, result=result)


def prior_edit(current, principal_id, request, payload_hash):
    return _prior(current, "edit_receipts", (principal_id, request["request_id"]),
                  payload_hash, base_identity=request["base_identity"])


def prior_selection(current, principal_id, request, payload_hash):
    return _prior(current, "selection_receipts", (principal_id, request["request_id"]), payload_hash)


def reject_existing(current, principal_id, request, payload_hash, family, code, now):
    """Receipt a permanent failure if the same request has not already settled."""
    prior = (prior_edit(current, principal_id, request, payload_hash) if family == "edit" else
             prior_selection(current, principal_id, request, payload_hash))
    if prior is not None:
        return prior
    date = request["issue_date"]
    base = request["base_identity"]
    field = "edit_receipts" if family == "edit" else "selection_receipts"
    result = {"issue_date": date, "base_identity": base, "result_code": code}
    if family == "edit":
        result["current_revision"] = current["review_heads"].get(base)
    else:
        result["control_version"] = current["control_version"]
    state = deepcopy(current)
    state[field][(principal_id, request["request_id"])] = _receipt(
        principal_id, date, request["request_id"], payload_hash, family, code, result, now)
    state["control_version"] += 1
    return IssueDecision(state, error_code=code, current_revision=result.get("current_revision"))


def edit_issue(current, principal_id, request, payload_hash, now):
    """Apply a validated C05 edit to one issue snapshot without storage I/O."""
    prior = prior_edit(current, principal_id, request, payload_hash)
    if prior is not None:
        return prior
    date = request["issue_date"]
    base = request["base_identity"]
    history = current["reviews"].get(base)
    if not history:
        return IssueDecision(None, error_code="base_mismatch")
    head = current["review_heads"][base]
    state = deepcopy(current)

    def reject(code):
        result = {"issue_date": date, "base_identity": base,
                  "current_revision": head, "result_code": code}
        state["edit_receipts"][(principal_id, request["request_id"])] = _receipt(
            principal_id, date, request["request_id"], payload_hash, "edit", code, result, now)
        state["control_version"] += 1
        return IssueDecision(state, error_code=code, current_revision=head)

    if request["expected_revision"] != head:
        return reject("revision_conflict")
    previous = history[head]["content"]
    changed = deepcopy(previous)
    if request["operation"] == "restore":
        target = request["restore_revision"]
        if target >= len(history):
            return reject("invalid_request")
        changed = deepcopy(history[target]["content"])
    else:
        order = request["ordered_story_ids"]
        if order is not None:
            if set(order) != set(previous["ordered_story_ids"]) or len(order) != len(previous["ordered_story_ids"]):
                return reject("unknown_story")
            changed["ordered_story_ids"] = list(order)
        for story_id, fields in request["updates"].items():
            if story_id not in changed["entries"]:
                return reject("unknown_story")
            changed["entries"][story_id].update(fields)
    next_revision = head + 1 if changed != previous else head
    code = "applied" if next_revision != head else "no_change"
    content_sha = hashlib.sha256(canonical_json(changed).encode("utf-8")).hexdigest()
    if next_revision != head:
        state["reviews"][base].append({
            "schema_version": 1, "issue_date": date, "base_identity": base,
            "revision": next_revision, "parent_revision": head,
            "content": changed, "content_sha256": content_sha,
            "actor_id": principal_id, "created_at": _wire(now),
            "request_id": request["request_id"]})
        state["review_heads"][base] = next_revision
    result = {"issue_date": date, "base_identity": base,
              "applied_revision": next_revision, "current_revision": next_revision,
              "content_sha256": content_sha, "result_code": code, "replayed": False}
    state["edit_receipts"][(principal_id, request["request_id"])] = _receipt(
        principal_id, date, request["request_id"], payload_hash, "edit", code, result, now)
    state["control_version"] += 1
    return IssueDecision(state, result=result)


def select_issue(current, principal_id, request, payload_hash, now):
    """CAS the selected base and receipt its result in the same issue state."""
    prior = prior_selection(current, principal_id, request, payload_hash)
    if prior is not None:
        return prior
    date = request["issue_date"]
    base = request["base_identity"]
    if current["control_version"] != request["expected_control_version"]:
        return reject_existing(current, principal_id, request, payload_hash,
                               "selection", "revision_conflict", now)
    if base not in current["review_heads"]:
        return reject_existing(current, principal_id, request, payload_hash,
                               "selection", "base_mismatch", now)
    state = deepcopy(current)
    state["selected_base"] = base
    state["control_version"] += 1
    result = {"issue_date": date, "selected_base": base,
              "current_selected_base": base,
              "control_version": state["control_version"], "replayed": False}
    state["selection_receipts"][(principal_id, request["request_id"])] = _receipt(
        principal_id, date, request["request_id"], payload_hash, "selection",
        "applied", result, now)
    return IssueDecision(state, result=result)
