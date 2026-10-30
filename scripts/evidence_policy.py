"""Text-only source filtering. Attachments are outside the news collector scope.

Source admission and publisher identity remain owned by publisher_policy.
This module restricts material formats; it does not promote publishers.
"""
from collections import Counter
import re
from urllib.parse import unquote, urlsplit, parse_qsl

VERSION = "official-text-v1"
TEXT_FORMATS = {"rss", "html", "text"}
EXCLUDED_SUFFIX = re.compile(
    r"\.(?:pdf|docx?|xlsx?|xlsm|pptx?|odt|ods|odp|rtf|epub|zip|gz|tar|7z|rar|"
    r"png|jpe?g|gif|webp|svg|tiff?|bmp|ico|avif|heic|mp[34]|m4[av]|mov|avi|webm|mkv|wav|ogg|flac)(?:$|[;/])", re.I)
NON_TEXT_NODES = "script, style, nav, aside, pre, table, figure, img, picture, video, audio, iframe, object, embed, canvas, svg, noscript, template, [hidden], [aria-hidden='true']"


def attachment_url(value):
    try:
        url = urlsplit(str(value or ""))
        path = unquote(unquote(url.path))
        if EXCLUDED_SUFFIX.search(path):
            return True
        for key, val in parse_qsl(url.query):
            decoded = unquote(unquote(val))
            if EXCLUDED_SUFFIX.search(decoded):
                return True
            if key.lower() in {"format", "type", "mime", "content-type"} and (
                    decoded.lower() in {"pdf", "docx", "xlsx", "pptx", "mp3", "mp4"}
                    or decoded.lower().startswith(("application/pdf", "image/", "audio/", "video/"))):
                return True
    except ValueError:
        pass
    return False


def validate_text_mime(content_type="", *, feed=False):
    """Reject attachment MIME before reading a streaming response body."""
    mime = str(content_type or "").split(";", 1)[0].strip().lower()
    allowed = {"text/html", "application/xhtml+xml", "text/plain"}
    if feed:
        allowed |= {"application/rss+xml", "application/atom+xml", "application/xml", "text/xml"}
    if mime and mime not in allowed:
        raise ValueError("unsupported_evidence_format")
    return mime


def validate_text_bytes(data, content_type="", *, feed=False):
    """Check MIME and bytes before interpreting HTML/XML; never decode a PDF."""
    mime = validate_text_mime(content_type, feed=feed)
    head = data.removeprefix(b"\xef\xbb\xbf").lstrip()[:1024]
    if (not head or head.startswith((b"%PDF", b"PK\x03\x04", b"\x89PNG", b"\xff\xd8", b"GIF8", b"RIFF", b"ID3", b"OggS", b"\x1f\x8b", b"\xd0\xcf\x11\xe0"))
            or b"\x00" in head or head[4:8] == b"ftyp"):
        raise ValueError("unsupported_evidence_format")
    if not mime:
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ValueError("unsupported_evidence_format") from None
    return data


def exclusion_reason(row):
    proof = row.get("primary_provenance") or {}
    if not isinstance(proof, dict):
        return "unsupported_evidence_format"
    formats = [row.get("evidence_format"), proof.get("evidence_format")]
    if any(value is not None and (not isinstance(value, str) or (value and value not in TEXT_FORMATS)) for value in formats):
        return "unsupported_evidence_format"
    if any(attachment_url(url) for url in [row.get("url"), proof.get("evidence_url"), *(proof.get("evidence_urls") or [])]):
        return "unsupported_evidence_format"
    return None


def annotate_archive(archive):
    counts = Counter()
    for row in archive.values():
        reason = exclusion_reason(row)
        if not reason:
            continue
        row["source_material_status"] = "superseded_unverified"
        proof = row.setdefault("primary_provenance", {})
        if isinstance(proof, dict):
            proof["qualification_hold_reason"] = reason
        counts[reason] += 1
    return dict(counts)
