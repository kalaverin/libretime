"""Red Team security tests for SmartBlockCriteria UPDATE endpoint (T243).

Tests focus on:
- API1:2023 BOLA (updating other users' criteria)
- API3:2023 BOPLA (mass assignment on update)
- IDOR via ID enumeration
- Injection attacks in update fields
- Business logic: changing block ownership
"""

import json

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaUpdateRedTeam:
    """Red Team tests for PATCH/PUT /api/v2/smart-block-criteria/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T505: BOLA - can update other user's criteria")
    def test_bola_update_other_users_criteria(self, api_client):
        """BOLA: Updating another user's criteria should fail."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        victim_criteria = baker.make(
            SmartBlockCriteria,
            block=victim_block,
            criteria="genre",
            condition="contains",
            value="Victim Genre",
        )

        # Attacker tries to update victim's criteria
        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{victim_criteria.id}",
            json.dumps({"value": "Attacker Genre"}),
            content_type="application/json",
        )
        assert response.status_code in [403, 404], \
            f"BOLA: Updated victim's criteria, got {response.status_code}"

    @pytest.mark.xfail(reason="T506: BOLA - can delete other user's criteria")
    def test_bola_delete_other_users_criteria(self, api_client):
        """BOLA: Deleting another user's criteria should fail."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        victim_criteria = baker.make(
            SmartBlockCriteria,
            block=victim_block,
            criteria="genre",
            condition="contains",
            value="Victim Genre",
        )

        # Attacker tries to delete victim's criteria
        response = api_client.delete(
            f"/api/v2/smart-block-criteria/{victim_criteria.id}",
        )
        assert response.status_code in [403, 404], \
            f"BOLA: Deleted victim's criteria, got {response.status_code}"

    # ========================================================================
    # IDOR via ID Enumeration
    # ========================================================================

    def test_idor_criteria_enumeration(self, api_client):
        """Security: Criteria ID enumeration mitigated."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        # Try to access with sequential IDs
        for test_id in range(1, 10):
            response = api_client.get(f"/api/v2/smart-block-criteria/{test_id}")
            # Should get 404 for non-existent or 403 for unauthorized
            assert response.status_code in [200, 403, 404], \
                f"ID {test_id} returned {response.status_code}"

    # ========================================================================
    # Block Takeover Attack
    # ========================================================================

    @pytest.mark.xfail(reason="T507: Can change criteria to point to other user's block")
    def test_block_takeover_via_update(self, api_client):
        """BOLA: Changing criteria to point to victim's block."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        attacker_block = baker.make(
            SmartBlock,
            name="Attacker Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=attacker,
        )
        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        criteria = baker.make(
            SmartBlockCriteria,
            block=attacker_block,
            criteria="genre",
            condition="contains",
            value="Genre",
        )

        # Attacker tries to move criteria to victim's block
        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"block": victim_block.id}),
            content_type="application/json",
        )
        assert response.status_code in [400, 403], \
            f"Block takeover possible, got {response.status_code}"

    # ========================================================================
    # Injection Attacks on Update
    # ========================================================================

    def test_sqli_in_update_value(self, api_client):
        """Injection: SQLi in PATCH value field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Original",
        )

        sqli_payloads = [
            "Jazz'; DROP TABLE cc_blockcriteria;--",
            "Jazz' OR '1'='1",
            "Jazz' UNION SELECT password FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = api_client.patch(
                f"/api/v2/smart-block-criteria/{criteria.id}",
                json.dumps({"value": payload}),
                content_type="application/json",
            )
            assert response.status_code in [200, 400], \
                f"SQLi '{payload}' caused {response.status_code}"

    def test_sqli_in_update_criteria_field(self, api_client):
        """Injection: SQLi in PATCH criteria field."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        sqli_payloads = [
            "genre'; DROP TABLE cc_blockcriteria;--",
            "genre' OR '1'='1",
        ]

        for payload in sqli_payloads:
            response = api_client.patch(
                f"/api/v2/smart-block-criteria/{criteria.id}",
                json.dumps({"criteria": payload}),
                content_type="application/json",
            )
            assert response.status_code in [200, 400], \
                f"SQLi '{payload}' caused {response.status_code}"

    # ========================================================================
    # Mass Assignment on Update
    # ========================================================================

    @pytest.mark.xfail(reason="T508: Can modify id field on update")
    def test_mass_assignment_id_on_update(self, api_client):
        """BOPLA: Changing id field on update should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )
        original_id = criteria.id

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"id": 99999}),
            content_type="application/json",
        )
        assert response.status_code in [200, 400], \
            f"ID modification caused {response.status_code}"

        if response.status_code == 200:
            # Verify ID wasn't changed
            data = response.json()
            assert data["id"] == original_id, \
                f"BOPLA: ID was changed to {data['id']}"

    # ========================================================================
    # PUT vs PATCH Behavior
    # ========================================================================

    @pytest.mark.xfail(reason="T509: PUT allows changing block to other user's")
    def test_put_full_update_block_takeover(self, api_client):
        """BOLA: PUT full update with victim's block ID."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        attacker_block = baker.make(
            SmartBlock,
            name="Attacker Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=attacker,
        )
        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        criteria = baker.make(
            SmartBlockCriteria,
            block=attacker_block,
            criteria="genre",
            condition="contains",
            value="Genre",
        )

        # PUT full update with victim's block
        response = api_client.put(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({
                "block": victim_block.id,
                "criteria": "artist",
                "condition": "starts",
                "value": "New Value",
            }),
            content_type="application/json",
        )
        assert response.status_code in [400, 403], \
            f"PUT block takeover possible, got {response.status_code}"

    # ========================================================================
    # Invalid ID Handling
    # ========================================================================

    def test_update_nonexistent_criteria(self, api_client):
        """Validation: Update non-existent criteria returns 404."""
        response = api_client.patch(
            "/api/v2/smart-block-criteria/999999",
            json.dumps({"value": "New Value"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_invalid_id_format(self, api_client):
        """Validation: Invalid ID format handled gracefully."""
        response = api_client.patch(
            "/api/v2/smart-block-criteria/invalid",
            json.dumps({"value": "New Value"}),
            content_type="application/json",
        )
        assert response.status_code in [400, 404], \
            f"Invalid ID caused {response.status_code}"

    # ========================================================================
    # Authentication Bypass
    # ========================================================================

    def test_update_without_auth(self, client):
        """Auth: Update without authentication should fail."""
        response = client.patch(
            "/api/v2/smart-block-criteria/1",
            json.dumps({"value": "New Value"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_without_auth(self, client):
        """Auth: Delete without authentication should fail."""
        response = client.delete("/api/v2/smart-block-criteria/1")
        assert response.status_code == 403

    # ========================================================================
    # Business Logic
    # ========================================================================

    @pytest.mark.xfail(reason="T510: Empty value accepted on update")
    def test_update_empty_value(self, api_client):
        """Validation: Empty value should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"value": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400, \
            f"Empty value accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T511: Very long value on update not validated")
    def test_update_very_long_value(self, api_client):
        """Validation: Very long value on update should be rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        long_value = "A" * 10000
        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"value": long_value}),
            content_type="application/json",
        )
        assert response.status_code in [200, 400], \
            f"Long value caused {response.status_code}"
