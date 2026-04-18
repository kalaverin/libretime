"""Tests for File RETRIEVE endpoint (T189)."""

import uuid

import pytest

from model_bakery import baker

from api.storage.models import File, Library


@pytest.mark.django_db(transaction=True)
class TestFileViewSetRetrieve:
    """Test Files RETRIEVE endpoint - GET /api/v2/files/{id}."""

    def test_retrieve_file_success(self, admin_client):
        """RETRIEVE existing file should return 200 with full data."""
        file = baker.make(
            File,
            name="Test Track",
            mime="audio/mpeg",
            size=10_000_000,
            accessed=0,
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        assert response.status_code == 200
        assert response.json()["id"] == file.id
        assert response.json()["name"] == "Test Track"

    def test_retrieve_file_returns_json(self, admin_client):
        """RETRIEVE should return JSON response."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        assert response["Content-Type"] == "application/json"

    def test_retrieve_file_response_structure(self, admin_client):
        """RETRIEVE response should have all model fields."""
        file = baker.make(
            File,
            name="Full Track",
            mime="audio/flac",
            size=50_000_000,
            accessed=1,
            artist_name="Artist",
            track_title="Title",
            album_title="Album",
            genre="Rock",
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        data = response.json()

        # Core fields
        assert "id" in data
        assert "name" in data
        assert "filepath" in data
        assert "mime" in data
        assert "size" in data
        assert "md5" in data

        # Status fields
        assert "import_status" in data
        assert "exists" in data
        assert "hidden" in data
        assert "scheduled" in data

        # Audio fields
        assert "bit_rate" in data
        assert "sample_rate" in data
        assert "format" in data
        assert "channels" in data
        assert "length" in data
        assert "replay_gain" in data
        assert "cue_in" in data
        assert "cue_out" in data

        # Metadata fields
        assert "artist_name" in data
        assert "track_title" in data
        assert "album_title" in data
        assert "genre" in data
        assert "mood" in data
        assert "date" in data
        assert "track_number" in data

        # Relations
        assert "library" in data
        assert "owner" in data
        assert "edited_by" in data

        # Timestamps
        assert "created_at" in data
        assert "updated_at" in data
        assert "last_played_at" in data

    def test_retrieve_file_all_field_values(self, admin_client):
        """RETRIEVE should return correct values for all fields."""
        file = baker.make(
            File,
            name="Specific Track",
            mime="audio/ogg",
            size=5_000_000,
            accessed=42,
            artist_name="Specific Artist",
            track_title="Specific Title",
            genre="Jazz",
            import_status=File.ImportStatus.SUCCESS,
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        data = response.json()

        assert data["name"] == "Specific Track"
        assert data["mime"] == "audio/ogg"
        assert data["size"] == 5_000_000
        assert data["accessed"] == 42
        assert data["artist_name"] == "Specific Artist"
        assert data["track_title"] == "Specific Title"
        assert data["genre"] == "Jazz"
        assert data["import_status"] == File.ImportStatus.SUCCESS

    def test_retrieve_file_with_library(self, admin_client):
        """RETRIEVE should include library relation."""
        library = baker.make(
            Library,
            code=f"music_{uuid.uuid4().hex[:8]}",
            name="Music",
            description="Desc",
        )
        file = baker.make(
            File,
            name="Library Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            library=library,
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        data = response.json()

        assert data["library"] == library.id

    def test_retrieve_file_not_found(self, admin_client):
        """RETRIEVE non-existent file should return 404."""
        response = admin_client.get("/api/v2/files/999999")
        assert response.status_code == 404

    def test_retrieve_file_invalid_id_format(self, admin_client):
        """RETRIEVE with invalid id format should return 404."""
        response = admin_client.get("/api/v2/files/invalid")
        assert response.status_code == 404

    def test_retrieve_file_negative_id(self, admin_client):
        """RETRIEVE with negative id should return 404."""
        response = admin_client.get("/api/v2/files/-1")
        assert response.status_code == 404

    def test_retrieve_file_zero_id(self, admin_client):
        """RETRIEVE with id=0 should return 404."""
        response = admin_client.get("/api/v2/files/0")
        assert response.status_code == 404

    def test_retrieve_file_no_auth_returns_403(self, client):
        """RETRIEVE should return 403 without authentication."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = client.get(f"/api/v2/files/{file.id}")
        assert response.status_code == 403

    def test_retrieve_file_post_not_allowed(self, admin_client):
        """POST on detail should not be allowed (returns 405)."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = admin_client.post(
            f"/api/v2/files/{file.id}",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_retrieve_file_data_types(self, admin_client):
        """RETRIEVE should return correct data types."""
        file = baker.make(
            File,
            name="Type Test",
            mime="audio/mpeg",
            size=10_000_000,
            accessed=100,
            track_number=5,
            bit_rate=320,
            import_status=File.ImportStatus.PENDING,
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        data = response.json()

        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["mime"], str)
        assert isinstance(data["size"], int)
        assert isinstance(data["accessed"], int)
        assert isinstance(data["track_number"], (int, type(None)))
        assert isinstance(data["bit_rate"], (int, type(None)))
        assert isinstance(data["import_status"], int)

    def test_retrieve_file_nullable_fields(self, admin_client):
        """RETRIEVE should handle nullable fields correctly."""
        file = baker.make(
            File,
            name="Nullable Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath=None,
            md5=None,
            artist_name=None,
            genre=None,
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        data = response.json()

        assert data["filepath"] is None
        assert data["md5"] is None
        assert data["artist_name"] is None
        assert data["genre"] is None

    def test_retrieve_file_import_status_values(self, admin_client):
        """RETRIEVE should return correct import_status for all values."""
        for status_val, status_name in File.ImportStatus.choices:
            file = baker.make(
                File,
                name=f"Track {status_name}",
                mime="audio/mpeg",
                size=1000,
                accessed=0,
                import_status=status_val,
            )
            response = admin_client.get(f"/api/v2/files/{file.id}")
            data = response.json()
            assert (
                data["import_status"] == status_val
            ), f"Failed for {status_name}"

    def test_retrieve_file_unicode_metadata(self, admin_client):
        """RETRIEVE should handle unicode metadata correctly."""
        file = baker.make(
            File,
            name="日本語トラック",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            artist_name="アーティスト",
            track_title="タイトル",
            genre="J-Pop",
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        data = response.json()

        assert data["name"] == "日本語トラック"
        assert data["artist_name"] == "アーティスト"
        assert data["track_title"] == "タイトル"

    def test_retrieve_file_long_strings(self, admin_client):
        """RETRIEVE should handle long string values."""
        # name max_length=255, comment is TextField (no limit)
        long_name = "A" * 255
        long_comment = "B" * 1000
        file = baker.make(
            File,
            name=long_name,
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            comment=long_comment,
        )
        response = admin_client.get(f"/api/v2/files/{file.id}")
        data = response.json()

        assert data["name"] == long_name
        assert data["comment"] == long_comment
