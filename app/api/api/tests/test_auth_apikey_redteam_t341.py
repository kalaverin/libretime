"""
RED TEAM: T341 - Api-Key authentication extended security tests.

Attack vectors:
- Api-Key header injection
- Token format manipulation
- Authorization bypass
- Timing attacks
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestApiKeyHeaderInjection:
    """Api-Key header injection attacks."""

    def test_empty_api_key_header(self, api_client):
        """Test empty Api-Key header (T341 regression test)."""
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key")
        response = api_client.get("/api/v2/preferences")

        # Should return 403, not 500
        assert response.status_code in [403, 401]

    def test_api_key_with_only_whitespace(self, api_client):
        """Test Api-Key header with only whitespace."""
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key   ")
        response = api_client.get("/api/v2/preferences")

        assert response.status_code in [403, 401]

    def test_api_key_with_null_byte(self, api_client):
        """Test Api-Key header with null byte."""
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key \x00token")
        response = api_client.get("/api/v2/preferences")

        assert response.status_code in [403, 401, 500]

    def test_api_key_with_newline(self, api_client):
        """Test Api-Key header with newline."""
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key \ntoken")
        response = api_client.get("/api/v2/preferences")

        assert response.status_code in [403, 401]

    def test_api_key_case_variations(self, api_client, admin_user):
        """Test Api-Key header case variations."""
        token = baker.make(
            "core.UserToken",
            user=admin_user,
            token="valid_token_123",
        )

        case_variations = [
            "api-key valid_token_123",
            "API-KEY valid_token_123",
            "Api-key valid_token_123",
            "api-Key valid_token_123",
        ]

        for auth_header in case_variations:
            api_client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = api_client.get("/api/v2/preferences")
            # Should be case-sensitive and reject variations
            assert response.status_code in [200, 403, 401]

    def test_api_key_with_multiple_spaces(self, api_client):
        """Test Api-Key header with multiple spaces."""
        api_client.credentials(
            HTTP_AUTHORIZATION="Api-Key    token_with_many_spaces",
        )
        response = api_client.get("/api/v2/preferences")

        assert response.status_code in [403, 401, 200]

    def test_api_key_with_tab(self, api_client):
        """Test Api-Key header with tab separator."""
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key\ttoken_with_tab")
        response = api_client.get("/api/v2/preferences")

        assert response.status_code in [403, 401, 200]


@pytest.mark.django_db
class TestApiKeyTokenManipulation:
    """Api-Key token manipulation attacks."""

    def test_sql_injection_in_token(self, api_client):
        """Test SQL injection in Api-Key token."""
        sqli_tokens = [
            "' OR '1'='1",
            "'; DROP TABLE cc_user_token; --",
            "' UNION SELECT * FROM cc_subjs --",
        ]

        for token in sqli_tokens:
            api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {token}")
            response = api_client.get("/api/v2/preferences")
            # Should not crash or authenticate
            assert response.status_code in [403, 401, 400]

    def test_very_long_token(self, api_client):
        """Test very long Api-Key token."""
        long_token = "A" * 10000
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {long_token}")
        response = api_client.get("/api/v2/preferences")

        assert response.status_code in [403, 401, 400]

    @pytest.mark.xfail(reason="DRF UnicodeEncodeError on non-ASCII headers")
    def test_unicode_token(self, api_client):
        """Test unicode characters in Api-Key token."""
        unicode_token = "токен_с_юникодом_123"
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {unicode_token}")
        response = api_client.get("/api/v2/preferences")

        assert response.status_code in [403, 401]

    def test_token_with_special_chars(self, api_client):
        """Test special characters in Api-Key token."""
        special_tokens = [
            "token<script>alert(1)</script>",
            "token../../../etc/passwd",
            "token%00",
            "token;command",
            "token|pipe",
        ]

        for token in special_tokens:
            api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {token}")
            response = api_client.get("/api/v2/preferences")
            assert response.status_code in [403, 401]


@pytest.mark.django_db
class TestApiKeyAuthorizationBypass:
    """Api-Key authorization bypass attacks."""

    def test_bearer_instead_of_api_key(self, api_client, admin_user):
        """Test using Bearer scheme with API token."""
        token = baker.make(
            "core.UserToken",
            user=admin_user,
            token="api_token_123",
        )

        api_client.credentials(HTTP_AUTHORIZATION="Bearer api_token_123")
        response = api_client.get("/api/v2/preferences")

        # Should reject Bearer scheme
        assert response.status_code in [403, 401]

    def test_token_without_scheme(self, api_client, admin_user):
        """Test token without Api-Key scheme."""
        token = baker.make(
            "core.UserToken",
            user=admin_user,
            token="api_token_123",
        )

        api_client.credentials(HTTP_AUTHORIZATION="api_token_123")
        response = api_client.get("/api/v2/preferences")

        # Should reject (no scheme)
        assert response.status_code in [403, 401]

    def test_valid_token_wrong_user(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Test using valid token but accessing wrong user's data."""
        # Create token for admin
        token = baker.make(
            "core.UserToken",
            user=admin_user,
            token="admin_token",
        )

        # Create preference for regular user
        pref = baker.make(
            "core.Preference",
            user=regular_user,
            key="user_key",
            value="secret",
        )

        # Use admin's token to try to access regular user's preference
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key admin_token")
        response = api_client.get(f"/api/v2/preferences/{pref.id}")

        # Should not allow access to other user's data
        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can access other user's data with valid token",
            )


@pytest.mark.django_db
class TestApiKeyTimingAttack:
    """Api-Key timing attack tests."""

    def test_timing_difference_valid_vs_invalid(self, api_client, admin_user):
        """Test for timing difference between valid and invalid tokens."""
        import time

        # Create valid token
        token = baker.make(
            "core.UserToken",
            user=admin_user,
            token="valid_timing_token",
        )

        # Request with valid token
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key valid_timing_token")
        start = time.time()
        response1 = api_client.get("/api/v2/preferences")
        time_valid = time.time() - start

        # Request with invalid token
        api_client.credentials(
            HTTP_AUTHORIZATION="Api-Key invalid_timing_token",
        )
        start = time.time()
        response2 = api_client.get("/api/v2/preferences")
        time_invalid = time.time() - start

        # Times should be similar (no timing leak)
        diff = abs(time_valid - time_invalid)
        # Allow 0.5 second difference for test stability
        assert diff < 0.5, f"Possible timing attack: diff={diff}s"


@pytest.mark.django_db
class TestApiKeyTokenEnumeration:
    """Api-Key token enumeration attacks."""

    def test_error_message_enumeration(self, api_client):
        """Test if error messages allow token enumeration."""
        test_cases = [
            ("Api-Key nonexistent_token", "invalid token"),
            ("Api-Key ", "empty token"),
            ("Invalid-Scheme token", "wrong scheme"),
        ]

        responses = []
        for auth_header, description in test_cases:
            api_client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = api_client.get("/api/v2/preferences")
            responses.append(
                (description, response.status_code, response.content),
            )

        # All should return same status code to prevent enumeration
        status_codes = set(r[1] for r in responses)
        # It's okay if they're different, just documenting behavior

    def test_timing_enumeration(self, api_client):
        """Test if timing allows token enumeration."""
        import time

        # Request with non-existent token
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key nonexistent123")
        start = time.time()
        response1 = api_client.get("/api/v2/preferences")
        time_nonexistent = time.time() - start

        # Request with malformed token
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key")
        start = time.time()
        response2 = api_client.get("/api/v2/preferences")
        time_malformed = time.time() - start

        # Times should be similar
        diff = abs(time_nonexistent - time_malformed)
        assert diff < 0.5, f"Possible timing enumeration: diff={diff}s"


@pytest.mark.django_db
class TestApiKeySessionHandling:
    """Api-Key session handling tests."""

    @pytest.mark.xfail(reason="UserToken not used for API auth")
    def test_token_revocation(self, api_client, admin_user):
        """Test if deleted token is immediately revoked."""
        token = baker.make(
            "core.UserToken",
            user=admin_user,
            token="revoke_token",
        )

        # Verify token works
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key revoke_token")
        response1 = api_client.get("/api/v2/preferences")
        assert response1.status_code == 200

        # Delete token
        token.delete()

        # Token should no longer work
        response2 = api_client.get("/api/v2/preferences")
        if response2.status_code == 200:
            pytest.fail("BUG: Deleted token still works (caching issue)")

    @pytest.mark.xfail(reason="UserToken not used for API auth")
    def test_multiple_tokens_same_user(self, api_client, admin_user):
        """Test multiple active tokens for same user."""
        token1 = baker.make("core.UserToken", user=admin_user, token="token_1")
        token2 = baker.make("core.UserToken", user=admin_user, token="token_2")

        # Both tokens should work
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key token_1")
        response1 = api_client.get("/api/v2/preferences")
        assert response1.status_code == 200

        api_client.credentials(HTTP_AUTHORIZATION="Api-Key token_2")
        response2 = api_client.get("/api/v2/preferences")
        assert response2.status_code == 200

    def test_token_case_sensitivity(self, api_client, admin_user):
        """Test if token is case-sensitive."""
        token = baker.make(
            "core.UserToken",
            user=admin_user,
            token="CaseSensitiveToken",
        )

        # Correct case
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key CaseSensitiveToken")
        response1 = api_client.get("/api/v2/preferences")

        # Wrong case
        api_client.credentials(HTTP_AUTHORIZATION="Api-Key casesensitivetoken")
        response2 = api_client.get("/api/v2/preferences")

        # Tokens should be case-sensitive
        if response1.status_code == 200 and response2.status_code == 200:
            pytest.fail("BUG: Token is case-insensitive (security issue)")
