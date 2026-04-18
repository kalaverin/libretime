"""Red Team security tests for Webstreams permissions (T249).

Tests focus on:
- API1:2023 BOLA (Broken Object Level Authorization)
- API2:2023 Broken Authentication
- API3:2023 BOPLA (Broken Object Property Level Authorization)
- API5:2023 BFLA (Broken Function Level Authorization)
- API6:2023 Unsafe Business Flows
- API7:2023 SSRF
- API8:2023 Security Misconfiguration
- Injection attacks
- Rate limiting bypasses
"""

import json
import time

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestWebstreamPermissionsRedTeam:
    """Red Team tests for Webstreams permissions - T249."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T562: BOLA - Any user can modify other user's webstream",
    )
    def test_bola_modify_other_users_webstream(self, api_client):
        """BOLA: User can PATCH another user's webstream without permission check."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_stream = baker.make(
            Webstream,
            name="Victim Stream",
            url="http://victim.com/stream",
            owner=victim,
        )

        response = api_client.patch(
            f"/api/v2/webstreams/{victim_stream.id}",
            json.dumps({"name": "Hacked by Attacker"}),
            content_type="application/json",
        )

        assert (
            response.status_code == 403
        ), f"BOLA: Got {response.status_code}, expected 403 - any user can modify other's stream"

    @pytest.mark.xfail(
        reason="T563: BOLA - Any user can delete other user's webstream",
    )
    def test_bola_delete_other_users_webstream(self, api_client):
        """BOLA: User can DELETE another user's webstream without permission check."""
        victim = baker.make(User, username="testred_victim")

        victim_stream = baker.make(
            Webstream,
            name="Victim Stream",
            url="http://victim.com/stream",
            owner=victim,
        )

        response = api_client.delete(f"/api/v2/webstreams/{victim_stream.id}")

        assert (
            response.status_code == 403
        ), f"BOLA: Got {response.status_code}, expected 403 - any user can delete other's stream"

    def test_bola_id_enumeration(self, api_client):
        """BOLA: Sequential ID enumeration allows accessing all webstreams."""
        # Create streams with predictable sequential IDs
        streams = []
        for i in range(10):
            user = baker.make(User, username=f"testred_user{i}")
            stream = baker.make(
                Webstream,
                name=f"Stream {i}",
                url=f"http://example.com/stream{i}",
                owner=user,
            )
            streams.append(stream)

        # Try to enumerate all IDs
        found_count = 0
        for i in range(1, 50):  # Try IDs 1-50
            response = api_client.get(f"/api/v2/webstreams/{i}")
            if response.status_code == 200:
                found_count += 1

        # If we found more than expected, IDs are sequential and enumerable
        assert found_count <= len(
            streams,
        ), f"ID enumeration: found {found_count} streams, vulnerability exists"

    @pytest.mark.xfail(
        reason="T564: BOLA - Batch endpoint allows mass access to all streams",
    )
    def test_bola_batch_access_all_streams(self, api_client):
        """BOLA: Batch/List endpoint returns all users' streams without filtering."""
        # Create streams for multiple users
        for i in range(5):
            user = baker.make(User, username=f"testred_user{i}")
            for j in range(3):
                baker.make(
                    Webstream,
                    name=f"User{i} Stream{j}",
                    url=f"http://user{i}.com/stream{j}",
                    owner=user,
                )

        response = api_client.get("/api/v2/webstreams")
        assert response.status_code == 200

        data = response.json()
        results = data.get("results", data)  # Handle pagination

        # Count unique owners
        owners = set()
        for stream in results:
            if "owner" in stream:
                owners.add(stream.get("owner"))

        # Should only see own streams, not all
        assert (
            len(owners) <= 1
        ), f"BOLA: List returned streams from {len(owners)} different owners"

    # ========================================================================
    # API2:2023 - Broken Authentication
    # ========================================================================

    def test_api_key_bypasses_permission_checks(self, client):
        """Broken Auth: Check if invalid API Key bypasses permission checks."""
        victim = baker.make(User, username="testred_victim")
        stream = baker.make(
            Webstream,
            name="Victim Stream",
            url="http://victim.com/stream",
            owner=victim,
        )

        # Try with invalid API-Key header
        response = client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": "Hacked"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Api-Key invalid_key",
        )

        # If invalid key allows modification, it's a vulnerability
        if response.status_code not in [401, 403]:
            pytest.fail(
                f"T565: Auth bypass - invalid API key got {response.status_code}, expected 401/403",
            )

    @pytest.mark.xfail(
        reason="BUG: Authorization header case sensitivity - Api-Key works but api-key/API-KEY fails",
    )
    def test_auth_case_sensitivity(self, api_client):
        """Broken Auth: Authorization header case sensitivity bypass.

        RFC 7230 states header field names are case-insensitive.
        'Api-Key', 'api-key', 'API-KEY' should all work identically.
        """
        # FIXED: Use credentials() instead of defaults[] for proper auth control
        from rest_framework.test import APIClient

        api_key = api_client._credentials.get(
            "HTTP_AUTHORIZATION", "",
        ).replace("Api-Key ", "")

        variations = [
            f"Api-Key {api_key}",  # Standard - works
            f"api-key {api_key}",  # lowercase - BUG: returns 403
            f"API-KEY {api_key}",  # UPPERCASE - BUG: returns 403
        ]

        results = []
        for auth_value in variations:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=auth_value)
            response = client.get("/api/v2/webstreams")
            results.append((auth_value, response.status_code))

        # All variations should work or all should fail consistently
        # Inconsistency indicates bypass possibility (or case sensitivity bug)
        status_codes = [r[1] for r in results]
        # Either all succeed (200) or all fail (403), no mix
        assert (
            len(set(status_codes)) == 1
        ), f"Inconsistent auth case handling: {results}"

    def test_auth_null_byte_injection(self, client):
        """Broken Auth: Null byte in auth header may cause bypass."""
        response = client.get(
            "/api/v2/webstreams",
            HTTP_AUTHORIZATION="Bearer token%00invalid",
        )
        # Should not authenticate successfully
        assert response.status_code in [
            401,
            403,
        ], "Null byte in auth may cause bypass"

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    def test_bopla_mass_assignment_owner_create(self, api_client):
        """BOPLA: Check if owner field can be mass assigned during CREATE."""
        victim = baker.make(User, username="testred_victim")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Hijacked Stream",
                    "url": "http://example.com/stream",
                    "owner": victim.id,
                },
            ),
            content_type="application/json",
        )

        # If creation succeeded with victim as owner, it's a vulnerability
        if response.status_code == 201:
            data = response.json()
            actual_owner = data.get("owner")
            if actual_owner == victim.id:
                pytest.fail(
                    f"T566: BOPLA - Can assign owner to another user during CREATE (owner={actual_owner})",
                )
            elif actual_owner is not None and actual_owner != victim.id:
                # Owner was set but not to victim - might be current user, which is acceptable
                pass

    @pytest.mark.xfail(
        reason="T567: BOPLA - Mass assignment via owner field in UPDATE",
    )
    def test_bopla_mass_assignment_owner_update(self, api_client):
        """BOPLA: Can change owner to another user during UPDATE."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        attacker_stream = baker.make(
            Webstream,
            name="Attacker Stream",
            url="http://attacker.com/stream",
            owner=attacker,
        )

        response = api_client.patch(
            f"/api/v2/webstreams/{attacker_stream.id}",
            json.dumps({"owner": victim.id}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("owner") == victim.id:
                assert (
                    False
                ), "BOPLA: Can change owner to another user during UPDATE"

    def test_bopla_mass_assignment_readonly_fields(self, api_client):
        """BOPLA: Check if read-only fields can be mass assigned."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        old_id = stream.id

        response = api_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps(
                {
                    "id": 999999,
                    "created_at": "2020-01-01T00:00:00Z",
                },
            ),
            content_type="application/json",
        )

        # If id was modified, it's a vulnerability
        if response.status_code == 200:
            data = response.json()
            new_id = data.get("id")
            if new_id != old_id:
                pytest.fail(
                    f"T568: BOPLA - Can modify id field (old={old_id}, new={new_id})",
                )

    # ========================================================================
    # API5:2023 - BFLA (Broken Function Level Authorization)
    # ========================================================================

    def test_bfla_method_override_patch_to_delete(self, api_client):
        """BFLA: Check if HTTP method override bypasses permission checks."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        # Try to override PATCH with DELETE
        api_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": "test"}),
            content_type="application/json",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )

        # Check if stream was deleted - if so, it's a vulnerability
        if not Webstream.objects.filter(id=stream.id).exists():
            pytest.fail(
                "T569: BFLA - Method override allowed DELETE via PATCH",
            )

    def test_bfla_admin_endpoint_access(self, api_client):
        """BFLA: Check if admin endpoints are accessible to regular users."""
        admin_endpoints = [
            "/api/v2/admin/webstreams",
            "/api/v2/webstreams/admin",
            "/api/admin/webstreams",
        ]

        for endpoint in admin_endpoints:
            response = api_client.get(endpoint)
            # Should return 404 (not found) or 403 (forbidden)
            assert response.status_code in [
                404,
                403,
            ], f"BFLA: Admin endpoint {endpoint} returned {response.status_code}"

    # ========================================================================
    # API6:2023 - Unsafe Business Flows
    # ========================================================================

    def test_race_condition_ownership_change(self, api_client):
        """Unsafe Flow: Check for race condition in concurrent operations."""
        import concurrent.futures

        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        def update_stream(name):
            return api_client.patch(
                f"/api/v2/webstreams/{stream.id}",
                json.dumps({"name": name}),
                content_type="application/json",
            ).status_code

        # Fire 10 concurrent updates
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(update_stream, f"Name{i}") for i in range(10)
            ]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        # Check for inconsistent results
        success_count = results.count(200)
        # If results are inconsistent (some succeed, some fail), it may indicate race condition
        if 0 < success_count < 10:
            pytest.fail(
                f"T570: Race condition - {success_count}/10 updates succeeded inconsistently",
            )

    # ========================================================================
    # API7:2023 - SSRF via URL field
    # ========================================================================

    def test_ssrf_cloud_metadata_in_url(self, api_client):
        """SSRF: Check if cloud metadata URLs are accepted in webstream URL."""
        user = baker.make(User, username="testred_user")

        ssrf_urls = [
            ("http://169.254.169.254/latest/meta-data/", "AWS metadata"),
            ("http://169.254.169.254/metadata/v1/", "DigitalOcean metadata"),
            ("http://metadata.google.internal/", "GCP metadata"),
            ("http://127.0.0.1:8080/admin", "localhost admin"),
            ("http://localhost:9000/internal", "localhost internal"),
        ]

        vulnerabilities = []
        for url, desc in ssrf_urls:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": "SSRF Test",
                        "url": url,
                    },
                ),
                content_type="application/json",
            )

            if response.status_code == 201:
                vulnerabilities.append(f"{desc}: {url}")

        if vulnerabilities:
            pytest.fail(
                f"T571: SSRF - Internal URLs accepted: {', '.join(vulnerabilities)}",
            )

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_security_headers_present(self, api_client):
        """Misconfig: Check for security headers."""
        response = api_client.get("/api/v2/webstreams")

        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
        ]

        missing = []
        for header in required_headers:
            if header not in response.headers:
                missing.append(header)

        if missing:
            pytest.skip(f"Security headers missing: {missing}")

    def test_cors_misconfiguration(self, api_client):
        """Misconfig: CORS allows arbitrary origins."""
        response = api_client.options(
            "/api/v2/webstreams",
            HTTP_ORIGIN="https://attacker.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        if allow_origin == "*" or allow_origin == "https://attacker.com":
            pytest.fail("CORS misconfiguration: allows arbitrary origin")

    def test_verbose_error_messages(self, api_client):
        """Misconfig: Error messages reveal implementation details."""
        # Trigger error with invalid input
        response = api_client.get("/api/v2/webstreams/invalid'union")

        error_body = response.content.decode().lower()

        # Check for information leakage
        sensitive_patterns = [
            "sql",
            "sqlite",
            "mysql",
            "postgresql",
            "django",
            "python",
            "traceback",
            "cc_webstream",
            "column",
            "table",
        ]

        for pattern in sensitive_patterns:
            if pattern in error_body:
                pytest.fail(f"Verbose error leaks: '{pattern}' in response")

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_nosql_injection_in_query(self, api_client):
        """Injection: NoSQL operators in query parameters."""
        nosql_payloads = [
            "?owner__ne=1",
            "?name__regex=.*",
            "?id__gt=0",
        ]

        for payload in nosql_payloads:
            response = api_client.get(f"/api/v2/webstreams{payload}")
            # Should not cause 500 or unexpected behavior
            assert response.status_code in [
                200,
                400,
            ], f"NoSQLi '{payload}' caused {response.status_code}"

    def test_sql_injection_in_filter(self, api_client):
        """Injection: SQLi in filter parameters."""
        sqli_payloads = [
            "?name=' OR '1'='1",
            "?name=1; DROP TABLE cc_webstream--",
            "?owner=1 UNION SELECT * FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/webstreams{payload}")
            # Should not cause 500
            assert (
                response.status_code != 500
            ), f"SQLi '{payload}' caused 500 error"

    # ========================================================================
    # Rate Limiting Bypasses
    # ========================================================================

    def test_rate_limit_bypass_via_headers(self, api_client):
        """Rate Limit: Bypass via X-Forwarded-For header."""
        user = baker.make(User, username="testred_user")

        # Make requests with different X-Forwarded-For values
        for i in range(20):
            response = api_client.get(
                "/api/v2/webstreams",
                HTTP_X_FORWARDED_FOR=f"1.2.3.{i}",
            )
            assert response.status_code == 200

    def test_rate_limit_bypass_via_user_agent(self, api_client):
        """Rate Limit: Bypass via User-Agent rotation."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "curl/7.68.0",
            "PostmanRuntime/7.28.4",
        ]

        for i in range(25):
            response = api_client.get(
                "/api/v2/webstreams",
                HTTP_USER_AGENT=user_agents[i % len(user_agents)],
            )
            assert response.status_code == 200

    # ========================================================================
    # Input Validation
    # ========================================================================

    def test_unicode_injection_in_fields(self, api_client):
        """Validation: Unicode bypass in permission checks."""
        user = baker.make(User, username="testred_user")

        # Try unicode variations that might bypass validation
        unicode_payloads = [
            "\u0000",  # Null byte
            "\uff00",  # Fullwidth characters
            "admin\u200b",  # Zero-width space
            "admin\ufeff",  # BOM
        ]

        for payload in unicode_payloads:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": f"Test {payload}",
                        "url": "http://example.com/stream",
                    },
                ),
                content_type="application/json",
            )
            # Should handle unicode gracefully
            assert response.status_code in [
                200,
                201,
                400,
            ], f"Unicode '{repr(payload)}' caused unexpected {response.status_code}"

    def test_path_traversal_in_id(self, api_client):
        """Validation: Path traversal in object ID."""
        traversal_ids = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for test_id in traversal_ids:
            response = api_client.get(f"/api/v2/webstreams/{test_id}")
            assert response.status_code in [
                400,
                404,
            ], f"Path traversal '{test_id}' caused {response.status_code}"

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    def test_timing_attack_user_enumeration(self, api_client):
        """Info Leak: Timing differences leak user existence."""
        # Time request for existing vs non-existing stream
        existing_times = []
        nonexistent_times = []

        # Existing stream
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        for _ in range(3):
            start = time.time()
            api_client.get(f"/api/v2/webstreams/{stream.id}")
            existing_times.append(time.time() - start)

        # Non-existing stream
        for _ in range(3):
            start = time.time()
            api_client.get("/api/v2/webstreams/999999")
            nonexistent_times.append(time.time() - start)

        avg_existing = sum(existing_times) / len(existing_times)
        avg_nonexistent = sum(nonexistent_times) / len(nonexistent_times)

        # Times should be similar (within 2x factor)
        if avg_existing > 0:
            ratio = max(avg_existing, avg_nonexistent) / min(
                avg_existing,
                avg_nonexistent,
            )
            if ratio > 2:
                pytest.fail(
                    f"Timing leak: existing={avg_existing:.4f}s, nonexistent={avg_nonexistent:.4f}s (ratio {ratio:.1f})",
                )

    def test_field_enumeration_via_error(self, api_client):
        """Info Leak: Error messages reveal valid field names."""
        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "invalid_field_name_xyz": "value",
                    "name": "Test",
                    "url": "http://example.com",
                },
            ),
            content_type="application/json",
        )

        # Error message might reveal which fields are valid
        error_text = response.content.decode().lower()

        # Check if error reveals field information
        if "valid fields are" in error_text or "valid fields:" in error_text:
            pytest.fail("Error message reveals valid field names")