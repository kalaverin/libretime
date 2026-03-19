from datetime import datetime, time, timezone


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

    return dt.replace(tzinfo=timezone.utc)


def to_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError

    return dt.astimezone(timezone.utc).replace(tzinfo=None)
