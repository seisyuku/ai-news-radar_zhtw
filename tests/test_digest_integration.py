"""D10: independent end-to-end evidence and interrupted delivery fixtures."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import generate_digest as cli
from scripts.digest_document import build_digest_document
from scripts.digest_input import load_digest_input
from scripts.digest_window import parse_published_at, window_for_date


DATE = "2026-10-02"
AS_OF = "2026-10-01T22:00:00Z"
WINDOW = window_for_date(DATE)


def pair(prefix="event", **changes):
    base = {"title": "OpenAI releases a new Codex cloud agent", "site_id": "official_ai",
            "source": "OpenAI News", "published_at": "2026-10-02T05:30:00+08:00",
            "summary": "Publisher states the agent costs $10.", **changes}
    return [{**base, "id": prefix + "-a", "url": f"https://example.invalid/{prefix}-a"},
            {**base, "id": prefix + "-b", "site_id": "curated_media", "source": "Other Publisher",
             "url": f"https://example.invalid/{prefix}-b"}]


def inputs(path, rows=(), *, archive_as_of=AS_OF, health_as_of=AS_OF, cache=None, sites=None):
    path.mkdir(parents=True, exist_ok=True)
    (path / "archive.json").write_text(json.dumps({"generated_at": archive_as_of, "items": list(rows)}))
    (path / "source-status.json").write_text(json.dumps({"generated_at": health_as_of,
        "sites": sites if sites is not None else [{"ok": False, "item_count": 0}]}))
    (path / "title-zh-cache.json").write_text(json.dumps(cache or {}))
    return path


def generate(source, output, *, extra=()):
    assert cli.main(["--input-dir", str(source), "--output-dir", str(output), "--date", DATE, *extra]) == 0
    paths = (output / f"digest-{DATE}.md", output / f"digest-{DATE}.meta.json")
    return paths[0].read_text(), cli.verify_digest_pair(*paths)


def test_reader_dates_use_taipei_not_previous_utc_day(tmp_path):
    source = inputs(tmp_path / "in", pair())
    markdown, metadata = generate(source, tmp_path / "out")
    assert metadata["candidates"]
    assert "發布日期（臺北）：2026-10-02" in markdown
    assert "2026-10-01 06:00 至 2026-10-02 06:00（Asia/Taipei；起點含、終點不含）" in markdown


def test_translated_summary_is_labeled_as_cached_publisher_evidence(tmp_path):
    summary = pair()[0]["summary"]
    source = inputs(tmp_path / "in", pair(), cache={"summary::" + summary: "出版者稱代理費用為 $10。"})
    markdown, metadata = generate(source, tmp_path / "out")
    assert metadata["candidates"][0]["summary_kind"] == "publisher_translation"
    assert "出版者摘要（既有快取譯文）：" in markdown
    assert "出版者稱代理費用為 $10。" in markdown


def test_endpoints_and_outside_reposts_never_enter_candidate_evidence(tmp_path):
    rows = (pair("start", published_at="2026-10-01T06:00:00+08:00")
            + pair("end", title="Anthropic releases Claude 6 for enterprise agents", published_at="2026-10-02T05:59:59+08:00")
            + pair("before", published_at="2026-10-01T05:59:59+08:00")
            + pair("after", published_at="2026-10-02T06:00:00+08:00"))
    markdown, metadata = generate(inputs(tmp_path / "in", rows), tmp_path / "out")
    assert metadata["candidates"]
    refs = [ref for item in metadata["candidates"] for ref in item["sources"]]
    assert any(ref["item_id"].startswith("start") for ref in refs)
    assert any(ref["item_id"].startswith("end") for ref in refs)
    assert all(WINDOW.contains(parse_published_at(ref["published_at"])) for ref in refs)
    assert not any(ref["item_id"].startswith(("before", "after")) for ref in refs)
    assert "/before-" not in markdown and "/after-" not in markdown


def test_late_discovery_and_changed_summary_create_new_same_day_draft(tmp_path):
    source = inputs(tmp_path / "in", pair())
    old_md, old = generate(source, tmp_path / "out")
    late = pair("late", title="Anthropic launches Claude 6 enterprise agent API",
                first_seen_at="2026-10-02T03:00:00Z", published_at="2026-10-02T05:59:00+08:00")
    inputs(source, pair(summary="Publisher states the updated price is $12.") + late,
           archive_as_of="2026-10-02T03:00:00Z", health_as_of="2026-10-02T03:00:00Z")
    new_md, new = generate(source, tmp_path / "out")
    assert old["input_identity"] != new["input_identity"] and old_md != new_md
    refs = [r for c in new["candidates"] for r in c["sources"]]
    assert any(r["item_id"].startswith("late") for r in refs)
    assert any("$12" in (r["summary_original"] or "") for r in refs)


@pytest.mark.parametrize("rows,code", [([], None), (pair(published_at="2026-09-01T00:00:00Z"), "outside_window"),
    (pair(title="City council approves a new local park", summary="New trees in a city park.", site_id="test_source", source="Local News"), "not_ai_related")])
def test_empty_outside_and_non_ai_cli_success_with_reasons(tmp_path, rows, code):
    markdown, metadata = generate(inputs(tmp_path / "in", rows), tmp_path / "out")
    assert metadata["candidates"] == [] and "本期沒有符合既有選題條件" in markdown
    if code:
        assert code in [d["code"] for d in metadata["diagnostics"]]


@pytest.mark.parametrize("health_time", [AS_OF, "2026-10-01T21:00:00Z", "unknown"])
def test_failed_or_unaligned_health_keeps_retained_news_usable(tmp_path, health_time):
    markdown, metadata = generate(inputs(tmp_path / "in", pair(), health_as_of=health_time), tmp_path / "out")
    assert metadata["candidates"]
    assert "留存新聞不代表本輪重新抓取" in markdown
    if health_time == AS_OF:
        assert metadata["health"]["current_round"]["site_counts"]["failed"] == 1
        assert "部分來源本輪失敗或部分失敗" in markdown
    else:
        assert metadata["health"]["current_round"] is None


def test_before_cutoff_and_default_date_never_wait_or_shift_issue(tmp_path, monkeypatch):
    source = inputs(tmp_path / "in", pair(), archive_as_of="2026-10-01T21:00:00Z", health_as_of="2026-10-01T21:00:00Z")
    calls = []
    real = cli.window_for_date
    def controlled(value=None):
        calls.append(value)
        return real(value, now=datetime(2026, 10, 1, 21, 30, tzinfo=timezone.utc))
    monkeypatch.setattr(cli, "window_for_date", controlled)
    assert cli.main(["--input-dir", str(source), "--output-dir", str(tmp_path / "out")]) == 0
    metadata = cli.verify_digest_pair(tmp_path / "out" / f"digest-{DATE}.md", tmp_path / "out" / f"digest-{DATE}.meta.json")
    assert calls.count(None) == 1 and metadata["window"]["date"] == DATE
    assert metadata["health"]["input_before_cutoff"] is True


def test_record_order_and_execution_clock_do_not_change_evidence(tmp_path, monkeypatch):
    from scripts import update_news as news
    rows = pair()
    source = inputs(tmp_path / "in", rows)
    first = build_digest_document(load_digest_input(source), WINDOW)
    inputs(source, list(reversed(rows)))
    def forbidden(*args, **kwargs):
        raise AssertionError("clock/provider/network")
    monkeypatch.setattr(news, "utc_now", forbidden)
    second = build_digest_document(load_digest_input(source), WINDOW)
    assert first["candidates"] == second["candidates"]
    assert first["input_identity"] != second["input_identity"]  # Byte identities differ.


@pytest.mark.parametrize("keys", [False, True])
def test_end_to_end_blocks_fetch_translate_synthesis_and_sockets(tmp_path, monkeypatch, keys):
    import requests
    import socket
    from scripts import update_news as news
    source = inputs(tmp_path / "in", pair())
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden external work")
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "X_BEARER_TOKEN", "SOCIALDATA_API_KEY", "TIKHUB_API_KEY"):
        if keys:
            monkeypatch.setenv(key, "fake-key")
        else:
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(requests.Session, "request", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    for name in ("main", "collect_all", "add_bilingual_fields", "summarize_stories"):
        monkeypatch.setattr(news, name, forbidden)
    generate(source, tmp_path / "out")
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}


def test_process_interrupted_between_replacements_is_detected_and_recoverable(tmp_path):
    source = inputs(tmp_path / "in", pair())
    _, old = generate(source, tmp_path / "out")
    program = '''
import os,sys
from scripts import generate_digest as cli
real=cli.atomic_write_text
def interrupt_after_one(path, text):
    real(path, text)
    os._exit(73)
cli.atomic_write_text=interrupt_after_one
cli.main(sys.argv[1:])
'''
    args = ["--input-dir", str(source), "--output-dir", str(tmp_path / "out"), "--date", DATE, "--limit", "0"]
    result = subprocess.run([sys.executable, "-c", program, *args], capture_output=True, text=True)
    assert result.returncode == 73 and "digest_generated" not in result.stdout
    md, meta = cli._paths(tmp_path / "out", DATE)
    assert json.loads(meta.read_text())["input_identity"] == old["input_identity"]
    with pytest.raises(cli.DigestOutputError):
        cli.verify_digest_pair(md, meta)
    _, recovered = generate(source, tmp_path / "out", extra=("--limit", "0"))
    assert recovered["candidates"] == []


def test_stream_write_failure_preserves_complete_pair_and_sanitizes_cli_error(tmp_path, monkeypatch, capsys):
    from scripts import archive_output
    source = inputs(tmp_path / "in", pair())
    generate(source, tmp_path / "out")
    capsys.readouterr()
    paths = cli._paths(tmp_path / "out", DATE)
    before = [p.read_bytes() for p in paths]
    fdopen = archive_output.os.fdopen
    class FailingStream:
        def __init__(self, stream): self.stream = stream
        def __enter__(self): return self
        def __exit__(self, *args): self.stream.close()
        def write(self, text): raise OSError("private write failure /secret/token")
    monkeypatch.setattr(archive_output.os, "fdopen", lambda *a, **k: FailingStream(fdopen(*a, **k)))
    assert cli.main(["--input-dir", str(source), "--output-dir", str(tmp_path / "out"), "--date", DATE]) == 1
    captured = capsys.readouterr()
    assert "digest_generated" not in captured.out and "private" not in captured.err
    assert [p.read_bytes() for p in paths] == before
    assert not list((tmp_path / "out").glob("*.tmp"))


@pytest.mark.parametrize("extra,code", [(["--date", "2026-02-30"], 2), ([], 1)])
def test_real_cli_failure_codes_do_not_create_outputs(tmp_path, extra, code):
    result = subprocess.run([sys.executable, "scripts/generate_digest.py", "--input-dir", str(tmp_path / "missing"),
                             "--output-dir", str(tmp_path / "out"), *extra], capture_output=True, text=True)
    assert result.returncode == code and "digest_generated" not in result.stdout
    assert not (tmp_path / "out").exists()
