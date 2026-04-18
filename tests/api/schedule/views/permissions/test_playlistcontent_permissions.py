"""Tests for PlaylistContents permissions (T233)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist, PlaylistContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistContentViewSetPermissions:
    """Test PlaylistContents permissions."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testpc").delete()

    # === AUTHENTICATION REQUIRED ===

    def test_list_requires_auth(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/playlist-contents")
        assert response.status_code == 403

    def test_retrieve_requires_auth(self, client):
        """RETRIEVE without auth should return 403."""
        response = client.get("/api/v2/playlist-contents/1")
        assert response.status_code == 403

    def test_create_requires_auth(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/playlist-contents",
            json.dumps({"kind": 0}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_requires_auth(self, client):
        """UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/playlist-contents/1",
            json.dumps({"position": 5}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_requires_auth(self, client):
        """DELETE without auth should return 403."""
        response = client.delete("/api/v2/playlist-contents/1")
        assert response.status_code == 403

    # === AUTHORIZED USERS CAN ACCESS ===

    def test_list_with_auth_returns_200(self, admin_client):
        """LIST with auth should return 200."""
        response = admin_client.get("/api/v2/playlist-contents")
        assert response.status_code == 200

    def test_retrieve_with_auth_returns_200(self, admin_client):
        """RETRIEVE with auth should return 200."""
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
        assert response.status_code == 200

    def test_create_with_auth_returns_201(self, admin_client):
        """CREATE with auth should return 201."""
        user = baker.make(User, username="testpc_user")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = admin_client.post(
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

    def test_update_with_auth_returns_200(self, admin_client):
        """UPDATE with auth should return 200."""
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
        response = admin_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"position": 5}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_delete_with_auth_returns_204(self, admin_client):
        """DELETE with auth should return 204."""
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
        response = admin_client.delete(f"/api/v2/playlist-contents/{content.id}")
        assert response.status_code == 204

    # === CROSS-USER ACCESS ===

    def test_user_can_view_other_users_content(self, admin_client):
        """Any authenticated user can view any content."""
        other_user = baker.make(User, username="testpc_other")
        playlist = baker.make(
            Playlist,
            name="Other Playlist",
            owner=other_user,
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=other_user,
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
        assert response.status_code == 200
        assert response.json()["id"] == content.id
