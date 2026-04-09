"""Tests for SmartBlocks UPDATE endpoint (T236)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock


@pytest.mark.django_db(transaction=True)
class TestSmartBlockViewSetUpdate:
    """Test SmartBlocks UPDATE endpoint - PATCH/PUT /api/v2/smart-blocks/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsb").delete()

    def test_patch_update_name_success(self, api_client):
        """PATCH name should update block."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Old Name",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_patch_update_description(self, api_client):
        """PATCH description should update block."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            description="Old",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"description": "New description"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["description"] == "New description"

    def test_patch_clear_description(self, api_client):
        """PATCH description to null should clear it."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            description="To clear",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"description": None}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["description"] is None

    def test_patch_partial_does_not_affect_other_fields(self, api_client):
        """PATCH should only update specified fields."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            description="Keep",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Keep"
        assert data["kind"] == SmartBlock.Kind.STATIC

    def test_put_full_update_success(self, api_client):
        """PUT should update all fields."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.put(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps(
                {
                    "name": "Updated Block",
                    "kind": SmartBlock.Kind.DYNAMIC,
                    "description": "Updated desc",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Block"
        assert data["kind"] == SmartBlock.Kind.DYNAMIC
        assert data["description"] == "Updated desc"

    def test_update_not_found_returns_404(self, api_client):
        """UPDATE non-existent block should return 404."""
        response = api_client.patch(
            "/api/v2/smart-blocks/999999",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_no_auth_fails(self, client):
        """UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/smart-blocks/1",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_empty_name_fails(self, api_client):
        """UPDATE with empty name should fail."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_unicode_values(self, api_client):
        """UPDATE with unicode values should succeed."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps(
                {
                    "name": "Обновлённый блок 🎵",
                    "description": "Описание",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Обновлённый блок 🎵"
        assert data["description"] == "Описание"
