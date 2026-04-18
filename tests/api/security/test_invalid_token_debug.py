"""Debug test for invalid token handling (T575/T584/T589/T597/T600)."""

import pytest

from rest_framework.test import APIClient


@pytest.mark.django_db
class TestInvalidTokenDebug:
    """Debug tests to understand invalid token behavior."""

    def test_no_auth(self, client):
        """No auth header at all."""
        response = client.get("/api/v2/schedule")
        print(f"\nNo auth: {response.status_code}")
        print(f"Response: {response.content[:200]}")
        assert response.status_code == 403

    def test_api_key_auth(self, guest_client):
        """Valid API-Key auth."""
        response = guest_client.get("/api/v2/schedule")
        print(f"\nAPI-Key: {response.status_code}")
        assert response.status_code == 200

    def test_bearer_invalid_token_explicit(self):
        """Explicit test with Bearer invalid_token."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        response = client.get("/api/v2/schedule")
        print(f"\nBearer invalid: {response.status_code}")
        print(f"Response: {response.content[:200]}")

        # Should be 403!
        assert (
            response.status_code == 403
        ), f"T575: Expected 403 for invalid token, got {response.status_code}"

    def test_bearer_malformed(self):
        """Malformed Bearer token."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer ")

        response = client.get("/api/v2/schedule")
        print(f"\nBearer empty: {response.status_code}")
        assert response.status_code == 403

    def test_random_auth_scheme(self):
        """Random auth scheme."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")

        response = client.get("/api/v2/schedule")
        print(f"\nBasic auth: {response.status_code}")
        assert response.status_code == 403
