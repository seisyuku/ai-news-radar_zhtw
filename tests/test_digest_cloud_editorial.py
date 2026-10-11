"""C05 synthetic editorial concurrency, revision, undo, export and boundary cases."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import socket
import subprocess
from uuid import uuid4

import pytest

from scripts.digest_cloud_editorial import EditorialError, MockEditorialService, SimulatedPrincipal
from test_digest_cloud_mock import D, attempt, prepared, service


OWNER = SimulatedPrincipal("owner", True)


def two_story_items():
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
    return originals + [{**row, "id": row["id"] + "-corroboration",
                         "site_id": "curated_media" if row["site_id"] == "official_ai" else "official_ai",
                         "source": "Independent Publisher",
                         "url": row["url"] + "/corroboration"} for row in originals]


def setup(tmp_path):
    pair = prepared(tmp_path, items=two_story_items())
    delivery = service(tmp_path)
    delivery.commit_delivery(pair, attempt(pair))
    editor = MockEditorialService(delivery, owner_id="owner")
    initial = editor.read_review(OWNER, D, pair.base_identity)
    assert len(initial["stories"]) == 2
    return pair, delivery, editor, initial


def patch(pair, expected_revision, updates=None, order=None, request_id=None):
    return {"schema_version": 1, "request_id": request_id or str(uuid4()),
            "issue_date": D, "base_identity": pair.base_identity,
            "expected_revision": expected_revision, "operation": "patch",
            "ordered_story_ids": order, "updates": updates or {}}


def restore(pair, expected_revision, target):
    return {"schema_version": 1, "request_id": str(uuid4()),
            "issue_date": D, "base_identity": pair.base_identity,
            "expected_revision": expected_revision, "operation": "restore",
            "restore_revision": target}


def test_f26_simultaneous_voice_and_web_edits_have_one_winner(tmp_path):
    pair, delivery, editor, initial = setup(tmp_path)
    story = initial["ordinal_map"]["1"]
    requests = [patch(pair, 0, {story: {"title_override": name}}) for name in ("語音校稿", "網頁校稿")]
    def submit(request):
        try:
            return editor.apply_edit(OWNER, request)
        except EditorialError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, requests))
    assert sum(isinstance(row, dict) for row in results) == 1
    assert results.count("revision_conflict") == 1
    state = delivery.control.get_issue(D)
    assert state["review_heads"][pair.base_identity] == 1
    assert len(state["reviews"][pair.base_identity]) == 2


def test_f27_same_request_replays_once_and_changed_payload_conflicts(tmp_path):
    pair, delivery, editor, initial = setup(tmp_path)
    story = initial["ordinal_map"]["1"]
    request = patch(pair, 0, {story: {"included": False}})
    first = editor.apply_edit(OWNER, request)
    second = editor.apply_edit(OWNER, request)
    assert first["applied_revision"] == second["applied_revision"] == 1
    assert second["replayed"] and second["current_revision"] == 1
    with pytest.raises(EditorialError, match="idempotency_conflict"):
        editor.apply_edit(OWNER, {**request, "updates": {story: {"included": True}}})
    assert len(delivery.control.get_issue(D)["reviews"][pair.base_identity]) == 2


def test_f28_lost_response_replay_reports_applied_and_current_separately(tmp_path):
    pair, _, editor, initial = setup(tmp_path)
    story = initial["ordinal_map"]["1"]
    first_request = patch(pair, 0, {story: {"title_override": "第一版"}})
    editor.apply_edit(OWNER, first_request)
    editor.apply_edit(OWNER, patch(pair, 1, {story: {"title_override": "第二版"}}))
    replay = editor.apply_edit(OWNER, first_request)
    assert replay["applied_revision"] == 1 and replay["current_revision"] == 2
    assert replay["replayed"] and editor.read_review(OWNER, D, pair.base_identity)["stories"][0]["title"] == "第二版"
    assert editor.read_review(OWNER, D, pair.base_identity, 1)["stories"][0]["title"] == "第一版"


def test_f29_batch_with_unknown_story_is_all_or_nothing_and_receipted(tmp_path):
    pair, delivery, editor, initial = setup(tmp_path)
    story = initial["ordinal_map"]["1"]
    request = patch(pair, 0, {story: {"included": False}, "missing-story": {"included": False}})
    for _ in range(2):
        with pytest.raises(EditorialError, match="unknown_story"):
            editor.apply_edit(OWNER, request)
    state = delivery.control.get_issue(D)
    assert state["review_heads"][pair.base_identity] == 0
    assert editor.read_review(OWNER, D, pair.base_identity)["stories"][0]["included"]
    assert len(state["edit_receipts"]) == 1


def test_f30_reorder_invalidates_old_ordinal_mapping(tmp_path):
    pair, delivery, editor, initial = setup(tmp_path)
    old_first = initial["ordinal_map"]["1"]
    reverse = list(reversed(initial["content"]["ordered_story_ids"]))
    editor.apply_edit(OWNER, patch(pair, 0, order=reverse))
    current = editor.read_review(OWNER, D, pair.base_identity)
    assert current["ordinal_map"]["1"] != old_first
    with pytest.raises(EditorialError, match="revision_conflict"):
        editor.apply_edit(OWNER, patch(pair, 0, {old_first: {"included": False}}))
    assert all(row["included"] for row in editor.read_review(OWNER, D, pair.base_identity)["stories"])
    assert delivery.control.get_issue(D)["review_heads"][pair.base_identity] == 1


def test_f31_same_story_ids_across_bases_do_not_transfer_edits(tmp_path):
    first, delivery, editor, initial = setup(tmp_path)
    second = prepared(tmp_path, items=two_story_items(), cache=b'{"unused":"different"}',
                      slot="2026-10-09T00:15:00Z")
    delivery.commit_delivery(second, attempt(second))
    assert first.base_identity != second.base_identity
    first_ids = initial["content"]["ordered_story_ids"]
    second_before = editor.read_review(OWNER, D, second.base_identity)
    assert set(first_ids) == set(second_before["content"]["ordered_story_ids"])
    editor.apply_edit(OWNER, patch(first, 0, {first_ids[0]: {"title_override": "人工標題"}}))
    assert editor.read_review(OWNER, D, first.base_identity)["stories"][0]["title"] == "人工標題"
    assert editor.read_review(OWNER, D, second.base_identity)["stories"][0]["title"] != "人工標題"


def test_f32_restore_creates_new_revision_and_no_change_does_not(tmp_path):
    pair, delivery, editor, initial = setup(tmp_path)
    story = initial["ordinal_map"]["1"]
    editor.apply_edit(OWNER, patch(pair, 0, {story: {"included": False}}))
    returned = editor.apply_edit(OWNER, restore(pair, 1, 0))
    assert returned["applied_revision"] == 2
    assert editor.read_review(OWNER, D, pair.base_identity)["content"] == initial["content"]
    unchanged = editor.apply_edit(OWNER, patch(pair, 2))
    assert unchanged["result_code"] == "no_change" and unchanged["applied_revision"] == 2
    assert len(delivery.control.get_issue(D)["reviews"][pair.base_identity]) == 3
    assert len(delivery.control.get_issue(D)["edit_receipts"]) == 3


def test_f33_exclude_reinclude_select_base_and_export_immutable_revision(tmp_path):
    first, delivery, editor, initial = setup(tmp_path)
    story = initial["ordinal_map"]["1"]
    original = delivery.read_base(D, first.base_identity)["markdown"]
    editor.apply_edit(OWNER, patch(first, 0, {story: {"included": False}}))
    excluded_export = editor.export_review(OWNER, D, first.base_identity, 1)
    editor.apply_edit(OWNER, patch(first, 1, {story: {"included": True}}))
    second = prepared(tmp_path, items=two_story_items(), cache=b'{"unused":"different"}',
                      slot="2026-10-09T00:15:00Z")
    delivery.commit_delivery(second, attempt(second))
    current_version = delivery.get_issue(D)["control_version"]
    select = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": D,
              "base_identity": second.base_identity, "expected_control_version": current_version}
    chosen = editor.select_base(OWNER, select)
    assert chosen["selected_base"] == second.base_identity
    assert editor.select_base(OWNER, select)["replayed"]
    assert delivery.control.get_issue(D)["review_heads"][first.base_identity] == 2
    assert editor.read_review(OWNER, D, second.base_identity)["revision"] == 0
    export_again = editor.export_review(OWNER, D, first.base_identity, 1)
    assert excluded_export == export_again
    data = json.loads(excluded_export["bytes"])
    assert data["content"]["entries"][story]["included"] is False
    assert len(data["stories"]) == 2 and data["stories"][0]["title"]
    assert excluded_export["sha256"] == hashlib.sha256(excluded_export["bytes"]).hexdigest()
    assert delivery.read_base(D, first.base_identity)["markdown"] == original
    back = {**select, "request_id": str(uuid4()), "base_identity": first.base_identity,
            "expected_control_version": delivery.get_issue(D)["control_version"]}
    editor.select_base(OWNER, back)
    old_replay = editor.select_base(OWNER, select)
    assert old_replay["selected_base"] == second.base_identity
    assert old_replay["current_selected_base"] == first.base_identity


def test_selection_conflict_is_receipted_and_replay_stays_conflict(tmp_path):
    pair, delivery, editor, _ = setup(tmp_path)
    before = delivery.get_issue(D)["control_version"]
    request = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": D,
               "base_identity": pair.base_identity, "expected_control_version": before - 1}
    for _ in range(2):
        with pytest.raises(EditorialError, match="revision_conflict"):
            editor.select_base(OWNER, request)
    state = delivery.control.get_issue(D)
    assert len(state["selection_receipts"]) == 1
    assert state["selected_base"] == pair.base_identity
    assert state["control_version"] == before + 1


@pytest.mark.parametrize("bad", [
    {"extra": "ignored"}, {"expected_revision": True},
    {"operation": "publish"}, {"operation": []},
    {"updates": {"story": {"source_url": "https://invalid"}}},
    {"updates": {"story": {"included": 1}}},
    {"updates": {"story": {"summary_override": "x" * 32769}}},
])
def test_f34_bad_shape_is_rejected_without_revision(tmp_path, bad):
    pair, delivery, editor, _ = setup(tmp_path)
    request = {**patch(pair, 0), **bad}
    with pytest.raises(EditorialError) as exc:
        editor.apply_edit(OWNER, request)
    assert exc.value.code in {"invalid_request", "payload_limit"}
    assert delivery.control.get_issue(D)["review_heads"][pair.base_identity] == 0
    assert not delivery.control.get_issue(D)["edit_receipts"]


def test_f34_duplicate_json_nan_and_large_request_rejected(tmp_path):
    pair, delivery, editor, _ = setup(tmp_path)
    request = patch(pair, 0)
    wire = json.dumps(request).encode()
    duplicate = wire[:-1] + b',"operation":"patch"}'
    for bad in (duplicate, wire[:-1] + b',"extra":NaN}', b"{}", b"x" * (1024 * 1024 + 1)):
        with pytest.raises(EditorialError) as exc:
            editor.apply_edit(OWNER, bad)
        assert exc.value.code in {"invalid_request", "payload_limit"}
    assert delivery.control.get_issue(D)["review_heads"][pair.base_identity] == 0


def test_f34_unauthorized_read_write_select_export_are_denied(tmp_path):
    pair, delivery, editor, _ = setup(tmp_path)
    stranger = SimulatedPrincipal("stranger", False)
    for action in (
        lambda: editor.read_review(stranger, D, pair.base_identity),
        lambda: editor.apply_edit(stranger, patch(pair, 0)),
        lambda: editor.select_base(stranger, {"secret": "ignored"}),
        lambda: editor.export_review(stranger, D, pair.base_identity, 0),
    ):
        with pytest.raises(EditorialError, match="unauthorized"):
            action()
    assert not delivery.control.get_issue(D)["edit_receipts"]


def test_f35_injected_private_exception_is_sanitized(tmp_path, monkeypatch):
    pair, _, editor, _ = setup(tmp_path)
    def fail(*args, **kwargs):
        raise RuntimeError("SECRET_TOKEN /private/path draft text")
    monkeypatch.setattr(editor.delivery, "read_base", fail)
    with pytest.raises(EditorialError) as exc:
        editor.apply_edit(OWNER, patch(pair, 0))
    assert str(exc.value) == "integrity_error"
    monkeypatch.undo()
    monkeypatch.setattr(editor.control, "get_issue", fail)
    with pytest.raises(EditorialError) as exc:
        editor.read_review(OWNER, D, pair.base_identity)
    assert str(exc.value) == "integrity_error"


def test_f36_editorial_calls_do_not_use_network_or_subprocess(tmp_path, monkeypatch):
    pair, delivery, editor, initial = setup(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError("network_or_subprocess_called")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "check_output", forbidden)
    story = initial["ordinal_map"]["1"]
    editor.apply_edit(OWNER, patch(pair, 0, {story: {"included": False}}))
    assert editor.read_review(OWNER, D, pair.base_identity)["revision"] == 1
    assert editor.export_review(OWNER, D, pair.base_identity, 1)["content_type"].startswith("application/json")
