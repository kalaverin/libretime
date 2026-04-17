"""
T282: Invalid authentication returns 403.

Tests that various forms of invalid auth are properly rejected with 403.
"""

import pytest

from django.conf import settings
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestInvalidAuthReturns403:
    """Test that invalid authentication returns 403."""

    PROTECTED_ENDPOINT = "/api/v2/files"

    def test_invalid_api_key_returns_403(self):
        """Invalid API key should return 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key-12345")

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_wrong_api_key_format_returns_403(self):
        """API key without 'Api-Key' prefix should return 403."""
        client = APIClient()
        # Just the key value without prefix
        client.credentials(HTTP_AUTHORIZATION=settings.CONFIG.general.api_key)

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_bearer_token_returns_403(self):
        """Bearer token should return 403 (not supported)."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer some-jwt-token")

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_basic_auth_returns_403(self):
        """Basic auth should return 403 (not supported)."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_no_auth_returns_403(self):
        """No authentication should return 403."""
        client = APIClient()

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_empty_auth_header_returns_403(self):
        """Empty Authorization header should return 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="")

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_malformed_auth_header_returns_403(self):
        """Malformed Authorization header should return 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="MalformedHeaderWithoutSpace")

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_session_auth_with_wrong_password_fails(self):
        """Session auth with wrong password should fail."""
        from django.contrib.auth import get_user_model

        from api.core.models import Role

        User = get_user_model()
        User.objects.create_user(
            role=Role.HOST,
            username="test_user",
            password="correct_password",
            email="test@test.com",
            first_name="Test",
            last_name="User",
        )

        client = APIClient()
        # Try to login with wrong password
        logged_in = client.login(
            username="test_user",
            password="wrong_password",
        )
        assert logged_in is False

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403

    def test_nonexistent_user_auth_fails(self):
        """Auth with non-existent user should fail."""
        client = APIClient()
        logged_in = client.login(
            username="nonexistent_user",
            password="any_password",
        )
        assert logged_in is False

        response = client.get(self.PROTECTED_ENDPOINT)
        assert response.status_code == 403
