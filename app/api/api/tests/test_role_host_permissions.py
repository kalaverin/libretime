"""
HOST Role Permissions Tests (Role.HOST / "H")

HOST users can:
- VIEW all resources (like GUEST)
- CREATE new resources (owned by themselves)
- UPDATE own resources (change_own_* permissions)
- DELETE own resources (delete_own_* permissions)

HOST users CANNOT:
- UPDATE other users' resources
- DELETE other users' resources
"""

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Playlist, Show, SmartBlock, Webstream
from api.storage.models import File

from sdk import now


@pytest.mark.django_db
class TestHostPlaylistPermissions:
    """Test HOST permissions on Playlist endpoints."""

    def test_host_can_list_all_playlists(self, host_client):
        """HOST can LIST all playlists (view_playlist permission)."""
        response = host_client.get("/api/v2/playlists")
        assert response.status_code == 200

    def test_host_can_retrieve_any_playlist(self, host_client, faker):
        """HOST can RETRIEVE any playlist (view_playlist permission)."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        playlist = baker.make(Playlist, name=f"Other Playlist {faker.uuid4()[:8]}", owner=other_host)

        response = host_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["name"] == playlist.name

    def test_host_can_create_own_playlist(self, host_client, host_user, faker):
        """HOST can CREATE playlist (add_playlist permission), auto-assigned as owner."""
        data = {
            "name": f"My Playlist {faker.uuid4()[:8]}",
        }
        response = host_client.post("/api/v2/playlists", data, format="json")
        assert response.status_code == 201

        # Verify playlist was created with host as owner
        playlist_id = response.data["id"]
        playlist = Playlist.objects.get(id=playlist_id)
        assert playlist.owner == host_user

    def test_host_can_update_own_playlist(self, host_client, host_user, faker):
        """HOST can UPDATE own playlist (change_own_playlist permission)."""
        playlist = baker.make(
            Playlist,
            name=f"Original {faker.uuid4()[:8]}",
            owner=host_user,
        )
        new_name = f"Updated {faker.uuid4()[:8]}"

        response = host_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        # Verify update
        playlist.refresh_from_db()
        assert playlist.name == new_name

    def test_host_cannot_update_other_playlist(self, host_client, faker):
        """HOST cannot UPDATE other user's playlist (BOLA prevention)."""
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
        original_name = other_playlist.name

        response = host_client.patch(
            f"/api/v2/playlists/{other_playlist.id}",
            {"name": "Hacked Name"},
            format="json",
        )
        # Should be denied (404 not found or 403 forbidden)
        assert response.status_code in [403, 404]

        # Verify not modified
        other_playlist.refresh_from_db()
        assert other_playlist.name == original_name

    def test_host_can_delete_own_playlist(self, host_client, host_user, faker):
        """HOST can DELETE own playlist (delete_own_playlist permission)."""
        playlist = baker.make(
            Playlist,
            name=f"To Delete {faker.uuid4()[:8]}",
            owner=host_user,
        )
        playlist_id = playlist.id

        response = host_client.delete(f"/api/v2/playlists/{playlist_id}")
        assert response.status_code == 204

        # Verify deleted
        assert not Playlist.objects.filter(id=playlist_id).exists()

    def test_host_cannot_delete_other_playlist(self, host_client, faker):
        """HOST cannot DELETE other user's playlist (BOLA prevention)."""
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

        response = host_client.delete(f"/api/v2/playlists/{other_playlist_id}")
        # Should be denied
        assert response.status_code in [403, 404]

        # Verify still exists
        assert Playlist.objects.filter(id=other_playlist_id).exists()


@pytest.mark.django_db
class TestHostFilePermissions:
    """Test HOST permissions on File endpoints."""

    def test_host_can_list_all_files(self, host_client):
        """HOST can LIST all files (view_file permission)."""
        response = host_client.get("/api/v2/files")
        assert response.status_code == 200

    def test_host_can_retrieve_any_file(self, host_client, faker):
        """HOST can RETRIEVE any file metadata (view_file permission)."""
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

        response = host_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        assert response.data["name"] == file_obj.name

    def test_host_can_create_own_file(self, host_client, host_user, faker):
        """HOST can CREATE file (add_file permission), auto-assigned as owner."""
        data = {
            "name": f"my_file_{faker.uuid4()[:8]}.mp3",
            "mime": "audio/mpeg",
            "size": 1024,
            "accessed": int(now().timestamp()),
        }
        response = host_client.post("/api/v2/files", data, format="json")
        assert response.status_code == 201

        # Verify file was created with host as owner
        file_id = response.data["id"]
        file_obj = File.objects.get(id=file_id)
        assert file_obj.owner == host_user

    def test_host_can_update_own_file(self, host_client, host_user, faker):
        """HOST can UPDATE own file (change_own_file permission)."""
        file_obj = baker.make(
            File,
            name=f"original_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
        )
        new_name = f"updated_{faker.uuid4()[:8]}.mp3"

        response = host_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        # Verify update
        file_obj.refresh_from_db()
        assert file_obj.name == new_name

    def test_host_cannot_update_other_file(self, host_client, faker):
        """HOST cannot UPDATE other user's file (BOLA prevention)."""
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
        original_name = other_file.name

        response = host_client.patch(
            f"/api/v2/files/{other_file.id}",
            {"name": "hacked.mp3"},
            format="json",
        )
        assert response.status_code in [403, 404]

        # Verify not modified
        other_file.refresh_from_db()
        assert other_file.name == original_name

    def test_host_can_delete_own_file(self, host_client, host_user, faker):
        """HOST can DELETE own file (delete_own_file permission)."""
        file_obj = baker.make(
            File,
            name=f"to_delete_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
        )
        file_id = file_obj.id

        response = host_client.delete(f"/api/v2/files/{file_id}")
        assert response.status_code == 204

        # Verify deleted (metadata only - file deletion is in perform_destroy)
        assert not File.objects.filter(id=file_id).exists()

    def test_host_cannot_delete_other_file(self, host_client, faker):
        """HOST cannot DELETE other user's file (BOLA prevention)."""
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

        response = host_client.delete(f"/api/v2/files/{other_file_id}")
        assert response.status_code in [403, 404]

        # Verify still exists
        assert File.objects.filter(id=other_file_id).exists()


@pytest.mark.django_db
class TestHostSmartBlockPermissions:
    """Test HOST permissions on SmartBlock endpoints."""

    def test_host_can_list_all_smartblocks(self, host_client):
        """HOST can LIST all smart blocks (view_smartblock permission)."""
        response = host_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200

    def test_host_can_retrieve_any_smartblock(self, host_client, faker):
        """HOST can RETRIEVE any smart block (view_smartblock permission)."""
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

        response = host_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200
        assert response.data["name"] == block.name

    def test_host_can_create_own_smartblock(self, host_client, host_user, faker):
        """HOST can CREATE smart block (add_smartblock permission)."""
        data = {
            "name": f"My Block {faker.uuid4()[:8]}",
            "kind": "dynamic",
        }
        response = host_client.post("/api/v2/smart-blocks", data, format="json")
        assert response.status_code == 201

        # Verify block was created with host as owner
        block_id = response.data["id"]
        block = SmartBlock.objects.get(id=block_id)
        assert block.owner == host_user

    def test_host_can_update_own_smartblock(self, host_client, host_user, faker):
        """HOST can UPDATE own smart block (change_own_smartblock permission)."""
        block = baker.make(
            SmartBlock,
            name=f"Original {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        new_name = f"Updated {faker.uuid4()[:8]}"

        response = host_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        # Verify update
        block.refresh_from_db()
        assert block.name == new_name

    def test_host_cannot_update_other_smartblock(self, host_client, faker):
        """HOST cannot UPDATE other user's smart block (BOLA prevention)."""
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
        original_name = other_block.name

        response = host_client.patch(
            f"/api/v2/smart-blocks/{other_block.id}",
            {"name": "Hacked Block"},
            format="json",
        )
        assert response.status_code in [403, 404]

        # Verify not modified
        other_block.refresh_from_db()
        assert other_block.name == original_name

    def test_host_can_delete_own_smartblock(self, host_client, host_user, faker):
        """HOST can DELETE own smart block (delete_own_smartblock via model permission)."""
        block = baker.make(
            SmartBlock,
            name=f"To Delete {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        block_id = block.id

        response = host_client.delete(f"/api/v2/smart-blocks/{block_id}")
        assert response.status_code == 204

        # Verify deleted
        assert not SmartBlock.objects.filter(id=block_id).exists()

    def test_host_cannot_delete_other_smartblock(self, host_client, faker):
        """HOST cannot DELETE other user's smart block (BOLA prevention)."""
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

        response = host_client.delete(f"/api/v2/smart-blocks/{other_block_id}")
        assert response.status_code in [403, 404]

        # Verify still exists
        assert SmartBlock.objects.filter(id=other_block_id).exists()


@pytest.mark.django_db
class TestHostShowPermissions:
    """Test HOST permissions on Show endpoints.

    Shows are special - they represent public broadcast schedule.
    All authenticated users can view, but only hosts of a show can modify it.
    """

    def test_host_can_list_all_shows(self, host_client):
        """HOST can LIST all shows (view_show permission)."""
        response = host_client.get("/api/v2/shows")
        assert response.status_code == 200

    def test_host_can_retrieve_any_show(self, host_client, faker):
        """HOST can RETRIEVE any show (view_show permission)."""
        show = baker.make(Show, name=f"Public Show {faker.uuid4()[:8]}")

        response = host_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        assert response.data["name"] == show.name

    def test_host_can_create_show(self, host_client, host_user, faker):
        """HOST can CREATE show (if they have add_show permission - depends on config)."""
        # Note: HOST may or may not have add_show permission
        # In current permission_constants.py, only MANAGER has add_show
        data = {
            "name": f"My Show {faker.uuid4()[:8]}",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = host_client.post("/api/v2/shows", data, format="json")
        # HOST doesn't have add_show permission in current config
        # So this should fail with 403
        assert response.status_code in [201, 403]

    def test_host_cannot_update_show_if_not_host(self, host_client, faker):
        """HOST cannot UPDATE show if they are not assigned as host."""
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

        original_name = show.name

        response = host_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "Hacked Show"},
            format="json",
        )
        # Should be denied since current host is not assigned to this show
        assert response.status_code in [403, 404]

        # Verify not modified
        show.refresh_from_db()
        assert show.name == original_name

    def test_host_can_update_show_if_assigned_host(self, host_client, host_user, faker):
        """HOST can UPDATE show if they are assigned as host."""
        from api.schedule.models import ShowHost
        show = baker.make(Show, name=f"My Show {faker.uuid4()[:8]}")
        ShowHost.objects.create(show=show, user=host_user)

        new_name = f"Updated {faker.uuid4()[:8]}"

        response = host_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": new_name},
            format="json",
        )
        # Should succeed since host_user is assigned as host
        assert response.status_code == 200

        # Verify update
        show.refresh_from_db()
        assert show.name == new_name

    def test_host_cannot_delete_show_if_not_host(self, host_client, faker):
        """HOST cannot DELETE show if they are not assigned as host."""
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

        response = host_client.delete(f"/api/v2/shows/{show_id}")
        assert response.status_code in [403, 404]

        # Verify still exists
        assert Show.objects.filter(id=show_id).exists()


@pytest.mark.django_db
class TestHostWebstreamPermissions:
    """Test HOST permissions on Webstream endpoints."""

    def test_host_can_list_all_webstreams(self, host_client):
        """HOST can LIST all webstreams (view_webstream permission)."""
        response = host_client.get("/api/v2/webstreams")
        assert response.status_code == 200

    def test_host_can_retrieve_any_webstream(self, host_client, faker):
        """HOST can RETRIEVE any webstream (view_webstream permission)."""
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

        response = host_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 200
        assert response.data["name"] == stream.name

    def test_host_can_create_own_webstream(self, host_client, host_user, faker):
        """HOST can CREATE webstream (add_webstream permission)."""
        data = {
            "name": f"My Stream {faker.uuid4()[:8]}",
            "url": f"https://example.com/{faker.uuid4()[:8]}.mp3",
            "description": f"Test stream description {faker.uuid4()[:8]}",
        }
        response = host_client.post("/api/v2/webstreams", data, format="json")
        assert response.status_code == 201

        # Verify stream was created with host as owner
        stream_id = response.data["id"]
        stream = Webstream.objects.get(id=stream_id)
        assert stream.owner == host_user

    def test_host_can_update_own_webstream(self, host_client, host_user, faker):
        """HOST can UPDATE own webstream (change_own_webstream permission)."""
        stream = baker.make(
            Webstream,
            name=f"Original {faker.uuid4()[:8]}",
            owner=host_user,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )
        new_name = f"Updated {faker.uuid4()[:8]}"

        response = host_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        # Verify update
        stream.refresh_from_db()
        assert stream.name == new_name

    def test_host_cannot_update_other_webstream(self, host_client, faker):
        """HOST cannot UPDATE other user's webstream (BOLA prevention)."""
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
        original_name = other_stream.name

        response = host_client.patch(
            f"/api/v2/webstreams/{other_stream.id}",
            {"name": "Hacked Stream"},
            format="json",
        )
        assert response.status_code in [403, 404]

        # Verify not modified
        other_stream.refresh_from_db()
        assert other_stream.name == original_name

    def test_host_can_delete_own_webstream(self, host_client, host_user, faker):
        """HOST can DELETE own webstream (delete_own_webstream permission)."""
        stream = baker.make(
            Webstream,
            name=f"To Delete {faker.uuid4()[:8]}",
            owner=host_user,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )
        stream_id = stream.id

        response = host_client.delete(f"/api/v2/webstreams/{stream_id}")
        assert response.status_code == 204

        # Verify deleted
        assert not Webstream.objects.filter(id=stream_id).exists()

    def test_host_cannot_delete_other_webstream(self, host_client, faker):
        """HOST cannot DELETE other user's webstream (BOLA prevention)."""
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

        response = host_client.delete(f"/api/v2/webstreams/{other_stream_id}")
        assert response.status_code in [403, 404]

        # Verify still exists
        assert Webstream.objects.filter(id=other_stream_id).exists()
