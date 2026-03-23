"""Shared utilities for HTTP handling.

This module provides JSON serialization, response parsing, and content
type detection utilities used by the HTTP client modules.

"""

# ruff: noqa: ANN401

from collections import defaultdict
from logging import getLogger
from typing import Any

from httpx import Headers, Response
from orjson import (
    OPT_NAIVE_UTC,
    OPT_NON_STR_KEYS,
    OPT_SERIALIZE_UUID,
    OPT_SORT_KEYS,
    dumps,
    loads,
)

JSONType = dict[str, Any] | list[Any] | float | int | str | None

MIME_JSON = "application/json"

OPT_JSON_FLAGS = (
    OPT_NAIVE_UTC | OPT_NON_STR_KEYS | OPT_SERIALIZE_UUID | OPT_SORT_KEYS
)

logger = getLogger(__name__)


def to_builtin(obj: Any) -> Any:
    """Convert special types to JSON-serializable builtins.

    Handles:
    - httpx.Headers -> dict
    - Vault String -> str or None

    Args:
        obj: Object to convert.

    Returns:
        JSON-serializable representation.

    Raises:
        NotImplementedError: If type is not supported.
    """
    if isinstance(obj, Headers):
        result = defaultdict(list)
        for key, value in obj.items():
            result[key].append(value)

        return {
            key: value[0] if len(value) == 1 else tuple(value)
            for key, value in result.items()
        }

    msg = "to_builtin: unsupported type"
    logger.exception(msg, extra={"type": type(obj), "repr": repr(obj)})
    raise NotImplementedError(msg)


def to_json(obj: Any) -> str:
    """Serialize object to JSON string using orjson.

    Args:
        obj: Object to serialize.

    Returns:
        JSON string.
    """
    if isinstance(obj, str):
        return obj

    if isinstance(obj, bytes):
        return obj.decode("utf-8")

    return dumps(obj, default=to_builtin, option=OPT_JSON_FLAGS).decode(
        "utf-8",
    )


def is_json_response(call: Response) -> bool:
    """Check if response has JSON content type.

    Args:
        call: HTTP response object.

    Returns:
        True if Content-Type header contains 'application/json'.
    """
    content_type = call.headers.get("Content-Type")
    return content_type and MIME_JSON in content_type.lower()


def read_json_from_response(
    call: Response,
    /,
    force: bool = False,
) -> JSONType:
    """Parse JSON from HTTP response.

    Args:
        call: HTTP response object.
        force: If True, parse even if Content-Type is not JSON.

    Returns:
        Parsed JSON data.

    Raises:
        ValueError: If response is not valid JSON or not JSON content type.
    """
    if force or is_json_response(call):
        try:
            result: JSONType = loads(call.content)

        except Exception as e:
            msg = "expected JSON, but isn't"
            raise ValueError(msg) from e

        return result

    msg = "it's not a JSON response"
    raise ValueError(msg)
