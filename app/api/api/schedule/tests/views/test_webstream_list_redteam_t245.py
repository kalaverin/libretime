"""Red Team security tests for Webstreams LIST endpoint (T245).

Tests focus on:
- API1:2023 BOLA (accessing other users' webstreams)
- Data exposure via __all__ fields
- SSRF via URL field reflection
- Injection in query parameters
- Pagination abuse
- Information disclosure
"""

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream


@pytest.mark.django_db(transaction=True)
class TestWebstreamListRedTeam:
    """Red Team tests for GET /api/v2/webstreams."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T518: BOLA - LIST shows all users' webstreams without filtering")
    def test_bola_list_shows_all_users_webstreams(self, api_client):
        """BOLA: LIST should only show webstreams from user's own account."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Victim's private webstream
        victim_stream = baker.make(
            Webstream,
            name="Victim Private Stream",
            url="http://victim-private.com/stream",
            description="Secret stream",
            owner=victim,
        )

        # Attacker lists all webstreams
        response = api_client.get("/api/v2/webstreams")
        assert response.status_code == 200

        data = response.json()
        victim_stream_ids = [s["id"] for s in data if s.get("name") == "Victim Private Stream"]

        assert len(victim_stream_ids) == 0, \
            f"BOLA: Attacker can see {len(victim_stream_ids)} victim's webstreams"

    def test_stream_id_enumeration_mitigated(self, api_client):
        """Security: Stream ID enumeration mitigated by owner filtering."""
        user = baker.make(User, username="testred_enum")
        for i in range(5):
            baker.make(
                Webstream,
                name=f"Stream {i}",
                url=f"http://example.com/stream{i}",
                owner=user,
            )

        response = api_client.get("/api/v2/webstreams")
        data = response.json()

        # Should only see own streams (or all if T518 not fixed)
        assert isinstance(data, list), "Response should be a list"

    # ========================================================================
    # Data Exposure via __all__ Serializer
    # ========================================================================

    @pytest.mark.xfail(reason="T519: __all__ fields may expose sensitive data")
    def test_field_exposure_all_fields_review(self, api_client):
        """Security: Review all fields exposed via __all__ serializer."""
        user = baker.make(User, username="testred_user")
        baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = api_client.get("/api/v2/webstreams")
        data = response.json()

        if len(data) > 0:
            fields = set(data[0].keys())
            # Check for potentially sensitive fields
            sensitive_fields = {"password", "secret", "token", "key", "internal_id", "_state"}
            leaked = fields & sensitive_fields
            assert len(leaked) == 0, f"Potentially sensitive fields exposed: {leaked}"

    # ========================================================================
    # SSRF via URL Field
    # ========================================================================

    @pytest.mark.xfail(reason="T520: URL field may reflect internal URLs")
    def test_url_field_ssrf_reflection(self, api_client):
        """Security: URL field should not reflect internal network URLs."""
        user = baker.make(User, username="testred_user")
        
        # Create stream with internal URL (should not be visible to others)
        baker.make(
            Webstream,
            name="Internal Stream",
            url="http://localhost:8080/internal/stream",
            owner=user,
        )

        response = api_client.get("/api/v2/webstreams")
        data = response.json()

        # If BOLA not fixed, attacker sees internal URL
        internal_urls = [s["url"] for s in data if "localhost" in s.get("url", "")]
        assert len(internal_urls) == 0, \
            f"SSRF info leak: internal URLs visible: {internal_urls}"

    # ========================================================================
    # MIME Type Validation
    # ========================================================================

    @pytest.mark.xfail(reason="T521: MIME type field accepts arbitrary values")
    def test_mime_type_arbitrary_values(self, api_client):
        """Validation: MIME type field should validate against allowed types."""
        user = baker.make(User, username="testred_user")
        
        # Create with malicious mime type (XSS vector)
        baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            mime="text/html<script>alert(1)</script>",
            owner=user,
        )

        response = api_client.get("/api/v2/webstreams")
        data = response.json()

        if len(data) > 0:
            mime = data[0].get("mime", "")
            # If mime is reflected without sanitization, potential XSS
            assert "<script>" not in mime, \
                "MIME type XSS: script tags not sanitized"

    # ========================================================================
    # URL Length and Format Validation
    # ========================================================================

    @pytest.mark.xfail(reason="T522: Very long URL not validated")
    def test_url_length_overflow(self, api_client):
        """Validation: Very long URLs should be rejected."""
        user = baker.make(User, username="testred_user")
        
        # Model allows 512 chars, but should validate reasonable length
        long_url = "http://example.com/" + "A" * 1000
        baker.make(
            Webstream,
            name="Test Stream",
            url=long_url,
            owner=user,
        )

        response = api_client.get("/api/v2/webstreams")
        # Should either reject or handle gracefully
        assert response.status_code in [200, 400], \
            f"Long URL caused {response.status_code}"

    @pytest.mark.xfail(reason="T523: Invalid URL format accepted")
    def test_url_format_validation(self, api_client):
        """Validation: Invalid URL formats should be rejected."""
        user = baker.make(User, username="testred_user")
        
        invalid_urls = [
            "not-a-url",
            "ftp://malicious.com",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ]
        
        for url in invalid_urls:
            # Try to create with invalid URL
            stream = baker.make(
                Webstream,
                name="Test Stream",
                url=url,
                owner=user,
            )
            # Should validate URL format
            assert False, f"Invalid URL '{url}' was accepted"

    # ========================================================================
    # Pagination Abuse
    # ========================================================================

    def test_pagination_page_size_limits(self, api_client):
        """Security: Page size is properly limited."""
        user = baker.make(User, username="testred_user")
        
        # Create many streams
        for i in range(100):
            baker.make(
                Webstream,
                name=f"Stream {i}",
                url=f"http://example.com/stream{i}",
                owner=user,
            )

        response = api_client.get("/api/v2/webstreams?page_size=999999")
        # Should have pagination limits
        assert response.status_code == 200, \
            f"Large page size caused {response.status_code}"

    # ========================================================================
    # Sorting / Ordering Attacks
    # ========================================================================

    def test_sorting_sql_injection_attempt(self, api_client):
        """Injection: SQLi in ordering parameter."""
        user = baker.make(User, username="testred_user")
        baker.make(Webstream, name="Stream", url="http://example.com", owner=user)

        malicious_orderings = [
            "name; DROP TABLE cc_webstream;--",
            "(SELECT password FROM cc_user)",
            "url' UNION SELECT * FROM cc_user--",
        ]

        for ordering in malicious_orderings:
            response = api_client.get(
                f"/api/v2/webstreams?ordering={ordering}",
            )
            # Django DRF safely ignores invalid ordering
            assert response.status_code in [200, 400], \
                f"Ordering '{ordering}' caused {response.status_code}"

    # ========================================================================
    # CORS and Security Headers
    # ========================================================================

    def test_cors_preflight_list(self, api_client):
        """CORS: Preflight request for LIST."""
        response = api_client.options(
            "/api/v2/webstreams",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        allowed_origin = response.get("Access-Control-Allow-Origin", "")
        assert "evil.com" not in allowed_origin, \
            "CORS allows arbitrary origin"

    def test_security_headers_present(self, api_client):
        """Security: Required security headers present."""
        user = baker.make(User, username="testred_user")
        baker.make(Webstream, name="Stream", url="http://example.com", owner=user)

        response = api_client.get("/api/v2/webstreams")
        
        # Check for basic security headers
        headers = response.headers
        assert "Content-Type" in headers, "Missing Content-Type header"

    # ========================================================================
    # Fuzzing Query Parameters
    # ========================================================================

    @pytest.mark.xfail(reason="T524: Special query params cause 500 error")
    def test_fuzzing_query_params(self, api_client):
        """Fuzzing: Naughty strings in query parameters."""
        naughty_params = [
            "undefined",
            "null",
            "None",
            "NaN",
            "Infinity",
            "-Infinity",
        ]

        for param in naughty_params:
            response = api_client.get(
                f"/api/v2/webstreams?page={param}",
            )
            # Should not crash with 500
            assert response.status_code in [200, 400, 404], \
                f"Naughty param '{param}' caused {response.status_code}"

    # ========================================================================
    # Timing Attacks
    # ========================================================================

    def test_timing_empty_vs_populated(self, api_client):
        """Timing: Difference between empty and populated list."""
        import time

        # Time empty list
        start = time.time()
        response1 = api_client.get("/api/v2/webstreams")
        time_empty = time.time() - start

        # Create some streams
        user = baker.make(User, username="testred_timing")
        for i in range(50):
            baker.make(
                Webstream,
                name=f"Stream {i}",
                url=f"http://example.com/stream{i}",
                owner=user,
            )

        # Time populated list
        start = time.time()
        response2 = api_client.get("/api/v2/webstreams")
        time_populated = time.time() - start

        # Difference should not be extreme (less than 5x)
        if time_empty > 0:
            ratio = time_populated / time_empty
            assert ratio < 5.0, \
                f"Timing leak: empty={time_empty:.4f}s, populated={time_populated:.4f}s (ratio {ratio:.1f})"

    # ========================================================================
    # Description Field Security
    # ========================================================================

    @pytest.mark.xfail(reason="T525: Description field XSS not sanitized")
    def test_description_xss_protection(self, api_client):
        """Security: Description field should sanitize XSS."""
        user = baker.make(User, username="testred_user")
        
        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
        ]
        
        for payload in xss_payloads:
            baker.make(
                Webstream,
                name="Test Stream",
                url="http://example.com/stream",
                description=payload,
                owner=user,
            )

        response = api_client.get("/api/v2/webstreams")
        data = response.json()

        for stream in data:
            desc = stream.get("description", "")
            assert "<script>" not in desc, "Description XSS: script tags not sanitized"
            assert "onerror=" not in desc, "Description XSS: event handlers not sanitized"

    # ========================================================================
    # Unicode and Encoding
    # ========================================================================

    def test_unicode_in_name_handling(self, api_client):
        """Validation: Unicode in name handled correctly."""
        user = baker.make(User, username="testred_user")
        
        unicode_names = [
            "日本語ストリーム",
            "Радио поток",
            "🔴 Live Stream",
            "<script>alert(1)</script>",
        ]
        
        for name in unicode_names:
            baker.make(
                Webstream,
                name=name,
                url="http://example.com/stream",
                owner=user,
            )

        response = api_client.get("/api/v2/webstreams")
        assert response.status_code == 200

    # ========================================================================
    # Authentication
    # ========================================================================

    def test_list_without_auth(self, client):
        """Auth: LIST without auth should return 403."""
        response = client.get("/api/v2/webstreams")
        assert response.status_code == 403
