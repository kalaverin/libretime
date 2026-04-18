"""Red Team security tests for SmartBlockCriteria LIST endpoint (T241).

Tests focus on:
- API1:2023 BOLA (accessing other users' criteria)
- Filter bypass attacks
- Injection in filter parameters
- Pagination abuse
- Field exposure
- Information disclosure
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaListRedTeam:
    """Red Team tests for GET /api/v2/smart-block-criteria."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T488: BOLA - LIST shows all users' criteria without filtering",
    )
    def test_bola_list_shows_all_users_criteria(self, admin_client):
        """BOLA: LIST should only show criteria from user's own blocks."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Victim's private block with criteria
        victim_block = baker.make(
            SmartBlock,
            name="Victim Private Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        victim_criteria = baker.make(
            SmartBlockCriteria,
            block=victim_block,
            criteria="genre",
            condition="contains",
            value="Secret Genre",
        )

        # Attacker lists all criteria
        response = admin_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 200

        data = response.json()
        victim_criteria_ids = [
            c["id"] for c in data if c.get("block") == victim_block.id
        ]

        assert (
            len(victim_criteria_ids) == 0
        ), f"BOLA: Attacker can see {len(victim_criteria_ids)} victim's criteria"

    @pytest.mark.xfail(
        reason="T489: BOLA - filter by block ID bypasses ownership",
    )
    def test_bola_filter_by_other_users_block(self, admin_client):
        """BOLA: Should not be able to filter by other user's block ID."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Victim's block with criteria
        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        baker.make(
            SmartBlockCriteria,
            block=victim_block,
            criteria="genre",
            condition="contains",
            value="Secret",
        )

        # Attacker filters by victim's block ID
        response = admin_client.get(
            f"/api/v2/smart-block-criteria?block={victim_block.id}",
        )
        assert response.status_code == 200

        data = response.json()
        assert (
            len(data) == 0
        ), f"BOLA: Filter by victim's block returned {len(data)} items"

    def test_criteria_id_enumeration_mitigated(self, admin_client):
        """Security: Criteria ID enumeration mitigated by owner filtering."""
        user = baker.make(User, username="testred_enum")
        for i in range(5):
            block = baker.make(
                SmartBlock,
                name=f"Block {i}",
                kind=SmartBlock.Kind.DYNAMIC,
                owner=user,
            )
            baker.make(
                SmartBlockCriteria,
                block=block,
                criteria="genre",
                condition="contains",
                value=f"Genre {i}",
            )

        response = admin_client.get("/api/v2/smart-block-criteria")
        data = response.json()

        assert isinstance(data, list), "Response should be a list"

    # ========================================================================
    # Filter Bypass Attacks
    # ========================================================================

    @pytest.mark.xfail(
        reason="T490: Filter bypass - SQL injection in block parameter",
    )
    def test_filter_sql_injection_block_param(self, admin_client):
        """Injection: SQLi in block filter parameter."""
        sqli_payloads = [
            "1' OR '1'='1",
            "1 OR 1=1",
            "1; DROP TABLE cc_blockcriteria;--",
            "1 UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = admin_client.get(
                f"/api/v2/smart-block-criteria?block={payload}",
            )
            assert response.status_code in [
                200,
                400,
                404,
            ], f"SQLi payload '{payload}' caused {response.status_code}"

    def test_filter_negative_block_id_handled(self, admin_client):
        """Validation: Negative block ID handled gracefully."""
        response = admin_client.get("/api/v2/smart-block-criteria?block=-1")
        assert response.status_code in [
            200,
            400,
        ], f"Negative block ID caused {response.status_code}"

    def test_filter_zero_block_id_handled(self, admin_client):
        """Validation: Zero block ID handled gracefully."""
        response = admin_client.get("/api/v2/smart-block-criteria?block=0")
        assert response.status_code in [
            200,
            400,
        ], f"Zero block ID caused {response.status_code}"

    @pytest.mark.xfail(reason="T491: 500 error on non-numeric block_id filter")
    def test_filter_non_numeric_block_id(self, admin_client):
        """Validation: Non-numeric block ID in filter - BUG T491."""
        response = admin_client.get("/api/v2/smart-block-criteria?block=abc")
        assert response.status_code in [
            400,
            404,
        ], f"BUG T491: Non-numeric block ID caused {response.status_code}"

    @pytest.mark.xfail(reason="T492: 500 error on unicode block_id filter")
    def test_filter_unicode_block_id(self, admin_client):
        """Validation: Unicode in block filter - BUG T492."""
        response = admin_client.get("/api/v2/smart-block-criteria?block=日本語")
        assert response.status_code in [
            400,
            404,
        ], f"BUG T492: Unicode block ID caused {response.status_code}"

    # ========================================================================
    # Sorting / Ordering Attacks
    # ========================================================================

    def test_sorting_arbitrary_field_rejected(self, admin_client):
        """Security: Arbitrary ordering fields are rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        malicious_orderings = [
            "id; DROP TABLE cc_blockcriteria;--",
            "(SELECT password FROM cc_user)",
        ]

        for ordering in malicious_orderings:
            response = admin_client.get(
                f"/api/v2/smart-block-criteria?ordering={ordering}",
            )
            assert response.status_code in [
                200,
                400,
            ], f"Ordering '{ordering}' caused {response.status_code}"

    # ========================================================================
    # Pagination Abuse
    # ========================================================================

    def test_pagination_page_size_limited(self, admin_client):
        """Security: Page size is properly limited."""
        user = baker.make(User, username="testred_user")

        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        for i in range(100):
            baker.make(
                SmartBlockCriteria,
                block=block,
                criteria="genre",
                condition="contains",
                value=f"Genre {i}",
            )

        response = admin_client.get(
            "/api/v2/smart-block-criteria?page_size=999999",
        )
        assert (
            response.status_code == 200
        ), f"Large page size caused {response.status_code}"

    def test_pagination_negative_page(self, admin_client):
        """Validation: Negative page number."""
        response = admin_client.get("/api/v2/smart-block-criteria?page=-1")
        assert response.status_code in [
            200,
            400,
        ], f"Negative page caused {response.status_code}"

    # ========================================================================
    # Field Exposure
    # ========================================================================

    def test_field_exposure_no_internal_fields(self, admin_client):
        """Security: Internal fields are not exposed."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        response = admin_client.get("/api/v2/smart-block-criteria")
        data = response.json()

        if len(data) > 0:
            fields = set(data[0].keys())
            forbidden_fields = {
                "_state",
                "password",
                "secret",
                "token",
                "internal_id",
            }
            leaked = fields & forbidden_fields
            assert len(leaked) == 0, f"Internal fields leaked: {leaked}"

    def test_field_exposure_related_objects_are_ids(self, admin_client):
        """Security: Related objects are returned as IDs only."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        response = admin_client.get("/api/v2/smart-block-criteria")
        data = response.json()

        if len(data) > 0:
            criteria = data[0]
            assert isinstance(criteria.get("block"), int), "Block should be ID"

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    @pytest.mark.xfail(reason="T493: Error message leaks query structure")
    def test_error_message_leaks_structure(self, admin_client):
        """Info Leak: Error messages reveal database structure."""
        response = admin_client.get(
            "/api/v2/smart-block-criteria?block=invalid'union",
        )

        error_body = response.content.decode().lower()

        sensitive_patterns = [
            "sql",
            "postgresql",
            "sqlite",
            "column",
            "table",
            "cc_blockcriteria",
        ]

        for pattern in sensitive_patterns:
            assert pattern not in error_body, f"Error message leaks: {pattern}"

    # ========================================================================
    # HPP (HTTP Parameter Pollution)
    # ========================================================================

    def test_hpp_duplicate_filter_params(self, admin_client):
        """HPP: Duplicate block filter parameters."""
        user = baker.make(User, username="testred_user")
        block1 = baker.make(
            SmartBlock,
            name="Block1",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        block2 = baker.make(
            SmartBlock,
            name="Block2",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        baker.make(
            SmartBlockCriteria,
            block=block1,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )
        baker.make(
            SmartBlockCriteria,
            block=block2,
            criteria="genre",
            condition="contains",
            value="Rock",
        )

        response = admin_client.get(
            f"/api/v2/smart-block-criteria?block={block1.id}&block={block2.id}",
        )
        assert (
            response.status_code == 200
        ), f"HPP caused {response.status_code}"

    # ========================================================================
    # CORS and Headers
    # ========================================================================

    def test_cors_preflight_list(self, admin_client):
        """CORS: Preflight request for LIST."""
        response = admin_client.options(
            "/api/v2/smart-block-criteria",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        allowed_origin = response.get("Access-Control-Allow-Origin", "")
        assert "evil.com" not in allowed_origin, "CORS allows arbitrary origin"

    # ========================================================================
    # Fuzzing
    # ========================================================================

    @pytest.mark.xfail(
        reason="T494: 500 error on special query params (undefined, null)",
    )
    def test_fuzzing_query_params(self, admin_client):
        """Fuzzing: Naughty strings in query parameters - BUG T494."""
        naughty_params = [
            "undefined",
            "null",
            "None",
        ]

        for param in naughty_params:
            response = admin_client.get(
                f"/api/v2/smart-block-criteria?block={param}",
            )
            assert response.status_code in [
                400,
                404,
            ], f"BUG T494: Naughty param '{param}' caused {response.status_code}"

    # ========================================================================
    # Value-based Information Leak
    # ========================================================================

    @pytest.mark.xfail(reason="T495: Criteria values leak block information")
    def test_criteria_value_leaks_block_info(self, admin_client):
        """Info Leak: Criteria values may reveal sensitive block configuration."""
        victim = baker.make(User, username="testred_victim")

        # Victim creates a block with sensitive criteria
        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        baker.make(
            SmartBlockCriteria,
            block=victim_block,
            criteria="owner",
            condition="is",
            value="specific_artist_name",
        )

        # Attacker lists criteria and sees the value
        response = admin_client.get("/api/v2/smart-block-criteria")
        data = response.json()

        for criteria in data:
            if criteria.get("value") == "specific_artist_name":
                assert (
                    False
                ), "Criteria value leaks victim's private configuration"