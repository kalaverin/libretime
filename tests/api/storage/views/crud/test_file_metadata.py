"""
T294: File metadata extraction tests.

Paranoid tests for file metadata fields.
Verify all metadata fields are correctly stored and retrieved.
"""

from datetime import timedelta
from decimal import Decimal

import pytest

from model_bakery import baker

from api.core.models import User
from api.storage.models import File, Library


@pytest.mark.django_db
class TestFileMetadataFields:
    """Test file metadata field storage and retrieval."""

    def test_audio_metadata_storage(self, admin_client):
        """Audio metadata (bit_rate, sample_rate, channels) stored correctly."""
        user = baker.make(User, username="metadata_test")
        library = baker.make(
            Library,
            code="META",
            name="Meta Test",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="high_quality.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            bit_rate=320000,
            sample_rate=48000,
            channels=2,
            length=timedelta(minutes=3, seconds=30),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["bit_rate"] == 320000
        assert data["sample_rate"] == 48000
        assert data["channels"] == 2
        assert data["length"] == "00:03:30"

    def test_replay_gain_metadata(self, admin_client):
        """Replay gain metadata stored correctly."""
        user = baker.make(User, username="replay_test")
        library = baker.make(
            Library,
            code="REPLAY",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="normalized.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-2.50"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["replay_gain"]) == Decimal("-2.50")

    def test_musical_metadata(self, admin_client):
        """Musical metadata (bpm, mood) stored correctly."""
        user = baker.make(User, username="music_test")
        library = baker.make(
            Library,
            code="MUSIC",
            name="Music",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="dance_track.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            bpm=128,
            mood="Energetic",
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["bpm"] == 128
        assert data["mood"] == "Energetic"

    def test_id3_metadata(self, admin_client):
        """ID3 tags stored correctly."""
        user = baker.make(User, username="id3_test")
        library = baker.make(
            Library,
            code="ID3",
            name="ID3",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="tagged_song.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            track_title="Test Title",
            artist_name="Test Artist",
            album_title="Test Album",
            track_number=5,
            genre="Rock",
            date="2024",
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["track_title"] == "Test Title"
        assert data["artist_name"] == "Test Artist"
        assert data["album_title"] == "Test Album"
        assert data["track_number"] == 5
        assert data["genre"] == "Rock"
        assert data["date"] == "2024"

    def test_full_metadata_retrieval(self, admin_client):
        """All metadata fields retrieved in single request."""
        user = baker.make(User, username="full_test")
        library = baker.make(
            Library,
            code="FULL",
            name="Full",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="complete.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            # Audio
            bit_rate=256000,
            sample_rate=44100,
            channels=2,
            length=timedelta(minutes=4),
            # Processing
            replay_gain=Decimal("-1.20"),
            # Musical
            bpm=120,
            mood="Happy",
            # ID3
            track_title="Complete Song",
            artist_name="Complete Artist",
            album_title="Complete Album",
            track_number=1,
            genre="Pop",
            date="2024",
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        # Verify all fields present
        assert data["bit_rate"] == 256000
        assert data["sample_rate"] == 44100
        assert data["channels"] == 2
        assert data["length"] == "00:04:00"
        assert Decimal(data["replay_gain"]) == Decimal("-1.20")
        assert data["bpm"] == 120
        assert data["mood"] == "Happy"
        assert data["track_title"] == "Complete Song"
        assert data["artist_name"] == "Complete Artist"
        assert data["album_title"] == "Complete Album"
        assert data["track_number"] == 1
        assert data["genre"] == "Pop"
        assert data["date"] == "2024"


@pytest.mark.django_db
class TestFileMetadataUpdate:
    """Test metadata field updates."""

    def test_update_audio_metadata(self, admin_client):
        """Update audio metadata fields."""
        import json

        user = baker.make(User, username="update_test")
        library = baker.make(
            Library,
            code="UPDATE",
            name="Update",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="update_me.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            bit_rate=128000,
        )

        response = admin_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"bit_rate": 320000}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bit_rate"] == 320000

    def test_update_id3_metadata(self, admin_client):
        """Update ID3 metadata fields."""
        import json

        user = baker.make(User, username="id3_update")
        library = baker.make(
            Library,
            code="ID3UPD",
            name="ID3 Update",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="retag.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            track_title="Old Title",
            artist_name="Old Artist",
        )

        response = admin_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps(
                {
                    "track_title": "New Title",
                    "artist_name": "New Artist",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["track_title"] == "New Title"
        assert data["artist_name"] == "New Artist"

    def test_clear_metadata_field(self, admin_client):
        """Clear metadata field by setting to null."""
        import json

        user = baker.make(User, username="clear_test")
        library = baker.make(
            Library,
            code="CLEAR",
            name="Clear",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="clear_me.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            bpm=120,
        )

        response = admin_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"bpm": None}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bpm"] is None


@pytest.mark.django_db
class TestMetadataInListView:
    """Test metadata in list responses."""

    def test_list_includes_key_metadata(self, admin_client):
        """LIST includes key metadata fields."""
        user = baker.make(User, username="list_meta")
        library = baker.make(
            Library,
            code="LIST",
            name="List",
            description="Test",
        )

        baker.make(
            File,
            name="listed.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            track_title="Listed Song",
            artist_name="Listed Artist",
            length=timedelta(minutes=3),
        )

        response = admin_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        # Check key fields present
        assert "track_title" in data[0]
        assert "artist_name" in data[0]
        assert "length" in data[0]

    def test_list_metadata_consistency(self, admin_client):
        """LIST and RETRIEVE show same metadata."""
        user = baker.make(User, username="consistency")
        library = baker.make(
            Library,
            code="CONSIST",
            name="Consistent",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="consistent.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            track_title="Same Title",
            artist_name="Same Artist",
        )

        # Get from list
        list_response = admin_client.get("/api/v2/files")
        list_data = next(
            f for f in list_response.json() if f["id"] == file_obj.id
        )

        # Get from retrieve
        retrieve_response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        retrieve_data = retrieve_response.json()

        # Metadata should match
        assert list_data["track_title"] == retrieve_data["track_title"]
        assert list_data["artist_name"] == retrieve_data["artist_name"]


@pytest.mark.django_db
class TestMetadataEdgeCases:
    """Test metadata edge cases."""

    def test_null_metadata_fields(self, admin_client):
        """File with null metadata fields."""
        user = baker.make(User, username="null_test")
        library = baker.make(
            Library,
            code="NULL",
            name="Null",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="no_meta.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            track_title=None,
            artist_name=None,
            bit_rate=None,
            bpm=None,
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["track_title"] is None
        assert data["artist_name"] is None
        assert data["bit_rate"] is None
        assert data["bpm"] is None

    def test_unicode_metadata(self, admin_client):
        """Metadata with unicode characters."""
        user = baker.make(User, username="unicode_meta")
        library = baker.make(
            Library,
            code="UNI",
            name="Unicode",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="unicode.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            track_title="日本語タイトル 🎵",
            artist_name="Артист 🎤",
            album_title="Álbum Éspecial",
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert "日本語" in data["track_title"]
        assert "Артист" in data["artist_name"]
        assert "Álbum" in data["album_title"]

    def test_zero_values(self, admin_client):
        """Metadata with zero values."""
        user = baker.make(User, username="zero_test")
        library = baker.make(
            Library,
            code="ZERO",
            name="Zero",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="zero.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            track_number=0,
            bpm=0,
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        # Zero should be preserved
        assert data["track_number"] == 0
        assert data["bpm"] == 0

    def test_negative_replay_gain(self, admin_client):
        """Negative replay gain values."""
        user = baker.make(User, username="negative_test")
        library = baker.make(
            Library,
            code="NEG",
            name="Negative",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="quiet.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-12.50"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["replay_gain"]) == Decimal("-12.50")
