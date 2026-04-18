"""Tests for sdk.http.schemas module."""

from unittest.mock import Mock

import pytest
from httpx import Headers
from pydantic import ValidationError

from sdk.http.schemas import BaseResponse, HTTPxResponse
from sdk.http.shared import to_json


class TestBaseResponse:
    """Tests for BaseResponse Pydantic model."""

    def test_create_minimal_response(self):
        """Test creating response with minimal required fields."""
        headers = Headers({"Content-Type": "application/json"})
        response = BaseResponse(status=200, headers=headers)

        assert response.status == 200
        assert response.headers == headers
        assert response.body is None
        assert response.data is None

    def test_create_full_response(self):
        """Test creating response with all fields."""
        headers = Headers({"Content-Type": "application/json"})
        response = BaseResponse(
            status=200,
            headers=headers,
            body=b'{"result": "success"}',
            data={"result": "success"},
        )

        assert response.status == 200
        assert response.body == b'{"result": "success"}'
        assert response.data == {"result": "success"}

    def test_status_validation_required(self):
        """Test that status is required."""
        headers = Headers({})

        with pytest.raises(ValidationError) as exc_info:
            BaseResponse(headers=headers)

        assert "status" in str(exc_info.value)

    def test_headers_validation_required(self):
        """Test that headers is required."""
        with pytest.raises(ValidationError) as exc_info:
            BaseResponse(status=200)

        assert "headers" in str(exc_info.value)

    def test_body_can_be_bytes(self):
        """Test that body can be bytes."""
        headers = Headers({})
        response = BaseResponse(status=200, headers=headers, body=b"binary data")

        assert response.body == b"binary data"

    def test_body_can_be_string(self):
        """Test that body can be a string."""
        headers = Headers({})
        response = BaseResponse(status=200, headers=headers, body="text data")

        assert response.body == "text data"

    def test_body_can_be_none(self):
        """Test that body can be None."""
        headers = Headers({})
        response = BaseResponse(status=200, headers=headers, body=None)

        assert response.body is None

    def test_data_can_be_dict(self):
        """Test that data can be a dictionary."""
        headers = Headers({})
        data = {"key": "value", "nested": {"a": 1}}
        response = BaseResponse(status=200, headers=headers, data=data)

        assert response.data == data

    def test_data_can_be_list(self):
        """Test that data can be a list."""
        headers = Headers({})
        data = [1, 2, 3, "test"]
        response = BaseResponse(status=200, headers=headers, data=data)

        assert response.data == data

    def test_data_can_be_string(self):
        """Test that data can be a string."""
        headers = Headers({})
        response = BaseResponse(status=200, headers=headers, data="test string")

        assert response.data == "test string"

    def test_data_can_be_number(self):
        """Test that data can be a number."""
        headers = Headers({})
        response = BaseResponse(status=200, headers=headers, data=42)

        assert response.data == 42

    def test_data_can_be_none(self):
        """Test that data can be None."""
        headers = Headers({})
        response = BaseResponse(status=200, headers=headers, data=None)

        assert response.data is None

    def test_arbitrary_types_allowed(self):
        """Test that arbitrary types are allowed in model config."""
        # The model_config should allow arbitrary types like httpx.Headers
        headers = Headers({"Content-Type": "application/json"})
        response = BaseResponse(status=200, headers=headers)

        # Should not raise validation error
        assert isinstance(response.headers, Headers)

    def test_status_must_be_integer(self):
        """Test that status must be an integer."""
        headers = Headers({})

        with pytest.raises(ValidationError):
            BaseResponse(status="not_an_int", headers=headers)

    def test_status_can_be_any_integer(self):
        """Test that status can be any HTTP status code."""
        headers = Headers({})

        # Test various status codes
        for status in [100, 200, 201, 204, 301, 302, 400, 401, 403, 404, 500, 502]:
            response = BaseResponse(status=status, headers=headers)
            assert response.status == status

    def test_headers_type_preserved(self):
        """Test that headers type is preserved as httpx.Headers."""
        headers = Headers({
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        })
        response = BaseResponse(status=200, headers=headers)

        assert isinstance(response.headers, Headers)
        assert response.headers["Content-Type"] == "application/json"

    def test_model_dump_works(self):
        """Test that model_dump method works."""
        headers = Headers({"Content-Type": "application/json"})
        response = BaseResponse(
            status=200,
            headers=headers,
            data={"key": "value"},
        )

        dumped = response.model_dump()

        assert dumped["status"] == 200
        assert dumped["data"] == {"key": "value"}
        # Headers should be converted to dict
        assert "headers" in dumped

    def test_model_dump_json_works(self):
        """Test that response can be serialized to JSON."""
        headers = Headers({"Content-Type": "application/json"})
        response = BaseResponse(
            status=200,
            headers=headers,
            data={"key": "value"},
        )

        # model_dump_json cannot serialize arbitrary types like Headers directly
        dumped = response.model_dump()
        json_str = to_json(dumped)

        # Should be valid JSON string
        import orjson
        parsed = orjson.loads(json_str)
        assert parsed["status"] == 200
        assert parsed["data"] == {"key": "value"}

    def test_model_copy_works(self):
        """Test that model_copy method works."""
        headers = Headers({"Content-Type": "application/json"})
        response = BaseResponse(status=200, headers=headers, data={"key": "value"})

        copied = response.model_copy(update={"status": 201})

        assert copied.status == 201
        assert copied.data == {"key": "value"}
        # Original should be unchanged
        assert response.status == 200


class TestHTTPxResponse:
    """Tests for HTTPxResponse class."""

    def test_is_subclass_of_base_response(self):
        """Test HTTPxResponse is subclass of BaseResponse."""
        assert issubclass(HTTPxResponse, BaseResponse)

    def test_create_httpx_response(self):
        """Test creating HTTPxResponse instance."""
        headers = Headers({"Content-Type": "application/json"})
        response = HTTPxResponse(
            status=200,
            headers=headers,
            body=b'{"result": "success"}',
            data={"result": "success"},
        )

        assert response.status == 200
        assert isinstance(response, HTTPxResponse)

    def test_create_httpx_response_minimal(self):
        """Test creating minimal HTTPxResponse."""
        headers = Headers({})
        response = HTTPxResponse(status=204, headers=headers)

        assert response.status == 204
        assert response.body is None
        assert response.data is None

    def test_inherits_arbitrary_types_config(self):
        """Test that HTTPxResponse inherits arbitrary_types config."""
        # HTTPxResponse should also allow httpx.Headers without validation errors
        headers = Headers({"X-Custom": "value"})
        response = HTTPxResponse(status=200, headers=headers)

        assert isinstance(response.headers, Headers)

    def test_type_safety_marker(self):
        """Test that HTTPxResponse serves as type safety marker."""
        # HTTPxResponse is primarily a marker class for type safety
        # This test verifies it can be used in type annotations
        def process_response(response: HTTPxResponse) -> int:
            return response.status

        headers = Headers({})
        response = HTTPxResponse(status=200, headers=headers)

        assert process_response(response) == 200

    def test_error_response_creation(self):
        """Test creating error response with HTTPxResponse."""
        headers = Headers({"Content-Type": "application/json"})
        response = HTTPxResponse(
            status=404,
            headers=headers,
            body=b'{"error": "not found"}',
            data={"error": "not found"},
        )

        assert response.status == 404
        assert response.data["error"] == "not found"

    def test_redirect_response(self):
        """Test creating redirect response."""
        headers = Headers({"Location": "https://example.com/new"})
        response = HTTPxResponse(status=301, headers=headers)

        assert response.status == 301
        assert response.headers["Location"] == "https://example.com/new"

    def test_empty_response(self):
        """Test creating empty response (204 No Content)."""
        headers = Headers({})
        response = HTTPxResponse(status=204, headers=headers, body=b"")

        assert response.status == 204
        assert response.body == b""
