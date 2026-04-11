"""
Comprehensive test matrix for ANONYMOUS access denial.

All endpoints must return 403 for unauthenticated requests.
API-Key authentication is the only exception (for services).

Coverage:
- All schedule endpoints (shows, playlists, smartblocks, webstreams, etc.)
- All storage endpoints (files, libraries)
- All podcast endpoints (podcasts, episodes)
- All core endpoints (users, preferences)
- All history endpoints

Usage:
    cd app/api && uv run pytest api/tests/test_role_anonymous_denied.py -v
"""

import pytest


# =============================================================================
# Schedule Module Endpoints
# =============================================================================

SCHEDULE_ENDPOINTS = [
    # Shows
    ("/api/v2/shows", "shows"),
    ("/api/v2/show-days", "show-days"),
    ("/api/v2/show-hosts", "show-hosts"),
    ("/api/v2/show-instances", "show-instances"),
    ("/api/v2/show-rebroadcasts", "show-rebroadcasts"),
    # Content
    ("/api/v2/playlists", "playlists"),
    ("/api/v2/playlist-contents", "playlist-contents"),
    ("/api/v2/smart-blocks", "smart-blocks"),
    ("/api/v2/smart-block-contents", "smart-block-contents"),
    ("/api/v2/smart-block-criteria", "smart-block-criteria"),
    ("/api/v2/webstreams", "webstreams"),
    ("/api/v2/webstream-metadata", "webstream-metadata"),
    ("/api/v2/schedule", "schedule"),
]

STORAGE_ENDPOINTS = [
    ("/api/v2/files", "files"),
    ("/api/v2/libraries", "libraries"),
]

PODCAST_ENDPOINTS = [
    ("/api/v2/podcasts", "podcasts"),
    ("/api/v2/podcast-episodes", "podcast-episodes"),
    ("/api/v2/station-podcasts", "station-podcasts"),
    ("/api/v2/imported-podcasts", "imported-podcasts"),
]

CORE_ENDPOINTS = [
    ("/api/v2/users", "users"),
    ("/api/v2/preferences", "preferences"),
    ("/api/v2/user-tokens", "user-tokens"),
    ("/api/v2/login-attempts", "login-attempts"),
]

HISTORY_ENDPOINTS = [
    ("/api/v2/playout-history", "playout-history"),
    ("/api/v2/playout-history-metadata", "playout-history-metadata"),
    ("/api/v2/playout-history-templates", "playout-history-templates"),
    ("/api/v2/playout-history-template-fields", "playout-history-template-fields"),
    ("/api/v2/mount-names", "mount-names"),
    ("/api/v2/timestamps", "timestamps"),
    ("/api/v2/listener-counts", "listener-counts"),
    ("/api/v2/live-logs", "live-logs"),
]

ALL_GET_ENDPOINTS = (
    SCHEDULE_ENDPOINTS +
    STORAGE_ENDPOINTS +
    PODCAST_ENDPOINTS +
    CORE_ENDPOINTS +
    HISTORY_ENDPOINTS
)


@pytest.mark.django_db
class TestAnonymousAccessDenied:
    """
    Anonymous users get 403 on ALL endpoints.
    
    Security principle: No anonymous access to any resource.
    Only authenticated users (session) or services (API-Key) allowed.
    """

    @pytest.mark.parametrize("endpoint,name", ALL_GET_ENDPOINTS)
    def test_anonymous_get_returns_403(self, anonymous_client, endpoint, name):
        """Anonymous GET request returns 403 Forbidden."""
        response = anonymous_client.get(endpoint)
        assert response.status_code == 403, (
            f"Anonymous GET {endpoint} should return 403, got {response.status_code}"
        )

    @pytest.mark.parametrize("endpoint,name", ALL_GET_ENDPOINTS)
    def test_anonymous_post_returns_403(self, anonymous_client, endpoint, name):
        """Anonymous POST request returns 403 Forbidden."""
        response = anonymous_client.post(endpoint, {}, format="json")
        assert response.status_code == 403, (
            f"Anonymous POST {endpoint} should return 403, got {response.status_code}"
        )

    @pytest.mark.parametrize("endpoint,name", ALL_GET_ENDPOINTS)
    def test_anonymous_put_returns_403(self, anonymous_client, endpoint, name):
        """Anonymous PUT request returns 403 Forbidden."""
        response = anonymous_client.put(f"{endpoint}/1", {}, format="json")
        assert response.status_code == 403, (
            f"Anonymous PUT {endpoint}/1 should return 403, got {response.status_code}"
        )

    @pytest.mark.parametrize("endpoint,name", ALL_GET_ENDPOINTS)
    def test_anonymous_patch_returns_403(self, anonymous_client, endpoint, name):
        """Anonymous PATCH request returns 403 Forbidden."""
        response = anonymous_client.patch(f"{endpoint}/1", {}, format="json")
        assert response.status_code == 403, (
            f"Anonymous PATCH {endpoint}/1 should return 403, got {response.status_code}"
        )

    @pytest.mark.parametrize("endpoint,name", ALL_GET_ENDPOINTS)
    def test_anonymous_delete_returns_403(self, anonymous_client, endpoint, name):
        """Anonymous DELETE request returns 403 Forbidden."""
        response = anonymous_client.delete(f"{endpoint}/1")
        assert response.status_code == 403, (
            f"Anonymous DELETE {endpoint}/1 should return 403, got {response.status_code}"
        )


@pytest.mark.django_db
class TestAnonymousAccessSpecificMessages:
    """Verify 403 response format for anonymous access."""

    def test_anonymous_403_has_correct_message(self, anonymous_client):
        """403 response should indicate authentication required."""
        response = anonymous_client.get("/api/v2/shows")
        assert response.status_code == 403
        assert "detail" in response.data
        assert "authentication" in str(response.data["detail"]).lower()

    def test_anonymous_401_not_used(self, anonymous_client):
        """Should use 403, not 401 (DRF default for permission denied)."""
        response = anonymous_client.get("/api/v2/playlists")
        assert response.status_code == 403
        # 401 is for authentication failures, 403 for permission denied
        # DRF uses 403 for unauthenticated access to protected resources


@pytest.mark.django_db
class TestAnonymousVsApiKey:
    """
    Anonymous = 403, API-Key = 200.
    
    Only API-Key bypasses authentication (for services).
    """

    def test_anonymous_gets_403_api_key_gets_200(self, anonymous_client, api_client):
        """Same endpoint: anonymous 403, API-Key 200."""
        endpoint = "/api/v2/playlists"
        
        # Anonymous
        anon_response = anonymous_client.get(endpoint)
        assert anon_response.status_code == 403
        
        # API-Key
        api_response = api_client.get(endpoint)
        assert api_response.status_code == 200

    def test_anonymous_cannot_access_anything_api_key_can(self, anonymous_client, api_client):
        """API-Key has full read access, anonymous has none."""
        endpoints = [
            "/api/v2/shows",
            "/api/v2/playlists",
            "/api/v2/files",
            "/api/v2/podcasts",
        ]
        
        for endpoint in endpoints:
            anon_response = anonymous_client.get(endpoint)
            api_response = api_client.get(endpoint)
            
            assert anon_response.status_code == 403, (
                f"Anonymous should get 403 on {endpoint}"
            )
            assert api_response.status_code == 200, (
                f"API-Key should get 200 on {endpoint}"
            )


@pytest.mark.django_db
class TestAnonymousWithInvalidAuthHeader:
    """Anonymous with malformed auth headers still gets 403."""

    def test_anonymous_with_bearer_token_still_403(self, anonymous_client):
        """Bearer token (not Api-Key) should not grant access."""
        anonymous_client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid-token-12345"
        )
        response = anonymous_client.get("/api/v2/shows")
        assert response.status_code == 403

    def test_anonymous_with_basic_auth_still_403(self, anonymous_client):
        """Basic auth should not grant access."""
        anonymous_client.credentials(
            HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz"  # user:pass base64
        )
        response = anonymous_client.get("/api/v2/shows")
        assert response.status_code == 403

    def test_anonymous_with_malformed_api_key_still_403(self, anonymous_client):
        """Malformed Api-Key header should not grant access."""
        anonymous_client.credentials(
            HTTP_AUTHORIZATION="ApiKey wrong-format"  # Missing hyphen
        )
        response = anonymous_client.get("/api/v2/shows")
        assert response.status_code == 403
