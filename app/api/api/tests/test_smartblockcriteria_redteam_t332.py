"""
RED TEAM: T332 - SmartBlockCriteria filter security tests.

Attack vectors:
- Filter injection (SQLi through block param)
- BOLA: access other users' criteria
- Block ID type confusion
- Information disclosure
"""

import pytest
from model_bakery import baker
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestSmartBlockCriteriaFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_block_id(self, api_client, admin_user):
        """Try to filter by invalid block_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-criteria?block=invalid")

        if response.status_code == 500:
            pytest.fail("BAG: Filter crashes on invalid block_id (500 error)")
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in block filter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_blockcriteria;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/smart-block-criteria?block={payload}"
            )

            if response.status_code == 500:
                pytest.fail(f"BAG: SQL injection causes 500: {payload}")

    def test_filter_by_negative_block_id(self, api_client, admin_user):
        """Try to filter by negative block_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-criteria?block=-1")
        assert response.status_code in [200, 400]

    def test_filter_by_float_block_id(self, api_client, admin_user):
        """Try to filter by float block_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-criteria?block=1.5")
        assert response.status_code in [200, 400]

    def test_filter_without_auth(self, api_client):
        """Try to filter without authentication."""
        response = api_client.get("/api/v2/smart-block-criteria?block=1")

        if response.status_code == 200:
            pytest.fail("BAG: Anonymous can filter smart block criteria")


@pytest.mark.django_db
class TestSmartBlockCriteriaBOLA:
    """Broken Object Level Authorization attacks."""

    def test_list_shows_only_own_criteria(self, api_client, admin_user, regular_user):
        """Verify list returns only user's own criteria."""
        # Create blocks and criteria for both users
        admin_block = baker.make("schedule.SmartBlock", owner=admin_user, kind="dynamic")
        user_block = baker.make("schedule.SmartBlock", owner=regular_user, kind="dynamic")

        admin_criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=admin_block,
            group=1,
            criteria="title",
            value="Admin",
        )
        user_criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=user_block,
            group=1,
            criteria="title",
            value="User",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/smart-block-criteria/")

        assert response.status_code == 200
        data = response.json()

        criteria_ids = [c["id"] for c in data]
        assert user_criteria.id in criteria_ids

        if admin_criteria.id in criteria_ids:
            pytest.fail("CRITICAL BAG: List shows other users' criteria (BOLA)")

    def test_access_other_user_criteria(self, api_client, admin_user, regular_user):
        """Try to access another user's criteria by ID."""
        admin_block = baker.make("schedule.SmartBlock", owner=admin_user, kind="dynamic")
        criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=admin_block,
            group=1,
            criteria="title",
            value="Admin",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/smart-block-criteria/{criteria.id}/")

        if response.status_code == 200:
            pytest.fail("CRITICAL BAG: Can access other user's criteria (BOLA)")

    def test_update_other_user_criteria(self, api_client, admin_user, regular_user):
        """Try to update another user's criteria."""
        admin_block = baker.make("schedule.SmartBlock", owner=admin_user, kind="dynamic")
        criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=admin_block,
            group=1,
            criteria="title",
            value="Admin",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}/",
            {"value": "Hacked"},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail("CRITICAL BAG: Can update other user's criteria (BOLA)")

    def test_delete_other_user_criteria(self, api_client, admin_user, regular_user):
        """Try to delete another user's criteria."""
        admin_block = baker.make("schedule.SmartBlock", owner=admin_user, kind="dynamic")
        criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=admin_block,
            group=1,
            criteria="title",
            value="Admin",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/smart-block-criteria/{criteria.id}/")

        if response.status_code == 204:
            pytest.fail("CRITICAL BAG: Can delete other user's criteria (BOLA)")

    def test_filter_shows_only_own_by_block(self, api_client, admin_user, regular_user):
        """Verify filter by block returns only user's own criteria."""
        admin_block = baker.make("schedule.SmartBlock", owner=admin_user, kind="dynamic")
        user_block = baker.make("schedule.SmartBlock", owner=regular_user, kind="dynamic")

        admin_criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=admin_block,
            group=1,
            criteria="title",
            value="Admin",
        )
        user_criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=user_block,
            group=1,
            criteria="title",
            value="User",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/smart-block-criteria?block={user_block.id}")

        assert response.status_code == 200
        data = response.json()

        criteria_ids = [c["id"] for c in data]
        assert user_criteria.id in criteria_ids

        if admin_criteria.id in criteria_ids:
            pytest.fail("BAG: Filter by block shows other users' criteria (BOLA)")


@pytest.mark.django_db
class TestSmartBlockCriteriaMassAssignment:
    """Mass assignment attacks."""

    def test_create_with_id_field(self, api_client, admin_user):
        """Try to set id field during creation."""
        block = baker.make("schedule.SmartBlock", owner=admin_user, kind="dynamic")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/smart-block-criteria/",
            {
                "id": 99999,
                "block": block.id,
                "group": 1,
                "criteria": "title",
                "value": "Test",
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.fail("BAG: Can set id field")

    def test_update_block_field(self, api_client, admin_user, regular_user):
        """Try to change block via PATCH."""
        block1 = baker.make("schedule.SmartBlock", owner=admin_user, kind="dynamic")
        block2 = baker.make("schedule.SmartBlock", owner=regular_user, kind="dynamic")
        criteria = baker.make(
            "schedule.SmartBlockCriteria",
            block=block1,
            group=1,
            criteria="title",
            value="Test",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}/",
            {"block": block2.id},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("block") == block2.id:
                pytest.fail("BAG: Can transfer criteria to another block")


@pytest.mark.django_db
class TestSmartBlockCriteriaBusinessLogic:
    """Business logic bypasses."""

    def test_create_without_auth(self, api_client):
        """Try to create without authentication."""
        response = api_client.post(
            "/api/v2/smart-block-criteria/",
            {
                "group": 1,
                "criteria": "title",
                "value": "Test",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BAG: Anonymous can create criteria")

    def test_create_with_nonexistent_block(self, api_client, admin_user):
        """Try to create with non-existent block."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/smart-block-criteria/",
            {
                "block": 99999,
                "group": 1,
                "criteria": "title",
                "value": "Test",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BAG: Accepts non-existent block_id")

    def test_create_criteria_for_static_block(self, api_client, admin_user):
        """Try to create criteria for static block (should be dynamic only)."""
        block = baker.make("schedule.SmartBlock", owner=admin_user, kind="static")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/smart-block-criteria/",
            {
                "block": block.id,
                "group": 1,
                "criteria": "title",
                "value": "Test",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]
