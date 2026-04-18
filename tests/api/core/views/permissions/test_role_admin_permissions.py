"""
ADMIN Role Permissions Tests (Role.ADMIN / "A")

ADMIN users are superusers with full system access.
They have all permissions including user management.
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Playlist, Show, SmartBlock
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestAdminPlaylistPermissions:
    """Test ADMIN permissions on Playlist endpoints."""

    def test_admin_can_list_all_playlists(self, admin_client):
        """ADMIN can LIST all playlists."""
        response = admin_client.get("/api/v2/playlists")
        assert response.status_code == 200

    def test_admin_can_retrieve_any_playlist(self, admin_client, faker):
        """ADMIN can RETRIEVE any playlist."""
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

        response = admin_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["name"] == playlist.name

    def test_admin_can_create_playlist(self, admin_client, admin_user, faker):
        """ADMIN can CREATE playlist."""
        data = {
            "name": f"Admin Playlist {faker.uuid4()[:8]}",
        }
        response = admin_client.post("/api/v2/playlists", data, format="json")
        assert response.status_code == 201

        playlist_id = response.data["id"]
        playlist = Playlist.objects.get(id=playlist_id)
        assert playlist.owner == admin_user

    def test_admin_can_update_any_playlist(self, admin_client, faker):
        """ADMIN can UPDATE ANY playlist."""
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
        new_name = f"Updated by Admin {faker.uuid4()[:8]}"

        response = admin_client.patch(
            f"/api/v2/playlists/{other_playlist.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        other_playlist.refresh_from_db()
        assert other_playlist.name == new_name

    def test_admin_can_delete_any_playlist(self, admin_client, faker):
        """ADMIN can DELETE ANY playlist."""
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

        response = admin_client.delete(
            f"/api/v2/playlists/{other_playlist_id}",
        )
        assert response.status_code == 204

        assert not Playlist.objects.filter(id=other_playlist_id).exists()


@pytest.mark.django_db
class TestAdminFilePermissions:
    """Test ADMIN permissions on File endpoints."""

    def test_admin_can_list_all_files(self, admin_client):
        """ADMIN can LIST all files."""
        response = admin_client.get("/api/v2/files")
        assert response.status_code == 200

    def test_admin_can_retrieve_any_file(self, admin_client, faker):
        """ADMIN can RETRIEVE any file."""
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

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200

    def test_admin_can_create_file(self, admin_client, admin_user, faker):
        """ADMIN can CREATE file."""
        data = {
            "name": f"admin_file_{faker.uuid4()[:8]}.mp3",
            "mime": "audio/mpeg",
            "size": 1024,
            "accessed": int(now().timestamp()),
        }
        response = admin_client.post("/api/v2/files", data, format="json")
        assert response.status_code == 201

    def test_admin_can_update_any_file(self, admin_client, faker):
        """ADMIN can UPDATE ANY file."""
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
        new_name = f"admin_updated_{faker.uuid4()[:8]}.mp3"

        response = admin_client.patch(
            f"/api/v2/files/{other_file.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        other_file.refresh_from_db()
        assert other_file.name == new_name

    def test_admin_cannot_delete_file(self, admin_client, faker):
        """ADMIN cannot DELETE file - file deletion is not allowed (409)."""
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

        response = admin_client.delete(f"/api/v2/files/{other_file_id}")
        # File deletion is not allowed for anyone (409 Conflict)
        assert response.status_code == 409

        # Verify file was NOT deleted
        assert File.objects.filter(id=other_file_id).exists()


@pytest.mark.django_db
class TestAdminSmartBlockPermissions:
    """Test ADMIN permissions on SmartBlock endpoints."""

    def test_admin_can_list_all_smartblocks(self, admin_client):
        """ADMIN can LIST all smart blocks."""
        response = admin_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200

    def test_admin_can_retrieve_any_smartblock(self, admin_client, faker):
        """ADMIN can RETRIEVE any smart block."""
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

        response = admin_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200

    def test_admin_can_create_smartblock(
        self, admin_client, admin_user, faker,
    ):
        """ADMIN can CREATE smart block."""
        data = {
            "name": f"Admin Block {faker.uuid4()[:8]}",
            "kind": "dynamic",
        }
        response = admin_client.post(
            "/api/v2/smart-blocks", data, format="json",
        )
        assert response.status_code == 201

    def test_admin_can_update_any_smartblock(self, admin_client, faker):
        """ADMIN can UPDATE ANY smart block."""
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
        new_name = f"Admin Updated {faker.uuid4()[:8]}"

        response = admin_client.patch(
            f"/api/v2/smart-blocks/{other_block.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        other_block.refresh_from_db()
        assert other_block.name == new_name

    def test_admin_can_delete_any_smartblock(self, admin_client, faker):
        """ADMIN can DELETE ANY smart block."""
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

        response = admin_client.delete(
            f"/api/v2/smart-blocks/{other_block_id}",
        )
        assert response.status_code == 204

        assert not SmartBlock.objects.filter(id=other_block_id).exists()


@pytest.mark.django_db
class TestAdminShowPermissions:
    """Test ADMIN permissions on Show endpoints."""

    def test_admin_can_list_all_shows(self, admin_client):
        """ADMIN can LIST all shows."""
        response = admin_client.get("/api/v2/shows")
        assert response.status_code == 200

    def test_admin_can_retrieve_any_show(self, admin_client, faker):
        """ADMIN can RETRIEVE any show."""
        show = baker.make(Show, name=f"Show {faker.uuid4()[:8]}")

        response = admin_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200

    def test_admin_can_create_show(self, admin_client, admin_user, faker):
        """ADMIN can CREATE show."""
        data = {
            "name": f"Admin Show {faker.uuid4()[:8]}",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = admin_client.post("/api/v2/shows", data, format="json")
        assert response.status_code == 201

    def test_admin_can_update_any_show(self, admin_client, faker):
        """ADMIN can UPDATE ANY show."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        from api.schedule.models import ShowHost

        show = baker.make(Show, name=f"Other Show {faker.uuid4()[:8]}")
        ShowHost.objects.create(show=show, user=other_host)

        new_name = f"Admin Updated {faker.uuid4()[:8]}"

        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200

        show.refresh_from_db()
        assert show.name == new_name

    def test_admin_can_delete_any_show(self, admin_client, faker):
        """ADMIN can DELETE ANY show."""
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

        response = admin_client.delete(f"/api/v2/shows/{show_id}")
        assert response.status_code == 204

        assert not Show.objects.filter(id=show_id).exists()


@pytest.mark.django_db
class TestAdminUserManagementPermissions:
    """Test ADMIN user management permissions (IsAdminOrOwnUser)."""

    def test_admin_can_list_all_users(self, admin_client):
        """ADMIN can LIST all users."""
        response = admin_client.get("/api/v2/users")
        assert response.status_code == 200

    def test_admin_can_retrieve_any_user(self, admin_client, faker):
        """ADMIN can RETRIEVE any user."""
        other_user = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )

        response = admin_client.get(f"/api/v2/users/{other_user.id}")
        assert response.status_code == 200
        assert response.data["username"] == other_user.username

    def test_admin_can_create_user(self, admin_client, faker):
        """ADMIN can CREATE new users."""
        data = {
            "username": f"newuser_{faker.uuid4()[:8]}",
            "email": f"new_{faker.uuid4()[:8]}@test.com",
            "first_name": faker.first_name(),
            "last_name": faker.last_name(),
            "role": "H",
            "password": "SecurePass123!",
        }
        response = admin_client.post("/api/v2/users", data, format="json")
        assert response.status_code == 201

    def test_admin_can_update_any_user(self, admin_client, faker):
        """ADMIN can UPDATE ANY user."""
        other_user = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            first_name="Original",
            role=Role.HOST,
        )
        new_first_name = f"Updated{faker.uuid4()[:8]}"

        response = admin_client.patch(
            f"/api/v2/users/{other_user.id}",
            {"first_name": new_first_name},
            format="json",
        )
        assert response.status_code == 200

        other_user.refresh_from_db()
        assert other_user.first_name == new_first_name

    def test_admin_can_delete_any_user(self, admin_client, faker):
        """ADMIN can DELETE ANY user."""
        other_user = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_user_id = other_user.id

        response = admin_client.delete(f"/api/v2/users/{other_user_id}")
        assert response.status_code == 204

        assert not User.objects.filter(id=other_user_id).exists()
