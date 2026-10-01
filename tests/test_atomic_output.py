"""Faults must preserve each previous file and defer resolver retention cleanup."""

import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import update_news as u


NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)
ACTIVE_ID = "a" * 40
EXPIRED_ID = "b" * 40


def record(item_id=ACTIVE_ID, last_seen="2026-09-28T00:00:00Z"):
    return {
        "id": item_id, "site_id": "official_ai", "site_name": "Official AI",
        "source": "Example", "title": "OpenAI releases an AI model",
        "url": "https://example.invalid/news", "published_at": last_seen,
        "first_seen_at": last_seen, "last_seen_at": last_seen,
    }


def inject_partial_write(monkeypatch):
    """Simulate disk failure after bytes reached either old or new writer."""
    original_write_text = Path.write_text
    original_fdopen = os.fdopen

    def partial_text(path, text, *args, **kwargs):
        original_write_text(path, text[:8], *args, **kwargs)
        raise OSError("injected partial write")

    class PartialStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def __getattr__(self, name):
            return getattr(self.stream, name)

        def write(self, text):
            self.stream.write(text[:8])
            self.stream.flush()
            raise OSError("injected partial write")

    monkeypatch.setattr(Path, "write_text", partial_text)
    monkeypatch.setattr(os, "fdopen", lambda *a, **k: PartialStream(original_fdopen(*a, **k)))


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("failure", ["write", "replace"])
def test_atomic_failure_preserves_target_and_cleans_only_own_temp(tmp_path, monkeypatch, existing, failure):
    target = tmp_path / "snapshot.json"
    if existing:
        target.write_text("previous complete snapshot")
    unrelated = tmp_path / ".snapshot.json.unrelated.tmp"
    unrelated.write_text("another invocation's temporary file")

    if failure == "write":
        inject_partial_write(monkeypatch)
    else:
        def fail_replace(source, destination):
            source = Path(source)
            assert source.parent == target.parent
            assert source.name.startswith(".snapshot.json.") and source.suffix == ".tmp"
            assert source.read_text() == "新的完整快照\n"
            assert Path(destination) == target
            raise OSError("injected replace failure")
        monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(OSError, match="injected"):
        u.atomic_write_text(target, "新的完整快照\n")

    if existing:
        assert target.read_text() == "previous complete snapshot"
    else:
        assert not target.exists()
    assert unrelated.read_text() == "another invocation's temporary file"
    assert set(tmp_path.iterdir()) == ({target, unrelated} if existing else {unrelated})


@pytest.mark.parametrize("mode", [None, 0o644, 0o600])
def test_atomic_success_preserves_text_and_permissions(tmp_path, mode):
    target = tmp_path / "snapshot.json"
    if mode is not None:
        target.write_text("old")
        target.chmod(mode)

    u.atomic_write_text(target, '{"title":"台灣 AI"}\n')

    assert target.read_bytes() == '{"title":"台灣 AI"}\n'.encode("utf-8")
    assert stat.S_IMODE(target.stat().st_mode) == (0o644 if mode is None else mode)
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("writer,relative", [
    (u.write_item_resolvers, f"data/items/{ACTIVE_ID}.json"),
    (u.write_item_html_adapters, f"item/{ACTIVE_ID}/index.html"),
])
def test_resolver_partial_write_keeps_old_file_and_expired_link(tmp_path, monkeypatch, writer, relative):
    output_dir = tmp_path / "data"
    archive = {ACTIVE_ID: record(), EXPIRED_ID: record(EXPIRED_ID)}
    writer(output_dir, archive)
    old_files = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    inject_partial_write(monkeypatch)

    with pytest.raises(OSError, match="injected partial write"):
        writer(output_dir, {ACTIVE_ID: record()})

    assert (tmp_path / relative).read_bytes() == old_files[tmp_path / relative]
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == old_files


@pytest.fixture
def offline_generation(tmp_path, monkeypatch):
    output_dir = tmp_path / "data"
    output_dir.mkdir()
    archive = {ACTIVE_ID: record(), EXPIRED_ID: record(EXPIRED_ID, "2026-08-01T00:00:00Z")}
    (output_dir / "archive.json").write_text(json.dumps({"items": list(archive.values())}))
    # Existing optional caches ensure their writes are exercised without API keys.
    for name in (
        "latest-24h.json", "latest-24h-all.json", "daily-brief.json", "stories-merged.json",
        "source-status.json", "market-signals.json", "llm-radar.json", "market-sensor-state.json",
        "paid-source-state.json", "title-zh-cache.json", "translation-state.json", "ai-summary-cache.json",
    ):
        (output_dir / name).write_text("{}")
    u.write_item_resolvers(output_dir, archive)
    u.write_item_html_adapters(output_dir, archive)
    monkeypatch.setattr(u, "utc_now", lambda: NOW)
    monkeypatch.setattr(u, "create_session", lambda: object())
    monkeypatch.setattr(u, "collect_all", lambda *_: ([], []))
    monkeypatch.setattr(u, "run_market_sensors", lambda *_: ({"generated_at": u.iso(NOW), "signals": []}, {}, []))
    for name in ("maybe_fetch_x_api_updates", "maybe_fetch_socialdata_updates", "maybe_fetch_tikhub_updates"):
        monkeypatch.setattr(u, name, lambda *_: ([], {"enabled": False}))
    for name in ("X_BEARER_TOKEN", "SOCIALDATA_API_KEY", "TIKHUB_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_TRANSLATE_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("unexpected external network access")

    monkeypatch.setattr("requests.sessions.Session.request", no_network)
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(output_dir), "--translate-max-new", "0"])
    return output_dir


@pytest.mark.parametrize("relative", [
    "data/latest-24h.json", "data/latest-24h-all.json", "data/daily-brief.json",
    "data/stories-merged.json", "data/archive.json", f"data/items/{ACTIVE_ID}.json",
    f"item/{ACTIVE_ID}/index.html", "data/source-status.json", "data/market-signals.json",
    "data/llm-radar.json", "data/market-sensor-state.json", "data/paid-source-state.json",
    "data/title-zh-cache.json", "data/translation-state.json", "data/ai-summary-cache.json",
])
def test_main_replace_failure_preserves_failed_target_and_both_expired_links(offline_generation, monkeypatch, relative):
    root = offline_generation.parent
    target = root / relative
    old_text = target.read_bytes()
    expired_json = offline_generation / "items" / f"{EXPIRED_ID}.json"
    expired_html = root / "item" / EXPIRED_ID / "index.html"
    old_json, old_html = expired_json.read_bytes(), expired_html.read_bytes()
    original_replace = os.replace

    def fail_selected_replace(source, destination):
        if Path(destination) == target:
            raise OSError("injected selected replace failure")
        return original_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_selected_replace)
    with pytest.raises(OSError, match="injected selected replace failure"):
        u.main()

    assert target.read_bytes() == old_text
    assert expired_json.read_bytes() == old_json
    assert expired_html.read_bytes() == old_html
    assert not list(root.rglob("*.tmp"))


def test_successful_main_prunes_both_expired_links_after_all_writes(offline_generation):
    assert u.main() == 0
    root = offline_generation.parent
    assert not (offline_generation / "items" / f"{EXPIRED_ID}.json").exists()
    assert not (root / "item" / EXPIRED_ID).exists()
    assert (offline_generation / "items" / f"{ACTIVE_ID}.json").exists()
    assert (root / "item" / ACTIVE_ID / "index.html").exists()
    assert not list(root.rglob("*.tmp"))
    assert json.loads((offline_generation / "archive.json").read_text())["total_items"] == 1


def test_main_redacts_persistent_non_group_failure_in_all_public_outputs(offline_generation, monkeypatch, capsys):
    summary = offline_generation.parent / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    first_failure = "2026-09-26T00:00:00Z"
    (offline_generation / "source-status.json").write_text(json.dumps({"sites": [
        {"site_id": "legacy", "ok": False, "consecutive_failures": 2,
         "first_failure_at": first_failure}]}))
    current = [{"site_id": "legacy", "ok": False, "item_count": 0,
                "error": "secret=synthetic-only-marker user@example.invalid"}]
    monkeypatch.setattr(u, "collect_all", lambda *_: ([], current))

    assert u.main() == 0

    public_json = (offline_generation / "source-status.json").read_text()
    warning, table = capsys.readouterr().out, summary.read_text()
    for output in (public_json, warning, table):
        assert "synthetic-only-marker" not in output and "user@example.invalid" not in output
        assert "[redacted-secret]" in output and "[redacted-email]" in output
    payload = json.loads(public_json)
    failure = next(row for row in payload["persistent_failures"] if row["site_id"] == "legacy")
    assert failure["consecutive_failures"] == 3
    assert failure["first_failure_at"] == first_failure
    assert current[0]["error"] == "secret=synthetic-only-marker user@example.invalid"


def test_generation_phase_records_elapsed_and_failure_without_exception_text(monkeypatch):
    clock = [10.0]
    monkeypatch.setattr(u.time, "perf_counter", lambda: clock[0])
    metrics = {}
    with u.record_generation_phase(metrics, "quiet"):
        clock[0] += 0.25
    assert metrics["quiet"] == {"state": "completed", "duration_ms": 250}
    with pytest.raises(ValueError):
        with u.record_generation_phase(metrics, "failed"):
            clock[0] += 0.5
            raise ValueError("secret=never-export")
    assert metrics["failed"] == {"state": "failed", "duration_ms": 500}
    assert "never-export" not in str(metrics)


@pytest.mark.parametrize("fails", [False, True])
def test_generator_subsource_duration_retains_safe_health_result(monkeypatch, fails):
    clock = [0.0]
    monkeypatch.setattr(u.time, "perf_counter", lambda: clock[0])
    def fetch():
        clock[0] += 0.375
        if fails:
            raise RuntimeError("secret=do-not-export")
        return [object()]
    items, status = u._group_subsource_status("stable_id", fetch)
    assert status["duration_ms"] == 375
    assert status["ok"] is not fails
    assert len(items) == (0 if fails else 1)
    assert "do-not-export" not in str(status)


def test_main_phase_metrics_separate_opml_wall_skips_and_output(offline_generation, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(u.time, "perf_counter", lambda: clock[0])
    def collect(*args):
        clock[0] += 0.5
        return [], []
    monkeypatch.setattr(u, "collect_all", collect)
    opml = offline_generation.parent / "public.opml"
    opml.write_text("<opml/>")
    def rss(*args, **kwargs):
        clock[0] += 0.25
        return [], {"site_id": "opmlrss", "ok": True, "item_count": 0,
                    "duration_ms": 700}, []
    monkeypatch.setattr(u, "fetch_opml_rss", rss)
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(offline_generation),
                                    "--rss-opml", str(opml), "--translate-max-new", "0"])
    monkeypatch.setattr(u, "maybe_fetch_socialdata_updates", lambda *_: ([], {
        "enabled": True, "attempted": False, "skipped": True, "ok": None,
        "item_count": 0, "skip_reason": "interval"}))
    original_write = u.atomic_write_text
    def slow_write(*args, **kwargs):
        clock[0] += 0.005
        return original_write(*args, **kwargs)
    monkeypatch.setattr(u, "atomic_write_text", slow_write)
    assert u.main() == 0
    payload = json.loads((offline_generation / "source-status.json").read_text())
    phases = payload["metrics"]["phases"]
    assert phases["collect"]["duration_ms"] == 500
    assert phases["opml"]["duration_ms"] == 250
    assert next(s for s in payload["sites"] if s["site_id"] == "opmlrss")["duration_ms"] == 700
    assert phases["socialdata"]["state"] == "skipped"
    assert phases["x_api"]["state"] == "skipped"
    assert phases["translations"]["provider_request_count"] == 0
    assert phases["summaries"]["provider_enabled"] is False
    assert phases["output"]["duration_ms"] >= 50
    assert payload["metrics"]["output_excludes"] == ["source_status_publication", "resolver_cleanup"]


def test_main_disabled_opml_and_providers_are_explicit(offline_generation):
    assert u.main() == 0
    phases = json.loads((offline_generation / "source-status.json").read_text())["metrics"]["phases"]
    assert phases["opml"]["state"] == "skipped"
    assert phases["summaries"]["provider_enabled"] is False
    assert phases["translations"]["provider_request_count"] == 0


def test_skipped_child_duration_is_current_zero_without_resetting_failure():
    current = [{"site_id": "official_ai", "skipped": True, "ok": None, "subsources": []}]
    previous = {"sites": [{"site_id": "official_ai", "subsources": [
        {"source_id": "child", "ok": False, "duration_ms": 1234,
         "consecutive_failures": 2, "last_failure_at": "2026-09-27T00:00:00Z"}]}]}
    assert u.apply_source_health_history(current, previous, NOW) == []
    row = current[0]["subsources"][0]
    assert row["duration_ms"] == 0 and row["attempted"] is False
    assert row["consecutive_failures"] == 2
