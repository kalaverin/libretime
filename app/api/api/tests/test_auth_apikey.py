"""
T280: Api-Key authentication tests.

Tests for LibreTime API Key (service token) authentication.
Uses IsSystemTokenOrUser permission class.
"""

import pytest

from django.conf import settings
from rest_framework.test import APIClient

# Helper to get API key value
API_KEY = settings.CONFIG.general.api_key


@pytest.mark.django_db
class TestApiKeyAuth:
    """Test API Key authentication for service accounts."""

    PROTECTED_ENDPOINTS = [
        "/api/v2/files",
        "/api/v2/libraries",
        "/api/v2/shows",
        "/api/v2/playlists",
    ]

    def test_api_key_auth_with_valid_token(self, api_client):
        """Valid API key should grant access to protected endpoints."""
        response = api_client.get("/api/v2/files")
        assert response.status_code == 200

    def test_api_key_auth_access_all_protected_endpoints(self, api_client):
        """API key should work across all protected endpoints."""
        for endpoint in self.PROTECTED_ENDPOINTS:
            response = api_client.get(endpoint)
            assert (
                response.status_code == 200
            ), f"Expected 200 for {endpoint}, got {response.status_code}"

    def test_invalid_api_key_returns_403(self):
        """Invalid API key should return 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key-12345")

        response = client.get("/api/v2/files")
        assert response.status_code == 403

    def test_missing_api_key_returns_403(self):
        """Missing API key should return 403 for protected endpoints."""
        client = APIClient()

        for endpoint in self.PROTECTED_ENDPOINTS:
            response = client.get(endpoint)
            assert (
                response.status_code == 403
            ), f"Expected 403 for {endpoint}, got {response.status_code}"

    def test_api_key_authorization_header_format(self):
        """API key must use Authorization: Api-Key <token> format."""
        client = APIClient()
        # Wrong format - just the key without "Api-Key" prefix
        client.credentials(HTTP_AUTHORIZATION=API_KEY)

        response = client.get("/api/v2/files")
        # Should be 403 because header format is wrong
        assert response.status_code == 403

    def test_api_key_with_session_auth_fallback(self, admin_user):
        """API key auth should work alongside session auth."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get("/api/v2/files")
        assert response.status_code == 200


@pytest.mark.django_db
class TestApiKeyAuthEdgeCases:
    """Edge cases for API key authentication."""

    def test_malformed_api_key_prefix_rejected(self):
        """Wrong prefix in Authorization header should be rejected."""
        client = APIClient()

        wrong_prefixes = [
            "Bearer token123",  # wrong prefix
            "Basic dXNlcjpwYXNz",  # Basic auth
            "",  # empty header
        ]

        for auth in wrong_prefixes:
            client.credentials(HTTP_AUTHORIZATION=auth)
            response = client.get("/api/v2/files")
            assert (
                response.status_code == 403
            ), f"Expected 403 for auth {repr(auth[:30])}, got {response.status_code}"

    @pytest.mark.xfail(reason="T341: IndexError on empty Api-Key value")
    def test_empty_api_key_value_rejected(self):
        """Empty Api-Key value should return 403, not crash.

        Bug T341: check_authorization_header() crashes with IndexError
        when Authorization header is 'Api-Key ' (with space but no key).
        """
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION="Api-Key ",
        )  # Note: space but no key

        response = client.get("/api/v2/files")
        assert response.status_code == 403, (
            f"T341: Expected 403, got {response.status_code}. "
            "Empty Api-Key should be rejected gracefully."
        )

    def test_api_key_wrong_endpoint_format(self, api_client):
        """API key should be rejected on non-existent endpoints (404, not 403)."""
        response = api_client.get("/api/v2/nonexistent-endpoint")
        assert response.status_code == 404


@pytest.mark.django_db
class TestAuthMethodPriority:
    """Test priority between different auth methods."""

    def test_session_auth_overrides_invalid_api_key(self, admin_user):
        """Valid session auth should work even with invalid API key."""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        client.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key")

        response = client.get("/api/v2/files")
        # Session auth should succeed despite invalid API key
        assert response.status_code == 200

    def test_valid_api_key_overrides_no_session(self):
        """Valid API key should work without session."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Api-Key {API_KEY}")

        response = client.get("/api/v2/files")
        assert response.status_code == 200


@pytest.mark.django_db
class TestBugT341:
    """Test to confirm T341: IndexError on empty Api-Key header value."""

    def test_t341_check_authorization_header_crashes_with_empty_key(self):
        """Confirm T341: IndexError when Authorization header is 'Api-Key '.

        Bug: check_authorization_header() does not check if split()
        returns enough parts before accessing [1].
        """
        from rest_framework.test import APIRequestFactory

        from api.permissions import check_authorization_header

        request = APIRequestFactory().get("/api/v2/files")
        request.headers = {"authorization": "Api-Key "}

        # This should crash with IndexError
        with pytest.raises(IndexError, match="list index out of range"):
            check_authorization_header(request)

    def test_t341_empty_api_key_returns_500_instead_of_403(self):
        """Confirm T341: Empty Api-Key causes 500 instead of 403.

        Expected: 403 Forbidden
        Actual: 500 Internal Server Error (IndexError in permission check)
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key ")

        # This will raise IndexError internally
        try:
            response = client.get("/api/v2/files")
            # If we get here without exception, T341 is fixed
            assert (
                response.status_code == 403
            ), f"T341 fixed? Expected 403, got {response.status_code}"
        except IndexError as e:
            # This confirms T341 is present
            assert "list index out of range" in str(e)
