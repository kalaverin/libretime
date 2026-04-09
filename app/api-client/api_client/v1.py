import logging

from collections.abc import Callable
from contextlib import suppress
from functools import partial, wraps
from time import sleep
from typing import Any, TypeVar

import orjson

from requests.exceptions import RequestException
from sdk.http import JSONType

from api_client._client import AbstractApiClient, Response

logger = logging.getLogger(__name__)

DEFAULT_JSON_OPTIONS: int = (
    orjson.OPT_SORT_KEYS
    | orjson.OPT_NAIVE_UTC
    | orjson.OPT_SERIALIZE_DATACLASS
    | orjson.OPT_SERIALIZE_NUMPY
    | orjson.OPT_SERIALIZE_UUID
)

dumps = partial(orjson.dumps, option=DEFAULT_JSON_OPTIONS)


F = TypeVar("F", bound=Callable[..., Any])


def retry_decorator(max_retries: int = 5) -> Callable[[F], F]:
    def retry_request(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = max_retries
            while True:
                try:
                    return func(*args, **kwargs)
                except RequestException as exception:
                    logger.warning(exception)

                    retries -= 1
                    if retries <= 0:
                        break

                    sleep(2.0)

            return None

        return wrapper  # type: ignore[return-value]

    return retry_request


class BaseApiClient(AbstractApiClient):
    def __init__(self, base_url: str, api_key: str) -> None:
        super().__init__(base_url=base_url)
        self.session.headers.update({"Authorization": f"Api-Key {api_key}"})
        self.session.params.update({"format": "json"})  # type: ignore[union-attr]

    def version(self) -> Response:
        return self._request(
            "GET",
            "/api/version",
        )

    def register_component(self, component: str) -> Response:
        return self._request(
            "GET",
            "/api/register-component",
            params={"component": component},
        )

    def notify_media_item_start_play(self, media_id: int) -> Response:
        return self._request(
            "GET",
            "/api/notify-media-item-start-play",
            params={"media_id": media_id},
        )

    def update_liquidsoap_status(
        self,
        msg: str,
        stream_id: int,
        boot_time: str,
    ) -> Response:
        return self._request(
            "POST",
            "/api/update-liquidsoap-status",
            params={"stream_id": stream_id, "boot_time": boot_time},
            data={"msg_post": msg},
        )

    def update_source_status(
        self,
        sourcename: str,
        status: str,
    ) -> Response:
        return self._request(
            "GET",
            "/api/update-source-status",
            params={"sourcename": sourcename, "status": status},
        )

    def check_live_stream_auth(
        self,
        username: str,
        password: str,
        djtype: str,
    ) -> Response:
        return self._request(
            "GET",
            "/api/check-live-stream-auth",
            params={
                "username": username,
                "password": password,
                "djtype": djtype,
            },
        )

    def notify_webstream_data(
        self,
        media_id: str,
        data: str,
    ) -> Response:
        return self._request(
            "POST",
            "/api/notify-webstream-data",
            params={"media_id": media_id},
            data={"data": data},  # Data is already a json formatted string
        )

    def rabbitmq_do_push(self) -> Response:
        return self._request(
            "GET",
            "/api/rabbitmq-do-push",
        )

    def push_stream_stats(
        self,
        data: list[dict[str, Any]],
    ) -> Response:
        return self._request(
            "POST",
            "/api/push-stream-stats",
            data={"data": dumps(data)},
        )

    def update_stream_setting_table(
        self,
        data: dict[int, Any],
    ) -> Response:
        return self._request(
            "POST",
            "/api/update-stream-setting-table",
            data={"data": dumps(data)},
        )

    def update_metadata_on_tunein(self) -> Response:
        return self._request(
            "GET",
            "/api/update-metadata-on-tunein",
        )


class ApiClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
    ) -> None:
        self._base_client: BaseApiClient = BaseApiClient(
            base_url=base_url,
            api_key=api_key,
        )

    def version(self) -> int:
        try:
            resp = self._base_client.version()
            payload = resp.json()
            return payload["api_version"]

        except RequestException:
            return -1

    def notify_liquidsoap_started(self) -> None:
        with suppress(RequestException):
            self._base_client.rabbitmq_do_push()

    def notify_media_item_start_playing(self, media_id: int) -> JSONType:
        """
        This is a callback from liquidsoap, we use this to notify
        about the currently playing *song*. We get passed a JSON string
        which we handed to liquidsoap in get_liquidsoap_data().
        """
        try:
            return self._base_client.notify_media_item_start_play(
                media_id=media_id,
            )
        except RequestException:
            return None

    def check_live_stream_auth(
        self,
        username: str,
        password: str,
        dj_type: str,
    ) -> JSONType:
        try:
            return self._base_client.check_live_stream_auth(
                username=username,
                password=password,
                djtype=dj_type,
            )
        except RequestException:
            return {}

    def register_component(self, component: str) -> Response:
        """
        Purpose of this method is to contact the server with a "Hey its
        me!" message. This will allow the server to register the component's
        (component = media-monitor, pypo etc.) ip address, and later use it
        to query monit via monit's http service, or download log files via a
        http server.
        """
        return self._base_client.register_component(component=component)

    @retry_decorator()
    def notify_liquidsoap_status(
        self,
        msg: str,
        stream_id: int,
        time: str,
    ) -> None:
        self._base_client.update_liquidsoap_status(
            msg=msg,
            stream_id=stream_id,
            boot_time=time,
        )

    @retry_decorator()
    def notify_source_status(
        self,
        sourcename: str,
        status: str,
    ) -> Response:
        return self._base_client.update_source_status(
            sourcename=sourcename,
            status=status,
        )

    @retry_decorator()
    def notify_webstream_data(
        self,
        data: str,
        media_id: int,
    ) -> Response:
        """
        Update the server with the latest metadata we've received from the
        external webstream
        """
        return self._base_client.notify_webstream_data(
            data=data,
            media_id=str(media_id),
        )

    def push_stream_stats(
        self,
        data: list[dict[str, Any]],
    ) -> Response:
        return self._base_client.push_stream_stats(data=data)

    def update_stream_setting_table(
        self,
        data: dict[int, Any],
    ) -> Response | None:
        try:
            return self._base_client.update_stream_setting_table(data=data)
        except RequestException:
            return None

    def update_metadata_on_tunein(self) -> None:
        self._base_client.update_metadata_on_tunein()

    def trigger_task_manager(self) -> None:
        self._base_client.version()
