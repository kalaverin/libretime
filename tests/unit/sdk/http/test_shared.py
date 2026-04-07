"""Tests for sdk.http.shared module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from httpx import Headers, Response

from sdk.http.shared import (
    JSONType,
    MIME_JSON,
    OPT_JSON_FLAGS,
    is_json_response,
    read_json_from_response,
    to_builtin,
    to_json,
)


class TestToBuiltin:
    """Tests for to_builtin function."""

    def test_converts_httpx_headers_to_dict(self):
        """Test that httpx Headers are converted to dict."""
        headers = Headers({
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        })

        result = to_builtin(headers)

        assert isinstance(result, dict)
        assert result["Content-Type"] == "application/json"
        assert result["Authorization"] == "Bearer token"

    def test_handles_duplicate_header_values(self):
        """Test handling of duplicate header values."""
        # httpx Headers can have multiple values for same key
        headers = Headers([
            ("Accept", "application/json"),
            ("Accept", "text/html"),
        ])

        result = to_builtin(headers)

        assert isinstance(result["Accept"], tuple)
        assert result["Accept"] == ("application/json", "text/html")

    def test_handles_single_value_as_string(self):
        """Test that single values are returned as strings."""
        headers = Headers({"Content-Type": "application/json"})

        result = to_builtin(headers)

        assert result["Content-Type"] == "application/json"

    def test_raises_not_implemented_for_unsupported_types(self):
        """Test that unsupported types raise NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            to_builtin(123)

        assert "unsupported type" in str(exc_info.value)

    def test_raises_not_implemented_for_custom_class(self):
        """Test that custom classes raise NotImplementedError."""
        class CustomClass:
            pass

        with pytest.raises(NotImplementedError):
            to_builtin(CustomClass())

    def test_logs_exception_on_unsupported_type(self):
        """Test that exception is logged for unsupported types."""
        with patch("sdk.http.shared.logger") as mock_logger:
            with pytest.raises(NotImplementedError):
                to_builtin(object())

            mock_logger.exception.assert_called_once()


class TestToJson:
    """Tests for to_json function."""

    def test_returns_string_unchanged(self):
        """Test that string input is returned unchanged."""
        input_str = '{"key": "value"}'

        result = to_json(input_str)

        assert result == input_str

    def test_decodes_bytes_to_string(self):
        """Test that bytes input is decoded to string."""
        input_bytes = b'{"key": "value"}'

        result = to_json(input_bytes)

        assert result == '{"key": "value"}'

    def test_serializes_dict_to_json(self):
        """Test that dict is serialized to JSON string."""
        data = {"key": "value", "number": 42}

        result = to_json(data)

        # Parse to verify valid JSON
        import orjson
        parsed = orjson.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_serializes_list_to_json(self):
        """Test that list is serialized to JSON string."""
        data = [1, 2, 3, "test"]

        result = to_json(data)

        import orjson
        parsed = orjson.loads(result)
        assert parsed == [1, 2, 3, "test"]

    def test_serializes_nested_structure(self):
        """Test that nested structures are serialized correctly."""
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            "meta": {"total": 2},
        }

        result = to_json(data)

        import orjson
        parsed = orjson.loads(result)
        assert len(parsed["users"]) == 2
        assert parsed["meta"]["total"] == 2

    def test_uses_to_builtin_for_special_types(self):
        """Test that to_builtin is used for special types like Headers."""
        headers = Headers({"Content-Type": "application/json"})

        result = to_json({"headers": headers})

        import orjson
        parsed = orjson.loads(result)
        assert parsed["headers"]["Content-Type"] == "application/json"

    def test_sorts_keys(self):
        """Test that JSON keys are sorted."""
        data = {"z": 1, "a": 2, "m": 3}

        result = to_json(data)

        # Keys should be sorted: a, m, z
        assert result.index("a") < result.index("m") < result.index("z")

    def test_handles_none(self):
        """Test that None is serialized correctly."""
        result = to_json(None)

        assert result == "null"

    def test_handles_numbers(self):
        """Test that numbers are serialized correctly."""
        assert to_json(42) == "42"
        assert to_json(3.14) == "3.14"

    def test_handles_booleans(self):
        """Test that booleans are serialized correctly."""
        assert to_json(True) == "true"
        assert to_json(False) == "false"

    def test_handles_empty_dict(self):
        """Test that empty dict is serialized correctly."""
        result = to_json({})

        assert result == "{}"

    def test_handles_empty_list(self):
        """Test that empty list is serialized correctly."""
        result = to_json([])

        assert result == "[]"


class TestIsJsonResponse:
    """Tests for is_json_response function."""

    def test_returns_true_for_application_json(self):
        """Test returns True for application/json content type."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}

        result = is_json_response(response)

        assert result is True

    def test_returns_true_for_application_json_with_charset(self):
        """Test returns True for application/json with charset."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json; charset=utf-8"}

        result = is_json_response(response)

        assert result is True

    def test_returns_false_for_text_plain(self):
        """Test returns False for text/plain content type."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "text/plain"}

        result = is_json_response(response)

        assert result is False

    def test_returns_false_for_missing_content_type(self):
        """Test returns False when Content-Type is missing."""
        response = Mock(spec=Response)
        response.headers = {}

        result = is_json_response(response)

        assert result is False

    def test_returns_false_for_none_content_type(self):
        """Test returns False when Content-Type is None."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": None}

        result = is_json_response(response)

        assert result is False

    def test_returns_true_for_json_subtype(self):
        """Test returns True for JSON subtype like application/ld+json."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/ld+json"}

        result = is_json_response(response)

        assert result is True

    def test_case_insensitive_check(self):
        """Test that check is case insensitive."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "APPLICATION/JSON"}

        result = is_json_response(response)

        assert result is True


class TestReadJsonFromResponse:
    """Tests for read_json_from_response function."""

    def test_parses_valid_json_response(self):
        """Test parsing valid JSON from response."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'{"key": "value"}'

        result = read_json_from_response(response)

        assert result == {"key": "value"}

    def test_parses_json_list(self):
        """Test parsing JSON list from response."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'[1, 2, 3]'

        result = read_json_from_response(response)

        assert result == [1, 2, 3]

    def test_parses_json_with_force_flag(self):
        """Test parsing JSON with force flag even if content type is wrong."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "text/plain"}
        response.content = b'{"key": "value"}'

        result = read_json_from_response(response, force=True)

        assert result == {"key": "value"}

    def test_raises_value_error_for_invalid_json(self):
        """Test raising ValueError for invalid JSON."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'not valid json'

        with pytest.raises(ValueError) as exc_info:
            read_json_from_response(response)

        assert "expected JSON, but isn't" in str(exc_info.value)

    def test_raises_value_error_for_non_json_content_type(self):
        """Test raising ValueError for non-JSON content type."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "text/plain"}
        response.content = b'some text'

        with pytest.raises(ValueError) as exc_info:
            read_json_from_response(response)

        assert "it's not a JSON response" in str(exc_info.value)

    def test_raises_value_error_with_original_exception(self):
        """Test that original exception is preserved in chain."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'invalid{'

        with pytest.raises(ValueError) as exc_info:
            read_json_from_response(response)

        # Check that the original exception is in the chain
        assert exc_info.value.__cause__ is not None

    def test_handles_empty_json_object(self):
        """Test handling of empty JSON object."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'{}'

        result = read_json_from_response(response)

        assert result == {}

    def test_handles_null(self):
        """Test handling of null JSON value."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'null'

        result = read_json_from_response(response)

        assert result is None

    def test_handles_string(self):
        """Test handling of string JSON value."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'"test string"'

        result = read_json_from_response(response)

        assert result == "test string"

    def test_handles_number(self):
        """Test handling of number JSON value."""
        response = Mock(spec=Response)
        response.headers = {"Content-Type": "application/json"}
        response.content = b'42'

        result = read_json_from_response(response)

        assert result == 42


class TestConstants:
    """Tests for module constants."""

    def test_mime_json_constant(self):
        """Test MIME_JSON constant value."""
        assert MIME_JSON == "application/json"

    def test_opt_json_flags_exists(self):
        """Test OPT_JSON_FLAGS constant exists."""
        # Should be a combination of orjson options
        assert isinstance(OPT_JSON_FLAGS, int)

    def test_json_type_alias(self):
        """Test JSONType type alias exists."""
        # JSONType should be a Union type including common JSON values
        # We can't directly test the type alias, but we can verify it works
        def accepts_json_type(value: JSONType) -> JSONType:
            return value

        # These should all be valid
        accepts_json_type(None)
        accepts_json_type("string")
        accepts_json_type(42)
        accepts_json_type(3.14)
        accepts_json_type([1, 2, 3])
        accepts_json_type({"key": "value"})
