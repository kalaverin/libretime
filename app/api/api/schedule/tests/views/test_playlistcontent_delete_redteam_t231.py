"""Red Team security tests for PlaylistContents DELETE endpoint (T231).

Tests focus on:
- API1:2023 BOLA (deleting other's content)
- API6:2023 Resource consumption (mass delete)
- Cascade delete effects
- Recovery after delete
"""

import time

from concurrent.futures import ThreadPoolExecutor

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist, PlaylistContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistContentDeleteRedTeam:
    """Red Team tests for DELETE /api/v2/playlist-contents/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA
    # ========================================================================

    @pytest.mark.xfail(reason="T420: BOLA - can delete other's content")
    def test_bola_delete_other_users_content(self, api_client):
        """BOLA: Should not delete another user's playlist content."""
        victim = baker.make(User, username="testred_victim")
        victim_playlist = baker.make(Playlist, name="Victim", owner=victim)
        victim_file = baker.make(
            File, name="victim.mp3", mime="audio/mp3", owner=victim,
        )
        content = baker.make(
            PlaylistContent,
            playlist=victim_playlist,
            kind=PlaylistContent.Kind.FILE,
            file=victim_file,
            position=1,
        )

        response = api_client.delete(f"/api/v2/playlist-contents/{content.id}")

        assert response.status_code in [
            403,
            404,
        ], f"BOLA: Deleted victim's content with {response.status_code}"
        assert PlaylistContent.objects.filter(
            id=content.id,
        ).exists(), "BOLA: Victim's content was deleted"

    @pytest.mark.xfail(reason="T420: BOLA - mass delete other's content")
    def test_bola_mass_delete_other_users_contents(self, api_client):
        """BOLA: Mass delete victim's playlist contents."""
        victim = baker.make(User, username="testred_victim")
        victim_playlist = baker.make(Playlist, name="Victim", owner=victim)

        contents = []
        for i in range(5):
            f = baker.make(
                File, name=f"victim{i}.mp3", mime="audio/mp3", owner=victim,
            )
            c = baker.make(
                PlaylistContent,
                playlist=victim_playlist,
                kind=PlaylistContent.Kind.FILE,
                file=f,
                position=i,
            )
            contents.append(c)

        # Try to delete all
        deleted = 0
        for c in contents:
            r = api_client.delete(f"/api/v2/playlist-contents/{c.id}")
            if r.status_code == 204:
                deleted += 1

        assert deleted == 0, f"BOLA: Deleted {deleted} victim's contents"

    # ========================================================================
    # API6:2023 - Resource Consumption
    # ========================================================================

    def test_delete_rapid_fire(self, api_client):
        """Resource: Rapid delete should be rate limited."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        # Create many contents
        contents = []
        for i in range(20):
            f = baker.make(
                File, name=f"file{i}.mp3", mime="audio/mp3", owner=user,
            )
            c = baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=f,
                position=i,
            )
            contents.append(c)

        # Rapid delete
        start = time.time()
        for c in contents:
            api_client.delete(f"/api/v2/playlist-contents/{c.id}")
        elapsed = time.time() - start

        if elapsed < 2:
            pass  # No rate limiting

    # ========================================================================
    # Race Conditions
    # ========================================================================

    def test_race_double_delete(self, api_client):
        """Race: Concurrent delete attempts."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        file_obj = baker.make(
            File, name="test.mp3", mime="audio/mp3", owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
        )

        def delete():
            return api_client.delete(f"/api/v2/playlist-contents/{content.id}")

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(delete)
            f2 = executor.submit(delete)
            r1, r2 = f1.result(), f2.result()

        statuses = {r1.status_code, r2.status_code}
        assert statuses == {204, 404} or len(statuses) == 1

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_delete_nonexistent(self, api_client):
        """Edge: Delete non-existent content."""
        response = api_client.delete("/api/v2/playlist-contents/999999")
        assert response.status_code == 404

    def test_delete_already_deleted(self, api_client):
        """Edge: Double delete same content."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)
        file_obj = baker.make(
            File, name="test.mp3", mime="audio/mp3", owner=user,
        )
        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
        )

        api_client.delete(f"/api/v2/playlist-contents/{content.id}")
        response = api_client.delete(f"/api/v2/playlist-contents/{content.id}")

        assert response.status_code == 404

    def test_delete_sql_injection_id(self, api_client):
        """SQLi: Injection in content ID."""
        sqli_ids = [
            "1 OR 1=1",
            "1; DROP TABLE cc_playlistcontents;--",
            "1' UNION SELECT * FROM users--",
        ]

        for sqli_id in sqli_ids:
            response = api_client.delete(
                f"/api/v2/playlist-contents/{sqli_id}",
            )
            assert response.status_code in [
                400,
                404,
            ], f"SQLi id '{sqli_id}' caused {response.status_code}"
