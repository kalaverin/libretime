"""Tests for File permissions (T195)."""

import json

from unittest.mock import patch

import pytest

from model_bakery import baker

from api.core.models import User
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestFileViewSetPermissions:
    """Test Files permissions - owner vs admin vs other users."""

    def test_list_files_visible_to_all(self, api_client):
        """LIST should show all files regardless of owner."""
        # Create files with different owners
        user1 = baker.make(User, username="perm_user1")
        user2 = baker.make(User, username="perm_user2")

        own_file = baker.make(
            File,
            owner=user1,
            name="My File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        other_file = baker.make(
            File,
            owner=user2,
            name="Other File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        no_owner_file = baker.make(
            File,
            owner=None,
            name="Orphan File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )

        response = api_client.get("/api/v2/files")
        data = response.json()
        ids = {item["id"] for item in data}

        # All files visible in list
        assert own_file.id in ids
        assert other_file.id in ids
        assert no_owner_file.id in ids

    def test_retrieve_file_visible_to_all(self, api_client):
        """RETRIEVE should work for any file with API key."""
        user = baker.make(User, username="perm_user3")
        file = baker.make(
            File,
            owner=user,
            name="Test File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = api_client.get(f"/api/v2/files/{file.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test File"

    def test_update_with_api_key_succeeds(self, api_client):
        """UPDATE with API key should succeed (no per-object permission check)."""
        user = baker.make(User, username="perm_user4")
        file = baker.make(
            File,
            owner=user,
            name="Original",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = api_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        # With API key, update succeeds
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_delete_with_api_key_succeeds(self, api_client):
        """DELETE with API key should succeed."""
        user = baker.make(User, username="perm_user5")
        file = baker.make(
            File,
            owner=user,
            name="To Delete",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/delete.mp3",
        )
        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch("api.storage.views.file.remove"):
                response = api_client.delete(f"/api/v2/files/{file.id}")
        # With API key, delete succeeds (returns 204)
        assert response.status_code == 204

    def test_create_file_with_api_key(self, api_client):
        """CREATE with API key should succeed."""
        data = {
            "name": "New File",
            "mime": "audio/mpeg",
            "size": 1000,
            "accessed": 0,
        }
        response = api_client.post(
            "/api/v2/files",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_download_with_api_key(self, api_client):
        """DOWNLOAD with API key should succeed."""
        user = baker.make(User, username="perm_user6")
        file = baker.make(
            File,
            owner=user,
            name="Downloadable",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/download.mp3",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")
        assert response.status_code == 200
        assert "X-Accel-Redirect" in response

    def test_file_without_owner_retrievable(self, api_client):
        """Files without owner should be retrievable."""
        file = baker.make(
            File,
            owner=None,
            name="Orphan File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = api_client.get(f"/api/v2/files/{file.id}")
        assert response.status_code == 200
        assert response.json()["owner"] is None

    def test_file_without_owner_updatable(self, api_client):
        """Files without owner should be updatable with API key."""
        file = baker.make(
            File,
            owner=None,
            name="Orphan File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = api_client.patch(
            f"/api/v2/files/{file.id}",
            json.dumps({"name": "Updated Orphan"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Orphan"

    def test_guest_user_can_view(self, api_client):
        """Guest user (via API) should be able to view files."""
        # API key auth is system-level, not user-level
        file = baker.make(
            File,
            name="File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        # With API key, can view
        response = api_client.get(f"/api/v2/files/{file.id}")
        assert response.status_code == 200

    def test_no_auth_fails(self, client):
        """Requests without auth should fail."""
        file = baker.make(
            File,
            name="File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        # No auth - should fail
        response = client.get(f"/api/v2/files/{file.id}")
        assert response.status_code == 403

    def test_download_requires_auth(self, client):
        """DOWNLOAD without auth should fail."""
        file = baker.make(
            File,
            name="File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = client.get(f"/api/v2/files/{file.id}/download")
        assert response.status_code == 403

    def test_owner_field_in_response(self, api_client):
        """Owner field should be present in responses."""
        user = baker.make(User, username="perm_owner")
        file = baker.make(
            File,
            owner=user,
            name="Owned File",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
        )
        response = api_client.get(f"/api/v2/files/{file.id}")
        data = response.json()
        assert "owner" in data
        assert data["owner"] == user.id
