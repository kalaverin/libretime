"""
Mass assignment protection tests.

Tests for:
- ID manipulation (T477, T497, T508, T547, T810, T833, T858, T426)
- Owner hijacking (T526, T546, T567, T812, T835, T860, T880, T882)
- Timestamp manipulation (T529, T548, T811, T834, T859)
- Extra fields rejection (T478, T498, T530, T813, T836, T861)
"""

import json

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.schedule.models import (
    Playlist,
    SmartBlock,
    SmartBlockCriteria,
    Webstream,
)
from api.storage.models import File, Library


class TestMassAssignmentIdBlocked:
    """Test that ID cannot be mass-assigned in CREATE/UPDATE."""

    @pytest.mark.django_db
    def test_create_playlist_with_id_blocked(self, admin_user, faker):
        """T810: Setting id on playlist CREATE should fail."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "id": 99999,
                    "name": f"Test Playlist {faker.uuid4()[:8]}",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "id" in str(response.content).lower()

    @pytest.mark.django_db
    def test_create_smartblock_with_id_blocked(self, admin_user, faker):
        """T833: Setting id on smartblock CREATE should fail."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "id": 88888,
                    "name": f"Test Block {faker.uuid4()[:8]}",
                    "kind": "static",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "id" in str(response.content).lower()

    @pytest.mark.django_db
    def test_create_webstream_with_id_blocked(self, admin_user, faker):
        """T547: Setting id on webstream CREATE should fail."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "id": 77777,
                    "name": f"Test Stream {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": "Test",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "id" in str(response.content).lower()

    @pytest.mark.django_db
    def test_update_playlist_id_blocked(self, admin_user, faker):
        """T810: Changing id on playlist UPDATE should fail."""
        playlist = baker.make(Playlist, name="Test Playlist", owner=admin_user)
        original_id = playlist.id

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"id": 99999}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "id" in str(response.content).lower()

        # Verify ID unchanged
        playlist.refresh_from_db()
        assert playlist.id == original_id


class TestMassAssignmentOwnerBlocked:
    """Test that owner cannot be mass-assigned."""

    @pytest.mark.django_db
    def test_create_playlist_owner_blocked(
        self, admin_user, guest_user, faker,
    ):
        """T812: Setting owner on playlist CREATE should fail with 400."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": f"Test Playlist {faker.uuid4()[:8]}",
                    "owner": guest_user.id,  # Try to assign to another user
                },
            ),
            content_type="application/json",
        )
        # API assigns owner - external assignment blocked with 400
        assert response.status_code == 400
        assert "owner" in str(response.content).lower()

    @pytest.mark.django_db
    def test_update_playlist_owner_blocked(
        self, admin_user, manager_user, faker,
    ):
        """T812: Changing owner on playlist UPDATE should fail."""
        playlist = baker.make(Playlist, name="Test Playlist", owner=admin_user)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"owner": manager_user.id}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "owner" in str(response.content).lower()

        # Verify owner unchanged
        playlist.refresh_from_db()
        assert playlist.owner == admin_user

    @pytest.mark.django_db
    def test_create_webstream_owner_blocked(
        self, admin_user, manager_user, faker,
    ):
        """T526: Setting owner on webstream CREATE should fail with 400."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": f"Test Stream {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": "Test",
                    "owner": manager_user.id,
                },
            ),
            content_type="application/json",
        )
        # API assigns owner - external assignment blocked with 400
        assert response.status_code == 400
        assert "owner" in str(response.content).lower()

    @pytest.mark.django_db
    def test_update_webstream_owner_blocked(
        self, admin_user, manager_user, faker,
    ):
        """T546, T567: Changing owner on webstream UPDATE should fail."""
        webstream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=admin_user,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/webstreams/{webstream.id}",
            json.dumps({"owner": manager_user.id}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "owner" in str(response.content).lower()

        webstream.refresh_from_db()
        assert webstream.owner == admin_user


class TestMassAssignmentTimestampsBlocked:
    """Test that created_at/updated_at cannot be mass-assigned."""

    @pytest.mark.django_db
    def test_create_playlist_created_at_blocked(self, admin_user, faker):
        """T811: Setting created_at on playlist CREATE should fail."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        fake_date = "2020-01-01T00:00:00Z"
        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": f"Test Playlist {faker.uuid4()[:8]}",
                    "created_at": fake_date,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "created_at" in str(response.content).lower()

    @pytest.mark.django_db
    def test_update_playlist_created_at_blocked(self, admin_user, faker):
        """T811: Changing created_at on playlist UPDATE should fail."""
        playlist = baker.make(Playlist, name="Test Playlist", owner=admin_user)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        fake_date = "2025-12-31T23:59:59Z"
        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"created_at": fake_date}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "created_at" in str(response.content).lower()

    @pytest.mark.django_db
    def test_create_webstream_created_at_blocked(self, admin_user, faker):
        """T529: Setting created_at on webstream CREATE should fail."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        fake_date = "2020-01-01T00:00:00Z"
        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": f"Test Stream {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": "Test",
                    "created_at": fake_date,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "created_at" in str(response.content).lower()

    @pytest.mark.django_db
    def test_update_webstream_created_at_blocked(self, admin_user, faker):
        """T548: Changing created_at on webstream UPDATE should fail."""
        webstream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=admin_user,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        fake_date = "2025-12-31T23:59:59Z"
        response = client.patch(
            f"/api/v2/webstreams/{webstream.id}",
            json.dumps({"created_at": fake_date}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "created_at" in str(response.content).lower()


class TestMassAssignmentSmartBlockContent:
    """Test SmartBlockContent mass assignment protection."""

    @pytest.mark.django_db
    def test_create_smartblockcontent_id_blocked(self, admin_user, faker):
        """T477: Setting id on SmartBlockContent CREATE should fail."""
        block = baker.make(SmartBlock, name="Test Block", owner=admin_user)
        library = baker.make(
            Library, name="Test Library", description="Test Desc",
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            filepath="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "id": 77777,
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                    "kind": "file",
                    "offset": "00:00:00",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "id" in str(response.content).lower()


class TestMassAssignmentSmartBlockCriteria:
    """Test SmartBlockCriteria mass assignment protection."""

    @pytest.mark.django_db
    def test_create_smartblockcriteria_id_blocked(self, admin_user, faker):
        """T497: Setting id on SmartBlockCriteria CREATE should fail."""
        block = baker.make(SmartBlock, name="Test Block", owner=admin_user)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "id": 66666,
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "2",  # "is" condition
                    "value": "Rock",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "id" in str(response.content).lower()

    @pytest.mark.django_db
    def test_update_smartblockcriteria_id_blocked(self, admin_user, faker):
        """T508: Changing id on SmartBlockCriteria UPDATE should fail."""
        block = baker.make(SmartBlock, name="Test Block", owner=admin_user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="2",  # "is" condition
            value="Rock",
        )
        original_id = criteria.id

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"id": 55555}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "id" in str(response.content).lower()

        criteria.refresh_from_db()
        assert criteria.id == original_id


class TestExtraFieldsRejected:
    """Test that unknown/extra fields are rejected."""

    @pytest.mark.django_db
    def test_create_playlist_extra_fields_blocked(self, admin_user, faker):
        """T813: Unknown fields on playlist CREATE should fail."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": f"Test Playlist {faker.uuid4()[:8]}",
                    "is_admin": True,
                    "role": "superuser",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert (
            "extra_fields" in str(response.content).lower()
            or "unknown" in str(response.content).lower()
        )

    @pytest.mark.django_db
    def test_create_webstream_extra_fields_blocked(self, admin_user, faker):
        """T530: Unknown fields on webstream CREATE should fail."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": f"Test Stream {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": "Test",
                    "password": "secret123",
                    "api_key": "super_secret",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert (
            "extra_fields" in str(response.content).lower()
            or "unknown" in str(response.content).lower()
        )

    @pytest.mark.django_db
    def test_update_smartblock_extra_fields_blocked(self, admin_user, faker):
        """T836: Unknown fields on smartblock UPDATE should fail."""
        block = baker.make(SmartBlock, name="Test Block", owner=admin_user)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps(
                {
                    "name": "Updated Block",
                    "is_system": True,
                    "internal_flag": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert (
            "extra_fields" in str(response.content).lower()
            or "unknown" in str(response.content).lower()
        )


class TestValidOperationsStillWork:
    """Test that valid CREATE/UPDATE operations still work."""

    @pytest.mark.django_db
    def test_create_playlist_valid(self, admin_user, faker):
        """Valid playlist CREATE should succeed."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": f"Valid Playlist {faker.uuid4()[:8]}",
                    "description": "Test description",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.data["owner"] == admin_user.id

    @pytest.mark.django_db
    def test_update_playlist_valid(self, admin_user, faker):
        """Valid playlist UPDATE should succeed."""
        playlist = baker.make(Playlist, name="Old Name", owner=admin_user)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "New Valid Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.data["name"] == "New Valid Name"

    @pytest.mark.django_db
    def test_create_webstream_valid(self, admin_user, faker):
        """Valid webstream CREATE should succeed."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": f"Valid Stream {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": "Test description",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.data["owner"] == admin_user.id
