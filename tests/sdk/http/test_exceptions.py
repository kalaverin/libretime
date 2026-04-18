"""Tests for sdk.http.exceptions module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from httpx import Response
from starlette import status

from sdk.http.exceptions import (
    HTTPStatusesMixin,
    HTTPxClientError,
    HTTPxError,
    HTTPxServerError,
)


class TestHTTPStatusesMixin:
    """Tests for HTTPStatusesMixin class."""

    @pytest.fixture
    def mixin(self):
        """Create a test class with HTTPStatusesMixin."""

        class TestClass(HTTPStatusesMixin):
            def __init__(self, status):
                self.status = status

        return TestClass

    # Informational responses (1xx)

    def test_is_continue_true(self, mixin):
        """Test isContinue property returns True for 100."""
        obj = mixin(status.HTTP_100_CONTINUE)
        assert obj.isContinue is True

    def test_is_continue_false(self, mixin):
        """Test isContinue property returns False for non-100."""
        obj = mixin(200)
        assert obj.isContinue is False

    def test_is_switching_protocols_true(self, mixin):
        """Test isSwitchingProtocols property returns True for 101."""
        obj = mixin(status.HTTP_101_SWITCHING_PROTOCOLS)
        assert obj.isSwitchingProtocols is True

    def test_is_processing_true(self, mixin):
        """Test isProcessing property returns True for 102."""
        obj = mixin(status.HTTP_102_PROCESSING)
        assert obj.isProcessing is True

    def test_is_early_hints_true(self, mixin):
        """Test isEarlyHints property returns True for 103."""
        obj = mixin(status.HTTP_103_EARLY_HINTS)
        assert obj.isEarlyHints is True

    # Successful responses (2xx)

    def test_is_ok_true(self, mixin):
        """Test isOk property returns True for 200."""
        obj = mixin(status.HTTP_200_OK)
        assert obj.isOk is True

    def test_is_ok_false(self, mixin):
        """Test isOk property returns False for non-200."""
        obj = mixin(404)
        assert obj.isOk is False

    def test_is_created_true(self, mixin):
        """Test isCreated property returns True for 201."""
        obj = mixin(status.HTTP_201_CREATED)
        assert obj.isCreated is True

    def test_is_accepted_true(self, mixin):
        """Test isAccepted property returns True for 202."""
        obj = mixin(status.HTTP_202_ACCEPTED)
        assert obj.isAccepted is True

    def test_is_non_authoritative_information_true(self, mixin):
        """Test isNonAuthoritativeInformation property returns True for 203."""
        obj = mixin(status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        assert obj.isNonAuthoritativeInformation is True

    def test_is_no_content_true(self, mixin):
        """Test isNoContent property returns True for 204."""
        obj = mixin(status.HTTP_204_NO_CONTENT)
        assert obj.isNoContent is True

    def test_is_reset_content_true(self, mixin):
        """Test isResetContent property returns True for 205."""
        obj = mixin(status.HTTP_205_RESET_CONTENT)
        assert obj.isResetContent is True

    def test_is_partial_content_true(self, mixin):
        """Test isPartialContent property returns True for 206."""
        obj = mixin(status.HTTP_206_PARTIAL_CONTENT)
        assert obj.isPartialContent is True

    def test_is_multi_status_true(self, mixin):
        """Test isMultiStatus property returns True for 207."""
        obj = mixin(status.HTTP_207_MULTI_STATUS)
        assert obj.isMultiStatus is True

    def test_is_already_reported_true(self, mixin):
        """Test isAlreadyReported property returns True for 208."""
        obj = mixin(status.HTTP_208_ALREADY_REPORTED)
        assert obj.isAlreadyReported is True

    def test_is_im_used_true(self, mixin):
        """Test isImUsed property returns True for 226."""
        obj = mixin(status.HTTP_226_IM_USED)
        assert obj.isImUsed is True

    # Redirection messages (3xx)

    def test_is_multiple_choices_true(self, mixin):
        """Test isMultipleChoices property returns True for 300."""
        obj = mixin(status.HTTP_300_MULTIPLE_CHOICES)
        assert obj.isMultipleChoices is True

    def test_is_moved_permanently_true(self, mixin):
        """Test isMovedPermanently property returns True for 301."""
        obj = mixin(status.HTTP_301_MOVED_PERMANENTLY)
        assert obj.isMovedPermanently is True

    def test_is_found_true(self, mixin):
        """Test isFound property returns True for 302."""
        obj = mixin(status.HTTP_302_FOUND)
        assert obj.isFound is True

    def test_is_see_other_true(self, mixin):
        """Test isSeeOther property returns True for 303."""
        obj = mixin(status.HTTP_303_SEE_OTHER)
        assert obj.isSeeOther is True

    def test_is_not_modified_true(self, mixin):
        """Test isNotModified property returns True for 304."""
        obj = mixin(status.HTTP_304_NOT_MODIFIED)
        assert obj.isNotModified is True

    def test_is_use_proxy_true(self, mixin):
        """Test isUseProxy property returns True for 305."""
        obj = mixin(status.HTTP_305_USE_PROXY)
        assert obj.isUseProxy is True

    def test_is_reserved_true(self, mixin):
        """Test isReserved property returns True for 306."""
        obj = mixin(status.HTTP_306_RESERVED)
        assert obj.isReserved is True

    def test_is_temporary_redirect_true(self, mixin):
        """Test isTemporaryRedirect property returns True for 307."""
        obj = mixin(status.HTTP_307_TEMPORARY_REDIRECT)
        assert obj.isTemporaryRedirect is True

    def test_is_permanent_redirect_true(self, mixin):
        """Test isPermanentRedirect property returns True for 308."""
        obj = mixin(status.HTTP_308_PERMANENT_REDIRECT)
        assert obj.isPermanentRedirect is True

    # Client error responses (4xx)

    def test_is_bad_request_true(self, mixin):
        """Test isBadRequest property returns True for 400."""
        obj = mixin(status.HTTP_400_BAD_REQUEST)
        assert obj.isBadRequest is True

    def test_is_unauthorized_true(self, mixin):
        """Test isUnauthorized property returns True for 401."""
        obj = mixin(status.HTTP_401_UNAUTHORIZED)
        assert obj.isUnauthorized is True

    def test_is_payment_required_true(self, mixin):
        """Test isPaymentRequired property returns True for 402."""
        obj = mixin(status.HTTP_402_PAYMENT_REQUIRED)
        assert obj.isPaymentRequired is True

    def test_is_forbidden_true(self, mixin):
        """Test isForbidden property returns True for 403."""
        obj = mixin(status.HTTP_403_FORBIDDEN)
        assert obj.isForbidden is True

    def test_is_not_found_true(self, mixin):
        """Test isNotFound property returns True for 404."""
        obj = mixin(status.HTTP_404_NOT_FOUND)
        assert obj.isNotFound is True

    def test_is_method_not_allowed_true(self, mixin):
        """Test isMethodNotAllowed property returns True for 405."""
        obj = mixin(status.HTTP_405_METHOD_NOT_ALLOWED)
        assert obj.isMethodNotAllowed is True

    def test_is_not_acceptable_true(self, mixin):
        """Test isNotAcceptable property returns True for 406."""
        obj = mixin(status.HTTP_406_NOT_ACCEPTABLE)
        assert obj.isNotAcceptable is True

    def test_is_proxy_authentication_required_true(self, mixin):
        """Test isProxyAuthenticationRequired property returns True for 407."""
        obj = mixin(status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED)
        assert obj.isProxyAuthenticationRequired is True

    def test_is_request_timeout_true(self, mixin):
        """Test isRequestTimeout property returns True for 408."""
        obj = mixin(status.HTTP_408_REQUEST_TIMEOUT)
        assert obj.isRequestTimeout is True

    def test_is_conflict_true(self, mixin):
        """Test isConflict property returns True for 409."""
        obj = mixin(status.HTTP_409_CONFLICT)
        assert obj.isConflict is True

    def test_is_gone_true(self, mixin):
        """Test isGone property returns True for 410."""
        obj = mixin(status.HTTP_410_GONE)
        assert obj.isGone is True

    def test_is_length_required_true(self, mixin):
        """Test isLengthRequired property returns True for 411."""
        obj = mixin(status.HTTP_411_LENGTH_REQUIRED)
        assert obj.isLengthRequired is True

    def test_is_precondition_failed_true(self, mixin):
        """Test isPreconditionFailed property returns True for 412."""
        obj = mixin(status.HTTP_412_PRECONDITION_FAILED)
        assert obj.isPreconditionFailed is True

    def test_is_request_entity_too_large_true(self, mixin):
        """Test isRequestEntityTooLarge property returns True for 413."""
        obj = mixin(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        assert obj.isRequestEntityTooLarge is True

    def test_is_request_uri_too_long_true(self, mixin):
        """Test isRequestUriTooLong property returns True for 414."""
        obj = mixin(status.HTTP_414_REQUEST_URI_TOO_LONG)
        assert obj.isRequestUriTooLong is True

    def test_is_unsupported_media_type_true(self, mixin):
        """Test isUnsupportedMediaType property returns True for 415."""
        obj = mixin(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        assert obj.isUnsupportedMediaType is True

    def test_is_requested_range_not_satisfiable_true(self, mixin):
        """Test isRequestedRangeNotSatisfiable property returns True for 416."""
        obj = mixin(status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
        assert obj.isRequestedRangeNotSatisfiable is True

    def test_is_expectation_failed_true(self, mixin):
        """Test isExpectationFailed property returns True for 417."""
        obj = mixin(status.HTTP_417_EXPECTATION_FAILED)
        assert obj.isExpectationFailed is True

    def test_is_im_a_teapot_true(self, mixin):
        """Test isImATeapot property returns True for 418."""
        obj = mixin(status.HTTP_418_IM_A_TEAPOT)
        assert obj.isImATeapot is True

    def test_is_misdirected_request_true(self, mixin):
        """Test isMisdirectedRequest property returns True for 421."""
        obj = mixin(status.HTTP_421_MISDIRECTED_REQUEST)
        assert obj.isMisdirectedRequest is True

    def test_is_unprocessable_entity_true(self, mixin):
        """Test isUnprocessableEntity property returns True for 422."""
        obj = mixin(status.HTTP_422_UNPROCESSABLE_CONTENT)
        assert obj.isUnprocessableEntity is True

    def test_is_locked_true(self, mixin):
        """Test isLocked property returns True for 423."""
        obj = mixin(status.HTTP_423_LOCKED)
        assert obj.isLocked is True

    def test_is_failed_dependency_true(self, mixin):
        """Test isFailedDependency property returns True for 424."""
        obj = mixin(status.HTTP_424_FAILED_DEPENDENCY)
        assert obj.isFailedDependency is True

    def test_is_too_early_true(self, mixin):
        """Test isTooEarly property returns True for 425."""
        obj = mixin(status.HTTP_425_TOO_EARLY)
        assert obj.isTooEarly is True

    def test_is_upgrade_required_true(self, mixin):
        """Test isUpgradeRequired property returns True for 426."""
        obj = mixin(status.HTTP_426_UPGRADE_REQUIRED)
        assert obj.isUpgradeRequired is True

    def test_is_precondition_required_true(self, mixin):
        """Test isPreconditionRequired property returns True for 428."""
        obj = mixin(status.HTTP_428_PRECONDITION_REQUIRED)
        assert obj.isPreconditionRequired is True

    def test_is_too_many_requests_true(self, mixin):
        """Test isTooManyRequests property returns True for 429."""
        obj = mixin(status.HTTP_429_TOO_MANY_REQUESTS)
        assert obj.isTooManyRequests is True

    def test_is_request_header_fields_too_large_true(self, mixin):
        """Test isRequestHeaderFieldsTooLarge property returns True for 431."""
        obj = mixin(status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE)
        assert obj.isRequestHeaderFieldsTooLarge is True

    def test_is_unavailable_for_legal_reasons_true(self, mixin):
        """Test isUnavailableForLegalReasons property returns True for 451."""
        obj = mixin(status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)
        assert obj.isUnavailableForLegalReasons is True

    # Server error responses (5xx)

    def test_is_internal_server_error_true(self, mixin):
        """Test isInternalServerError property returns True for 500."""
        obj = mixin(status.HTTP_500_INTERNAL_SERVER_ERROR)
        assert obj.isInternalServerError is True

    def test_is_not_implemented_true(self, mixin):
        """Test isNotImplemented property returns True for 501."""
        obj = mixin(status.HTTP_501_NOT_IMPLEMENTED)
        assert obj.isNotImplemented is True

    def test_is_bad_gateway_true(self, mixin):
        """Test isBadGateway property returns True for 502."""
        obj = mixin(status.HTTP_502_BAD_GATEWAY)
        assert obj.isBadGateway is True

    def test_is_service_unavailable_true(self, mixin):
        """Test isServiceUnavailable property returns True for 503."""
        obj = mixin(status.HTTP_503_SERVICE_UNAVAILABLE)
        assert obj.isServiceUnavailable is True

    def test_is_gateway_timeout_true(self, mixin):
        """Test isGatewayTimeout property returns True for 504."""
        obj = mixin(status.HTTP_504_GATEWAY_TIMEOUT)
        assert obj.isGatewayTimeout is True

    def test_is_http_version_not_supported_true(self, mixin):
        """Test isHttpVersionNotSupported property returns True for 505."""
        obj = mixin(status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED)
        assert obj.isHttpVersionNotSupported is True

    def test_is_variant_also_negotiates_true(self, mixin):
        """Test isVariantAlsoNegotiates property returns True for 506."""
        obj = mixin(status.HTTP_506_VARIANT_ALSO_NEGOTIATES)
        assert obj.isVariantAlsoNegotiates is True

    def test_is_insufficient_storage_true(self, mixin):
        """Test isInsufficientStorage property returns True for 507."""
        obj = mixin(status.HTTP_507_INSUFFICIENT_STORAGE)
        assert obj.isInsufficientStorage is True

    def test_is_loop_detected_true(self, mixin):
        """Test isLoopDetected property returns True for 508."""
        obj = mixin(status.HTTP_508_LOOP_DETECTED)
        assert obj.isLoopDetected is True

    def test_is_not_extended_true(self, mixin):
        """Test isNotExtended property returns True for 510."""
        obj = mixin(status.HTTP_510_NOT_EXTENDED)
        assert obj.isNotExtended is True

    def test_is_network_authentication_required_true(self, mixin):
        """Test isNetworkAuthenticationRequired property returns True for 511."""
        obj = mixin(status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED)
        assert obj.isNetworkAuthenticationRequired is True


class TestHTTPxError:
    """Tests for HTTPxError exception class."""

    @pytest.fixture
    def mock_response_json(self):
        """Create a mock JSON response."""
        response = Mock(spec=Response)
        response.status_code = 400
        response.reason_phrase = "Bad Request"
        response.content = b'{"error": "test error"}'
        response.text = '{"error": "test error"}'
        response.headers = {"Content-Type": "application/json"}
        response.is_client_error = True
        response.is_server_error = False
        return response

    @pytest.fixture
    def mock_response_non_json(self):
        """Create a mock non-JSON response."""
        response = Mock(spec=Response)
        response.status_code = 500
        response.reason_phrase = "Internal Server Error"
        response.content = b"Server Error"
        response.text = "Server Error"
        response.headers = {"Content-Type": "text/plain"}
        response.is_client_error = False
        response.is_server_error = True
        return response

    def test_init_basic(self):
        """Test basic initialization of HTTPxError."""
        error = HTTPxError(404, "Not Found", {"detail": "not found"})

        assert error.status == 404
        assert error.reason == "Not Found"
        assert error.data == {"detail": "not found"}
        assert error.description is None

    def test_init_with_description(self):
        """Test initialization with description."""
        error = HTTPxError(
            500,
            "Internal Server Error",
            {"error": "server error"},
            description="Something went wrong",
        )

        assert error.description == "Something went wrong"

    def test_init_exception_args(self):
        """Test that exception args are set correctly."""
        error = HTTPxError(404, "Not Found", {}, "description")

        # Exception args should be (description, status)
        assert error.args == ("description", 404)

    def test_str_method(self):
        """Test __str__ method returns message."""
        error = HTTPxError(404, "Not Found", {})

        assert str(error) == error.message

    def test_message_without_description(self):
        """Test message property without description."""
        error = HTTPxError(200, "OK", {})

        assert error.message == "200 OK"

    def test_message_with_description(self):
        """Test message property with description."""
        error = HTTPxError(404, "Not Found", {}, description="User not found")

        assert error.message == "404 Not Found: User not found"

    def test_message_capitalizes_lowercase_reason(self):
        """Test message property capitalizes lowercase reason."""
        error = HTTPxError(404, "notfound", {})

        assert error.message == "404 Notfound"

    def test_message_does_not_modify_mixed_case_reason(self):
        """Test message property does not modify mixed case reason."""
        error = HTTPxError(404, "NotFound", {})

        # Should not capitalize since it has uppercase letters
        assert error.message == "404 NotFound"

    def test_as_dict_property(self):
        """Test as_dict property returns correct dictionary."""
        error = HTTPxError(404, "Not Found", {"error": "test"}, "description")
        result = error.as_dict

        assert result["status"] == 404
        assert result["reason"] == "Not Found"
        assert result["data"] == {"error": "test"}
        assert result["description"] == "description"
        assert result["message"] == "404 Not Found: description"

    def test_as_json_property(self):
        """Test as_json property returns valid JSON string."""
        import orjson

        error = HTTPxError(404, "Not Found", {"error": "test"})
        result = error.as_json

        # Should be valid JSON
        parsed = orjson.loads(result)
        assert parsed["status"] == 404
        assert parsed["reason"] == "Not Found"

    @patch("sdk.http.exceptions.is_json_response")
    @patch("sdk.http.exceptions.read_json_from_response")
    def test_make_from_json_response(
        self, mock_read_json, mock_is_json, mock_response_json
    ):
        """Test make_from with JSON response."""
        mock_is_json.return_value = True
        mock_read_json.return_value = {"error": "test error"}

        error = HTTPxError.make_from(mock_response_json)

        assert error.status == 400
        assert error.reason == "Bad Request"
        assert error.data == {"error": "test error"}

    @patch("sdk.http.exceptions.is_json_response")
    def test_make_from_non_json_response(self, mock_is_json, mock_response_non_json):
        """Test make_from with non-JSON response."""
        mock_is_json.return_value = False

        error = HTTPxError.make_from(mock_response_non_json)

        assert error.status == 500
        assert error.data == b"Server Error"

    @patch("sdk.http.exceptions.is_json_response")
    def test_make_from_with_custom_class(self, mock_is_json, mock_response_json):
        """Test make_from with custom exception class."""
        mock_is_json.return_value = True

        class CustomError(HTTPxError):
            pass

        with patch(
            "sdk.http.exceptions.read_json_from_response"
        ) as mock_read_json:
            mock_read_json.return_value = {"error": "test"}
            error = HTTPxError.make_from(mock_response_json, klass=CustomError)

        assert isinstance(error, CustomError)

    @patch("sdk.http.exceptions.is_json_response")
    def test_make_from_with_custom_description(self, mock_is_json, mock_response_json):
        """Test make_from with custom description."""
        mock_is_json.return_value = True

        with patch(
            "sdk.http.exceptions.read_json_from_response"
        ) as mock_read_json:
            mock_read_json.return_value = {"error": "test"}
            error = HTTPxError.make_from(
                mock_response_json, description="Custom description"
            )

        assert error.description == "Custom description"

    def test_catch_returns_none_for_success(self):
        """Test catch returns None for successful response."""
        response = Mock(spec=Response)
        response.status_code = 200
        response.is_client_error = False
        response.is_server_error = False

        result = HTTPxError.catch(response)

        assert result is None

    def test_catch_returns_client_error_for_4xx(self, mock_response_json):
        """Test catch returns HTTPxClientError for 4xx response."""
        with patch("sdk.http.exceptions.is_json_response") as mock_is_json:
            mock_is_json.return_value = True
            with patch(
                "sdk.http.exceptions.read_json_from_response"
            ) as mock_read_json:
                mock_read_json.return_value = {"error": "test"}
                result = HTTPxError.catch(mock_response_json)

        assert isinstance(result, HTTPxClientError)
        assert result.status == 400

    def test_catch_returns_server_error_for_5xx(self, mock_response_non_json):
        """Test catch returns HTTPxServerError for 5xx response."""
        with patch("sdk.http.exceptions.is_json_response") as mock_is_json:
            mock_is_json.return_value = False
            result = HTTPxError.catch(mock_response_non_json)

        assert isinstance(result, HTTPxServerError)
        assert result.status == 500


class TestHTTPxClientError:
    """Tests for HTTPxClientError exception class."""

    def test_is_subclass_of_httpx_error(self):
        """Test HTTPxClientError is subclass of HTTPxError."""
        assert issubclass(HTTPxClientError, HTTPxError)

    def test_basic_usage(self):
        """Test basic usage of HTTPxClientError."""
        error = HTTPxClientError(404, "Not Found", {"error": "not found"})

        assert error.status == 404
        assert error.isNotFound is True


class TestHTTPxServerError:
    """Tests for HTTPxServerError exception class."""

    def test_is_subclass_of_httpx_error(self):
        """Test HTTPxServerError is subclass of HTTPxError."""
        assert issubclass(HTTPxServerError, HTTPxError)

    def test_basic_usage(self):
        """Test basic usage of HTTPxServerError."""
        error = HTTPxServerError(500, "Internal Server Error", {"error": "oops"})

        assert error.status == 500
        assert error.isInternalServerError is True
