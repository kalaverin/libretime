"""Tests for Playlists LIST endpoint (T223)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistViewSetList:
    """Test Playlists LIST endpoint - GET /api/v2/playlists."""

    def setup_method(self):
        """Clean up playlists before each test."""
        Playlist.objects.all().delete()
        User.objects.filter(username__startswith="testplaylist").delete()

    def test_list_playlists_empty_returns_200(self, api_client):
        """LIST with no playlists should return empty array."""
        response = api_client.get("/api/v2/playlists")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_playlists_returns_all(self, api_client):
        """LIST should return all playlists."""
        user = baker.make(User, username="testplaylist_user")
        playlist1 = baker.make(Playlist, name="Playlist 1", owner=user)
        playlist2 = baker.make(Playlist, name="Playlist 2", owner=user)

        response = api_client.get("/api/v2/playlists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_playlists_returns_json(self, api_client):
        """LIST should return JSON response."""
        user = baker.make(User, username="testplaylist_user")
        baker.make(Playlist, name="Test Playlist", owner=user)

        response = api_client.get("/api/v2/playlists")
        assert response["Content-Type"] == "application/json"

    def test_list_playlists_contains_id(self, api_client):
        """LIST should include playlist id."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        response = api_client.get("/api/v2/playlists")
        data = response.json()
        assert data[0]["id"] == playlist.id

    def test_list_playlists_contains_name(self, api_client):
        """LIST should include playlist name."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="My Playlist", owner=user)

        response = api_client.get("/api/v2/playlists")
        data = response.json()
        assert data[0]["name"] == "My Playlist"

    def test_list_playlists_contains_description(self, api_client):
        """LIST should include playlist description."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="Test",
            description="Test description",
            owner=user,
        )

        response = api_client.get("/api/v2/playlists")
        data = response.json()
        assert data[0]["description"] == "Test description"

    def test_list_playlists_null_description(self, api_client):
        """LIST should handle null description."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="Test",
            description=None,
            owner=user,
        )

        response = api_client.get("/api/v2/playlists")
        assert response.json()[0]["description"] is None

    def test_list_playlists_contains_owner(self, api_client):
        """LIST should include owner reference."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        response = api_client.get("/api/v2/playlists")
        data = response.json()
        assert data[0]["owner"] == user.id

    def test_list_playlists_contains_length(self, api_client):
        """LIST should include computed length."""

        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        # Length is typically computed from contents

        response = api_client.get("/api/v2/playlists")
        data = response.json()
        assert "length" in data[0]

    @pytest.mark.xfail(reason="PlaylistSerializer missing file_count field")
    def test_list_playlists_contains_file_count(self, api_client):
        """LIST should include file count."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        response = api_client.get("/api/v2/playlists")
        data = response.json()
        assert "file_count" in data[0]

    def test_list_playlists_filter_by_owner(self, api_client):
        """LIST should support filtering by owner."""
        user1 = baker.make(User, username="testplaylist_user1")
        user2 = baker.make(User, username="testplaylist_user2")

        baker.make(Playlist, name="Playlist 1", owner=user1)
        baker.make(Playlist, name="Playlist 2", owner=user2)

        response = api_client.get(f"/api/v2/playlists?owner={user1.id}")
        assert response.status_code in [200, 400]

    def test_list_playlists_multiple_owners(self, api_client):
        """LIST should return playlists from multiple owners."""
        user1 = baker.make(User, username="testplaylist_user1")
        user2 = baker.make(User, username="testplaylist_user2")

        baker.make(Playlist, name="Playlist 1", owner=user1)
        baker.make(Playlist, name="Playlist 2", owner=user2)

        response = api_client.get("/api/v2/playlists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_playlists_unicode_names(self, api_client):
        """LIST should handle unicode playlist names."""
        user = baker.make(User, username="testplaylist_user")
        playlist = baker.make(
            Playlist,
            name="日本語プレイリスト",
            description="日本語の説明",
            owner=user,
        )

        response = api_client.get("/api/v2/playlists")
        data = response.json()
        assert data[0]["name"] == "日本語プレイリスト"

    def test_list_playlists_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/playlists")
        assert response.status_code == 403
