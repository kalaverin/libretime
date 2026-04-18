from rest_framework.test import APIClient


def test_stream_preferences_get(db, api_client: APIClient):
    response = api_client.get("/api/v2/stream/preferences")
    assert response.status_code == 200
    assert response.json() == {
        "input_fade_transition": 0.0,
        "message_format": 0,
        "message_offline": "LibreTime - offline",
        "replay_gain_enabled": True,
        "replay_gain_offset": 0.0,
    }


def test_stream_state_get(db, api_client: APIClient):
    response = api_client.get("/api/v2/stream/state")
    assert response.status_code == 200
    assert response.json() == {
        "input_main_connected": False,
        "input_main_streaming": False,
        "input_show_connected": False,
        "input_show_streaming": False,
        "schedule_streaming": True,
    }
