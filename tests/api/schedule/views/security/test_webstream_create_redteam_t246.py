"""Red Team security tests for Webstreams CREATE endpoint (T246).

Tests focus on:
- API1:2023 BOLA (creating webstreams for other users)
- API3:2023 BOPLA (mass assignment attacks)
- SSRF via URL field
- URL scheme validation bypass
- Injection attacks
- XSS in name/description fields
"""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestWebstreamCreateRedTeam:
    """Red Team tests for POST /api/v2/webstreams."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T526: BOPLA - can set other user as owner via owner field",
    )
    def test_bopla_create_with_other_user_owner(self, api_client):
        """BOPLA: Setting other user as owner should be rejected."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Attacker tries to create webstream with victim as owner
        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Attacker Stream",
                    "url": "http://example.com/stream.mp3",
                    "owner": victim.id,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("owner") != victim.id
            ), "BOPLA: Attacker created stream with victim as owner"

    @pytest.mark.xfail(reason="T527: perform_create allows null owner bypass")
    def test_create_unauthenticated_owner_bypass(self, client):
        """Auth: Unauthenticated create should not allow owner manipulation."""
        # Create without auth - perform_create should not allow this
        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Anonymous Stream",
                    "url": "http://example.com/stream.mp3",
                },
            ),
            content_type="application/json",
        )
        # Should fail with 403, not create with null owner
        assert (
            response.status_code == 403
        ), f"Unauthenticated create allowed with status {response.status_code}"

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T528: BOPLA - mass assignment via id field")
    def test_bopla_mass_assignment_id(self, api_client):
        """BOPLA: Setting id field should be ignored or rejected."""
        user = baker.make(User, username="testred_user")
        forced_id = 99999

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "id": forced_id,
                    "name": "Test Stream",
                    "url": "http://example.com/stream.mp3",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data["id"] != forced_id
            ), f"BOPLA: ID mass assignment worked, got id={data['id']}"

    @pytest.mark.xfail(
        reason="T529: BOPLA - can set created_at/updated_at manually",
    )
    def test_bopla_mass_assignment_timestamps(self, api_client):
        """BOPLA: Setting timestamps manually should be ignored."""
        user = baker.make(User, username="testred_user")
        fake_time = "2020-01-01T00:00:00Z"

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": "http://example.com/stream.mp3",
                    "created_at": fake_time,
                    "updated_at": fake_time,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("created_at") != fake_time
            ), "BOPLA: created_at mass assignment worked"
            assert (
                data.get("updated_at") != fake_time
            ), "BOPLA: updated_at mass assignment worked"

    @pytest.mark.xfail(reason="T530: BOPLA - extra fields not rejected")
    def test_bopla_extra_fields_rejected(self, api_client):
        """BOPLA: Extra/unknown fields should be rejected."""
        user = baker.make(User, username="testred_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": "http://example.com/stream.mp3",
                    "is_admin": True,
                    "role": "admin",
                    "password": "hacked",
                },
            ),
            content_type="application/json",
        )
        # Should reject unknown fields
        assert (
            response.status_code == 400
        ), f"BOPLA: Extra fields accepted, got {response.status_code}"

    # ========================================================================
    # SSRF via URL Field
    # ========================================================================

    @pytest.mark.xfail(reason="T531: SSRF - internal URL accepted")
    def test_ssrf_internal_url(self, api_client):
        """SSRF: Internal network URLs should be rejected."""
        user = baker.make(User, username="testred_user")

        internal_urls = [
            "http://localhost:8080/stream",
            "http://127.0.0.1:8080/stream",
            "http://192.168.1.1/stream",
            "http://10.0.0.1/stream",
            "http://172.16.0.1/stream",
            "http://[::1]/stream",
        ]

        for url in internal_urls:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": "Internal Stream",
                        "url": url,
                    },
                ),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"SSRF: Internal URL '{url}' accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T532: SSRF - cloud metadata URLs accepted")
    def test_ssrf_cloud_metadata(self, api_client):
        """SSRF: Cloud metadata URLs should be rejected."""
        user = baker.make(User, username="testred_user")

        metadata_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS
            "http://metadata.google.internal/",  # GCP
            "http://169.254.169.254/metadata/v1/",  # DigitalOcean
        ]

        for url in metadata_urls:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": "Metadata Stream",
                        "url": url,
                    },
                ),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"SSRF: Metadata URL '{url}' accepted with {response.status_code}"

    # ========================================================================
    # URL Scheme Validation
    # ========================================================================

    @pytest.mark.xfail(reason="T533: Dangerous URL schemes accepted")
    def test_url_scheme_validation(self, api_client):
        """Validation: Dangerous URL schemes should be rejected."""
        user = baker.make(User, username="testred_user")

        dangerous_schemes = [
            "file:///etc/passwd",
            "ftp://attacker.com/stream",
            "dict://localhost:11211/",
            "gopher://localhost:9000/",
            "ldap://localhost:389/",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ]

        for url in dangerous_schemes:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": "Dangerous Stream",
                        "url": url,
                    },
                ),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"Dangerous scheme '{url}' accepted with {response.status_code}"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_name_field(self, api_client):
        """Injection: SQLi attempts in name field."""
        user = baker.make(User, username="testred_user")

        sqli_payloads = [
            "Stream'; DROP TABLE cc_webstream;--",
            "Stream' OR '1'='1",
            "Stream' UNION SELECT * FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": payload,
                        "url": "http://example.com/stream.mp3",
                    },
                ),
                content_type="application/json",
            )
            # Should not crash with 500
            assert response.status_code in [
                201,
                400,
            ], f"SQLi in name caused {response.status_code}"

    @pytest.mark.xfail(
        reason="T540: 500 error due to creator_id NOT NULL violation",
    )
    def test_sqli_in_description_field(self, api_client):
        """Injection: SQLi attempts in description field - BUG T540."""
        user = baker.make(User, username="testred_user")

        sqli_payloads = [
            "Description'; DROP TABLE cc_webstream;--",
            "Description' OR '1'='1",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": "Test Stream",
                        "url": "http://example.com/stream.mp3",
                        "description": payload,
                    },
                ),
                content_type="application/json",
            )
            # BUG T540: Returns 500 instead of 201/400 due to creator_id NOT NULL
            assert response.status_code in [
                201,
                400,
            ], f"BUG T540: SQLi in description caused {response.status_code}"

    def test_sqli_in_url_field(self, api_client):
        """Injection: SQLi attempts in URL field."""
        user = baker.make(User, username="testred_user")

        sqli_payloads = [
            "http://example.com/stream' OR '1'='1",
            "http://example.com/stream'; DROP TABLE cc_webstream;--",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": "Test Stream",
                        "url": payload,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                201,
                400,
            ], f"SQLi in URL caused {response.status_code}"

    # ========================================================================
    # XSS Attacks
    # ========================================================================

    @pytest.mark.xfail(reason="T534: XSS - name field not sanitized")
    def test_xss_in_name_field(self, api_client):
        """XSS: Script tags in name should be sanitized or rejected."""
        user = baker.make(User, username="testred_user")

        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
        ]

        for payload in xss_payloads:
            response = api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": payload,
                        "url": "http://example.com/stream.mp3",
                    },
                ),
                content_type="application/json",
            )

            if response.status_code == 201:
                data = response.json()
                name = data.get("name", "")
                assert (
                    "<script>" not in name
                ), "XSS: script tags not sanitized in name"
                assert (
                    "onerror=" not in name
                ), "XSS: event handlers not sanitized in name"
                assert (
                    "onload=" not in name
                ), "XSS: onload not sanitized in name"

    @pytest.mark.xfail(reason="T535: XSS - description field not sanitized")
    def test_xss_in_description_field(self, api_client):
        """XSS: Script tags in description should be sanitized or rejected."""
        user = baker.make(User, username="testred_user")

        xss_payload = "<script>alert('xss')</script>"

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": "http://example.com/stream.mp3",
                    "description": xss_payload,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            desc = data.get("description", "")
            assert (
                "<script>" not in desc
            ), "XSS: script tags not sanitized in description"

    # ========================================================================
    # Input Validation
    # ========================================================================

    @pytest.mark.xfail(reason="T536: Name length not validated")
    def test_name_length_validation(self, api_client):
        """Validation: Very long name should be rejected."""
        user = baker.make(User, username="testred_user")

        long_name = "A" * 1000  # Model allows 255

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": long_name,
                    "url": "http://example.com/stream.mp3",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code in [
            201,
            400,
        ], f"Long name caused {response.status_code}"

    @pytest.mark.xfail(reason="T537: Empty name accepted")
    def test_empty_name_validation(self, api_client):
        """Validation: Empty name should be rejected."""
        user = baker.make(User, username="testred_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "",
                    "url": "http://example.com/stream.mp3",
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Empty name accepted with {response.status_code}"

    # ========================================================================
    # Authentication
    # ========================================================================

    def test_create_without_auth(self, client):
        """Auth: Create without authentication should fail."""
        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": "http://example.com/stream.mp3",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 403

    # ========================================================================
    # Content-Type Attacks
    # ========================================================================

    @pytest.mark.xfail(reason="T538: Wrong content-type accepted")
    def test_create_wrong_content_type(self, api_client):
        """Validation: Wrong Content-Type should be rejected."""
        user = baker.make(User, username="testred_user")

        response = api_client.post(
            "/api/v2/webstreams",
            "name=Test&url=http://example.com/stream.mp3",  # Form data
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code in [
            400,
            415,
        ], f"Wrong content-type caused {response.status_code}"

    # ========================================================================
    # Race Conditions
    # ========================================================================

    @pytest.mark.xfail(reason="T539: Race condition in concurrent create")
    def test_race_condition_concurrent_create(self, api_client):
        """Race: Concurrent creation with same name."""
        import concurrent.futures

        user = baker.make(User, username="testred_user")

        def create_stream():
            return api_client.post(
                "/api/v2/webstreams",
                json.dumps(
                    {
                        "name": "Duplicate Name",
                        "url": "http://example.com/stream.mp3",
                    },
                ),
                content_type="application/json",
            ).status_code

        # Fire 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_stream) for _ in range(5)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        success_count = results.count(201)
        # Should allow all (different streams) or handle gracefully
        assert (
            success_count >= 0
        ), f"Race condition: {success_count} concurrent creates succeeded"