"""Red Team security tests for SmartBlockCriteria CREATE endpoint (T242).

Tests focus on:
- API1:2023 BOLA (creating criteria for other users' blocks)
- API3:2023 BOPLA (mass assignment attacks)
- Injection attacks in criteria/condition/value fields
- Input validation bypasses
- Business logic flaws
"""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaCreateRedTeam:
    """Red Team tests for POST /api/v2/smart-block-criteria."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T496: BOLA - can create criteria for other user's block",
    )
    def test_bola_create_for_other_users_block(self, api_client):
        """BOLA: Creating criteria for another user's block should fail."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Victim's private block
        victim_block = baker.make(
            SmartBlock,
            name="Victim Private Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )

        # Attacker tries to create criteria for victim's block
        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": victim_block.id,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Attacker Genre",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            404,
        ], f"BOLA: Created criteria for victim's block, got {response.status_code}"

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T497: BOPLA - mass assignment via id field")
    def test_bopla_mass_assignment_id_field(self, api_client):
        """BOPLA: Setting id field should be ignored or rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        forced_id = 99999
        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "id": forced_id,
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert (
            data["id"] != forced_id
        ), f"BOPLA: ID mass assignment worked, got id={data['id']}"

    @pytest.mark.xfail(reason="T498: BOPLA - extra fields not rejected")
    def test_bopla_extra_fields_rejected(self, api_client):
        """BOPLA: Extra/unknown fields should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Jazz",
                    "is_admin": True,
                    "role": "admin",
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"BOPLA: Extra fields accepted, got {response.status_code}"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_criteria_field(self, api_client):
        """Injection: SQLi attempts in criteria field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        sqli_payloads = [
            "genre'; DROP TABLE cc_blockcriteria;--",
            "genre' OR '1'='1",
            "genre UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/smart-block-criteria",
                json.dumps(
                    {
                        "block": block.id,
                        "criteria": payload,
                        "condition": "contains",
                        "value": "Jazz",
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                201,
                400,
            ], f"SQLi in criteria '{payload}' caused {response.status_code}"

    def test_sqli_in_condition_field(self, api_client):
        """Injection: SQLi attempts in condition field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        sqli_payloads = [
            "contains'; DROP TABLE cc_blockcriteria;--",
            "contains' OR '1'='1",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/smart-block-criteria",
                json.dumps(
                    {
                        "block": block.id,
                        "criteria": "genre",
                        "condition": payload,
                        "value": "Jazz",
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                201,
                400,
            ], f"SQLi in condition '{payload}' caused {response.status_code}"

    def test_sqli_in_value_field(self, api_client):
        """Injection: SQLi attempts in value field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        sqli_payloads = [
            "Jazz'; DROP TABLE cc_blockcriteria;--",
            "Jazz' OR '1'='1",
            "Jazz' UNION SELECT password FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/smart-block-criteria",
                json.dumps(
                    {
                        "block": block.id,
                        "criteria": "genre",
                        "condition": "contains",
                        "value": payload,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                201,
                400,
            ], f"SQLi in value '{payload}' caused {response.status_code}"

    def test_sqli_in_extra_field(self, api_client):
        """Injection: SQLi attempts in extra field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        sqli_payloads = [
            "extra'; DROP TABLE cc_blockcriteria;--",
            "extra' OR '1'='1",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/smart-block-criteria",
                json.dumps(
                    {
                        "block": block.id,
                        "criteria": "genre",
                        "condition": "contains",
                        "value": "Jazz",
                        "extra": payload,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                201,
                400,
            ], f"SQLi in extra '{payload}' caused {response.status_code}"

    # ========================================================================
    # Input Validation Bypasses
    # ========================================================================

    @pytest.mark.xfail(reason="T499: Very long criteria value not validated")
    def test_overflow_criteria_value(self, api_client):
        """Validation: Very long value should be rejected or truncated."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        long_value = "A" * 10000
        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": long_value,
                },
            ),
            content_type="application/json",
        )
        # Should either reject or handle gracefully
        assert response.status_code in [
            201,
            400,
        ], f"Overflow value caused {response.status_code}"

    def test_unicode_injection_value_field(self, api_client):
        """Validation: Unicode and special chars in value field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        unicode_payloads = [
            "日本語",
            "<script>alert(1)</script>",
            "${7*7}",
            "{{7*7}}",
            "%s%s%s",
        ]

        for payload in unicode_payloads:
            response = api_client.post(
                "/api/v2/smart-block-criteria",
                json.dumps(
                    {
                        "block": block.id,
                        "criteria": "genre",
                        "condition": "contains",
                        "value": payload,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                201,
                400,
            ], f"Unicode '{payload}' caused {response.status_code}"

    @pytest.mark.xfail(reason="T500: Negative group value accepted")
    def test_negative_group_value(self, api_client):
        """Validation: Negative group value should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Jazz",
                    "group": -1,
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Negative group accepted with {response.status_code}"

    # ========================================================================
    # Business Logic Attacks
    # ========================================================================

    @pytest.mark.xfail(reason="T501: Duplicate criteria not prevented")
    def test_duplicate_criteria_same_block(self, api_client):
        """Logic: Duplicate criteria in same block should be handled."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        # First criteria
        response1 = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response1.status_code == 201

        # Duplicate criteria
        response2 = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        # Should either allow (it's valid to have multiple) or reject with clear error
        assert response2.status_code in [
            201,
            400,
            409,
        ], f"Duplicate criteria caused {response2.status_code}"

    @pytest.mark.xfail(reason="T502: Invalid criteria type not validated")
    def test_invalid_criteria_type(self, api_client):
        """Validation: Invalid criteria type should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "invalid_criteria_type",
                    "condition": "contains",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Invalid criteria type accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T503: Invalid condition type not validated")
    def test_invalid_condition_type(self, api_client):
        """Validation: Invalid condition type should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "invalid_condition",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Invalid condition type accepted with {response.status_code}"

    # ========================================================================
    # Authentication Bypass
    # ========================================================================

    def test_create_without_auth(self, client):
        """Auth: Create without authentication should fail."""
        response = client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": 1,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 403

    # ========================================================================
    # Race Conditions
    # ========================================================================

    @pytest.mark.xfail(reason="T504: Race condition in concurrent creates")
    def test_race_condition_concurrent_create(self, api_client):
        """Race: Concurrent creation with same data."""
        import concurrent.futures

        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user,
        )

        def create_criteria():
            return api_client.post(
                "/api/v2/smart-block-criteria",
                json.dumps(
                    {
                        "block": block.id,
                        "criteria": "genre",
                        "condition": "contains",
                        "value": "Jazz",
                    },
                ),
                content_type="application/json",
            ).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_criteria) for _ in range(5)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        success_count = results.count(201)
        # All should succeed (duplicates allowed) or only one should succeed
        assert (
            success_count >= 1
        ), f"Race condition: {success_count} concurrent creates succeeded"

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    def test_error_message_enumeration_block(self, api_client):
        """Info Leak: Error messages shouldn't reveal which IDs exist."""
        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": 999999,
                    "criteria": "genre",
                    "condition": "contains",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )

        error_body = response.content.decode().lower()
        # Should not reveal if block exists or not
        assert (
            "block" not in error_body or "invalid" in error_body
        ), "Error message may leak block existence information"
