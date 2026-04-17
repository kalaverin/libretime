"""
GUEST Role Permissions Tests (Role.GUEST / "G")

GUEST users have read-only access (view_* permissions).
They should be able to:
- LIST all public resources (shows, schedules for viewing)
- RETRIEVE individual resources

They should NOT be able to:
- CREATE any resources
- UPDATE any resources
- DELETE any resources
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Playlist, Show, SmartBlock, Webstream
from api.storage.models import File


@pytest.mark.django_db
class TestGuestPlaylistPermissions:
    """Test GUEST permissions on Playlist endpoints."""

    def test_guest_can_list_playlists(self, guest_client):
        """GUEST can LIST playlists (view_playlist permission)."""
        response = guest_client.get("/api/v2/playlists")
        # GUEST has view_playlist permission
        assert response.status_code == 200

    def test_guest_can_retrieve_playlist(self, guest_client, faker):
        """GUEST can RETRIEVE a playlist (view_playlist permission)."""
        # Create a playlist owned by someone else
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        playlist = baker.make(
            Playlist, name=f"Playlist {faker.uuid4()[:8]}", owner=owner,
        )

        response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        # GUEST should see the playlist (public schedule info)
        assert response.status_code == 200
        assert response.data["name"] == playlist.name

    def test_guest_cannot_create_playlist(self, guest_client, faker):
        """GUEST cannot CREATE playlist (no add_playlist permission)."""
        data = {
            "name": f"Guest Playlist {faker.uuid4()[:8]}",
        }
        response = guest_client.post("/api/v2/playlists", data, format="json")
        # Should be denied - GUEST has no add permission
        assert response.status_code in [403, 401]

    def test_guest_cannot_update_playlist(self, guest_client, faker):
        """GUEST cannot UPDATE playlist (no change_playlist permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        playlist = baker.make(
            Playlist, name=f"Original {faker.uuid4()[:8]}", owner=owner,
        )

        response = guest_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            {"name": "Hacked Name"},
            format="json",
        )
        # Should be denied
        assert response.status_code in [403, 401]

        # Verify not modified
        playlist.refresh_from_db()
        assert playlist.name.startswith("Original")

    def test_guest_cannot_delete_playlist(self, guest_client, faker):
        """GUEST cannot DELETE playlist (no delete_playlist permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        playlist = baker.make(
            Playlist, name=f"Playlist {faker.uuid4()[:8]}", owner=owner,
        )
        playlist_id = playlist.id

        response = guest_client.delete(f"/api/v2/playlists/{playlist_id}")
        # Should be denied
        assert response.status_code in [403, 401]

        # Verify still exists
        assert Playlist.objects.filter(id=playlist_id).exists()


@pytest.mark.django_db
class TestGuestFilePermissions:
    """Test GUEST permissions on File endpoints."""

    def test_guest_can_list_files(self, guest_client):
        """GUEST can LIST files (view_file permission)."""
        response = guest_client.get("/api/v2/files")
        assert response.status_code == 200

    def test_guest_can_retrieve_file(self, guest_client, faker):
        """GUEST can RETRIEVE file metadata (view_file permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        file_obj = baker.make(
            File,
            name=f"file_{faker.uuid4()[:8]}.mp3",
            owner=owner,
            mime="audio/mpeg",
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        assert response.data["name"] == file_obj.name

    def test_guest_cannot_create_file(self, guest_client, faker):
        """GUEST cannot CREATE file (no add_file permission)."""
        data = {
            "name": f"guest_file_{faker.uuid4()[:8]}.mp3",
            "mime": "audio/mpeg",
        }
        response = guest_client.post("/api/v2/files", data, format="json")
        assert response.status_code in [403, 401]

    def test_guest_cannot_update_file(self, guest_client, faker):
        """GUEST cannot UPDATE file (no change_file permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        file_obj = baker.make(
            File,
            name=f"original_{faker.uuid4()[:8]}.mp3",
            owner=owner,
            mime="audio/mpeg",
        )

        response = guest_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"name": "hacked.mp3"},
            format="json",
        )
        assert response.status_code in [403, 401]

    def test_guest_cannot_delete_file(self, guest_client, faker):
        """GUEST cannot DELETE file (no delete_file permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        file_obj = baker.make(
            File,
            name=f"file_{faker.uuid4()[:8]}.mp3",
            owner=owner,
            mime="audio/mpeg",
        )
        file_id = file_obj.id

        response = guest_client.delete(f"/api/v2/files/{file_id}")
        assert response.status_code in [403, 401]
        assert File.objects.filter(id=file_id).exists()


@pytest.mark.django_db
class TestGuestSmartBlockPermissions:
    """Test GUEST permissions on SmartBlock endpoints."""

    def test_guest_can_list_smartblocks(self, guest_client):
        """GUEST can LIST smart blocks (view_smartblock permission)."""
        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200

    def test_guest_can_retrieve_smartblock(self, guest_client, faker):
        """GUEST can RETRIEVE smart block (view_smartblock permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        block = baker.make(
            SmartBlock,
            name=f"Block {faker.uuid4()[:8]}",
            owner=owner,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        response = guest_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200
        assert response.data["name"] == block.name

    def test_guest_cannot_create_smartblock(self, guest_client, faker):
        """GUEST cannot CREATE smart block (no add_smartblock permission)."""
        data = {
            "name": f"Guest Block {faker.uuid4()[:8]}",
            "kind": "dynamic",
        }
        response = guest_client.post(
            "/api/v2/smart-blocks", data, format="json",
        )
        assert response.status_code in [403, 401]

    def test_guest_cannot_update_smartblock(self, guest_client, faker):
        """GUEST cannot UPDATE smart block (no change_smartblock permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        block = baker.make(
            SmartBlock,
            name=f"Original {faker.uuid4()[:8]}",
            owner=owner,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        response = guest_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            {"name": "Hacked"},
            format="json",
        )
        assert response.status_code in [403, 401]

    def test_guest_cannot_delete_smartblock(self, guest_client, faker):
        """GUEST cannot DELETE smart block (no delete_smartblock permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        block = baker.make(
            SmartBlock,
            name=f"Block {faker.uuid4()[:8]}",
            owner=owner,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        block_id = block.id

        response = guest_client.delete(f"/api/v2/smart-blocks/{block_id}")
        assert response.status_code in [403, 401]
        assert SmartBlock.objects.filter(id=block_id).exists()


@pytest.mark.django_db
class TestGuestShowPermissions:
    """Test GUEST permissions on Show endpoints (public broadcast schedule)."""

    def test_guest_can_list_shows(self, guest_client):
        """GUEST can LIST shows (view_show permission) - public schedule."""
        response = guest_client.get("/api/v2/shows")
        assert response.status_code == 200

    def test_guest_can_retrieve_show(self, guest_client, faker):
        """GUEST can RETRIEVE show (view_show permission) - public schedule."""
        show = baker.make(Show, name=f"Show {faker.uuid4()[:8]}")

        response = guest_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        assert response.data["name"] == show.name

    def test_guest_cannot_create_show(self, guest_client, faker):
        """GUEST cannot CREATE show (no add_show permission)."""
        data = {
            "name": f"Guest Show {faker.uuid4()[:8]}",
            "linked": False,
            "linkable": True,
        }
        response = guest_client.post("/api/v2/shows", data, format="json")
        assert response.status_code in [403, 401]

    def test_guest_cannot_update_show(self, guest_client, faker):
        """GUEST cannot UPDATE show (no change_show permission)."""
        show = baker.make(Show, name=f"Original {faker.uuid4()[:8]}")

        response = guest_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "Hacked"},
            format="json",
        )
        assert response.status_code in [403, 401]

    def test_guest_cannot_delete_show(self, guest_client, faker):
        """GUEST cannot DELETE show (no delete_show permission)."""
        show = baker.make(Show, name=f"Show {faker.uuid4()[:8]}")
        show_id = show.id

        response = guest_client.delete(f"/api/v2/shows/{show_id}")
        assert response.status_code in [403, 401]
        assert Show.objects.filter(id=show_id).exists()


@pytest.mark.django_db
class TestGuestWebstreamPermissions:
    """Test GUEST permissions on Webstream endpoints."""

    def test_guest_can_list_webstreams(self, guest_client):
        """GUEST can LIST webstreams (view_webstream permission)."""
        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200

    def test_guest_can_retrieve_webstream(self, guest_client, faker):
        """GUEST can RETRIEVE webstream (view_webstream permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        stream = baker.make(
            Webstream,
            name=f"Stream {faker.uuid4()[:8]}",
            owner=owner,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )

        response = guest_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 200
        assert response.data["name"] == stream.name

    def test_guest_cannot_create_webstream(self, guest_client, faker):
        """GUEST cannot CREATE webstream (no add_webstream permission)."""
        data = {
            "name": f"Guest Stream {faker.uuid4()[:8]}",
            "url": f"https://example.com/{faker.uuid4()[:8]}.mp3",
        }
        response = guest_client.post("/api/v2/webstreams", data, format="json")
        assert response.status_code in [403, 401]

    def test_guest_cannot_update_webstream(self, guest_client, faker):
        """GUEST cannot UPDATE webstream (no change_webstream permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        stream = baker.make(
            Webstream,
            name=f"Original {faker.uuid4()[:8]}",
            owner=owner,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )

        response = guest_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"name": "Hacked"},
            format="json",
        )
        assert response.status_code in [403, 401]

    def test_guest_cannot_delete_webstream(self, guest_client, faker):
        """GUEST cannot DELETE webstream (no delete_webstream permission)."""
        owner = baker.make(
            User,
            username=f"owner_{faker.uuid4()[:8]}",
            email=f"owner_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        stream = baker.make(
            Webstream,
            name=f"Stream {faker.uuid4()[:8]}",
            owner=owner,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )
        stream_id = stream.id

        response = guest_client.delete(f"/api/v2/webstreams/{stream_id}")
        assert response.status_code in [403, 401]
        assert Webstream.objects.filter(id=stream_id).exists()
