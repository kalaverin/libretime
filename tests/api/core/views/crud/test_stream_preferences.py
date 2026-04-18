"""Tests for StreamPreferences endpoint (T184)."""

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
class TestStreamPreferencesView:
    """Test StreamPreferences endpoint - GET /api/v2/stream/preferences."""

    def setup_method(self):
        """Clean up site preferences before each test."""
        Preference.objects.filter(user=None).delete()

    def test_stream_pref_endpoint_available_with_api_key(self, guest_client):
        """StreamPreferences endpoint should be accessible with API key."""
        response = guest_client.get("/api/v2/stream/preferences")
        assert response.status_code == 200

    def test_stream_pref_returns_json(self, guest_client):
        """StreamPreferences endpoint should return JSON."""
        response = guest_client.get("/api/v2/stream/preferences")
        assert response["Content-Type"] == "application/json"

    def test_stream_pref_response_structure(self, guest_client):
        """StreamPreferences response should have all expected fields."""
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        expected_fields = {
            "input_fade_transition",
            "message_format",
            "message_offline",
            "replay_gain_enabled",
            "replay_gain_offset",
        }
        assert set(data.keys()) == expected_fields

    def test_stream_pref_default_values(self, guest_client):
        """Default values should be returned when no preferences set."""
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        assert data["input_fade_transition"] == 0.0
        assert data["message_format"] == 0  # ARTIST_TITLE
        assert data["message_offline"] == "Offline"
        assert data["replay_gain_enabled"] is False
        assert data["replay_gain_offset"] == 0.0

    def test_stream_pref_custom_fade_transition(self, guest_client):
        """Custom input_fade_transition should be returned."""
        create_site_pref("default_transition_fade", "2.5")
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        assert data["input_fade_transition"] == 2.5

    def test_stream_pref_custom_message_format(self, guest_client):
        """Custom message_format should be returned."""
        create_site_pref("stream_label_format", "1")
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        assert data["message_format"] == 1  # SHOW_ARTIST_TITLE

    def test_stream_pref_custom_message_offline(self, guest_client):
        """Custom message_offline should be returned."""
        create_site_pref("off_air_meta", "Station is offline, back soon!")
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        assert data["message_offline"] == "Station is offline, back soon!"

    def test_stream_pref_replay_gain_enabled_true(self, guest_client):
        """replay_gain_enabled should be True when set to '1'."""
        create_site_pref("enable_replay_gain", "1")
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        assert data["replay_gain_enabled"] is True

    def test_stream_pref_custom_replay_gain_offset(self, guest_client):
        """Custom replay_gain_offset should be returned."""
        create_site_pref("replay_gain_modifier", "-3.5")
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        assert data["replay_gain_offset"] == -3.5

    def test_stream_pref_data_types(self, guest_client):
        """All fields should have correct data types."""
        create_site_pref("default_transition_fade", "1.5")
        create_site_pref("stream_label_format", "2")
        create_site_pref("off_air_meta", "Test message")
        create_site_pref("enable_replay_gain", "1")
        create_site_pref("replay_gain_modifier", "2.0")

        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()

        assert isinstance(data["input_fade_transition"], float)
        assert isinstance(data["message_format"], int)
        assert isinstance(data["message_offline"], str)
        assert isinstance(data["replay_gain_enabled"], bool)
        assert isinstance(data["replay_gain_offset"], float)

    def test_stream_pref_no_auth_returns_403(self, client: Client):
        """Endpoint should return 403 without authentication."""
        response = client.get("/api/v2/stream/preferences")
        assert response.status_code == 403

    def test_stream_pref_post_not_allowed(self, guest_client):
        """POST should not be allowed on StreamPreferences endpoint."""
        response = guest_client.post(
            "/api/v2/stream/preferences",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_stream_pref_put_not_allowed(self, guest_client):
        """PUT should not be allowed on StreamPreferences endpoint."""
        response = guest_client.put(
            "/api/v2/stream/preferences",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_stream_pref_patch_not_allowed(self, guest_client):
        """PATCH should not be allowed on StreamPreferences endpoint."""
        response = guest_client.patch(
            "/api/v2/stream/preferences",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_stream_pref_delete_not_allowed(self, guest_client):
        """DELETE should not be allowed on StreamPreferences endpoint."""
        response = guest_client.delete("/api/v2/stream/preferences")
        assert response.status_code == 405

    def test_stream_pref_with_session_auth_with_permission(
        self,
        authenticated_client,
    ):
        """Endpoint should work with session auth and proper permission."""
        # Admin user has all permissions
        response = authenticated_client.get("/api/v2/stream/preferences")
        assert response.status_code == 200
        assert "input_fade_transition" in response.json()

    def test_stream_pref_message_format_values(self, guest_client):
        """Test all valid message_format values."""
        test_cases = [
            ("0", 0),  # ARTIST_TITLE
            ("1", 1),  # SHOW_ARTIST_TITLE
            ("2", 2),  # RADIO_SHOW
        ]
        for input_val, expected in test_cases:
            Preference.objects.filter(
                user=None,
                key="stream_label_format",
            ).delete()
            create_site_pref("stream_label_format", input_val)
            response = guest_client.get("/api/v2/stream/preferences")
            data = response.json()
            assert (
                data["message_format"] == expected
            ), f"Failed for input {input_val}"

    def test_stream_pref_replay_gain_enabled_variations(self, guest_client):
        """Test replay_gain_enabled with various truthy/falsy values."""
        test_cases = [
            ("1", True),
            ("0", False),
            ("", False),
            ("true", False),  # Only "1" is truthy
        ]
        for input_val, expected in test_cases:
            Preference.objects.filter(
                user=None,
                key="enable_replay_gain",
            ).delete()
            create_site_pref("enable_replay_gain", input_val)
            response = guest_client.get("/api/v2/stream/preferences")
            data = response.json()
            assert (
                data["replay_gain_enabled"] is expected
            ), f"Failed for input {input_val}"

    def test_stream_pref_user_preferences_ignored(self, guest_client):
        """User-specific preferences should not affect StreamPreferences."""
        user = baker.make(User)
        Preference.objects.create(
            user=user,
            key="default_transition_fade",
            value="99.9",
        )
        # No site preference, should use default
        response = guest_client.get("/api/v2/stream/preferences")
        data = response.json()
        assert data["input_fade_transition"] == 0.0
