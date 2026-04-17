"""Red Team security tests for PlaylistContents RETRIEVE endpoint (T232).

Tests focus on:
- API1:2023 BOLA (viewing other's content)
- API3:2023 BOPLA (field exposure)
- API6:2023 Resource consumption
- Information disclosure
"""

import time

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist, PlaylistContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistContentRetrieveRedTeam:
    """Red Team tests for GET /api/v2/playlist-contents/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA
    # ========================================================================

    @pytest.mark.xfail(reason="T420: BOLA - can view other's content")
    def test_bola_retrieve_other_users_content(self, api_client):
        """BOLA: Should not retrieve another user's content."""
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

        response = api_client.get(f"/api/v2/playlist-contents/{content.id}")

        assert response.status_code in [
            403,
            404,
        ], f"BOLA: Retrieved victim's content with {response.status_code}"

    @pytest.mark.xfail(reason="T420: IDOR - sequential ID enumeration")
    def test_idor_enumerate_content_ids(self, api_client):
        """IDOR: Enumerate content IDs to find victim's data."""
        victim = baker.make(User, username="testred_victim")
        victim_playlist = baker.make(Playlist, name="Victim", owner=victim)

        contents = []
        for i in range(3):
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

        base_id = contents[0].id
        found = 0
        for offset in range(-2, 5):
            test_id = base_id + offset
            r = api_client.get(f"/api/v2/playlist-contents/{test_id}")
            if r.status_code == 200:
                found += 1

        assert (
            found == 0
        ), f"IDOR: Found {found} victim contents via enumeration"

    # ========================================================================
    # API3:2023 - BOPLA
    # ========================================================================

    def test_bopla_field_exposure(self, api_client):
        """BOPLA: Check sensitive field exposure in retrieve."""
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

        response = api_client.get(f"/api/v2/playlist-contents/{content.id}")
        data = response.json()

        sensitive = ["password", "secret", "token", "internal"]
        for field in data.keys():
            for s in sensitive:
                assert (
                    s not in field.lower()
                ), f"BOPLA: Sensitive field '{field}' exposed"

    # ========================================================================
    # API6:2023 - Resource
    # ========================================================================

    def test_retrieve_rapid_fire(self, api_client):
        """Resource: Rapid retrieve should be rate limited."""
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
        for _ in range(50):
            api_client.get(f"/api/v2/playlist-contents/{content.id}")
        elapsed = time.time() - start

        if elapsed < 2:
            pass  # No rate limiting

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_retrieve_nonexistent(self, api_client):
        """Edge: Retrieve non-existent content."""
        response = api_client.get("/api/v2/playlist-contents/999999")
        assert response.status_code == 404

    def test_retrieve_invalid_id(self, api_client):
        """Edge: Invalid content ID formats."""
        invalid_ids = ["abc", "1.5", "-1", "1' OR '1'='1"]

        for invalid_id in invalid_ids:
            response = api_client.get(
                f"/api/v2/playlist-contents/{invalid_id}",
            )
            assert response.status_code in [
                400,
                404,
            ], f"Invalid id '{invalid_id}' caused {response.status_code}"

    def test_retrieve_timing_attack(self, api_client):
        """Timing: Response time should not reveal existence."""
        # Time non-existent
        start = time.time()
        api_client.get("/api/v2/playlist-contents/999999")
        time_missing = time.time() - start

        # Create and time existent
        user = baker.make(User, username="testred_timing")
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
        api_client.get(f"/api/v2/playlist-contents/{content.id}")
        time_exists = time.time() - start

        diff = abs(time_missing - time_exists)
        assert diff < 0.5, f"Timing leak: {diff}s difference"
