from importlib.metadata import version as get_version

from libretime_api_client import v1, v2

PACKAGE = __name__
VERSION = get_version(__name__)

__all__ = (
    "v1",
    "v2",
)
