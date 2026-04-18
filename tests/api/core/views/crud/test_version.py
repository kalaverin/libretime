"""Tests for Version endpoint (T183)."""

import pytest

from django.conf import settings
from django.test import Client


@pytest.mark.django_db(transaction=True)
class TestVersionView:
    """Test Version endpoint - GET /api/v2/version."""

    def test_version_endpoint_available(self, client: Client):
        """Version endpoint should be accessible."""
        response = client.get("/api/v2/version")
        assert response.status_code == 200

    def test_version_returns_json(self, client: Client):
        """Version endpoint should return JSON."""
        response = client.get("/api/v2/version")
        assert response["Content-Type"] == "application/json"

    def test_version_response_structure(self, client: Client):
        """Version response should have api_version field."""
        response = client.get("/api/v2/version")
        data = response.json()
        assert "api_version" in data
        assert isinstance(data["api_version"], str)

    def test_version_matches_settings(self, client: Client):
        """Version should match settings.API_VERSION."""
        response = client.get("/api/v2/version")
        data = response.json()
        assert data["api_version"] == settings.API_VERSION

    def test_version_no_auth_required(self, client: Client):
        """Version endpoint should be accessible without authentication."""
        response = client.get("/api/v2/version")
        assert response.status_code == 200
        assert "api_version" in response.json()

    def test_version_returns_only_api_version(self, client: Client):
        """Version should return only api_version field."""
        response = client.get("/api/v2/version")
        data = response.json()
        assert set(data.keys()) == {"api_version"}

    def test_version_format_semantic(self, client: Client):
        """Version should follow semantic versioning format (X.Y.Z)."""
        response = client.get("/api/v2/version")
        data = response.json()
        version = data["api_version"]
        # Check basic semantic version format: major.minor.patch
        parts = version.split(".")
        assert (
            len(parts) >= 2
        ), f"Version should have at least 2 parts: {version}"
        # All parts should be numeric (or start with numeric for pre-release)
        for part in parts[:3]:  # Check first 3 parts
            assert (
                part.isdigit() or part[0].isdigit()
            ), f"Version part should be numeric: {part}"

    def test_version_not_empty(self, client: Client):
        """Version should not be empty string."""
        response = client.get("/api/v2/version")
        data = response.json()
        assert data["api_version"] != ""
        assert len(data["api_version"]) > 0

    def test_version_post_not_allowed(self, client: Client):
        """POST should not be allowed on Version endpoint."""
        response = client.post(
            "/api/v2/version",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_version_put_not_allowed(self, client: Client):
        """PUT should not be allowed on Version endpoint."""
        response = client.put(
            "/api/v2/version",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_version_patch_not_allowed(self, client: Client):
        """PATCH should not be allowed on Version endpoint."""
        response = client.patch(
            "/api/v2/version",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_version_delete_not_allowed(self, client: Client):
        """DELETE should not be allowed on Version endpoint."""
        response = client.delete("/api/v2/version")
        assert response.status_code == 405

    def test_version_with_api_key(self, guest_client):
        """Version endpoint should work with API key authentication."""
        response = guest_client.get("/api/v2/version")
        assert response.status_code == 200
        assert "api_version" in response.json()

    def test_version_with_session_auth(self, authenticated_client):
        """Version endpoint should work with session authentication."""
        response = authenticated_client.get("/api/v2/version")
        assert response.status_code == 200
        assert "api_version" in response.json()

    def test_version_consistent_across_calls(self, client: Client):
        """Version should be consistent across multiple calls."""
        response1 = client.get("/api/v2/version")
        response2 = client.get("/api/v2/version")
        assert response1.json() == response2.json()
