"""Tests for Playlists DELETE endpoint (T226)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistViewSetDelete:
    """Test Playlists DELETE endpoint - DELETE /api/v2/playlists/{id}."""

    def setup_method(self):
        """Clean up playlists before each test."""
        Playlist.objects.all().delete()
        User.objects.filter(username__startswith="testplaylist").delete()

    def test_delete_playlist_success_returns_204(self, admin_client):
        """DELETE should return 204 on successful deletion."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        response = admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 204

    def test_delete_playlist_removes_from_db(self, admin_client):
        """DELETE should remove playlist from database."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert Playlist.objects.filter(id=playlist.id).count() == 0

    def test_delete_playlist_not_found_returns_404(self, admin_client):
        """DELETE non-existent playlist should return 404."""
        response = admin_client.delete("/api/v2/playlists/999999")
        assert response.status_code == 404

    def test_delete_playlist_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        response = client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 403

    def test_delete_playlist_double_delete_returns_404(self, admin_client):
        """DELETE already deleted playlist should return 404."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        response = admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 404

    def test_delete_playlist_returns_empty_body(self, admin_client):
        """DELETE should return empty response body."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        response = admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.content == b""

    def test_delete_one_playlist_others_remain(self, admin_client):
        """DELETE one playlist should leave others."""
        user = baker.make(User, username="testplaylist_user")
        playlist1 = baker.make(Playlist, name="Playlist 1", owner=user)
        playlist2 = baker.make(Playlist, name="Playlist 2", owner=user)
        playlist3 = baker.make(Playlist, name="Playlist 3", owner=user)

        admin_client.delete(f"/api/v2/playlists/{playlist2.id}")

        assert Playlist.objects.filter(id=playlist1.id).exists()
        assert not Playlist.objects.filter(id=playlist2.id).exists()
        assert Playlist.objects.filter(id=playlist3.id).exists()

    def test_delete_playlist_with_description(self, admin_client):
        """DELETE playlist with description should succeed."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            description="Test description",
            owner=user,
        )

        response = admin_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 204

    def test_delete_playlist_id_zero_returns_404(self, admin_client):
        """DELETE with id=0 should return 404."""
        response = admin_client.delete("/api/v2/playlists/0")
        assert response.status_code == 404

    def test_delete_playlist_negative_id_returns_404(self, admin_client):
        """DELETE with negative id should return 404."""
        response = admin_client.delete("/api/v2/playlists/-1")
        assert response.status_code == 404

    def test_delete_playlist_sql_injection_attempt(self, admin_client):
        """DELETE with SQL injection in id should be handled safely."""
        response = admin_client.delete("/api/v2/playlists/1 OR 1=1")
        assert response.status_code == 404
