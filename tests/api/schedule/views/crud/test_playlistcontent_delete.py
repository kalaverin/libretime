"""Tests for PlaylistContents DELETE endpoint (T231)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist, PlaylistContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistContentViewSetDelete:
    """Test PlaylistContents DELETE endpoint - DELETE /api/v2/playlist-contents/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testpc").delete()

    def test_delete_content_success_returns_204(self, guest_client):
        """DELETE should return 204 on success."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            offset=0,
        )

        response = guest_client.delete(f"/api/v2/playlist-contents/{content.id}")
        assert response.status_code == 204

    def test_delete_content_removes_from_db(self, guest_client):
        """DELETE should remove content from database."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            offset=0,
        )

        guest_client.delete(f"/api/v2/playlist-contents/{content.id}")
        assert PlaylistContent.objects.filter(id=content.id).count() == 0

    def test_delete_not_found_returns_404(self, guest_client):
        """DELETE non-existent content should return 404."""
        response = guest_client.delete("/api/v2/playlist-contents/999999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        response = client.delete("/api/v2/playlist-contents/1")
        assert response.status_code == 403

    def test_delete_double_delete_returns_404(self, guest_client):
        """DELETE already deleted content should return 404."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            offset=0,
        )

        guest_client.delete(f"/api/v2/playlist-contents/{content.id}")
        response = guest_client.delete(f"/api/v2/playlist-contents/{content.id}")
        assert response.status_code == 404

    def test_delete_one_content_others_remain(self, guest_client):
        """DELETE one content should leave others."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file1 = baker.make(
            File,
            name="file1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="file2.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file3 = baker.make(
            File,
            name="file3.mp3",
            mime="audio/mp3",
            owner=user,
        )

        content1 = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file1,
            position=1,
            offset=0,
        )
        content2 = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file2,
            position=2,
            offset=0,
        )
        content3 = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file3,
            position=3,
            offset=0,
        )

        guest_client.delete(f"/api/v2/playlist-contents/{content2.id}")

        assert PlaylistContent.objects.filter(id=content1.id).exists()
        assert not PlaylistContent.objects.filter(id=content2.id).exists()
        assert PlaylistContent.objects.filter(id=content3.id).exists()

    def test_delete_returns_empty_body(self, guest_client):
        """DELETE should return empty response body."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            offset=0,
        )

        response = guest_client.delete(f"/api/v2/playlist-contents/{content.id}")
        assert response.content == b""

    def test_delete_id_zero_returns_404(self, guest_client):
        """DELETE with id=0 should return 404."""
        response = guest_client.delete("/api/v2/playlist-contents/0")
        assert response.status_code == 404

    def test_delete_negative_id_returns_404(self, guest_client):
        """DELETE with negative id should return 404."""
        response = guest_client.delete("/api/v2/playlist-contents/-1")
        assert response.status_code == 404

    def test_delete_sql_injection_attempt(self, guest_client):
        """DELETE with SQL injection in id should be handled safely."""
        response = guest_client.delete("/api/v2/playlist-contents/1 OR 1=1")
        assert response.status_code == 404
