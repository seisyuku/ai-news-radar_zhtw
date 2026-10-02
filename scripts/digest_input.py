"""Read three digest inputs once; no fetching, translation or file writes.

Captured bytes are immutable; decoded working dictionaries are independently
owned by this snapshot. Consumers must copy them before enrichment. Multi-file
capture is not transactional, even when producer timestamps match.
"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

if __package__:
    from .archive_output import Archive, RecordTransform, archive_from_payload
    from .digest_window import DigestTimeError, parse_published_at
else:  # Direct maintainer imports with scripts on sys.path.
    from archive_output import Archive, RecordTransform, archive_from_payload
    from digest_window import DigestTimeError, parse_published_at


INPUT_NAMES = ("archive.json", "title-zh-cache.json", "source-status.json")
_HEALTH_FIELDS = {
    "site_id", "site_name", "source_id", "ok", "attempted", "skipped", "disabled",
    "item_count", "partial_failures", "degraded", "persistent_failure",
    "consecutive_failures", "last_attempt_ok", "first_failure_at", "last_failure_at",
    "last_success_at", "feed_count", "effective_feed_count", "ok_feed_count",
    "failed_feed_count", "skipped_feed_count", "replaced_feed_count", "undated_count",
    "enabled", "enable_toggle", "disabled_reason", "skip_reason",
    "feed_total", "effective_feed_total", "ok_feeds", "failed_feeds", "skipped_feeds",
    "replaced_feeds", "zero_item_feeds",
}


class DigestInputError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class InputDescriptor:
    name: str
    status: str
    sha256: str | None
    producer_as_of: str | None
    alignment: str


@dataclass(frozen=True)
class Diagnostic:
    code: str
    count: int
    input: str


@dataclass(frozen=True)
class DigestInput:
    records: Archive
    title_cache: dict[str, str]
    health: dict[str, Any] | None
    inputs: tuple[InputDescriptor, ...]
    diagnostics: tuple[Diagnostic, ...]
    fingerprint: str
    captured_bytes: Mapping[str, bytes | None] = field(repr=False)


def _as_of(value: object) -> datetime | None:
    try:
        return parse_published_at(value)
    except DigestTimeError:
        return None


def _health_row(row: dict[str, Any]) -> dict[str, Any]:
    # Drop errors, URLs, credentials and unknown payload fields at this boundary.
    out = {
        k: v for k, v in row.items()
        if k in _HEALTH_FIELDS and isinstance(v, (str, bool, int, float, type(None)))
    }
    children = row.get("subsources")
    if isinstance(children, list):
        out["subsources"] = [_health_row(child) for child in children if isinstance(child, dict)]
    return out


def load_digest_input(input_dir: Path, *, normalize_record: RecordTransform | None = None) -> DigestInput:
    """Missing/bad archive is fatal; optional inputs degrade with diagnostics.

    Default normalization reuses the generator's pure identity policy, imported
    lazily after archive decoding. A supplied policy supports isolated consumers.
    No source coordinator or provider is called, even with credentials present.
    """
    captured: dict[str, bytes | None] = {}
    statuses: dict[str, str] = {}
    payloads: dict[str, Any] = {}
    hashes: dict[str, str | None] = {}
    diagnostics: list[Diagnostic] = []
    for name in INPUT_NAMES:
        try:
            raw = (input_dir / name).read_bytes()
        except FileNotFoundError:
            if name == "archive.json":
                raise DigestInputError("archive_missing") from None
            captured[name], hashes[name], statuses[name] = None, None, "missing"
            diagnostics.append(Diagnostic("optional_missing", 1, name))
            continue
        except OSError:
            if name == "archive.json":
                raise DigestInputError("archive_unreadable") from None
            captured[name], hashes[name], statuses[name] = None, None, "invalid"
            diagnostics.append(Diagnostic("optional_unreadable", 1, name))
            continue
        captured[name] = raw
        hashes[name] = hashlib.sha256(raw).hexdigest()
        try:
            payloads[name] = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError):
            if name == "archive.json":
                raise DigestInputError("archive_invalid") from None
            statuses[name] = "invalid"
            diagnostics.append(Diagnostic("optional_invalid", 1, name))
        else:
            statuses[name] = "loaded"

    if normalize_record is None:
        if __package__:
            from .update_news import normalize_reader_source_identity
        else:
            from update_news import normalize_reader_source_identity
        normalize_record = normalize_reader_source_identity
    try:
        records = archive_from_payload(payloads["archive.json"], normalize_record=normalize_record)
    except ValueError:
        raise DigestInputError("archive_invalid") from None

    cache: dict[str, str] = {}
    cache_name = "title-zh-cache.json"
    if statuses[cache_name] == "loaded":
        payload = payloads[cache_name]
        if not isinstance(payload, dict):
            statuses[cache_name] = "invalid"
            diagnostics.append(Diagnostic("optional_invalid", 1, cache_name))
        else:
            cache = {k: v for k, v in payload.items() if k.strip() and isinstance(v, str) and v.strip()}
            rejected = len(payload) - len(cache)
            if rejected:
                diagnostics.append(Diagnostic("cache_entries_skipped", rejected, cache_name))

    health = None
    health_name = "source-status.json"
    if statuses[health_name] == "loaded":
        payload = payloads[health_name]
        if (not isinstance(payload, dict) or not isinstance(payload.get("generated_at"), str)
                or not isinstance(payload.get("sites"), list)
                or not all(isinstance(row, dict) for row in payload["sites"])):
            statuses[health_name] = "invalid"
            diagnostics.append(Diagnostic("optional_invalid", 1, health_name))
        else:
            health = {"generated_at": payload["generated_at"], "sites": [_health_row(row) for row in payload["sites"]]}
            for provider in ("x_api", "socialdata", "tikhub", "rss_opml"):
                if isinstance(payload.get(provider), dict):
                    health[provider] = _health_row(payload[provider])

    archive_as_of = _as_of(payloads["archive.json"].get("generated_at"))
    health_as_of = _as_of(health.get("generated_at")) if health else None
    alignment = "unverifiable" if archive_as_of is None or health_as_of is None else (
        "matched" if archive_as_of == health_as_of else "mismatched"
    )
    if alignment != "matched":
        diagnostics.append(Diagnostic("health_" + alignment, 1, health_name))
    for name, value in (("archive.json", archive_as_of), (health_name, health_as_of)):
        if statuses[name] == "loaded" and value is None:
            diagnostics.append(Diagnostic("unknown_as_of", 1, name))
    as_of = {"archive.json": archive_as_of, health_name: health_as_of, cache_name: None}
    inputs = tuple(InputDescriptor(
        name, statuses[name], hashes[name],
        as_of[name].isoformat().replace("+00:00", "Z") if as_of[name] else None,
        "unversioned" if name == cache_name else alignment,
    ) for name in INPUT_NAMES)
    material = [[row.name, row.status, row.sha256] for row in inputs]
    fingerprint = hashlib.sha256(json.dumps(material, separators=(",", ":")).encode()).hexdigest()
    return DigestInput(records, cache, health, inputs, tuple(diagnostics), fingerprint, MappingProxyType(captured))
