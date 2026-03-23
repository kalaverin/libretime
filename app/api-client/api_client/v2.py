from api_client._client import (
    AbstractApiClient,
    Response,
    default_retry,
)


class ApiClient(AbstractApiClient):
    VERSION: str = "2.0"

    def __init__(self, base_url: str, api_key: str) -> None:
        super().__init__(
            base_url=base_url,
            retry=default_retry(),
        )
        self.session.headers.update({"Authorization": f"Api-Key {api_key}"})

    def get_info(self) -> Response:
        return self._request("GET", "/api/v2/info")

    def get_version(self) -> Response:
        return self._request("GET", "/api/v2/version")

    def get_show(self, item_id: int) -> Response:
        return self._request("GET", f"/api/v2/shows/{item_id}")

    def get_show_instance(self, item_id: int) -> Response:
        return self._request("GET", f"/api/v2/show-instances/{item_id}")

    def list_schedule(
        self,
        ends_after: str,
        ends_before: str,
        overbooked: bool = False,
        position_status__gt: int = 0,
    ) -> Response:
        return self._request(
            "GET",
            "/api/v2/schedule",
            params={
                "ends_after": ends_after,
                "ends_before": ends_before,
                "overbooked": overbooked,
                "position_status__gt": position_status__gt,
            },
        )

    def get_webstream(self, item_id: int) -> Response:
        return self._request("GET", f"/api/v2/webstreams/{item_id}")

    def get_file(self, item_id: int) -> Response:
        return self._request("GET", f"/api/v2/files/{item_id}")

    def update_file(
        self,
        item_id: int,
        size: int,
        md5: str,
    ) -> Response:
        return self._request(
            "PATCH",
            f"/api/v2/files/{item_id}",
            json={"filesize": size, "md5": md5},
        )

    def download_file(self, item_id: int, stream: bool = False) -> Response:
        return self._request(
            "GET",
            f"/api/v2/files/{item_id:d}/download",
            stream=stream,
        )

    def get_stream_preferences(self) -> Response:
        return self._request("GET", "/api/v2/stream/preferences")

    def get_stream_state(self) -> Response:
        return self._request("GET", "/api/v2/stream/state")
