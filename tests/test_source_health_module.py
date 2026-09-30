"""The health boundary works without source adapters or the generator."""

import importlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest


PROJECT = Path(__file__).resolve().parents[1]
NOW = "2026-09-30T08:00:00Z"


def health():
    return importlib.import_module("scripts.source_health")


def test_minimal_contracts_require_identity_without_rejecting_legacy_extensions():
    module = health()
    assert module.SiteStatus.__required_keys__ == {"site_id"}
    assert module.SubsourceStatus.__required_keys__ == {"source_id"}
    assert module.PersistentFailure.__required_keys__ == {"site_id", "consecutive_failures"}
    assert {"last_attempt_ok", "consecutive_failures", "last_success_at"} <= module.SiteStatus.__optional_keys__


@pytest.mark.parametrize("package", [True, False])
def test_module_import_and_health_transition_need_only_standard_library(tmp_path, package):
    code = '''
import importlib.abc
import importlib
import sys
class RejectSourceStack(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'update_news', 'scripts.update_news', 'requests', 'bs4', 'dateutil', 'feedparser'}:
            raise AssertionError('health imported source stack: ' + fullname)
sys.meta_path.insert(0, RejectSourceStack())
h = importlib.import_module(sys.argv[1])
current = {'site_id': 'official_ai', 'ok': True, 'subsources': [
    {'source_id': 'quiet', 'ok': True, 'item_count': 0, 'error': None},
    {'source_id': 'broken', 'ok': False, 'item_count': 0, 'error': 'fetch_failed'}]}
previous = {'sites': [{'site_id': 'official_ai', 'subsources': [
    {'source_id': 'broken', 'ok': False, 'consecutive_failures': 2}]}]}
alerts = h.apply_source_health_history([current], previous, '2026-09-30T08:00:00Z')
assert current['subsources'][0]['last_success_at'] == '2026-09-30T08:00:00Z'
assert current['subsources'][1]['consecutive_failures'] == 3
assert [(r['site_id'], r['source_id']) for r in alerts] == [('official_ai', 'broken')]
assert 'update_news' not in sys.modules and 'scripts.update_news' not in sys.modules
'''
    result = subprocess.run(
        [sys.executable, "-c", code, "scripts.source_health" if package else "source_health"],
        cwd=tmp_path, capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONPATH": str(PROJECT if package else PROJECT / "scripts"),
             "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("payload", [None, "{invalid", "[]", "null", '{"sites": [], "extension": 1}'])
def test_health_loader_preserves_lenient_snapshot_policy(tmp_path, payload):
    path = tmp_path / "source-status.json"
    if payload is not None:
        path.write_text(payload)
    expected = {"sites": [], "extension": 1} if payload and "extension" in payload else {}
    assert health().load_source_status(path) == expected
    if payload is not None:
        assert path.read_text() == payload


@pytest.mark.parametrize("exception,error", [(ValueError, "invalid_source"), (RuntimeError, "fetch_failed")])
def test_subsource_diagnostics_never_export_exception_details(exception, error):
    def broken():
        raise exception("secret=never-export user@example.invalid https://private.invalid/feed")
    items, status = health().fetch_subsource_with_status("public_id", broken)
    assert items == []
    assert status == {"source_id": "public_id", "ok": False, "item_count": 0, "error": error}


def test_valid_empty_fetch_is_success_and_partial_group_keeps_child_rows():
    module = health()
    items, quiet = module.fetch_subsource_with_status("quiet", lambda: [])
    failed = {"source_id": "failed", "ok": False, "item_count": 0, "error": "fetch_failed"}
    rows = [quiet, failed]
    details = module.summarize_subsources(rows)
    assert items == [] and quiet["ok"] is True
    assert details["subsources"] is rows
    assert details["ok"] is True and details["degraded"] is True
    assert details["degraded_reason"] == "partial_subsource_failure"
    assert module.summarize_subsources([failed])["error"] == "all_subsources_failed"
    assert module.summarize_subsources([])["ok"] is False


def test_generator_wrapper_serializes_clock_and_retains_extension_fields():
    from scripts import update_news
    current = [{"site_id": "legacy", "ok": False, "extension": {"keep": True}}]
    previous = {"sites": [{"site_id": "legacy", "ok": False, "consecutive_failures": 2}]}
    saved_previous = deepcopy(previous)
    direct = deepcopy(current)
    expected = health().apply_source_health_history(direct, previous, NOW)
    actual = update_news.apply_source_health_history(
        current, previous, datetime(2026, 9, 30, 8, tzinfo=timezone.utc))
    assert actual == expected and current == direct
    assert current[0]["extension"] == {"keep": True}
    assert previous == saved_previous


def test_report_preserves_workflow_and_markdown_escaping(tmp_path, monkeypatch, capsys):
    summary = tmp_path / "summary.md"
    summary.write_text("existing\n")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    alerts = [{"site_id": "official_ai", "source_id": "public_id", "consecutive_failures": 3,
               "first_failure_at": NOW, "error": "rate 50% | line\r\nnext"}]
    original = deepcopy(alerts)
    health().report_persistent_source_failures(alerts)
    assert capsys.readouterr().out == (
        "::warning file=data/source-status.json,title=Persistent source failure::"
        "official_ai/public_id failed 3 consecutive runs: rate 50%25 | line%0D%0Anext\n")
    assert summary.read_text().startswith("existing\n")
    assert "official_ai/public_id | 3 | " + NOW in summary.read_text()
    assert "rate 50% \\| line\n next" in summary.read_text()
    assert alerts == original
    size = summary.stat().st_size
    health().report_persistent_source_failures([])
    assert summary.stat().st_size == size and capsys.readouterr().out == ""


def test_public_health_payload_retains_generator_sanitization_policy():
    from scripts import update_news
    current = [{"site_id": "legacy", "ok": False, "error": "secret=never-export user@example.invalid"}]
    alerts = health().apply_source_health_history(current, {}, NOW, threshold=1)
    payload = update_news.sanitize_public_payload({"sites": current, "persistent_failures": alerts})
    serialized = json.dumps(payload)
    assert "never-export" not in serialized and "user@example.invalid" not in serialized
    assert "[redacted-secret]" in serialized and "[redacted-email]" in serialized
    assert current[0]["error"] == "secret=never-export user@example.invalid"


@pytest.mark.parametrize("source_id", [None, "public_id"])
def test_generator_report_redacts_public_diagnostics_without_changing_history(tmp_path, monkeypatch, capsys, source_id):
    from scripts import update_news
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    alerts = [{"site_id": "official_ai", "consecutive_failures": 3,
               "first_failure_at": NOW,
               "error": "secret=synthetic-only-marker user@example.invalid rate 50% | line\r\nnext"}]
    if source_id:
        alerts[0]["source_id"] = source_id
    original = deepcopy(alerts)

    update_news.report_persistent_source_failures(alerts)

    warning, table = capsys.readouterr().out, summary.read_text()
    for output in (warning, table):
        assert "synthetic-only-marker" not in output and "user@example.invalid" not in output
        assert "[redacted-secret] [redacted-email]" in output
    label = "official_ai/public_id" if source_id else "official_ai"
    assert label + " failed 3 consecutive runs:" in warning
    assert "rate 50%25 | line%0D%0Anext" in warning
    assert label + " | 3 | " + NOW in table
    assert "rate 50% \\| line\n next" in table
    assert alerts == original
