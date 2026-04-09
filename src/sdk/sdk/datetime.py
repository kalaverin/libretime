from datetime import datetime, time
from re import match

from dateutil import parser

from sdk.compat import UTC


class TimezoneExpectedError(TypeError): ...


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 string with seconds precision.

    The datetime is converted to UTC and formatted with 'Z' suffix
    instead of '+00:00' for cleaner representation.

    Args:
        dt: The datetime with timezone to format.

    Returns:
        The formatted datetime string: 2026-03-26T12:14:56Z

    Raises:
        ValueError: If the datetime is not timezone-aware.

    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2026, 3, 26, 12, 14, 56, tzinfo=UTC)
        >>> format_datetime(dt)
        '2026-03-26T12:14:56Z'
    """

    # timezone-aware datetimes are required for unambiguous formatting
    if not dt.tzinfo:
        raise TimezoneExpectedError("Datetime must be timezone-aware")

    # always convert taken datetime to UTC
    result = dt.astimezone(UTC).isoformat(timespec="seconds")

    # and format with 'Z' suffix
    if m := match(r"^(.+?)(\+00:00$)", result):
        return f"{m.group(1)}Z"

    # if we got here, something went wrong with formatting
    msg = f"Unexpected datetime format: {result}"
    raise ValueError(msg)


def reformat_datetime(dt: str) -> str:
    """Parse datetime string from API and format it -
    triggers TimezoneExpectedError if naive.
    """
    return format_datetime(parser.parse(dt))


def time_in_seconds(value: time) -> float:
    return (
        value.hour * 60 * 60
        + value.minute * 60
        + value.second
        + value.microsecond / 1000000.0
    )


def time_in_milliseconds(value: time) -> float:
    return time_in_seconds(value) * 1000


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        raise ValueError

    return dt.replace(tzinfo=UTC)


def to_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError

    return dt.astimezone(UTC).replace(tzinfo=None)


def now() -> datetime:
    return datetime.now(UTC)
