"""Tests for File LIST endpoint (T186)."""

import uuid

import pytest

from model_bakery import baker

from api.storage.models import File, Library


@pytest.mark.django_db(transaction=True)
class TestFileViewSetList:
    """Test Files LIST endpoint - GET /api/v2/files."""

    def setup_method(self):
        """Clean up files before each test."""
        File.objects.all().delete()

    def test_list_files_endpoint_available(self, admin_client):
        """LIST endpoint should be accessible with API key."""
        response = admin_client.get("/api/v2/files")
        assert response.status_code == 200

    def test_list_returns_json(self, admin_client):
        """LIST should return JSON response."""
        response = admin_client.get("/api/v2/files")
        assert response["Content-Type"] == "application/json"

    def test_list_empty_when_no_files(self, admin_client):
        """LIST should return empty list when no files exist."""
        response = admin_client.get("/api/v2/files")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_all_files(self, admin_client):
        """LIST should return all existing files."""
        file1 = baker.make(File, name="Track 1", mime="audio/mpeg")
        file2 = baker.make(File, name="Track 2", mime="audio/mpeg")
        file3 = baker.make(File, name="Track 3", mime="audio/mpeg")

        response = admin_client.get("/api/v2/files")
        data = response.json()
        assert len(data) == 3
        ids = {item["id"] for item in data}
        assert ids == {file1.id, file2.id, file3.id}

    def test_list_response_has_all_fields(self, admin_client):
        """LIST response should include all model fields."""
        file = baker.make(
            File,
            name="Test Track",
            mime="audio/mpeg",
            size=10_000_000,
            genre="Rock",
            artist_name="Test Artist",
            track_title="Test Title",
        )

        response = admin_client.get("/api/v2/files")
        data = response.json()
        # Find our file in the list
        file_data = next(
            (item for item in data if item["id"] == file.id),
            None,
        )
        assert file_data is not None

        # Core fields
        assert "id" in file_data
        assert "name" in file_data
        assert "filepath" in file_data
        assert "mime" in file_data
        assert "size" in file_data
        assert "md5" in file_data

        # Status fields
        assert "import_status" in file_data
        assert "exists" in file_data
        assert "hidden" in file_data
        assert "scheduled" in file_data
        assert "accessed" in file_data

        # Audio fields
        assert "bit_rate" in file_data
        assert "sample_rate" in file_data
        assert "format" in file_data
        assert "channels" in file_data
        assert "length" in file_data
        assert "replay_gain" in file_data
        assert "cue_in" in file_data
        assert "cue_out" in file_data

        # Metadata fields
        assert "artist_name" in file_data
        assert "track_title" in file_data
        assert "album_title" in file_data
        assert "genre" in file_data
        assert "mood" in file_data
        assert "date" in file_data
        assert "track_number" in file_data
        assert "disc_number" in file_data
        assert "comment" in file_data
        assert "language" in file_data
        assert "label" in file_data
        assert "copyright" in file_data
        assert "composer" in file_data
        assert "conductor" in file_data

        # Relations
        assert "library" in file_data
        assert "owner" in file_data
        assert "edited_by" in file_data

        # Timestamps
        assert "created_at" in file_data
        assert "updated_at" in file_data
        assert "last_played_at" in file_data

    def test_list_field_types(self, admin_client):
        """LIST should return correct data types for fields."""
        file = baker.make(
            File,
            name="Test Track",
            filepath="/audio/test.mp3",
            mime="audio/mpeg",
            size=10_000_000,
            md5="abc123def456",
            genre="Rock",
            track_number=5,
            import_status=File.ImportStatus.SUCCESS,
        )

        response = admin_client.get("/api/v2/files")
        data = next(
            (item for item in response.json() if item["id"] == file.id),
            None,
        )
        assert data is not None

        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["filepath"], str)
        assert isinstance(data["mime"], str)
        assert isinstance(data["size"], int)
        assert isinstance(data["md5"], (str, type(None)))
        assert isinstance(data["genre"], (str, type(None)))
        assert isinstance(data["track_number"], (int, type(None)))
        assert isinstance(data["import_status"], int)

    def test_list_import_status_values(self, admin_client):
        """LIST should return correct import_status values."""
        success_file = baker.make(
            File,
            import_status=File.ImportStatus.SUCCESS,
        )
        pending_file = baker.make(
            File,
            import_status=File.ImportStatus.PENDING,
        )
        failed_file = baker.make(File, import_status=File.ImportStatus.FAILED)

        response = admin_client.get("/api/v2/files")
        data = response.json()

        statuses = {item["import_status"] for item in data}
        assert statuses == {0, 1, 2}  # SUCCESS=0, PENDING=1, FAILED=2

    def test_list_with_library_relation(self, admin_client):
        """LIST should include library data when file has library."""
        library = baker.make(
            Library,
            code=f"music_{uuid.uuid4().hex[:8]}",
            name="Music",
            description="Music library",
        )
        file = baker.make(
            File,
            library=library,
            name="Track",
            mime="audio/mpeg",
        )

        response = admin_client.get("/api/v2/files")
        data = next(
            (item for item in response.json() if item["id"] == file.id),
            None,
        )
        assert data is not None

        # Library should be serialized as ID
        assert data["library"] == library.id

    def test_list_with_owner_relation(self, admin_client, regular_user):
        """LIST should include owner data when file has owner."""
        file = baker.make(
            File,
            owner=regular_user,
            name="Track",
            mime="audio/mpeg",
        )

        response = admin_client.get("/api/v2/files")
        data = response.json()[0]

        # Owner field should be serialized
        assert "owner" in data

    def test_list_no_auth_returns_403(self, client):
        """LIST should return 403 without authentication."""
        response = client.get("/api/v2/files")
        assert response.status_code == 403

    def test_list_put_not_allowed(self, admin_client):
        """PUT should not be allowed on LIST endpoint."""
        response = admin_client.put(
            "/api/v2/files",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_list_patch_not_allowed(self, admin_client):
        """PATCH should not be allowed on LIST endpoint."""
        response = admin_client.patch(
            "/api/v2/files",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_list_delete_not_allowed(self, admin_client):
        """DELETE should not be allowed on LIST endpoint."""
        response = admin_client.delete("/api/v2/files")
        assert response.status_code == 405

    def test_list_pagination_not_enabled(self, admin_client):
        """LIST should return all results without pagination."""
        # Get initial count
        initial_response = admin_client.get("/api/v2/files")
        initial_count = len(initial_response.json())

        # Create many files
        for _ in range(5):
            baker.make(File)

        response = admin_client.get("/api/v2/files")
        data = response.json()

        # Should return all files directly, not paginated response
        assert isinstance(data, list)
        assert len(data) == initial_count + 5
        # Verify it's not a paginated response structure
        assert "results" not in data if isinstance(data, list) else True
