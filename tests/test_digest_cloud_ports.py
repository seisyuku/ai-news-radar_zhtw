"""C07a exercises service ports with a real rollback-capable SQLite boundary.

The adapter below is a test fixture, not a production cloud storage adapter.
"""

from copy import deepcopy
from datetime import datetime, timezone
import json
import sqlite3

import pytest

from scripts.digest_cloud_editorial import EditorialError, EditorialService
from test_digest_cloud_editorial import D, OWNER, patch, setup


class SQLiteBoundary:
    def __init__(self, path, seed=None):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS issues (date TEXT PRIMARY KEY, state TEXT NOT NULL)")
        if seed is not None:
            self.db.execute("INSERT INTO issues VALUES (?, ?)", (D, self.encode(seed)))
            self.db.commit()

    @staticmethod
    def encode(state):
        value = deepcopy(state)
        for field in ("edit_receipts", "selection_receipts"):
            value[field] = [[*key, row] for key, row in value[field].items()]
        return json.dumps(value, ensure_ascii=False, allow_nan=False)

    def get_issue(self, date):
        row = self.db.execute("SELECT state FROM issues WHERE date=?", (date,)).fetchone()
        value = json.loads(row[0])
        for field in ("edit_receipts", "selection_receipts"):
            value[field] = {(actor, request): receipt for actor, request, receipt in value[field]}
        return value

    def transact_issue(self, date, decide):
        # sqlite rolls back when the callback raises inside this context.
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            decision = decide(self.get_issue(date), datetime(2026, 10, 9, 0, 45, tzinfo=timezone.utc))
            if decision.state is not None:
                self.db.execute("UPDATE issues SET state=? WHERE date=?", (self.encode(decision.state), date))
        return decision


class OriginalReader:
    def __init__(self, delivery):
        self.delivery = delivery

    def read_base(self, date, base):
        return self.delivery.read_base(date, base)


class FixtureOwnerPolicy:
    def require(self, principal, owner, permission):
        if principal is not OWNER or owner != OWNER.principal_id:
            raise EditorialError("unauthorized")
        return principal.principal_id


def service(tmp_path):
    pair, delivery, _, initial = setup(tmp_path)
    path = tmp_path / "transaction.sqlite"
    control = SQLiteBoundary(path, delivery.control.get_issue(D))
    original = OriginalReader(delivery)
    editor = EditorialService(original, owner_id=OWNER.principal_id,
                              control=control, policy=FixtureOwnerPolicy())
    return pair, original, path, control, editor, initial


def reopen(original, path):
    control = SQLiteBoundary(path)
    return control, EditorialService(original, owner_id=OWNER.principal_id,
                                     control=control, policy=FixtureOwnerPolicy())


def test_permanent_rejection_commits_before_error_and_survives_reopen(tmp_path):
    pair, original, path, control, editor, _ = service(tmp_path)
    request = patch(pair, 1)
    with pytest.raises(EditorialError, match="revision_conflict"):
        editor.apply_edit(OWNER, request)
    control.db.close()
    control, editor = reopen(original, path)
    with pytest.raises(EditorialError, match="revision_conflict"):
        editor.apply_edit(OWNER, request)
    with pytest.raises(EditorialError, match="idempotency_conflict"):
        editor.apply_edit(OWNER, {**request, "expected_revision": 0})
    state = control.get_issue(D)
    assert len(state["edit_receipts"]) == 1
    assert state["review_heads"][pair.base_identity] == 0
    control.db.close()


def test_lost_success_replays_after_reopen_without_overwriting_later_revision(tmp_path):
    pair, original, path, control, editor, initial = service(tmp_path)
    story = initial["ordinal_map"]["1"]
    request = patch(pair, 0, {story: {"title_override": "已保存的第一版"}})
    editor.apply_edit(OWNER, request)
    control.db.close()
    control, editor = reopen(original, path)
    editor.apply_edit(OWNER, patch(pair, 1, {story: {"title_override": "第二版"}}))
    replay = editor.apply_edit(OWNER, request)
    assert replay["replayed"] and replay["applied_revision"] == 1 and replay["current_revision"] == 2
    assert editor.read_review(OWNER, D, pair.base_identity)["stories"][0]["title"] == "第二版"
    control.db.close()


def test_unexpected_transaction_exception_leaves_snapshot_unchanged(tmp_path):
    _, _, _, control, _, _ = service(tmp_path)
    before = control.get_issue(D)

    def failing(snapshot, now):
        snapshot["selected_base"] = None
        raise RuntimeError("infrastructure_failure")

    with pytest.raises(RuntimeError, match="infrastructure_failure"):
        control.transact_issue(D, failing)
    assert control.get_issue(D) == before
    control.db.close()


def test_identity_policy_denial_precedes_original_read_and_transaction(tmp_path, monkeypatch):
    pair, original, _, control, editor, _ = service(tmp_path)
    before = control.get_issue(D)

    def forbidden(*args, **kwargs):
        pytest.fail("denied identity reached storage")

    monkeypatch.setattr(original, "read_base", forbidden)
    monkeypatch.setattr(control, "transact_issue", forbidden)
    with pytest.raises(EditorialError, match="unauthorized"):
        editor.apply_edit(object(), patch(pair, 0))
    assert control.get_issue(D) == before
    control.db.close()
