"""D07: as-of alignment, observation levels, and safe metadata."""

from copy import deepcopy
from dataclasses import asdict
import json
from types import MappingProxyType

import pytest

from scripts.digest_health import summarize_digest_health
from scripts.digest_input import DigestInput, InputDescriptor, load_digest_input
from scripts.digest_window import window_for_date


AS_OF = "2026-10-01T22:00:00Z"
WINDOW = window_for_date("2026-10-02")


def snapshot(sites=(), *, archive_as_of=AS_OF, health_as_of=AS_OF, status="loaded", **providers):
    return DigestInput({"retained": {"id": "retained"}}, {},
                       {"sites": list(sites), **providers} if status == "loaded" else None,
                       (InputDescriptor("archive.json", "loaded", "a", archive_as_of, "unverifiable"),
                        InputDescriptor("source-status.json", status, "h", health_as_of, "unverifiable")),
                       (), "fingerprint", MappingProxyType({}))


@pytest.mark.parametrize("row,state", [
    ({"ok": True, "item_count": 2}, "successful"),
    ({"ok": True, "item_count": 0}, "healthy_zero"),
    ({"ok": False, "item_count": 0}, "failed"),
    ({"ok": True, "degraded": True, "item_count": 0}, "partial"),
    ({"ok": True, "partial_failures": 2}, "partial"),
    ({"ok": True, "skipped": True, "persistent_failure": True}, "skipped"),
    ({"ok": False, "enabled": False, "skipped": True}, "disabled"),
    ({"ok": True, "disabled": True}, "disabled"),
    ({"ok": True, "attempted": False}, "unknown"),
    ({"ok": None, "last_attempt_ok": True}, "unknown"),
    ({"ok": "true"}, "unknown"),
    ({}, "unknown"),
])
def test_states_are_current_observations_not_history(row, state):
    result = summarize_digest_health(snapshot([row]), WINDOW)
    assert result.current_round.site_counts[state] == 1
    assert sum(result.current_round.site_counts.values()) == 1


@pytest.mark.parametrize("count", [None, -1, True, 0.0, "0", float("nan")])
def test_bad_counts_are_not_healthy_zero(count):
    result = summarize_digest_health(snapshot([{"ok": True, "item_count": count}]), WINDOW)
    assert result.current_round.site_counts["successful"] == 1
    assert result.current_round.site_counts["healthy_zero"] == 0


def test_partial_group_and_children_never_mix_totals():
    group = {"ok": True, "item_count": 2, "subsources": [
        {"ok": True, "item_count": 2}, {"ok": True, "item_count": 0}, {"ok": False, "item_count": 0}]}
    result = summarize_digest_health(snapshot([group, {"ok": False}]), WINDOW).current_round
    assert result.groups_with_children == 1
    assert result.site_counts["partial"] == 1 and result.site_counts["failed"] == 1
    assert sum(result.site_counts.values()) == 2
    assert sum(result.child_counts.values()) == 3
    assert result.child_counts["successful"] == result.child_counts["healthy_zero"] == result.child_counts["failed"] == 1


@pytest.mark.parametrize("parent,state", [({"skipped": True}, "skipped"),
                                          ({"enabled": False}, "disabled"),
                                          ({"attempted": False}, "unknown")])
def test_unattempted_parent_does_not_replay_child_success(parent, state):
    row = {"ok": True, "subsources": [{"ok": True, "item_count": 0}], **parent}
    result = summarize_digest_health(snapshot([row]), WINDOW).current_round
    assert result.site_counts[state] == result.child_counts[state] == 1


def test_all_failed_archive_content_is_retained_not_new_fetch():
    original = snapshot([{"ok": False, "item_count": 0}])
    result = summarize_digest_health(original, WINDOW)
    assert result.current_round.site_counts["failed"] == 1
    assert result.current_round.site_counts["healthy_zero"] == 0
    assert "archive_not_new_fetch" in result.notices
    assert "source_failures" in result.notices
    assert original.records == {"retained": {"id": "retained"}}


@pytest.mark.parametrize("archive,health,alignment", [
    (AS_OF, "2026-10-01T21:00:00Z", "mismatched"),
    (None, AS_OF, "unverifiable"), (AS_OF, None, "unverifiable"),
    ("bad private timestamp", AS_OF, "unverifiable"),
])
def test_unaligned_health_omits_all_current_round_counts(archive, health, alignment):
    result = summarize_digest_health(snapshot([{"ok": False}], archive_as_of=archive, health_as_of=health), WINDOW)
    assert result.alignment == alignment and result.current_round is None
    assert "health_" + alignment in result.notices
    assert "private" not in json.dumps(asdict(result))


@pytest.mark.parametrize("status", ["missing", "invalid"])
def test_optional_health_degrades_without_fake_success_or_failure(status):
    result = summarize_digest_health(snapshot(status=status, health_as_of=None), WINDOW)
    assert result.current_round is None and result.health_status == status
    assert "health_" + status in result.notices


@pytest.mark.parametrize("time,before", [
    ("2026-10-01T21:59:59Z", True), (AS_OF, False), ("2026-10-02T03:00:00Z", False), (None, None),
])
def test_cutoff_is_a_notice_not_an_extra_window_rule(time, before):
    result = summarize_digest_health(snapshot(archive_as_of=time, health_as_of=time), WINDOW)
    assert result.input_before_cutoff is before
    assert ("input_before_cutoff" in result.notices) is (before is True)
    assert WINDOW == window_for_date("2026-10-02")


def test_equivalent_offsets_match_and_normalize():
    result = summarize_digest_health(snapshot(health_as_of="2026-10-02T06:00:00+08:00"), WINDOW)
    assert result.alignment == "matched"
    assert result.archive_as_of == result.health_as_of == AS_OF


def test_provider_availability_is_separate_and_never_counted_twice():
    result = summarize_digest_health(snapshot([{"ok": True, "item_count": 0}],
        x_api={"enabled": False}, socialdata={"enabled": True, "skipped": True},
        tikhub={"enabled": True, "ok": False}), WINDOW).current_round
    assert result.provider_states == {"x_api": "disabled", "socialdata": "skipped", "tikhub": "enabled", "rss_opml": "unknown"}
    assert sum(result.site_counts.values()) == 1


def test_empty_health_is_not_all_success_and_shape_errors_are_unknown():
    result = summarize_digest_health(snapshot(), WINDOW)
    assert sum(result.current_round.site_counts.values()) == 0
    assert "health_not_window_coverage" in result.notices
    original = snapshot()
    original.health["sites"] = None
    result = summarize_digest_health(original, WINDOW)
    assert result.current_round is None and "health_shape_unknown" in result.notices


def test_safe_owned_deterministic_output_and_unknown_rows():
    original = snapshot([{"ok": True, "site_id": "private@example.com", "site_name": "/secret/path", "error": "token", "subsources": [None]}, None],
                        x_api={"enabled": False, "disabled_reason": "secret"})
    before = deepcopy(original.health)
    first = summarize_digest_health(original, WINDOW)
    second = summarize_digest_health(original, WINDOW)
    assert first == second and original.health == before
    encoded = json.dumps(asdict(first), allow_nan=False)
    assert not any(s in encoded for s in ("private@", "/secret", "token", '"secret"'))
    first.current_round.site_counts["failed"] = 100
    assert second.current_round.site_counts["failed"] == 0
    assert second.current_round.child_counts["unknown"] == 1
    assert second.current_round.site_counts["unknown"] == 1


def test_actual_loader_boundary_no_network_or_write(tmp_path, monkeypatch):
    (tmp_path / "archive.json").write_text(json.dumps({"items": [], "generated_at": AS_OF}))
    (tmp_path / "source-status.json").write_text(json.dumps({"generated_at": AS_OF, "sites": [
        {"site_id": "opmlrss", "ok": True, "item_count": 0, "partial_failures": 1}],
        "rss_opml": {"enabled": False, "path": "/private/feed"}}))
    original = load_digest_input(tmp_path, normalize_record=dict)
    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected side effect")
    import requests
    monkeypatch.setattr(requests.Session, "request", forbidden)
    monkeypatch.setattr(type(tmp_path), "read_bytes", forbidden)
    monkeypatch.setattr(type(tmp_path), "write_text", forbidden)
    result = summarize_digest_health(original, WINDOW)
    assert result.current_round.site_counts["partial"] == 1
    assert result.current_round.provider_states["rss_opml"] == "disabled"
    assert "private" not in json.dumps(asdict(result))
