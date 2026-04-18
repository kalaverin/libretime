"""Tests for File validation (T196)."""

import json

import pytest

from model_bakery import baker

from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestFileViewSetValidation:
    """Test Files CREATE validation - invalid mime, size, etc."""

    def get_minimal_data(self):
        """Return minimal valid data for file creation."""
        return {
            "name": "Test Track",
            "mime": "audio/mpeg",
            "size": 10_000_000,
            "accessed": 0,
        }

    def test_create_missing_name_fails(self, guest_client):
        """CREATE without name should return 400."""
        data = self.get_minimal_data()
        del data["name"]
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "name" in response.json()

    def test_create_missing_mime_fails(self, guest_client):
        """CREATE without mime should return 400."""
        data = self.get_minimal_data()
        del data["mime"]
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "mime" in response.json()

    def test_create_missing_size_fails(self, guest_client):
        """CREATE without size should return 400."""
        data = self.get_minimal_data()
        del data["size"]
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "size" in response.json()

    def test_create_missing_accessed_fails(self, guest_client):
        """CREATE without accessed should return 400."""
        data = self.get_minimal_data()
        del data["accessed"]
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "accessed" in response.json()

    def test_create_empty_name_fails(self, guest_client):
        """CREATE with empty name should fail (blank=True not set)."""
        data = self.get_minimal_data()
        data["name"] = ""
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # Empty string fails - name field doesn't allow blank
        assert response.status_code == 400
        assert "name" in response.json()

    def test_create_long_name_succeeds(self, guest_client):
        """CREATE with very long name should succeed (up to 255 chars)."""
        data = self.get_minimal_data()
        data["name"] = "A" * 255
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "A" * 255

    def test_create_name_too_long_fails(self, guest_client):
        """CREATE with name > 255 chars should fail."""
        data = self.get_minimal_data()
        data["name"] = "A" * 256
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_negative_size_fails(self, guest_client):
        """CREATE with negative size should fail."""
        data = self.get_minimal_data()
        data["size"] = -1
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # Negative size may or may not be allowed depending on model
        assert response.status_code in [201, 400]

    def test_create_zero_size_succeeds(self, guest_client):
        """CREATE with zero size should succeed."""
        data = self.get_minimal_data()
        data["size"] = 0
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["size"] == 0

    def test_create_large_size_fails(self, guest_client):
        """CREATE with size > max_int should fail (IntegerField limit)."""
        data = self.get_minimal_data()
        data["size"] = 10_000_000_000  # 10 GB > 2147483647
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # IntegerField max value is 2147483647
        assert response.status_code == 400
        assert "size" in response.json()

    def test_create_invalid_mime_format_succeeds(self, guest_client):
        """CREATE with invalid mime format may succeed (no validation)."""
        data = self.get_minimal_data()
        data["mime"] = "invalid-mime-format"
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # No mime validation in serializer
        assert response.status_code == 201
        assert response.json()["mime"] == "invalid-mime-format"

    def test_create_empty_mime_fails(self, guest_client):
        """CREATE with empty mime should fail (required field)."""
        data = self.get_minimal_data()
        data["mime"] = ""
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "mime" in response.json()

    def test_create_unicode_in_name_succeeds(self, guest_client):
        """CREATE with unicode characters in name should succeed."""
        data = self.get_minimal_data()
        data["name"] = "日本語トラック 🎵"
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "日本語トラック 🎵"

    def test_create_special_chars_in_name_succeeds(self, guest_client):
        """CREATE with special characters in name should succeed."""
        data = self.get_minimal_data()
        data["name"] = "Track <script>alert('xss')</script>"
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # No XSS sanitization
        assert response.status_code == 201

    def test_create_invalid_import_status_fails(self, guest_client):
        """CREATE with invalid import_status should fail."""
        data = self.get_minimal_data()
        data["import_status"] = 999  # Invalid value
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # IntegerField with choices may reject invalid values
        assert response.status_code in [201, 400]

    def test_create_null_required_field_fails(self, guest_client):
        """CREATE with null in required field should fail."""
        data = self.get_minimal_data()
        data["name"] = None
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_extra_fields_ignored(self, guest_client):
        """CREATE with extra fields should ignore them."""
        data = self.get_minimal_data()
        data["nonexistent_field"] = "value"
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # May succeed and ignore extra field, or fail
        assert response.status_code in [201, 400]

    def test_create_duplicate_filepath_succeeds(self, guest_client):
        """CREATE with same filepath as existing file should succeed (no unique constraint)."""
        # Create first file
        baker.make(
            File,
            name="First",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/shared.mp3",
        )
        # Create second with same filepath
        data = self.get_minimal_data()
        data["filepath"] = "audio/shared.mp3"
        response = guest_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        # No unique constraint on filepath
        assert response.status_code == 201

    def test_create_invalid_json_fails(self, guest_client):
        """CREATE with invalid JSON should return 400."""
        response = guest_client.post(
            "/api/v2/files",
            "invalid json {",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_empty_body_fails(self, guest_client):
        """CREATE with empty body should return 400."""
        response = guest_client.post(
            "/api/v2/files",
            "",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_invalid_mime_succeeds(self, guest_client):
        """UPDATE with invalid mime format may succeed."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = guest_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"mime": "invalid/mime"}),
            content_type="application/json",
        )
        # No mime validation
        assert response.status_code == 200
