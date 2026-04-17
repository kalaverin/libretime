import pytest

from api_client.v1 import ApiClient


def test_api_client(requests_mock):
    api_client = ApiClient(base_url="http://localhost:8080", api_key="test-key")

    requests_mock.get(
        "http://localhost:8080/api/version",
        json={"api_version": "1.0.0"},
    )

    assert api_client.version() == "1.0.0"
