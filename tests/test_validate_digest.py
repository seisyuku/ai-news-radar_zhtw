"""Public CI summaries cannot expose private drafts, payloads or errors."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest
import yaml

from scripts import validate_digest as validation


NOW = datetime(2026, 10, 2, 23, 15, tzinfo=timezone.utc)
COMMIT = "a" * 40


def get(url):
    if url.endswith("/heads/master"):
        return json.dumps({"object": {"sha": COMMIT}}).encode()
    assert url.endswith("?ref=" + COMMIT)
    name = url.split("?")[0].rsplit("/", 1)[-1]
    if name == "archive.json":
        return json.dumps({"generated_at": "2026-10-02T22:05:00Z", "items": []}).encode()
    if name == "source-status.json":
        return json.dumps({"generated_at": "2026-10-02T22:05:00Z", "sites": []}).encode()
    return b'{"PRIVATE title":"PRIVATE draft"}'


def test_empty_ready_pair_rerun_and_cleanup(tmp_path):
    report = validation.validate("2026-10-03", get=get, clock=lambda: NOW, parent=tmp_path)
    assert report["status"] == "ready-for-review" and report["selected_count"] == 0
    assert report["pair_verified"] and report["rerun_identical"]
    assert report["source_commit"] == COMMIT
    assert not list(tmp_path.iterdir())
    assert "PRIVATE" not in json.dumps(report) and str(tmp_path) not in json.dumps(report)


def test_review_only_checks_pair_without_claiming_ready(tmp_path):
    report = validation.validate("2026-10-03", get=get, clock=lambda: datetime(2026, 10, 3, 2, tzinfo=timezone.utc), parent=tmp_path)
    assert report["status"] == "review-only" and report["reason"] == "archive_stale"
    assert report["pair_verified"] and report["rerun_identical"]
    assert not list(tmp_path.iterdir())


def test_failed_download_sanitizes_and_removes_inputs(tmp_path):
    def failed(url):
        if "archive.json" in url:
            raise OSError("SECRET draft credentials")
        return get(url)
    report = validation.validate("2026-10-03", get=failed, clock=lambda: NOW, parent=tmp_path)
    assert report["status"] == "failed" and not report["pair_verified"]
    assert "SECRET" not in json.dumps(report) and not list(tmp_path.iterdir())


def test_rerun_mismatch_is_failed_and_not_retained(tmp_path, monkeypatch):
    write = validation.write_digest
    def changed(*args):
        paths = write(*args)
        paths[0].write_text("PRIVATE altered rerun")
        return paths
    monkeypatch.setattr(validation, "write_digest", changed)
    report = validation.validate("2026-10-03", get=get, clock=lambda: NOW, parent=tmp_path)
    assert report["status"] == "failed" and report["reason"] == "validation_failed"
    assert not list(tmp_path.iterdir())


def test_scheduled_creation_date_and_cross_day_delay():
    assert validation.issue_date(None, "2026-10-02T23:15:00Z", NOW) == ("2026-10-03", False)
    later = datetime(2026, 10, 3, 17, tzinfo=timezone.utc)
    assert validation.issue_date(None, "2026-10-02T23:15:00Z", later) == ("2026-10-03", True)
    assert validation.issue_date("2026-10-03", None, later) == ("2026-10-03", False)


@pytest.mark.parametrize("status,code", [("ready-for-review", 0), ("review-only", 3), ("failed", 1)])
def test_main_summary_and_exit(tmp_path, monkeypatch, capsys, status, code):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setattr(validation, "validate", lambda *a, **k: {"status": status, "reason": "validation_failed"})
    assert validation.main(["--date", "2026-10-03"]) == code
    output = capsys.readouterr().out
    assert json.loads(output)["status"] == status
    assert output.strip() in summary.read_text()


def test_invalid_date_rejected_before_network():
    with pytest.raises(SystemExit) as result:
        validation.main(["--date", "2026-02-30"])
    assert result.value.code == 2


@pytest.mark.parametrize("returncode,stderr,expected", [(1, b"HTTP 404", "not_found"), (1, b"SECRET", "download_failed")])
def test_github_read_failure_has_only_controlled_codes(monkeypatch, returncode, stderr, expected):
    def fake(argv, **kwargs):
        assert "--method" in argv and "GET" in argv
        assert kwargs["timeout"] == 50
        return SimpleNamespace(returncode=returncode, stderr=stderr, stdout=b"")
    monkeypatch.setattr(validation.subprocess, "run", fake)
    with pytest.raises(validation.delivery.DeliveryError, match=expected):
        validation.github_get("https://api.github.com/repos/example/contents/data")


def test_github_read_hard_timeout(monkeypatch):
    def timeout(*a, **k):
        raise subprocess.TimeoutExpired("SECRET", 50)
    monkeypatch.setattr(validation.subprocess, "run", timeout)
    with pytest.raises(validation.delivery.DeliveryError, match="^download_failed$"):
        validation.github_get("https://api.github.com/test")


def test_workflow_is_read_only_and_has_no_artifact_publication():
    path = Path(__file__).resolve().parents[1] / ".github/workflows/digest-validation.yml"
    text = path.read_text()
    document = yaml.safe_load(text)
    triggers = document.get("on", document.get(True))
    assert {row["cron"] for row in triggers["schedule"]} == {"15 23 * * *", "15 0 * * *"}
    assert document["permissions"] == {"contents": "read", "actions": "read"}
    steps = document["jobs"]["validate"]["steps"]
    assert not any("upload-artifact" in row.get("uses", "") for row in steps)
    assert all("git push" not in row.get("run", "") and "update_news.py" not in row.get("run", "") for row in steps)
    assert document["concurrency"]["cancel-in-progress"] is False
