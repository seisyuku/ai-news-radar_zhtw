"""C06 loopback preview: synthetic fixture, WSGI boundary and C05 readback."""

from io import BytesIO
import hashlib
import json
import socket
import subprocess
from uuid import uuid4

import pytest

from scripts.digest_cloud_preview import MAX_BODY, build_synthetic_preview
from test_digest_cloud_editorial import two_story_items
from test_digest_cloud_mock import attempt, prepared


ORIGIN = "http://127.0.0.1:8765"


@pytest.fixture
def app(tmp_path):
    return build_synthetic_preview(tmp_path, "2026-10-09", origin=ORIGIN, token="test-token")


def call(app, method, path, *, query="", payload=None, token=True, origin=True, host=True,
         content_type="application/json"):
    raw = b"" if payload is None else (payload if isinstance(payload, bytes) else json.dumps(payload).encode())
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
               "HTTP_HOST": "127.0.0.1:8765" if host else "evil.invalid",
               "HTTP_X_PREVIEW_TOKEN": "test-token" if token else "wrong",
               "HTTP_ORIGIN": ORIGIN if origin else "https://evil.invalid",
               "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(len(raw)),
               "wsgi.input": BytesIO(raw)}
    observed = {}
    def start_response(status, headers):
        observed["status"] = status
        observed["headers"] = dict(headers)
    observed["body"] = b"".join(app(environ, start_response))
    return observed


def result_json(row):
    return json.loads(row["body"])


def test_synthetic_preview_has_two_addressable_stories_and_secure_no_cache_boundary(app):
    page = call(app, "GET", "/", token=False)
    assert page["status"] == "200 OK" and b"test-token" in page["body"]
    assert b"<html lang=\"zh-Hant\">" in page["body"]
    assert b"<label for=\"restore-revision\">" in page["body"]
    assert page["headers"]["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in page["headers"]["Content-Security-Policy"]
    assert call(app, "GET", "/", host=False)["status"] == "403 Forbidden"
    assert call(app, "GET", "/api/status", token=False)["status"] == "403 Forbidden"

    status = result_json(call(app, "GET", "/api/status"))
    assert status["synthetic"] and not status["durable"]
    assert status["delivery_count"] == 1 and status["integrity"] == "verified"
    base = status["selected_base"]
    review = result_json(call(app, "GET", "/api/review", query=f"base={base}"))
    assert review["revision"] == 0 and review["current_revision"] == 0
    assert len(review["stories"]) == 2
    assert review["ordinal_map"] == {str(i): story["story_id"] for i, story in enumerate(review["stories"], 1)}
    assert all(story["sources"] for story in review["stories"])


def test_edit_readback_conflict_restore_export_and_original_immutability(app):
    status = result_json(call(app, "GET", "/api/status"))
    base = status["selected_base"]
    before = result_json(call(app, "GET", "/api/review", query=f"base={base}"))
    original = app.delivery.read_base(app.issue_date, base)["markdown"]
    first = before["ordinal_map"]["1"]
    request = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": app.issue_date,
               "base_identity": base, "expected_revision": 0, "operation": "patch",
               "ordered_story_ids": None,
               "updates": {first: {"included": False, "title_override": "口述校稿標題"}}}
    applied = result_json(call(app, "POST", "/api/edit", payload=request))
    assert applied["applied_revision"] == 1 and applied["result_code"] == "applied"
    exact = result_json(call(app, "GET", "/api/revision", query=f"base={base}&revision=1"))
    assert exact["content_sha256"] == applied["content_sha256"]
    assert exact["stories"][0]["title"] == "口述校稿標題"
    assert exact["stories"][0]["included"] is False
    assert result_json(call(app, "POST", "/api/edit", payload=request))["replayed"]

    stale = {**request, "request_id": str(uuid4()), "updates": {first: {"included": True}}}
    conflict = call(app, "POST", "/api/edit", payload=stale)
    assert conflict["status"] == "409 Conflict"
    assert result_json(conflict) == {"error": "revision_conflict", "current_revision": 1}
    assert result_json(call(app, "GET", "/api/review", query=f"base={base}"))["revision"] == 1

    restore = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": app.issue_date,
               "base_identity": base, "expected_revision": 1, "operation": "restore", "restore_revision": 0}
    restored = result_json(call(app, "POST", "/api/edit", payload=restore))
    assert restored["applied_revision"] == 2
    current = result_json(call(app, "GET", "/api/review", query=f"base={base}"))
    assert current["content"] == before["content"] and current["revision"] == 2
    exported = call(app, "GET", "/api/export", query=f"base={base}&revision=1")
    assert exported["status"] == "200 OK"
    assert exported["headers"]["X-Content-SHA256"] == hashlib.sha256(exported["body"]).hexdigest()
    assert json.loads(exported["body"])["stories"][0]["title"] == "口述校稿標題"
    assert app.delivery.read_base(app.issue_date, base)["markdown"] == original


def test_explicit_base_selection_and_stale_control_rejection(app, tmp_path):
    first_status = result_json(call(app, "GET", "/api/status"))
    first_base = first_status["selected_base"]
    second = prepared(tmp_path, items=two_story_items(), slot="2026-10-09T00:15:00Z")
    app.delivery.commit_delivery(second, attempt(second))
    assert second.base_identity != first_base
    status = result_json(call(app, "GET", "/api/status"))
    assert len(status["bases"]) == 2 and status["selected_base"] == first_base
    select = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": app.issue_date,
              "base_identity": second.base_identity, "expected_control_version": status["control_version"]}
    chosen = result_json(call(app, "POST", "/api/select", payload=select))
    assert chosen["selected_base"] == second.base_identity
    assert result_json(call(app, "GET", "/api/status"))["selected_base"] == second.base_identity
    stale = {**select, "request_id": str(uuid4()), "base_identity": first_base}
    rejected = call(app, "POST", "/api/select", payload=stale)
    assert rejected["status"] == "409 Conflict"
    assert result_json(rejected)["error"] == "revision_conflict"
    assert result_json(call(app, "GET", "/api/status"))["selected_base"] == second.base_identity


def test_api_rejects_cross_origin_host_bad_body_and_bad_query_without_edit(app):
    base = result_json(call(app, "GET", "/api/status"))["selected_base"]
    before = app.delivery.control.get_issue(app.issue_date)["review_heads"][base]
    for response in (
        call(app, "POST", "/api/edit", payload=b"{}", origin=False),
        call(app, "POST", "/api/edit", payload=b"{}", host=False),
        call(app, "POST", "/api/edit", payload=b"{}", token=False),
        call(app, "POST", "/api/edit", payload=b"{}", content_type="text/plain"),
        call(app, "GET", "/api/review", query=f"base={base}&base={base}"),
        call(app, "GET", "/api/revision", query=f"base={base}&revision=NaN"),
        call(app, "POST", "/api/edit", payload=b"x" * (MAX_BODY + 1)),
    ):
        assert response["status"] != "200 OK"
        assert response["headers"]["Cache-Control"] == "no-store"
    assert app.delivery.control.get_issue(app.issue_date)["review_heads"][base] == before


def test_preview_seed_does_not_call_network_or_shell(monkeypatch, tmp_path):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("network_or_shell_call")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    preview = build_synthetic_preview(tmp_path, "2026-10-09", origin=ORIGIN)
    assert len(preview._status()["bases"]) == 1
