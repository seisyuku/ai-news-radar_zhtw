"""Small tool facade shared by authenticated MCP and HTTP callers."""

from copy import deepcopy
import hashlib

from .digest_cloud_editorial import EditorialError, _request_dict, _date, _identity
from .digest_json import canonical_json


TOOL_PERMISSIONS = {
    "get_digest_status": ["digest:read"],
    "read_digest": ["digest:read"],
    "apply_digest_edit": ["digest:read", "digest:edit"],
    "select_digest_base": ["digest:read", "digest:edit"],
}


class DigestTools:
    def __init__(self, editorial, status_reader):
        self.editorial = editorial
        self.status_reader = status_reader

    def _authorize(self, principal, tool):
        if tool not in TOOL_PERMISSIONS:
            raise EditorialError("invalid_request")
        for permission in TOOL_PERMISSIONS[tool]:
            self.editorial._actor(principal, permission)

    @staticmethod
    def _verified(snapshot):
        actual = hashlib.sha256(canonical_json(snapshot["content"]).encode("utf-8")).hexdigest()
        if actual != snapshot["content_sha256"]:
            raise EditorialError("integrity_error")
        return snapshot

    def call(self, principal, tool, raw):
        try:
            self._authorize(principal, tool)
            request = _request_dict(raw)
            if tool == "get_digest_status":
                if set(request) != {"issue_date"}:
                    raise EditorialError("invalid_request")
                _date(request["issue_date"])
                return self.status_reader.get_issue(request["issue_date"])
            if tool == "read_digest":
                if set(request) != {"issue_date", "base_identity", "revision", "story_ids"}:
                    raise EditorialError("invalid_request")
                _date(request["issue_date"])
                _identity(request["base_identity"])
                subset = request["story_ids"]
                if (subset is not None and (not isinstance(subset, list) or len(subset) > 20 or
                        any(not isinstance(x, str) or not x for x in subset) or len(set(subset)) != len(subset))):
                    raise EditorialError("invalid_request")
                snapshot = self._verified(self.editorial.read_review(
                    principal, request["issue_date"], request["base_identity"], request["revision"]))
                if subset is not None:
                    if not set(subset) <= set(snapshot["content"]["entries"]):
                        raise EditorialError("unknown_story")
                    snapshot["stories"] = [row for row in snapshot["stories"] if row["story_id"] in subset]
                snapshot["complete_stories"] = len(snapshot["stories"]) == len(snapshot["content"]["entries"])
                snapshot["total_stories"] = len(snapshot["content"]["entries"])
                snapshot.pop("content")  # Verified above; avoid duplicating full overrides on every page.
                return self._bounded(snapshot)
            if tool == "apply_digest_edit":
                result = self.editorial.apply_edit(principal, request)
                return self._readback(principal, request, result)
            result = self.editorial.select_base(principal, request)
            return {"committed": True, "result": result}
        except EditorialError as exc:
            result = {"error": exc.code}
            if exc.current_revision is not None:
                result["current_revision"] = exc.current_revision
            return result
        except Exception:
            return {"error": "storage_failed"}

    @staticmethod
    def _bounded(result):
        if len(canonical_json(result).encode("utf-8")) > 1024 * 1024:
            raise EditorialError("payload_limit")
        return result

    def _readback(self, principal, request, result):
        saved = {"committed": True, "verified": False, "result": deepcopy(result)}
        try:
            snapshot = self._verified(self.editorial.read_review(
                principal, request["issue_date"], request["base_identity"], result["applied_revision"]))
            if snapshot["content_sha256"] != result["content_sha256"]:
                raise EditorialError("integrity_error")
            saved["verified"] = True
            saved["applied_revision"] = snapshot["revision"]
            saved["current_revision"] = snapshot["current_revision"]
        except EditorialError as exc:
            saved["readback_error"] = exc.code
        except Exception:
            saved["readback_error"] = "storage_failed"
        return saved
