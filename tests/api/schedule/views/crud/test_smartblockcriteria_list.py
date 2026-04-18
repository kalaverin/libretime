"""Tests for SmartBlockCriteria LIST endpoint (T241)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaViewSetList:
    """Test SmartBlockCriteria LIST endpoint - GET /api/v2/smart-block-criteria."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsbcr").delete()

    def test_list_empty_returns_200(self, admin_client):
        """LIST empty should return 200 with empty list."""
        response = admin_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_criteria(self, admin_client):
        """LIST should return single criteria with correct fields."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        response = admin_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["block"] == block.id
        assert data[0]["criteria"] == "genre"
        assert data[0]["condition"] == "contains"
        assert data[0]["value"] == "Jazz"

    def test_list_multiple_criteria(self, admin_client):
        """LIST should return multiple criteria."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
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
        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="artist",
            condition="starts",
            value="Miles",
        )

        response = admin_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_filter_by_block(self, admin_client):
        """LIST should filter by block parameter."""
        user = baker.make(User, username="testsbcr_user")
        block1 = baker.make(
            SmartBlock,
            name="Block 1",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        block2 = baker.make(
            SmartBlock,
            name="Block 2",
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
            f"/api/v2/smart-block-criteria?block={block1.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["block"] == block1.id

    def test_list_with_group(self, admin_client):
        """LIST should include group field."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
            group=1,
        )

        response = admin_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 200
        assert response.json()[0]["group"] == 1

    def test_list_with_extra(self, admin_client):
        """LIST should include extra field."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
            extra="extra data",
        )

        response = admin_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 200
        assert response.json()[0]["extra"] == "extra data"

    def test_list_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 403

    def test_list_returns_all_fields(self, admin_client):
        """LIST should return all serializer fields."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
            group=1,
            extra="extra",
        )

        response = admin_client.get("/api/v2/smart-block-criteria")
        data = response.json()[0]
        expected_fields = {
            "id",
            "block",
            "group",
            "criteria",
            "condition",
            "value",
            "extra",
        }
        assert set(data.keys()) == expected_fields
