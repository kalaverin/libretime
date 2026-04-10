"""Red Team security tests for SmartBlockContents CREATE endpoint (T240).

Tests focus on:
- API1:2023 BOLA (creating content in other users' blocks)
- API3:2023 BOPLA (mass assignment attacks)
- Injection attacks in all fields
- Input validation bypasses
- Business logic flaws
- Race conditions
"""

import json

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockContentCreateRedTeam:
    """Red Team tests for POST /api/v2/smart-block-contents."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockContent.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T475: BOLA - can create content in other user's block (API1:2023)")
    def test_bola_create_in_other_users_block(self, api_client):
        """BOLA: Creating content in another user's block should fail."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Victim's private block
        victim_block = baker.make(
            SmartBlock,
            name="Victim Private Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )
        attacker_file = baker.make(File, name="attacker.mp3", mime="audio/mp3", owner=attacker)

        # Attacker tries to create content in victim's block
        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": victim_block.id,
                "file": attacker_file.id,
                "position": 1,
            }),
            content_type="application/json",
        )
        # Should fail with 403 or 404
        assert response.status_code in [403, 404], \
            f"BOLA: Created content in victim's block, got {response.status_code}"

    @pytest.mark.xfail(reason="T476: BOLA - can use other user's private file (API1:2023)")
    def test_bola_create_with_other_users_file(self, api_client):
        """BOLA: Using other user's file should fail without revealing existence."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        attacker_block = baker.make(
            SmartBlock,
            name="Attacker Block",
            kind=SmartBlock.Kind.STATIC,
            owner=attacker,
        )
        victim_file = baker.make(File, name="victim_secret.mp3", mime="audio/mp3", owner=victim)

        # Attacker tries to use victim's file
        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": attacker_block.id,
                "file": victim_file.id,
                "position": 1,
            }),
            content_type="application/json",
        )
        # Should fail - either file not found (404) or forbidden (403)
        # But should NOT succeed
        assert response.status_code != 201, \
            "BOLA: Attacker can use victim's private file"

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T477: BOPLA - mass assignment via id field (API3:2023)")
    def test_bopla_mass_assignment_id_field(self, api_client):
        """BOPLA: Setting id field should be ignored or rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        # Try to set own ID (could overwrite existing record)
        forced_id = 99999
        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "id": forced_id,
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        # ID should be auto-generated, not our forced value
        assert data["id"] != forced_id, \
            f"BOPLA: ID mass assignment worked, got id={data['id']}"

    @pytest.mark.xfail(reason="T478: BOPLA - extra fields silently ignored (API3:2023)")
    def test_bopla_extra_fields_rejected(self, api_client):
        """BOPLA: Extra/unknown fields should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "is_admin": True,
                "password": "hacked",
                "role": "admin",
            }),
            content_type="application/json",
        )
        # Should reject unknown fields
        assert response.status_code == 400, \
            f"BOPLA: Extra fields accepted, got {response.status_code}"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_position_field(self, api_client):
        """Injection: SQLi attempts in position field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        sqli_payloads = [
            "1; DROP TABLE cc_blockcontents;--",
            "1' OR '1'='1",
            "1 UNION SELECT * FROM cc_user",
            "1) OR (1=1",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": payload,
                }),
                content_type="application/json",
            )
            # Should not crash with 500
            assert response.status_code in [201, 400], \
                f"SQLi in position '{payload}' caused {response.status_code}"

    def test_sqli_in_cue_fields(self, api_client):
        """Injection: SQLi in cue_in/cue_out fields."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        sqli_payloads = [
            "00:00:00'; DROP TABLE cc_blockcontents;--",
            "00:00:00' OR '1'='1",
            "1 UNION SELECT password FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                    "cue_in": payload,
                    "cue_out": payload,
                }),
                content_type="application/json",
            )
            # Should handle gracefully
            assert response.status_code in [201, 400], \
                f"SQLi in cue field caused {response.status_code}"

    def test_nosql_injection_block_field(self, api_client):
        """Injection: NoSQL operators in block field."""
        user = baker.make(User, username="testred_user")
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        # Try MongoDB-style operators
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
        ]

        for payload in nosql_payloads:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": payload,
                    "file": file_obj.id,
                    "position": 1,
                }),
                content_type="application/json",
            )
            # Should reject non-numeric values
            assert response.status_code in [400], \
                f"NoSQL payload {payload} caused {response.status_code}"

    # ========================================================================
    # Input Validation Bypasses
    # ========================================================================

    @pytest.mark.xfail(reason="T479: Path traversal in cue fields not validated")
    def test_path_traversal_in_cue_fields(self, api_client):
        """Validation: Path traversal in cue fields should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "file:///etc/passwd",
        ]

        for payload in path_traversal_payloads:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                    "cue_in": payload,
                }),
                content_type="application/json",
            )
            # Should reject path traversal
            assert response.status_code == 400, \
                f"Path traversal '{payload}' accepted with {response.status_code}"

    def test_overflow_position_value(self, api_client):
        """Validation: Very large position values."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        overflow_values = [
            999999999999999999999999999999,
            float("inf"),
            -999999999999999999999999999999,
        ]

        for value in overflow_values:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": value,
                }),
                content_type="application/json",
            )
            # Should handle gracefully
            assert response.status_code in [201, 400], \
                f"Overflow value {value} caused {response.status_code}"

    def test_fuzzing_naughty_strings_position(self, api_client):
        """Fuzzing: Naughty strings in position field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        naughty_strings = [
            "undefined",
            "null",
            "None",
            "true",
            "false",
            "NaN",
            "Infinity",
            "-Infinity",
            "1/0",
            "0/0",
            "0x0",
            "0xffffffff",
        ]

        for string in naughty_strings:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": string,
                }),
                content_type="application/json",
            )
            # Should not crash
            assert response.status_code in [201, 400], \
                f"Naughty string '{string}' caused {response.status_code}"

    def test_unicode_injection_cue_fields(self, api_client):
        """Validation: Unicode and special chars in cue fields."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        unicode_payloads = [
            "日本語",
            "<script>alert(1)</script>",
            "${7*7}",
            "{{7*7}}",
            "`id`",
            "$(whoami)",
            "%s%s%s%s%s",
            "%x%x%x%x",
        ]

        for payload in unicode_payloads:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                    "cue_in": payload,
                }),
                content_type="application/json",
            )
            # Should handle gracefully
            assert response.status_code in [201, 400], \
                f"Unicode '{payload}' caused {response.status_code}"

    # ========================================================================
    # Business Logic Attacks
    # ========================================================================

    @pytest.mark.xfail(reason="T480: Duplicate position values allowed in same block")
    def test_duplicate_position_same_block(self, api_client):
        """Logic: Duplicate positions in same block should be handled."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file1 = baker.make(File, name="song1.mp3", mime="audio/mp3", owner=user)
        file2 = baker.make(File, name="song2.mp3", mime="audio/mp3", owner=user)

        # First content at position 1
        response1 = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file1.id,
                "position": 1,
            }),
            content_type="application/json",
        )
        assert response1.status_code == 201

        # Second content at same position
        response2 = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file2.id,
                "position": 1,
            }),
            content_type="application/json",
        )
        # Should either reject or handle gracefully (reassign position)
        assert response2.status_code in [201, 400, 409], \
            f"Duplicate position caused {response2.status_code}"

    @pytest.mark.xfail(reason="T481: Negative offset value not validated")
    def test_negative_offset_validation(self, api_client):
        """Logic: Negative offset should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "offset": -100,
            }),
            content_type="application/json",
        )
        # Negative offset doesn't make sense
        assert response.status_code == 400, \
            f"Negative offset accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T482: cue_out before cue_in not validated")
    def test_cue_out_before_cue_in(self, api_client):
        """Logic: cue_out before cue_in should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "cue_in": "00:03:00",
                "cue_out": "00:01:00",  # Before cue_in
            }),
            content_type="application/json",
        )
        # cue_out before cue_in is invalid
        assert response.status_code == 400, \
            f"Invalid cue times accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T483: Invalid cue time format accepted")
    def test_invalid_cue_format(self, api_client):
        """Validation: Invalid cue time format should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        invalid_formats = [
            "not-a-time",
            "99:99:99",
            "25:00:00",
            "-00:01:00",
            "1:2:3",
            "12:34",
            "12",
        ]

        for fmt in invalid_formats:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                    "cue_in": fmt,
                }),
                content_type="application/json",
            )
            # Should reject invalid format
            assert response.status_code == 400, \
                f"Invalid cue format '{fmt}' accepted with {response.status_code}"

    # ========================================================================
    # Authentication Bypass
    # ========================================================================

    def test_create_without_auth(self, client):
        """Auth: Create without authentication should fail."""
        response = client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": 1,
                "file": 1,
                "position": 1,
            }),
            content_type="application/json",
        )
        assert response.status_code == 403

    @pytest.mark.xfail(reason="T484: Invalid auth tokens may be partially accepted")
    def test_create_with_invalid_token(self, api_client):
        """Auth: Invalid token format should fail."""
        # Temporarily modify client to use invalid token
        original_headers = api_client.defaults.get("HTTP_AUTHORIZATION", "")
        api_client.defaults["HTTP_AUTHORIZATION"] = "Bearer invalid_token_here"

        try:
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": 1,
                    "file": 1,
                    "position": 1,
                }),
                content_type="application/json",
            )
            assert response.status_code == 403, \
                f"Invalid token caused {response.status_code}"
        finally:
            api_client.defaults["HTTP_AUTHORIZATION"] = original_headers

    # ========================================================================
    # Content-Type Attacks
    # ========================================================================

    @pytest.mark.xfail(reason="T485: Wrong Content-Type not rejected with 415")
    def test_create_wrong_content_type(self, api_client):
        """Validation: Wrong Content-Type should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        response = api_client.post(
            "/api/v2/smart-block-contents",
            f"block={block.id}&file={file_obj.id}&position=1",  # Form data
            content_type="application/x-www-form-urlencoded",
        )
        # Should reject or handle gracefully
        assert response.status_code in [400, 415], \
            f"Wrong content-type caused {response.status_code}"

    # ========================================================================
    # Race Conditions
    # ========================================================================

    @pytest.mark.xfail(reason="T486: Race condition in concurrent CREATE requests")
    def test_race_condition_concurrent_create(self, api_client):
        """Race: Concurrent creation with same data."""
        import threading
        import concurrent.futures

        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        results = []

        def create_content():
            response = api_client.post(
                "/api/v2/smart-block-contents",
                json.dumps({
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                }),
                content_type="application/json",
            )
            return response.status_code

        # Fire 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_content) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = results.count(201)
        # Should only create one, others should fail or be duplicates
        assert success_count <= 1, \
            f"Race condition: {success_count} concurrent creates succeeded"

    # ========================================================================
    # ID Enumeration / Information Disclosure
    # ========================================================================

    def test_error_message_enumeration_block(self, api_client):
        """Info Leak: Error messages shouldn't reveal which IDs exist."""
        user = baker.make(User, username="testred_user")
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        # Try with non-existent block
        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": 999999,
                "file": file_obj.id,
                "position": 1,
            }),
            content_type="application/json",
        )

        error_body = response.content.decode().lower()
        # Should not reveal if block exists or not
        assert "block" not in error_body or "invalid" in error_body, \
            "Error message may leak block existence information"

    def test_error_message_enumeration_file(self, api_client):
        """Info Leak: Error messages shouldn't reveal which file IDs exist."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)

        # Try with non-existent file
        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": 999999,
                "position": 1,
            }),
            content_type="application/json",
        )

        error_body = response.content.decode().lower()
        # Should not reveal if file exists or not
        assert "file" not in error_body or "invalid" in error_body, \
            "Error message may leak file existence information"

    # ========================================================================
    # Mass Assignment via JSON Merge Patch
    # ========================================================================

    @pytest.mark.xfail(reason="T487: JSON Merge Patch accepted without validation")
    def test_json_merge_patch_mass_assignment(self, api_client):
        """BOPLA: JSON Merge Patch for partial update on create."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "role": "admin",
                "is_staff": True,
            }),
            content_type="application/merge-patch+json",
        )
        # Should reject unknown content type or validate strictly
        if response.status_code == 201:
            data = response.json()
            assert "role" not in data and "is_staff" not in data, \
                "BOPLA: Mass assignment via JSON Merge Patch worked"
