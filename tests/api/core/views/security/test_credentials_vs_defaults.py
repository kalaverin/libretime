"""
RED TEAM: T575/T584/T589/T597/T600 - Test credentials() vs defaults[] priority.

This file demonstrates and verifies the behavior of DRF APIClient's
authentication override mechanisms.

IMPORTANT LESSON: `credentials()` has PRIORITY over `defaults[]`.
Previous tests incorrectly used defaults[] to override auth, which
resulted in false positives - the Api-Key was still being sent.

BUGFIX: The actual permission system was working correctly all along.
The bug was in the test methodology, not in IsSystemTokenOrUser permission.
"""

import pytest

from django.conf import settings
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestCredentialsVsDefaults:
    """Verify correct authentication override behavior."""

    def test_credentials_priority_over_defaults(self, api_client):
        """
        Demonstrates that credentials() has priority over defaults[].

        If a client is created with credentials(Api-Key), then setting
        defaults['Authorization'] has NO EFFECT - the Api-Key is still sent.
        """
        # api_client already has Api-Key credentials set
        # Now try to override using defaults[]
        api_client.defaults["HTTP_AUTHORIZATION"] = "Bearer invalid_token"

        response = api_client.get("/api/v2/schedule")

        # The Api-Key is still used! defaults[] does NOT override credentials()
        # This returns 200, NOT 403, because credentials() has priority
        assert response.status_code == 200, (
            "credentials(Api-Key) takes priority over defaults[Bearer]. "
            "This is expected DRF behavior, not a bug."
        )

    def test_credentials_override_method(self):
        """
        Demonstrates the CORRECT way to override authentication.

        To override credentials, use credentials() again, not defaults[].
        """
        client = APIClient()

        # Set valid Api-Key
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        # This works - valid key
        response = client.get("/api/v2/schedule")
        assert response.status_code == 200, "Valid Api-Key should work"

        # CORRECT: Override using credentials(), not defaults[]
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        response = client.get("/api/v2/schedule")
        # Now it returns 403 because the invalid token is actually sent
        assert response.status_code == 403, (
            "After credentials(Bearer invalid_token), 403 should be returned. "
            "This is the correct way to test invalid token rejection."
        )


@pytest.mark.django_db
class TestProperInvalidTokenTesting:
    """
    PROPER testing methodology for invalid token scenarios.

    These tests use the correct approach: create fresh clients with
    invalid credentials, rather than trying to override existing ones.
    """

    def test_list_schedule_with_invalid_bearer(self):
        """
        T575: PROPER test - LIST with invalid Bearer token returns 403.

        This test creates a fresh client with only the invalid token,
        avoiding the credentials() vs defaults[] confusion entirely.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer totally_invalid")

        response = client.get("/api/v2/schedule")
        assert (
            response.status_code == 403
        ), f"T575: LIST with invalid token should return 403, got {response.status_code}"

    def test_create_schedule_with_invalid_bearer(self):
        """T584: PROPER test - CREATE with invalid Bearer token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer totally_invalid")

        response = client.post("/api/v2/schedule", {})
        assert (
            response.status_code == 403
        ), f"T584: CREATE with invalid token should return 403, got {response.status_code}"

    def test_retrieve_schedule_with_invalid_bearer(self):
        """T589: PROPER test - RETRIEVE with invalid Bearer token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer totally_invalid")

        response = client.get("/api/v2/schedule/1")
        assert (
            response.status_code == 403
        ), f"T589: RETRIEVE with invalid token should return 403, got {response.status_code}"

    def test_update_schedule_with_invalid_bearer(self):
        """T597: PROPER test - UPDATE with invalid Bearer token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer totally_invalid")

        response = client.patch("/api/v2/schedule/1", {})
        assert (
            response.status_code == 403
        ), f"T597: UPDATE with invalid token should return 403, got {response.status_code}"

    def test_delete_schedule_with_invalid_bearer(self):
        """T600: PROPER test - DELETE with invalid Bearer token returns 403."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer totally_invalid")

        response = client.delete("/api/v2/schedule/1")
        assert (
            response.status_code == 403
        ), f"T600: DELETE with invalid token should return 403, got {response.status_code}"
