"""D09: offline composition, CLI exits, determinism and per-file failure."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import generate_digest as cli
from scripts.digest_document import build_digest_document, document_identity
from scripts.digest_input import load_digest_input
from scripts.digest_window import window_for_date


DATE = "2026-10-02"
AS_OF = "2026-10-01T22:00:00Z"
WINDOW = window_for_date(DATE)


def inputs(path, *, items=(), as_of=AS_OF, health_as_of=AS_OF):
    path.mkdir(parents=True, exist_ok=True)
    (path / "archive.json").write_text(json.dumps({"items": list(items), "generated_at": as_of}))
    (path / "source-status.json").write_text(json.dumps({"generated_at": health_as_of, "sites": [{"ok": False, "item_count": 0}]}))
    (path / "title-zh-cache.json").write_text("{}")
    return path


def row(item_id, **changes):
    record = {"id": item_id, "site_id": "official_ai", "source": "OpenAI News",
              "title": "OpenAI releases a new Codex cloud agent",
              "url": f"https://example.invalid/{item_id}",
              "published_at": "2026-10-01T10:00:00Z",
              "summary": "OpenAI released the new Codex cloud agent for teams."}
    record.update(changes)
    return record


def build(path, **settings):
    return build_digest_document(load_digest_input(path), WINDOW, **settings)


def command(source, target, *extra):
    return ["--input-dir", str(source), "--output-dir", str(target), "--date", DATE, *extra]


def test_document_composes_real_stages_and_retains_primary_evidence(tmp_path):
    source = inputs(tmp_path / "in", items=[row("one")])
    document = build(source)
    assert document["window"]["start_utc"] == "2026-09-30T22:00:00Z"
    assert document["window"]["end_utc"] == AS_OF
    assert document["schema_version"] == 1
    assert document["selection_counts"]["selected_count"] == len(document["candidates"])
    assert document["selection_counts"]["total_candidates"] == 1
    assert document["health"]["current_round"]["site_counts"]["failed"] == 1
    assert document["input_identity"] == document_identity(document)
    # Brief gate may discard low-score single stories; limit=0 is explicit.
    assert build(source, limit=0)["candidates"] == []


def test_nonempty_multisource_digest_and_translation(tmp_path):
    source = inputs(tmp_path / "in", items=[row("a"), row("b", source="Other Publisher", site_id="curated_media")])
    text = row("a")["title"]
    (source / "title-zh-cache.json").write_text(json.dumps({text: "OpenAI 發布 Codex 雲端代理"}))
    document = build(source)
    assert document["candidates"]
    assert document["candidates"][0]["title"] == "OpenAI 發布 Codex 雲端代理"
    assert document["candidates"][0]["summary_kind"] == "publisher"
    paths = cli.write_digest(document, tmp_path / "out")
    assert "OpenAI 發布 Codex 雲端代理" in paths[0].read_text()
    assert cli.verify_digest_pair(*paths)["input_identity"] == document["input_identity"]


def test_same_bytes_different_directory_same_document_and_files(tmp_path):
    a = inputs(tmp_path / "a")
    b = inputs(tmp_path / "b")
    first, second = build(a), build(b)
    assert first == second
    p1 = cli.write_digest(first, tmp_path / "out1")
    p2 = cli.write_digest(second, tmp_path / "out2")
    assert [p.read_bytes() for p in p1] == [p.read_bytes() for p in p2]
    before = [p.read_bytes() for p in p1]
    cli.write_digest(first, tmp_path / "out1")
    assert before == [p.read_bytes() for p in p1]


def test_snapshot_date_settings_and_version_change_identity(tmp_path):
    source = inputs(tmp_path / "in")
    document = build(source)
    assert build(source, limit=0)["input_identity"] != document["input_identity"]
    assert build(source, same_source_penalty=0.04)["input_identity"] != document["input_identity"]
    other_date = build_digest_document(load_digest_input(source), window_for_date("2026-10-03"))
    assert other_date["input_identity"] != document["input_identity"]
    changed = deepcopy(document)
    changed["pipeline_version"] = "next"
    assert document_identity(changed) != document["input_identity"]
    (source / "title-zh-cache.json").write_text('{"unused": "未使用"}')
    assert build(source)["input_identity"] != document["input_identity"]


@pytest.mark.parametrize("extra", [["--date", "2026-02-30"], ["--date", "2026-1-2"],
                                  ["--limit", "-1"], ["--limit", "a"],
                                  ["--same-source-penalty", "nan"], ["--same-source-penalty", "-0.1"]])
def test_bad_parameters_exit_two_before_read_or_write(tmp_path, extra):
    with pytest.raises(SystemExit) as exc:
        cli.main(command(tmp_path / "missing", tmp_path / "out", *extra))
    assert exc.value.code == 2
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("wire", [None, "bad JSON", '{"items":[{}]}'])
def test_bad_archive_exit_one_and_preserves_old_pair(tmp_path, wire):
    source = inputs(tmp_path / "in")
    target = tmp_path / "out"
    assert cli.main(command(source, target)) == 0
    paths = cli._paths(target, DATE)
    before = [p.read_bytes() for p in paths]
    if wire is None:
        (source / "archive.json").unlink()
    else:
        (source / "archive.json").write_text(wire)
    assert cli.main(command(source, target)) == 1
    assert [p.read_bytes() for p in paths] == before


def test_empty_optional_degradation_and_mismatch_succeed(tmp_path):
    source = inputs(tmp_path / "in", health_as_of="2026-10-01T21:00:00Z")
    (source / "title-zh-cache.json").unlink()
    assert cli.main(command(source, tmp_path / "out")) == 0
    metadata = cli.verify_digest_pair(*cli._paths(tmp_path / "out", DATE))
    assert metadata["candidates"] == []
    assert metadata["health"]["current_round"] is None
    assert metadata["health"]["alignment"] == "mismatched"


@pytest.mark.parametrize("output", ["input", "nested", "data", "item"])
def test_protected_output_is_parameter_error(tmp_path, output):
    source = inputs(tmp_path / "in")
    project = Path(cli.__file__).resolve().parents[1]
    target = {"input": source, "nested": source / "nested", "data": project / "data" / "digest", "item": project / "item"}[output]
    with pytest.raises(SystemExit) as exc:
        cli.main(command(source, target))
    assert exc.value.code == 2


@pytest.mark.parametrize("fail_at", [1, 2])
def test_replace_failure_preserves_failed_file_and_pair_rejects_partial(tmp_path, monkeypatch, fail_at):
    from scripts import archive_output
    source = inputs(tmp_path / "in")
    old = build(source)
    paths = cli.write_digest(old, tmp_path / "out")
    before = [p.read_bytes() for p in paths]
    new = build(source, limit=0)
    replace = archive_output.os.replace
    calls = []
    def fail(src, dst):
        calls.append(dst)
        if len(calls) == fail_at:
            raise OSError("private failure text")
        return replace(src, dst)
    monkeypatch.setattr(archive_output.os, "replace", fail)
    with pytest.raises(OSError):
        cli.write_digest(new, tmp_path / "out")
    assert paths[fail_at - 1].read_bytes() == before[fail_at - 1]
    assert not list((tmp_path / "out").glob("*.tmp"))
    if fail_at == 1:
        assert cli.verify_digest_pair(*paths)["input_identity"] == old["input_identity"]
    else:
        with pytest.raises(cli.DigestOutputError):
            cli.verify_digest_pair(*paths)
    monkeypatch.setattr(archive_output.os, "replace", replace)
    cli.write_digest(new, tmp_path / "out")
    assert cli.verify_digest_pair(*paths)["input_identity"] == new["input_identity"]


@pytest.mark.parametrize("tamper", ["md", "identity", "metadata", "missing"])
def test_pair_verification_rejects_tampering(tmp_path, tamper):
    document = build(inputs(tmp_path / "in"))
    md, meta = cli.write_digest(document, tmp_path / "out")
    if tamper == "md":
        md.write_text(md.read_text() + "edited")
    elif tamper == "missing":
        meta.unlink()
    else:
        changed = json.loads(meta.read_text())
        changed["input_identity" if tamper == "identity" else "schema_version"] = "changed"
        meta.write_text(json.dumps(changed))
    with pytest.raises(cli.DigestOutputError):
        cli.verify_digest_pair(md, meta)


def test_render_failure_changes_no_existing_success(tmp_path, monkeypatch):
    document = build(inputs(tmp_path / "in"))
    paths = cli.write_digest(document, tmp_path / "out")
    before = [p.read_bytes() for p in paths]
    def forbidden(*args):
        raise ValueError("bad render")
    monkeypatch.setattr(cli, "render_digest", forbidden)
    with pytest.raises(ValueError):
        cli.write_digest(document, tmp_path / "out")
    assert [p.read_bytes() for p in paths] == before


def test_no_network_with_fake_keys_and_no_input_mutation(tmp_path, monkeypatch):
    import requests
    source = inputs(tmp_path / "in", items=[row("a")])
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    def forbidden(*args, **kwargs):
        raise AssertionError("network")
    monkeypatch.setattr(requests.Session, "request", forbidden)
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    assert cli.main(command(source, tmp_path / "out")) == 0
    assert {p.name: p.read_bytes() for p in source.iterdir()} == before


@pytest.mark.parametrize("entry", [["scripts/generate_digest.py"], ["-m", "scripts.generate_digest"]])
def test_real_direct_and_module_cli_exit_zero(tmp_path, entry):
    source = inputs(tmp_path / "in")
    result = subprocess.run([sys.executable, *entry, *command(source, tmp_path / "out")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "digest_generated" in result.stdout
    cli.verify_digest_pair(*cli._paths(tmp_path / "out", DATE))
