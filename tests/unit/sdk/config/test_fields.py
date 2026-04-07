"""Unit tests for sdk.config._fields module."""

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from sdk.config._fields import (
    AnyHttpUrlStr,
    AnyUrlStr,
    StrNoLeadingSlash,
    StrNoTrailingSlash,
)


# =============================================================================
# Tests for StrNoTrailingSlash
# =============================================================================


class TestStrNoTrailingSlash:
    """Tests for StrNoTrailingSlash type."""

    def test_string_without_trailing_slash(self):
        """Test string without trailing slash remains unchanged."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("hello")
        assert result == "hello"

    def test_string_with_single_trailing_slash(self):
        """Test single trailing slash is removed."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("hello/")
        assert result == "hello"

    def test_string_with_multiple_trailing_slashes(self):
        """Test multiple trailing slashes are all removed."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("hello//")
        assert result == "hello"

    def test_string_with_many_trailing_slashes(self):
        """Test many trailing slashes are all removed."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("path///")
        assert result == "path"

    def test_only_slashes(self):
        """Test string of only slashes becomes empty."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("///")
        assert result == ""

    def test_empty_string(self):
        """Test empty string remains empty."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("")
        assert result == ""

    def test_single_slash(self):
        """Test single slash becomes empty."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("/")
        assert result == ""

    def test_path_with_internal_and_trailing_slash(self):
        """Test path with internal slash keeps internal, removes trailing."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("path/to/file/")
        assert result == "path/to/file"

    def test_url_like_path(self):
        """Test URL-like path has trailing slash removed."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("http://example.com/path/")
        assert result == "http://example.com/path"

    def test_in_pydantic_model(self):
        """Test StrNoTrailingSlash works in a Pydantic model."""

        class Config(BaseModel):
            path: StrNoTrailingSlash

        config = Config(path="/some/path//")
        assert config.path == "/some/path"

    def test_none_value_raises_error(self):
        """Test that None value raises validation error."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        with pytest.raises(ValidationError):
            adapter.validate_python(None)

    def test_integer_value_converted(self):
        """Test that integer is converted to string and processed."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        # AfterValidator uses str(x), so 123 becomes "123"
        result = adapter.validate_python(123)
        assert result == "123"

    def test_whitespace_only_string(self):
        """Test whitespace-only string (doesn't have trailing slash)."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        result = adapter.validate_python("   ")
        assert result == "   "


# =============================================================================
# Tests for StrNoLeadingSlash
# =============================================================================


class TestStrNoLeadingSlash:
    """Tests for StrNoLeadingSlash type."""

    def test_string_without_leading_slash(self):
        """Test string without leading slash remains unchanged."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("hello")
        assert result == "hello"

    def test_string_with_single_leading_slash(self):
        """Test single leading slash is removed."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("/hello")
        assert result == "hello"

    def test_string_with_multiple_leading_slashes(self):
        """Test multiple leading slashes are all removed."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("//hello")
        assert result == "hello"

    def test_string_with_many_leading_slashes(self):
        """Test many leading slashes are all removed."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("///path")
        assert result == "path"

    def test_only_slashes(self):
        """Test string of only slashes becomes empty."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("///")
        assert result == ""

    def test_empty_string(self):
        """Test empty string remains empty."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("")
        assert result == ""

    def test_single_slash(self):
        """Test single slash becomes empty."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("/")
        assert result == ""

    def test_path_with_internal_and_leading_slash(self):
        """Test path with internal slash keeps internal, removes leading."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("/path/to/file")
        assert result == "path/to/file"

    def test_path_with_both_leading_and_trailing(self):
        """Test path with both - only leading is removed by this type."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        result = adapter.validate_python("/path/to/file/")
        assert result == "path/to/file/"

    def test_in_pydantic_model(self):
        """Test StrNoLeadingSlash works in a Pydantic model."""

        class Config(BaseModel):
            mount: StrNoLeadingSlash

        config = Config(mount="//mount/point")
        assert config.mount == "mount/point"

    def test_none_value_raises_error(self):
        """Test that None value raises validation error."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        with pytest.raises(ValidationError):
            adapter.validate_python(None)


# =============================================================================
# Tests for AnyUrlStr
# =============================================================================


class TestAnyUrlStr:
    """Tests for AnyUrlStr type."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        result = AnyUrlStr("http://example.com")
        assert str(result) == "http://example.com"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        result = AnyUrlStr("https://example.com")
        assert str(result) == "https://example.com"

    def test_url_with_port(self):
        """Test URL with port."""
        result = AnyUrlStr("http://localhost:8080")
        assert str(result) == "http://localhost:8080"
        assert result.port == 8080

    def test_url_with_path(self):
        """Test URL with path."""
        result = AnyUrlStr("http://example.com/path/to/resource")
        assert str(result) == "http://example.com/path/to/resource"
        assert result.path == "/path/to/resource"

    def test_url_with_trailing_slash_stripped(self):
        """Test that trailing slash is stripped."""
        result = AnyUrlStr("http://example.com/path/")
        assert str(result) == "http://example.com/path"

    def test_url_with_query_string(self):
        """Test URL with query string."""
        result = AnyUrlStr("http://example.com?key=value")
        assert str(result) == "http://example.com/?key=value"

    def test_url_with_username_password(self):
        """Test URL with username and password."""
        result = AnyUrlStr("http://user:pass@example.com")
        assert str(result) == "http://user:pass@example.com"

    def test_ftp_url(self):
        """Test FTP URL is valid."""
        result = AnyUrlStr("ftp://files.example.com")
        assert str(result) == "ftp://files.example.com"

    def test_file_url(self):
        """Test file URL is valid."""
        result = AnyUrlStr("file:///path/to/file")
        assert str(result) == "file:///path/to/file"

    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises error."""
        with pytest.raises(ValidationError):
            AnyUrlStr("not a url")

    def test_invalid_url_scheme(self):
        """Test URL with invalid scheme raises error."""
        with pytest.raises(ValidationError):
            AnyUrlStr("unknown://example.com")

    def test_empty_string_raises_error(self):
        """Test that empty string raises error."""
        with pytest.raises(ValidationError):
            AnyUrlStr("")

    def test_url_properties(self):
        """Test that URL properties are accessible."""
        result = AnyUrlStr("https://user:pass@example.com:8080/path")
        assert result.scheme == "https"
        assert result.host == "example.com"
        assert result.port == 8080
        assert result.path == "/path"

    def test_url_repr(self):
        """Test URL repr format."""
        result = AnyUrlStr("http://example.com")
        assert repr(result) == "AnyUrlStr('http://example.com')"

    def test_url_subclass_of_str(self):
        """Test that AnyUrlStr is a subclass of str."""
        result = AnyUrlStr("http://example.com")
        assert isinstance(result, str)

    def test_url_obj_attribute(self):
        """Test that the underlying URL object is accessible."""
        result = AnyUrlStr("http://example.com")
        assert hasattr(result, "obj")
        # The obj is a pydantic AnyUrl object
        assert result.obj is not None

    def test_in_pydantic_model(self):
        """Test AnyUrlStr works in a Pydantic model."""

        class Config(BaseModel):
            endpoint: AnyUrlStr

        config = Config(endpoint="http://api.example.com")
        assert str(config.endpoint) == "http://api.example.com"

    def test_in_pydantic_model_validation_error(self):
        """Test validation error in Pydantic model."""

        class Config(BaseModel):
            endpoint: AnyUrlStr

        with pytest.raises(ValidationError):
            Config(endpoint="invalid url")

    def test_url_idempotency(self):
        """Test that wrapping AnyUrlStr in AnyUrlStr works."""
        first = AnyUrlStr("http://example.com")
        second = AnyUrlStr(str(first))
        assert str(first) == str(second)


# =============================================================================
# Tests for AnyHttpUrlStr
# =============================================================================


class TestAnyHttpUrlStr:
    """Tests for AnyHttpUrlStr type."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        result = AnyHttpUrlStr("http://example.com")
        assert str(result) == "http://example.com"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        result = AnyHttpUrlStr("https://example.com")
        assert str(result) == "https://example.com"

    def test_url_with_path(self):
        """Test URL with path."""
        result = AnyHttpUrlStr("https://example.com/api/v1")
        assert str(result) == "https://example.com/api/v1"

    def test_url_with_trailing_slash_stripped(self):
        """Test that trailing slash is stripped."""
        result = AnyHttpUrlStr("https://example.com/api/")
        assert str(result) == "https://example.com/api"

    def test_invalid_ftp_url_raises_error(self):
        """Test that FTP URL raises error (not HTTP/HTTPS)."""
        with pytest.raises(ValidationError):
            AnyHttpUrlStr("ftp://files.example.com")

    def test_invalid_file_url_raises_error(self):
        """Test that file URL raises error (not HTTP/HTTPS)."""
        with pytest.raises(ValidationError):
            AnyHttpUrlStr("file:///path/to/file")

    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises error."""
        with pytest.raises(ValidationError):
            AnyHttpUrlStr("not a url")

    def test_url_properties(self):
        """Test that URL properties are accessible."""
        result = AnyHttpUrlStr("https://example.com:8443/path")
        assert result.scheme == "https"
        assert result.host == "example.com"
        assert result.port == 8443
        assert result.path == "/path"

    def test_url_repr(self):
        """Test URL repr format."""
        result = AnyHttpUrlStr("https://example.com")
        assert repr(result) == "AnyHttpUrlStr('https://example.com')"

    def test_url_subclass_of_str(self):
        """Test that AnyHttpUrlStr is a subclass of str."""
        result = AnyHttpUrlStr("https://example.com")
        assert isinstance(result, str)

    def test_url_subclass_of_anyurlstr(self):
        """Test that AnyHttpUrlStr is a subclass of AnyUrlStr."""
        result = AnyHttpUrlStr("https://example.com")
        assert isinstance(result, AnyUrlStr)

    def test_in_pydantic_model(self):
        """Test AnyHttpUrlStr works in a Pydantic model."""

        class Config(BaseModel):
            api_url: AnyHttpUrlStr

        config = Config(api_url="https://api.example.com")
        assert str(config.api_url) == "https://api.example.com"

    def test_localhost_url(self):
        """Test localhost URL is valid."""
        result = AnyHttpUrlStr("http://localhost:8080")
        assert str(result) == "http://localhost:8080"
        assert result.host == "localhost"

    def test_ip_address_url(self):
        """Test IP address URL is valid."""
        result = AnyHttpUrlStr("http://192.168.1.1:3000")
        assert str(result) == "http://192.168.1.1:3000"
        assert result.host == "192.168.1.1"

    def test_url_with_subdomain(self):
        """Test URL with subdomain."""
        result = AnyHttpUrlStr("https://api.subdomain.example.com")
        assert str(result) == "https://api.subdomain.example.com"

    def test_url_with_complex_path(self):
        """Test URL with complex path."""
        result = AnyHttpUrlStr("https://example.com/api/v1/users/123")
        assert str(result) == "https://example.com/api/v1/users/123"


# =============================================================================
# Integration tests with TypeAdapter
# =============================================================================


class TestFieldsWithTypeAdapter:
    """Integration tests using TypeAdapter."""

    def test_str_no_trailing_slash_via_adapter(self):
        """Test StrNoTrailingSlash via TypeAdapter."""
        adapter = TypeAdapter(StrNoTrailingSlash)
        assert adapter.validate_python("test/") == "test"
        assert adapter.dump_python("test") == "test"  # No trailing slash

    def test_str_no_leading_slash_via_adapter(self):
        """Test StrNoLeadingSlash via TypeAdapter."""
        adapter = TypeAdapter(StrNoLeadingSlash)
        assert adapter.validate_python("/test") == "test"

    def test_any_url_str_via_adapter(self):
        """Test AnyUrlStr via TypeAdapter."""
        adapter = TypeAdapter(AnyUrlStr)
        result = adapter.validate_python("http://example.com")
        assert str(result) == "http://example.com"

    def test_any_http_url_str_via_adapter(self):
        """Test AnyHttpUrlStr via TypeAdapter."""
        adapter = TypeAdapter(AnyHttpUrlStr)
        result = adapter.validate_python("https://example.com")
        assert str(result) == "https://example.com"

    def test_any_http_url_str_rejects_ftp_via_adapter(self):
        """Test AnyHttpUrlStr rejects FTP via TypeAdapter."""
        adapter = TypeAdapter(AnyHttpUrlStr)
        with pytest.raises(ValidationError):
            adapter.validate_python("ftp://example.com")


# =============================================================================
# Tests for JSON Schema generation
# =============================================================================


class TestJsonSchema:
    """Tests for JSON schema generation from field types."""

    def test_any_url_str_json_schema(self):
        """Test JSON schema for AnyUrlStr has uri format."""

        class Config(BaseModel):
            url: AnyUrlStr

        schema = Config.model_json_schema()
        assert schema["properties"]["url"]["format"] == "uri"

    def test_any_http_url_str_json_schema(self):
        """Test JSON schema for AnyHttpUrlStr has uri format."""

        class Config(BaseModel):
            url: AnyHttpUrlStr

        schema = Config.model_json_schema()
        assert schema["properties"]["url"]["format"] == "uri"

    def test_str_no_trailing_slash_no_special_format(self):
        """Test StrNoTrailingSlash doesn't add special format."""

        class Config(BaseModel):
            path: StrNoTrailingSlash

        schema = Config.model_json_schema()
        # Should be a regular string
        assert schema["properties"]["path"]["type"] == "string"
        assert "format" not in schema["properties"]["path"]

    def test_str_no_leading_slash_no_special_format(self):
        """Test StrNoLeadingSlash doesn't add special format."""

        class Config(BaseModel):
            mount: StrNoLeadingSlash

        schema = Config.model_json_schema()
        assert schema["properties"]["mount"]["type"] == "string"
        assert "format" not in schema["properties"]["mount"]
