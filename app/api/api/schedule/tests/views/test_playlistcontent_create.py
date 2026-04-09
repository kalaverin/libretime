"""Tests for PlaylistContents CREATE endpoint (T229)."""

import json

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
class TestPlaylistContentViewSetCreate:
    """Test PlaylistContents CREATE endpoint - POST /api/v2/playlist-contents."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testpc").delete()

    def test_create_file_content_success(self, api_client):
        """CREATE file content should return 201."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == PlaylistContent.Kind.FILE
        assert data["file"] == file_obj.id
        assert data["playlist"] == playlist.id

    def test_create_stream_content_success(self, api_client):
        """CREATE stream content should return 201."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.STREAM,
                    "stream": stream.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == PlaylistContent.Kind.STREAM
        assert data["stream"] == stream.id

    def test_create_block_content_success(self, api_client):
        """CREATE block content should return 201."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        block = baker.make(SmartBlock, name="Test Block", owner=user)

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.BLOCK,
                    "block": block.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == PlaylistContent.Kind.BLOCK
        assert data["block"] == block.id

    def test_create_without_position_uses_null(self, api_client):
        """CREATE without position should default to null."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["position"] is None

    def test_create_with_cue_points(self, api_client):
        """CREATE with cue_in/cue_out should succeed."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                    "cue_in": "00:00:05",
                    "cue_out": "00:03:30",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cue_in"] == "00:00:05"
        assert data["cue_out"] == "00:03:30"

    def test_create_with_offset(self, api_client):
        """CREATE with offset should succeed."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0.5,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["offset"] == 0.5

    def test_create_with_fade_in_out(self, api_client):
        """CREATE with fade_in/fade_out should succeed."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                    "fade_in": "00:00:02",
                    "fade_out": "00:00:03",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["fade_in"] == "00:00:02"
        assert data["fade_out"] == "00:00:03"

    @pytest.mark.xfail(
        reason="T325: missing playlist not validated, returns 201",
    )
    def test_create_missing_playlist_fails(self, api_client):
        """CREATE without playlist should return 400."""
        user = baker.make(User, username="testpc_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_missing_kind_fails(self, api_client):
        """CREATE without kind should return 400."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.xfail(
        reason="T326: FILE kind without file not validated, returns 201",
    )
    def test_create_file_without_file_id_fails(self, api_client):
        """CREATE FILE kind without file ID should return 400."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_invalid_playlist_fails(self, api_client):
        """CREATE with non-existent playlist should return 400."""
        user = baker.make(User, username="testpc_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": 999999,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_invalid_file_fails(self, api_client):
        """CREATE with non-existent file should return 400."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": 999999,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/playlist-contents",
            json.dumps({"kind": 0}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_unicode_in_metadata(self, api_client):
        """CREATE with unicode should succeed."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
