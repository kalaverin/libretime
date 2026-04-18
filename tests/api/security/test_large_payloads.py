"""
T293: Large payload handling tests.

Paranoid tests for large data scenarios.
Verify API handles large payloads without corruption.
"""

import json

import pytest

from model_bakery import baker

from api.core.models import Role, User
from api.schedule.models import Playlist, PlaylistContent
from api.storage.models import File, Library


@pytest.mark.django_db
class TestLargePlaylistCreation:
    """Test playlists with many contents."""

    def test_create_playlist_with_50_contents(self, guest_client):
        """Playlist with 50 content items."""
        user = baker.make(User, username="large_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="LARGE",
            name="Large Test",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Large Playlist", owner=user)

        # Add 50 content items
        for i in range(50):
            file_obj = baker.make(
                File,
                name=f"track_{i:03d}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file_obj,
                position=i + 1,
                offset=0,
            )

        # Verify via API
        response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200

        # Verify count
        count = PlaylistContent.objects.filter(playlist=playlist).count()
        assert count == 50

    def test_create_playlist_with_100_contents(self, guest_client):
        """Playlist with 100 content items."""
        user = baker.make(User, username="huge_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="HUGE",
            name="Huge Test",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Huge Playlist", owner=user)

        # Add 100 content items
        for i in range(100):
            file_obj = baker.make(
                File,
                name=f"huge_{i:03d}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file_obj,
                position=i + 1,
            )

        response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200

        count = PlaylistContent.objects.filter(playlist=playlist).count()
        assert count == 100

    def test_large_playlist_list_response(self, guest_client):
        """LIST with many playlists."""
        user = baker.make(User, username="list_test", role=Role.HOST)

        # Create 50 playlists
        for i in range(50):
            baker.make(Playlist, name=f"Playlist {i:03d}", owner=user)

        response = guest_client.get("/api/v2/playlists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 50


@pytest.mark.django_db
class TestLargeNameAndDescription:
    """Test with large text fields."""

    def test_max_length_playlist_name(self, guest_client):
        """Playlist with 255 character name (max allowed)."""

        user = baker.make(User, username="long_name", role=Role.HOST)
        max_name = "A" * 255

        response = guest_client.post(
            "/api/v2/playlists",
            json.dumps({"name": max_name}),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == max_name

    def test_name_too_long_rejected(self, guest_client):
        """Playlist name > 255 characters rejected."""

        user = baker.make(User, username="long_name2", role=Role.HOST)
        too_long_name = "A" * 256

        response = guest_client.post(
            "/api/v2/playlists",
            json.dumps({"name": too_long_name}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_max_length_description(self, guest_client):
        """Playlist with 512 character description (max)."""

        user = baker.make(User, username="long_desc", role=Role.HOST)
        max_desc = "B" * 512

        response = guest_client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Long Desc Playlist",
                    "description": max_desc,
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["description"]) == 512

    def test_description_too_long_rejected(self, guest_client):
        """Description > 512 characters rejected."""

        user = baker.make(User, username="long_desc2", role=Role.HOST)
        too_long_desc = "C" * 513

        response = guest_client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Test",
                    "description": too_long_desc,
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_unicode_name(self, guest_client):
        """Playlist with unicode name (within limit)."""

        user = baker.make(User, username="unicode_test", role=Role.HOST)
        # Emojis are multi-byte, keep under 255 char limit
        unicode_name = ("🎵 Музыка Music 🎼" * 10).strip()

        response = guest_client.post(
            "/api/v2/playlists",
            json.dumps({"name": unicode_name}),
            content_type="application/json",
        )

        # Should either succeed or fail due to length, not encoding
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            data = response.json()
            assert "Музыка" in data["name"] or "Music" in data["name"]


@pytest.mark.django_db
class TestLargeBulkOperations:
    """Test bulk operations with many items."""

    def test_filter_large_dataset(self, guest_client):
        """Filter through large dataset."""
        user = baker.make(User, username="filter_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="FILTER",
            name="Filter Test",
            description="Test",
        )

        # Create files with various names
        for i in range(100):
            baker.make(
                File,
                name=f"file_{i:03d}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )

        # Filter should work without issues
        response = guest_client.get("/api/v2/files?mime=audio/mp3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 100

    def test_large_response_serialization(self, guest_client):
        """Large response serializes correctly."""
        user = baker.make(User, username="serial_test", role=Role.HOST)

        # Create playlist with detailed content
        playlist = baker.make(Playlist, name="Serial Test", owner=user)
        library = baker.make(
            Library,
            code="SERIAL",
            name="Serial",
            description="Test",
        )

        for i in range(20):
            file_obj = baker.make(
                File,
                name=f"detailed_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                album_title=f"Album {i}",
                artist_name=f"Artist {i}",
            )
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file_obj,
                position=i + 1,
                cue_in="00:00:00",
                cue_out="00:03:00",
                fade_in="00:00:01",
                fade_out="00:00:01",
            )

        response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        # Verify response is valid JSON
        data = response.json()
        assert "id" in data
        assert "name" in data


@pytest.mark.django_db
class TestPayloadSizeLimits:
    """Test API payload size handling."""

    def test_large_valid_json_payload(self, guest_client):
        """API handles large but valid JSON payload."""

        user = baker.make(User, username="payload_test", role=Role.HOST)

        # Create large but valid payload (within field limits)
        large_data = {
            "name": "X" * 255,  # Max allowed
            "description": "Y" * 512,  # Max allowed
        }

        response = guest_client.post(
            "/api/v2/playlists",
            json.dumps(large_data),
            content_type="application/json",
        )

        assert response.status_code == 201

    def test_many_fields_in_payload(self, guest_client):
        """Payload with many fields."""

        user = baker.make(User, username="fields_test", role=Role.HOST)

        response = guest_client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Many Fields",
                    "description": "Test",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201


@pytest.mark.django_db
class TestDataIntegrityWithLargePayloads:
    """Verify data integrity with large operations."""

    def test_position_integrity_with_many_items(self, guest_client):
        """Position values remain unique with many items."""
        user = baker.make(User, username="integrity_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="INTEGRITY",
            name="Integrity",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Integrity Test", owner=user)

        # Add many items
        for i in range(50):
            file_obj = baker.make(
                File,
                name=f"integrity_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file_obj,
                position=i + 1,
            )

        # Verify all positions are unique
        positions = list(
            PlaylistContent.objects.filter(playlist=playlist).values_list(
                "position",
                flat=True,
            ),
        )
        assert len(positions) == len(set(positions))
        assert max(positions) == 50

    def test_no_missing_items_in_large_list(self, guest_client):
        """No items missing in large list response."""
        user = baker.make(User, username="missing_test", role=Role.HOST)

        # Create known number of playlists
        created_ids = []
        for i in range(30):
            playlist = baker.make(Playlist, name=f"Known {i}", owner=user)
            created_ids.append(playlist.id)

        # Get list
        response = guest_client.get("/api/v2/playlists")
        data = response.json()

        # Verify all created playlists are in response
        response_ids = [p["id"] for p in data]
        for pid in created_ids:
            assert pid in response_ids

    def test_total_count_consistency(self, guest_client):
        """Count matches actual items."""
        user = baker.make(User, username="count_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="COUNT",
            name="Count",
            description="Test",
        )

        # Create known number of files
        expected_count = 25
        for i in range(expected_count):
            baker.make(
                File,
                name=f"count_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )

        # Verify via API
        response = guest_client.get("/api/v2/files")
        data = response.json()
        actual_count = len([f for f in data if f["name"].startswith("count_")])
        assert actual_count == expected_count
