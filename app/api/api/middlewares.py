from structlog import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(response, 'exception', None):
            logger.fatal(
                f"{request.method} {request.path} {response.status_code} "
                f"{request.headers} {response.content}"
            )

        return response
