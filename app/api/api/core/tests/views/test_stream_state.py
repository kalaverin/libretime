"""Tests for StreamState endpoint (T185)."""

import pytest

from api.core.models import Preference, User
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
class TestStreamStateView:
    """Test StreamState endpoint - GET /api/v2/stream/state."""

    def setup_method(self):
        """Clean up site preferences before each test."""
        Preference.objects.filter(user=None).delete()

    def test_stream_state_endpoint_available_with_api_key(self, api_client):
        """StreamState endpoint should be accessible with API key."""
        response = api_client.get("/api/v2/stream/state")
        assert response.status_code == 200

    def test_stream_state_returns_json(self, api_client):
        """StreamState endpoint should return JSON."""
        response = api_client.get("/api/v2/stream/state")
        assert response["Content-Type"] == "application/json"

    def test_stream_state_response_structure(self, api_client):
        """StreamState response should have all expected fields."""
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        expected_fields = {
            "input_main_connected",
            "input_main_streaming",
            "input_show_connected",
            "input_show_streaming",
            "schedule_streaming",
        }
        assert set(data.keys()) == expected_fields

    def test_stream_state_default_values(self, api_client):
        """Default values should be False when no preferences set."""
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["input_main_connected"] is False
        assert data["input_main_streaming"] is False
        assert data["input_show_connected"] is False
        assert data["input_show_streaming"] is False
        assert data["schedule_streaming"] is False

    def test_stream_state_input_main_connected_true(self, api_client):
        """input_main_connected should be True when master_dj='true'."""
        create_site_pref("master_dj", "true")
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["input_main_connected"] is True

    def test_stream_state_input_main_streaming_true(self, api_client):
        """input_main_streaming should be True when master_dj_switch='on'."""
        create_site_pref("master_dj_switch", "on")
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["input_main_streaming"] is True

    def test_stream_state_input_show_connected_true(self, api_client):
        """input_show_connected should be True when live_dj='true'."""
        create_site_pref("live_dj", "true")
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["input_show_connected"] is True

    def test_stream_state_input_show_streaming_true(self, api_client):
        """input_show_streaming should be True when live_dj_switch='on'."""
        create_site_pref("live_dj_switch", "on")
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["input_show_streaming"] is True

    def test_stream_state_schedule_streaming_true(self, api_client):
        """schedule_streaming should be True when scheduled_play_switch='on'."""
        create_site_pref("scheduled_play_switch", "on")
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["schedule_streaming"] is True

    def test_stream_state_all_connected(self, api_client):
        """All inputs can be connected simultaneously."""
        create_site_pref("master_dj", "true")
        create_site_pref("master_dj_switch", "on")
        create_site_pref("live_dj", "true")
        create_site_pref("live_dj_switch", "on")
        create_site_pref("scheduled_play_switch", "on")

        response = api_client.get("/api/v2/stream/state")
        data = response.json()

        assert data["input_main_connected"] is True
        assert data["input_main_streaming"] is True
        assert data["input_show_connected"] is True
        assert data["input_show_streaming"] is True
        assert data["schedule_streaming"] is True

    def test_stream_state_mixed_states(self, api_client):
        """Different inputs can have different states."""
        create_site_pref("master_dj", "true")
        create_site_pref("master_dj_switch", "off")
        create_site_pref("live_dj", "false")
        create_site_pref("live_dj_switch", "on")
        create_site_pref("scheduled_play_switch", "off")

        response = api_client.get("/api/v2/stream/state")
        data = response.json()

        assert data["input_main_connected"] is True
        assert data["input_main_streaming"] is False
        assert data["input_show_connected"] is False
        assert data["input_show_streaming"] is True
        assert data["schedule_streaming"] is False

    def test_stream_state_data_types(self, api_client):
        """All fields should be boolean type."""
        create_site_pref("master_dj", "true")
        create_site_pref("master_dj_switch", "on")

        response = api_client.get("/api/v2/stream/state")
        data = response.json()

        assert isinstance(data["input_main_connected"], bool)
        assert isinstance(data["input_main_streaming"], bool)
        assert isinstance(data["input_show_connected"], bool)
        assert isinstance(data["input_show_streaming"], bool)
        assert isinstance(data["schedule_streaming"], bool)

    def test_stream_state_no_auth_returns_403(self, client):
        """Endpoint should return 403 without authentication."""
        response = client.get("/api/v2/stream/state")
        assert response.status_code == 403

    def test_stream_state_post_not_allowed(self, api_client):
        """POST should not be allowed on StreamState endpoint."""
        response = api_client.post(
            "/api/v2/stream/state",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_stream_state_put_not_allowed(self, api_client):
        """PUT should not be allowed on StreamState endpoint."""
        response = api_client.put(
            "/api/v2/stream/state",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_stream_state_patch_not_allowed(self, api_client):
        """PATCH should not be allowed on StreamState endpoint."""
        response = api_client.patch(
            "/api/v2/stream/state",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_stream_state_delete_not_allowed(self, api_client):
        """DELETE should not be allowed on StreamState endpoint."""
        response = api_client.delete("/api/v2/stream/state")
        assert response.status_code == 405

    def test_stream_state_user_preferences_ignored(self, api_client):
        """User-specific preferences should not affect StreamState."""
        user = baker.make(User)
        Preference.objects.create(
            user=user,
            key="master_dj",
            value="true",
        )
        # No site preference, should be False
        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["input_main_connected"] is False

    def test_stream_state_site_pref_takes_precedence(self, api_client):
        """Site preference should be used even when user pref exists."""
        user = baker.make(User)
        Preference.objects.create(
            user=user,
            key="master_dj",
            value="false",
        )
        create_site_pref("master_dj", "true")

        response = api_client.get("/api/v2/stream/state")
        data = response.json()
        assert data["input_main_connected"] is True

    def test_stream_state_invalid_values_treated_as_false(self, api_client):
        """Invalid preference values should be treated as False."""
        create_site_pref("master_dj", "invalid_value")
        create_site_pref("master_dj_switch", "random")
        create_site_pref("live_dj", "yes")
        create_site_pref("live_dj_switch", "enabled")
        create_site_pref("scheduled_play_switch", "1")

        response = api_client.get("/api/v2/stream/state")
        data = response.json()

        # Only exact matches should be True
        assert data["input_main_connected"] is False  # != "true"
        assert data["input_main_streaming"] is False  # != "on"
        assert data["input_show_connected"] is False  # != "true"
        assert data["input_show_streaming"] is False  # != "on"
        assert data["schedule_streaming"] is False  # != "on"
