"""Tests for Playlists permissions (T227)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistViewSetPermissions:
    """Test Playlists permissions."""

    def setup_method(self):
        """Clean up before each test."""
        Playlist.objects.all().delete()
        User.objects.filter(username__startswith="testplaylist").delete()

    # === AUTHENTICATION REQUIRED ===

    def test_list_requires_auth(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/playlists")
        assert response.status_code == 403

    def test_retrieve_requires_auth(self, client):
        """RETRIEVE without auth should return 403."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        response = client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 403

    def test_create_requires_auth(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/playlists",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_requires_auth(self, client):
        """UPDATE without auth should return 403."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_requires_auth(self, client):
        """DELETE without auth should return 403."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        response = client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 403

    # === AUTHORIZED USERS CAN ACCESS ===

    def test_list_with_auth_returns_200(self, admin_client):
        """LIST with auth should return 200."""
        response = admin_client.get("/api/v2/playlists")
        assert response.status_code == 200

    def test_retrieve_with_auth_returns_200(self, admin_client):
        """RETRIEVE with auth should return 200."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        response = admin_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200

    def test_create_with_auth_returns_201(self, admin_client):
        """CREATE with auth should return 201."""
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_update_with_auth_returns_200(self, admin_client):
        """UPDATE with auth should return 200."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        response = admin_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_delete_with_auth_returns_204(self, admin_client):
        """DELETE with auth should return 204."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        response = admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 204

    # === CROSS-USER ACCESS ===

    def test_user_can_view_other_users_playlists(self, admin_client):
        """Any authenticated user can view any playlist (no owner isolation)."""
        other_user = baker.make(User, username="testplaylist_other")
        playlist = baker.make(
            Playlist,
            name="Other Playlist",
            owner=other_user,
        )

        response = admin_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Other Playlist"

    def test_user_can_update_other_users_playlists(self, admin_client):
        """Any authenticated user can update any playlist."""
        other_user = baker.make(User, username="testplaylist_other")
        playlist = baker.make(
            Playlist,
            name="Other Playlist",
            owner=other_user,
        )

        response = admin_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "Modified by other"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Modified by other"

    def test_user_can_delete_other_users_playlists(self, admin_client):
        """Any authenticated user can delete any playlist."""
        other_user = baker.make(User, username="testplaylist_other")
        playlist = baker.make(
            Playlist,
            name="Other Playlist",
            owner=other_user,
        )

        response = admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 204
        assert not Playlist.objects.filter(id=playlist.id).exists()
