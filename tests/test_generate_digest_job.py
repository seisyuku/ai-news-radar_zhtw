"""Checkout-only generation, private outputs and explicit issue boundaries."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from scripts import generate_digest_job as job


DATE = "2026-10-10"
NOW = datetime(2026, 10, 9, 23, 15, tzinfo=timezone.utc)
AS_OF = "2026-10-09T22:30:00Z"


def inputs(root, *, as_of=AS_OF, rows=()):
    root.mkdir()
    (root / "archive.json").write_text(json.dumps({"generated_at": as_of, "items": list(rows)}))
    (root / "source-status.json").write_text(json.dumps({"generated_at": as_of, "sites": []}))
    (root / "title-zh-cache.json").write_text("{}")
    return root


def test_nonempty_checkout_generation_without_network_or_git(tmp_path, monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("Network or Git invocation is not allowed")
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "check_output", forbidden)
    import socket
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    row = {"title": "OpenAI releases a new Codex cloud agent", "site_id": "official_ai",
           "source": "OpenAI News", "published_at": "2026-10-10T05:30:00+08:00",
           "summary": "PRIVATE publisher summary"}
    rows = [{**row, "id": "a", "url": "https://example.invalid/a"},
            {**row, "id": "b", "site_id": "curated_media", "source": "Other Publisher",
             "url": "https://example.invalid/b"}]
    source = inputs(tmp_path / "input", rows=rows)
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    target = tmp_path / "output"
    report = job.generate(DATE, source, target, clock=lambda: NOW)
    assert report["status"] == "generated" and report["selected_count"] > 0
    assert report["pair_verified"] and report["rerun_identical"]
    assert report["generation_timeliness"] == "on_time" and not report["delivery_verified"]
    document = job.verify_digest_pair(target / "pair" / f"digest-{DATE}.md",
                                      target / "pair" / f"digest-{DATE}.meta.json")
    assert document["window"]["start_utc"] == "2026-10-08T22:00:00Z"
    assert document["window"]["end_utc"] == "2026-10-09T22:00:00Z"
    assert document["candidates"]
    assert {p.name: p.read_bytes() for p in source.iterdir()} == before
    assert len(list(target.iterdir())) == 1  # only the pair; captured inputs/repeat removed
    assert "PRIVATE" not in json.dumps(report) and str(tmp_path) not in json.dumps(report)
    assert not any("sha" in key or "commit" in key for key in report)
    assert all(p.stat().st_mode & 0o077 == 0 for p in (target / "pair").iterdir())


def test_fresh_zero_news_is_generated_not_claim_of_no_news(tmp_path):
    report = job.generate(DATE, inputs(tmp_path / "input"), tmp_path / "output", clock=lambda: NOW)
    assert report["status"] == "generated" and report["selected_count"] == 0
    assert not report["delivery_verified"]


@pytest.mark.parametrize("as_of,reason", [
    (None, "archive_as_of_unknown"),
    ("2026-10-09T23:16:00Z", "archive_as_of_future"),
    ("2026-10-09T21:59:59Z", "archive_before_cutoff"),
    (AS_OF, "archive_stale"),
])
def test_review_only_still_has_verified_pair(tmp_path, as_of, reason):
    now = datetime(2026, 10, 10, 1, tzinfo=timezone.utc) if reason == "archive_stale" else NOW
    target = tmp_path / "output"
    report = job.generate(DATE, inputs(tmp_path / "input", as_of=as_of), target, clock=lambda: now)
    assert report["status"] == "review-only" and report["reason"] == reason
    assert report["pair_verified"] and report["rerun_identical"]
    assert not report["delivery_verified"] and (target / "pair").is_dir()


def test_date_mismatch_before_generation_and_cross_day_at_completion(tmp_path, monkeypatch):
    source = inputs(tmp_path / "input")
    target = tmp_path / "output"
    tomorrow = datetime(2026, 10, 10, 16, tzinfo=timezone.utc)
    original = job.load_digest_input
    monkeypatch.setattr(job, "load_digest_input", lambda *a: pytest.fail("must reject before reading"))
    assert job.generate(DATE, source, target, clock=lambda: tomorrow)["status"] == "missed_issue"
    assert not target.exists()
    monkeypatch.setattr(job, "load_digest_input", original)
    times = iter([NOW, tomorrow])
    assert job.generate(DATE, source, target, clock=lambda: next(times))["status"] == "missed_issue"
    assert not list(target.iterdir())


def test_historical_never_counts_as_current_success(tmp_path):
    report = job.generate(DATE, inputs(tmp_path / "input"), tmp_path / "output",
                          historical=True, clock=lambda: NOW)
    assert report["status"] == "review-only" and report["reason"] == "historical_review"
    assert report["generation_timeliness"] == "historical" and report["pair_verified"]


def test_generation_time_is_separate_from_private_delivery(tmp_path):
    now = datetime(2026, 10, 10, 1, 1, tzinfo=timezone.utc)
    report = job.generate(DATE, inputs(tmp_path / "input", as_of="2026-10-10T00:30:00Z"),
                          tmp_path / "output", clock=lambda: now)
    assert report["status"] == "generated" and report["generation_timeliness"] == "late"
    assert not report["delivery_verified"]


def test_previous_original_review_and_input_directories_are_protected(tmp_path):
    source = inputs(tmp_path / "input")
    target = tmp_path / "output"
    target.mkdir()
    (target / "review.md").write_text("PRIVATE human review")
    assert job.generate(DATE, source, target, clock=lambda: NOW)["reason"] == "output_exists"
    assert (target / "review.md").read_text() == "PRIVATE human review"
    assert job.generate(DATE, source, source / "inside", clock=lambda: NOW)["reason"] == "invalid_output_directory"
    assert job.generate(DATE, source, Path.cwd() / "data", clock=lambda: NOW)["reason"] == "invalid_output_directory"
    assert not (source / "inside").exists()


def test_corrupted_rerun_does_not_leave_a_pair_or_leak_error(tmp_path, monkeypatch):
    source = inputs(tmp_path / "input")
    target = tmp_path / "output"
    original = job.write_digest
    def corrupt(document, output):
        paths = original(document, output)
        if Path(output).name == "repeat":
            paths[0].write_text("PRIVATE secret changed content")
        return paths
    monkeypatch.setattr(job, "write_digest", corrupt)
    report = job.generate(DATE, source, target, clock=lambda: NOW)
    assert report["status"] == "failed" and not report["pair_verified"]
    assert not list(target.iterdir()) and "PRIVATE" not in json.dumps(report)


def test_independent_valid_but_different_rerun_fails(tmp_path, monkeypatch):
    source = inputs(tmp_path / "input")
    target = tmp_path / "output"
    original = job.build_digest_document
    # Change a document version while keeping its identity valid, even for empty input.
    from scripts.digest_document import document_identity
    calls = [True, False]
    def changed(snapshot, window):
        doc = original(snapshot, window)
        if calls.pop():
            doc["pipeline_version"] = "changed-rerun"
            doc["input_identity"] = document_identity(doc)
        return doc
    monkeypatch.setattr(job, "build_digest_document", changed)
    report = job.generate(DATE, source, target, clock=lambda: NOW)
    assert report["status"] == "failed" and report["reason"] == "rerun_mismatch"
    assert not list(target.iterdir())


def test_missing_archive_and_exceptions_have_only_safe_output(tmp_path, monkeypatch):
    target = tmp_path / "output"
    report = job.generate(DATE, tmp_path / "missing", target, clock=lambda: NOW)
    assert report["status"] == "failed" and not target.exists()
    monkeypatch.setattr(job, "load_digest_input", lambda *a: (_ for _ in ()).throw(OSError("PRIVATE token")))
    assert "PRIVATE" not in json.dumps(job.generate(DATE, tmp_path, target, clock=lambda: NOW))


def test_cli_requires_explicit_date_and_has_safe_summary(tmp_path, monkeypatch, capsys):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    source = inputs(tmp_path / "input")
    args = ["--input-dir", str(source), "--output-dir", str(tmp_path / "output")]
    with pytest.raises(SystemExit):
        job.main(args)
    with pytest.raises(SystemExit):
        job.main([*args, "--date", "2026-02-30"])
    capsys.readouterr()
    assert job.main([*args, "--date", DATE, "--historical"]) == 3
    output = capsys.readouterr().out
    assert json.loads(output)["delivery_verified"] is False
    assert output.strip() in summary.read_text()
    assert str(source) not in output and "PRIVATE" not in output


def test_direct_cli_uses_checkout_without_cloud_sdk(tmp_path):
    source = inputs(tmp_path / "input")
    code = """
import importlib.abc, runpy, sys
class CloudImportFence(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'mcp', 'jwt', 'cryptography'} or 'digest_cloud' in fullname:
            raise AssertionError('Cloud SDK cannot be imported for generation')
sys.meta_path.insert(0, CloudImportFence())
sys.argv = ['scripts/generate_digest_job.py', *sys.argv[1:]]
sys.path.insert(0, 'scripts')
runpy.run_path('scripts/generate_digest_job.py', run_name='__main__')
"""
    result = subprocess.run([sys.executable, "-c", code, "--date", DATE,
                             "--historical", "--input-dir", str(source), "--output-dir", str(tmp_path / "output")],
                            capture_output=True, text=True)
    assert result.returncode == 3 and json.loads(result.stdout)["pair_verified"]


def test_manual_workflow_cannot_publish_or_enable_daily_schedule():
    path = Path(__file__).resolve().parents[1] / ".github/workflows/digest-generation.yml"
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["on"]["workflow_dispatch"]["inputs"]["date"]["required"] == "true"
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] == "false"
    assert workflow["jobs"]["generate"]["timeout-minutes"] == "10"
    steps = workflow["jobs"]["generate"]["steps"]
    assert any("generate_digest_job.py" in step.get("run", "") for step in steps)
    assert steps[-1]["if"] == "${{ always() }}"
    assert all(not any(word in step.get("run", "") for word in
                       ("git push", "gh api", "update_news.py", "requirements-cloud", "requirements-dev")) for step in steps)
    assert not any("upload-artifact" in step.get("uses", "") for step in steps)
