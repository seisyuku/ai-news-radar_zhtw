"""C07c owner/scope enforcement, commit evidence, and actual MCP HTTP auth."""

from dataclasses import replace
from datetime import datetime, timezone
import asyncio

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.testclient import TestClient

from scripts.digest_cloud_auth import JWTVerifier, VerifiedOwnerPolicy
from scripts.digest_cloud_editorial import EditorialService, EditorialError
from scripts.digest_cloud_mcp import build_mcp_app, build_mcp_server
from scripts.digest_cloud_tools import DigestTools
from test_digest_cloud_editorial import D, patch, setup


ISSUER = "https://issuer.example.invalid"
RESOURCE = "http://127.0.0.1:8000/mcp"


@pytest.fixture(scope="module")
def key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def verifier(key):
    return JWTVerifier(issuer=ISSUER, resource=RESOURCE, owner_subject="fixture-owner",
                       owner_id="owner", resolve_key=lambda kid: key.public_key() if kid == "fixture" else None,
                       allow_loopback=True)


def token(key, *, changes=None, scope="digest:read digest:edit", kid="fixture"):
    now = int(datetime.now(timezone.utc).timestamp())
    claims = {"iss": ISSUER, "sub": "fixture-owner", "aud": RESOURCE,
              "iat": now - 1, "exp": now + 3600, "client_id": "fixture-client", "scope": scope}
    claims.update(changes or {})
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def configured(tmp_path, key):
    pair, delivery, _, initial = setup(tmp_path)
    editor = EditorialService(delivery, owner_id="owner",
                              policy=VerifiedOwnerPolicy(ISSUER, "fixture-owner"))
    tools = DigestTools(editor, delivery)
    auth = verifier(key)
    return pair, delivery, editor, tools, auth, auth.verify(token(key)), initial


@pytest.mark.parametrize("changes", [
    {"iss": "https://wrong.example.invalid"}, {"aud": "https://other-resource.example.invalid"},
    {"sub": "another-owner"}, {"exp": 0}, {"iat": True}, {"exp": True},
    {"nbf": 9999999999}, {"scope": ["digest:edit"]}, {"client_id": ""},
])
def test_invalid_signed_claims_are_denied(key, changes):
    assert verifier(key).verify(token(key, changes=changes)) is None


def test_wrong_signature_unknown_key_and_algorithm_are_denied(key):
    auth = verifier(key)
    assert auth.verify(token(rsa.generate_private_key(public_exponent=65537, key_size=2048))) is None
    assert auth.verify(token(key, kid="unknown")) is None
    assert auth.verify(jwt.encode({"sub": "fixture-owner"}, "fixture-only-secret" * 3, algorithm="HS256")) is None


def test_read_only_and_forged_identity_never_mutate_state(tmp_path, key):
    pair, delivery, _, tools, auth, principal, _ = configured(tmp_path, key)
    before = delivery.control.get_issue(D)
    read_only = auth.verify(token(key, scope="digest:read"))
    assert tools.call(read_only, "get_digest_status", {"issue_date": D})["issue_date"] == D
    for bad in (read_only, None, {"principal_id": "owner"}, replace(principal, expires_at=0)):
        assert tools.call(bad, "apply_digest_edit", patch(pair, 0)) == {"error": "unauthorized"}
    assert delivery.control.get_issue(D) == before


def test_saved_readback_failure_keeps_commit_evidence_and_original_request(tmp_path, key, monkeypatch):
    pair, delivery, editor, tools, _, principal, initial = configured(tmp_path, key)
    story = initial["ordinal_map"]["1"]
    request = patch(pair, 0, {story: {"title_override": "保存但讀回中斷"}})
    with monkeypatch.context() as patcher:
        patcher.setattr(editor, "read_review", lambda *a: (_ for _ in ()).throw(EditorialError("integrity_error")))
        result = tools.call(principal, "apply_digest_edit", request)
    assert result["committed"] and not result["verified"] and result["readback_error"] == "integrity_error"
    replay = tools.call(principal, "apply_digest_edit", request)
    assert replay["verified"] and replay["result"]["replayed"] and replay["applied_revision"] == 1
    assert len(delivery.control.get_issue(D)["edit_receipts"]) == 1


def test_partial_story_read_is_explicit_and_revision_corruption_is_rejected(tmp_path, key):
    pair, delivery, _, tools, _, principal, initial = configured(tmp_path, key)
    request = {"issue_date": D, "base_identity": pair.base_identity, "revision": None,
               "story_ids": [initial["ordinal_map"]["1"]]}
    result = tools.call(principal, "read_digest", request)
    assert not result["complete_stories"] and len(result["stories"]) == 1 and result["total_stories"] == 2
    delivery.control._issues[D]["reviews"][pair.base_identity][0]["content_sha256"] = "0" * 64
    assert tools.call(principal, "read_digest", request) == {"error": "integrity_error"}


def test_http_mcp_auth_discovery_tools_and_scope_rejection(tmp_path, key):
    pair, delivery, _, tools, auth, _, _ = configured(tmp_path, key)
    app = build_mcp_app(tools, auth)
    headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25"}
    before = delivery.control.get_issue(D)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        discovery = client.get("/.well-known/oauth-protected-resource/mcp").json()
        assert discovery["resource"] == RESOURCE
        assert discovery["authorization_servers"] == [ISSUER]
        rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        denied = client.post("/mcp", json=rpc, headers=headers)
        assert denied.status_code == 401 and "resource_metadata=" in denied.headers["www-authenticate"]
        bad_headers = {**headers, "Authorization": "Bearer " + token(key, changes={"sub": "stranger"})}
        assert client.post("/mcp", json=rpc, headers=bad_headers).status_code == 401
        allowed = {**headers, "Authorization": "Bearer " + token(key)}
        duplicate = b'{"jsonrpc":"2.0","id":1,"id":2,"method":"tools/list"}'
        assert client.post("/mcp", content=duplicate, headers={**allowed, "Content-Type": "application/json"}).status_code == 400
        nan = b'{"jsonrpc":"2.0","id":NaN,"method":"tools/list"}'
        assert client.post("/mcp", content=nan, headers={**allowed, "Content-Type": "application/json"}).status_code == 400
        listed = client.post("/mcp", json=rpc, headers=allowed).json()["result"]["tools"]
        assert {x["name"] for x in listed} == {"get_digest_status", "read_digest", "apply_digest_edit", "select_digest_base"}
        edit = next(x for x in listed if x["name"] == "apply_digest_edit")
        assert edit["securitySchemes"][0]["scopes"] == ["digest:read", "digest:edit"]
        assert edit["securitySchemes"] == edit["_meta"]["securitySchemes"]
        assert edit["annotations"]["readOnlyHint"] is False
        read_only = {**headers, "Authorization": "Bearer " + token(key, scope="digest:read")}
        call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "apply_digest_edit", "arguments": {"request": patch(pair, 0)}}}
        rejected = client.post("/mcp", json=call, headers=read_only).json()["result"]
        assert rejected["isError"] and rejected["structuredContent"]["error"] == "unauthorized"
        assert "mcp/www_authenticate" in rejected["_meta"]
        assert delivery.control.get_issue(D) == before
        story = next(iter(before["reviews"][pair.base_identity][0]["content"]["entries"]))
        call["params"]["arguments"]["request"] = patch(pair, 0, {story: {"title_override": "HTTP已保存"}})
        saved = client.post("/mcp", json=call, headers=allowed).json()["result"]["structuredContent"]
        assert saved["committed"] and saved["verified"] and saved["applied_revision"] == 1
        read = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "read_digest", "arguments": {"request": {"issue_date": D,
                "base_identity": pair.base_identity, "revision": None, "story_ids": [story]}}}}
        readback = client.post("/mcp", json=read, headers=allowed).json()["result"]["structuredContent"]
        assert readback["stories"][0]["title"] == "HTTP已保存"


def test_in_memory_sdk_calls_do_not_bypass_missing_http_identity(tmp_path, key):
    pair, _, _, tools, auth, _, _ = configured(tmp_path, key)
    server = build_mcp_server(tools, auth)
    result = asyncio.run(server.call_tool("apply_digest_edit", {"request": patch(pair, 0)}))
    assert result.is_error and result.structured_content["error"] == "unauthorized"
