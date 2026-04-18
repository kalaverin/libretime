"""Tests for PlaylistContents RETRIEVE endpoint (T232)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import (
    Playlist,
    PlaylistContent,
    SmartBlock,
    Webstream,
)
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistContentViewSetRetrieve:
    """Test PlaylistContents RETRIEVE endpoint - GET /api/v2/playlist-contents/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testpc").delete()

    def test_retrieve_file_content_success(self, admin_client):
        """RETRIEVE file content should return 200 with all fields."""
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
            offset=0.5,
            cue_in="00:00:05",
            cue_out="00:03:30",
            fade_in="00:00:02",
            fade_out="00:00:03",
        )

        response = admin_client.get(f"/api/v2/playlist-contents/{content.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content.id
        assert data["kind"] == PlaylistContent.Kind.FILE
        assert data["file"] == file_obj.id
        assert data["playlist"] == playlist.id
        assert data["position"] == 1
        assert data["offset"] == 0.5
        assert data["cue_in"] == "00:00:05"
        assert data["cue_out"] == "00:03:30"
        assert data["fade_in"] == "00:00:02"
        assert data["fade_out"] == "00:00:03"

    def test_retrieve_stream_content_success(self, admin_client):
        """RETRIEVE stream content should return 200."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.STREAM,
            stream=stream,
            position=2,
            offset=0,
        )

        response = admin_client.get(f"/api/v2/playlist-contents/{content.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == PlaylistContent.Kind.STREAM
        assert data["stream"] == stream.id
        assert data["file"] is None
        assert data["block"] is None

    def test_retrieve_block_content_success(self, admin_client):
        """RETRIEVE block content should return 200."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        block = baker.make(SmartBlock, name="Test Block", owner=user)
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.BLOCK,
            block=block,
            position=3,
            offset=0,
        )

        response = admin_client.get(f"/api/v2/playlist-contents/{content.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == PlaylistContent.Kind.BLOCK
        assert data["block"] == block.id
        assert data["file"] is None
        assert data["stream"] is None

    def test_retrieve_not_found_returns_404(self, admin_client):
        """RETRIEVE non-existent content should return 404."""
        response = admin_client.get("/api/v2/playlist-contents/999999")
        assert response.status_code == 404

    def test_retrieve_no_auth_fails(self, client):
        """RETRIEVE without auth should return 403."""
        response = client.get("/api/v2/playlist-contents/1")
        assert response.status_code == 403

    def test_retrieve_returns_all_fields(self, admin_client):
        """RETRIEVE should return all serializer fields."""
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

        response = admin_client.get(f"/api/v2/playlist-contents/{content.id}")
        data = response.json()
        expected_fields = {
            "id",
            "playlist",
            "kind",
            "file",
            "stream",
            "block",
            "position",
            "offset",
            "length",
            "cue_in",
            "cue_out",
            "fade_in",
            "fade_out",
        }
        assert set(data.keys()) == expected_fields

    def test_retrieve_id_zero_returns_404(self, admin_client):
        """RETRIEVE with id=0 should return 404."""
        response = admin_client.get("/api/v2/playlist-contents/0")
        assert response.status_code == 404

    def test_retrieve_negative_id_returns_404(self, admin_client):
        """RETRIEVE with negative id should return 404."""
        response = admin_client.get("/api/v2/playlist-contents/-1")
        assert response.status_code == 404

    def test_retrieve_sql_injection_attempt(self, admin_client):
        """RETRIEVE with SQL injection in id should be handled safely."""
        response = admin_client.get("/api/v2/playlist-contents/1 OR 1=1")
        assert response.status_code == 404
