"""Tests for SmartBlocks CREATE endpoint (T235)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock


@pytest.mark.django_db(transaction=True)
class TestSmartBlockViewSetCreate:
    """Test SmartBlocks CREATE endpoint - POST /api/v2/smart-blocks."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsb").delete()

    def test_create_static_block_success(self, guest_client):
        """CREATE static block should return 201."""
        user = baker.make(User, username="testsb_user")

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Static Block",
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Static Block"
        assert data["kind"] == SmartBlock.Kind.STATIC

    def test_create_dynamic_block_success(self, guest_client):
        """CREATE dynamic block should return 201."""
        user = baker.make(User, username="testsb_user")

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Dynamic Block",
                    "kind": SmartBlock.Kind.DYNAMIC,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Dynamic Block"
        assert data["kind"] == SmartBlock.Kind.DYNAMIC

    def test_create_with_description(self, guest_client):
        """CREATE with description should succeed."""
        user = baker.make(User, username="testsb_user")

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": SmartBlock.Kind.STATIC,
                    "description": "My test description",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["description"] == "My test description"

    def test_create_default_kind_is_dynamic(self, guest_client):
        """CREATE without kind should default to dynamic."""
        user = baker.make(User, username="testsb_user")

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps({"name": "Test Block"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["kind"] == SmartBlock.Kind.DYNAMIC

    def test_create_missing_name_fails(self, guest_client):
        """CREATE without name should return 400."""
        user = baker.make(User, username="testsb_user")

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps({"kind": SmartBlock.Kind.STATIC}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_unicode_name(self, guest_client):
        """CREATE with unicode name should succeed."""
        user = baker.make(User, username="testsb_user")

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Блок 🎵 Music",
                    "kind": SmartBlock.Kind.DYNAMIC,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Блок 🎵 Music"

    def test_create_long_description(self, guest_client):
        """CREATE with long description should succeed."""
        user = baker.make(User, username="testsb_user")
        long_desc = "A" * 512

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": SmartBlock.Kind.STATIC,
                    "description": long_desc,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["description"] == long_desc

    def test_create_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_invalid_kind_fails(self, guest_client):
        """CREATE with invalid kind should return 400."""
        user = baker.make(User, username="testsb_user")

        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Test Block",
                    "kind": "invalid",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
