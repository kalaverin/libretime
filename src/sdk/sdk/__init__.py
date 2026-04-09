from importlib.metadata import version as get_version
from typing import Any

from sdk import cli, config, logging
from sdk.compat import UTC
from sdk.datetime import format_datetime, to_naive, to_utc

PACKAGE = __name__
VERSION = get_version(__name__)

JSONType = dict[str, Any] | list[Any] | float | int | str | None

__all__ = (
    "UTC",
    "JSONType",
    "cli",
    "config",
    "config",
    "format_datetime",
    "logging",
    "to_naive",
    "to_utc",
)
