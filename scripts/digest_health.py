"""Pure, bounded digest health metadata; never replay history or expose labels.

Group counts and child counts describe different observation levels. Neither
is a historical coverage measure or a unique-article/fetched-raw total.
"""

from dataclasses import dataclass

if __package__:
    from .digest_input import DigestInput
    from .digest_window import DigestTimeError, DigestWindow, parse_published_at
else:
    from digest_input import DigestInput
    from digest_window import DigestTimeError, DigestWindow, parse_published_at


STATES = ("successful", "healthy_zero", "failed", "partial", "skipped", "disabled", "unknown")
PROVIDERS = ("x_api", "socialdata", "tikhub", "rss_opml")


@dataclass(frozen=True)
class RoundHealth:
    site_counts: dict[str, int]
    child_counts: dict[str, int]
    groups_with_children: int
    provider_states: dict[str, str]


@dataclass(frozen=True)
class DigestHealth:
    archive_as_of: str | None
    health_as_of: str | None
    health_status: str
    alignment: str
    input_before_cutoff: bool | None
    current_round: RoundHealth | None
    notices: tuple[str, ...]


def _timestamp(value):
    try:
        return parse_published_at(value)
    except DigestTimeError:
        return None


def _wire(value):
    return value.isoformat().replace("+00:00", "Z") if value is not None else None


def _count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _availability(row):
    if row.get("disabled") is True or row.get("enabled") is False:
        return "disabled"
    if row.get("skipped") is True:
        return "skipped"
    return None


def _state(row, forced=None):
    availability = forced or _availability(row)
    if availability:
        return availability
    if row.get("attempted") is False:
        return "unknown"
    if row.get("ok") is False:
        return "failed"
    if row.get("ok") is not True:
        return "unknown"
    children = row.get("subsources")
    child_failure = any(_state(child) in {"failed", "partial"}
                        for child in children if isinstance(child, dict)) if isinstance(children, list) else False
    if (row.get("degraded") is True or (_count(row.get("partial_failures")) or 0) > 0
            or child_failure):
        return "partial"
    return "healthy_zero" if _count(row.get("item_count")) == 0 else "successful"


def summarize_digest_health(snapshot: DigestInput, window: DigestWindow) -> DigestHealth:
    """Use descriptor as-of evidence, not mtime, wall clock or history fields.

    Only matched loaded health yields round statistics. Provider metadata is
    availability only and is not counted again as a site. Output contains no
    caller-supplied IDs, names, reasons, errors or paths. Notices are safe codes
    for D08 to map to controlled reader text; input diagnostics remain separate.
    """
    descriptors = {row.name: row for row in snapshot.inputs}
    archive = descriptors.get("archive.json")
    health = descriptors.get("source-status.json")
    archive_time = _timestamp(archive.producer_as_of) if archive else None
    health_time = _timestamp(health.producer_as_of) if health else None
    status = health.status if health and health.status in {"loaded", "missing", "invalid"} else "invalid"
    alignment = "unverifiable" if archive_time is None or health_time is None else (
        "matched" if archive_time == health_time else "mismatched"
    )
    before_cutoff = archive_time < window.end_utc if archive_time is not None else None
    notices = ["health_not_window_coverage", "archive_not_new_fetch"]
    if before_cutoff is True:
        notices.append("input_before_cutoff")
    elif before_cutoff is None:
        notices.append("archive_as_of_unknown")
    current = None
    payload = snapshot.health
    if status != "loaded":
        notices.append("health_" + status)
    elif alignment != "matched":
        notices.append("health_" + alignment)
    elif not isinstance(payload, dict) or not isinstance(payload.get("sites"), list):
        notices.append("health_shape_unknown")
    else:
        site_counts = dict.fromkeys(STATES, 0)
        child_counts = dict.fromkeys(STATES, 0)
        groups = 0
        for row in payload["sites"]:
            if not isinstance(row, dict):
                site_counts["unknown"] += 1
                continue
            site_counts[_state(row)] += 1
            children = row.get("subsources")
            if isinstance(children, list) and children:
                groups += 1
                for child in children:
                    forced = _availability(row) or ("unknown" if row.get("attempted") is False else None)
                    child_counts[_state(child, forced) if isinstance(child, dict) else "unknown"] += 1
        providers = {}
        for key in PROVIDERS:
            row = payload.get(key)
            providers[key] = (_availability(row) or ("enabled" if row.get("enabled") is True else "unknown")) if isinstance(row, dict) else "unknown"
        current = RoundHealth(site_counts, child_counts, groups, providers)
        if site_counts["failed"] or site_counts["partial"]:
            notices.append("source_failures")
        if site_counts["unknown"] or child_counts["unknown"]:
            notices.append("source_status_unknown")
    return DigestHealth(_wire(archive_time), _wire(health_time), status, alignment,
                        before_cutoff, current, tuple(notices))
