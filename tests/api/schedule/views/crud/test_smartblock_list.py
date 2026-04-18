"""Tests for SmartBlocks LIST endpoint (T234)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock


@pytest.mark.django_db(transaction=True)
class TestSmartBlockViewSetList:
    """Test SmartBlocks LIST endpoint - GET /api/v2/smart-blocks."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsb").delete()

    def test_list_empty_returns_200(self, guest_client):
        """LIST empty should return 200 with empty list."""
        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_static_block(self, guest_client):
        """LIST should return static block with correct fields."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Static Block"
        assert data[0]["kind"] == SmartBlock.Kind.STATIC

    def test_list_single_dynamic_block(self, guest_client):
        """LIST should return dynamic block with correct fields."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Dynamic Block"
        assert data[0]["kind"] == SmartBlock.Kind.DYNAMIC

    def test_list_multiple_blocks(self, guest_client):
        """LIST should return multiple blocks."""
        user = baker.make(User, username="testsb_user")
        baker.make(
            SmartBlock,
            name="Block 1",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        baker.make(
            SmartBlock,
            name="Block 2",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        baker.make(
            SmartBlock,
            name="Block 3",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_filter_by_kind(self, guest_client):
        """LIST should filter by kind parameter."""
        user = baker.make(User, username="testsb_user")
        baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = guest_client.get(
            f"/api/v2/smart-blocks?kind={SmartBlock.Kind.STATIC}",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["kind"] == SmartBlock.Kind.STATIC

    def test_list_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/smart-blocks")
        assert response.status_code == 403

    def test_list_returns_all_fields(self, guest_client):
        """LIST should return all serializer fields."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Test Block",
            description="Test description",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        data = response.json()[0]
        expected_fields = {
            "id",
            "name",
            "description",
            "length",
            "kind",
            "owner",
            "created_at",
            "updated_at",
        }
        assert set(data.keys()) == expected_fields

    def test_list_with_description(self, guest_client):
        """LIST should include description field."""
        user = baker.make(User, username="testsb_user")
        baker.make(
            SmartBlock,
            name="Block",
            description="My description",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        assert response.json()[0]["description"] == "My description"

    def test_list_unicode_names(self, guest_client):
        """LIST should handle unicode in block names."""
        user = baker.make(User, username="testsb_user")
        baker.make(
            SmartBlock,
            name="Блок с музыкой 🎵",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        assert response.json()[0]["name"] == "Блок с музыкой 🎵"
