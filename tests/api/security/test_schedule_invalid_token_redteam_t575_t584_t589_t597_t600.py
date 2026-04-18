"""
RED TEAM: T575/T584/T589/T597/T600 - Invalid Token Authentication Bypass Tests.

Verifies that invalid/malformed Bearer tokens are rejected with 403.
These tests confirm the fixes for:
- T575: LIST with invalid token returns 403 (not 200)
- T584: CREATE with invalid token returns 403 (not 200)
- T589: RETRIEVE with invalid token returns 403 (not 200)
- T597: UPDATE with invalid token returns 403 (not 200)
- T600: DELETE with invalid token returns 403 (not 200)

BUGFIX NOTE: Previous tests incorrectly used defaults[] to override auth,
but DRF's credentials() has priority over defaults[]. These tests use
the correct approach - creating fresh clients with invalid tokens.
"""

from datetime import timedelta

import pytest

from rest_framework.test import APIClient
from sdk.datetime import format_datetime

from sdk import now


@pytest.mark.django_db
class TestScheduleInvalidTokenLIST:
    """T575: LIST with invalid token should return 403."""

    def test_list_with_invalid_bearer_token(self):
        """LIST with Bearer invalid_token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        response = client.get("/api/v2/schedule")

        # Fixed: Should return 403, not 200
        assert (
            response.status_code == 403
        ), f"T575 NOT FIXED: LIST with invalid token returned {response.status_code}, expected 403"

    def test_list_with_malformed_bearer(self):
        """LIST with malformed Bearer token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer ")

        response = client.get("/api/v2/schedule")
        assert (
            response.status_code == 403
        ), f"T575: Expected 403, got {response.status_code}"

    def test_list_with_random_token_scheme(self):
        """LIST with random auth scheme returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Token abc123")

        response = client.get("/api/v2/schedule")
        assert (
            response.status_code == 403
        ), f"T575: Expected 403, got {response.status_code}"


@pytest.mark.django_db
class TestScheduleInvalidTokenCREATE:
    """T584: CREATE with invalid token should return 403."""

    def test_create_with_invalid_bearer_token(self):
        """CREATE with Bearer invalid_token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        data = {
            "instance": 1,
            "starts_at": format_datetime(now()),
            "ends_at": format_datetime(now() + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 0,
        }

        response = client.post("/api/v2/schedule", data, format="json")

        # Fixed: Should return 403, not 200/201
        assert (
            response.status_code == 403
        ), f"T584 NOT FIXED: CREATE with invalid token returned {response.status_code}, expected 403"


@pytest.mark.django_db
class TestScheduleInvalidTokenRETRIEVE:
    """T589: RETRIEVE with invalid token should return 403."""

    def test_retrieve_with_invalid_bearer_token(self):
        """RETRIEVE with Bearer invalid_token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        # Try to access any ID
        response = client.get("/api/v2/schedule/1")

        # Fixed: Should return 403, not 200
        assert (
            response.status_code == 403
        ), f"T589 NOT FIXED: RETRIEVE with invalid token returned {response.status_code}, expected 403"

    def test_retrieve_nonexistent_with_invalid_token(self):
        """RETRIEVE non-existent with invalid token still returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        response = client.get("/api/v2/schedule/99999")
        assert (
            response.status_code == 403
        ), f"T589: Expected 403, got {response.status_code}"


@pytest.mark.django_db
class TestScheduleInvalidTokenUPDATE:
    """T597: UPDATE with invalid token should return 403."""

    def test_patch_with_invalid_bearer_token(self):
        """PATCH with Bearer invalid_token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        response = client.patch(
            "/api/v2/schedule/1",
            {"position": 999},
            format="json",
        )

        # Fixed: Should return 403, not 200
        assert (
            response.status_code == 403
        ), f"T597 NOT FIXED: PATCH with invalid token returned {response.status_code}, expected 403"

    def test_put_with_invalid_bearer_token(self):
        """PUT with Bearer invalid_token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        data = {
            "instance": 1,
            "starts_at": format_datetime(now()),
            "ends_at": format_datetime(now() + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 0,
        }

        response = client.put("/api/v2/schedule/1", data, format="json")
        assert (
            response.status_code == 403
        ), f"T597: Expected 403, got {response.status_code}"


@pytest.mark.django_db
class TestScheduleInvalidTokenDELETE:
    """T600: DELETE with invalid token should return 403."""

    def test_delete_with_invalid_bearer_token(self):
        """DELETE with Bearer invalid_token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        response = client.delete("/api/v2/schedule/1")

        # Fixed: Should return 403, not 200/204
        assert (
            response.status_code == 403
        ), f"T600 NOT FIXED: DELETE with invalid token returned {response.status_code}, expected 403"


@pytest.mark.django_db
class TestScheduleInvalidTokenComprehensive:
    """Comprehensive invalid token tests."""

    def test_all_endpoints_reject_invalid_token(self):
        """All CRUD endpoints reject invalid Bearer token."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer totally_invalid_token")

        endpoints = [
            ("GET", "/api/v2/schedule"),
            ("GET", "/api/v2/schedule/1"),
            ("POST", "/api/v2/schedule"),
            ("PATCH", "/api/v2/schedule/1"),
            ("PUT", "/api/v2/schedule/1"),
            ("DELETE", "/api/v2/schedule/1"),
        ]

        for method, url in endpoints:
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, {})
            elif method == "PATCH":
                response = client.patch(url, {})
            elif method == "PUT":
                response = client.put(url, {})
            elif method == "DELETE":
                response = client.delete(url)

            assert (
                response.status_code == 403
            ), f"T575/T584/T589/T597/T600: {method} {url} returned {response.status_code}, expected 403"

    def test_valid_api_key_still_works(self, admin_client):
        """Valid Api-Key auth still works correctly."""
        response = admin_client.get("/api/v2/schedule")
        assert response.status_code == 200, "Valid API-Key should work"

    def test_no_auth_returns_403(self, client):
        """No auth header returns 403."""
        response = client.get("/api/v2/schedule")
        assert response.status_code == 403, "No auth should return 403"
