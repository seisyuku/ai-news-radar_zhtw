"""Calendar-day digest windows; independent of reader windows and fetching.

Wire timestamps use calendar ISO dates, T/space, hour:minute with optional
seconds (up to six fractional digits), and Z or a numeric timezone offset.
Invalid/missing timestamps raise a coded error rather than inventing UTC.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import re
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")
UTC = timezone.utc
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_LOCAL_TIMESTAMP = (
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ]"
    r"[0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]{1,6})?)?"
)
_AWARE_TIMESTAMP = re.compile(
    _LOCAL_TIMESTAMP + r"(?:Z|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])"
)


class DigestTimeError(ValueError):
    """A safe diagnostic code; never includes the rejected source value."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class DigestWindow:
    date: str
    timezone: str
    start_utc: datetime
    end_utc: datetime

    def contains(self, published_at: datetime) -> bool:
        """Start inclusive, end exclusive; naive values are never accepted."""
        if not isinstance(published_at, datetime) or published_at.utcoffset() is None:
            raise DigestTimeError("naive_timestamp")
        return self.start_utc <= published_at < self.end_utc


def parse_published_at(value: object) -> datetime:
    """Parse a wire timestamp to UTC, with no first-seen or clock fallback.

    Codes: missing_timestamp, date_only, naive_timestamp, invalid_timestamp.
    Callers count/exclude rejected records; this module knows no record fields.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise DigestTimeError("missing_timestamp")
    if not isinstance(value, str):
        raise DigestTimeError("invalid_timestamp")
    if _DATE.fullmatch(value):
        try:
            date.fromisoformat(value)
        except ValueError:
            raise DigestTimeError("invalid_timestamp") from None
        raise DigestTimeError("date_only")
    if re.fullmatch(_LOCAL_TIMESTAMP, value):
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise DigestTimeError("invalid_timestamp") from None
        raise DigestTimeError("naive_timestamp")
    if not _AWARE_TIMESTAMP.fullmatch(value):
        raise DigestTimeError("invalid_timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, OverflowError):
        raise DigestTimeError("invalid_timestamp") from None


def window_for_date(value: str | None = None, *, now: datetime | None = None) -> DigestWindow:
    """Resolve one Taipei date and its preceding 06:00-to-06:00 window.

    Explicit dates are pure and ignore now. For a default date, capture the
    clock once (or inject an aware now); before 06:00 does not shift the issue.
    """
    if value is None:
        captured = datetime.now(UTC) if now is None else now
        if not isinstance(captured, datetime) or captured.utcoffset() is None:
            raise DigestTimeError("invalid_now")
        issue_date = captured.astimezone(TAIPEI).date()
    else:
        if not isinstance(value, str) or not _DATE.fullmatch(value):
            raise DigestTimeError("invalid_date")
        try:
            issue_date = date.fromisoformat(value)
        except ValueError:
            raise DigestTimeError("invalid_date") from None
    try:
        previous_date = issue_date - timedelta(days=1)
        start_utc = datetime.combine(previous_date, time(6), TAIPEI).astimezone(UTC)
        end_utc = datetime.combine(issue_date, time(6), TAIPEI).astimezone(UTC)
    except OverflowError:
        raise DigestTimeError("invalid_date") from None
    return DigestWindow(
        date=issue_date.isoformat(),
        timezone="Asia/Taipei",
        start_utc=start_utc,
        end_utc=end_utc,
    )
