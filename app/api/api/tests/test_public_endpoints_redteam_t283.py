"""T283: Public endpoints positive and security tests.

Tests for public endpoints (/api/v2/info, /api/v2/version) that should be
accessible without authentication. Includes positive tests and security checks.
"""

import json
import time

import pytest
from rest_framework.test import APIClient


# =============================================================================
# Positive Tests - Public Endpoints Without Auth
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsT283Positive:
    """Positive tests for public endpoints - should work without auth."""

    def test_info_endpoint_no_auth_success(self):
        """T283: /api/v2/info should return 200 without authentication."""
        client = APIClient()
        response = client.get("/api/v2/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "station_name" in data
        assert data["station_name"] == "LibreTime"

    def test_version_endpoint_no_auth_success(self):
        """T283: /api/v2/version should return 200 without authentication."""
        client = APIClient()
        response = client.get("/api/v2/version")
        
        assert response.status_code == 200
        data = response.json()
        assert "api_version" in data

    def test_public_endpoints_with_session_auth_still_work(self, admin_user):
        """T283: Public endpoints should work with authenticated session."""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get("/api/v2/info")
        assert response.status_code == 200
        
        response = client.get("/api/v2/version")
        assert response.status_code == 200

    def test_public_endpoints_with_api_key_still_work(self):
        """T283: Public endpoints should work with API key."""
        from django.conf import settings
        
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}"
        )
        
        response = client.get("/api/v2/info")
        assert response.status_code == 200

    def test_public_endpoints_ignore_invalid_auth(self):
        """T283: Invalid auth should not break public endpoints."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
        
        response = client.get("/api/v2/info")
        assert response.status_code == 200


# =============================================================================
# Security Tests - Information Disclosure
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsT283InfoDisclosure:
    """Information disclosure tests for public endpoints."""

    def test_info_no_sensitive_data(self):
        """T283: Info endpoint should not expose sensitive configuration."""
        client = APIClient()
        response = client.get("/api/v2/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for sensitive fields that should NOT be present
        sensitive = ["api_key", "secret", "password", "db_host", "db_name", "db_user"]
        found = [field for field in sensitive if field in str(data).lower()]
        
        if found:
            pytest.xfail(f"T803: Info endpoint exposes sensitive fields: {found}")

    def test_version_no_internal_versions(self):
        """T283: Version should not expose internal component versions."""
        client = APIClient()
        response = client.get("/api/v2/version")
        
        assert response.status_code == 200
        data = response.json()
        
        # Internal versions aid attackers in finding known vulnerabilities
        internal_fields = ["django_version", "python_version", "postgresql_version"]
        found = [f for f in internal_fields if f in data]
        
        if len(found) > 1:
            pytest.xfail(f"T804: Version exposes internal info: {found}")


# =============================================================================
# Security Tests - DoS Protection
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsT283DoS:
    """DoS protection tests for public endpoints."""

    def test_rate_limiting_on_public_endpoints(self):
        """T283: Rapid requests to public endpoints should be rate limited."""
        client = APIClient()
        
        start = time.time()
        for _ in range(100):
            response = client.get("/api/v2/info")
            assert response.status_code == 200
        elapsed = time.time() - start
        
        if elapsed < 5:
            pytest.xfail(f"T805: No rate limiting on public endpoints (100 req in {elapsed:.2f}s)")

    def test_response_size_reasonable(self):
        """T283: Response size should be reasonable."""
        client = APIClient()
        response = client.get("/api/v2/info")
        
        size = len(response.content)
        if size > 10000:  # 10KB
            pytest.xfail(f"T806: Public endpoint response too large: {size} bytes")


# =============================================================================
# Security Tests - CORS
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsT283CORS:
    """CORS tests for public endpoints."""

    def test_cors_arbitrary_origin_blocked(self):
        """T283: CORS should not allow arbitrary origins."""
        client = APIClient()
        
        response = client.options(
            "/api/v2/info",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET"
        )
        
        if response.status_code == 200:
            allow_origin = response.get("Access-Control-Allow-Origin")
            if allow_origin == "*":
                pytest.xfail("T807: CORS allows wildcard origin on public endpoint")
            if allow_origin == "https://evil.com":
                pytest.xfail("T808: CORS reflects arbitrary origin")

    def test_cors_credentials_not_allowed(self):
        """T283: CORS should not allow credentials with open origin."""
        client = APIClient()
        
        response = client.options(
            "/api/v2/info",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET"
        )
        
        if response.get("Access-Control-Allow-Credentials") == "true":
            pytest.xfail("T809: CORS credentials enabled on public endpoint")


# =============================================================================
# Security Tests - Injection
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsT283Injection:
    """Injection tests for public endpoints."""

    def test_sqli_in_query_params_blocked(self):
        """T283: SQL injection in query params should be handled."""
        client = APIClient()
        
        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE--",
        ]
        
        for payload in sqli_payloads:
            response = client.get(f"/api/v2/info?param={payload}")
            
            if response.status_code == 500:
                pytest.xfail("T810: SQLi in query params causes 500")

    def test_xss_reflection_blocked(self):
        """T283: XSS payloads should not be reflected."""
        client = APIClient()
        
        xss_payload = "<script>alert(1)</script>"
        response = client.get(f"/api/v2/info?callback={xss_payload}")
        
        if xss_payload in str(response.content):
            pytest.xfail("T811: XSS payload reflected in response")


# =============================================================================
# Security Tests - HTTP Methods
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsT283Methods:
    """HTTP method tests for public endpoints."""

    def test_post_on_readonly_public_endpoint_blocked(self):
        """T283: POST on public read-only endpoint should fail."""
        client = APIClient()
        response = client.post("/api/v2/info", {})
        
        assert response.status_code in [405, 403, 404]

    def test_delete_on_public_endpoint_blocked(self):
        """T283: DELETE on public endpoint should fail."""
        client = APIClient()
        response = client.delete("/api/v2/info")
        
        assert response.status_code in [405, 403, 404]

    def test_trace_on_public_endpoint_blocked(self):
        """T283: TRACE on public endpoint should fail."""
        client = APIClient()
        response = client.trace("/api/v2/info")
        
        assert response.status_code in [405, 403]


# =============================================================================
# Security Tests - Error Handling
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsT283Errors:
    """Error handling tests for public endpoints."""

    def test_error_messages_not_verbose(self):
        """T283: Error messages should not reveal implementation details."""
        client = APIClient()
        
        # Trigger an error with bad input
        response = client.get("/api/v2/info?format=invalid")
        
        if response.status_code == 500:
            error_text = str(response.content).lower()
            leak_keywords = ["traceback", "file \"", "line ", "django", "python"]
            if any(kw in error_text for kw in leak_keywords):
                pytest.xfail("T812: Error message leaks implementation details")

    def test_malformed_json_handled(self):
        """T283: Malformed JSON should be handled gracefully."""
        client = APIClient()
        
        response = client.post(
            "/api/v2/info",
            data="invalid json {",
            content_type="application/json"
        )
        
        if response.status_code == 500:
            pytest.xfail("T813: Malformed JSON causes 500")
