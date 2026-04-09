"""Tests for Shows RETRIEVE endpoint (T204)."""

import uuid

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowViewSetRetrieve:
    """Test Shows RETRIEVE endpoint - GET /api/v2/shows/{id}."""

    def setup_method(self):
        """Clean up shows before each test."""
        Show.objects.all().delete()
        ShowHost.objects.all().delete()

    def test_retrieve_show_success(self, api_client):
        """RETRIEVE should return show details."""
        show = baker.make(
            Show,
            name="Test Show",
            description="Test description",
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Show"

    def test_retrieve_show_returns_json(self, api_client):
        """RETRIEVE should return JSON response."""
        show = baker.make(Show, name="Test Show")
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response["Content-Type"] == "application/json"

    def test_retrieve_show_contains_id(self, api_client):
        """RETRIEVE should include show id."""
        show = baker.make(Show, name="Test Show")
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["id"] == show.id

    def test_retrieve_show_contains_name(self, api_client):
        """RETRIEVE should include show name."""
        show = baker.make(Show, name="Test Show")
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["name"] == "Test Show"

    def test_retrieve_show_contains_description(self, api_client):
        """RETRIEVE should include show description."""
        show = baker.make(Show, name="Test", description="Test description")
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["description"] == "Test description"

    def test_retrieve_show_null_description(self, api_client):
        """RETRIEVE should handle null description."""
        show = baker.make(Show, name="Test", description=None)
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["description"] is None

    def test_retrieve_show_contains_genre(self, api_client):
        """RETRIEVE should include show genre."""
        show = baker.make(Show, name="Test", genre="Rock")
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["genre"] == "Rock"

    def test_retrieve_show_contains_url(self, api_client):
        """RETRIEVE should include show url."""
        show = baker.make(Show, name="Test", url="https://example.com")
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["url"] == "https://example.com"

    def test_retrieve_show_contains_image(self, api_client):
        """RETRIEVE should include show image."""
        show = baker.make(Show, name="Test", image="/path/to/image.png")
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["image"] == "/path/to/image.png"

    def test_retrieve_show_contains_colors(self, api_client):
        """RETRIEVE should include foreground and background colors."""
        show = baker.make(
            Show,
            name="Test",
            foreground_color="FFFFFF",
            background_color="000000",
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        result = response.json()
        assert result["foreground_color"] == "FFFFFF"
        assert result["background_color"] == "000000"

    def test_retrieve_show_contains_linked_flags(self, api_client):
        """RETRIEVE should include linked and linkable flags."""
        show = baker.make(Show, name="Test", linked=True, linkable=False)
        response = api_client.get(f"/api/v2/shows/{show.id}")
        result = response.json()
        assert result["linked"] is True
        assert result["linkable"] is False

    def test_retrieve_show_contains_auto_playlist_flags(self, api_client):
        """RETRIEVE should include auto_playlist_enabled and auto_playlist_repeat."""
        show = baker.make(
            Show,
            name="Test",
            auto_playlist_enabled=True,
            auto_playlist_repeat=True,
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        result = response.json()
        assert result["auto_playlist_enabled"] is True
        assert result["auto_playlist_repeat"] is True

    def test_retrieve_show_contains_intro_outro_flags(self, api_client):
        """RETRIEVE should include override_intro_playlist and override_outro_playlist."""
        show = baker.make(
            Show,
            name="Test",
            override_intro_playlist=True,
            override_outro_playlist=False,
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        result = response.json()
        assert result["override_intro_playlist"] is True
        assert result["override_outro_playlist"] is False

    def test_retrieve_show_live_enabled_false(self, api_client):
        """RETRIEVE should show live_enabled=false when no live auth."""
        show = baker.make(
            Show,
            name="Test",
            live_auth_registered=False,
            live_auth_custom=False,
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["live_enabled"] is False

    def test_retrieve_show_live_enabled_true_registered(self, api_client):
        """RETRIEVE should show live_enabled=true when live_auth_registered."""
        show = baker.make(
            Show,
            name="Test",
            live_auth_registered=True,
            live_auth_custom=False,
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["live_enabled"] is True

    def test_retrieve_show_live_enabled_true_custom(self, api_client):
        """RETRIEVE should show live_enabled=true when live_auth_custom."""
        show = baker.make(
            Show,
            name="Test",
            live_auth_registered=False,
            live_auth_custom=True,
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["live_enabled"] is True

    def test_retrieve_show_not_found_returns_404(self, api_client):
        """RETRIEVE non-existent show should return 404."""
        response = api_client.get("/api/v2/shows/999999")
        assert response.status_code == 404

    def test_retrieve_show_no_auth_fails(self, client):
        """RETRIEVE without auth should return 403."""
        show = baker.make(Show, name="Test Show")
        response = client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 403

    def test_retrieve_show_unicode_name(self, api_client):
        """RETRIEVE should handle unicode show names."""
        show = baker.make(
            Show,
            name="日本語ショー",
            description="日本語の説明",
        )
        response = api_client.get(f"/api/v2/shows/{show.id}")
        result = response.json()
        assert result["name"] == "日本語ショー"
        assert result["description"] == "日本語の説明"

    def test_retrieve_show_long_description(self, api_client):
        """RETRIEVE should handle long descriptions."""
        long_desc = "A" * 8192
        show = baker.make(Show, name="Test", description=long_desc)
        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.json()["description"] == long_desc

    def test_retrieve_show_with_hosts(self, api_client):
        """RETRIEVE show with hosts - hosts not directly in serializer."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username=f"host1_{uuid.uuid4().hex[:8]}")
        baker.make(ShowHost, show=show, user=user)

        response = api_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        # Show serializer doesn't include hosts
        result = response.json()
        assert "hosts" not in result or result.get("hosts") is None

    def test_retrieve_show_id_zero_returns_404(self, api_client):
        """RETRIEVE with id=0 should return 404."""
        response = api_client.get("/api/v2/shows/0")
        assert response.status_code == 404

    def test_retrieve_show_negative_id_returns_404(self, api_client):
        """RETRIEVE with negative id should return 404."""
        response = api_client.get("/api/v2/shows/-1")
        assert response.status_code == 404

    def test_retrieve_show_large_id_returns_404(self, api_client):
        """RETRIEVE with very large id should return 404."""
        response = api_client.get("/api/v2/shows/999999999")
        assert response.status_code == 404

    def test_retrieve_show_sql_injection_attempt(self, api_client):
        """RETRIEVE with SQL injection in id should be handled safely."""
        response = api_client.get("/api/v2/shows/1 OR 1=1")
        assert response.status_code == 404

    def test_retrieve_show_path_traversal_attempt(self, api_client):
        """RETRIEVE with path traversal should be handled safely."""
        response = api_client.get("/api/v2/shows/../../../etc/passwd")
        assert response.status_code == 404
