"""
MANAGER Role Permissions Tests (Role.MANAGER / "P")

MANAGER users have full CRUD permissions on all resources.
They can:
- VIEW all resources
- CREATE any resource
- UPDATE any resource (not limited to own)
- DELETE any resource (not limited to own)

MANAGER is essentially full admin except for user management.
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Playlist, Show, SmartBlock, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestManagerPlaylistPermissions:
    """Test MANAGER permissions on Playlist endpoints."""

    def test_manager_can_list_all_playlists(self, manager_client):
        """MANAGER can LIST all playlists."""
        response = manager_client.get("/api/v2/playlists")
        assert response.status_code == 200

    def test_manager_can_retrieve_any_playlist(self, manager_client, faker):
        """MANAGER can RETRIEVE any playlist."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        playlist = baker.make(
            Playlist,
            name=f"Other Playlist {faker.uuid4()[:8]}",
            owner=other_host,
        )

        response = manager_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["name"] == playlist.name

    def test_manager_can_create_playlist(
        self, manager_client, manager_user, faker,
    ):
        """MANAGER can CREATE playlist (add_playlist permission)."""
        data = {
            "name": f"Manager Playlist {faker.uuid4()[:8]}",
        }
        response = manager_client.post(
            "/api/v2/playlists", data, format="json",
        )
        assert response.status_code == 201

        # Verify playlist was created
        playlist_id = response.data["id"]
        playlist = Playlist.objects.get(id=playlist_id)
        # Manager is set as owner
        assert playlist.owner == manager_user

    def test_manager_can_update_any_playlist(self, manager_client, faker):
        """MANAGER can UPDATE ANY playlist (change_playlist permission, not limited to own)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_playlist = baker.make(
            Playlist,
            name=f"Other Original {faker.uuid4()[:8]}",
            owner=other_host,
        )
        new_name = f"Updated by Manager {faker.uuid4()[:8]}"

        response = manager_client.patch(
            f"/api/v2/playlists/{other_playlist.id}",
            {"name": new_name},
            format="json",
        )
        # Manager should be able to update any playlist
        assert response.status_code == 200

        # Verify update
        other_playlist.refresh_from_db()
        assert other_playlist.name == new_name

    def test_manager_can_delete_any_playlist(self, manager_client, faker):
        """MANAGER can DELETE ANY playlist (delete_playlist permission, not limited to own)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_playlist = baker.make(
            Playlist,
            name=f"Other Playlist {faker.uuid4()[:8]}",
            owner=other_host,
        )
        other_playlist_id = other_playlist.id

        response = manager_client.delete(
            f"/api/v2/playlists/{other_playlist_id}",
        )
        # Manager should be able to delete any playlist
        assert response.status_code == 204

        # Verify deleted
        assert not Playlist.objects.filter(id=other_playlist_id).exists()


@pytest.mark.django_db
class TestManagerFilePermissions:
    """Test MANAGER permissions on File endpoints."""

    def test_manager_can_list_all_files(self, manager_client):
        """MANAGER can LIST all files."""
        response = manager_client.get("/api/v2/files")
        assert response.status_code == 200

    def test_manager_can_retrieve_any_file(self, manager_client, faker):
        """MANAGER can RETRIEVE any file metadata."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        file_obj = baker.make(
            File,
            name=f"other_file_{faker.uuid4()[:8]}.mp3",
            owner=other_host,
            mime="audio/mpeg",
        )

        response = manager_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        assert response.data["name"] == file_obj.name

    def test_manager_can_create_file(
        self, manager_client, manager_user, faker,
    ):
        """MANAGER can CREATE file (add_file permission)."""
        data = {
            "name": f"manager_file_{faker.uuid4()[:8]}.mp3",
            "mime": "audio/mpeg",
            "size": 1024,
            "accessed": int(now().timestamp()),
        }
        response = manager_client.post("/api/v2/files", data, format="json")
        assert response.status_code == 201

        # Verify file was created
        file_id = response.data["id"]
        file_obj = File.objects.get(id=file_id)
        assert file_obj.owner == manager_user

    def test_manager_can_update_any_file(self, manager_client, faker):
        """MANAGER can UPDATE ANY file (change_file permission)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_file = baker.make(
            File,
            name=f"other_original_{faker.uuid4()[:8]}.mp3",
            owner=other_host,
            mime="audio/mpeg",
        )
        new_name = f"manager_updated_{faker.uuid4()[:8]}.mp3"

        response = manager_client.patch(
            f"/api/v2/files/{other_file.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        # Verify update
        other_file.refresh_from_db()
        assert other_file.name == new_name

    def test_manager_cannot_delete_file(self, manager_client, faker):
        """MANAGER cannot DELETE file - file deletion is not allowed (409)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_file = baker.make(
            File,
            name=f"other_file_{faker.uuid4()[:8]}.mp3",
            owner=other_host,
            mime="audio/mpeg",
        )
        other_file_id = other_file.id

        response = manager_client.delete(f"/api/v2/files/{other_file_id}")
        # File deletion is not allowed for anyone (409 Conflict)
        assert response.status_code == 409

        # Verify file was NOT deleted
        assert File.objects.filter(id=other_file_id).exists()


@pytest.mark.django_db
class TestManagerSmartBlockPermissions:
    """Test MANAGER permissions on SmartBlock endpoints."""

    def test_manager_can_list_all_smartblocks(self, manager_client):
        """MANAGER can LIST all smart blocks."""
        response = manager_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200

    def test_manager_can_retrieve_any_smartblock(self, manager_client, faker):
        """MANAGER can RETRIEVE any smart block."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        block = baker.make(
            SmartBlock,
            name=f"Other Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        response = manager_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200
        assert response.data["name"] == block.name

    def test_manager_can_create_smartblock(
        self, manager_client, manager_user, faker,
    ):
        """MANAGER can CREATE smart block (add_smartblock permission)."""
        data = {
            "name": f"Manager Block {faker.uuid4()[:8]}",
            "kind": "dynamic",
        }
        response = manager_client.post(
            "/api/v2/smart-blocks", data, format="json",
        )
        assert response.status_code == 201

        block_id = response.data["id"]
        block = SmartBlock.objects.get(id=block_id)
        assert block.owner == manager_user

    def test_manager_can_update_any_smartblock(self, manager_client, faker):
        """MANAGER can UPDATE ANY smart block (change_smartblock permission)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Original {faker.uuid4()[:8]}",
            owner=other_host,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        new_name = f"Manager Updated {faker.uuid4()[:8]}"

        response = manager_client.patch(
            f"/api/v2/smart-blocks/{other_block.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        other_block.refresh_from_db()
        assert other_block.name == new_name

    def test_manager_can_delete_any_smartblock(self, manager_client, faker):
        """MANAGER can DELETE ANY smart block (delete_smartblock permission)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        other_block_id = other_block.id

        response = manager_client.delete(
            f"/api/v2/smart-blocks/{other_block_id}",
        )
        assert response.status_code == 204

        assert not SmartBlock.objects.filter(id=other_block_id).exists()


@pytest.mark.django_db
class TestManagerShowPermissions:
    """Test MANAGER permissions on Show endpoints."""

    def test_manager_can_list_all_shows(self, manager_client):
        """MANAGER can LIST all shows."""
        response = manager_client.get("/api/v2/shows")
        assert response.status_code == 200

    def test_manager_can_retrieve_any_show(self, manager_client, faker):
        """MANAGER can RETRIEVE any show."""
        show = baker.make(Show, name=f"Show {faker.uuid4()[:8]}")

        response = manager_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        assert response.data["name"] == show.name

    def test_manager_can_create_show(
        self, manager_client, manager_user, faker,
    ):
        """MANAGER can CREATE show (add_show permission)."""
        data = {
            "name": f"Manager Show {faker.uuid4()[:8]}",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = manager_client.post("/api/v2/shows", data, format="json")
        assert response.status_code == 201

        show_id = response.data["id"]
        show = Show.objects.get(id=show_id)
        # Manager becomes host of the show
        from api.schedule.models import ShowHost

        assert ShowHost.objects.filter(show=show, user=manager_user).exists()

    def test_manager_can_update_any_show(self, manager_client, faker):
        """MANAGER can UPDATE ANY show (change_show permission)."""
        # Create a show with another host
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        from api.schedule.models import ShowHost

        show = baker.make(Show, name=f"Other Show {faker.uuid4()[:8]}")
        ShowHost.objects.create(show=show, user=other_host)

        new_name = f"Manager Updated {faker.uuid4()[:8]}"

        response = manager_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": new_name},
            format="json",
        )
        # Manager should be able to update any show
        assert response.status_code == 200

        show.refresh_from_db()
        assert show.name == new_name

    def test_manager_can_delete_any_show(self, manager_client, faker):
        """MANAGER can DELETE ANY show (delete_show permission)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        from api.schedule.models import ShowHost

        show = baker.make(Show, name=f"Other Show {faker.uuid4()[:8]}")
        ShowHost.objects.create(show=show, user=other_host)
        show_id = show.id

        response = manager_client.delete(f"/api/v2/shows/{show_id}")
        assert response.status_code == 204

        assert not Show.objects.filter(id=show_id).exists()


@pytest.mark.django_db
class TestManagerWebstreamPermissions:
    """Test MANAGER permissions on Webstream endpoints."""

    def test_manager_can_list_all_webstreams(self, manager_client):
        """MANAGER can LIST all webstreams."""
        response = manager_client.get("/api/v2/webstreams")
        assert response.status_code == 200

    def test_manager_can_retrieve_any_webstream(self, manager_client, faker):
        """MANAGER can RETRIEVE any webstream."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        stream = baker.make(
            Webstream,
            name=f"Other Stream {faker.uuid4()[:8]}",
            owner=other_host,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )

        response = manager_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 200
        assert response.data["name"] == stream.name

    def test_manager_can_create_webstream(
        self, manager_client, manager_user, faker,
    ):
        """MANAGER can CREATE webstream (add_webstream permission)."""
        data = {
            "name": f"Manager Stream {faker.uuid4()[:8]}",
            "url": f"https://example.com/{faker.uuid4()[:8]}.mp3",
            "description": f"Manager test stream {faker.uuid4()[:8]}",
        }
        response = manager_client.post(
            "/api/v2/webstreams", data, format="json",
        )
        assert response.status_code == 201

        stream_id = response.data["id"]
        stream = Webstream.objects.get(id=stream_id)
        assert stream.owner == manager_user

    def test_manager_can_update_any_webstream(self, manager_client, faker):
        """MANAGER can UPDATE ANY webstream (change_webstream permission)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_stream = baker.make(
            Webstream,
            name=f"Other Original {faker.uuid4()[:8]}",
            owner=other_host,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )
        new_name = f"Manager Updated {faker.uuid4()[:8]}"

        response = manager_client.patch(
            f"/api/v2/webstreams/{other_stream.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        other_stream.refresh_from_db()
        assert other_stream.name == new_name

    def test_manager_can_delete_any_webstream(self, manager_client, faker):
        """MANAGER can DELETE ANY webstream (delete_webstream permission)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_stream = baker.make(
            Webstream,
            name=f"Other Stream {faker.uuid4()[:8]}",
            owner=other_host,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )
        other_stream_id = other_stream.id

        response = manager_client.delete(
            f"/api/v2/webstreams/{other_stream_id}",
        )
        assert response.status_code == 204

        assert not Webstream.objects.filter(id=other_stream_id).exists()
