"""F01-F04: issue boundaries and timestamps must not follow fetch time."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.digest_window import DigestTimeError, parse_published_at, window_for_date


@pytest.mark.parametrize("timestamp,included", [
    ("2026-10-01T05:59:59+08:00", False),
    ("2026-10-01T06:00:00+08:00", True),
    ("2026-10-02T05:59:59.999999+08:00", True),
    ("2026-10-02T06:00:00+08:00", False),
])
def test_issue_uses_half_open_publish_window(timestamp, included):
    window = window_for_date("2026-10-02")
    assert window.contains(parse_published_at(timestamp)) is included
    assert window.start_utc == datetime(2026, 9, 30, 22, tzinfo=timezone.utc)
    assert window.end_utc == datetime(2026, 10, 1, 22, tzinfo=timezone.utc)


@pytest.mark.parametrize("timestamp", [
    "2026-09-30T22:00:00Z",
    "2026-10-01T06:00:00+08:00",
    "2026-09-30T18:00:00-04:00",
    "2026-10-01 06:00+0800",
])
def test_offsets_represent_same_instant(timestamp):
    parsed = parse_published_at(timestamp)
    assert parsed == datetime(2026, 9, 30, 22, tzinfo=timezone.utc)
    assert parsed.tzinfo is timezone.utc
    assert window_for_date("2026-10-02").contains(parsed)


@pytest.mark.parametrize("issue,start,end", [
    ("2027-01-01", "2026-12-30T22:00:00Z", "2026-12-31T22:00:00Z"),
    ("2024-02-29", "2024-02-27T22:00:00Z", "2024-02-28T22:00:00Z"),
    ("2024-03-01", "2024-02-28T22:00:00Z", "2024-02-29T22:00:00Z"),
])
def test_calendar_rollovers(issue, start, end):
    window = window_for_date(issue)
    assert window.start_utc == parse_published_at(start)
    assert window.end_utc == parse_published_at(end)
    assert window.end_utc - window.start_utc == timedelta(hours=24)


@pytest.mark.parametrize("value", [
    "", "20261002", "2026-1-02", "2026-10-2", "2026-02-29", "2026-13-01",
    "2026-10-02T06:00:00Z", " 2026-10-02", "2026-10-02\n", "0001-01-01", "0001-01-02", 20261002,
])
def test_bad_issue_dates_fail(value):
    with pytest.raises(DigestTimeError) as error:
        window_for_date(value)
    assert error.value.code == "invalid_date"


@pytest.mark.parametrize("now,expected", [
    ("2026-10-01T16:00:00Z", "2026-10-02"),
    ("2026-10-01T21:59:59Z", "2026-10-02"),
    ("2026-10-01T22:00:00Z", "2026-10-02"),
    ("2026-10-02T15:59:59Z", "2026-10-02"),
    ("2026-10-02T16:00:00Z", "2026-10-03"),
])
def test_default_date_is_taipei_day_even_before_cutoff(now, expected):
    assert window_for_date(now=parse_published_at(now)).date == expected


def test_explicit_date_is_independent_of_clock():
    assert window_for_date("2026-10-02", now=datetime(2030, 1, 1)) == window_for_date("2026-10-02")


def test_default_date_rejects_naive_clock():
    with pytest.raises(DigestTimeError, match="invalid_now"):
        window_for_date(now=datetime(2026, 10, 2))


def test_default_captures_clock_once(monkeypatch):
    from scripts import digest_window

    class Clock(datetime):
        calls = 0

        @classmethod
        def now(cls, tz):
            cls.calls += 1
            return cls(2026, 10, 1, 21, 59, 59, tzinfo=tz)

    monkeypatch.setattr(digest_window, "datetime", Clock)
    assert digest_window.window_for_date().date == "2026-10-02"
    assert Clock.calls == 1


@pytest.mark.parametrize("value,code", [
    (None, "missing_timestamp"), ("", "missing_timestamp"), ("  ", "missing_timestamp"),
    ("2026-10-01", "date_only"),
    ("2026-10-01T06:00:00", "naive_timestamp"),
    ("2026-10-01 06:00", "naive_timestamp"),
    ("2026-02-30", "invalid_timestamp"),
    ("2026-02-30T06:00:00", "invalid_timestamp"),
    ("bad", "invalid_timestamp"), (12, "invalid_timestamp"), ({}, "invalid_timestamp"),
    ("2026-10-01T24:00:00Z", "invalid_timestamp"),
    ("2026-10-01T06:00:00+08:99", "invalid_timestamp"),
    ("2026-10-01T06:00:00+24:00", "invalid_timestamp"),
    ("2026-10-01T06:00:00+08", "invalid_timestamp"),
    ("2026-10-01T06:00:00Z\n", "invalid_timestamp"),
])
def test_rejected_publish_times_have_diagnostic_codes(value, code):
    with pytest.raises(DigestTimeError) as error:
        parse_published_at(value)
    assert error.value.code == code
    assert str(error.value) == code


def test_window_cannot_be_mutated_or_accept_naive_publish_time():
    window = window_for_date("2026-10-02")
    with pytest.raises(FrozenInstanceError):
        window.date = "2026-10-03"
    with pytest.raises(DigestTimeError, match="naive_timestamp"):
        window.contains(datetime(2026, 10, 1, 6))


def test_import_is_independent_of_generator_and_network_stack():
    script = """
import importlib.abc
import sys
class RejectDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'scripts.update_news', 'update_news', 'requests', 'bs4', 'dateutil'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, RejectDependencies())
from scripts.digest_window import window_for_date, parse_published_at
assert window_for_date('2026-10-02').contains(parse_published_at('2026-09-30T22:00:00Z'))
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
