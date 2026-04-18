"""Tests for SmartBlocks permissions (T238)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock


@pytest.mark.django_db(transaction=True)
class TestSmartBlockViewSetPermissions:
    """Test SmartBlocks permissions."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsb").delete()

    # === AUTHENTICATION REQUIRED ===

    def test_list_requires_auth(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/smart-blocks")
        assert response.status_code == 403

    def test_retrieve_requires_auth(self, client):
        """RETRIEVE without auth should return 403."""
        response = client.get("/api/v2/smart-blocks/1")
        assert response.status_code == 403

    def test_create_requires_auth(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_requires_auth(self, client):
        """UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/smart-blocks/1",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_requires_auth(self, client):
        """DELETE without auth should return 403."""
        response = client.delete("/api/v2/smart-blocks/1")
        assert response.status_code == 403

    # === AUTHORIZED USERS CAN ACCESS ===

    def test_list_with_auth_returns_200(self, admin_client):
        """LIST with auth should return 200."""
        response = admin_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200

    def test_retrieve_with_auth_returns_200(self, admin_client):
        """RETRIEVE with auth should return 200."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        response = admin_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200

    def test_create_with_auth_returns_201(self, admin_client):
        """CREATE with auth should return 201."""
        response = admin_client.post(
            "/api/v2/smart-blocks",
            json.dumps({"name": "Test", "kind": SmartBlock.Kind.STATIC}),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_update_with_auth_returns_200(self, admin_client):
        """UPDATE with auth should return 200."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        response = admin_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_delete_with_auth_returns_204(self, admin_client):
        """DELETE with auth should return 204."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        response = admin_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 204

    # === CROSS-USER ACCESS ===

    def test_user_can_view_other_users_blocks(self, admin_client):
        """Any authenticated user can view any block."""
        other_user = baker.make(User, username="testsb_other")
        block = baker.make(
            SmartBlock,
            name="Other Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=other_user,
        )

        response = admin_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Other Block"
