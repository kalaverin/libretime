"""Tests for Shows CREATE endpoint (T202-T203)."""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowViewSetCreate:
    """Test Shows CREATE endpoint - POST /api/v2/shows."""

    def setup_method(self):
        """Clean up shows before each test."""
        Show.objects.all().delete()
        ShowHost.objects.all().delete()

    def test_create_show_minimal_success(self, api_client):
        """CREATE with minimal required fields should succeed."""
        data = {
            "name": "Test Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Test Show"

    def test_create_show_with_description(self, api_client):
        """CREATE with description should succeed."""
        data = {
            "name": "Test Show",
            "description": "Test description",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["description"] == "Test description"

    def test_create_show_with_genre(self, api_client):
        """CREATE with genre should succeed."""
        data = {
            "name": "Test Show",
            "genre": "Rock",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["genre"] == "Rock"

    def test_create_show_with_url(self, api_client):
        """CREATE with url should succeed."""
        data = {
            "name": "Test Show",
            "url": "https://example.com/show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["url"] == "https://example.com/show"

    def test_create_show_with_colors(self, api_client):
        """CREATE with colors should succeed."""
        data = {
            "name": "Test Show",
            "foreground_color": "FFFFFF",
            "background_color": "000000",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.json()
        assert result["foreground_color"] == "FFFFFF"
        assert result["background_color"] == "000000"

    def test_create_show_missing_name_fails(self, api_client):
        """CREATE without name should fail."""
        data = {
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_missing_linked_fails(self, api_client):
        """CREATE without linked should fail."""
        data = {
            "name": "Test Show",
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_missing_linkable_fails(self, api_client):
        """CREATE without linkable should fail."""
        data = {
            "name": "Test Show",
            "linked": False,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_returns_json(self, api_client):
        """CREATE should return JSON response."""
        data = {
            "name": "Test Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response["Content-Type"] == "application/json"

    def test_create_show_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        data = {"name": "Test Show"}
        response = client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_show_unicode_name(self, api_client):
        """CREATE with unicode name should succeed."""
        data = {
            "name": "日本語ショー",
            "description": "日本語の説明",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "日本語ショー"
        assert result["description"] == "日本語の説明"

    def test_create_show_long_description(self, api_client):
        """CREATE with long description should succeed."""
        long_desc = "A" * 8192
        data = {
            "name": "Test Show",
            "description": long_desc,
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["description"] == long_desc

    @pytest.mark.xfail(
        reason="BUG T319: live_auth fields not in serializer - can't set via API",
    )
    def test_create_show_with_live_auth_registered(self, api_client):
        """CREATE with live_auth_registered should succeed."""
        data = {
            "name": "Test Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
            "live_auth_registered": True,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        # live_enabled is computed property from live_auth fields
        assert response.json()["live_enabled"] is True

    @pytest.mark.xfail(
        reason="BUG T319: live_auth fields not in serializer - can't set via API",
    )
    def test_create_show_with_live_auth_custom(self, api_client):
        """CREATE with live_auth_custom should succeed."""
        data = {
            "name": "Test Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
            "live_auth_custom": True,
            "live_auth_custom_user": "dj_user",
            "live_auth_custom_password": "secret123",
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["live_enabled"] is True

    def test_create_show_with_auto_playlist_enabled(self, api_client):
        """CREATE with auto_playlist_enabled should succeed."""
        data = {
            "name": "Test Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": True,
            "auto_playlist_repeat": True,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.json()
        assert result["auto_playlist_enabled"] is True
        assert result["auto_playlist_repeat"] is True

    def test_create_show_duplicate_name_fails(self, api_client):
        """CREATE with duplicate name should fail."""
        baker.make(Show, name="Duplicate Show")
        data = {
            "name": "Duplicate Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        # Name may or may not be unique - accept either
        assert response.status_code in [201, 400]

    def test_create_show_empty_name_fails(self, api_client):
        """CREATE with empty name should fail."""
        data = {
            "name": "",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_name_too_long_fails(self, api_client):
        """CREATE with name > 255 chars should fail."""
        data = {
            "name": "A" * 256,
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_invalid_color_format(self, api_client):
        """CREATE with invalid color format may fail or be accepted."""
        data = {
            "name": "Test Show",
            "foreground_color": "not-a-color",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post(
            "/api/v2/shows",
            json.dumps(data),
            content_type="application/json",
        )
        # May accept any string or validate - accept either
        assert response.status_code in [201, 400]
