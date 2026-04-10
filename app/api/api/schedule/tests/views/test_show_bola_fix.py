"""Tests for Show BOLA fix - session auth filtering."""

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import Show, ShowHost


@pytest.mark.django_db
class TestShowBOLASessionAuth:
    """BOLA tests with session auth (not API-Key)."""

    def test_session_auth_list_only_own_shows(self, host_client, regular_user):
        """Host sees only shows where they are assigned."""
        # Create show with regular_user as host
        own_show = baker.make(Show, name="Own Show")
        baker.make(ShowHost, show=own_show, user=regular_user)

        # Create another show with different host
        other_user = baker.make(User, username="other_host")
        other_show = baker.make(Show, name="Other Show")
        baker.make(ShowHost, show=other_show, user=other_user)

        response = host_client.get("/api/v2/shows")
        assert response.status_code == 200
        data = response.json()
        # Should see only own show
        names = [s["name"] for s in data]
        assert "Own Show" in names
        assert "Other Show" not in names

    def test_session_auth_retrieve_own_show(self, host_client, regular_user):
        """Host can retrieve their own show."""
        show = baker.make(Show, name="My Show")
        baker.make(ShowHost, show=show, user=regular_user)

        response = host_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "My Show"

    def test_session_auth_retrieve_other_show_fails(self, host_client, regular_user):
        """Host cannot retrieve other user's show (BOLA fix)."""
        other_user = baker.make(User, username="other_host")
        other_show = baker.make(Show, name="Other Show")
        baker.make(ShowHost, show=other_show, user=other_user)

        response = host_client.get(f"/api/v2/shows/{other_show.id}")
        # Should be 404 (not found for this user)
        assert response.status_code == 404

    def test_session_auth_update_other_show_fails(self, host_client, regular_user):
        """Host cannot update other user's show (BOLA fix)."""
        other_user = baker.make(User, username="other_host")
        other_show = baker.make(Show, name="Other Show")
        baker.make(ShowHost, show=other_show, user=other_user)

        response = host_client.patch(
            f"/api/v2/shows/{other_show.id}",
            {"name": "Hacked Name"},
            format="json",
        )
        # 403 (permission denied) or 404 (not found) - both acceptable
        assert response.status_code in [403, 404]

    def test_session_auth_delete_other_show_fails(self, host_client, regular_user):
        """Host cannot delete other user's show (BOLA fix)."""
        other_user = baker.make(User, username="other_host")
        other_show = baker.make(Show, name="Other Show")
        baker.make(ShowHost, show=other_show, user=other_user)

        response = host_client.delete(f"/api/v2/shows/{other_show.id}")
        # 403 (permission denied) or 404 (not found) - both acceptable
        assert response.status_code in [403, 404]

    def test_anonymous_list_fails(self, client):
        """Anonymous cannot list shows - 403 Forbidden."""
        baker.make(Show, name="Test Show")
        response = client.get("/api/v2/shows")
        # Permission denied for anonymous
        assert response.status_code == 403

    def test_anonymous_retrieve_fails(self, client):
        """Anonymous cannot retrieve shows - 403 Forbidden."""
        show = baker.make(Show, name="Test Show")
        response = client.get(f"/api/v2/shows/{show.id}")
        # Permission denied for anonymous
        assert response.status_code == 403
