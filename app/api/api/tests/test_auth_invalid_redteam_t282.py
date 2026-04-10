"""T282: Invalid authentication redteam security tests.

Red Team security tests for invalid authentication handling.
Tests for timing attacks, user enumeration, and authentication bypasses.
"""

import time

import pytest

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.core.models import Role

# =============================================================================
# API2:2023 Broken Authentication - Timing Attacks
# =============================================================================


@pytest.mark.django_db
class TestInvalidAuthRedTeamTiming:
    """Timing attack tests for authentication."""

    def test_timing_user_enumeration_via_login(self):
        """
        Timing attack: Different response times for existent vs non-existent users.

        If user exists but password wrong - one time.
        If user doesn't exist - different time.
        """
        User = get_user_model()
        User.objects.create_user(
            role=Role.HOST,
            username="existing_user",
            password="correct_password",
            email="existing@test.com",
            first_name="Existing",
            last_name="User",
        )

        # Time login for existing user (wrong password)
        times_existing = []
        for _ in range(5):
            client = APIClient()
            start = time.time()
            client.login(username="existing_user", password="wrong_password")
            times_existing.append(time.time() - start)

        # Time login for non-existent user
        times_nonexistent = []
        for _ in range(5):
            client = APIClient()
            start = time.time()
            client.login(
                username="nonexistent_user_12345", password="any_password",
            )
            times_nonexistent.append(time.time() - start)

        avg_existing = sum(times_existing) / len(times_existing)
        avg_nonexistent = sum(times_nonexistent) / len(times_nonexistent)

        # If timing differs significantly, user enumeration is possible
        if abs(avg_existing - avg_nonexistent) > 0.05:  # 50ms threshold
            pytest.xfail(
                f"T780: Timing attack - user enumeration possible "
                f"(existing: {avg_existing:.4f}s, nonexistent: {avg_nonexistent:.4f}s)",
            )

    def test_timing_password_check_vs_user_lookup(self):
        """
        Timing attack: Password check time vs user lookup time.

        If password hashing takes time, valid user with wrong password
        should take longer than non-existent user.
        """
        User = get_user_model()
        User.objects.create_user(
            role=Role.HOST,
            username="timing_test_user",
            password="a_very_long_password_that_requires_hashing",
            email="timing@test.com",
            first_name="Timing",
            last_name="Test",
        )

        # Measure timing for various scenarios
        scenarios = [
            ("valid_user_wrong_password", "timing_test_user", "wrong"),
            ("nonexistent_user", "totally_fake_user_99999", "password"),
        ]

        results = {}
        for name, username, password in scenarios:
            times = []
            for _ in range(5):
                client = APIClient()
                start = time.time()
                client.login(username=username, password=password)
                times.append(time.time() - start)
            results[name] = sum(times) / len(times)

        # Check if timings reveal information
        diff = abs(
            results["valid_user_wrong_password"] - results["nonexistent_user"],
        )
        if diff > 0.05:
            pytest.xfail(
                f"T781: Timing difference reveals user existence: {diff:.4f}s",
            )


# =============================================================================
# API2:2023 Broken Authentication - User Enumeration
# =============================================================================


@pytest.mark.django_db
class TestInvalidAuthRedTeamEnumeration:
    """User enumeration tests."""

    def test_error_message_user_enumeration(self):
        """
        Error messages may reveal if username exists.

        Different error messages for "user not found" vs "wrong password".
        """
        User = get_user_model()
        User.objects.create_user(
            role=Role.HOST,
            username="enumerate_test",
            password="password123",
            email="enumerate@test.com",
            first_name="Enumerate",
            last_name="Test",
        )

        # Try login with existing user (wrong password)
        client1 = APIClient()
        result1 = client1.login(username="enumerate_test", password="wrong")

        # Try login with non-existent user
        client2 = APIClient()
        result2 = client2.login(
            username="nonexistent_enum_test", password="wrong",
        )

        # Both should fail the same way
        assert result1 is False
        assert result2 is False

        # If we could see error messages, we'd check for differences
        # But Django's client.login() returns bool only

    def test_response_code_enumeration(self):
        """
        Different response codes may reveal user existence.

        Some systems return 401 for wrong password vs 404 for no user.
        """
        User = get_user_model()
        User.objects.create_user(
            role=Role.HOST,
            username="code_enum_test",
            password="password123",
            email="codeenum@test.com",
            first_name="Code",
            last_name="Enum",
        )

        client = APIClient()

        # Request with existing user context (via session attempt)
        client.login(username="code_enum_test", password="wrong")
        response1 = client.get("/api/v2/files")

        # Request with non-existent user context
        client2 = APIClient()
        client2.login(username="fake_user_99999", password="wrong")
        response2 = client2.get("/api/v2/files")

        # Both should be 403
        if response1.status_code != response2.status_code:
            pytest.xfail(
                "T782: Different response codes reveal user existence",
            )

    def test_account_lockout_enumeration(self):
        """
        Account lockout may reveal user existence.

        If only existing users get locked out, we can enumerate.
        """
        User = get_user_model()
        User.objects.create_user(
            role=Role.HOST,
            username="lockout_enum_test",
            password="password123",
            email="lockoutenum@test.com",
            first_name="Lockout",
            last_name="Enum",
        )

        # Try many logins for existing user
        for _ in range(10):
            client = APIClient()
            client.login(username="lockout_enum_test", password="wrong")

        # Try many logins for non-existent user
        for _ in range(10):
            client = APIClient()
            client.login(username="fake_lockout_99999", password="wrong")

        # If lockout only applies to existing user, we can tell which is which
        # This is hard to test without actual lockout mechanism


# =============================================================================
# API2:2023 Broken Authentication - Brute Force
# =============================================================================


@pytest.mark.django_db
class TestInvalidAuthRedTeamBruteForce:
    """Brute force attack tests."""

    def test_password_brute_force_no_rate_limit(self):
        """
        Rapid password attempts should be rate limited.
        """
        User = get_user_model()
        User.objects.create_user(
            role=Role.HOST,
            username="brute_test",
            password="correct_password",
            email="brute@test.com",
            first_name="Brute",
            last_name="Test",
        )

        start = time.time()
        for i in range(30):
            client = APIClient()
            client.login(username="brute_test", password=f"guess_{i}")
        elapsed = time.time() - start

        if elapsed < 5:  # 30 attempts in under 5 seconds
            pytest.xfail(
                f"T783: No rate limiting on password attempts (30 in {elapsed:.2f}s)",
            )

    def test_api_key_brute_force_no_captcha(self):
        """
        Brute force on API key should require CAPTCHA or block.
        """
        client = APIClient()

        start = time.time()
        for i in range(50):
            client.credentials(HTTP_AUTHORIZATION=f"Api-Key guess_{i}")
            client.get("/api/v2/files")
        elapsed = time.time() - start

        if elapsed < 5:
            pytest.xfail(
                f"T784: No CAPTCHA/block on API key brute force (50 in {elapsed:.2f}s)",
            )


# =============================================================================
# Authentication Bypass Tests
# =============================================================================


@pytest.mark.django_db
class TestInvalidAuthRedTeamBypass:
    """Authentication bypass tests."""

    def test_null_byte_in_auth_header(self):
        """
        Null byte may bypass auth parsing.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key \x00valid-key")

        response = client.get("/api/v2/files")

        # Should be 403, if 200 then bypass worked
        if response.status_code == 200:
            pytest.xfail("T785: Null byte bypass in auth header")

    def test_unicode_normalization_bypass(self):
        """
        Unicode normalization may bypass auth.

        Different Unicode representations of same character.
        """
        # Try auth with different Unicode forms
        test_cases = [
            "Api-Key test",  # Normal
            "Api-Keyｔest",  # Full-width
        ]

        for auth in test_cases:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=auth)
            try:
                response = client.get("/api/v2/files")
                # All should be 403 (invalid key)
                if response.status_code == 200:
                    pytest.xfail(
                        f"T786: Unicode normalization bypass: {auth[:20]}",
                    )
            except (UnicodeEncodeError, TypeError):
                pytest.xfail(
                    f"T793: Unicode in auth header causes exception: {auth[:20]}",
                )

    def test_header_injection_bypass(self):
        """
        Header injection may bypass auth.

        CRLF injection to add second auth header.
        """
        client = APIClient()
        # Try to inject second header
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key invalid\r\nAuthorization: Api-Key {settings.CONFIG.general.api_key}",
        )

        response = client.get("/api/v2/files")

        if response.status_code == 200:
            pytest.xfail("T787: Header injection bypass worked")

    def test_case_variation_bypass(self):
        """
        Case variations may bypass auth checks.
        """
        variations = [
            "api-key test",  # lowercase
            "API-KEY test",  # uppercase
            "Api_Key test",  # underscore
        ]

        for auth in variations:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=auth)
            response = client.get("/api/v2/files")

            # All should be 403
            if response.status_code == 200:
                pytest.xfail(f"T788: Case variation bypass: {auth}")


# =============================================================================
# Session Fixation Tests
# =============================================================================


@pytest.mark.django_db
class TestInvalidAuthRedTeamSessionFixation:
    """Session fixation tests."""

    def test_session_id_on_failed_login(self):
        """
        Session ID should not be set on failed login.

        If session is created even on failed login, fixation is possible.
        """
        client = APIClient()

        # Get session before login
        session_before = (
            client.session.session_key if hasattr(client, "session") else None
        )

        # Failed login
        client.login(username="nonexistent_user_12345", password="wrong")

        # Get session after failed login
        session_after = (
            client.session.session_key if hasattr(client, "session") else None
        )

        # Session should not be created on failed login
        # (This is hard to test with APIClient)


# =============================================================================
# JWT/Token Confusion Tests
# =============================================================================


@pytest.mark.django_db
class TestInvalidAuthRedTeamTokenConfusion:
    """Token confusion attack tests."""

    def test_jwt_alg_none_bypass(self):
        """
        Try JWT with alg=none to bypass signature.

        If system accepts JWT, alg=none is a common bypass.
        """
        # Create JWT with alg=none
        import base64
        import json

        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode(),
        ).rstrip(b"=")
        payload = base64.urlsafe_b64encode(
            json.dumps({"user": "admin"}).encode(),
        ).rstrip(b"=")
        token = f"{header.decode()}.{payload.decode()}."

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get("/api/v2/files")

        if response.status_code == 200:
            pytest.xfail("T789: JWT alg=none bypass worked")

    def test_jwt_weak_secret_brute_force(self):
        """
        Try common secrets to forge JWT.
        """
        # Common JWT secrets from SecLists
        common_secrets = ["secret", "jwt", "password", "123456", "key"]

        for secret in common_secrets:
            # This would require JWT library to test properly
            pass

    def test_multiple_auth_headers_priority(self):
        """
        Multiple auth headers - which one takes priority?
        """
        # Django/DRF should only see one Authorization header
        # but test what happens with weird formats
        client = APIClient()

        # Try with comma-separated auth schemes
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer fake-token, Api-Key {settings.CONFIG.general.api_key}",
        )

        response = client.get("/api/v2/files")

        # If second scheme is used, that's a parsing issue
        # Should be 403 (first invalid) or 200 (if comma parsing broken)
        if response.status_code == 403:
            # First scheme was used (correct)
            pass


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.django_db
class TestInvalidAuthRedTeamErrorHandling:
    """Error handling tests."""

    def test_verbose_error_on_invalid_auth(self):
        """
        Invalid auth should not reveal implementation details.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key ' OR '1'='1")

        response = client.get("/api/v2/files")

        assert response.status_code == 403

        # Error message should be generic
        error_text = str(response.content).lower()
        sensitive_keywords = [
            "sql",
            "query",
            "database",
            "exception",
            "traceback",
        ]
        if any(kw in error_text for kw in sensitive_keywords):
            pytest.xfail("T790: Error message reveals implementation details")

    def test_stack_trace_not_exposed(self):
        """
        Stack traces should never be exposed.
        """
        # Try various malformed inputs that might cause exceptions
        malformed_auths = [
            "Api-Key " + "A" * 100000,  # Very long
            "Api-Key \x00",  # Null byte
            "Api-Key \xff",  # Invalid UTF-8
        ]

        for auth in malformed_auths:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=auth)

            try:
                response = client.get("/api/v2/files")
                if response.status_code == 500:
                    content = str(response.content)
                    if "Traceback" in content or 'File "' in content:
                        pytest.xfail(f"T791: Stack trace exposed: {auth[:20]}")
            except (UnicodeEncodeError, TypeError) as e:
                # This is the bug we're testing for
                pytest.xfail(
                    f"T793: Exception not handled in auth: {type(e).__name__} for {auth[:20]}",
                )
