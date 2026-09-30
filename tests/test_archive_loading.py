"""An unreadable archive must never look like a fresh installation."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import pytest

from scripts import update_news


NOW = datetime(2026, 9, 26, tzinfo=timezone.utc)
ITEM_ID = "a" * 40


def archive_row(item_id=ITEM_ID):
    return {
        "id": item_id,
        "site_id": "official_ai",
        "source": "Example",
        "title": "Example AI update",
        "url": "https://example.com/news",
        "published_at": "2026-09-26T00:00:00Z",
        "last_seen_at": "2026-09-26T00:00:00Z",
    }


def test_missing_archive_allows_first_generation(tmp_path):
    assert update_news.load_archive(tmp_path / "archive.json") == {}


@pytest.mark.parametrize("items", [[], {}])
def test_valid_empty_archive_is_accepted(tmp_path, items):
    path = tmp_path / "archive.json"
    path.write_text(json.dumps({"generated_at": "2026-09-26T00:00:00Z", "items": items}))
    assert update_news.load_archive(path) == {}


def test_list_archive_preserves_legacy_aibase_normalization(tmp_path):
    path = tmp_path / "archive.json"
    row = archive_row()
    row.update(site_id="aibase", site_name="AIbase", source="AIbase")
    path.write_text(json.dumps({"items": [row]}))

    loaded = update_news.load_archive(path)

    assert list(loaded) == [ITEM_ID]
    assert loaded[ITEM_ID]["site_id"] == "curated_media"
    assert loaded[ITEM_ID]["source"] == "AIBASE"


def test_legacy_dict_archive_uses_key_as_record_id(tmp_path):
    path = tmp_path / "archive.json"
    row = archive_row("old-internal-id")
    path.write_text(json.dumps({"items": {ITEM_ID: row}}))

    loaded = update_news.load_archive(path)

    assert loaded[ITEM_ID]["id"] == ITEM_ID


@pytest.mark.parametrize("payload", [
    "{broken",
    "null",
    "[]",
    "{}",
    '{"items": null}',
    '{"items": "not-a-collection"}',
    '{"items": [null]}',
    '{"items": [{"title": "missing id"}]}',
    '{"items": [{"id": "same"}, {"id": "same"}]}',
    '{"items": {"key": null}}',
])
def test_existing_malformed_archive_raises_instead_of_becoming_empty(tmp_path, payload):
    path = tmp_path / "archive.json"
    path.write_text(payload)

    with pytest.raises(ValueError, match="archive"):
        update_news.load_archive(path)


def test_unreadable_archive_raises_instead_of_becoming_empty(tmp_path, monkeypatch):
    path = tmp_path / "archive.json"
    path.write_text('{"items": []}')
    original_read_text = type(path).read_text

    def unreadable(self, *args, **kwargs):
        if self == path:
            raise PermissionError("simulated unreadable archive")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(type(path), "read_text", unreadable)
    with pytest.raises(PermissionError, match="simulated unreadable archive"):
        update_news.load_archive(path)


@pytest.mark.parametrize("payload", ["{broken", '{"items": [null]}'])
def test_main_rejects_corrupt_archive_before_fetch_or_cleanup(tmp_path, monkeypatch, payload):
    output_dir = tmp_path / "data"
    output_dir.mkdir()
    archive_path = output_dir / "archive.json"
    archive_path.write_text(payload)
    latest_path = output_dir / "latest-24h.json"
    latest_path.write_text("previous snapshot")
    json_resolver = output_dir / "items" / f"{ITEM_ID}.json"
    json_resolver.parent.mkdir()
    json_resolver.write_text("previous resolver")
    html_adapter = tmp_path / "item" / ITEM_ID / "index.html"
    html_adapter.parent.mkdir(parents=True)
    html_adapter.write_text("previous adapter")

    def should_not_fetch(*args, **kwargs):
        raise AssertionError("fetch began before archive was validated")

    monkeypatch.setattr(update_news, "collect_all", should_not_fetch)
    monkeypatch.setattr(update_news, "utc_now", lambda: NOW)
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(output_dir)])

    with pytest.raises(ValueError, match="archive"):
        update_news.main()

    assert archive_path.read_text() == payload
    assert latest_path.read_text() == "previous snapshot"
    assert json_resolver.read_text() == "previous resolver"
    assert html_adapter.read_text() == "previous adapter"


def test_valid_archive_still_prunes_expired_records(tmp_path):
    path = tmp_path / "archive.json"
    fresh = archive_row()
    expired = archive_row("b" * 40)
    expired["last_seen_at"] = "2026-08-01T00:00:00Z"
    path.write_text(json.dumps({"items": [fresh, expired]}))

    retained = update_news.prune_archive_records(update_news.load_archive(path), NOW, 21)

    assert list(retained) == [ITEM_ID]


def test_first_generation_creates_archive_and_item_links(tmp_path, monkeypatch):
    output_dir = tmp_path / "data"
    raw = update_news.RawItem(
        site_id="official_ai",
        site_name="Official AI Updates",
        source="Example",
        title="OpenAI releases GPT-5 model",
        url="https://example.com/news",
        published_at=NOW,
        meta={},
    )

    def no_network(*args, **kwargs):
        raise AssertionError("unexpected network access")

    monkeypatch.setattr(update_news, "utc_now", lambda: NOW)
    monkeypatch.setattr(update_news, "create_session", lambda: object())
    monkeypatch.setattr(update_news, "collect_all", lambda *_: (
        [raw], [{"site_id": "official_ai", "site_name": "Official AI Updates", "ok": True, "item_count": 1}]
    ))
    monkeypatch.setattr(update_news, "run_market_sensors", lambda *_: (
        {"generated_at": update_news.iso(NOW), "signals": []}, {}, []
    ))
    monkeypatch.setattr("requests.sessions.Session.request", no_network)
    for name in ("X_BEARER_TOKEN", "SOCIALDATA_API_KEY", "TIKHUB_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(output_dir), "--translate-max-new", "0"])

    assert update_news.main() == 0
    archive = json.loads((output_dir / "archive.json").read_text())
    assert len(archive["items"]) == 1
    item_id = archive["items"][0]["id"]
    assert (output_dir / "items" / f"{item_id}.json").exists()
    assert (tmp_path / "item" / item_id / "index.html").exists()


def test_cli_fails_before_replacing_existing_output(tmp_path):
    output_dir = tmp_path / "data"
    output_dir.mkdir()
    (output_dir / "archive.json").write_text("{broken")
    latest = output_dir / "latest-24h.json"
    latest.write_text("previous snapshot")

    result = subprocess.run(
        [sys.executable, str(update_news.Path(update_news.__file__)), "--output-dir", str(output_dir)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=10,
    )

    assert result.returncode != 0
    assert "Invalid archive" in result.stderr
    assert latest.read_text() == "previous snapshot"
