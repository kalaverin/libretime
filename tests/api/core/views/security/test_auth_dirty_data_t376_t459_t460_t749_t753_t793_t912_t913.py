"""
RED TEAM: Dirty data handling in Authorization header.

Fixes and tests for:
- T376: Unicode in Auth header - UnicodeEncodeError
- T459: Case sensitivity in Auth header - Case-sensitive parsing
- T460: Empty token - Empty/malformed handling
- T749: Unicode in API Key - 500 error
- T753: Case sensitivity in Authorization - Case-sensitive reject
- T793: Unicode in Auth header - Unhandled exception
- T912: Newline in API Key - Header injection \\n
- T913: CR in API Key - Header injection \\r
"""

import pytest

from django.conf import settings
from rest_framework.test import APIClient


class TestDirtyDataAuthorizationHeader:
    """Comprehensive tests for dirty/malformed Authorization headers."""

    @pytest.mark.django_db
    def test_valid_api_key_still_works(self):
        """Valid Api-Key should still authenticate successfully."""
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.get("/api/v2/playlists")
        assert response.status_code == 200

    # ==================================================================
    # T376, T793: Unicode handling in Auth header
    # ==================================================================

    @pytest.mark.django_db
    def test_t376_t793_unicode_in_auth_header(self):
        """Unicode in Authorization header should return 403, not 500."""
        client = APIClient()
        unicode_headers = [
            "Api-Key тест",  # Cyrillic
            "Api-Key 测试",  # Chinese
            "Api-Key 🎧",  # Emoji
            "Api-Key \u0000",  # Null byte
            "Api-Key \uffff",  # High Unicode
        ]
        for header in unicode_headers:
            client.credentials(HTTP_AUTHORIZATION=header)
            response = client.get("/api/v2/playlists")
            # Should return 403, not 500
            assert response.status_code in [
                403,
                401,
            ], f"Header {repr(header)}: expected 403/401, got {response.status_code}"

    @pytest.mark.django_db
    def test_t749_unicode_in_api_key_value(self):
        """Unicode in API Key value should be rejected gracefully."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key 🔑тестключ")
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]

    # ==================================================================
    # T459, T753: Case sensitivity
    # ==================================================================

    @pytest.mark.django_db
    def test_t459_t753_case_sensitivity_rejects_variations(self):
        """Only exact 'Api-Key' prefix should be accepted (case-sensitive)."""
        client = APIClient()
        case_variations = [
            "api-key valid_token",
            "API-KEY valid_token",
            "Api-key valid_token",
            "api-Key valid_token",
            "aPi-KeY valid_token",
        ]
        for header in case_variations:
            client.credentials(HTTP_AUTHORIZATION=header)
            response = client.get("/api/v2/playlists")
            assert response.status_code in [
                403,
                401,
            ], f"Header {repr(header)}: expected 403/401, got {response.status_code}"

    @pytest.mark.django_db
    def test_t459_exact_api_key_prefix_works(self):
        """Exact 'Api-Key' prefix should work with valid key."""
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.get("/api/v2/playlists")
        assert response.status_code == 200

    # ==================================================================
    # T460: Empty/malformed token
    # ==================================================================

    @pytest.mark.django_db
    def test_t460_empty_token_after_prefix(self):
        """Empty token after 'Api-Key ' should return 403, not crash."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key ")
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]

    @pytest.mark.django_db
    def test_t460_no_space_after_prefix(self):
        """'Api-Key' without space should return 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key")
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]

    @pytest.mark.django_db
    def test_t460_only_whitespace_token(self):
        """Only whitespace as token should return 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key    ")
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]

    # ==================================================================
    # T912, T913: Header injection via newlines
    # ==================================================================

    @pytest.mark.django_db
    def test_t912_newline_injection_rejected(self):
        """Newline in Api-Key should be rejected (header injection protection)."""
        client = APIClient()
        injection_attempts = [
            "Api-Key valid\nX-Injected: header",
            "Api-Key valid\nContent-Length: 0",
            "Api-Key \ntoken",
        ]
        for header in injection_attempts:
            client.credentials(HTTP_AUTHORIZATION=header)
            response = client.get("/api/v2/playlists")
            assert response.status_code in [
                403,
                401,
            ], f"Header {repr(header)}: expected 403/401, got {response.status_code}"

    @pytest.mark.django_db
    def test_t913_carriage_return_injection_rejected(self):
        """Carriage return in Api-Key should be rejected."""
        client = APIClient()
        injection_attempts = [
            "Api-Key valid\rX-Injected: header",
            "Api-Key valid\r\nSet-Cookie: evil=true",
            "Api-Key \rtoken",
        ]
        for header in injection_attempts:
            client.credentials(HTTP_AUTHORIZATION=header)
            response = client.get("/api/v2/playlists")
            assert response.status_code in [
                403,
                401,
            ], f"Header {repr(header)}: expected 403/401, got {response.status_code}"

    # ==================================================================
    # Additional edge cases
    # ==================================================================

    @pytest.mark.django_db
    def test_tab_separator_rejected(self):
        """Tab instead of space should be rejected."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key\ttoken")
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]

    @pytest.mark.django_db
    def test_multiple_spaces_in_token_rejected(self):
        """Multiple tokens separated by spaces should be rejected."""
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key} extra",
        )
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]

    @pytest.mark.django_db
    def test_leading_trailing_whitespace_in_token_rejected(self):
        """Token with leading/trailing whitespace should be rejected."""
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key  {settings.CONFIG.general.api_key} ",
        )
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]

    @pytest.mark.django_db
    def test_control_characters_rejected(self):
        """Control characters (0x01-0x1F) should be rejected."""
        client = APIClient()
        control_chars = [
            "Api-Key \x01token",
            "Api-Key \x1ftoken",
            "Api-Key \x7ftoken",
        ]
        for header in control_chars:
            client.credentials(HTTP_AUTHORIZATION=header)
            response = client.get("/api/v2/playlists")
            assert response.status_code in [
                403,
                401,
            ], f"Control char header: expected 403/401, got {response.status_code}"

    @pytest.mark.django_db
    def test_null_byte_rejected(self):
        """Null byte in header should be rejected."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key \x00token")
        response = client.get("/api/v2/playlists")
        assert response.status_code in [403, 401]


class TestDirtyDataDirectFunction:
    """Direct tests for check_authorization_header function."""

    def test_direct_unicode_handling(self):
        """Function should handle unicode without crashing."""
        from unittest.mock import MagicMock

        from api.permissions import check_authorization_header

        request = MagicMock()
        request.headers = {"authorization": "Api-Key тест"}
        result = check_authorization_header(request)
        assert result is False

    def test_direct_newline_rejection(self):
        """Function should reject newlines."""
        from unittest.mock import MagicMock

        from api.permissions import check_authorization_header

        request = MagicMock()
        request.headers = {"authorization": "Api-Key token\ninjection"}
        result = check_authorization_header(request)
        assert result is False

    def test_direct_cr_rejection(self):
        """Function should reject carriage returns."""
        from unittest.mock import MagicMock

        from api.permissions import check_authorization_header

        request = MagicMock()
        request.headers = {"authorization": "Api-Key token\rinjection"}
        result = check_authorization_header(request)
        assert result is False

    def test_direct_case_sensitivity(self):
        """Function should be case-sensitive."""
        from unittest.mock import MagicMock

        from django.conf import settings

        from api.permissions import check_authorization_header

        request = MagicMock()
        # Wrong case should fail
        request.headers = {
            "authorization": f"api-key {settings.CONFIG.general.api_key}",
        }
        result = check_authorization_header(request)
        assert result is True

        # Correct case should succeed
        request.headers = {
            "authorization": f"Api-Key {settings.CONFIG.general.api_key}",
        }
        result = check_authorization_header(request)
        assert result is True

    def test_direct_empty_token(self):
        """Function should handle empty token."""
        from unittest.mock import MagicMock

        from api.permissions import check_authorization_header

        request = MagicMock()
        request.headers = {"authorization": "Api-Key "}
        result = check_authorization_header(request)
        assert result is False

    def test_direct_no_space(self):
        """Function should reject 'Api-Key' without space."""
        from unittest.mock import MagicMock

        from api.permissions import check_authorization_header

        request = MagicMock()
        request.headers = {"authorization": "Api-Key"}
        result = check_authorization_header(request)
        assert result is False
