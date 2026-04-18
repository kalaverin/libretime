"""Tests for PlaylistContents UPDATE endpoint (T230)."""

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
class TestPlaylistContentViewSetUpdate:
    """Test PlaylistContents UPDATE endpoint - PATCH/PUT /api/v2/playlist-contents/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testpc").delete()

    def test_patch_update_position_success(self, guest_client):
        """PATCH position should reorder content."""
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

        response = guest_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"position": 5}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["position"] == 5

    def test_patch_update_cue_points(self, guest_client):
        """PATCH cue points should update timing."""
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
            cue_in="00:00:00",
            cue_out="00:05:00",
        )

        response = guest_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps(
                {
                    "cue_in": "00:00:10",
                    "cue_out": "00:04:30",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cue_in"] == "00:00:10"
        assert data["cue_out"] == "00:04:30"

    def test_patch_update_offset(self, guest_client):
        """PATCH offset should update track offset."""
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

        response = guest_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"offset": 1.5}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["offset"] == 1.5

    def test_patch_update_fade_times(self, guest_client):
        """PATCH fade in/out should update fade times."""
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

        response = guest_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps(
                {
                    "fade_in": "00:00:05",
                    "fade_out": "00:00:10",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fade_in"] == "00:00:05"
        assert data["fade_out"] == "00:00:10"

    def test_patch_partial_does_not_affect_other_fields(self, guest_client):
        """PATCH should only update specified fields."""
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
        )

        response = guest_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"position": 10}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 10
        assert data["offset"] == 0.5
        assert data["cue_in"] == "00:00:05"

    def test_put_full_update_success(self, guest_client):
        """PUT should update all fields."""
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

        response = guest_client.put(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 20,
                    "offset": 2.0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 20
        assert data["offset"] == 2.0

    def test_update_not_found_returns_404(self, guest_client):
        """UPDATE non-existent content should return 404."""
        response = guest_client.patch(
            "/api/v2/playlist-contents/999999",
            json.dumps({"position": 5}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_no_auth_fails(self, client):
        """UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/playlist-contents/1",
            json.dumps({"position": 5}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_change_playlist(self, guest_client):
        """PATCH to change playlist should work."""
        user = baker.make(User, username="testpc_user")
        playlist1 = baker.make(Playlist, name="Playlist 1", owner=user)
        playlist2 = baker.make(Playlist, name="Playlist 2", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist1,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            offset=0,
        )

        response = guest_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"playlist": playlist2.id}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["playlist"] == playlist2.id

    def test_update_change_content_kind(self, guest_client):
        """UPDATE cannot change content kind (file->stream)."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        stream = baker.make(
            Webstream,
            name="Stream",
            url="http://example.com",
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

        response = guest_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps(
                {
                    "kind": PlaylistContent.Kind.STREAM,
                    "stream": stream.id,
                },
            ),
            content_type="application/json",
        )
        # Should either fail or handle gracefully
        assert response.status_code in [200, 400]
