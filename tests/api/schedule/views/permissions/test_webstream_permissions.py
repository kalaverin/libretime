"""Tests for Webstreams permissions (T249)."""

import json

import pytest

from model_bakery import baker
from sdk.datetime import reformat_datetime

from api.core.models import User
from api.schedule.models import Webstream


@pytest.mark.django_db(transaction=True)
class TestWebstreamViewSetPermissions:
    """Test Webstreams permissions."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        User.objects.filter(username__startswith="testws").delete()

    # === AUTHENTICATION REQUIRED ===

    def test_list_requires_auth(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/webstreams")
        assert response.status_code == 403

    def test_retrieve_requires_auth(self, client):
        """RETRIEVE without auth should return 403."""
        response = client.get("/api/v2/webstreams/1")
        assert response.status_code == 403

    def test_create_requires_auth(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/webstreams",
            json.dumps({"name": "Test", "url": "http://example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_requires_auth(self, client):
        """UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/webstreams/1",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_requires_auth(self, client):
        """DELETE without auth should return 403."""
        response = client.delete("/api/v2/webstreams/1")
        assert response.status_code == 403

    # === AUTHORIZED USERS CAN ACCESS ===

    def test_list_with_auth_returns_200(self, guest_client):
        """LIST with auth should return 200."""
        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200

    def test_retrieve_with_auth_returns_200(self, guest_client):
        """RETRIEVE with auth should return 200."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            owner=user,
        )
        response = guest_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 200
        data = response.json()
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "created_at" in data
        assert reformat_datetime(data["created_at"]) is not None

    def test_update_with_auth_returns_200(self, guest_client):
        """UPDATE with auth should return 200."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            owner=user,
        )
        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "updated_at" in data
        assert reformat_datetime(data["updated_at"]) is not None

    def test_delete_with_auth_returns_204(self, guest_client):
        """DELETE with auth should return 204."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            owner=user,
        )
        response = guest_client.delete(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 204

    # === CROSS-USER ACCESS ===

    def test_user_can_view_other_users_streams(self, guest_client):
        """Any authenticated user can view any webstream."""
        other_user = baker.make(User, username="testws_other")
        stream = baker.make(
            Webstream,
            name="Other Stream",
            url="http://example.com/stream",
            owner=other_user,
        )

        response = guest_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Other Stream"
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "created_at" in data
        assert reformat_datetime(data["created_at"]) is not None
