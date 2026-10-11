"""Single-maintainer private Drive delivery. No transaction-service claims.

Raw MD/meta stay unchanged. Existing originals and human reviews are never
updated. GitHub concurrency serializes this workflow; Drive is not immutable.
"""

from datetime import datetime, time, timezone
import json
import re
import secrets

import requests

try:
    from .digest_drive_oauth import SCOPE, TOKEN_ENDPOINT
    from .digest_integrity import verify_digest_bytes
    from .digest_window import TAIPEI, window_for_date
except ImportError:
    from digest_drive_oauth import SCOPE, TOKEN_ENDPOINT
    from digest_integrity import verify_digest_bytes
    from digest_window import TAIPEI, window_for_date


DRIVE = "https://www.googleapis.com/drive/v3/files"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
DOCS = "https://docs.googleapis.com/v1/documents"
DOC_MIME = "application/vnd.google-apps.document"
FOLDER_MIME = "application/vnd.google-apps.folder"
FILE_FIELDS = "id,name,mimeType,parents,webViewLink,shared,owners(me),permissions(type,role),appProperties"
ID = re.compile(r"[A-Za-z0-9_-]{1,200}\Z")


class DriveDeliveryError(ValueError):
    pass


def file_id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise DriveDeliveryError("invalid_drive_config")
    return value


class DriveClient:
    def __init__(self, credentials, *, session=None):
        if (not isinstance(credentials, dict) or credentials.get("scope") != SCOPE
                or credentials.get("token_type") != "Bearer"
                or any(not isinstance(credentials.get(k), str) or not credentials[k]
                       for k in ("client_id", "client_secret", "refresh_token"))):
            raise DriveDeliveryError("invalid_drive_credentials")
        self.session = session or requests.Session()
        response = self._request("POST", TOKEN_ENDPOINT, data={
            "client_id": credentials["client_id"], "client_secret": credentials["client_secret"],
            "refresh_token": credentials["refresh_token"], "grant_type": "refresh_token",
        })
        grant = response.json()
        if (grant.get("token_type") != "Bearer" or not isinstance(grant.get("access_token"), str)
                or not grant["access_token"] or
                ("scope" in grant and set(grant["scope"].split()) != {SCOPE})):
            raise DriveDeliveryError("unexpected_grant")
        self.session.headers["Authorization"] = "Bearer " + grant["access_token"]

    def _request(self, method, url, **kwargs):
        # URLs are built only by methods below; never from config or document text.
        try:
            response = self.session.request(method, url, timeout=(10, 30),
                                            allow_redirects=False, **kwargs)
            if not 200 <= response.status_code < 300:
                raise DriveDeliveryError("drive_request_failed")
            return response
        except DriveDeliveryError:
            raise
        except Exception:
            raise DriveDeliveryError("drive_unavailable") from None

    def json(self, method, url, **kwargs):
        try:
            result = self._request(method, url, **kwargs).json()
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except DriveDeliveryError:
            raise
        except Exception:
            raise DriveDeliveryError("invalid_drive_response") from None

    def metadata(self, id):
        return self.json("GET", DRIVE + "/" + file_id(id), params={"fields": FILE_FIELDS})

    def find(self, parent, name):
        # Names come from fixed issue/role labels, not arbitrary Drive settings.
        name = name.replace("\\", "\\\\").replace("'", "\\'")
        result = self.json("GET", DRIVE, params={
            "q": "'" + file_id(parent) + "' in parents and name = '" + name + "' and trashed = false",
            "fields": "files(" + FILE_FIELDS + "),nextPageToken", "pageSize": 100,
        })
        files = result.get("files", [])
        if len(files) > 1 or result.get("nextPageToken"):
            raise DriveDeliveryError("ambiguous_existing_file")
        return files[0] if files else None

    def create(self, parent, name, mime, *, base=None, raw=None):
        body = {"name": name, "mimeType": mime, "parents": [file_id(parent)]}
        if base:
            body["appProperties"] = {"digest_base": base}
        if raw is None:
            return self.json("POST", DRIVE, params={"fields": FILE_FIELDS}, json=body)
        boundary = "digest-" + secrets.token_hex(16)
        payload = ("--" + boundary + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n").encode()
        payload += json.dumps(body, ensure_ascii=False).encode() + b"\r\n"
        payload += ("--" + boundary + "\r\nContent-Type: " + mime + "\r\n\r\n").encode()
        payload += raw + ("\r\n--" + boundary + "--\r\n").encode()
        return self.json("POST", UPLOAD, params={"fields": FILE_FIELDS, "uploadType": "multipart"},
                         data=payload, headers={"Content-Type": "multipart/related; boundary=" + boundary})

    def download(self, id):
        return self._request("GET", DRIVE + "/" + file_id(id), params={"alt": "media"}).content

    def document(self, id):
        return self.json("GET", DOCS + "/" + file_id(id))

    def write_document(self, id, revision, requests):
        return self.json("POST", DOCS + "/" + file_id(id) + ":batchUpdate",
                         json={"writeControl": {"requiredRevisionId": revision}, "requests": requests})

    def copy(self, id, parent, name):
        return self.json("POST", DRIVE + "/" + file_id(id) + "/copy",
                         params={"fields": FILE_FIELDS},
                         json={"name": name, "parents": [file_id(parent)]})


def private(file, parent=None, mime=None):
    if (file.get("shared") is not False or file.get("owners") != [{"me": True}]
            or file.get("permissions") != [{"type": "user", "role": "owner"}]
            or (parent and file.get("parents") != [parent])
            or (mime and file.get("mimeType") != mime)):
        raise DriveDeliveryError("private_destination_required")


def document_text(document):
    return "".join(e.get("textRun", {}).get("content", "")
                   for item in document.get("body", {}).get("content", [])
                   for e in item.get("paragraph", {}).get("elements", []))


def read_settings(client, id):
    text = document_text(client.document(id))
    try:
        data = json.loads(text[text.index("{"):])
        allowed = {"schema_version", "mode", "timezone", "cutoff", "generation_location",
                   "automation_enabled", "trial_status"}
        if (not isinstance(data, dict) or set(data) - allowed
                or type(data.get("schema_version")) is not int or data["schema_version"] != 1
                or data.get("timezone") != "Asia/Taipei" or data.get("cutoff") != "06:00"
                or data.get("generation_location") != "github-actions"
                or type(data.get("automation_enabled")) is not bool):
            raise ValueError()
    except Exception:
        raise DriveDeliveryError("invalid_drive_settings") from None
    return data


def native_content(metadata, review_only):
    """Readable native paragraphs and links; identities stay in the raw pair."""
    date = metadata["window"]["date"]
    window = window_for_date(date)
    title = "AI 新聞日報｜" + date + "｜原稿"
    lines, styles, links = [], [], []
    offset = 1
    def line(text, style=None, url=None):
        nonlocal offset
        start = offset
        lines.append(text + "\n")
        offset += len((text + "\n").encode("utf-16-le")) // 2
        if style:
            styles.append({"updateParagraphStyle": {"range": {"startIndex": start, "endIndex": offset},
                           "paragraphStyle": {"namedStyleType": style}, "fields": "namedStyleType"}})
        if url:
            links.append({"updateTextStyle": {"range": {"startIndex": start, "endIndex": offset - 1},
                         "textStyle": {"link": {"url": url}}, "fields": "link"}})
    line(title, "TITLE")
    line("新聞窗口：" + window.start_utc.astimezone(TAIPEI).strftime("%Y-%m-%d %H:%M") + "～" +
         window.end_utc.astimezone(TAIPEI).strftime("%Y-%m-%d %H:%M") + "（臺北時間）")
    line("狀態：歷史審閱稿。" if review_only else "狀態：供人工校稿；是否達標另見本次生成結果。")
    line("今日重點", "HEADING_1")
    candidates = metadata.get("candidates", [])
    if not candidates:
        line("本次選題零則。")
    for index, item in enumerate(candidates, 1):
        line(str(index) + ". " + (item.get("title") or item.get("title_original") or "未標示標題"),
             "HEADING_2", item.get("primary_url"))
        label = "出版者摘要（既有快取譯文）：" if item.get("summary_kind") == "publisher_translation" else "出版者摘要："
        line(label + item["summary"] if item.get("summary") else "摘要：目前沒有可用的出版者摘要。")
        for source in item.get("sources", []):
            line("來源：" + (source.get("source") or "未標示來源") + "｜" +
                 (source.get("title") or source.get("title_original") or "原文"), url=source.get("url"))
    from_text = "".join(lines)
    return title, from_text, styles + links


def retain(client, parent, name, mime, raw):
    file = client.find(parent, name)
    if file is None:
        file = client.create(parent, name, mime, raw=raw)
    private(client.metadata(file["id"]), parent, mime)
    downloaded = client.download(file["id"])
    if downloaded != raw:
        raise DriveDeliveryError("existing_original_mismatch")
    return file, downloaded


def deliver_pair(client, target, markdown, metadata_bytes, *, historical=False,
                 clock=lambda: datetime.now(timezone.utc)):
    """Create/resume one issue folder without overwriting any existing document."""
    folder_id, settings_id = file_id(target.get("folder_id")), file_id(target.get("settings_id"))
    metadata = verify_digest_bytes(markdown, metadata_bytes)
    date = metadata["window"]["date"]
    window_for_date(date)
    if not historical and clock().astimezone(TAIPEI).date().isoformat() != date:
        raise DriveDeliveryError("missed_issue")
    private(client.metadata(folder_id), mime=FOLDER_MIME)
    settings = client.metadata(settings_id)
    private(settings, mime=DOC_MIME)
    read_settings(client, settings_id)
    mode = "historical" if historical else "current"
    name = date + "｜" + mode
    folder = client.find(folder_id, name)
    base = metadata["input_identity"]
    if folder:
        private(client.metadata(folder["id"]), folder_id, FOLDER_MIME)
        if folder.get("appProperties", {}).get("digest_base") != base:
            raise DriveDeliveryError("existing_issue_conflict")
    else:
        folder = client.create(folder_id, name, FOLDER_MIME, base=base)
        private(client.metadata(folder["id"]), folder_id, FOLDER_MIME)
    parent = folder["id"]
    md_file, read_md = retain(client, parent, "digest-" + date + ".md", "text/markdown", markdown)
    meta_file, read_meta = retain(client, parent, "digest-" + date + ".meta.json", "application/json", metadata_bytes)
    verify_digest_bytes(read_md, read_meta)  # Existing pair contract, not a code/remote SHA audit.
    # Readable original is deterministic. Age at a later retry cannot change it.
    title, text, styles = native_content(metadata, historical)
    original = client.find(parent, title)
    if original is None:
        original = client.create(parent, title, DOC_MIME)
        before = client.document(original["id"])
        client.write_document(original["id"], before["revisionId"], [
            {"insertText": {"location": {"index": 1}, "text": text}}, *styles])
    original = client.metadata(original["id"])
    private(original, parent, DOC_MIME)
    actual = document_text(client.document(original["id"]))
    if actual.strip() != text.strip():
        raise DriveDeliveryError("existing_original_mismatch")
    review_name = title.replace("｜原稿", "｜校稿副本")
    review = client.find(parent, review_name)
    if review is None:
        review = client.copy(original["id"], parent, review_name)
        before = client.document(review["id"])
        client.write_document(review["id"], before["revisionId"], [{"replaceAllText": {
            "containsText": {"text": title, "matchCase": True}, "replaceText": review_name}}])
        if document_text(client.document(review["id"])).strip() != text.replace(title, review_name).strip():
            raise DriveDeliveryError("review_readback_mismatch")
    review = client.metadata(review["id"])
    private(review, parent, DOC_MIME)
    saved_at = clock()
    if not historical and saved_at.astimezone(TAIPEI).date().isoformat() != date:
        raise DriveDeliveryError("missed_issue")
    # URLs are private return values only; caller must not put these in Actions logs.
    if not all(isinstance(f.get("webViewLink"), str) and f["webViewLink"]
               for f in (original, review, settings)):
        raise DriveDeliveryError("private_links_unavailable")
    try:
        from .deliver_digest import readiness
    except ImportError:
        from deliver_digest import readiness
    as_of = next((i.get("producer_as_of") for i in metadata.get("inputs", [])
                  if i.get("name") == "archive.json"), None)
    quality, reason = readiness(as_of, window_for_date(date), saved_at)
    deadline = datetime.combine(window_for_date(date).end_utc.astimezone(TAIPEI).date(), time(9), TAIPEI)
    return {"delivery_verified": True, "saved_at": saved_at.isoformat(),
            "storage_quality": quality, "storage_reason": reason,
            "storage_timeliness": "historical" if historical else ("on_time" if saved_at <= deadline else "late"),
            "links": {"original": original.get("webViewLink"), "review": review.get("webViewLink"),
                      "settings": settings.get("webViewLink")},
            "file_ids": {"markdown": md_file["id"], "metadata": meta_file["id"],
                         "original": original["id"], "review": review["id"]}}
