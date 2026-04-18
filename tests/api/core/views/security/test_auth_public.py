"""
T281: Public endpoints without authentication.

Tests for endpoints that should be accessible without any auth.
Uses AllowAny permission class.
"""

import pytest

from rest_framework.test import APIClient


@pytest.mark.django_db
class TestPublicEndpoints:
    """Test endpoints accessible without authentication."""

    PUBLIC_ENDPOINTS = [
        "/api/v2/info",
        "/api/v2/version",
    ]

    def test_public_endpoints_no_auth_required(self):
        """Public endpoints should return 200 without authentication."""
        client = APIClient()

        for endpoint in self.PUBLIC_ENDPOINTS:
            response = client.get(endpoint)
            assert (
                response.status_code == 200
            ), f"Expected 200 for public endpoint {endpoint}, got {response.status_code}"

    def test_public_endpoints_with_invalid_auth_still_work(self):
        """Public endpoints should work even with invalid auth headers."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

        for endpoint in self.PUBLIC_ENDPOINTS:
            response = client.get(endpoint)
            assert (
                response.status_code == 200
            ), f"Public endpoint {endpoint} should ignore invalid auth, got {response.status_code}"

    def test_public_endpoints_with_session_auth_still_work(self, admin_user):
        """Public endpoints should work with session auth (no 403)."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for endpoint in self.PUBLIC_ENDPOINTS:
            response = client.get(endpoint)
            assert (
                response.status_code == 200
            ), f"Public endpoint {endpoint} should work with session auth, got {response.status_code}"

    def test_public_endpoints_with_api_key_still_work(self):
        """Public endpoints should work with API key (no conflict)."""
        from django.conf import settings

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        for endpoint in self.PUBLIC_ENDPOINTS:
            response = client.get(endpoint)
            assert (
                response.status_code == 200
            ), f"Public endpoint {endpoint} should work with API key, got {response.status_code}"

    def test_info_endpoint_returns_data(self):
        """Info endpoint should return LibreTime information."""
        client = APIClient()
        response = client.get("/api/v2/info")

        assert response.status_code == 200
        data = response.json()
        assert "station_name" in data
        assert data["station_name"] == "LibreTime"

    def test_version_endpoint_returns_data(self):
        """Version endpoint should return version information."""
        client = APIClient()
        response = client.get("/api/v2/version")

        assert response.status_code == 200
        data = response.json()
        assert "api_version" in data
