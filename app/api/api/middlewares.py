from collections.abc import Callable
from typing import TYPE_CHECKING

from structlog import get_logger

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    def __init__(
        self,
        get_response: Callable[["HttpRequest"], "HttpResponse"],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: "HttpRequest") -> "HttpResponse":
        response = self.get_response(request)

        if getattr(response, "exception", None):
            logger.fatal(
                f"{request.method} {request.path} {response.status_code} "
                f"{request.headers} {response.content}",
            )

        return response
