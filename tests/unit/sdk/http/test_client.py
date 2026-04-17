"""Tests for sdk.http.client module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, patch

import pytest
from httpx import AsyncClient, Headers, Limits, Response
from pydantic import ValidationError

from sdk.http.client import (
    HTTPxClient,
    HTTPxClientConfig,
    Method,
    join_url_path,
    normalize_url,
    url_to_netloc,
)
from sdk.http.exceptions import HTTPxClientError, HTTPxError, HTTPxServerError
from sdk.http.schemas import HTTPxResponse


class TestMethod:
    """Tests for Method enum."""

    def test_method_values(self):
        """Test that Method enum has correct values."""
        assert Method.GET.value == "get"
        assert Method.PUT.value == "put"
        assert Method.POST.value == "post"
        assert Method.PATCH.value == "patch"
        assert Method.DELETE.value == "delete"

    def test_method_is_str_subclass(self):
        """Test that Method is a subclass of str."""
        assert issubclass(Method, str)


class TestNormalizeUrl:
    """Tests for normalize_url function."""

    def test_normalizes_simple_url(self):
        """Test normalizing a simple URL."""
        result = normalize_url("https://example.com/path")

        assert result == "https://example.com/path"

    def test_lowercases_scheme_and_host(self):
        """Test that scheme and host are lowercased."""
        result = normalize_url("HTTPS://EXAMPLE.COM/path")

        assert result == "https://example.com/path"

    def test_normalizes_multiple_slashes(self):
        """Test that multiple slashes are normalized."""
        result = normalize_url("https://example.com//path///to/resource")

        assert result == "https://example.com/path/to/resource"

    def test_preserves_query_and_fragment(self):
        """Test that query and fragment are preserved."""
        result = normalize_url("https://example.com/path?query=value#fragment")

        assert result == "https://example.com/path?query=value#fragment"

    def test_preserves_params(self):
        """Test that URL params are preserved."""
        result = normalize_url("https://example.com/path;param=value")

        assert "param=value" in result

    def test_raises_value_error_for_missing_scheme(self):
        """Test that ValueError is raised for URL without scheme."""
        with pytest.raises(ValueError) as exc_info:
            normalize_url("example.com/path")

        assert "scheme and host required" in str(exc_info.value)

    def test_raises_value_error_for_missing_host(self):
        """Test that ValueError is raised for URL without host."""
        with pytest.raises(ValueError) as exc_info:
            normalize_url("https:///path")

        assert "scheme and host required" in str(exc_info.value)

    def test_ensures_leading_slash_on_path(self):
        """Test that path has leading slash."""
        result = normalize_url("https://example.com")

        assert result == "https://example.com/"

    def test_handles_empty_path(self):
        """Test handling of empty path."""
        result = normalize_url("https://example.com/")

        assert result == "https://example.com/"

    def test_logs_exception_on_error(self):
        """Test that exception is logged on error."""
        with patch("sdk.http.client.logger") as mock_logger:
            with pytest.raises(ValueError):
                normalize_url("invalid-url")

            mock_logger.exception.assert_called_once()


class TestJoinUrlPath:
    """Tests for join_url_path function."""

    def test_joins_relative_path(self):
        """Test joining relative path to base URL."""
        result = join_url_path("https://api.example.com/v1", "users")

        assert result == "https://api.example.com/v1/users"

    def test_joins_absolute_path(self):
        """Test joining absolute path to base URL."""
        result = join_url_path("https://api.example.com/v1", "/users")

        assert result == "https://api.example.com/users"

    def test_normalizes_result(self):
        """Test that result is normalized."""
        result = join_url_path("HTTPS://API.EXAMPLE.COM//v1", "users")

        assert result == "https://api.example.com/v1/users"

    def test_handles_empty_path(self):
        """Test handling of empty path."""
        result = join_url_path("https://api.example.com/v1", "")

        assert result == "https://api.example.com/v1"

    def test_raises_value_error_for_empty_base(self):
        """Test that ValueError is raised for empty base."""
        with pytest.raises(ValueError) as exc_info:
            join_url_path("", "users")

        assert "base URL is required" in str(exc_info.value)

    def test_raises_value_error_for_base_with_query(self):
        """Test that ValueError is raised for base with query string."""
        with pytest.raises(ValueError) as exc_info:
            join_url_path("https://api.example.com?query=value", "users")

        assert "must not contain query" in str(exc_info.value)

    def test_raises_value_error_for_full_url_as_path(self):
        """Test that ValueError is raised when path is full URL."""
        with pytest.raises(ValueError) as exc_info:
            join_url_path("https://api.example.com", "https://other.com/users")

        assert "not full URL" in str(exc_info.value)

    def test_raises_value_error_for_invalid_base(self):
        """Test that ValueError is raised for invalid base URL."""
        with pytest.raises(ValueError) as exc_info:
            join_url_path("not-a-valid-url", "users")

        assert "scheme and host required" in str(exc_info.value)

    def test_handles_http_url_as_path(self):
        """Test that HTTP URL as path raises error."""
        with pytest.raises(ValueError):
            join_url_path("https://api.example.com", "http://other.com/users")

    def test_logs_exception_for_empty_base(self):
        """Test that exception is logged for empty base."""
        with patch("sdk.http.client.logger") as mock_logger:
            with pytest.raises(ValueError):
                join_url_path("", "users")

            mock_logger.exception.assert_called_once()


class TestUrlToNetloc:
    """Tests for url_to_netloc function."""

    def test_extracts_scheme_and_host(self):
        """Test extracting scheme and host from URL."""
        result = url_to_netloc("https://api.example.com/v1/users")

        assert result == "https://api.example.com"

    def test_normalizes_input(self):
        """Test that input URL is normalized."""
        result = url_to_netloc("HTTPS://API.EXAMPLE.COM/path")

        assert result == "https://api.example.com"

    def test_removes_path(self):
        """Test that path is removed."""
        result = url_to_netloc("https://example.com/very/long/path/to/resource")

        assert result == "https://example.com"

    def test_preserves_port(self):
        """Test that port is preserved."""
        result = url_to_netloc("https://example.com:8443/path")

        assert result == "https://example.com:8443"

    def test_handles_root_path(self):
        """Test handling of root path."""
        result = url_to_netloc("https://example.com/")

        assert result == "https://example.com"


class TestHTTPxClientConfig:
    """Tests for HTTPxClientConfig Pydantic model."""

    def test_create_minimal_config(self):
        """Test creating config with minimal required fields."""
        config = HTTPxClientConfig(base="https://api.example.com")

        assert config.base == "https://api.example.com"
        # Check defaults
        assert config.follow is True
        assert config.timeout == 10.0
        assert config.verbose is False
        assert config.verify is False
        assert config.max_connections == 1
        assert config.keep_connections == 1

    def test_create_full_config(self):
        """Test creating config with all fields."""
        config = HTTPxClientConfig(
            base="https://api.example.com",
            follow=False,
            timeout=30.0,
            verbose=True,
            verify="/path/to/ca-bundle.crt",
            max_connections=10,
            keep_connections=5,
        )

        assert config.base == "https://api.example.com"
        assert config.follow is False
        assert config.timeout == 30.0
        assert config.verbose is True
        assert config.verify == "/path/to/ca-bundle.crt"
        assert config.max_connections == 10
        assert config.keep_connections == 5

    def test_base_is_required(self):
        """Test that base is required."""
        with pytest.raises(ValidationError) as exc_info:
            HTTPxClientConfig()

        assert "base" in str(exc_info.value)

    def test_timeout_must_be_float(self):
        """Test that timeout must be numeric."""
        with pytest.raises(ValidationError):
            HTTPxClientConfig(base="https://api.example.com", timeout="invalid")

    def test_verify_can_be_bool(self):
        """Test that verify can be a boolean."""
        config = HTTPxClientConfig(base="https://api.example.com", verify=True)

        assert config.verify is True

    def test_verify_can_be_string(self):
        """Test that verify can be a string path."""
        config = HTTPxClientConfig(
            base="https://api.example.com", verify="/path/to/cert"
        )

        assert config.verify == "/path/to/cert"

    def test_arbitrary_types_allowed(self):
        """Test that arbitrary types are allowed in config."""
        config = HTTPxClientConfig(base="https://api.example.com")

        # Should not raise validation errors for httpx types
        assert isinstance(config.model_config, dict)


class TestHTTPxClient:
    """Tests for HTTPxClient class."""

    @pytest.fixture(autouse=True)
    def clear_instances(self):
        """Clear client instances before each test."""
        HTTPxClient._instances.clear()
        yield
        HTTPxClient._instances.clear()

    @pytest.fixture
    def mock_async_client(self):
        """Create a mock AsyncClient."""
        with patch("sdk.http.client.AsyncClient") as mock:
            client_instance = AsyncMock(spec=AsyncClient)
            mock.return_value = client_instance
            yield mock, client_instance

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        response = Mock(spec=Response)
        response.status_code = 200
        response.reason_phrase = "OK"
        response.content = b'{"result": "success"}'
        response.text = '{"result": "success"}'
        response.headers = Headers({"Content-Type": "application/json"})
        response.url = "https://api.example.com/test"
        response.is_success = True
        response.is_client_error = False
        response.is_server_error = False
        return response

    # Instance creation tests

    def test_create_returns_instance(self, mock_async_client):
        """Test that create returns a client instance."""
        client = HTTPxClient.create("https://api.example.com")

        assert isinstance(client, HTTPxClient)

    def test_create_caches_instances(self, mock_async_client):
        """Test that create caches instances per netloc."""
        client1 = HTTPxClient.create("https://api.example.com")
        client2 = HTTPxClient.create("https://api.example.com")

        assert client1 is client2

    def test_create_different_netloc_different_instances(self, mock_async_client):
        """Test that different netlocs get different instances."""
        client1 = HTTPxClient.create("https://api1.example.com")
        client2 = HTTPxClient.create("https://api2.example.com")

        assert client1 is not client2

    def test_create_different_classes_different_instances(self, mock_async_client):
        """Test that different client classes get different instances."""

        class OtherClient(HTTPxClient):
            pass

        client1 = HTTPxClient.create("https://api.example.com")
        client2 = OtherClient.create("https://api.example.com")

        assert client1 is not client2

    def test_create_raises_value_error_for_empty_base(self, mock_async_client):
        """Test that create raises ValueError for empty base."""
        with pytest.raises(ValueError) as exc_info:
            HTTPxClient.create("")

        assert "base url is required" in str(exc_info.value)

    def test_direct_instantiation_raises_runtime_error(self):
        """Test that direct instantiation raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            HTTPxClient()

        assert "Use .create()" in str(exc_info.value)

    def test_safe_parameter_allows_instantiation(self):
        """Test that safe=True allows instantiation."""
        # This is for internal use
        client = HTTPxClient(safe=True, base="https://api.example.com")

        assert isinstance(client, HTTPxClient)

    def test_direct_instantiation_logs_fatal(self):
        """Test that direct instantiation logs fatal error."""
        with patch("sdk.http.client.logger") as mock_logger:
            with pytest.raises(RuntimeError):
                HTTPxClient()

            mock_logger.fatal.assert_called_once()

    # Configuration tests

    def test_config_property(self, mock_async_client):
        """Test that config property returns HTTPxClientConfig."""
        client = HTTPxClient.create("https://api.example.com")

        assert isinstance(client.config, HTTPxClientConfig)
        assert client.config.base == "https://api.example.com"

    def test_config_validation_error_logged(self, mock_async_client):
        """Test that config validation error is logged."""
        client = HTTPxClient(safe=True, base="https://api.example.com", timeout="invalid")

        with patch("sdk.http.client.logger") as mock_logger:
            with pytest.raises(ValidationError):
                _ = client.config

            mock_logger.exception.assert_called_once()

    def test_base_property_normalizes_url(self, mock_async_client):
        """Test that base property returns normalized URL."""
        client = HTTPxClient.create("HTTPS://API.EXAMPLE.COM//path")

        assert client.base == "https://api.example.com/path"

    def test_base_property_raises_value_error_if_undefined(self, mock_async_client):
        """Test that base property raises ValueError if not defined."""
        # Need to mock config to return empty base
        client = HTTPxClient(safe=True)
        client.params = {"base": ""}

        with patch.object(
            HTTPxClient, "config", new_callable=PropertyMock
        ) as mock_config:
            mock_config.return_value = Mock(base="")
            with pytest.raises(ValueError) as exc_info:
                _ = client.base

            assert "isn't defined" in str(exc_info.value)

    # Client property tests

    def test_client_property_returns_async_client(self, mock_async_client):
        """Test that client property returns AsyncClient."""
        client = HTTPxClient.create("https://api.example.com")

        async_client = client.client

        assert isinstance(async_client, AsyncMock)
        mock_async_client[0].assert_called_once()

    def test_client_configured_with_limits(self, mock_async_client):
        """Test that client is configured with connection limits."""
        client = HTTPxClient.create(
            "https://api.example.com",
            max_connections=10,
            keep_connections=5,
            timeout=30.0,
            verify=True,
            follow=False,
        )

        _ = client.client

        call_kwargs = mock_async_client[0].call_args.kwargs
        assert call_kwargs["timeout"] == 30.0
        assert call_kwargs["verify"] is True
        assert call_kwargs["follow_redirects"] is False
        limits = call_kwargs["limits"]
        assert isinstance(limits, Limits)
        assert limits.max_connections == 10
        assert limits.max_keepalive_connections == 5

    # Context manager tests

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_async_client):
        """Test async context manager usage."""
        client = HTTPxClient.create("https://api.example.com")

        async with client as ctx:
            assert ctx is client

        # Verify client was closed
        mock_async_client[1].aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_closes_all_instances(self, mock_async_client):
        """Test shutdown closes all cached instances."""
        client1 = HTTPxClient.create("https://api1.example.com")
        client2 = HTTPxClient.create("https://api2.example.com")

        await HTTPxClient.shutdown()

        # Both clients should be closed
        mock_async_client[1].aclose.assert_called()

    # make_expectations tests

    def test_make_expectations_with_none(self, mock_async_client):
        """Test make_expectations with None."""
        client = HTTPxClient.create("https://api.example.com")

        result = client.make_expectations(None)

        assert result == ()

    def test_make_expectations_with_int(self, mock_async_client):
        """Test make_expectations with single int."""
        client = HTTPxClient.create("https://api.example.com")

        result = client.make_expectations(200)

        assert result == (200,)

    def test_make_expectations_with_tuple(self, mock_async_client):
        """Test make_expectations with tuple."""
        client = HTTPxClient.create("https://api.example.com")

        result = client.make_expectations((200, 201, 204))

        assert result == (200, 201, 204)

    def test_make_expectations_with_empty_tuple(self, mock_async_client):
        """Test make_expectations with empty tuple."""
        client = HTTPxClient.create("https://api.example.com")

        result = client.make_expectations(())

        assert result == ()

    # send method tests

    @pytest.mark.asyncio
    async def test_send_get_request(self, mock_async_client, mock_response):
        """Test sending GET request."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.send(Method.GET, "/users")

        assert isinstance(result, HTTPxResponse)
        assert result.status == 200
        mock_async_client[1].get.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_post_request(self, mock_async_client, mock_response):
        """Test sending POST request."""
        mock_async_client[1].post = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.send(Method.POST, "/users", data={"name": "test"})

        assert isinstance(result, HTTPxResponse)
        mock_async_client[1].post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_put_request(self, mock_async_client, mock_response):
        """Test sending PUT request."""
        mock_async_client[1].put = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.send(Method.PUT, "/users/1", data={"name": "test"})

        mock_async_client[1].put.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_patch_request(self, mock_async_client, mock_response):
        """Test sending PATCH request."""
        mock_async_client[1].patch = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.send(Method.PATCH, "/users/1", data={"name": "test"})

        mock_async_client[1].patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_delete_request(self, mock_async_client, mock_response):
        """Test sending DELETE request."""
        mock_async_client[1].delete = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.send(Method.DELETE, "/users/1")

        mock_async_client[1].delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_invalid_method_raises_value_error(
        self, mock_async_client
    ):
        """Test that invalid method raises ValueError."""
        client = HTTPxClient.create("https://api.example.com")

        # Create a mock method that doesn't exist on httpx client
        invalid_method = Mock()
        invalid_method.value = "invalid_method"

        with pytest.raises(ValueError) as exc_info:
            await client.send(invalid_method, "/test")

        assert "invalid HTTP method" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_with_query_params(self, mock_async_client, mock_response):
        """Test sending request with query parameters."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        await client.send(Method.GET, "/users", params={"page": 1, "limit": 10})

        call_args = mock_async_client[1].get.call_args
        assert "params" in call_args.kwargs
        assert call_args.kwargs["params"] == {"page": 1, "limit": 10}

    @pytest.mark.asyncio
    async def test_send_with_custom_headers(self, mock_async_client, mock_response):
        """Test sending request with custom headers."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        await client.send(Method.GET, "/users", headers={"X-Custom": "value"})

        call_args = mock_async_client[1].get.call_args
        headers = call_args.kwargs["headers"]
        assert headers["X-Custom"] == "value"

    @pytest.mark.asyncio
    async def test_send_with_star_header_clears_defaults(
        self, mock_async_client, mock_response
    ):
        """Test that header with '*' key clears default headers."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        await client.send(Method.GET, "/users", headers={"*": None, "X-Only": "value"})

        call_args = mock_async_client[1].get.call_args
        headers = call_args.kwargs["headers"]
        assert "Accept" not in headers
        assert headers["X-Only"] == "value"

    @pytest.mark.asyncio
    async def test_send_with_authorization_header_logging(self, mock_async_client, mock_response):
        """Test that Authorization header is removed from non-verbose logs."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com", verbose=False)

        with patch("sdk.http.client.logger") as mock_logger:
            await client.send(Method.GET, "/users", headers={"Authorization": "secret"})

            # Check that Authorization was removed from logged headers
            logged_call = mock_logger.info.call_args_list[0]
            logged_headers = logged_call.kwargs["extra"]["headers"]
            assert "Authorization" not in logged_headers

    @pytest.mark.asyncio
    async def test_send_data_is_json_serialized(self, mock_async_client, mock_response):
        """Test that dict data is JSON serialized."""
        mock_async_client[1].post = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        data = {"name": "test", "value": 123}
        await client.send(Method.POST, "/users", data=data)

        call_args = mock_async_client[1].post.call_args
        # Data should be JSON string
        import orjson

        parsed = orjson.loads(call_args.kwargs["data"])
        assert parsed == data

    @pytest.mark.asyncio
    async def test_send_with_non_json_content_type(self, mock_async_client, mock_response):
        """Test that non-JSON content type doesn't serialize data."""
        mock_async_client[1].post = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        data = "raw body"
        await client.send(
            Method.POST, "/users", data=data, headers={"Content-Type": "text/plain"}
        )

        call_args = mock_async_client[1].post.call_args
        assert call_args.kwargs["data"] == data

    # recv method tests

    @pytest.mark.asyncio
    async def test_recv_success_response(self, mock_async_client, mock_response):
        """Test receiving successful response."""
        mock_func = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.recv(mock_func, {"url": "https://api.example.com/test"})

        assert isinstance(result, HTTPxResponse)
        assert result.status == 200
        assert result.data == {"result": "success"}

    @pytest.mark.asyncio
    async def test_recv_non_json_response(self, mock_async_client):
        """Test receiving non-JSON response."""
        response = Mock(spec=Response)
        response.status_code = 200
        response.reason_phrase = "OK"
        response.content = b"plain text"
        response.text = "plain text"
        response.headers = Headers({"Content-Type": "text/plain"})
        response.url = "https://api.example.com/test"
        response.is_success = True
        response.is_client_error = False
        response.is_server_error = False

        mock_func = AsyncMock(return_value=response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.recv(mock_func, {"url": "https://api.example.com/test"})

        assert result.status == 200
        assert result.data == {}

    @pytest.mark.asyncio
    async def test_recv_raises_on_client_error(self, mock_async_client):
        """Test that client error raises HTTPxError."""
        response = Mock(spec=Response)
        response.status_code = 404
        response.reason_phrase = "Not Found"
        response.content = b'{"error": "not found"}'
        response.text = '{"error": "not found"}'
        response.headers = Headers({"Content-Type": "application/json"})
        response.url = "https://api.example.com/test"
        response.is_success = False
        response.is_client_error = True
        response.is_server_error = False

        mock_func = AsyncMock(return_value=response)
        client = HTTPxClient.create("https://api.example.com")

        with pytest.raises(HTTPxError) as exc_info:
            await client.recv(mock_func, {"url": "https://api.example.com/test"})

        assert exc_info.value.status == 404

    @pytest.mark.asyncio
    async def test_recv_raises_on_server_error(self, mock_async_client):
        """Test that server error raises HTTPxError."""
        response = Mock(spec=Response)
        response.status_code = 500
        response.reason_phrase = "Internal Server Error"
        response.content = b"Server Error"
        response.text = "Server Error"
        response.headers = Headers({"Content-Type": "text/plain"})
        response.url = "https://api.example.com/test"
        response.is_success = False
        response.is_client_error = False
        response.is_server_error = True

        mock_func = AsyncMock(return_value=response)
        client = HTTPxClient.create("https://api.example.com")

        with pytest.raises(HTTPxError) as exc_info:
            await client.recv(mock_func, {"url": "https://api.example.com/test"})

        assert exc_info.value.status == 500

    @pytest.mark.asyncio
    async def test_recv_raises_on_unexpected_status(self, mock_async_client, mock_response):
        """Test that unexpected status raises HTTPxError."""
        mock_response.status_code = 201
        mock_response.is_success = True

        mock_func = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        with pytest.raises(HTTPxError) as exc_info:
            await client.recv(
                mock_func, {"url": "https://api.example.com/test"}, expect=200
            )

        assert exc_info.value.status == 201

    # catch method tests

    def test_catch_with_expected_status_match(self, mock_async_client):
        """Test catch returns None when expected status matches."""
        client = HTTPxClient.create("https://api.example.com")
        response = Mock(spec=Response)
        response.status_code = 200

        result = client.catch(response, (200, 201))

        assert result is None

    def test_catch_with_expected_status_no_match_and_error(self, mock_async_client):
        """Test catch returns exception when expected status doesn't match and it's an error."""
        client = HTTPxClient.create("https://api.example.com")
        response = Mock(spec=Response)
        response.status_code = 404
        response.reason_phrase = "Not Found"
        response.content = b"Not Found"
        response.text = "Not Found"
        response.headers = Headers({"Content-Type": "text/plain"})

        with patch("sdk.http.client.HTTPxError.catch") as mock_catch:
            mock_catch.return_value = HTTPxClientError(404, "Not Found", {})
            result = client.catch(response, (200,))

        assert isinstance(result, HTTPxClientError)

    def test_catch_with_expected_status_no_match_and_make_exception(self, mock_async_client):
        """Test catch creates exception when expected status doesn't match."""
        client = HTTPxClient.create("https://api.example.com")
        response = Mock(spec=Response)
        response.status_code = 418
        response.reason_phrase = "I'm a Teapot"
        response.content = b"I'm a Teapot"
        response.text = "I'm a Teapot"
        response.headers = Headers({"Content-Type": "text/plain"})
        response.is_client_error = True
        response.is_server_error = False

        result = client.catch(response, (200,))

        assert isinstance(result, HTTPxError)
        assert result.status == 418

    def test_catch_without_expect_and_success(self, mock_async_client):
        """Test catch returns None for successful response without expect."""
        client = HTTPxClient.create("https://api.example.com")
        response = Mock(spec=Response)
        response.status_code = 200
        response.is_client_error = False
        response.is_server_error = False

        result = client.catch(response, ())

        assert result is None

    def test_catch_without_expect_and_client_error(self, mock_async_client):
        """Test catch returns exception for client error without expect."""
        client = HTTPxClient.create("https://api.example.com")
        response = Mock(spec=Response)
        response.status_code = 400
        response.reason_phrase = "Bad Request"
        response.content = b"Bad Request"
        response.text = "Bad Request"
        response.headers = Headers({"Content-Type": "text/plain"})
        response.is_client_error = True
        response.is_server_error = False

        result = client.catch(response, ())

        assert isinstance(result, HTTPxClientError)

    def test_catch_without_expect_and_server_error(self, mock_async_client):
        """Test catch returns exception for server error without expect."""
        client = HTTPxClient.create("https://api.example.com")
        response = Mock(spec=Response)
        response.status_code = 500
        response.reason_phrase = "Internal Server Error"
        response.content = b"Server Error"
        response.text = "Server Error"
        response.headers = Headers({"Content-Type": "text/plain"})
        response.is_client_error = False
        response.is_server_error = True

        result = client.catch(response, ())

        assert isinstance(result, HTTPxServerError)

    # Convenience method tests

    @pytest.mark.asyncio
    async def test_get_method(self, mock_async_client, mock_response):
        """Test get convenience method."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.get("/users")

        assert isinstance(result, HTTPxResponse)
        mock_async_client[1].get.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_method(self, mock_async_client, mock_response):
        """Test post convenience method."""
        mock_async_client[1].post = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.post("/users", data={"name": "test"})

        assert isinstance(result, HTTPxResponse)
        mock_async_client[1].post.assert_called_once()

    @pytest.mark.asyncio
    async def test_put_method(self, mock_async_client, mock_response):
        """Test put convenience method."""
        mock_async_client[1].put = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.put("/users/1", data={"name": "test"})

        assert isinstance(result, HTTPxResponse)
        mock_async_client[1].put.assert_called_once()

    @pytest.mark.asyncio
    async def test_patch_method(self, mock_async_client, mock_response):
        """Test patch convenience method."""
        mock_async_client[1].patch = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.patch("/users/1", data={"name": "test"})

        assert isinstance(result, HTTPxResponse)
        mock_async_client[1].patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_method(self, mock_async_client, mock_response):
        """Test delete convenience method."""
        mock_async_client[1].delete = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com")

        result = await client.delete("/users/1")

        assert isinstance(result, HTTPxResponse)
        mock_async_client[1].delete.assert_called_once()

    # Headers tests

    def test_headers_property_returns_copy(self, mock_async_client):
        """Test that headers property returns a copy of class headers."""
        client = HTTPxClient.create("https://api.example.com")

        headers = client.headers

        assert headers is not HTTPxClient.Headers
        assert headers == HTTPxClient.Headers

    def test_headers_includes_default_values(self, mock_async_client):
        """Test that headers include default values."""
        client = HTTPxClient.create("https://api.example.com")

        headers = client.headers

        assert headers["Accept"] == "*/*"
        assert headers["Accept-Encoding"] == "br, gzip, deflate, zstd"

    def test_class_headers_unmodified_by_instance(self, mock_async_client):
        """Test that modifying instance headers doesn't affect class headers."""
        client = HTTPxClient.create("https://api.example.com")

        original_accept = HTTPxClient.Headers["Accept"]
        client.headers["Accept"] = "application/json"

        assert HTTPxClient.Headers["Accept"] == original_accept

    # ResponseClass and ExceptionClass tests

    def test_response_class_is_httpx_response(self, mock_async_client):
        """Test that ResponseClass is HTTPxResponse."""
        assert HTTPxClient.ResponseClass is HTTPxResponse

    def test_exception_class_is_httpx_error(self, mock_async_client):
        """Test that ExceptionClass is HTTPxError."""
        assert HTTPxClient.ExceptionClass is HTTPxError

    # Verbose logging tests

    @pytest.mark.asyncio
    async def test_verbose_logging_includes_full_data(self, mock_async_client, mock_response):
        """Test that verbose logging includes full request and response data."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com", verbose=True)

        with patch("sdk.http.client.logger") as mock_logger:
            await client.get("/users", data={"filter": "test"})

            # Check that data is logged
            send_call = [
                call for call in mock_logger.info.call_args_list
                if call.args[0] == "Sending request"
            ][0]
            logged_data = send_call.kwargs["extra"]["data"]
            assert logged_data == {"filter": "test"}

    @pytest.mark.asyncio
    async def test_non_verbose_logging_excludes_data(self, mock_async_client, mock_response):
        """Test that non-verbose logging excludes request data."""
        mock_async_client[1].get = AsyncMock(return_value=mock_response)
        client = HTTPxClient.create("https://api.example.com", verbose=False)

        with patch("sdk.http.client.logger") as mock_logger:
            await client.get("/users", data={"filter": "test"})

            # Check that data is not logged
            send_call = [
                call for call in mock_logger.info.call_args_list
                if call.args[0] == "Sending request"
            ][0]
            logged_data = send_call.kwargs["extra"]["data"]
            assert logged_data == {}

    # Error handling tests

    @pytest.mark.asyncio
    async def test_send_with_invalid_method_logs_exception(self, mock_async_client):
        """Test that invalid method logs exception."""
        client = HTTPxClient.create("https://api.example.com")
        invalid_method = Mock()
        invalid_method.value = "nonexistent"

        with patch("sdk.http.client.logger") as mock_logger:
            with pytest.raises(ValueError):
                await client.send(invalid_method, "/test")

            mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_recv_logs_exception_on_error(self, mock_async_client):
        """Test that recv logs exception details on error."""
        response = Mock(spec=Response)
        response.status_code = 404
        response.reason_phrase = "Not Found"
        response.content = b"Not Found"
        response.text = "Not Found"
        response.headers = Headers({"Content-Type": "text/plain"})
        response.url = "https://api.example.com/test"
        response.is_success = False
        response.is_client_error = True
        response.is_server_error = False

        mock_func = AsyncMock(return_value=response)
        client = HTTPxClient.create("https://api.example.com")

        with patch("sdk.http.client.logger") as mock_logger:
            with pytest.raises(HTTPxError):
                await client.recv(mock_func, {"url": "https://api.example.com/test"})

            # Should log warning about raising exception
            mock_logger.warning.assert_called_once()
