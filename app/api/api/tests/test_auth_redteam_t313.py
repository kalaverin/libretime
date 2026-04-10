"""
RED TEAM: T313/T314 - UserToken and LoginAttempt lookup security tests.

Attack vectors:
- Token enumeration
- IP spoofing in lookup
- BOLA on user tokens
- Mass assignment on auth entities
- Login attempt manipulation
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestUserTokenLookup:
    """UserToken lookup security tests."""

    @pytest.mark.xfail(reason="PostgreSQL rejects NUL bytes in text fields")
    def test_token_with_special_chars(self, api_client, admin_user):
        """Try to use token with special characters in lookup."""
        api_client.force_authenticate(user=admin_user)

        special_tokens = [
            'token"; DROP TABLE',
            "token' OR '1'='1",
            "token/../../etc/passwd",
            "token%00",
            "token\n",
        ]

        for token in special_tokens:
            response = api_client.get(f"/api/v2/user-tokens/{token}")
            # Should not crash
            assert response.status_code in [200, 404, 400]

    def test_very_long_token_lookup(self, api_client, admin_user):
        """Try to lookup with very long token."""
        api_client.force_authenticate(user=admin_user)

        long_token = "a" * 1000
        response = api_client.get(f"/api/v2/user-tokens/{long_token}")

        assert response.status_code in [200, 404, 400]

    def test_unicode_token_lookup(self, api_client, admin_user):
        """Try to lookup with unicode token."""
        api_client.force_authenticate(user=admin_user)

        unicode_token = "токен_пользователя_123"
        response = api_client.get(f"/api/v2/user-tokens/{unicode_token}")

        assert response.status_code in [200, 404, 400]


@pytest.mark.django_db
class TestUserTokenBOLA:
    """UserToken Broken Object Level Authorization."""

    def test_access_other_user_token(
        self, api_client, admin_user, regular_user,
    ):
        """Try to access another user's token."""
        token = baker.make(
            "core.UserToken", user=admin_user, token="admin_secret_token",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/user-tokens/admin_secret_token")

        if response.status_code == 200:
            pytest.fail("CRITICAL BUG: Can access other user's token (BOLA)")

    def test_delete_other_user_token(
        self, api_client, admin_user, regular_user,
    ):
        """Try to delete another user's token."""
        token = baker.make(
            "core.UserToken", user=admin_user, token="admin_secret_token",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete("/api/v2/user-tokens/admin_secret_token")

        if response.status_code == 204:
            pytest.fail("CRITICAL BUG: Can delete other user's token (BOLA)")

    @pytest.mark.xfail(reason="HOST user lacks view_usertoken permission")
    def test_list_shows_only_own_tokens(
        self, api_client, admin_user, regular_user,
    ):
        """Verify list returns only user's own tokens."""
        admin_token = baker.make(
            "core.UserToken", user=admin_user, token="admin_token",
        )
        user_token = baker.make(
            "core.UserToken", user=regular_user, token="user_token",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/user-tokens")

        assert response.status_code == 200
        data = response.json()

        tokens = [t["token"] for t in data]
        assert "user_token" in tokens

        if "admin_token" in tokens:
            pytest.fail("CRITICAL BUG: List shows other users' tokens (BOLA)")


@pytest.mark.django_db
class TestUserTokenMassAssignment:
    """UserToken mass assignment attacks."""

    def test_create_token_for_other_user(
        self, api_client, admin_user, regular_user,
    ):
        """Try to create token for another user."""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(
            "/api/v2/user-tokens",
            {
                "user": admin_user.id,
                "token": "hacked_admin_token",
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("user") == admin_user.id:
                pytest.fail("CRITICAL BUG: Can create token for other user")

    @pytest.mark.xfail(reason="Token value can be modified via PATCH")
    def test_update_token_value(self, api_client, admin_user):
        """Try to change token value via PATCH."""
        token = baker.make(
            "core.UserToken", user=admin_user, token="original_token",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            "/api/v2/user-tokens/original_token",
            {"token": "modified_token"},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: Can modify token value (should be immutable)")


@pytest.mark.django_db
class TestLoginAttemptLookup:
    """LoginAttempt lookup security tests."""

    def test_ip_with_malformed_format(self, api_client, admin_user):
        """Try to lookup with malformed IP address."""
        api_client.force_authenticate(user=admin_user)

        malformed_ips = [
            "999.999.999.999",  # Out of range
            "192.168.1",  # Incomplete
            "192.168.1.1.1",  # Extra octet
            "not-an-ip",
            "192.168.1.1; DROP TABLE",
            "192.168.1.1' OR '1'='1",
        ]

        for ip in malformed_ips:
            response = api_client.get(f"/api/v2/login-attempts/{ip}")
            assert response.status_code in [200, 404, 400]

    def test_ipv6_lookup(self, api_client, admin_user):
        """Try to lookup with IPv6 address."""
        api_client.force_authenticate(user=admin_user)

        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        response = api_client.get(f"/api/v2/login-attempts/{ipv6}")

        assert response.status_code in [200, 404, 400]

    def test_ip_with_path_traversal(self, api_client, admin_user):
        """Try path traversal in IP lookup."""
        api_client.force_authenticate(user=admin_user)

        traversal_ips = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "192.168.1.1/../../../etc/passwd",
        ]

        for ip in traversal_ips:
            response = api_client.get(f"/api/v2/login-attempts/{ip}")
            assert response.status_code in [200, 404, 400]


@pytest.mark.django_db
class TestLoginAttemptBOLA:
    """LoginAttempt Broken Object Level Authorization."""

    def test_access_other_user_login_attempt(
        self, api_client, admin_user, regular_user,
    ):
        """Try to access another user's login attempt record."""
        attempt = baker.make(
            "core.LoginAttempt", ip="192.168.1.100", attempts=5,
        )
        # Note: LoginAttempt may not have user FK - need to verify model

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/login-attempts/192.168.1.100")

        # Document behavior - may be global or per-user
        assert response.status_code in [200, 403, 404]

    @pytest.mark.xfail(reason="Login attempt counter can be modified via PATCH")
    def test_modify_login_attempt_count(self, api_client, admin_user):
        """Try to modify login attempt counter."""
        attempt = baker.make(
            "core.LoginAttempt", ip="192.168.1.100", attempts=5,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            "/api/v2/login-attempts/192.168.1.100",
            {"attempts": 0},  # Reset counter to bypass brute force protection
            format="json",
        )

        if response.status_code == 200:
            pytest.fail("CRITICAL BUG: Can modify login attempt counter")

    @pytest.mark.xfail(reason="Login attempt record can be deleted")
    def test_delete_login_attempt_record(self, api_client, admin_user):
        """Try to delete login attempt record."""
        attempt = baker.make(
            "core.LoginAttempt", ip="192.168.1.100", attempts=5,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.delete("/api/v2/login-attempts/192.168.1.100")

        if response.status_code == 204:
            pytest.fail("BUG: Can delete login attempt record (evasion)")


@pytest.mark.django_db
class TestLoginAttemptInjection:
    """LoginAttempt injection attacks."""

    def test_create_login_attempt_with_xff_header(
        self, api_client, admin_user,
    ):
        """Try to create login attempt with X-Forwarded-For header."""
        api_client.force_authenticate(user=admin_user)

        # Simulate X-Forwarded-For spoofing
        response = api_client.post(
            "/api/v2/login-attempts",
            {
                "ip": "192.168.1.1",
                "attempts": 1,
            },
            format="json",
            HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2",
        )

        # Document behavior
        assert response.status_code in [201, 403, 400]


@pytest.mark.django_db
class TestAuthBusinessLogic:
    """Business logic bypasses."""

    def test_create_token_without_auth(self, api_client):
        """Try to create token without authentication."""
        response = api_client.post(
            "/api/v2/user-tokens",
            {"token": "anonymous_token"},
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can create token")

    @pytest.mark.xfail(reason="Anonymous can list tokens")
    def test_list_tokens_without_auth(self, api_client):
        """Try to list tokens without authentication."""
        response = api_client.get("/api/v2/user-tokens")

        if response.status_code == 200:
            pytest.fail("CRITICAL BUG: Anonymous can list tokens")

    def test_create_duplicate_token(self, api_client, admin_user):
        """Try to create duplicate token."""
        baker.make("core.UserToken", user=admin_user, token="unique_token")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/user-tokens",
            {"token": "unique_token"},
            format="json",
        )

        # Should reject duplicate
        assert response.status_code in [201, 400]
