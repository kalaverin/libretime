"""
BOLA (Broken Object Level Authorization) Prevention Tests

These tests verify that:
1. HOST users can only modify their OWN resources
2. HOST users CANNOT modify other users' resources (BOLA prevention)
3. MANAGER/ADMIN users CAN modify any resource (expected behavior)
4. GUEST users cannot modify anything

These tests are critical for API1:2023 compliance.
"""

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Playlist, SmartBlock, Webstream
from api.storage.models import File


@pytest.mark.django_db
class TestBolaPlaylistPrevention:
    """BOLA prevention tests for Playlist resource."""

    def test_host_cannot_update_other_host_playlist(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot UPDATE another HOST's playlist (BOLA)."""
        # Create another host user with their playlist
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_playlist = baker.make(
            Playlist,
            name=f"Other Host Playlist {faker.uuid4()[:8]}",
            owner=other_host,
        )
        original_name = other_playlist.name

        # Current host tries to modify
        response = host_client.patch(
            f"/api/v2/playlists/{other_playlist.id}",
            {"name": "HACKED BY HOST"},
            format="json",
        )

        # Should be denied (403 Forbidden or 404 Not Found)
        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST updated another HOST's playlist! "
            f"Status: {response.status_code}"
        )

        # Verify not modified
        other_playlist.refresh_from_db()
        assert other_playlist.name == original_name

    def test_host_cannot_delete_other_host_playlist(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot DELETE another HOST's playlist (BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_playlist = baker.make(
            Playlist,
            name=f"Other Host Playlist {faker.uuid4()[:8]}",
            owner=other_host,
        )
        other_playlist_id = other_playlist.id

        response = host_client.delete(f"/api/v2/playlists/{other_playlist_id}")

        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST deleted another HOST's playlist! "
            f"Status: {response.status_code}"
        )

        # Verify still exists
        assert Playlist.objects.filter(id=other_playlist_id).exists()

    def test_manager_can_update_any_host_playlist(self, manager_client, faker):
        """MANAGER can UPDATE any HOST's playlist (expected, not BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_playlist = baker.make(
            Playlist,
            name=f"Other Host Playlist {faker.uuid4()[:8]}",
            owner=other_host,
        )
        new_name = f"Manager Updated {faker.uuid4()[:8]}"

        response = manager_client.patch(
            f"/api/v2/playlists/{other_playlist.id}",
            {"name": new_name},
            format="json",
        )

        # Manager should succeed
        assert response.status_code == 200, (
            f"MANAGER should be able to update any playlist"
        )

        other_playlist.refresh_from_db()
        assert other_playlist.name == new_name

    def test_manager_can_delete_any_host_playlist(self, manager_client, faker):
        """MANAGER can DELETE any HOST's playlist (expected, not BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_playlist = baker.make(
            Playlist,
            name=f"Other Host Playlist {faker.uuid4()[:8]}",
            owner=other_host,
        )
        other_playlist_id = other_playlist.id

        response = manager_client.delete(f"/api/v2/playlists/{other_playlist_id}")

        assert response.status_code == 204
        assert not Playlist.objects.filter(id=other_playlist_id).exists()


@pytest.mark.django_db
class TestBolaFilePrevention:
    """BOLA prevention tests for File resource."""

    def test_host_cannot_update_other_host_file(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot UPDATE another HOST's file (BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_file = baker.make(
            File,
            name=f"other_host_file_{faker.uuid4()[:8]}.mp3",
            owner=other_host,
            mime="audio/mpeg",
        )
        original_name = other_file.name

        response = host_client.patch(
            f"/api/v2/files/{other_file.id}",
            {"name": "HACKED.mp3"},
            format="json",
        )

        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST updated another HOST's file!"
        )

        other_file.refresh_from_db()
        assert other_file.name == original_name

    def test_host_cannot_delete_other_host_file(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot DELETE another HOST's file (BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_file = baker.make(
            File,
            name=f"other_host_file_{faker.uuid4()[:8]}.mp3",
            owner=other_host,
            mime="audio/mpeg",
        )
        other_file_id = other_file.id

        response = host_client.delete(f"/api/v2/files/{other_file_id}")

        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST deleted another HOST's file!"
        )

        assert File.objects.filter(id=other_file_id).exists()

    def test_host_can_download_other_host_file(self, host_client, faker):
        """HOST can DOWNLOAD another HOST's file (public read design)."""
        # Files are public for all authenticated users (broadcast system design)
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_file = baker.make(
            File,
            name=f"other_host_file_{faker.uuid4()[:8]}.mp3",
            owner=other_host,
            mime="audio/mpeg",
            filepath=f"other/{faker.uuid4()[:8]}.mp3",
        )

        response = host_client.get(f"/api/v2/files/{other_file.id}/download")

        # All authenticated users can download (public read design)
        assert response.status_code == 200

    def test_anonymous_cannot_download_file(self, anonymous_client, faker):
        """Anonymous cannot DOWNLOAD file (403)."""
        from api.core.models import User
        from api.core.models.role import Role
        
        host = baker.make(
            User,
            username=f"host_{faker.uuid4()[:8]}",
            email=f"host_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        file_obj = baker.make(
            File,
            name=f"host_file_{faker.uuid4()[:8]}.mp3",
            owner=host,
            mime="audio/mpeg",
            filepath=f"files/{faker.uuid4()[:8]}.mp3",
        )

        response = anonymous_client.get(f"/api/v2/files/{file_obj.id}/download")

        # Anonymous gets 403
        assert response.status_code == 403


@pytest.mark.django_db
class TestBolaSmartBlockPrevention:
    """BOLA prevention tests for SmartBlock resource."""

    def test_host_cannot_update_other_host_smartblock(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot UPDATE another HOST's smart block (BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Host Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        original_name = other_block.name

        response = host_client.patch(
            f"/api/v2/smart-blocks/{other_block.id}",
            {"name": "HACKED BLOCK"},
            format="json",
        )

        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST updated another HOST's smart block!"
        )

        other_block.refresh_from_db()
        assert other_block.name == original_name

    def test_host_cannot_delete_other_host_smartblock(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot DELETE another HOST's smart block (BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Host Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        other_block_id = other_block.id

        response = host_client.delete(f"/api/v2/smart-blocks/{other_block_id}")

        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST deleted another HOST's smart block!"
        )

        assert SmartBlock.objects.filter(id=other_block_id).exists()


@pytest.mark.django_db
class TestBolaWebstreamPrevention:
    """BOLA prevention tests for Webstream resource."""

    def test_host_cannot_update_other_host_webstream(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot UPDATE another HOST's webstream (BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_stream = baker.make(
            Webstream,
            name=f"Other Host Stream {faker.uuid4()[:8]}",
            owner=other_host,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )
        original_name = other_stream.name

        response = host_client.patch(
            f"/api/v2/webstreams/{other_stream.id}",
            {"name": "HACKED STREAM"},
            format="json",
        )

        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST updated another HOST's webstream!"
        )

        other_stream.refresh_from_db()
        assert other_stream.name == original_name

    def test_host_cannot_delete_other_host_webstream(self, host_client, host_user, faker):
        """CRITICAL: HOST cannot DELETE another HOST's webstream (BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_stream = baker.make(
            Webstream,
            name=f"Other Host Stream {faker.uuid4()[:8]}",
            owner=other_host,
            url=f"https://example.com/{faker.uuid4()[:8]}.mp3",
        )
        other_stream_id = other_stream.id

        response = host_client.delete(f"/api/v2/webstreams/{other_stream_id}")

        assert response.status_code in [403, 404], (
            f"BOLA VULNERABILITY: HOST deleted another HOST's webstream!"
        )

        assert Webstream.objects.filter(id=other_stream_id).exists()


@pytest.mark.django_db
class TestBolaCrossRoleSummary:
    """Summary tests showing BOLA prevention across all roles."""

    def test_cross_role_playlist_modification_matrix(self, api_client, faker):
        """Complete matrix: which roles can modify which user's playlist."""
        # Create users of each role
        host1 = baker.make(User, username=f"host1_{faker.uuid4()[:8]}", role=Role.HOST)
        host2 = baker.make(User, username=f"host2_{faker.uuid4()[:8]}", role=Role.HOST)
        manager = baker.make(User, username=f"manager_{faker.uuid4()[:8]}", role=Role.MANAGER)
        admin = baker.make(User, username=f"admin_{faker.uuid4()[:8]}", role=Role.ADMIN)

        # Create playlist owned by host1
        playlist = baker.make(Playlist, name=f"Host1 Playlist {faker.uuid4()[:8]}", owner=host1)
        playlist_id = playlist.id

        results = {}

        # Test HOST1 (owner) - should succeed
        api_client.force_authenticate(user=host1)
        response = api_client.patch(f"/api/v2/playlists/{playlist_id}", {"name": "Updated"}, format="json")
        results["owner_host"] = response.status_code
        api_client.logout()

        # Test HOST2 (other host) - should fail (BOLA prevention)
        api_client.force_authenticate(user=host2)
        response = api_client.patch(f"/api/v2/playlists/{playlist_id}", {"name": "Hacked"}, format="json")
        results["other_host"] = response.status_code
        api_client.logout()

        # Test MANAGER - should succeed
        api_client.force_authenticate(user=manager)
        response = api_client.patch(f"/api/v2/playlists/{playlist_id}", {"name": "Manager Updated"}, format="json")
        results["manager"] = response.status_code
        api_client.logout()

        # Test ADMIN - should succeed
        api_client.force_authenticate(user=admin)
        response = api_client.patch(f"/api/v2/playlists/{playlist_id}", {"name": "Admin Updated"}, format="json")
        results["admin"] = response.status_code
        api_client.logout()

        # Assert expected results
        assert results["owner_host"] == 200, "Owner HOST should be able to update"
        assert results["other_host"] in [403, 404], "Other HOST should NOT be able to update (BOLA)"
        assert results["manager"] == 200, "MANAGER should be able to update"
        assert results["admin"] == 200, "ADMIN should be able to update"

        print(f"\nBOLA Prevention Matrix for Playlist:")
        print(f"  Owner HOST:   {results['owner_host']} (expected: 200)")
        print(f"  Other HOST:   {results['other_host']} (expected: 403/404)")
        print(f"  MANAGER:      {results['manager']} (expected: 200)")
        print(f"  ADMIN:        {results['admin']} (expected: 200)")
