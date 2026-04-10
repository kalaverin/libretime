"""Red Team security tests for PlaylistContents permissions (T233).

Tests focus on:
- API2:2023 Broken Authentication
- API5:2023 BFLA
- Permission bypass vectors
- Cross-user access controls
"""

import json

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist, PlaylistContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistContentPermissionsRedTeam:
    """Red Team tests for PlaylistContents permissions."""

    def setup_method(self):
        """Clean up before each test."""
        PlaylistContent.objects.all().delete()
        Playlist.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API2:2023 - Broken Authentication
    # ========================================================================

    def test_list_requires_auth(self, client):
        """Auth: LIST without auth should fail."""
        response = client.get("/api/v2/playlist-contents")
        assert response.status_code == 403

    def test_retrieve_requires_auth(self, client):
        """Auth: RETRIEVE without auth should fail."""
        response = client.get("/api/v2/playlist-contents/1")
        assert response.status_code == 403

    def test_create_requires_auth(self, client):
        """Auth: CREATE without auth should fail."""
        response = client.post(
            "/api/v2/playlist-contents",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_requires_auth(self, client):
        """Auth: UPDATE without auth should fail."""
        response = client.patch(
            "/api/v2/playlist-contents/1",
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_requires_auth(self, client):
        """Auth: DELETE without auth should fail."""
        response = client.delete("/api/v2/playlist-contents/1")
        assert response.status_code == 403

    # ========================================================================
    # API5:2023 - BFLA
    # ========================================================================

    def test_bfla_admin_endpoints(self, api_client):
        """BFLA: Try to access admin endpoints."""
        admin_patterns = [
            "/api/v2/admin/playlist-contents",
            "/api/v2/playlist-contents/admin",
            "/api/v2/internal/playlist-contents",
        ]

        for pattern in admin_patterns:
            response = api_client.get(pattern)
            assert response.status_code in [403, 404], \
                f"BFLA: {pattern} returned {response.status_code}"

    # ========================================================================
    # Cross-User Access
    # ========================================================================

    @pytest.mark.xfail(reason="T420: No cross-user access control")
    def test_cross_user_cannot_list_others(self, api_client):
        """Cross-user: User should only see own contents."""
        victim = baker.make(User, username="testred_victim")
        victim_playlist = baker.make(Playlist, name="Victim", owner=victim)
        victim_file = baker.make(File, name="victim.mp3", mime="audio/mp3", owner=victim)
        victim_content = baker.make(
            PlaylistContent,
            playlist=victim_playlist,
            kind=PlaylistContent.Kind.FILE,
            file=victim_file,
            position=1,
        )

        response = api_client.get("/api/v2/playlist-contents")
        data = response.json()

        ids = [c["id"] for c in data]
        assert victim_content.id not in ids, \
            "Cross-user: Attacker sees victim's content"

    # ========================================================================
    # Permission Elevation
    # ========================================================================

    def test_permission_elevation_param(self, api_client):
        """Elevation: Try to elevate via query params."""
        response = api_client.get("/api/v2/playlist-contents?admin=true&role=admin")
        # Should ignore params or return 403
        assert response.status_code in [200, 403], \
            f"Elevation param caused {response.status_code}"
