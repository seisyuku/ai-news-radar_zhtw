import json

from scripts import workflow_result_email as notify


def test_generic_terminal_report_uses_configured_job_and_safe_checkpoints(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/radar")
    monkeypatch.setenv("WORKFLOW_JOB_NAME", "evaluate")
    monkeypatch.setenv("WORKFLOW_LABEL", "Manual task")
    monkeypatch.setattr(notify, "github_json", lambda _: {"jobs": [{
        "name": "evaluate", "status": "completed", "conclusion": "failure",
        "steps": [{"name": "Evaluate", "status": "completed", "conclusion": "failure"}],
    }]})
    record = tmp_path / "events.jsonl"
    record.write_text(json.dumps({"stage": "request", "status": "failed", "case_id": "synthetic",
                                  "error_type": "ReadTimeout", "elapsed_seconds": 30.5,
                                  "secret": "never-copy-this"}) + "\n")
    subject, body = notify.report("123", str(record))
    assert "Manual task" in subject and "失敗或中斷" in subject
    assert "Evaluate: failure" in body and "ReadTimeout" in body and "seconds=30.5" in body
    assert "never-copy-this" not in body


def test_query_failure_still_uses_existing_smtp_adapter_without_logging_error_text(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/radar")
    monkeypatch.setenv("WORKFLOW_RECEIPT_PATH", str(tmp_path / "receipt.json"))
    monkeypatch.setattr(notify, "report", lambda *_: (_ for _ in ()).throw(RuntimeError("unlogged request text")))
    payloads = []
    monkeypatch.setattr(notify.tw_source_email, "send", lambda payload, _settings: payloads.append(payload) or {
        "status": "provider_accepted", "smtp_code": 250})
    assert notify.main() == 0
    assert "RuntimeError" in payloads[0]["body"]
    assert "unlogged" not in payloads[0]["body"]
    assert json.loads((tmp_path / "receipt.json").read_text())["delivery"]["status"] == "provider_accepted"
    assert "provider_accepted" in capsys.readouterr().out
