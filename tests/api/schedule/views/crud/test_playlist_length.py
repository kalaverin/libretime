"""
T287: Playlist length field tests.

Tests that playlist length field is exposed in API.
Note: length is a database field, not auto-computed from contents.
"""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist


@pytest.mark.django_db
class TestPlaylistLengthField:
    """Test playlist length field in API responses."""

    def test_playlist_retrieve_contains_length(self, admin_client):
        """RETRIEVE should include length field."""
        user = baker.make(User, username="length_test")
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=user,
            length=timedelta(minutes=5, seconds=30),
        )

        response = admin_client.get(f"/api/v2/playlists/{playlist.id}")

        assert response.status_code == 200
        data = response.json()
        assert "length" in data
        assert data["length"] == "00:05:30"

    def test_playlist_list_contains_length(self, admin_client):
        """LIST should include length field for each playlist."""
        user = baker.make(User, username="length_test")
        baker.make(
            Playlist,
            name="Test Playlist",
            owner=user,
            length=timedelta(hours=1, minutes=30),
        )

        response = admin_client.get("/api/v2/playlists")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "length" in data[0]
        assert data[0]["length"] == "01:30:00"

    def test_playlist_create_accepts_length(self, admin_client):
        """CREATE should accept length field."""
        import json

        user = baker.make(User, username="length_test")

        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "New Playlist",
                    "length": "00:45:00",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["length"] == "00:45:00"

    def test_playlist_update_accepts_length(self, admin_client):
        """UPDATE should accept length field."""
        import json

        user = baker.make(User, username="length_test")
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=user,
            length=timedelta(minutes=10),
        )

        response = admin_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(
                {
                    "length": "00:20:00",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["length"] == "00:20:00"

    def test_playlist_null_length(self, admin_client):
        """Playlist with null length should return null."""
        user = baker.make(User, username="length_test")
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=user,
            length=None,
        )

        response = admin_client.get(f"/api/v2/playlists/{playlist.id}")

        assert response.status_code == 200
        data = response.json()
        assert "length" in data
        assert data["length"] is None

    def test_playlist_length_zero(self, admin_client):
        """Playlist with zero length should return 00:00:00."""
        user = baker.make(User, username="length_test")
        playlist = baker.make(
            Playlist,
            name="Empty Playlist",
            owner=user,
            length=timedelta(0),
        )

        response = admin_client.get(f"/api/v2/playlists/{playlist.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["length"] == "00:00:00"
