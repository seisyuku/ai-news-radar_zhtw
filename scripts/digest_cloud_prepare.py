"""C03 offline preparation. A trusted intent and pinned bytes are injected; no fetch."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from typing import Callable, Mapping
from uuid import UUID

from .digest_document import build_digest_document
from .digest_input import INPUT_NAMES, load_digest_input
from .digest_window import DigestTimeError, TAIPEI, window_for_date
from .generate_digest import verify_digest_pair, write_digest


_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z\Z")
_SLOTS = {(7, 15), (8, 15), (8, 45)}
_MAX_INPUT = 64 * 1024 * 1024


class PreparationError(ValueError):
    """Only a safe fixed code is exposed, never input or exception text."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class PinnedInputs:
    source_commit: str
    content: Mapping[str, bytes | None]
    sha256: Mapping[str, str | None]
    source_commits: Mapping[str, str]


@dataclass(frozen=True)
class PreparedPair:
    issue_date: str
    mode: str
    request_id: str
    scheduled_for: str | None
    issued_at: str
    issuer_id: str
    started_at: str
    source_commit: str
    input_sha256: Mapping[str, str | None]
    base_identity: str
    markdown: bytes
    metadata: bytes
    markdown_sha256: str
    metadata_sha256: str
    archive_as_of: str | None
    selected_count: int
    diagnostic_codes: tuple[str, ...]
    prepared_at: str
    pair_verified: bool
    rerun_identical: bool


def _bad(code="invalid_request"):
    raise PreparationError(code)


def _timestamp(value):
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        _bad()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _bad()


def _clock(clock):
    value = clock()
    if not isinstance(value, datetime) or value.utcoffset() is None:
        _bad()
    return value.astimezone(timezone.utc)


def _uuid(value):
    if not isinstance(value, str):
        _bad()
    try:
        if str(UUID(value)) != value:
            _bad()
    except ValueError:
        _bad()


def _validate_intent(intent, now, trusted_issuer_ids):
    keys = {"schema_version", "request_id", "issue_date", "mode", "scheduled_for",
            "issued_at", "issuer_id", "owner_authorized"}
    if not isinstance(intent, Mapping) or set(intent) != keys or type(intent["schema_version"]) is not int or intent["schema_version"] != 1:
        _bad()
    if (not isinstance(trusted_issuer_ids, frozenset) or
            not isinstance(intent["issuer_id"], str) or
            intent["issuer_id"] not in trusted_issuer_ids):
        _bad("unauthorized")
    _uuid(intent["request_id"])
    if not isinstance(intent["issue_date"], str):
        _bad()
    try:
        window = window_for_date(intent["issue_date"])
    except DigestTimeError:
        _bad()
    issued = _timestamp(intent["issued_at"])
    mode = intent["mode"]
    if type(intent["owner_authorized"]) is not bool:
        _bad()
    if mode == "scheduled":
        if intent["owner_authorized"] or intent["scheduled_for"] is None:
            _bad()
        scheduled = _timestamp(intent["scheduled_for"])
        local = scheduled.astimezone(TAIPEI)
        if (local.date().isoformat() != window.date or (local.hour, local.minute) not in _SLOTS
                or local.second or local.microsecond or not scheduled <= issued <= scheduled + timedelta(minutes=15)
                or issued > now):
            _bad()
    elif mode in {"manual_current", "manual_historical"}:
        if intent["scheduled_for"] is not None or not intent["owner_authorized"]:
            _bad("unauthorized")
        today = now.astimezone(TAIPEI).date().isoformat()
        if (mode == "manual_current" and window.date != today or
                mode == "manual_historical" and window.date >= today):
            _bad()
        if issued > now:
            _bad()
    else:
        _bad()
    if mode != "manual_historical" and now.astimezone(TAIPEI).date().isoformat() != window.date:
        _bad("missed_issue")
    return window


def _validate_pins(pinned):
    names = set(INPUT_NAMES)
    if (not isinstance(pinned, PinnedInputs) or not isinstance(pinned.source_commit, str)
            or not _COMMIT.fullmatch(pinned.source_commit) or set(pinned.content) != names
            or set(pinned.sha256) != names or set(pinned.source_commits) != names):
        _bad()
    if pinned.content["archive.json"] is None:
        _bad("generation_failed")
    for name in INPUT_NAMES:
        value = pinned.content[name]
        digest = pinned.sha256[name]
        if pinned.source_commits[name] != pinned.source_commit:
            _bad()
        if value is None:
            if digest is not None:
                _bad()
        elif (not isinstance(value, bytes) or len(value) > _MAX_INPUT or not isinstance(digest, str)
              or not _SHA.fullmatch(digest) or hashlib.sha256(value).hexdigest() != digest):
            _bad()


def _workspace_root(workspace):
    base = Path(workspace).resolve()
    downloads = (Path.home() / "Downloads").resolve()
    if downloads not in base.parents:
        _bad()
    return base


def prepare_generation(intent: Mapping, pinned_inputs: PinnedInputs, clock: Callable[[], datetime],
                       workspace: Path, *, trusted_issuer_ids: frozenset[str]) -> PreparedPair:
    """Prepare verified bytes for C04; neither freshness nor delivery is decided here.

    `intent` must have been retrieved by request_id from the trusted intent source.
    The caller configures allowed issuer IDs; C03 cannot authenticate a real issuer.
    """
    now = _clock(clock)
    window = _validate_intent(intent, now, trusted_issuer_ids)
    _validate_pins(pinned_inputs)
    base = _workspace_root(workspace)
    try:
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
        with TemporaryDirectory(prefix="c03-", dir=base) as scratch:
            root = Path(scratch)
            source = root / "inputs"
            source.mkdir(mode=0o700)
            for name in INPUT_NAMES:
                raw = pinned_inputs.content[name]
                if raw is not None:
                    path = source / name
                    path.write_bytes(raw)
                    path.chmod(0o600)
            snapshot = load_digest_input(source)
            first = build_digest_document(snapshot, window)
            if first["selection_counts"]["selected_count"] > 20:
                _bad("payload_limit")
            md, meta = write_digest(first, root / "first")
            verified = verify_digest_pair(md, meta)
            repeated = build_digest_document(load_digest_input(source), window)
            md2, meta2 = write_digest(repeated, root / "repeat")
            original = (md.read_bytes(), meta.read_bytes())
            if original != (md2.read_bytes(), meta2.read_bytes()):
                _bad("generation_failed")
            if verified["input_identity"] != first["input_identity"]:
                _bad("generation_failed")
            for candidate in verified["candidates"]:
                title = candidate["title"]
                summary = candidate["summary"]
                if (title is not None and len(title) > 4096 or
                        summary is not None and len(summary) > 32768):
                    _bad("payload_limit")
            completed = _clock(clock)
            if intent["mode"] != "manual_historical" and completed.astimezone(TAIPEI).date().isoformat() != window.date:
                _bad("missed_issue")
            return PreparedPair(
                issue_date=window.date, mode=intent["mode"], request_id=intent["request_id"],
                scheduled_for=intent["scheduled_for"], issued_at=intent["issued_at"],
                issuer_id=intent["issuer_id"], started_at=now.isoformat().replace("+00:00", "Z"),
                source_commit=pinned_inputs.source_commit, input_sha256=dict(pinned_inputs.sha256),
                base_identity=first["input_identity"], markdown=original[0], metadata=original[1],
                markdown_sha256=hashlib.sha256(original[0]).hexdigest(),
                metadata_sha256=hashlib.sha256(original[1]).hexdigest(),
                archive_as_of=snapshot.inputs[0].producer_as_of,
                selected_count=verified["selection_counts"]["selected_count"],
                diagnostic_codes=tuple(row.code for row in snapshot.diagnostics),
                prepared_at=completed.isoformat().replace("+00:00", "Z"),
                pair_verified=True, rerun_identical=True)
    except PreparationError:
        raise
    except Exception:
        raise PreparationError("generation_failed") from None
