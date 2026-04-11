"""
BOLA (Broken Object Level Authorization) Tests for Playlist

Tests for:
- T808: Playlist UPDATE other user's playlist
- T809: Playlist DELETE other user's playlist
"""

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Playlist


@pytest.mark.django_db
class TestBolaPlaylistPrevention:
    """BOLA prevention tests for Playlist (T808, T809)."""

    def test_anonymous_get_playlists_returns_403(self, anonymous_client):
        """Anonymous GET /playlists returns 403."""
        response = anonymous_client.get("/api/v2/playlists")
        assert response.status_code == 403

    def test_anonymous_post_playlists_returns_403(self, anonymous_client):
        """Anonymous POST /playlists returns 403."""
        response = anonymous_client.post("/api/v2/playlists", {})
        assert response.status_code == 403

    def test_bola_update_other_host_playlist(self, host_client, host_user, faker):
        """BOLA T808: HOST cannot UPDATE another HOST's playlist."""
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        victim_playlist = baker.make(
            Playlist,
            name=f"Victim Playlist {faker.uuid4()[:8]}",
            description=faker.sentence(),
            owner=victim,
        )
        original_name = victim_playlist.name

        # Attacker tries to update victim's playlist
        response = host_client.patch(
            f"/api/v2/playlists/{victim_playlist.id}",
            {"name": f"Hacked {faker.uuid4()[:8]}"},
            format="json",
        )
        
        assert response.status_code in [403, 404], (
            f"BOLA T808: HOST updated victim's playlist, got {response.status_code}"
        )
        
        # Verify not modified
        victim_playlist.refresh_from_db()
        assert victim_playlist.name == original_name

    def test_bola_delete_other_host_playlist(self, host_client, host_user, faker):
        """BOLA T809: HOST cannot DELETE another HOST's playlist."""
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        victim_playlist = baker.make(
            Playlist,
            name=f"Victim Playlist {faker.uuid4()[:8]}",
            description=faker.sentence(),
            owner=victim,
        )
        victim_playlist_id = victim_playlist.id

        # Attacker tries to delete victim's playlist
        response = host_client.delete(f"/api/v2/playlists/{victim_playlist_id}")
        
        assert response.status_code in [403, 404], (
            f"BOLA T809: HOST deleted victim's playlist, got {response.status_code}"
        )
        
        # Verify still exists
        assert Playlist.objects.filter(id=victim_playlist_id).exists()

    def test_bola_list_playlists_only_shows_own(self, host_client, host_user, faker):
        """BOLA: HOST LIST should only show own playlists."""
        # Create victim user with private playlist
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        victim_playlist = baker.make(
            Playlist,
            name=f"Victim Playlist {faker.uuid4()[:8]}",
            description=faker.sentence(),
            owner=victim,
        )
        
        # Create own playlist
        own_playlist = baker.make(
            Playlist,
            name=f"Own Playlist {faker.uuid4()[:8]}",
            description=faker.sentence(),
            owner=host_user,
        )

        response = host_client.get("/api/v2/playlists")
        assert response.status_code == 200

        data = response.json()
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data)
        
        result_ids = [p["id"] for p in results]
        
        # Should see own playlist
        assert own_playlist.id in result_ids, "HOST should see own playlist"
        
        # Should NOT see victim's playlist
        assert victim_playlist.id not in result_ids, (
            f"BOLA: HOST can see victim's playlist in LIST!"
        )

    def test_manager_can_update_any_host_playlist(self, manager_client, faker):
        """MANAGER can UPDATE any HOST's playlist (expected, not BOLA)."""
        host_user = baker.make(
            User,
            username=f"host_{faker.uuid4()[:8]}",
            email=f"host_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        host_playlist = baker.make(
            Playlist,
            name=f"Host Playlist {faker.uuid4()[:8]}",
            owner=host_user,
        )
        new_name = f"Manager Updated {faker.uuid4()[:8]}"

        response = manager_client.patch(
            f"/api/v2/playlists/{host_playlist.id}",
            {"name": new_name},
            format="json",
        )

        assert response.status_code == 200, (
            f"MANAGER should update any playlist! Status: {response.status_code}"
        )

        host_playlist.refresh_from_db()
        assert host_playlist.name == new_name
