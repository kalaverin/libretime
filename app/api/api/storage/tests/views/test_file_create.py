"""Tests for File CREATE endpoint (T188)."""

import json

import pytest

from model_bakery import baker

from api.storage.models import File, Library


@pytest.mark.django_db(transaction=True)
class TestFileViewSetCreate:
    """Test Files CREATE endpoint - POST /api/v2/files."""

    def setup_method(self):
        """Clean up files before each test."""
        File.objects.all().delete()

    def get_minimal_file_data(self):
        """Return minimal valid data for creating a file."""
        return {
            "name": "Test Track",
            "mime": "audio/mpeg",
            "size": 10_000_000,
            "accessed": 0,
        }

    def test_create_file_endpoint_available(self, api_client):
        """CREATE endpoint should be accessible with API key."""
        data = self.get_minimal_file_data()
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_create_file_returns_json(self, api_client):
        """CREATE should return JSON response."""
        data = self.get_minimal_file_data()
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response["Content-Type"] == "application/json"

    def test_create_file_minimal_data(self, api_client):
        """CREATE with minimal data should succeed."""
        data = self.get_minimal_file_data()
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201

        result = response.json()
        assert result["name"] == "Test Track"
        assert result["mime"] == "audio/mpeg"
        assert result["size"] == 10_000_000
        assert result["accessed"] == 0

    def test_create_file_missing_required_name(self, api_client):
        """CREATE without name should fail with 400."""
        data = {
            "mime": "audio/mpeg",
            "size": 10_000_000,
            "accessed": 0,
        }
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "name" in response.json()

    def test_create_file_missing_required_mime(self, api_client):
        """CREATE without mime should fail with 400."""
        data = {
            "name": "Test Track",
            "size": 10_000_000,
            "accessed": 0,
        }
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "mime" in response.json()

    def test_create_file_missing_required_size(self, api_client):
        """CREATE without size should fail with 400."""
        data = {
            "name": "Test Track",
            "mime": "audio/mpeg",
            "accessed": 0,
        }
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "size" in response.json()

    def test_create_file_missing_required_accessed(self, api_client):
        """CREATE without accessed should fail with 400."""
        data = {
            "name": "Test Track",
            "mime": "audio/mpeg",
            "size": 10_000_000,
        }
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "accessed" in response.json()

    def test_create_file_with_metadata(self, api_client):
        """CREATE with full metadata should succeed."""
        data = {
            "name": "Full Metadata Track",
            "mime": "audio/flac",
            "size": 50_000_000,
            "accessed": 1,
            "filepath": "/audio/full_metadata.flac",
            "md5": "abcdef12345678901234567890123456",
            "artist_name": "Test Artist",
            "track_title": "Test Title",
            "album_title": "Test Album",
            "genre": "Rock",
            "year": "2024",
            "track_number": 5,
            "bit_rate": 1411,
            "sample_rate": 44100,
            "channels": 2,
            "import_status": File.ImportStatus.SUCCESS,
        }
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201

        result = response.json()
        assert result["artist_name"] == "Test Artist"
        assert result["track_title"] == "Test Title"
        assert result["album_title"] == "Test Album"
        assert result["genre"] == "Rock"
        assert result["track_number"] == 5
        assert result["bit_rate"] == 1411

    def test_create_file_with_library(self, api_client):
        """CREATE with library reference should succeed."""
        library = baker.make(
            Library,
            code="music",
            name="Music",
            description="Music lib",
        )
        data = {
            "name": "Library Track",
            "mime": "audio/mpeg",
            "size": 10_000_000,
            "accessed": 0,
            "library": library.id,
        }
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["library"] == library.id

    def test_create_file_default_import_status(self, api_client):
        """CREATE without import_status should use default (PENDING=1)."""
        data = self.get_minimal_file_data()
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        result = response.json()
        # Default is PENDING=1 per model
        assert result["import_status"] == File.ImportStatus.PENDING

    def test_create_file_explicit_import_status(self, api_client):
        """CREATE with explicit import_status should use provided value."""
        data = self.get_minimal_file_data()
        data["import_status"] = File.ImportStatus.SUCCESS
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        result = response.json()
        assert result["import_status"] == File.ImportStatus.SUCCESS

    def test_create_file_all_import_statuses(self, api_client):
        """CREATE with all import_status values should work."""
        for status_val, status_name in File.ImportStatus.choices:
            File.objects.all().delete()
            data = self.get_minimal_file_data()
            data["name"] = f"Track {status_name}"
            data["import_status"] = status_val
            response = api_client.post(
                "/api/v2/files",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code == 201, f"Failed for {status_name}"
            assert response.json()["import_status"] == status_val

    def test_create_file_no_auth_returns_403(self, client):
        """CREATE should return 403 without authentication."""
        data = self.get_minimal_file_data()
        response = client.post(
            "/api/v2/files",
            data,
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_file_generates_id(self, api_client):
        """CREATE should generate a unique id for the file."""
        data = self.get_minimal_file_data()
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        result = response.json()
        assert "id" in result
        assert isinstance(result["id"], int)
        assert result["id"] > 0

    def test_create_file_response_has_all_fields(self, api_client):
        """CREATE response should include all model fields."""
        data = self.get_minimal_file_data()
        data["artist_name"] = "Artist"
        data["track_title"] = "Title"
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        result = response.json()

        # Check key fields present
        assert "id" in result
        assert "name" in result
        assert "mime" in result
        assert "size" in result
        assert "accessed" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "import_status" in result
        assert "artist_name" in result
        assert "track_title" in result
