"""Private storage, resume/no overwrite, raw pair readback, and public-log boundaries."""

from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from scripts import digest_drive_delivery as drive
from scripts import generate_digest_job as job
from tests.test_generate_digest_job import inputs


NOW = datetime(2026, 10, 9, 23, 15, tzinfo=timezone.utc)
DATE = "2026-10-10"
TARGET = {"folder_id": "root", "settings_id": "settings"}
SETTINGS = {"schema_version": 1, "mode": "synthetic-test", "timezone": "Asia/Taipei",
            "cutoff": "06:00", "generation_location": "github-actions",
            "automation_enabled": False, "trial_status": "verified"}


class MemoryDrive:
    def __init__(self):
        self.files, self.docs, self.bytes, self.writes = {}, {}, {}, []
        self.new("root", "Root", drive.FOLDER_MIME)
        self.new("settings", "Settings", drive.DOC_MIME)
        self.docs["settings"] = "設定\n" + json.dumps(SETTINGS)

    def new(self, id, name, mime, parent=None, base=None):
        file = {"id": id, "name": name, "mimeType": mime, "parents": [parent] if parent else [],
                "shared": False, "owners": [{"me": True}],
                "permissions": [{"type": "user", "role": "owner"}],
                "webViewLink": "https://docs.google.com/document/d/" + id,
                "appProperties": {"digest_base": base} if base else {}}
        self.files[id] = file
        if mime == drive.DOC_MIME:
            self.docs[id] = ""
        return deepcopy(file)

    def metadata(self, id):
        return deepcopy(self.files[id])

    def find(self, parent, name):
        return next((deepcopy(f) for f in self.files.values() if f["parents"] == [parent] and f["name"] == name), None)

    def create(self, parent, name, mime, *, base=None, raw=None):
        id = "file" + str(len(self.files))
        self.writes.append(("create", id))
        file = self.new(id, name, mime, parent, base)
        if raw is not None:
            self.bytes[id] = raw
        return file

    def download(self, id):
        return self.bytes[id]

    def document(self, id):
        return {"revisionId": "synthetic-revision", "body": {"content": [
            {"paragraph": {"elements": [{"textRun": {"content": self.docs[id] + "\n"}}]}}]}}

    def write_document(self, id, revision, requests):
        assert revision == "synthetic-revision"
        self.writes.append(("write", id))
        for request in requests:
            if "insertText" in request:
                self.docs[id] += request["insertText"]["text"]
            if "replaceAllText" in request:
                replace = request["replaceAllText"]
                self.docs[id] = self.docs[id].replace(replace["containsText"]["text"], replace["replaceText"])

    def copy(self, id, parent, name):
        file = self.create(parent, name, drive.DOC_MIME)
        self.docs[file["id"]] = self.docs[id]
        return file


def pair(tmp_path):
    row = {"title": "OpenAI announces a synthetic agent 😀", "site_id": "official_ai",
           "source": "OpenAI News", "published_at": "2026-10-10T05:30:00+08:00",
           "summary": "PRIVATE publisher summary", "id": "a", "url": "https://example.invalid/a"}
    source = inputs(tmp_path / "input", rows=[row])
    output = tmp_path / "generated"
    assert job.generate(DATE, source, output, clock=lambda: NOW)["pair_verified"]
    return [(output / "pair" / ("digest-" + DATE + ext)).read_bytes() for ext in (".md", ".meta.json")]


def test_real_pair_preserved_native_original_review_and_repeat_keeps_human_edit(tmp_path):
    client, raw = MemoryDrive(), pair(tmp_path)
    result = drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    assert result["delivery_verified"]
    assert result["storage_quality"] == "ready-for-review" and result["storage_timeliness"] == "on_time"
    ids = result["file_ids"]
    assert client.bytes[ids["markdown"]] == raw[0] and client.bytes[ids["metadata"]] == raw[1]
    assert "原稿" in client.docs[ids["original"]] and "校稿副本" in client.docs[ids["review"]]
    assert "digest-identity" not in client.docs[ids["original"]]
    assert "PRIVATE publisher summary" in client.docs[ids["original"]]
    client.docs[ids["review"]] = "私人人工校稿"
    writes = list(client.writes)
    later = datetime(2026, 10, 10, 7, tzinfo=timezone.utc)
    repeated = drive.deliver_pair(client, TARGET, *raw, clock=lambda: later)
    assert repeated["storage_quality"] == "review-only" and repeated["storage_timeliness"] == "late"
    assert repeated["file_ids"] == ids and client.writes == writes
    assert client.docs[ids["review"]] == "私人人工校稿"


def test_bad_pair_or_shared_target_fails_before_creating_files(tmp_path):
    client, raw = MemoryDrive(), pair(tmp_path)
    with pytest.raises(ValueError):
        drive.deliver_pair(client, TARGET, b"corrupt", raw[1], clock=lambda: NOW)
    assert not client.writes
    client.files["root"]["shared"] = True
    with pytest.raises(drive.DriveDeliveryError, match="private_destination_required"):
        drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    assert not client.writes


def test_changed_original_never_overwritten_and_partial_pair_resumes(tmp_path):
    client, raw = MemoryDrive(), pair(tmp_path)
    original_download = client.download
    calls = [0]
    def interrupted(id):
        calls[0] += 1
        if calls[0] == 2:
            raise drive.DriveDeliveryError("drive_unavailable")
        return original_download(id)
    client.download = interrupted
    with pytest.raises(drive.DriveDeliveryError):
        drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    client.download = original_download
    result = drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    assert sum(f["name"].endswith(".md") for f in client.files.values()) == 1
    client.bytes[result["file_ids"]["markdown"]] = b"human changed original"
    writes = list(client.writes)
    with pytest.raises(drive.DriveDeliveryError, match="existing_original_mismatch"):
        drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    assert client.writes == writes


def test_different_base_and_date_crossing_do_not_replace_previous(tmp_path):
    client, raw = MemoryDrive(), pair(tmp_path)
    result = drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    folder = next(f for f in client.files.values() if f["mimeType"] == drive.FOLDER_MIME and f["id"] != "root")
    folder["appProperties"]["digest_base"] = "other-base"
    writes = list(client.writes)
    with pytest.raises(drive.DriveDeliveryError, match="existing_issue_conflict"):
        drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    assert client.writes == writes
    folder["appProperties"]["digest_base"] = json.loads(raw[1])["input_identity"]
    times = iter([NOW, datetime(2026, 10, 10, 16, tzinfo=timezone.utc)])
    with pytest.raises(drive.DriveDeliveryError, match="missed_issue"):
        drive.deliver_pair(client, TARGET, *raw, clock=lambda: next(times))
    assert client.bytes[result["file_ids"]["markdown"]] == raw[0]


@pytest.mark.parametrize("patch", [{"cutoff": "03:00"}, {"timezone": "UTC"},
                                  {"generation_location": "cloudflare"}, {"automation_enabled": "true"},
                                  {"command": "PRIVATE shell instruction"}])
def test_settings_cannot_expand_actions_or_change_agreed_window(tmp_path, patch):
    client, raw = MemoryDrive(), pair(tmp_path)
    client.docs["settings"] = json.dumps({**SETTINGS, **patch})
    with pytest.raises(drive.DriveDeliveryError, match="invalid_drive_settings"):
        drive.deliver_pair(client, TARGET, *raw, clock=lambda: NOW)
    assert not client.writes


def test_native_formats_utf16_headings_and_source_links(tmp_path):
    raw = pair(tmp_path)
    title, text, requests = drive.native_content(json.loads(raw[1]), False)
    assert text.startswith(title) and "###" not in text
    styles = [r["updateParagraphStyle"] for r in requests if "updateParagraphStyle" in r]
    assert {r["paragraphStyle"]["namedStyleType"] for r in styles} == {"TITLE", "HEADING_1", "HEADING_2"}
    links = [r["updateTextStyle"] for r in requests if "updateTextStyle" in r]
    assert links and all(r["textStyle"]["link"]["url"].startswith("https://") for r in links)
    assert max(r["range"]["endIndex"] for r in styles) <= 1 + len(text.encode("utf-16-le")) // 2


def test_http_refresh_and_upload_do_not_redirect_or_replay_provider_errors():
    class Session:
        headers = {}
        def request(self, method, url, **kwargs):
            assert kwargs["allow_redirects"] is False
            assert kwargs["timeout"] == (10, 30)
            return type("Response", (), {"status_code": 200, "json": lambda _: {
                "access_token": "SYNTHETIC", "token_type": "Bearer", "scope": drive.SCOPE}})()
    credentials = {"scope": drive.SCOPE, "token_type": "Bearer", "client_id": "SYNTHETIC",
                   "client_secret": "PRIVATE", "refresh_token": "PRIVATE"}
    client = drive.DriveClient(credentials, session=Session())
    assert client.session.headers["Authorization"] == "Bearer SYNTHETIC"
    with pytest.raises(drive.DriveDeliveryError, match="invalid_drive_config"):
        client.metadata("https://evil.invalid")


def test_cli_saves_private_links_without_public_log_or_summary(tmp_path, monkeypatch, capsys):
    from scripts import digest_drive_delivery
    source = inputs(tmp_path / "input")
    monkeypatch.setenv("GOOGLE_DRIVE_OAUTH_CREDENTIALS", '{"PRIVATE":"token"}')
    monkeypatch.setenv("GOOGLE_DRIVE_DIGEST_TARGET", '{"folder_id":"PRIVATE-FOLDER"}')
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))
    monkeypatch.setattr(digest_drive_delivery, "DriveClient", lambda _: object())
    result = {"delivery_verified": True, "saved_at": NOW.isoformat(),
              "storage_quality": "ready-for-review", "storage_reason": "archive_recent_after_cutoff",
              "storage_timeliness": "historical",
              "links": {"review": "https://docs.google.com/document/d/PRIVATE"},
              "file_ids": {"review": "PRIVATE-FILE"}}
    monkeypatch.setattr(digest_drive_delivery, "deliver_pair", lambda *a, **k: result)
    args = ["--date", DATE, "--historical", "--deliver-drive", "--input-dir", str(source),
            "--output-dir", str(tmp_path / "output")]
    assert job.main(args) == 0
    printed = capsys.readouterr().out
    assert json.loads(printed)["status"] == "review-only"
    assert json.loads(printed)["delivery_verified"] is True
    assert "PRIVATE" not in printed and "PRIVATE" not in (tmp_path / "summary.md").read_text()
    saved = tmp_path / "output" / "private-delivery.json"
    assert json.loads(saved.read_text()) == result and saved.stat().st_mode & 0o077 == 0
    monkeypatch.setattr(digest_drive_delivery, "deliver_pair", lambda *a, **k: (_ for _ in ()).throw(OSError("PRIVATE secret")))
    args[-1] = str(tmp_path / "failure")
    assert job.main(args) == 1
    assert "PRIVATE" not in capsys.readouterr().out
