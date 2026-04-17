"""Tests for Info endpoint (T182)."""

import pytest

from api.core.models import Preference, User
from django.test import Client
from model_bakery import baker


def create_site_pref(key: str, value: str):
    """Helper to create or update site preference."""
    pref, _ = Preference.objects.get_or_create(
        user=None,
        key=key,
        defaults={"value": value},
    )
    if pref.value != value:
        pref.value = value
        pref.save()
    return pref


@pytest.mark.django_db(transaction=True)
class TestInfoView:
    """Test Info endpoint - GET /api/v2/info."""

    def setup_method(self):
        """Clean up site preferences before each test."""
        Preference.objects.filter(user=None, key="station_name").delete()

    def test_info_endpoint_available(self, client: Client):
        """Info endpoint should be accessible."""
        response = client.get("/api/v2/info")
        assert response.status_code == 200

    def test_info_returns_json(self, client: Client):
        """Info endpoint should return JSON."""
        response = client.get("/api/v2/info")
        assert response["Content-Type"] == "application/json"

    def test_info_response_structure(self, client: Client):
        """Info response should have station_name field."""
        response = client.get("/api/v2/info")
        data = response.json()
        assert "station_name" in data
        assert isinstance(data["station_name"], str)

    def test_info_default_station_name(self, client: Client):
        """Default station_name should be 'LibreTime' when no preference set."""
        response = client.get("/api/v2/info")
        data = response.json()
        assert data["station_name"] == "LibreTime"

    def test_info_custom_station_name(self, client: Client):
        """Info should return custom station_name from site preferences."""
        create_site_pref("station_name", "Test Radio Station")
        response = client.get("/api/v2/info")
        data = response.json()
        assert data["station_name"] == "Test Radio Station"

    def test_info_no_auth_required(self, client: Client):
        """Info endpoint should be accessible without authentication."""
        response = client.get("/api/v2/info")
        assert response.status_code == 200
        assert "station_name" in response.json()

    def test_info_returns_only_station_name(self, client: Client):
        """Info should return only station_name, not other preferences."""
        create_site_pref("station_name", "My Station")
        create_site_pref("other_key", "other_value")
        response = client.get("/api/v2/info")
        data = response.json()
        assert set(data.keys()) == {"station_name"}

    def test_info_empty_station_name_fallback(self, client: Client):
        """Empty string station_name should fall back to 'LibreTime'."""
        create_site_pref("station_name", "")
        response = client.get("/api/v2/info")
        data = response.json()
        assert data["station_name"] == "LibreTime"

    def test_info_unicode_station_name(self, client: Client):
        """Station name with unicode characters should work."""
        create_site_pref("station_name", "Радио «Звезда» 🎵")
        response = client.get("/api/v2/info")
        data = response.json()
        assert data["station_name"] == "Радио «Звезда» 🎵"

    def test_info_long_station_name(self, client: Client):
        """Long station name should be handled."""
        long_name = "A" * 1000
        create_site_pref("station_name", long_name)
        response = client.get("/api/v2/info")
        data = response.json()
        assert data["station_name"] == long_name

    def test_info_special_chars_station_name(self, client: Client):
        """Station name with special characters should work."""
        special_name = "<script>alert('xss')</script> & \"quotes\""
        create_site_pref("station_name", special_name)
        response = client.get("/api/v2/info")
        data = response.json()
        assert data["station_name"] == special_name

    def test_info_post_not_allowed(self, client: Client):
        """POST should not be allowed on Info endpoint."""
        response = client.post(
            "/api/v2/info",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_info_put_not_allowed(self, client: Client):
        """PUT should not be allowed on Info endpoint."""
        response = client.put(
            "/api/v2/info",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_info_patch_not_allowed(self, client: Client):
        """PATCH should not be allowed on Info endpoint."""
        response = client.patch(
            "/api/v2/info",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_info_delete_not_allowed(self, client: Client):
        """DELETE should not be allowed on Info endpoint."""
        response = client.delete("/api/v2/info")
        assert response.status_code == 405

    def test_info_user_preferences_ignored(self, client: Client):
        """User-specific preferences should not affect Info endpoint."""
        user = baker.make(User)
        # Make sure no site preference exists
        Preference.objects.filter(user=None, key="station_name").delete()
        Preference.objects.create(
            user=user,
            key="station_name",
            value="User Station Name",
        )
        response = client.get("/api/v2/info")
        data = response.json()
        # Should still be default since only site prefs matter
        assert data["station_name"] == "LibreTime"

    def test_info_site_pref_takes_precedence_over_user(self, client: Client):
        """Site preference should be used even when user pref exists."""
        user = baker.make(User)
        Preference.objects.create(
            user=user,
            key="station_name",
            value="User Station",
        )
        create_site_pref("station_name", "Site Station")
        response = client.get("/api/v2/info")
        data = response.json()
        assert data["station_name"] == "Site Station"
