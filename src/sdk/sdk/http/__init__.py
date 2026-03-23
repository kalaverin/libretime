"""HTTP client utilities and Zitadel integration.

This module provides HTTP client classes for general API communication
and Zitadel-specific interactions, along with utilities for URL handling.

Example:
    >>> from sdk.http import HTTPxClient, ZitadelClient
    >>> client = HTTPxClient.create("https://api.example.com")
    >>> response = await client.get("/users")

    >>> # Zitadel client
    >>> zitadel = ZitadelClient.create(
    ...     base="https://zitadel.example.com",
    ...     vault=vault,
    ...     bearer_token="env:ZITADEL_TOKEN",
    ...     service_account_id="123",
    ... )
"""

from sdk.http.client import (
    HTTPxClient,
    join_url_path,
    normalize_url,
    url_to_netloc,
)
from sdk.http.exceptions import HTTPxError
from sdk.http.schemas import HTTPxResponse
from sdk.http.shared import JSONType, to_json

__all__ = (
    "HTTPxClient",
    "HTTPxError",
    "HTTPxResponse",
    "JSONType",
    "join_url_path",
    "normalize_url",
    "to_json",
    "url_to_netloc",
)
