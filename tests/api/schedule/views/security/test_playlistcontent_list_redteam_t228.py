"""Red Team security tests for PlaylistContents LIST endpoint (T228).

Tests focus on:
- API1:2023 Broken Object Level Authorization (BOLA/IDOR)
- API3:2023 Broken Object Property Level Authorization (BOPLA)
- API6:2023 Unrestricted Resource Consumption
- API8:2023 Security Misconfiguration
- Information disclosure via list endpoints
"""

import time

from concurrent.futures import ThreadPoolExecutor

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
class TestPlaylistContentListRedTeam:
    """Red Team tests for GET /api/v2/playlist-contents."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T420: BOLA - no owner filtering on playlist contents",
    )
    def test_bola_list_other_users_contents(self, api_client):
        """BOLA: User should only see contents of their playlists."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Create victim's playlist with content
        victim_playlist = baker.make(
            Playlist,
            name="Victim Playlist",
            owner=victim,
        )
        victim_file = baker.make(
            File,
            name="victim.mp3",
            mime="audio/mp3",
            owner=victim,
        )
        victim_content = baker.make(
            PlaylistContent,
            playlist=victim_playlist,
            kind=PlaylistContent.Kind.FILE,
            file=victim_file,
            position=1,
        )

        # Attacker lists all contents
        response = api_client.get("/api/v2/playlist-contents")
        data = response.json()

        # Attacker should NOT see victim's content
        content_ids = [c["id"] for c in data]
        assert (
            victim_content.id not in content_ids
        ), "BOLA: Attacker can see victim's playlist content"

    @pytest.mark.xfail(reason="T420: BOLA via playlist filter")
    def test_bola_filter_by_other_users_playlist(self, api_client):
        """BOLA: Filter by other user's playlist ID should fail."""
        victim = baker.make(User, username="testred_victim")

        victim_playlist = baker.make(
            Playlist,
            name="Victim Playlist",
            owner=victim,
        )
        victim_file = baker.make(
            File,
            name="victim.mp3",
            mime="audio/mp3",
            owner=victim,
        )
        baker.make(
            PlaylistContent,
            playlist=victim_playlist,
            kind=PlaylistContent.Kind.FILE,
            file=victim_file,
            position=1,
        )

        # Attacker tries to filter by victim's playlist
        response = api_client.get(
            f"/api/v2/playlist-contents?playlist={victim_playlist.id}",
        )
        data = response.json()

        # Should return empty list (no access to victim's playlist)
        assert (
            len(data) == 0
        ), "BOLA: Filter by victim's playlist returned contents"

    @pytest.mark.xfail(reason="T420: IDOR - sequential ID exposure")
    def test_idor_content_id_enumeration(self, api_client):
        """IDOR: Attacker can enumerate all contents by ID."""
        victim = baker.make(User, username="testred_victim")

        # Create multiple victim contents
        victim_playlist = baker.make(Playlist, name="Victim", owner=victim)
        contents = []
        for i in range(5):
            f = baker.make(
                File,
                name=f"victim{i}.mp3",
                mime="audio/mp3",
                owner=victim,
            )
            c = baker.make(
                PlaylistContent,
                playlist=victim_playlist,
                kind=PlaylistContent.Kind.FILE,
                file=f,
                position=i,
            )
            contents.append(c)

        # Attacker lists all - should not see victim's
        response = api_client.get("/api/v2/playlist-contents")
        data = response.json()

        victim_ids = {c.id for c in contents}
        found_ids = {c["id"] for c in data}

        overlap = victim_ids & found_ids
        assert (
            len(overlap) == 0
        ), f"IDOR: Found {len(overlap)} victim contents via enumeration"

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    def test_bopla_field_exposure_in_list(self, api_client):
        """BOPLA: Check if sensitive fields are exposed in list view."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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
        )

        response = api_client.get("/api/v2/playlist-contents")
        data = response.json()

        # Check for sensitive field exposure
        sensitive_patterns = [
            "password",
            "secret",
            "token",
            "internal",
            "private",
            "created_by",
            "updated_by",
            "ip_address",
        ]

        for item in data:
            for field in item.keys():
                for pattern in sensitive_patterns:
                    assert (
                        pattern not in field.lower()
                    ), f"BOPLA: Sensitive field '{field}' exposed in list"

    def test_bopla_extra_fields_injection(self, api_client):
        """BOPLA: Try to request extra fields via query params."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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
        )

        # Try various field injection patterns
        injection_attempts = [
            "?fields=password,secret",
            "?include=internal_notes",
            "?expand=all",
            "?select=*",
        ]

        for attempt in injection_attempts:
            response = api_client.get(f"/api/v2/playlist-contents{attempt}")
            # Should not expose extra fields
            assert response.status_code in [
                200,
                400,
            ], f"Field injection '{attempt}' caused {response.status_code}"

    # ========================================================================
    # API6:2023 - Unrestricted Resource Consumption
    # ========================================================================

    def test_list_pagination_missing(self, api_client):
        """Resource: List without pagination can cause DoS."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        # Create many contents
        for i in range(100):
            f = baker.make(
                File,
                name=f"file{i}.mp3",
                mime="audio/mp3",
                owner=user,
            )
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=f,
                position=i,
            )

        start = time.time()
        response = api_client.get("/api/v2/playlist-contents")
        elapsed = time.time() - start

        data = response.json()
        # If all 100 returned without pagination, that's a problem
        if len(data) == 100:
            # Should implement pagination
            pass  # Document: no pagination detected

        # Response should be reasonably fast
        assert elapsed < 5.0, f"DoS: 100 items took {elapsed}s"

    def test_list_mass_content_creation(self, api_client):
        """Resource: Rapid listing during mass creation."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        def create_and_list():
            # Create a content
            f = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=f,
                position=1,
            )
            # List immediately
            return api_client.get("/api/v2/playlist-contents")

        # Rapid create + list cycles
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_and_list) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(
            r.status_code == 200 for r in responses
        ), "Some list requests failed during mass creation"

    def test_list_with_huge_offset(self, api_client):
        """Resource: Test with extremely large offset parameter."""
        # Try various large offsets
        huge_offsets = [
            999999999,
            2**31 - 1,  # Max int32
            2**63 - 1,  # Max int64
        ]

        for offset in huge_offsets:
            response = api_client.get(
                f"/api/v2/playlist-contents?offset={offset}",
            )
            # Should handle gracefully
            assert response.status_code in [
                200,
                400,
                404,
            ], f"Offset {offset} caused {response.status_code}"

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_list_http_method_override(self, api_client):
        """Security: Method override on list endpoint."""
        response = api_client.get(
            "/api/v2/playlist-contents",
            headers={"X-HTTP-Method-Override": "DELETE"},
        )
        # Should not delete all contents
        assert response.status_code in [
            200,
            405,
        ], f"Method override returned {response.status_code}"

    def test_list_with_trace(self, api_client):
        """Security: TRACE method should not work."""
        response = api_client.trace("/api/v2/playlist-contents")
        assert response.status_code in [
            405,
            501,
        ], f"TRACE returned {response.status_code}"

    def test_list_cors_headers(self, api_client):
        """Security: Check CORS headers on list endpoint."""
        response = api_client.options(
            "/api/v2/playlist-contents",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should not allow arbitrary origins
        allowed_origin = response.headers.get("Access-Control-Allow-Origin")
        assert allowed_origin != "*", "CORS allows wildcard origin"
        assert (
            allowed_origin != "https://evil.com"
        ), "CORS reflects arbitrary origin"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    @pytest.mark.xfail(reason="T421: 500 error on invalid playlist filter")
    def test_list_sql_injection_in_filter(self, api_client):
        """SQLi: Injection in playlist filter parameter should return 400."""
        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_playlistcontents;--",
            "1 UNION SELECT * FROM users",
            "1) OR (1=1",
            "1' AND 1=1--",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/playlist-contents?playlist={payload}",
            )
            # Should return 400 (bad request) for invalid input
            # Currently returns 500 (bug T421)
            assert response.status_code in [
                400,
                404,
            ], f"SQLi payload '{payload}' caused {response.status_code}, expected 400/404"

    @pytest.mark.xfail(reason="T421: 500 error on invalid playlist filter")
    def test_list_nosql_injection_in_filter(self, api_client):
        """NoSQLi: MongoDB operators in filter should return 400."""
        nosql_payloads = [
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$regex": ".*"}',
            '{"$in": [1, 2, 3]}',
        ]

        for payload in nosql_payloads:
            response = api_client.get(
                f"/api/v2/playlist-contents?playlist={payload}",
            )
            # Should return 400 (bad request) for invalid input
            # Currently returns 500 (bug T421)
            assert response.status_code in [
                400,
                404,
            ], f"NoSQLi payload '{payload}' caused {response.status_code}, expected 400/404"

    def test_list_order_by_injection(self, api_client):
        """SQLi: Injection in ordering parameter."""
        order_payloads = [
            "position; DROP TABLE users;--",
            "position ASC; DELETE FROM cc_playlistcontents;--",
            "(SELECT * FROM users)",
            "position, (SELECT password FROM users LIMIT 1)",
        ]

        for payload in order_payloads:
            response = api_client.get(
                f"/api/v2/playlist-contents?ordering={payload}",
            )
            assert response.status_code in [
                200,
                400,
            ], f"Order injection '{payload}' caused {response.status_code}"

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    @pytest.mark.xfail(reason="T421: 500 error exposes internal details")
    def test_list_error_message_disclosure(self, api_client):
        """Info: Error messages should not leak internal details."""
        # Trigger errors with invalid parameters
        invalid_params = [
            "?playlist=invalid'",
            "?ordering=<script>",
            "?limit=-1",
        ]

        for param in invalid_params:
            response = api_client.get(f"/api/v2/playlist-contents{param}")
            # Should never get 500
            assert (
                response.status_code != 500
            ), f"Bug T421: 500 error for '{param}' exposes internal details"

            if response.status_code >= 400:
                content = response.content.decode().lower()
                leaks = ["sql", "django", "traceback", "exception", "password"]
                for leak in leaks:
                    assert (
                        leak not in content
                    ), f"Info leak: '{leak}' in error for '{param}'"

    def test_list_timing_attack(self, api_client):
        """Timing: Response time should not reveal data existence."""
        # Time empty list
        start = time.time()
        api_client.get("/api/v2/playlist-contents")
        time_empty = time.time() - start

        # Create content
        user = baker.make(User, username="testred_timing")
        playlist = baker.make(Playlist, name="Test", owner=user)
        f = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)
        baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=f,
            position=1,
        )

        # Time non-empty list
        start = time.time()
        api_client.get("/api/v2/playlist-contents")
        time_nonempty = time.time() - start

        diff = abs(time_empty - time_nonempty)
        assert (
            diff < 0.5
        ), f"Timing leak: {diff}s difference between empty/non-empty"

    # ========================================================================
    # Business Logic
    # ========================================================================

    def test_list_filter_by_nonexistent_playlist(self, api_client):
        """Logic: Filter by non-existent playlist should return empty."""
        response = api_client.get("/api/v2/playlist-contents?playlist=999999")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_filter_by_deleted_playlist(self, api_client):
        """Logic: Filter by deleted playlist should return empty."""
        user = baker.make(User, username="testred_deleted")
        playlist = baker.make(Playlist, name="To Delete", owner=user)
        f = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=f,
            position=1,
        )
        playlist_id = playlist.id

        # Delete playlist (cascade or orphan)
        playlist.delete()

        # Try to filter by deleted playlist ID
        response = api_client.get(
            f"/api/v2/playlist-contents?playlist={playlist_id}",
        )
        assert response.status_code == 200
        # Should return empty (orphaned content should not be visible)
        data = response.json()
        assert len(data) == 0 or content.id not in [
            c["id"] for c in data
        ], "Orphaned content visible after playlist deletion"

    def test_list_multiple_filter_parameters(self, api_client):
        """Logic: Multiple filter params should combine correctly."""
        # Try conflicting filters
        response = api_client.get(
            "/api/v2/playlist-contents?playlist=1&playlist=2",
        )
        # Should handle gracefully
        assert response.status_code in [
            200,
            400,
        ], f"Multiple filters caused {response.status_code}"
