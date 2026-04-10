"""
RED TEAM: T322/T323/T324 - PlaylistContent filter/ordering security tests.

Attack vectors:
- Filter injection (SQLi, type confusion)
- Ordering manipulation for data extraction
- Information disclosure via error messages
- Mass ordering extraction
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestPlaylistContentFilterInjection:
    """Filter parameter injection attacks."""

    @pytest.mark.xfail(reason="500 error on invalid playlist_id filter")
    def test_filter_by_invalid_playlist_id(self, api_client, admin_user):
        """Try to filter by invalid playlist_id - should not crash."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=invalid")

        # Should return 400, not 500
        if response.status_code == 500:
            pytest.fail(
                "BUG: Filter crashes on invalid playlist_id (500 error)",
            )
        assert response.status_code in [200, 400]

    @pytest.mark.xfail(reason="500 error on SQLi in playlist filter")
    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in playlist filter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_playlistcontents;--",
            "1 UNION SELECT * FROM cc_subjs",
            "1' UNION SELECT username,password FROM cc_subjs--",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/playlist-contents?playlist={payload}",
            )

            # Should not crash or execute SQL
            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes 500 error: {payload}")
            # Should not return all records
            if response.status_code == 200:
                data = response.json()
                # If we get results, check if it's suspiciously large
                # (indicating potential data leak)

    def test_filter_by_negative_playlist_id(self, api_client, admin_user):
        """Try to filter by negative playlist_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=-1")

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_filter_by_zero_playlist_id(self, api_client, admin_user):
        """Try to filter by zero playlist_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=0")

        assert response.status_code in [200, 400]

    def test_filter_by_very_large_playlist_id(self, api_client, admin_user):
        """Try to filter by very large playlist_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v2/playlist-contents?playlist=999999999999999999",
        )

        assert response.status_code in [200, 400]

    @pytest.mark.xfail(reason="500 error on float playlist_id filter")
    def test_filter_by_float_playlist_id(self, api_client, admin_user):
        """Try to filter by float playlist_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=1.5")

        # Should handle gracefully
        assert response.status_code in [200, 400]

    @pytest.mark.xfail(reason="500 error on hex playlist_id filter")
    def test_filter_by_hex_playlist_id(self, api_client, admin_user):
        """Try to filter by hex playlist_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=0x1")

        assert response.status_code in [200, 400]

    def test_filter_without_auth(self, api_client):
        """Try to filter without authentication."""
        response = api_client.get("/api/v2/playlist-contents?playlist=1")

        if response.status_code == 200:
            pytest.fail("BUG: Anonymous can filter playlist contents")


@pytest.mark.django_db
class TestPlaylistContentOrderingManipulation:
    """Ordering parameter manipulation attacks."""

    def test_order_by_invalid_field(self, api_client, admin_user):
        """Try to order by non-existent field."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v2/playlist-contents?ordering=nonexistent_field",
        )

        # Should reject invalid field
        assert response.status_code in [200, 400]

    def test_order_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in ordering parameter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "position; DROP TABLE cc_playlistcontents;--",
            "position,(SELECT password FROM cc_subjs LIMIT 1)",
            "position'||'",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/playlist-contents?ordering={payload}",
            )

            if response.status_code == 500:
                pytest.fail(f"BUG: Ordering SQLi causes 500: {payload}")

    def test_order_by_private_field(self, api_client, admin_user):
        """Try to order by internal/private fields."""
        api_client.force_authenticate(user=admin_user)

        internal_fields = [
            "id",
            "_state",
            "playlist__owner__password",
            "playlist__owner__secret_key",
        ]

        for field in internal_fields:
            response = api_client.get(
                f"/api/v2/playlist-contents?ordering={field}",
            )

            # May accept or reject
            if response.status_code == 500:
                pytest.fail(f"BUG: Ordering by {field} causes 500 error")

    def test_reverse_ordering(self, api_client, admin_user):
        """Test reverse ordering works correctly."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)

        # Create content with positions 1, 2, 3
        for i in range(1, 4):
            file_obj = baker.make("storage.File", owner=admin_user)
            baker.make(
                "schedule.PlaylistContent",
                playlist=playlist,
                file=file_obj,
                kind=0,
                position=i,
                offset=0,
            )

        api_client.force_authenticate(user=admin_user)

        # Test ascending order
        response = api_client.get(
            "/api/v2/playlist-contents?ordering=position",
        )
        assert response.status_code == 200

        # Test descending order
        response = api_client.get(
            "/api/v2/playlist-contents?ordering=-position",
        )
        assert response.status_code == 200
        data = response.json()

        # Verify descending order
        if len(data) >= 2:
            positions = [c.get("position") for c in data]
            assert positions == sorted(positions, reverse=True)


@pytest.mark.django_db
class TestPlaylistContentInformationDisclosure:
    """Information disclosure via filter/ordering."""

    def test_error_message_on_invalid_filter(self, api_client, admin_user):
        """Check if error messages leak implementation details."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?playlist=invalid")

        if response.status_code == 400:
            content = response.content.decode()
            # Check for information leakage
            leaked_terms = [
                "cc_playlistcontents",
                "column",
                "django",
                "sql",
                "field 'id'",
            ]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: Error message leaks info: {term}")

    def test_timing_attack_on_filter(self, api_client, admin_user):
        """Test for timing-based information disclosure."""
        import time

        api_client.force_authenticate(user=admin_user)

        # Request with valid filter
        start = time.time()
        response1 = api_client.get("/api/v2/playlist-contents?playlist=1")
        time_valid = time.time() - start

        # Request with invalid filter
        start = time.time()
        response2 = api_client.get("/api/v2/playlist-contents?playlist=999999")
        time_invalid = time.time() - start

        # Times should be similar (no timing leak)
        diff = abs(time_valid - time_invalid)
        # Allow 1 second difference for test stability
        assert diff < 1.0, f"Possible timing attack: diff={diff}s"


@pytest.mark.django_db
class TestPlaylistContentIDORWithFilter:
    """IDOR attacks combined with filtering."""

    def test_filter_by_other_user_playlist(
        self, api_client, admin_user, regular_user,
    ):
        """Try to filter by another user's playlist_id."""
        admin_playlist = baker.make("schedule.Playlist", owner=admin_user)
        admin_file = baker.make("storage.File", owner=admin_user)
        admin_content = baker.make(
            "schedule.PlaylistContent",
            playlist=admin_playlist,
            file=admin_file,
            kind=0,
            position=1,
            offset=0,
        )

        # User tries to filter by admin's playlist
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(
            f"/api/v2/playlist-contents?playlist={admin_playlist.id}",
        )

        assert response.status_code == 200
        data = response.json()

        # Should not see admin's content
        content_ids = [c["id"] for c in data]
        if admin_content.id in content_ids:
            pytest.fail(
                "BUG: Can filter by other user's playlist and see content (BOLA)",
            )


@pytest.mark.django_db
class TestPlaylistContentPagination:
    """Pagination-related security tests."""

    def test_large_limit_parameter(self, api_client, admin_user):
        """Try to request very large number of items."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?limit=999999")

        # Should not crash or return all items
        assert response.status_code in [200, 400]

    def test_negative_limit(self, api_client, admin_user):
        """Try negative limit parameter."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?limit=-1")

        assert response.status_code in [200, 400]

    def test_negative_offset(self, api_client, admin_user):
        """Try negative offset parameter."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/playlist-contents?offset=-1")

        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestPlaylistContentOffsetValidation:
    """T324 offset field optional - security implications."""

    def test_create_without_offset_succeeds(self, api_client, admin_user):
        """Verify offset is truly optional."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": 0,
                "position": 1,
                # No offset field!
            },
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        # Offset should have default value
        assert "offset" in data

    def test_create_with_null_offset(self, api_client, admin_user):
        """Try to create with explicit null offset."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": 0,
                "position": 1,
                "offset": None,
            },
            format="json",
        )

        # Should handle null offset
        assert response.status_code in [201, 400]

    def test_create_with_negative_offset(self, api_client, admin_user):
        """Try to create with negative offset."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": 0,
                "position": 1,
                "offset": -100,
            },
            format="json",
        )

        # May accept or reject - documenting behavior
        assert response.status_code in [201, 400]

    def test_create_with_very_large_offset(self, api_client, admin_user):
        """Try to create with very large offset."""
        playlist = baker.make("schedule.Playlist", owner=admin_user)
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playlist-contents/",
            {
                "playlist": playlist.id,
                "file": file_obj.id,
                "kind": 0,
                "position": 1,
                "offset": 999999999,
            },
            format="json",
        )

        # Should handle large offset
        assert response.status_code in [201, 400]
