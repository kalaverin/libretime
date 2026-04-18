"""Tests for Webstreams UPDATE endpoint (T247)."""

import json

import pytest

from model_bakery import baker
from sdk.datetime import reformat_datetime

from api.core.models import User
from api.schedule.models import Webstream


@pytest.mark.django_db(transaction=True)
class TestWebstreamViewSetUpdate:
    """Test Webstreams UPDATE endpoint - PATCH/PUT /api/v2/webstreams/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        User.objects.filter(username__startswith="testws").delete()

    def test_patch_update_name_success(self, guest_client):
        """PATCH name should update webstream."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Old Name",
            url="http://example.com/stream",
            owner=user,
        )

        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "updated_at" in data
        assert reformat_datetime(data["updated_at"]) is not None

    def test_patch_update_url(self, guest_client):
        """PATCH URL should update webstream."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://old.com/stream",
            owner=user,
        )

        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"url": "http://new.com/stream"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "http://new.com/stream"
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "updated_at" in data
        assert reformat_datetime(data["updated_at"]) is not None

    def test_patch_update_description(self, guest_client):
        """PATCH description should update webstream."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            description="Old",
            owner=user,
        )

        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"description": "New description"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "updated_at" in data
        assert reformat_datetime(data["updated_at"]) is not None

    def test_patch_partial_does_not_affect_other_fields(self, guest_client):
        """PATCH should only update specified fields."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            description="Keep",
            owner=user,
        )

        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["url"] == "http://example.com/stream"
        assert data["description"] == "Keep"
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "updated_at" in data
        assert reformat_datetime(data["updated_at"]) is not None

    def test_put_full_update_success(self, guest_client):
        """PUT should update all fields."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = guest_client.put(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps(
                {
                    "name": "Updated Stream",
                    "url": "http://updated.com/stream",
                    "description": "Updated desc",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Stream"
        assert data["url"] == "http://updated.com/stream"
        assert data["description"] == "Updated desc"

    def test_update_not_found_returns_404(self, guest_client):
        """UPDATE non-existent webstream should return 404."""
        response = guest_client.patch(
            "/api/v2/webstreams/999999",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_no_auth_fails(self, client):
        """UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/webstreams/1",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_empty_name_fails(self, guest_client):
        """UPDATE with empty name should fail."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_unicode_values(self, guest_client):
        """UPDATE with unicode values should succeed."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps(
                {
                    "name": "Обновлённый поток 🎵",
                    "description": "Описание",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Обновлённый поток 🎵"
        assert data["description"] == "Описание"
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T351)
        assert "updated_at" in data
        assert reformat_datetime(data["updated_at"]) is not None
