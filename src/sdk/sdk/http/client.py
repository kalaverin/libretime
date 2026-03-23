"""HTTP client implementation using httpx.

This module provides an HTTP client with:
- Connection pooling and reuse
- Request/response logging
- Exception handling with detailed error information
- Support for custom headers and expectations

Example:
    >>> from sdk.http import HTTPxClient
    >>> client = HTTPxClient.create("https://api.example.com")
    >>> response = await client.get("/users", expect=200)
    >>> print(response.data)
"""

# ruff: noqa: ANN401

import re

from asyncio import create_task, gather
from collections.abc import Awaitable, Callable
from contextlib import suppress
from enum import Enum
from functools import cached_property
from logging import WARNING, getLogger
from operator import methodcaller
from re import match
from typing import Any, ClassVar
from urllib.parse import urlparse, urlunparse

from httpx import AsyncClient, Headers, Limits, Response
from orjson import loads
from pydantic import BaseModel, ConfigDict, ValidationError
from typing_extensions import Self

from sdk.http import schemas
from sdk.http.exceptions import HTTPxError
from sdk.http.shared import (
    MIME_JSON,
    is_json_response,
    read_json_from_response,
    to_json,
)

logger = getLogger(__name__)

# reduce noise from httpx internals

getLogger("httpcore").setLevel(WARNING)
getLogger("httpx").setLevel(WARNING)


class Method(str, Enum):
    """HTTP methods supported by the client.

    Attributes:
        GET: HTTP GET method.
        PUT: HTTP PUT method.
        POST: HTTP POST method.
        PATCH: HTTP PATCH method.
        DELETE: HTTP DELETE method.
    """

    GET = "get"
    PUT = "put"
    POST = "post"
    PATCH = "patch"
    DELETE = "delete"


def normalize_url(url: str) -> str:
    """Normalize a URL by cleaning path and lowercasing host/scheme.

    Args:
        url: The URL to normalize.

    Returns:
        Normalized URL string.

    Raises:
        ValueError: If URL is missing scheme or host.

    Example:
        >>> normalize_url("HTTPS://Example.COM//path//to//resource")
        'https://example.com/path/to/resource'
    """
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        msg = "invalid URL, scheme and host required"
        logger.exception(msg, extra={"url": url})
        raise ValueError(msg)

    # normalize multiple slashes in path to single slash
    # also ensure path is at least /
    normalized_path = re.sub(r"/+", "/", parsed.path) if parsed.path else "/"

    # scheme and host must be always lowercase
    return str(
        urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                normalized_path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            ),
        ),
    )


def join_url_path(base: str, path: str) -> str:
    """Join a base URL with a relative or absolute path.

    Args:
        base: The base URL (must have scheme and host).
        path: The path to append (relative or absolute).

    Returns:
        Complete normalized URL.

    Raises:
        ValueError: If base URL is invalid or path is a full URL.

    Example:
        >>> join_url_path("https://api.example.com/v1", "users")
        'https://api.example.com/v1/users'
        >>> join_url_path("https://api.example.com/v1", "/users")
        'https://api.example.com/users'
    """
    if not base:
        msg = "base URL is required"
        logger.exception(msg, extra={"base": base})
        raise ValueError(msg)

    if not path:
        return normalize_url(base)

    parsed_base = urlparse(normalize_url(base))
    if parsed_base.query:
        msg = "base URL must not contain query"
        logger.exception(msg, extra={"base": base})
        raise ValueError(msg)

    if not parsed_base.scheme or not parsed_base.netloc:
        msg = "invalid base URL, scheme and host required"
        logger.exception(msg, extra={"base": base})
        raise ValueError(msg)

    if match(r"(?i)^(https?://)", path):
        msg = "path must be relative or absolute, not full URL"
        logger.exception(msg, extra={"path": path})
        raise ValueError(msg)

    # relative path, append to the existing path
    if not path.startswith("/"):
        path = f"{parsed_base.path.rstrip('/')}/{path.lstrip('/')}"

    # otherwise, absolute path, just use it
    return normalize_url(
        str(
            urlunparse(
                (
                    # scheme and host must be always lowercase
                    parsed_base.scheme.lower(),
                    parsed_base.netloc.lower(),
                    path,
                    parsed_base.params,
                    parsed_base.query,
                    parsed_base.fragment,
                ),
            ),
        ),
    )


def url_to_netloc(url: str) -> str:
    """Extract scheme and netloc from URL for connection pooling.

    Args:
        url: Full URL.

    Returns:
        URL with only scheme and netloc (no path).

    Example:
        >>> url_to_netloc("https://api.example.com/v1/users")
        'https://api.example.com'
    """
    # netloc designed for connection pooling key
    # then, trailing slash always removed, because netloc is without path
    parsed = urlparse(normalize_url(url))
    return f"{parsed.scheme}://{parsed.netloc}"


class HTTPxClientConfig(BaseModel):
    """Configuration for HTTPxClient.

    Attributes:
        base: Base URL for all requests.
        follow: Whether to follow redirects (default: True).
        timeout: Request timeout in seconds (default: 10.0).
        verbose: Enable verbose logging (default: False).
        verify: SSL verification (path to CA bundle or False, default: False).
        max_connections: Maximum number of connections in pool (default: 1).
        keep_connections: Number of keep-alive connections (default: 1).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True,
    )

    base: str
    follow: bool = True  # follow redirects
    timeout: float = 10.0

    verbose: bool = False
    verify: str | bool = False

    max_connections: int = 1  # max connections count
    keep_connections: int = 1  # keep connections


class HTTPxClient:
    """Async HTTP client with connection pooling and logging.

    This client provides:
    - Automatic connection pooling via class-level instance cache
    - Request/response logging with configurable verbosity
    - Exception handling with HTTPxError
    - JSON serialization/deserialization

    Note:
        Do not instantiate directly - use create() factory method.

    Example:
        >>> client = HTTPxClient.create(
        ...     "https://api.example.com", verbose=True)
        >>> async with client:
        ...     response = await client.get("/users")
        ...     print(response.status, response.data)
    """

    ResponseClass: ClassVar[type[schemas.HTTPxResponse]] = (
        schemas.HTTPxResponse
    )
    ExceptionClass: ClassVar[type[HTTPxError]] = HTTPxError

    _instances: ClassVar[dict[str, Any]] = {}

    Headers: ClassVar[dict[str, str]] = {
        "Accept": "*/*",
        "Accept-Encoding": "br, gzip, deflate, zstd",
    }

    @cached_property
    def headers(self) -> dict[str, Any]:
        """Instance-level headers copied from class defaults."""
        return self.Headers.copy()

    # instances and connections handling

    @classmethod
    def create(cls, base: str, **kw: Any) -> Self:
        """Create or retrieve a cached client instance.

        Clients are cached per class and base URL netloc to enable
        connection reuse.

        Args:
            base: Base URL for the client.
            **kw: Additional configuration parameters.

        Returns:
            Cached or new client instance.

        Raises:
            ValueError: If base URL is empty.
        """
        if not base:
            msg = "base url is required"
            logger.exception(msg, extra={"base": base})
            raise ValueError(msg)

        # connections in pool per class
        key = f"{cls.__name__}:{url_to_netloc(base)}"

        with suppress(KeyError):
            # we avoid using globals and cache instance in class

            result: Self = cls._instances[key]
            return result

        args = kw.copy()
        args.setdefault("base", base)
        cls._instances[key] = self = cls(**args, safe=True)
        return self

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *_) -> None:
        """Async context manager exit - closes the underlying client."""
        logger.debug(
            "Closing HTTPx client",
            extra={"class": type(self).__name__, "url": self.base},
        )
        await self.client.aclose()

    @classmethod
    async def shutdown(cls) -> None:
        """Shutdown all cached client instances.

        This should be called during application shutdown to properly
        close all connection pools.
        """
        await gather(
            *map(
                create_task,
                map(methodcaller("__aexit__"), cls._instances.values()),
            ),
        )

    # base attributes

    def __init__(self, /, safe: bool = False, **kw: Any) -> None:
        """Initialize client (internal use only).

        Args:
            safe: Must be True to allow instantiation (factory pattern).
            **kw: Configuration parameters.

        Raises:
            RuntimeError: If safe is False (use create() instead).
        """
        self.params: dict[str, Any] = kw
        if not safe:
            logger.fatal(
                "Direct instantiation of HTTPxClient is not allowed, "
                "use .create() method",
                extra={"class": type(self).__name__},
            )
            raise RuntimeError("Use .create() method to instantiate client")

    @cached_property
    def config(self) -> HTTPxClientConfig:
        """Parsed client configuration.

        Returns:
            Validated HTTPxClientConfig instance.

        Raises:
            ValidationError: If configuration parameters are invalid.
        """
        try:
            config = HTTPxClientConfig(**self.params)

        except ValidationError:
            logger.exception("Invalid params", extra={"params": self.params})
            raise

        if config.verbose:
            logger.info(
                "Client configuration",
                extra={
                    "class": type(self).__name__,
                    "config": loads(to_json(config.model_dump())),
                },
            )

        return config

    @cached_property
    def base(self) -> str:
        """Normalized base URL.

        Returns:
            Base URL with normalized path and lowercase host.

        Raises:
            ValueError: If base URL is not defined.
        """
        if url := self.config.base:
            return normalize_url(url)

        msg = "base URL isn't defined"
        logger.exception(msg, extra={"base": self.config.base})
        raise ValueError(msg)

    @cached_property
    def client(self) -> AsyncClient:
        """Underlying httpx AsyncClient instance.

        Returns:
            Configured AsyncClient with connection limits and timeouts.
        """
        msg = f"Creating {type(self).__name__} instance"
        logger.debug(
            msg,
            extra={"class": type(self).__name__, "host": self.base},
        )
        return AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify,
            limits=Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.keep_connections,
            ),
            follow_redirects=self.config.follow,
        )

    # convert input status codes to tuple with it

    def make_expectations(
        self,
        expect: tuple[int] | int | None,
    ) -> tuple[()] | tuple[int] | tuple[int, ...]:
        """Convert expected status codes to tuple format.

        Args:
            expect: Single status code, tuple of codes, or None.

        Returns:
            Tuple of expected status codes (empty tuple if None).
        """
        if isinstance(expect, int):
            return (expect,)

        if not expect:
            return ()

        return expect

    # mkay, let's go, send, receive and error catch

    async def send(  # noqa: PLR0913
        self,
        # only one we really required, it's method
        method: Method,
        # can be empty because we define base url
        url: str = "",
        /,
        # multiform, json-like or other data for request
        data: dict[str, Any] | None = None,
        # http-client other parameters, like timeouts, etc
        params: dict[str, Any] | None = None,
        # add custom headers for override, or pass additional '*' key for clean
        headers: dict[str, Any] | None = None,
        # without status-code expectations only errors (>=400) will be raised
        expect: tuple[int] | int | None = None,
    ) -> schemas.HTTPxResponse:
        """Send an HTTP request.

        Args:
            method: HTTP method to use.
            url: URL path (relative or absolute).
            data: Request body data (will be JSON serialized if dict).
            params: Query parameters.
            headers: Additional headers (use {"*": None} to clear defaults).
            expect: Expected status code(s) - raises exception if mismatch.

        Returns:
            HTTP response with parsed data.

        Raises:
            ValueError: For invalid HTTP method.
            HTTPxError: For unexpected status codes or HTTP errors.
        """
        client: AsyncClient = self.client

        try:
            func = getattr(client, method.value.lower())

        except AttributeError as e:
            msg = "invalid HTTP method"
            logger.exception(msg, extra={"method": method})
            raise ValueError(msg) from e

        request: dict[str, Any] = {"url": join_url_path(self.base, url)}

        headers = dict(headers or {})
        if "*" in headers:
            # when header named * passed - use only passed headers
            headers.pop("*")
        else:
            # otherwise merge all headers:
            # parent class -> class -> instance headers -> passed headers
            headers = {
                k: v
                for k, v in (self.headers | headers).items()
                if v is not None
            }

        # prepare data and fill headers

        request_headers = Headers(headers)
        if data:
            if request_headers.get("Content-Type") in (MIME_JSON, None):
                request["data"] = to_json(data)
                request_headers.setdefault("Content-Type", MIME_JSON)
            else:
                request["data"] = data

        if params:
            request["params"] = params

        # prepare logging message

        request["headers"] = request_headers
        if not self.config.verbose:
            request_headers = request_headers.copy()
            request_headers.pop("Authorization", None)

        data_log = loads(to_json(data or {})) if self.config.verbose else {}
        logger.info(
            "Sending request",
            extra={
                "class": type(self).__name__,
                "method": method.value.upper(),
                "url": request["url"],
                "headers": loads(to_json(request_headers)),
                "data": data_log,
            },
        )
        return await self.recv(func, request, expect)  # type: ignore[arg-type]

    async def recv(
        self,
        func: Callable[..., Awaitable[Any]],
        request: dict[str, Any],
        expect: tuple[int] | int | None = None,
    ) -> schemas.HTTPxResponse:
        """Receive and process HTTP response.

        Args:
            func: Async function to call (e.g., client.get).
            request: Request parameters dict.
            expect: Expected status code(s).

        Returns:
            Parsed HTTP response.

        Raises:
            HTTPxError: For error responses or unexpected status codes.
        """
        response = await func(**request)

        data = None
        if is_json_response(response):
            data = read_json_from_response(response)

        logger.info(
            "Received response",
            extra={
                "class": type(self).__name__,
                "status": response.status_code,
                "reason": response.reason_phrase,
                "headers": loads(to_json(response.headers)),
                "url": str(response.url),
                "data": data if self.config.verbose else None,
            },
        )

        # postprocess response and make exceptions

        if (not response.is_success or expect) and (
            exception := self.catch(response, self.make_expectations(expect))
        ):
            logger.warning(
                "Raising exception",
                extra={
                    "class": type(self).__name__,
                    "url": str(response.url),
                    "status": response.status_code,
                    "exception": type(exception).__name__,
                    "error": str(exception),
                },
            )
            raise exception

        return self.ResponseClass(
            status=response.status_code,
            headers=response.headers,
            body=response.content or None,
            data=data or {},
        )

    def catch(  # noqa: PLR0911
        self,
        call: Response,
        expect: tuple[()] | tuple[int] | tuple[int, ...],
    ) -> HTTPxError | None:
        """Catch and create exceptions from HTTP response.

        Args:
            call: HTTP response object.
            expect: Expected status codes.

        Returns:
            HTTPxError instance if an error occurred, None otherwise.
        """
        if expect:
            # first check, if we expect some status codes
            if call.status_code in expect:
                logger.debug(
                    "Got expected status",
                    extra={"status": call.status_code},
                )
                return None

            # second, catch expected defaults
            if exception := self.ExceptionClass.catch(call):
                return exception

            # then make and throw exception if not expected
            return self.ExceptionClass.make_from(call)

        # when expectations are not set, we just skip correct responses
        if not (call.is_client_error or call.is_server_error):
            return None

        # but, after it we grab potential customized exceptions
        if exception := self.ExceptionClass.catch(call):
            return exception

        # finally, we try to catch generic HTTP exceptions
        if exception := HTTPxError.catch(call):
            return exception

        return None

    # public interface

    async def get(self, url: str = "", **kw: Any) -> schemas.HTTPxResponse:
        """Send GET request.

        Args:
            url: URL path.
            **kw: Additional parameters (data, headers, expect, etc.).

        Returns:
            HTTP response.
        """
        return await self.send(Method.GET, url, **kw)

    async def put(self, url: str = "", **kw: Any) -> schemas.HTTPxResponse:
        """Send PUT request.

        Args:
            url: URL path.
            **kw: Additional parameters.

        Returns:
            HTTP response.
        """
        return await self.send(Method.PUT, url, **kw)

    async def post(self, url: str = "", **kw: Any) -> schemas.HTTPxResponse:
        """Send POST request.

        Args:
            url: URL path.
            **kw: Additional parameters.

        Returns:
            HTTP response.
        """
        return await self.send(Method.POST, url, **kw)

    async def patch(self, url: str = "", **kw: Any) -> schemas.HTTPxResponse:
        """Send PATCH request.

        Args:
            url: URL path.
            **kw: Additional parameters.

        Returns:
            HTTP response.
        """
        return await self.send(Method.PATCH, url, **kw)

    async def delete(self, url: str = "", **kw: Any) -> schemas.HTTPxResponse:
        """Send DELETE request.

        Args:
            url: URL path.
            **kw: Additional parameters.

        Returns:
            HTTP response.
        """
        return await self.send(Method.DELETE, url, **kw)
