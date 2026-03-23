"""HTTP response schema definitions.

This module provides Pydantic models for HTTP responses with support
for various content types and httpx Headers.

Example:
    >>> from sdk.http.schemas import HTTPxResponse
    >>> response = HTTPxResponse(
    ...     status=200,
    ...     headers={"Content-Type": "application/json"},
    ...     data={"users": []},
    ... )
"""

from typing import ClassVar

from httpx import Headers
from pydantic import BaseModel, ConfigDict

from sdk.http.shared import JSONType


class BaseResponse(BaseModel):
    """Base response model with common HTTP response fields.

    Attributes:
        status: HTTP status code.
        headers: Response headers as httpx Headers object.
        body: Raw response body (bytes, str, or None).
        data: Parsed response data (JSON, etc.).

    Example:
        >>> response = BaseResponse(
        ...     status=200,
        ...     headers=Headers({"Content-Type": "application/json"}),
        ...     data={"result": "success"},
        ... )
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True,
    )

    status: int
    headers: Headers
    body: bytes | str | None = None
    data: JSONType | None = None


class HTTPxResponse(BaseResponse):
    """Response model for HTTPxClient requests.

    This is a marker class extending BaseResponse for type safety
    with HTTPxClient.
    """
