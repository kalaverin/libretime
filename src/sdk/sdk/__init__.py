from importlib.metadata import version as get_version
from typing import Any

from sdk import cli, config, logging
from sdk.compat import UTC

PACKAGE = __name__
VERSION = get_version(__name__)

JSONType = dict[str, Any] | list[Any] | float | int | str | None

__all__ = ("JSONType", "UTC", "cli", "config", "config", "logging")
