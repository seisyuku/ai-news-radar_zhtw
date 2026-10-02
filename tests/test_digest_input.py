"""F06/F07/F10/F11: capture identity and safe input degradation."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.archive_output import archive_from_payload, load_archive
from scripts.digest_input import DigestInputError, load_digest_input


AS_OF = "2026-10-01T22:00:00Z"
ROW = {"id": "item-a", "site_id": "aibase", "source": "aibase", "title": "AI news", "url": "https://example.invalid/a"}


def write_inputs(path, *, items=None, as_of=AS_OF, health_as_of=AS_OF):
    path.mkdir(exist_ok=True)
    (path / "archive.json").write_text(json.dumps({"generated_at": as_of, "items": [dict(ROW)] if items is None else items}))
    (path / "title-zh-cache.json").write_text(json.dumps({"AI news": "AI 新聞"}))
    (path / "source-status.json").write_text(json.dumps({"generated_at": health_as_of, "sites": [{"site_id": "official_ai", "ok": False, "error": "secret error", "token": "secret", "subsources": [{"source_id": "feed", "ok": True, "item_count": 0, "error": "secret"}]}]}))


def descriptors(snapshot):
    return {row.name: row for row in snapshot.inputs}


def test_normalized_records_and_health_are_read_only_inputs(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    (tmp_path / "ai-summary-cache.json").write_text("not an input")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    import requests
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    def forbidden(*args, **kwargs):
        raise AssertionError("network or output write")
    monkeypatch.setattr(requests.Session, "request", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    snapshot = load_digest_input(tmp_path)
    assert snapshot.records["item-a"]["site_id"] == "curated_media"
    assert snapshot.records["item-a"]["source"] == "AIBASE"
    assert snapshot.title_cache == {"AI news": "AI 新聞"}
    assert descriptors(snapshot)["archive.json"].alignment == "matched"
    assert descriptors(snapshot)["title-zh-cache.json"].alignment == "unversioned"
    assert snapshot.health["sites"][0] == {"site_id": "official_ai", "ok": False, "subsources": [{"source_id": "feed", "ok": True, "item_count": 0}]}
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
    assert set(snapshot.captured_bytes) == {"archive.json", "title-zh-cache.json", "source-status.json"}


@pytest.mark.parametrize("payload", [[], {}, {"items": None}, {"items": [None]}, {"items": [{}]}, {"items": [{"id": "x"}, {"id": "x"}]}, {"items": {"": {}}}])
def test_invalid_archive_is_fatal_and_shared_validator_agrees(tmp_path, payload):
    write_inputs(tmp_path)
    (tmp_path / "archive.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        load_archive(tmp_path / "archive.json", normalize_record=dict)
    with pytest.raises(ValueError):
        archive_from_payload(payload, normalize_record=dict)
    with pytest.raises(DigestInputError, match="archive_invalid"):
        load_digest_input(tmp_path, normalize_record=dict)


@pytest.mark.parametrize("wire", [b"{", b"\xff"])
def test_bad_archive_encoding_or_json_is_fatal(tmp_path, wire):
    (tmp_path / "archive.json").write_bytes(wire)
    with pytest.raises(DigestInputError, match="archive_invalid"):
        load_digest_input(tmp_path, normalize_record=dict)


def test_missing_archive_is_not_empty_day_but_old_loader_keeps_first_run_semantics(tmp_path):
    assert load_archive(tmp_path / "archive.json", normalize_record=dict) == {}
    with pytest.raises(DigestInputError, match="archive_missing"):
        load_digest_input(tmp_path)


@pytest.mark.parametrize("items", [[], {}, {"key": {"id": "wrong", "extension": {"keep": True}}}])
def test_empty_and_legacy_archive_shapes(tmp_path, items):
    write_inputs(tmp_path, items=items)
    snapshot = load_digest_input(tmp_path, normalize_record=dict)
    expected = {"key": {"id": "key", "extension": {"keep": True}}} if items else {}
    assert snapshot.records == expected
    assert snapshot.records == load_archive(tmp_path / "archive.json", normalize_record=dict)


def test_missing_optional_inputs_and_unknown_legacy_as_of(tmp_path):
    (tmp_path / "archive.json").write_text('{"items": []}')
    snapshot = load_digest_input(tmp_path, normalize_record=dict)
    desc = descriptors(snapshot)
    assert desc["archive.json"].producer_as_of is None
    assert desc["source-status.json"].status == "missing"
    assert desc["source-status.json"].sha256 is None
    assert snapshot.health is None and snapshot.title_cache == {}
    assert "unknown_as_of" in [d.code for d in snapshot.diagnostics]


@pytest.mark.parametrize("name,wire", [
    ("title-zh-cache.json", "bad"), ("title-zh-cache.json", "[]"),
    ("source-status.json", "bad"), ("source-status.json", "[]"),
    ("source-status.json", '{"generated_at":"x","sites":[1]}'),
    ("source-status.json", '{"sites":[]}'),
])
def test_optional_corruption_degrades_without_losing_news(tmp_path, name, wire):
    write_inputs(tmp_path)
    (tmp_path / name).write_text(wire)
    snapshot = load_digest_input(tmp_path, normalize_record=dict)
    assert snapshot.records
    assert descriptors(snapshot)[name].status == "invalid"
    assert descriptors(snapshot)[name].sha256 == hashlib.sha256(wire.encode()).hexdigest()
    assert any(d.code == "optional_invalid" and d.input == name for d in snapshot.diagnostics)


def test_cache_entries_are_not_coerced_to_strings(tmp_path):
    write_inputs(tmp_path)
    (tmp_path / "title-zh-cache.json").write_text(json.dumps({"good": "好", "empty": " ", "list": ["bad"], "num": 0, "": "bad"}))
    snapshot = load_digest_input(tmp_path, normalize_record=dict)
    assert snapshot.title_cache == {"good": "好"}
    assert next(d.count for d in snapshot.diagnostics if d.code == "cache_entries_skipped") == 4


def test_disabled_and_skipped_provider_metadata_survives_without_private_details(tmp_path):
    write_inputs(tmp_path)
    path = tmp_path / "source-status.json"
    health = json.loads(path.read_text())
    health["x_api"] = {"enabled": False, "disabled_reason": "disabled_by_config", "api_key_present": True, "token": "secret"}
    health["socialdata"] = {"enabled": True, "skipped": True, "skip_reason": "interval", "error": "secret"}
    health["rss_opml"] = {"enabled": True, "failed_feeds": 1, "path": "/private/feed", "feeds": [{"url": "private"}]}
    path.write_text(json.dumps(health))
    snapshot = load_digest_input(tmp_path, normalize_record=dict)
    assert snapshot.health["x_api"] == {"enabled": False, "disabled_reason": "disabled_by_config"}
    assert snapshot.health["socialdata"] == {"enabled": True, "skipped": True, "skip_reason": "interval"}
    assert snapshot.health["rss_opml"] == {"enabled": True, "failed_feeds": 1}


@pytest.mark.parametrize("archive_as_of,health_as_of,alignment", [
    (AS_OF, "2026-10-02T06:00:00+08:00", "matched"),
    (AS_OF, "2026-10-01T21:59:59Z", "mismatched"),
    (None, AS_OF, "unverifiable"),
    (AS_OF, "2026-10-01T22:00:00", "unverifiable"),
])
def test_as_of_alignment_uses_aware_instants_not_file_mtime(tmp_path, archive_as_of, health_as_of, alignment):
    write_inputs(tmp_path, as_of=archive_as_of, health_as_of=health_as_of)
    snapshot = load_digest_input(tmp_path, normalize_record=dict)
    assert descriptors(snapshot)["source-status.json"].alignment == alignment
    assert descriptors(snapshot)["archive.json"].alignment == alignment
    # Preserve separate sanitized health evidence; D07 decides whether to show counts.
    assert snapshot.health is not None


def test_each_file_read_once_and_parse_matches_captured_bytes_during_update(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    original = (tmp_path / "archive.json").read_bytes()
    read = Path.read_bytes
    counts = {}
    def updating_read(path):
        counts[path.name] = counts.get(path.name, 0) + 1
        if path.name == "title-zh-cache.json":
            # Simulate upstream replacing archive after our archive read.
            (tmp_path / "archive.json").write_text('{"items": []}')
        return read(path)
    monkeypatch.setattr(Path, "read_bytes", updating_read)
    snapshot = load_digest_input(tmp_path, normalize_record=dict)
    assert counts == {name: 1 for name in snapshot.captured_bytes}
    assert snapshot.records
    assert snapshot.captured_bytes["archive.json"] == original
    assert descriptors(snapshot)["archive.json"].sha256 == hashlib.sha256(original).hexdigest()
    with pytest.raises(TypeError):
        snapshot.captured_bytes["archive.json"] = b"changed"


def test_fingerprint_is_directory_independent_and_changes_with_snapshot(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    write_inputs(left)
    right.mkdir()
    for path in left.iterdir():
        (right / path.name).write_bytes(path.read_bytes())
    a, b = load_digest_input(left, normalize_record=dict), load_digest_input(right, normalize_record=dict)
    assert a.fingerprint == b.fingerprint
    (right / "title-zh-cache.json").write_text('{}')
    assert a.fingerprint != load_digest_input(right, normalize_record=dict).fingerprint
    b.records["item-a"]["title"] = "changed in memory"
    assert a.records["item-a"]["title"] == "AI news"


@pytest.mark.parametrize("name", ["archive.json", "title-zh-cache.json", "source-status.json"])
def test_unreadable_inputs_have_safe_codes(tmp_path, monkeypatch, name):
    write_inputs(tmp_path)
    read = Path.read_bytes
    def denied(path):
        if path.name == name:
            raise PermissionError("secret filename/error")
        return read(path)
    monkeypatch.setattr(Path, "read_bytes", denied)
    if name == "archive.json":
        with pytest.raises(DigestInputError) as error:
            load_digest_input(tmp_path, normalize_record=dict)
        assert str(error.value) == "archive_unreadable"
    else:
        snapshot = load_digest_input(tmp_path, normalize_record=dict)
        assert descriptors(snapshot)[name].status == "invalid"
        assert descriptors(snapshot)[name].sha256 is None


def test_injected_policy_keeps_loader_independent_in_both_import_modes(tmp_path):
    write_inputs(tmp_path)
    root = Path(__file__).resolve().parents[1]
    script = """
import importlib, importlib.abc, sys
from pathlib import Path
class Reject(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'update_news','scripts.update_news','requests','bs4','dateutil'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, Reject())
sys.path.insert(0, sys.argv[1])
module = importlib.import_module(sys.argv[2])
assert module.load_digest_input(Path(sys.argv[3]), normalize_record=dict).records
"""
    for import_path, module in [(root, "scripts.digest_input"), (root / "scripts", "digest_input")]:
        result = subprocess.run([sys.executable, "-B", "-c", script, str(import_path), module, str(tmp_path)], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stdout + result.stderr
