"""Tests for PlaylistContents LIST endpoint (T228)."""

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
class TestPlaylistContentViewSetList:
    """Test PlaylistContents LIST endpoint - GET /api/v2/playlist-contents."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testpc").delete()

    def test_list_empty_returns_200(self, api_client):
        """LIST empty should return 200 with empty list."""
        response = api_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_file_content(self, api_client):
        """LIST should return file content with correct fields."""
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
        )

        response = api_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["kind"] == PlaylistContent.Kind.FILE
        assert data[0]["file"] == file_obj.id
        assert data[0]["playlist"] == playlist.id
        assert data[0]["position"] == 1

    def test_list_single_stream_content(self, api_client):
        """LIST should return stream content with correct fields."""
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
            position=1,
        )

        response = api_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["kind"] == PlaylistContent.Kind.STREAM
        assert data[0]["stream"] == stream.id

    def test_list_single_block_content(self, api_client):
        """LIST should return block content with correct fields."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        block = baker.make(SmartBlock, name="Test Block", owner=user)

        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.BLOCK,
            block=block,
            position=1,
        )

        response = api_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["kind"] == PlaylistContent.Kind.BLOCK
        assert data[0]["block"] == block.id

    def test_list_multiple_contents(self, api_client):
        """LIST should return multiple contents."""
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

        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file1,
            position=1,
        )
        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file2,
            position=2,
        )

        response = api_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_filter_by_playlist(self, api_client):
        """LIST should filter by playlist parameter."""
        user = baker.make(User, username="testpc_user")
        playlist1 = baker.make(Playlist, name="Playlist 1", owner=user)
        playlist2 = baker.make(Playlist, name="Playlist 2", owner=user)
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

        baker.make(
            PlaylistContent,
            playlist=playlist1,
            kind=PlaylistContent.Kind.FILE,
            file=file1,
            position=1,
        )
        baker.make(
            PlaylistContent,
            playlist=playlist2,
            kind=PlaylistContent.Kind.FILE,
            file=file2,
            position=1,
        )

        response = api_client.get(
            f"/api/v2/playlist-contents?playlist={playlist1.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["playlist"] == playlist1.id

    def test_list_contents_ordered_by_position(self, api_client):
        """LIST should be ordered by position."""
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

        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file1,
            position=3,
        )
        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file2,
            position=1,
        )
        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file3,
            position=2,
        )

        response = api_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200
        positions = [item["position"] for item in response.json()]
        assert positions == [1, 2, 3]

    def test_list_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/playlist-contents")
        assert response.status_code == 403

    def test_list_returns_all_fields(self, api_client):
        """LIST should return all serializer fields."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            offset=0.5,
            cue_in="00:00:05",
            cue_out="00:03:30",
        )

        response = api_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200
        data = response.json()[0]
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

    def test_list_null_relations_for_different_kinds(self, api_client):
        """LIST should show null for unused relations based on kind."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            stream=None,
            block=None,
            position=1,
        )

        response = api_client.get("/api/v2/playlist-contents")
        data = response.json()[0]
        assert data["file"] == file_obj.id
        assert data["stream"] is None
        assert data["block"] is None
