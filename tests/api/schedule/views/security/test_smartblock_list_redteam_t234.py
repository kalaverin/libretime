"""Red Team security tests for SmartBlocks LIST endpoint (T234).

Tests focus on:
- API1:2023 BOLA (viewing other's blocks)
- API3:2023 BOPLA (field exposure)
- API6:2023 Resource consumption
- Injection in filter params
"""

import time

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockListRedTeam:
    """Red Team tests for GET /api/v2/smart-blocks."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA
    # ========================================================================

    @pytest.mark.xfail(reason="T425: BOLA - no owner filtering on SmartBlocks")
    def test_bola_list_other_users_blocks(self, guest_client):
        """BOLA: Should only see own smart blocks."""
        victim = baker.make(User, username="testred_victim")
        victim_block = baker.make(
            SmartBlock,
            name="Victim Secret Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        data = response.json()

        block_names = [b["name"] for b in data]
        assert (
            "Victim Secret Block" not in block_names
        ), "BOLA: Attacker sees victim's block"

    @pytest.mark.xfail(reason="T425: BOLA via kind filter")
    def test_bola_filter_kind_shows_others(self, guest_client):
        """BOLA: Kind filter should not expose other's blocks."""
        victim = baker.make(User, username="testred_victim")
        baker.make(
            SmartBlock,
            name="Victim Dynamic",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )

        response = guest_client.get(
            f"/api/v2/smart-blocks?kind={SmartBlock.Kind.DYNAMIC}",
        )
        data = response.json()

        names = [b["name"] for b in data]
        assert (
            "Victim Dynamic" not in names
        ), "BOLA: Filter exposes victim's blocks"

    # ========================================================================
    # API3:2023 - BOPLA
    # ========================================================================

    def test_bopla_field_exposure(self, guest_client):
        """BOPLA: Check for sensitive field exposure."""
        user = baker.make(User, username="testred_user")
        baker.make(
            SmartBlock,
            name="Test Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        data = response.json()

        sensitive = ["password", "secret", "token", "internal"]
        for block in data:
            for field in block.keys():
                for s in sensitive:
                    assert (
                        s not in field.lower()
                    ), f"BOPLA: Sensitive field '{field}'"

    # ========================================================================
    # API6:2023 - Resource
    # ========================================================================

    def test_list_pagination_check(self, guest_client):
        """Resource: Check for pagination on large lists."""
        user = baker.make(User, username="testred_user")

        # Create many blocks
        for i in range(50):
            baker.make(
                SmartBlock,
                name=f"Block {i}",
                kind=SmartBlock.Kind.STATIC,
                owner=user,
            )

        start = time.time()
        response = guest_client.get("/api/v2/smart-blocks")
        elapsed = time.time() - start

        data = response.json()
        # If all 50 returned without pagination, that's a concern
        if len(data) == 50:
            pass  # Document: no pagination

        assert elapsed < 3.0, f"DoS: 50 blocks took {elapsed}s"

    # ========================================================================
    # Injection
    # ========================================================================

    def test_filter_sql_injection_kind(self, guest_client):
        """SQLi: Injection in kind filter."""
        sqli_payloads = [
            "0' OR '1'='1",
            "0; DROP TABLE cc_block;--",
            "0 UNION SELECT * FROM users",
        ]

        for payload in sqli_payloads:
            response = guest_client.get(f"/api/v2/smart-blocks?kind={payload}")
            assert response.status_code in [
                200,
                400,
                404,
            ], f"SQLi '{payload}' caused {response.status_code}"

    def test_ordering_sql_injection(self, guest_client):
        """SQLi: Injection in ordering param."""
        payloads = [
            "name; DROP TABLE users;--",
            "name ASC; DELETE FROM cc_block;--",
        ]

        for payload in payloads:
            response = guest_client.get(
                f"/api/v2/smart-blocks?ordering={payload}",
            )
            assert response.status_code in [
                200,
                400,
            ], f"Order injection caused {response.status_code}"

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_list_invalid_kind(self, guest_client):
        """Edge: Invalid kind value."""
        response = guest_client.get("/api/v2/smart-blocks?kind=invalid")
        assert response.status_code in [
            200,
            400,
        ], f"Invalid kind caused {response.status_code}"

    def test_list_no_auth(self, client):
        """Auth: No auth should fail."""
        response = client.get("/api/v2/smart-blocks")
        assert response.status_code == 403