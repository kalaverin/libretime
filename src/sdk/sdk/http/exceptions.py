"""HTTP exception classes with status code helpers.

This module provides comprehensive HTTP exception handling with
status code checking properties and factory methods for creating
exceptions from HTTP responses.

Example:
    >>> from sdk.http.exceptions import HTTPxError
    >>> error = HTTPxError.make_from(response)
    >>> if error.isNotFound:
    ...     print("Resource not found")
"""

# ruff: noqa: N802

from functools import cached_property
from logging import getLogger
from re import match
from typing import Any

from httpx import Response
from starlette import status
from typing_extensions import Self, override

from sdk.http.shared import (
    is_json_response,
    read_json_from_response,
    to_json,
)

logger = getLogger(__name__)


class HTTPStatusesMixin:
    """Mixin providing HTTP status code check properties.

    This mixin adds boolean properties for checking specific HTTP status codes.
    All properties follow the pattern `is<StatusName>`.

    Attributes:
        status: The HTTP status code (must be set by subclass).

    Example:
        >>> class Response(HTTPStatusesMixin):
        ...     def __init__(self, status):
        ...         self.status = status
        >>> r = Response(404)
        >>> r.isNotFound
        True
    """

    status: int

    # informational responses

    @property
    def isContinue(self) -> bool:
        """Check if status is 100 Continue."""
        return bool(self.status == status.HTTP_100_CONTINUE)

    @property
    def isSwitchingProtocols(self) -> bool:
        """Check if status is 101 Switching Protocols."""
        return bool(self.status == status.HTTP_101_SWITCHING_PROTOCOLS)

    @property
    def isProcessing(self) -> bool:
        """Check if status is 102 Processing."""
        return bool(self.status == status.HTTP_102_PROCESSING)

    @property
    def isEarlyHints(self) -> bool:
        """Check if status is 103 Early Hints."""
        return bool(self.status == status.HTTP_103_EARLY_HINTS)

    # successful responses

    @property
    def isOk(self) -> bool:
        """Check if status is 200 OK."""
        return bool(self.status == status.HTTP_200_OK)

    @property
    def isCreated(self) -> bool:
        """Check if status is 201 Created."""
        return bool(self.status == status.HTTP_201_CREATED)

    @property
    def isAccepted(self) -> bool:
        """Check if status is 202 Accepted."""
        return bool(self.status == status.HTTP_202_ACCEPTED)

    @property
    def isNonAuthoritativeInformation(self) -> bool:
        """Check if status is 203 Non-Authoritative Information."""
        return bool(
            self.status == status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
        )

    @property
    def isNoContent(self) -> bool:
        """Check if status is 204 No Content."""
        return bool(self.status == status.HTTP_204_NO_CONTENT)

    @property
    def isResetContent(self) -> bool:
        """Check if status is 205 Reset Content."""
        return bool(self.status == status.HTTP_205_RESET_CONTENT)

    @property
    def isPartialContent(self) -> bool:
        """Check if status is 206 Partial Content."""
        return bool(self.status == status.HTTP_206_PARTIAL_CONTENT)

    @property
    def isMultiStatus(self) -> bool:
        """Check if status is 207 Multi-Status."""
        return bool(self.status == status.HTTP_207_MULTI_STATUS)

    @property
    def isAlreadyReported(self) -> bool:
        """Check if status is 208 Already Reported."""
        return bool(self.status == status.HTTP_208_ALREADY_REPORTED)

    @property
    def isImUsed(self) -> bool:
        """Check if status is 226 IM Used."""
        return bool(self.status == status.HTTP_226_IM_USED)

    # redirection messages

    @property
    def isMultipleChoices(self) -> bool:
        """Check if status is 300 Multiple Choices."""
        return bool(self.status == status.HTTP_300_MULTIPLE_CHOICES)

    @property
    def isMovedPermanently(self) -> bool:
        """Check if status is 301 Moved Permanently."""
        return bool(self.status == status.HTTP_301_MOVED_PERMANENTLY)

    @property
    def isFound(self) -> bool:
        """Check if status is 302 Found."""
        return bool(self.status == status.HTTP_302_FOUND)

    @property
    def isSeeOther(self) -> bool:
        """Check if status is 303 See Other."""
        return bool(self.status == status.HTTP_303_SEE_OTHER)

    @property
    def isNotModified(self) -> bool:
        """Check if status is 304 Not Modified."""
        return bool(self.status == status.HTTP_304_NOT_MODIFIED)

    @property
    def isUseProxy(self) -> bool:
        """Check if status is 305 Use Proxy."""
        return bool(self.status == status.HTTP_305_USE_PROXY)

    @property
    def isReserved(self) -> bool:
        """Check if status is 306 Reserved."""
        return bool(self.status == status.HTTP_306_RESERVED)

    @property
    def isTemporaryRedirect(self) -> bool:
        """Check if status is 307 Temporary Redirect."""
        return bool(self.status == status.HTTP_307_TEMPORARY_REDIRECT)

    @property
    def isPermanentRedirect(self) -> bool:
        """Check if status is 308 Permanent Redirect."""
        return bool(self.status == status.HTTP_308_PERMANENT_REDIRECT)

    # client error responses

    @property
    def isBadRequest(self) -> bool:
        """Check if status is 400 Bad Request."""
        return bool(self.status == status.HTTP_400_BAD_REQUEST)

    @property
    def isUnauthorized(self) -> bool:
        """Check if status is 401 Unauthorized."""
        return bool(self.status == status.HTTP_401_UNAUTHORIZED)

    @property
    def isPaymentRequired(self) -> bool:
        """Check if status is 402 Payment Required."""
        return bool(self.status == status.HTTP_402_PAYMENT_REQUIRED)

    @property
    def isForbidden(self) -> bool:
        """Check if status is 403 Forbidden."""
        return bool(self.status == status.HTTP_403_FORBIDDEN)

    @property
    def isNotFound(self) -> bool:
        """Check if status is 404 Not Found."""
        return bool(self.status == status.HTTP_404_NOT_FOUND)

    @property
    def isMethodNotAllowed(self) -> bool:
        """Check if status is 405 Method Not Allowed."""
        return bool(self.status == status.HTTP_405_METHOD_NOT_ALLOWED)

    @property
    def isNotAcceptable(self) -> bool:
        """Check if status is 406 Not Acceptable."""
        return bool(self.status == status.HTTP_406_NOT_ACCEPTABLE)

    @property
    def isProxyAuthenticationRequired(self) -> bool:
        """Check if status is 407 Proxy Authentication Required."""
        return bool(
            self.status == status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED,
        )

    @property
    def isRequestTimeout(self) -> bool:
        """Check if status is 408 Request Timeout."""
        return bool(self.status == status.HTTP_408_REQUEST_TIMEOUT)

    @property
    def isConflict(self) -> bool:
        """Check if status is 409 Conflict."""
        return bool(self.status == status.HTTP_409_CONFLICT)

    @property
    def isGone(self) -> bool:
        """Check if status is 410 Gone."""
        return bool(self.status == status.HTTP_410_GONE)

    @property
    def isLengthRequired(self) -> bool:
        """Check if status is 411 Length Required."""
        return bool(self.status == status.HTTP_411_LENGTH_REQUIRED)

    @property
    def isPreconditionFailed(self) -> bool:
        """Check if status is 412 Precondition Failed."""
        return bool(self.status == status.HTTP_412_PRECONDITION_FAILED)

    @property
    def isRequestEntityTooLarge(self) -> bool:
        """Check if status is 413 Request Entity Too Large."""
        return bool(self.status == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    @property
    def isRequestUriTooLong(self) -> bool:
        """Check if status is 414 Request URI Too Long."""
        return bool(self.status == status.HTTP_414_REQUEST_URI_TOO_LONG)

    @property
    def isUnsupportedMediaType(self) -> bool:
        """Check if status is 415 Unsupported Media Type."""
        return bool(self.status == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    @property
    def isRequestedRangeNotSatisfiable(self) -> bool:
        """Check if status is 416 Requested Range Not Satisfiable."""
        return bool(
            self.status == status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
        )

    @property
    def isExpectationFailed(self) -> bool:
        """Check if status is 417 Expectation Failed."""
        return bool(self.status == status.HTTP_417_EXPECTATION_FAILED)

    @property
    def isImATeapot(self) -> bool:
        """Check if status is 418 I'm a Teapot."""
        return bool(self.status == status.HTTP_418_IM_A_TEAPOT)

    @property
    def isMisdirectedRequest(self) -> bool:
        """Check if status is 421 Misdirected Request."""
        return bool(self.status == status.HTTP_421_MISDIRECTED_REQUEST)

    @property
    def isUnprocessableEntity(self) -> bool:
        """Check if status is 422 Unprocessable Entity."""
        return bool(self.status == status.HTTP_422_UNPROCESSABLE_CONTENT)

    @property
    def isLocked(self) -> bool:
        """Check if status is 423 Locked."""
        return bool(self.status == status.HTTP_423_LOCKED)

    @property
    def isFailedDependency(self) -> bool:
        """Check if status is 424 Failed Dependency."""
        return bool(self.status == status.HTTP_424_FAILED_DEPENDENCY)

    @property
    def isTooEarly(self) -> bool:
        """Check if status is 425 Too Early."""
        return bool(self.status == status.HTTP_425_TOO_EARLY)

    @property
    def isUpgradeRequired(self) -> bool:
        """Check if status is 426 Upgrade Required."""
        return bool(self.status == status.HTTP_426_UPGRADE_REQUIRED)

    @property
    def isPreconditionRequired(self) -> bool:
        """Check if status is 428 Precondition Required."""
        return bool(self.status == status.HTTP_428_PRECONDITION_REQUIRED)

    @property
    def isTooManyRequests(self) -> bool:
        """Check if status is 429 Too Many Requests."""
        return bool(self.status == status.HTTP_429_TOO_MANY_REQUESTS)

    @property
    def isRequestHeaderFieldsTooLarge(self) -> bool:
        """Check if status is 431 Request Header Fields Too Large."""
        return bool(
            self.status == status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
        )

    @property
    def isUnavailableForLegalReasons(self) -> bool:
        """Check if status is 451 Unavailable For Legal Reasons."""
        return bool(
            self.status == status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
        )

    # server error responses

    @property
    def isInternalServerError(self) -> bool:
        """Check if status is 500 Internal Server Error."""
        return bool(self.status == status.HTTP_500_INTERNAL_SERVER_ERROR)

    @property
    def isNotImplemented(self) -> bool:
        """Check if status is 501 Not Implemented."""
        return bool(self.status == status.HTTP_501_NOT_IMPLEMENTED)

    @property
    def isBadGateway(self) -> bool:
        """Check if status is 502 Bad Gateway."""
        return bool(self.status == status.HTTP_502_BAD_GATEWAY)

    @property
    def isServiceUnavailable(self) -> bool:
        """Check if status is 503 Service Unavailable."""
        return bool(self.status == status.HTTP_503_SERVICE_UNAVAILABLE)

    @property
    def isGatewayTimeout(self) -> bool:
        """Check if status is 504 Gateway Timeout."""
        return bool(self.status == status.HTTP_504_GATEWAY_TIMEOUT)

    @property
    def isHttpVersionNotSupported(self) -> bool:
        """Check if status is 505 HTTP Version Not Supported."""
        return bool(self.status == status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED)

    @property
    def isVariantAlsoNegotiates(self) -> bool:
        """Check if status is 506 Variant Also Negotiates."""
        return bool(self.status == status.HTTP_506_VARIANT_ALSO_NEGOTIATES)

    @property
    def isInsufficientStorage(self) -> bool:
        """Check if status is 507 Insufficient Storage."""
        return bool(self.status == status.HTTP_507_INSUFFICIENT_STORAGE)

    @property
    def isLoopDetected(self) -> bool:
        """Check if status is 508 Loop Detected."""
        return bool(self.status == status.HTTP_508_LOOP_DETECTED)

    @property
    def isNotExtended(self) -> bool:
        """Check if status is 510 Not Extended."""
        return bool(self.status == status.HTTP_510_NOT_EXTENDED)

    @property
    def isNetworkAuthenticationRequired(self) -> bool:
        """Check if status is 511 Network Authentication Required."""
        return bool(
            self.status == status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED,
        )


class HTTPxError(HTTPStatusesMixin, Exception):
    """Base exception for HTTP errors.

    Combines HTTP status code checking with exception functionality.
    Can be created from HTTP responses or manually instantiated.

    Attributes:
        status: HTTP status code.
        reason: HTTP reason phrase.
        data: Parsed response data (JSON or raw content).
        description: Error description or response text.

    Example:
        >>> error = HTTPxError(404, "Not Found", {"error": "User not found"})
        >>> error.isNotFound
        True
        >>> str(error)
        '404 Not Found'
    """

    @classmethod
    def make_from(
        cls,
        call: Response,
        klass: type | None = None,
        description: str | None = None,
    ) -> Self:
        """Create an exception from an HTTP response.

        Args:
            call: HTTP response object.
            klass: Optional exception subclass to use.
            description: Optional custom description.

        Returns:
            HTTPxError instance with parsed response data.
        """
        # extract details from response body and build exception
        # we expect that response body is JSON with error details
        # but if not - just use raw content

        if is_json_response(call):
            data = read_json_from_response(call)
        else:
            data = None

        result: Self = (klass or cls)(
            call.status_code,
            call.reason_phrase,
            data or call.content,
            description or call.text,
        )
        return result

    @classmethod
    def catch(cls, call: Response) -> Self | None:
        """Catch HTTP errors from a response.

        Args:
            call: HTTP response object.

        Returns:
            Exception instance if status >= 400, None otherwise.
        """
        # make HTTP exception when response hit >=400,<=599

        if call.is_client_error:
            return cls.make_from(call, klass=HTTPxClientError)

        if call.is_server_error:
            return cls.make_from(call, klass=HTTPxServerError)

        return None

    def __init__(
        self,
        status: int,
        reason: str,
        data: Any,  # noqa: ANN401
        description: str | None = None,
    ) -> None:
        """Initialize HTTP error.

        Args:
            status: HTTP status code.
            reason: HTTP reason phrase.
            data: Response data (parsed JSON or bytes).
            description: Error description.
        """
        self.status: int = status
        self.reason: str = reason

        self.data: Any = data
        self.description: str | None = description

        super().__init__(description, status)

    @override
    def __str__(self) -> str:
        return self.message

    @cached_property
    def message(self) -> str:
        """Formatted error message."""
        reason = self.reason
        if match(r"^([a-z]+)$", reason):
            reason = reason.capitalize()

        msg = f"{self.status} {reason}"
        if not self.description:
            return msg

        return f"{msg}: {self.description}"

    @cached_property
    def as_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary.

        Returns:
            Dictionary with error details.
        """
        return {
            "data": self.data,
            "description": self.description,
            "reason": self.reason,
            "status": self.status,
            "message": self.message,
        }

    @cached_property
    def as_json(self) -> str:
        """Convert exception to JSON string.

        Returns:
            JSON representation of the error.
        """
        return to_json(self.as_dict)


class HTTPxClientError(HTTPxError):
    """Exception for 4xx client errors."""


class HTTPxServerError(HTTPxError):
    """Exception for 5xx server errors."""
