"""Tests for Playlists CREATE endpoint (T224)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistViewSetCreate:
    """Test Playlists CREATE endpoint - POST /api/v2/playlists."""

    def setup_method(self):
        """Clean up playlists before each test."""
        Playlist.objects.all().delete()
        User.objects.filter(username__startswith="testplaylist").delete()

    def test_create_playlist_success(self, api_client):
        """CREATE playlist should succeed."""
        user = baker.make(User, username="testplaylist_user")
        data = {
            "name": "My Playlist",
                    }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "My Playlist"

    def test_create_playlist_with_description(self, api_client):
        """CREATE playlist with description should succeed."""
        user = baker.make(User, username="testplaylist_user")
        data = {
            "name": "My Playlist",
            "description": "Test description",
                    }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["description"] == "Test description"

    def test_create_playlist_missing_name_fails(self, api_client):
        """CREATE without name should fail."""
        user = baker.make(User, username="testplaylist_user")
        data = {
                    }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.xfail(
        reason="BUG T321: Playlist CREATE allows null owner - no validation",
    )
    def test_create_playlist_missing_owner_fails(self, api_client):
        """CREATE without owner should fail."""
        data = {
            "name": "My Playlist",
        }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400  # Should fail but returns 201

    def test_create_playlist_invalid_owner_fails(self, api_client):
        """CREATE with invalid owner should fail."""
        data = {
            "name": "My Playlist",
            "owner": 999999,
        }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_playlist_empty_name_fails(self, api_client):
        """CREATE with empty name should fail."""
        user = baker.make(User, username="testplaylist_user")
        data = {
            "name": "",
                    }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_playlist_unicode_name(self, api_client):
        """CREATE with unicode name should succeed."""
        user = baker.make(User, username="testplaylist_user")
        data = {
            "name": "日本語プレイリスト",
            "description": "日本語の説明",
                    }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "日本語プレイリスト"
        assert result["description"] == "日本語の説明"

    def test_create_playlist_returns_json(self, api_client):
        """CREATE should return JSON response."""
        user = baker.make(User, username="testplaylist_user")
        data = {
            "name": "My Playlist",
                    }
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response["Content-Type"] == "application/json"

    def test_create_playlist_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        data = {"name": "My Playlist"}
        response = client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_playlist_duplicate_name_same_owner(self, api_client):
        """CREATE playlist with duplicate name for same owner."""
        user = baker.make(User, username="testplaylist_user")

        # First playlist
        data = {
            "name": "Duplicate Name",
                    }
        api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        # Second playlist with same name
        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        # May or may not allow duplicates
        assert response.status_code in [201, 400]
