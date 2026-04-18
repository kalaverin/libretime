"""Tests for File UPDATE endpoints (T190)."""

import json

import pytest

from model_bakery import baker

from api.storage.models import File, Library


@pytest.mark.django_db(transaction=True)
class TestFileViewSetUpdate:
    """Test Files UPDATE endpoints - PUT/PATCH /api/v2/files/{id}."""

    def get_file_data(self, **overrides):
        """Return valid data for updating a file."""
        data = {
            "name": "Updated Track",
            "mime": "audio/mpeg",
            "size": 10_000_000,
            "accessed": 0,
            "artist_name": "Updated Artist",
            "track_title": "Updated Title",
            "album_title": "Updated Album",
            "genre": "Updated Genre",
        }
        data.update(overrides)
        return data

    def test_patch_update_metadata_success(self, admin_client):
        """PATCH should update editable metadata fields."""
        file = baker.make(
            File,
            name="Original",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            artist_name="Original Artist",
        )
        patch_data = {"artist_name": "New Artist", "track_title": "New Title"}

        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps(patch_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        result = response.json()
        assert result["artist_name"] == "New Artist"
        assert result["track_title"] == "New Title"
        # Unchanged fields remain
        assert result["name"] == "Original"

    def test_patch_update_genre(self, admin_client):
        """PATCH should update genre field."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            genre="Rock",
        )
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"genre": "Jazz"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["genre"] == "Jazz"

    def test_patch_clear_nullable_field(self, admin_client):
        """PATCH should clear nullable fields with null."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            artist_name="Artist",
        )
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"artist_name": None}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["artist_name"] is None

    def test_patch_update_multiple_fields(self, admin_client):
        """PATCH should update multiple fields at once."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            artist_name="Old Artist",
            track_title="Old Title",
            album_title="Old Album",
            genre="Old Genre",
        )
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps(
                {
                    "artist_name": "New Artist",
                    "track_title": "New Title",
                    "album_title": "New Album",
                    "genre": "New Genre",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200

        result = response.json()
        assert result["artist_name"] == "New Artist"
        assert result["track_title"] == "New Title"
        assert result["album_title"] == "New Album"
        assert result["genre"] == "New Genre"

    def test_patch_not_found(self, admin_client):
        """PATCH non-existent file should return 404."""
        response = admin_client.patch(
            "/api/v2/files/999999",
            json.dumps({"artist_name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_patch_no_auth_returns_403(self, client):
        """PATCH should return 403 without authentication."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"artist_name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_patch_empty_body_no_change(self, admin_client):
        """PATCH with empty body should not change anything."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            artist_name="Artist",
        )
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["artist_name"] == "Artist"
        assert response.json()["name"] == "Track"

    def test_put_update_requires_all_fields(self, admin_client):
        """PUT without all required fields should fail."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        # PUT with only some fields (missing required)
        response = admin_client.put(
            f"/api/v2/files/{file.id}",
            json.dumps({"artist_name": "New Artist"}),
            content_type="application/json",
        )
        # Should fail because PUT requires all required fields
        assert response.status_code == 400

    def test_put_update_success(self, admin_client):
        """PUT with all required fields should succeed."""
        file = baker.make(
            File,
            name="Old Name",
            mime="audio/wav",
            size=5000,
            accessed=10,
            artist_name="Old Artist",
        )
        data = {
            "name": "New Name",
            "mime": "audio/flac",
            "size": 50_000_000,
            "accessed": 100,
            "artist_name": "New Artist",
            "track_title": "New Title",
        }
        response = admin_client.put(
            f"/api/v2/files/{file.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200

        result = response.json()
        assert result["name"] == "New Name"
        assert result["mime"] == "audio/flac"
        assert result["size"] == 50_000_000
        assert result["accessed"] == 100
        assert result["artist_name"] == "New Artist"
        assert result["track_title"] == "New Title"

    def test_put_not_found(self, admin_client):
        """PUT non-existent file should return 404."""
        data = self.get_file_data()
        response = admin_client.put(
            "/api/v2/files/999999",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_unicode_values(self, admin_client):
        """PATCH with unicode values should work."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps(
                {
                    "artist_name": "日本語アーティスト",
                    "track_title": "日本語タイトル",
                    "genre": "J-Pop",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200

        result = response.json()
        assert result["artist_name"] == "日本語アーティスト"
        assert result["track_title"] == "日本語タイトル"

    def test_update_returns_json(self, admin_client):
        """UPDATE should return JSON response."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"artist_name": "New"}),
            content_type="application/json",
        )
        assert response["Content-Type"] == "application/json"

    def test_patch_update_library(self, admin_client):
        """PATCH should update library reference."""
        old_lib = baker.make(
            Library,
            code="old",
            name="Old",
            description="Old lib",
        )
        new_lib = baker.make(
            Library,
            code="new",
            name="New",
            description="New lib",
        )
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            library=old_lib,
        )
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"library": new_lib.id}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["library"] == new_lib.id

    def test_update_preserves_id(self, admin_client):
        """UPDATE should preserve the file id."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        original_id = file.id
        response = admin_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"artist_name": "New"}),
            content_type="application/json",
        )
        assert response.json()["id"] == original_id
