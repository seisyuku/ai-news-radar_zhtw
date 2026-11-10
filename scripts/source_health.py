"""Source health history and public group diagnostics.

This standard-library module has no generator/source imports or clock reads.
The generator supplies an ISO timestamp and retains public payload sanitization.
See docs/SOURCE_HEALTH.md for identity, skipped and legacy snapshot contracts.
"""

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, Required, TypeVar, TypedDict


SOURCE_PERSISTENT_FAILURE_THRESHOLD = 3
Item = TypeVar("Item")


# Eager annotations preserve Required metadata on Python 3.11.
class HealthHistory(TypedDict, total=False):
    """Known history fields; optional for older snapshots and before calculation."""

    skipped: bool
    attempted: bool
    last_attempt_ok: bool | None
    consecutive_failures: int
    first_failure_at: str | None
    last_failure_at: str | None
    last_success_at: str | None
    last_run_at: str | None
    persistent_failure: bool
    degraded: bool
    degraded_reason: str | None


class SubsourceStatus(HealthHistory, total=False):
    """One stable public child identity, scoped by its containing site."""

    source_id: Required[str]
    ok: bool | None
    item_count: int
    error: str | None
    duration_ms: int


class SiteStatus(HealthHistory, total=False):
    """Whole-source observation; child history is separate from group history."""

    site_id: Required[str]
    site_name: str
    ok: bool | None
    item_count: int
    error: str | None
    subsources: list[SubsourceStatus]


class PersistentFailure(TypedDict, total=False):
    """A new attempted failure at/above threshold; skips never emit this record."""

    site_id: Required[str]
    consecutive_failures: Required[int]
    site_name: str
    source_id: str
    first_failure_at: str | None
    last_failure_at: str | None
    last_success_at: str | None
    error: str | None


def fetch_subsource_with_status(
    source_id: str, fetch: Callable[[], list[Item]],
) -> tuple[list[Item], SubsourceStatus]:
    """Fetch one child; publish only stable error codes, never exception text."""
    try:
        items = fetch()
        return items, {"source_id": source_id, "ok": True, "item_count": len(items), "error": None}
    except Exception as exc:
        error = "invalid_source" if isinstance(exc, ValueError) else "fetch_failed"
        return [], {"source_id": source_id, "ok": False, "item_count": 0, "error": error}


def summarize_subsources(subsources: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe group availability while retaining each child observation."""
    successes = sum(1 for row in subsources if row["ok"])
    failures = len(subsources) - successes
    return {
        "ok": successes > 0,
        "degraded": successes > 0 and failures > 0,
        "degraded_reason": "partial_subsource_failure" if successes > 0 and failures > 0 else None,
        "error": "all_subsources_failed" if successes == 0 else None,
        "subsources": subsources,
    }


def load_source_status(path: Path) -> dict[str, Any]:
    """Treat missing/unreadable/non-object health snapshots as no history."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _apply_attempt_history(
    row: dict[str, Any],
    previous: dict[str, Any],
    now_iso: str,
    threshold: int,
    *,
    outcome: bool | None,
    last_success_at: str | None,
) -> None:
    """Update retained history for success, failure, or a skipped attempt."""
    count = int(previous.get("consecutive_failures") or 0)
    last_ok = previous.get("last_attempt_ok")
    if not isinstance(last_ok, bool):
        # Legacy skipped snapshots can only recover the last actual outcome
        # from a retained streak or a recorded success.
        if previous.get("skipped"):
            last_ok = False if count else (True if previous.get("last_success_at") else None)
        else:
            last_ok = previous.get("ok") if isinstance(previous.get("ok"), bool) else None

    first_failure_at = previous.get("first_failure_at")
    last_failure_at = previous.get("last_failure_at")
    if outcome is None:
        if isinstance(row.get("last_attempt_ok"), bool):
            last_ok = row["last_attempt_ok"]
        if last_ok is False:
            count = count or 1
        last_failure_at = last_failure_at or (row.get("last_run_at") if last_ok is False else None)
        first_failure_at = first_failure_at or (last_failure_at if last_ok is False else None)
    elif outcome:
        last_ok = True
        count = 0
        first_failure_at = None
        last_success_at = now_iso
    else:
        if last_ok is False:
            count = (count or 1) + 1
            first_failure_at = first_failure_at or now_iso
        else:
            count = 1
            first_failure_at = now_iso
        last_ok = False
        last_failure_at = now_iso

    row["last_attempt_ok"] = last_ok
    row["consecutive_failures"] = count
    row["first_failure_at"] = first_failure_at
    row["last_failure_at"] = last_failure_at
    row["last_success_at"] = last_success_at
    row["persistent_failure"] = last_ok is False and count >= max(1, threshold)


def apply_subsource_health_history(
    status: dict[str, Any],
    previous: dict[str, Any],
    now_iso: str,
    threshold: int,
    persistent_failures: list[PersistentFailure],
) -> bool:
    """Carry only exact (site_id, source_id) matches across runs."""
    subsources = status.get("subsources")
    if not isinstance(subsources, list):
        return False
    previous_rows = previous.get("subsources")
    previous_subsources = {
        str(row.get("source_id")): row
        for row in (previous_rows if isinstance(previous_rows, list) else [])
        if isinstance(row, dict) and row.get("source_id")
    }
    if status.get("skipped") and not subsources:
        # A group skip has no current fetch rows. Preserve the known children
        # as explicitly skipped observations instead of dropping their streaks.
        subsources.extend(
            {"source_id": source_id, "ok": None, "item_count": 0, "error": None}
            for source_id in previous_subsources
        )

    for row in subsources:
        if not isinstance(row, dict) or not row.get("source_id"):
            continue
        source_id = str(row["source_id"])
        old = previous_subsources.get(source_id, {})
        skipped = bool(status.get("skipped") or row.get("skipped"))
        row["skipped"] = skipped
        row["attempted"] = not skipped
        last_success_at = old.get("last_success_at")
        if skipped:
            row["duration_ms"] = 0
            row["ok"] = None
            row["item_count"] = 0
            row["error"] = None
            last_success_at = row.get("last_success_at") or last_success_at
        _apply_attempt_history(
            row, old, now_iso, threshold, outcome=None if skipped else row.get("ok") is True,
            last_success_at=last_success_at,
        )
        if skipped:
            if row["last_attempt_ok"] is False:
                row["degraded"] = True
                row["degraded_reason"] = "last_attempt_failed_waiting_for_retry"
                status["degraded"] = True
                status["degraded_reason"] = "last_subsource_failure_waiting_for_retry"
            continue
        if row["persistent_failure"]:
            persistent_failures.append({
                "site_id": status["site_id"],
                "site_name": status.get("site_name") or status["site_id"],
                "source_id": source_id,
                "consecutive_failures": row["consecutive_failures"],
                "first_failure_at": row["first_failure_at"],
                "last_failure_at": now_iso,
                "last_success_at": row["last_success_at"],
                "error": row.get("error"),
            })
    return bool(subsources)


def apply_source_health_history(
    statuses: list[dict[str, Any]],
    previous_status: dict[str, Any] | None,
    now_iso: str,
    *,
    threshold: int = SOURCE_PERSISTENT_FAILURE_THRESHOLD,
) -> list[PersistentFailure]:
    """Carry source failure streaks across generated source-status snapshots."""
    previous_sites = {
        str(item.get("site_id") or ""): item
        for item in (previous_status or {}).get("sites", [])
        if isinstance(item, dict) and item.get("site_id")
    }
    persistent_failures: list[PersistentFailure] = []

    for status in statuses:
        site_id = str(status.get("site_id") or "")
        previous = previous_sites.get(site_id, {})
        has_subsources = apply_subsource_health_history(
            status, previous, now_iso, threshold, persistent_failures,
        )
        skipped = bool(status.get("skipped"))
        _apply_attempt_history(
            status, previous, now_iso, threshold, outcome=None if skipped else bool(status.get("ok")),
            last_success_at=status.get("last_success_at") or previous.get("last_success_at"),
        )
        if skipped:
            if status["last_attempt_ok"] is False:
                status["degraded"] = True
                status["degraded_reason"] = "last_attempt_failed_waiting_for_retry"
            continue
        if status["persistent_failure"] and not has_subsources:
            persistent_failures.append(
                {
                    "site_id": site_id,
                    "site_name": status.get("site_name") or site_id,
                    "consecutive_failures": status["consecutive_failures"],
                    "first_failure_at": status["first_failure_at"],
                    "last_failure_at": now_iso,
                    "last_success_at": status.get("last_success_at"),
                    "error": status.get("error"),
                }
            )
    return persistent_failures


def report_persistent_source_failures(persistent_failures: list[PersistentFailure]) -> None:
    if not persistent_failures:
        return
    for failure in persistent_failures:
        source_label = failure["site_id"] + (
            "/" + str(failure["source_id"]) if failure.get("source_id") else ""
        )
        annotation_error = (
            str(failure.get("error") or "unknown error")
            .replace("%", "%25")
            .replace("\r", "%0D")
            .replace("\n", "%0A")
        )
        print(
            "::warning file=data/source-status.json,title=Persistent source failure::"
            f"{source_label} failed {failure['consecutive_failures']} consecutive runs: "
            f"{annotation_error}"
        )

    summary_path = str(os.environ.get("GITHUB_STEP_SUMMARY") or "").strip()
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write("\n### Persistent source failures\n\n")
        summary.write("| Source | Consecutive failures | Since | Error |\n")
        summary.write("| --- | ---: | --- | --- |\n")
        for failure in persistent_failures:
            source_label = failure["site_id"] + (
                "/" + str(failure["source_id"]) if failure.get("source_id") else ""
            )
            error = str(failure.get("error") or "unknown error").replace("|", "\\|").replace("\n", " ")
            summary.write(
                f"| {source_label} | {failure['consecutive_failures']} | "
                f"{failure.get('first_failure_at') or 'unknown'} | {error} |\n"
            )
