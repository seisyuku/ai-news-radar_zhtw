import io
import json
import zipfile

from scripts import t04_delivery_watchdog as watchdog
from scripts import t04_notify


def test_terminal_email_reports_steps_and_safe_stage_only(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/radar")
    monkeypatch.setattr(t04_notify, "github_json", lambda _path: {"jobs": [{
        "name": "synthetic-only", "status": "completed", "conclusion": "failure",
        "steps": [{"name": "Evaluate synthetic summaries", "status": "completed",
                   "conclusion": "failure"}],
    }]})
    record = tmp_path / "stages.jsonl"
    record.write_text(json.dumps({"stage": "gemini_cases", "status": "failed",
                                  "counts": {"failed": 1}}) + "\n")
    subject, body = t04_notify.report("123", str(record))
    assert "失敗或中斷" in subject
    assert "Evaluate synthetic summaries: failure" in body
    assert "gemini_cases: failed" in body
    assert "https://github.com/example/radar/actions/runs/123" in body


def test_watchdog_reads_accepted_receipt(monkeypatch):
    receipt = {"run_id": "123", "delivery": {"status": "provider_accepted"}}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("t04-receipt.json", json.dumps(receipt))

    def fake_get(path, *, binary=False):
        if path.endswith("/artifacts?per_page=100"):
            return {"total_count": 1, "artifacts": [{"name": "t04-email-receipt",
                                                   "id": 9, "expired": False}]}
        assert path == "actions/artifacts/9/zip" and binary
        return buffer.getvalue()

    monkeypatch.setattr(watchdog, "get", fake_get)
    assert watchdog.accepted_receipt(123)


def test_watchdog_accepts_successful_email_step_when_artifact_missing(monkeypatch):
    def fake_get(path, *, binary=False):
        if path.endswith("/artifacts?per_page=100"):
            return {"total_count": 0, "artifacts": []}
        assert path.endswith("/jobs?per_page=100&filter=latest") and not binary
        return {"jobs": [{"name": "notify", "steps": [
            {"name": "Email terminal result", "conclusion": "success"}]}]}

    monkeypatch.setattr(watchdog, "get", fake_get)
    assert watchdog.accepted_receipt(123)


def test_watchdog_missing_run_email_is_explicit(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/radar")
    payload = watchdog.compose([])
    assert "排程未啟動" in payload["subject"]
    assert "沒有 T04 workflow_dispatch run" in payload["body"]
    assert "payload_hash" in payload
