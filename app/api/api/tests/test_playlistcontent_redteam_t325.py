"""
RED TEAM: T325/T326 - PlaylistContent validation security tests.

Attack vectors:
- Mass assignment via __all__
- Null injection for required fields
- Missing validation for STREAM kind
- BOLA: access other users' playlist content
- Query param injection in filter
"""


import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestPlaylistContentMassAssignment:
    """Mass assignment attacks via __all__."""

    def test_create_with_id_field(self, api_client, admin_user):
        """Try to set id field during creation."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "id": 99999,
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": 0,  # FILE = 0
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should not allow setting id
        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.fail(
                    "BUG: Can set id field during creation (mass assignment)",
                )

    def test_create_with_created_at(self, api_client, admin_user):
        """Try to set created_at during creation."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": 0,  # FILE = 0
                "position": 1,
                "offset": 0,
                "created_at": "2019-01-01T00:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("created_at") and "2019" in data.get("created_at", ""):
                pytest.fail("BUG: Can set created_at field (mass assignment)")

    def test_update_playlist_field(self, api_client, admin_user):
        """Try to change playlist via PATCH."""
        playlist1 = baker.make("schedule.Playlist", owner=admin_user)
        playlist2 = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)
        content = baker.make(
            "schedule.PlaylistContent",
            playlist=playlist1,
            file=file_obj,
            kind=0,  # FILE = 0
            position=1,
            offset=0,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/playlist-contents/{content.id}/",
            {"playlist": playlist2.id},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("playlist") == playlist2.id:
                pytest.fail(
                    "BUG: Can transfer content to another playlist via PATCH",
                )


@pytest.mark.django_db
class TestPlaylistContentNullInjection:
    """Null injection for required fields."""

    def test_create_with_null_playlist(self, api_client, admin_user):
        """Try to create with null playlist."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": None,
                "file": file_obj.id,
                "kind": 0,  # FILE = 0
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should reject null playlist
        if response.status_code == 201:
            pytest.fail("BUG: Accepts null playlist despite required=True")

    def test_create_with_null_file_for_file_kind(self, api_client, admin_user):
        """Try to create FILE kind with null file."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": None,
                "kind": 0,  # FILE = 0
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should reject null file for FILE kind
        if response.status_code == 201:
            pytest.fail("BUG: Accepts null file for FILE kind")

    def test_create_with_null_kind(self, api_client, admin_user):
        """Try to create with null kind."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": None,
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should reject null kind
        if response.status_code == 201:
            pytest.fail("BUG: Accepts null kind field")


@pytest.mark.django_db
class TestPlaylistContentStreamKindValidation:
    """Missing validation for STREAM kind."""

    def test_create_stream_kind_without_stream(self, api_client, admin_user):
        """Try to create STREAM kind without stream."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "kind": 1,  # STREAM = 1
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should require stream for STREAM kind
        if response.status_code == 201:
            pytest.fail(
                "BUG: Accepts STREAM kind without stream field (incomplete validation)",
            )

    def test_create_stream_kind_with_file_instead(
        self, api_client, admin_user,
    ):
        """Try to create STREAM kind but provide file instead of stream."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": 1,  # STREAM = 1
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should reject - STREAM kind should have stream, not file
        if response.status_code == 201:
            pytest.fail(
                "BUG: Accepts STREAM kind with file field (wrong media type)",
            )


@pytest.mark.django_db
class TestPlaylistContentBOLA:
    """Broken Object Level Authorization attacks."""

    def test_list_shows_only_own_content(
        self, api_client, admin_user, regular_user,
    ):
        """Verify list returns only user's own content."""
        # Create playlists and content for both users
        admin_playlist = baker.make("schedule.Playlist", owner=admin_user)
        user_playlist = baker.make("schedule.Playlist", owner=regular_user)

        admin_file = baker.make("storage.File", owner=admin_user)
        user_file = baker.make("storage.File", owner=regular_user)

        admin_content = baker.make(
            "schedule.PlaylistContent",
            playlist=admin_playlist,
            file=admin_file,
            kind=0,  # FILE = 0
            position=1,
            offset=0,
        )
        user_content = baker.make(
            "schedule.PlaylistContent",
            playlist=user_playlist,
            file=user_file,
            kind=0,  # FILE = 0
            position=1,
            offset=0,
        )

        # User lists content
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/playlist-contents/")

        assert response.status_code == 200
        data = response.json()

        content_ids = [c["id"] for c in data]
        assert user_content.id in content_ids

        if admin_content.id in content_ids:
            pytest.fail("CRITICAL BUG: List shows other users' content (BOLA)")

    def test_access_other_user_content_directly(
        self, api_client, admin_user, regular_user,
    ):
        """Try to access another user's content by ID."""
        admin_playlist = baker.make("schedule.Playlist", owner=admin_user)
        admin_file = baker.make("storage.File", owner=admin_user)
        admin_content = baker.make(
            "schedule.PlaylistContent",
            playlist=admin_playlist,
            file=admin_file,
            kind=0,  # FILE = 0
            position=1,
            offset=0,
        )

        # User tries to access admin's content
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(
            f"/api/v2/playlist-contents/{admin_content.id}/",
        )

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can access other user's content directly (BOLA)",
            )

    def test_update_other_user_content(
        self, api_client, admin_user, regular_user,
    ):
        """Try to update another user's content."""
        admin_playlist = baker.make("schedule.Playlist", owner=admin_user)
        admin_file = baker.make("storage.File", owner=admin_user)
        admin_content = baker.make(
            "schedule.PlaylistContent",
            playlist=admin_playlist,
            file=admin_file,
            kind=0,  # FILE = 0
            position=1,
            offset=0,
        )

        # User tries to update admin's content
        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/playlist-contents/{admin_content.id}/",
            {"position": 999},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail("CRITICAL BUG: Can update other user's content (BOLA)")

    def test_delete_other_user_content(
        self, api_client, admin_user, regular_user,
    ):
        """Try to delete another user's content."""
        admin_playlist = baker.make("schedule.Playlist", owner=admin_user)
        admin_file = baker.make("storage.File", owner=admin_user)
        admin_content = baker.make(
            "schedule.PlaylistContent",
            playlist=admin_playlist,
            file=admin_file,
            kind=0,  # FILE = 0
            position=1,
            offset=0,
        )

        # User tries to delete admin's content
        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(
            f"/api/v2/playlist-contents/{admin_content.id}/",
        )

        if response.status_code == 204:
            pytest.fail("CRITICAL BUG: Can delete other user's content (BOLA)")

    def test_create_content_for_other_user_playlist(
        self, api_client, admin_user, regular_user,
    ):
        """Try to create content in another user's playlist."""
        admin_playlist = baker.make("schedule.Playlist", owner=admin_user)
        admin_file = baker.make("storage.File", owner=admin_user)

        # User tries to create content in admin's playlist
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": admin_playlist.id,
                "file": admin_file.id,
                "kind": 0,  # FILE = 0
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail(
                "CRITICAL BUG: Can create content in other user's playlist (BOLA)",
            )


@pytest.mark.django_db
class TestPlaylistContentFilterInjection:
    """Query parameter injection attacks."""

    def test_filter_by_invalid_playlist_id(self, api_client, admin_user):
        """Try to filter by invalid playlist_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=invalid")

        # Should handle gracefully
        if response.status_code == 500:
            pytest.fail(
                "BUG: Filter crashes on invalid playlist_id (ValueError)",
            )

    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in playlist filter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_playlistcontents;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/playlist-contents?playlist={payload}",
            )

            # Should not execute SQL or crash
            if response.status_code == 500:
                pytest.fail(
                    f"BUG: SQL injection payload causes crash: {payload}",
                )

    def test_filter_by_negative_playlist_id(self, api_client, admin_user):
        """Try to filter by negative playlist_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=-1")

        # Should handle gracefully
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestPlaylistContentBusinessLogic:
    """Business logic bypass attacks."""

    def test_create_with_nonexistent_playlist(self, api_client, admin_user):
        """Try to create content with non-existent playlist."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": 99999,
                "file": file_obj.id,
                "kind": 0,  # FILE = 0
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should reject non-existent playlist
        if response.status_code == 201:
            pytest.fail("BUG: Accepts non-existent playlist_id")

    def test_create_with_nonexistent_file(self, api_client, admin_user):
        """Try to create content with non-existent file."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": 99999,
                "kind": 0,  # FILE = 0
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        # Should reject non-existent file
        if response.status_code == 201:
            pytest.fail("BUG: Accepts non-existent file_id")

    def test_duplicate_position_in_same_playlist(self, api_client, admin_user):
        """Try to create duplicate position in same playlist."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file1 = baker.make("storage.File", owner=admin_user)
        file2 = baker.make("storage.File", owner=admin_user)

        # Create first content at position 1
        baker.make(
            "schedule.PlaylistContent",
            playlist=playlist,
            file=file1,
            kind=0,  # FILE = 0
            position=1,
            offset=0,
        )

        # Try to create second content at same position
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file2.id,
                "kind": 0,  # FILE = 0
                "position": 1,  # Same position!
                "offset": 0,
            },
            format="json",
        )

        # May accept or reject - just documenting behavior
        # This is typically handled by application logic, not API

    def test_create_without_auth(self, api_client):
        """Try to create content without authentication."""
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": 1,
                "kind": 0,  # FILE = 0
                "position": 1,
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can create content")

    def test_create_with_expired_session(self, api_client, admin_user):
        """Try to create with manipulated/expired session."""
        api_client.force_authenticate(user=admin_user)

        # Simulate expired token by modifying auth header
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": 1,
                "kind": 0,  # FILE = 0
                "position": 1,
            },
            format="json",
        )

        assert response.status_code in [
            401,
            403,
            404,
        ]  # 404 if auth middleware rejects early
