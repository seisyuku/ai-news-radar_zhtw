"""The archive I/O boundary must work without the generator or source stack."""

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT = Path(__file__).resolve().parents[1]
ITEM_ID = "a" * 40


def test_record_contract_requires_identity_and_keeps_optional_fields_optional():
    output = importlib.import_module("scripts.archive_output")
    assert output.ArchiveRecord.__required_keys__ == {"id"}
    assert {"title", "url", "last_seen_at", "duplicate_of"} <= output.ArchiveRecord.__optional_keys__
    assert output.PublicItemResolver is output.ArchiveRecord


@pytest.mark.parametrize("package", [True, False])
def test_archive_output_is_independent_in_both_import_modes(tmp_path, package):
    module_name = "scripts.archive_output" if package else "archive_output"
    python_path = PROJECT if package else PROJECT / "scripts"
    script = """
import importlib.abc
import importlib
import json
import sys
from pathlib import Path

class RejectGeneratorDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'update_news', 'scripts.update_news', 'requests', 'bs4', 'dateutil'}:
            raise AssertionError('archive output imported generator/source dependencies: ' + fullname)

sys.meta_path.insert(0, RejectGeneratorDependencies())
output = importlib.import_module(sys.argv[1])
root = Path(sys.argv[2])
data = root / 'data'
data.mkdir()
item_id = 'a' * 40
record = {'id': item_id, 'title': 'Public AI update', 'url': 'https://example.invalid/news'}
path = data / 'archive.json'
output.atomic_write_text(path, json.dumps({'items': [record]}))
archive = output.load_archive(path, normalize_record=lambda row: dict(row))
assert archive == {item_id: record}
assert output.write_item_resolvers(data, archive, sanitize_record=lambda row: dict(row)) == 1
assert output.write_item_html_adapters(data, archive, sanitize_record=lambda row: dict(row)) == 1
assert json.loads((data / 'items' / (item_id + '.json')).read_text()) == record
assert item_id in (root / 'item' / item_id / 'index.html').read_text()
assert 'update_news' not in sys.modules and 'scripts.update_news' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script, module_name, str(tmp_path)],
        cwd=tmp_path, capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONPATH": str(python_path), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("legacy", [False, True])
def test_loader_validates_identity_then_uses_explicit_normalization(tmp_path, legacy):
    output = importlib.import_module("scripts.archive_output")
    row = {"id": "legacy-internal" if legacy else ITEM_ID, "site_id": "old-source", "extension": {"keep": True}}
    items = {ITEM_ID: row} if legacy else [row]
    path = tmp_path / "archive.json"
    path.write_text(json.dumps({"items": items}))
    received = []

    def normalize(record):
        received.append(dict(record))
        return {**record, "site_id": "normalized-source"}

    archive = output.load_archive(path, normalize_record=normalize)

    assert received == [{**row, "id": ITEM_ID}]
    assert archive == {ITEM_ID: {**row, "id": ITEM_ID, "site_id": "normalized-source"}}
    assert json.loads(path.read_text())["items"] == items


def test_resolvers_apply_explicit_public_policy_without_mutating_archive(tmp_path):
    output = importlib.import_module("scripts.archive_output")
    row = {"id": "wrong-field", "title": "private input", "url": "https://example.invalid/news", "extension": {"keep": True}}
    archive = {ITEM_ID: row}

    def sanitize(record):
        record["title"] = "公開標題 <safe>"
        return record

    data = tmp_path / "data"
    assert output.write_item_resolvers(data, archive, sanitize_record=sanitize) == 1
    assert output.write_item_html_adapters(data, archive, sanitize_record=sanitize) == 1
    assert json.loads((data / "items" / f"{ITEM_ID}.json").read_text()) == {
        **row, "id": ITEM_ID, "title": "公開標題 <safe>",
    }
    page = (tmp_path / "item" / ITEM_ID / "index.html").read_text()
    assert "公開標題 &lt;safe&gt;" in page and "private input" not in page
    assert archive == {ITEM_ID: row} and row["title"] == "private input"


def test_generator_resolver_wrappers_keep_public_redaction(tmp_path):
    from scripts import update_news

    row = {
        "id": ITEM_ID, "title": "Contact editor@example.invalid",
        "summary": "token=synthetic-sensitive-value", "url": "https://example.invalid/news",
        "extension": {"email": "editor@example.invalid"},
    }
    data = tmp_path / "data"
    update_news.write_item_resolvers(data, {ITEM_ID: row})
    update_news.write_item_html_adapters(data, {ITEM_ID: row})

    resolver = json.loads((data / "items" / f"{ITEM_ID}.json").read_text())
    assert resolver == update_news.sanitize_public_payload(row)
    page = (tmp_path / "item" / ITEM_ID / "index.html").read_text()
    assert "[redacted-email]" in page and "[redacted-secret]" in page
    assert "editor@example.invalid" not in page and "synthetic-sensitive-value" not in page
    assert row["title"] == "Contact editor@example.invalid"
