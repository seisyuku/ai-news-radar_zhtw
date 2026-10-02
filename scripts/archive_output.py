"""Validated archive input and per-file public resolver output.

This module uses only the standard library. The generator supplies normalization
and sanitization policies explicitly; no source adapters or generation entrypoint
are imported. See docs/ARCHIVE_OUTPUT.md for the retained wire contract.
"""

import html
import json
import os
import re
import stat
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Required, TypedDict, cast


# Eager annotations keep Required[id] visible to Python 3.11 introspection.
class ArchiveRecord(TypedDict, total=False):
    """Known generated fields; historical/extension keys remain untouched.

    Loading validates record identity only, as before. Optional field annotations
    describe generated records rather than imposing new runtime validation.
    """

    id: Required[str]
    site_id: str
    site_name: str
    source: str
    title: str
    url: str
    published_at: str | None
    first_seen_at: str | None
    last_seen_at: str | None
    summary: str
    content_language: str
    field_languages: dict[str, str]
    aibase_article_id: str
    duplicate_of: str


Archive = dict[str, ArchiveRecord]
# A resolver carries the same record as the public archive, not a new schema.
PublicItemResolver = ArchiveRecord
RecordTransform = Callable[[dict[str, Any]], dict[str, Any]]


class ArchiveSnapshot(TypedDict):
    """Canonical generated archive; load_archive also accepts legacy keyed items."""

    generated_at: str
    total_items: int
    items: list[ArchiveRecord]


def load_archive(path: Path, *, normalize_record: RecordTransform) -> Archive:
    """Load retained items; only a missing file represents first generation.

    An existing but unreadable or malformed archive must stop the update
    before resolver cleanup can remove previously published item links.
    """
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid archive at {path}: cannot decode JSON") from exc
    return archive_from_payload(payload, normalize_record=normalize_record, label=str(path))


def archive_from_payload(
    payload: object, *, normalize_record: RecordTransform, label: str = "archive"
) -> Archive:
    """Validate an already captured payload using the path loader's policy.

    No filesystem access: callers can parse and fingerprint the same bytes.
    The legacy path loader keeps its missing-file and decoding semantics.
    """
    path = label

    if not isinstance(payload, dict) or "items" not in payload:
        raise ValueError(f"Invalid archive at {path}: expected an object with items")
    items = payload["items"]
    out: Archive = {}
    if isinstance(items, list):
        for index, it in enumerate(items):
            if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"].strip():
                raise ValueError(f"Invalid archive at {path}: items[{index}] has no valid ID")
            item_id = it["id"]
            if item_id in out:
                raise ValueError(f"Invalid archive at {path}: duplicate item ID")
            out[item_id] = cast(ArchiveRecord, normalize_record(it))
    elif isinstance(items, dict):
        for item_id, it in items.items():
            if not isinstance(item_id, str) or not item_id.strip() or not isinstance(it, dict):
                raise ValueError(f"Invalid archive at {path}: items contains an invalid entry")
            normalized = dict(it)
            normalized["id"] = item_id
            out[item_id] = cast(ArchiveRecord, normalize_record(normalized))
    else:
        raise ValueError(f"Invalid archive at {path}: items must be a list or object")
    return out


def atomic_write_text(path: Path, text: str) -> None:
    """Replace one UTF-8 file only after a complete same-directory write.

    Existing file permissions are retained; new generated files are readable
    like the published snapshots. This is not a multi-file transaction or a
    guarantee of durability after power loss. Only our temporary file is removed.
    """
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        mode = 0o644
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        try:
            stream = os.fdopen(fd, "w", encoding="utf-8")
        except BaseException:
            os.close(fd)
            raise
        with stream:
            stream.write(text)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def prune_item_outputs(
    output_dir: Path,
    archive: Mapping[str, Mapping[str, Any]],
    *,
    json_resolvers: bool = True,
    html_adapters: bool = True,
) -> None:
    """Apply existing retention rules after the caller's output writes succeed."""
    active_ids = {
        item_id for item_id in archive
        if re.fullmatch(r"[a-f0-9]{40}", str(item_id), flags=re.IGNORECASE)
    }
    if json_resolvers:
        for path in (output_dir / "items").glob("*.json"):
            is_resolver = re.fullmatch(r"[a-f0-9]{40}\.json", path.name, flags=re.IGNORECASE)
            if is_resolver and path.stem not in active_ids:
                path.unlink()
    adapter_dir = output_dir.parent / "item"
    if html_adapters and adapter_dir.exists():
        for item_dir in adapter_dir.iterdir():
            is_adapter_dir = (
                item_dir.is_dir()
                and re.fullmatch(r"[a-f0-9]{40}", item_dir.name, flags=re.IGNORECASE)
            )
            if is_adapter_dir and item_dir.name not in active_ids:
                page_path = item_dir / "index.html"
                if page_path.exists():
                    page_path.unlink()
                try:
                    item_dir.rmdir()
                except OSError:
                    pass


def write_item_resolvers(
    output_dir: Path,
    archive: Mapping[str, Mapping[str, Any]],
    *,
    sanitize_record: RecordTransform,
    prune: bool = True,
) -> int:
    """Write one public archive-schema JSON record per stable news item ID.

    The directory is a GitHub Pages lookup surface, not a second item schema:
    each file contains the same public record stored in archive.json. Removing
    resolver files absent from the pruned archive keeps retention aligned with
    the archive and prevents stale files from accumulating indefinitely.
    """
    resolver_dir = output_dir / "items"
    resolver_dir.mkdir(parents=True, exist_ok=True)
    active_ids = {
        item_id
        for item_id in archive
        if re.fullmatch(r"[a-f0-9]{40}", str(item_id), flags=re.IGNORECASE)
    }

    for item_id in active_ids:
        record = dict(archive[item_id])
        # The filename, lookup key, and public field must always agree.
        record["id"] = item_id
        atomic_write_text(
            resolver_dir / f"{item_id}.json",
            json.dumps(sanitize_record(record), ensure_ascii=False, indent=2),
        )

    if prune:
        prune_item_outputs(output_dir, archive, html_adapters=False)

    return len(active_ids)


def write_item_html_adapters(
    output_dir: Path,
    archive: Mapping[str, Mapping[str, Any]],
    *,
    sanitize_record: RecordTransform,
    prune: bool = True,
) -> int:
    """Write one static, human-readable resolver page per archived item ID.

    JSON resolvers live below ``data/items``. These documents deliberately live
    at the Pages root (``item/<id>/``) so browser and LLM retrieval can use a
    deterministic HTML path without a client-side lookup. They use the same
    pruned archive records and cleanup rule as the JSON resolvers.
    """
    adapter_dir = output_dir.parent / "item"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    active_ids = {
        item_id
        for item_id in archive
        if re.fullmatch(r"[a-f0-9]{40}", str(item_id), flags=re.IGNORECASE)
    }

    def definition_row(label: str, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        return f"    <dt>{html.escape(label)}</dt>\n    <dd>{html.escape(text, quote=True)}</dd>"

    for item_id in active_ids:
        record = sanitize_record(dict(archive[item_id]))
        record["id"] = item_id
        rows = [definition_row("Radar ID", item_id)]
        for label, field in (
            ("Title", "title"),
            ("Source", "source"),
            ("Published", "published_at"),
            ("Summary", "summary"),
        ):
            row = definition_row(label, record.get(field))
            if row:
                rows.append(row)

        original_url = str(record.get("url") or "").strip()
        if original_url:
            escaped_url = html.escape(original_url, quote=True)
            rows.append(
                "    <dt>Original URL</dt>\n"
                f'    <dd><a href="{escaped_url}">{escaped_url}</a></dd>'
            )

        page = "\n".join((
            "<!doctype html>",
            '<html lang="zh-Hant">',
            "<head>",
            '  <meta charset="utf-8">',
            "  <title>AI News Radar Pulse — News Item</title>",
            "</head>",
            "<body>",
            "  <main>",
            "    <h1>AI News Radar Pulse — News Item</h1>",
            "    <dl>",
            *rows,
            "    </dl>",
            "  </main>",
            "</body>",
            "</html>",
            "",
        ))
        item_dir = adapter_dir / item_id
        item_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_text(item_dir / "index.html", page)

    if prune:
        prune_item_outputs(output_dir, archive, json_resolvers=False)

    return len(active_ids)
