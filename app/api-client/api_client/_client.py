from typing import Any

from requests import Response
from requests import Session as BaseSession
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.models import PreparedRequest
from sdk.http import join_url_path
from starlette import status
from structlog import get_logger
from typing_extensions import override
from urllib3.util import Retry

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 5


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(
        self,
        *args: Any,
        **kwargs: dict[str, Any],
    ) -> None:
        self.timeout: float | int = kwargs.pop("timeout", DEFAULT_TIMEOUT)
        super().__init__(*args, **kwargs)

    @override
    def send(
        self,
        request: PreparedRequest,
        *args: Any,
        **kwargs: dict[str, Any],
    ) -> Response:
        kwargs.setdefault("timeout", self.timeout)
        return super().send(request, *args, **kwargs)


def default_retry(max_retries: int = 5) -> Retry:
    return Retry(
        total=max_retries,
        backoff_factor=2,
        status_forcelist=[
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ],
    )


class Session(BaseSession):
    base_url: str | None

    def __init__(
        self,
        base_url: str | None = None,
        retry: Retry | None = None,
    ):
        super().__init__()
        self.base_url = base_url

        adapter = TimeoutHTTPAdapter(max_retries=retry)

        self.mount("http://", adapter)
        self.mount("https://", adapter)

    @override
    def request(
        self, method: str, url: str, *args: Any, **kwargs: Any,
    ) -> Response:
        """Send the request after generating the complete URL."""
        url = self.create_url(url)
        return super().request(method, url, *args, **kwargs)

    def create_url(self, url: str) -> str:
        """Create the URL based off this partial path."""
        if self.base_url is None:
            return url
        return join_url_path(self.base_url, url)


# pylint: disable=too-few-public-methods
class AbstractApiClient:
    session: Session
    base_url: str

    def __init__(
        self,
        base_url: str,
        retry: Retry | None = None,
    ) -> None:
        self.base_url = base_url
        self.session = Session(
            base_url=base_url,
            retry=retry,
        )

    def _request(
        self,
        method: str,
        url: str,
        stream: bool = False,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Response:
        try:
            response = self.session.request(
                method,
                url,
                data=data,
                json=json,
                params=params,
                stream=stream,
            )
            response.raise_for_status()

        except RequestException:
            logger.exception("request failed", method=method, url=url)
            raise

        return response
