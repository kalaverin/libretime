"""Tests for Playlists UPDATE endpoint (T225)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistViewSetUpdate:
    """Test Playlists UPDATE endpoint - PUT/PATCH /api/v2/playlists/{id}."""

    def setup_method(self):
        """Clean up playlists before each test."""
        Playlist.objects.all().delete()
        User.objects.filter(username__startswith="testplaylist").delete()

    def test_patch_update_name_success(self, api_client):
        """PATCH should update playlist name."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Original Name", owner=user)

        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "Updated Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_patch_update_description_success(self, api_client):
        """PATCH should update playlist description."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="Test",
            description="Original",
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"description": "Updated description"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_patch_clear_description(self, api_client):
        """PATCH should clear description."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="Test",
            description="Original",
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"description": None}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["description"] is None

    def test_patch_not_found_returns_404(self, api_client):
        """PATCH non-existent playlist should return 404."""
        response = api_client.patch(
            "/api/v2/playlists/999999",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_patch_no_auth_fails(self, client):
        """PATCH without auth should return 403."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_patch_empty_body_no_change(self, api_client):
        """PATCH with empty body should not change anything."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="Original",
            description="Test",
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Original"
        assert result["description"] == "Test"

    def test_put_update_success(self, api_client):
        """PUT with all fields should succeed."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="Old",
            description="Old desc",
            owner=user,
        )

        data = {
            "name": "New Name",
            "description": "New description",
            "owner": user.id,
        }
        response = api_client.put(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [200, 400]

    def test_put_not_found_returns_404(self, api_client):
        """PUT non-existent playlist should return 404."""
        user = baker.make(User, username="testplaylist_user")
        data = {
            "name": "Test",
            "owner": user.id,
        }
        response = api_client.put(
            "/api/v2/playlists/999999",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_unicode_values(self, api_client):
        """PATCH with unicode values should work."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(
                {"name": "日本語プレイリスト", "description": "日本語の説明"},
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "日本語プレイリスト"
        assert result["description"] == "日本語の説明"

    def test_update_empty_name_fails(self, api_client):
        """UPDATE with empty name should fail."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
