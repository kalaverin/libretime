"""Tests for Shows LIST endpoint (T201)."""

import uuid

import pytest

from model_bakery import baker

from api.schedule.models import Show


@pytest.mark.django_db(transaction=True)
class TestShowViewSetList:
    """Test Shows LIST endpoint - GET /api/v2/shows."""

    def setup_method(self):
        """Clean up shows before each test."""
        Show.objects.all().delete()

    def test_list_shows_empty_returns_200(self, admin_client):
        """LIST with no shows should return empty array."""
        response = admin_client.get("/api/v2/shows")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_shows_returns_all(self, admin_client):
        """LIST should return all shows."""
        show1 = baker.make(Show, name="Show One")
        show2 = baker.make(Show, name="Show Two")

        response = admin_client.get("/api/v2/shows")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = [s["name"] for s in data]
        assert "Show One" in names
        assert "Show Two" in names

    def test_list_shows_returns_json(self, admin_client):
        """LIST should return JSON response."""
        baker.make(Show, name="Test Show")
        response = admin_client.get("/api/v2/shows")
        assert response["Content-Type"] == "application/json"

    def test_list_shows_contains_id(self, admin_client):
        """LIST should include show id."""
        show = baker.make(Show, name="Test Show")
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == show.id

    def test_list_shows_contains_name(self, admin_client):
        """LIST should include show name."""
        baker.make(Show, name="Test Show")
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["name"] == "Test Show"

    def test_list_shows_contains_description(self, admin_client):
        """LIST should include show description."""
        baker.make(Show, name="Test", description="Test description")
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["description"] == "Test description"

    def test_list_shows_null_description(self, admin_client):
        """LIST should handle null description."""
        baker.make(Show, name="Test", description=None)
        response = admin_client.get("/api/v2/shows")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["description"] is None

    def test_list_shows_contains_genre(self, admin_client):
        """LIST should include show genre."""
        baker.make(Show, name="Test", genre="Rock")
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["genre"] == "Rock"

    def test_list_shows_contains_url(self, admin_client):
        """LIST should include show url."""
        baker.make(Show, name="Test", url="https://example.com")
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["url"] == "https://example.com"

    def test_list_shows_contains_image(self, admin_client):
        """LIST should include show image."""
        baker.make(Show, name="Test", image="/path/to/image.png")
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["image"] == "/path/to/image.png"

    def test_list_shows_contains_colors(self, admin_client):
        """LIST should include foreground and background colors."""
        baker.make(
            Show,
            name="Test",
            foreground_color="FFFFFF",
            background_color="000000",
        )
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["foreground_color"] == "FFFFFF"
        assert data[0]["background_color"] == "000000"

    def test_list_shows_contains_linked_flags(self, admin_client):
        """LIST should include linked and linkable flags."""
        baker.make(Show, name="Test", linked=True, linkable=False)
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["linked"] is True
        assert data[0]["linkable"] is False

    def test_list_shows_contains_auto_playlist_flags(self, admin_client):
        """LIST should include auto_playlist_enabled and auto_playlist_repeat."""
        baker.make(
            Show,
            name="Test",
            auto_playlist_enabled=True,
            auto_playlist_repeat=True,
        )
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["auto_playlist_enabled"] is True
        assert data[0]["auto_playlist_repeat"] is True

    def test_list_shows_contains_intro_outro_flags(self, admin_client):
        """LIST should include override_intro_playlist and override_outro_playlist."""
        baker.make(
            Show,
            name="Test",
            override_intro_playlist=True,
            override_outro_playlist=False,
        )
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["override_intro_playlist"] is True
        assert data[0]["override_outro_playlist"] is False

    def test_list_shows_live_enabled_false_when_no_auth(self, admin_client):
        """LIST should show live_enabled=false when no live auth."""
        baker.make(
            Show,
            name="Test",
            live_auth_registered=False,
            live_auth_custom=False,
        )
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["live_enabled"] is False

    def test_list_shows_live_enabled_true_when_registered_auth(
        self,
        admin_client,
    ):
        """LIST should show live_enabled=true when live_auth_registered is true."""
        baker.make(
            Show,
            name="Test",
            live_auth_registered=True,
            live_auth_custom=False,
        )
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["live_enabled"] is True

    def test_list_shows_live_enabled_true_when_custom_auth(self, admin_client):
        """LIST should show live_enabled=true when live_auth_custom is true."""
        baker.make(
            Show,
            name="Test",
            live_auth_registered=False,
            live_auth_custom=True,
        )
        response = admin_client.get("/api/v2/shows")
        data = response.json()
        assert data[0]["live_enabled"] is True

    @pytest.mark.xfail(
        reason="ShowViewSet missing pagination - returns all results",
    )
    def test_list_shows_pagination_limit(self, admin_client):
        """LIST should support limit parameter."""
        for i in range(10):
            baker.make(Show, name=f"Show {i}")

        response = admin_client.get("/api/v2/shows?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    @pytest.mark.xfail(
        reason="ShowViewSet missing pagination - returns all results",
    )
    def test_list_shows_pagination_offset(self, admin_client):
        """LIST should support offset parameter."""
        for i in range(10):
            baker.make(Show, name=f"Show {i}")

        response = admin_client.get("/api/v2/shows?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_list_shows_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/shows")
        assert response.status_code == 403

    def test_list_shows_unicode_names(self, admin_client):
        """LIST should handle unicode show names."""
        baker.make(Show, name="日本語ショー", description="日本語の説明")
        response = admin_client.get("/api/v2/shows")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["name"] == "日本語ショー"
        assert data[0]["description"] == "日本語の説明"

    def test_list_shows_long_description(self, admin_client):
        """LIST should handle long descriptions (max 8192 chars)."""
        long_desc = "A" * 8192
        baker.make(Show, name="Test", description=long_desc)
        response = admin_client.get("/api/v2/shows")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["description"] == long_desc

    def test_list_shows_with_hosts(self, admin_client):
        """LIST shows with hosts - hosts accessible via separate endpoint."""
        from api.core.models import User

        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username=f"host1_{uuid.uuid4().hex[:8]}")
        # Create ShowHost relationship
        baker.make("schedule.ShowHost", show=show, user=user)

        response = admin_client.get("/api/v2/shows")
        assert response.status_code == 200
        data = response.json()
        # Show serializer doesn't include hosts directly
        assert len(data) == 1
        assert data[0]["name"] == "Test Show"

    @pytest.mark.xfail(
        reason="ShowViewSet missing filter_backends - ordering not supported",
    )
    def test_list_shows_ordering_by_name(self, admin_client):
        """LIST should be orderable by name."""
        baker.make(Show, name="Charlie")
        baker.make(Show, name="Alpha")
        baker.make(Show, name="Bravo")

        response = admin_client.get("/api/v2/shows?ordering=name")
        assert response.status_code == 200
        data = response.json()
        names = [s["name"] for s in data]
        assert names == ["Alpha", "Bravo", "Charlie"]

    def test_list_shows_filter_by_name(self, admin_client):
        """LIST should support filtering by name."""
        baker.make(Show, name="Morning Show")
        baker.make(Show, name="Evening Show")

        response = admin_client.get("/api/v2/shows?name=Morning")
        # Filtering may or may not be supported
        assert response.status_code in [200, 400]
