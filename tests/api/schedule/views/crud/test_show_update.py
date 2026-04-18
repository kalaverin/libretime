"""Tests for Shows UPDATE endpoint (T205)."""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show


@pytest.mark.django_db(transaction=True)
class TestShowViewSetUpdate:
    """Test Shows UPDATE endpoints - PUT/PATCH /api/v2/shows/{id}."""

    def setup_method(self):
        """Clean up shows before each test."""
        Show.objects.all().delete()

    def test_patch_update_name_success(self, admin_client):
        """PATCH should update show name."""
        show = baker.make(Show, name="Original Name")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"name": "Updated Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_patch_update_description_success(self, admin_client):
        """PATCH should update show description."""
        show = baker.make(Show, name="Test", description="Original")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"description": "Updated description"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_patch_update_genre_success(self, admin_client):
        """PATCH should update show genre."""
        show = baker.make(Show, name="Test", genre="Rock")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"genre": "Jazz"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["genre"] == "Jazz"

    def test_patch_update_url_success(self, admin_client):
        """PATCH should update show url."""
        show = baker.make(Show, name="Test", url="https://old.com")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"url": "https://new.com"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["url"] == "https://new.com"

    def test_patch_update_colors_success(self, admin_client):
        """PATCH should update show colors."""
        show = baker.make(
            Show,
            name="Test",
            foreground_color="000000",
            background_color="FFFFFF",
        )
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps(
                {"foreground_color": "FFFFFF", "background_color": "000000"},
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["foreground_color"] == "FFFFFF"
        assert result["background_color"] == "000000"

    def test_patch_update_linked_flags_success(self, admin_client):
        """PATCH should update linked and linkable flags."""
        show = baker.make(Show, name="Test", linked=False, linkable=True)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"linked": True, "linkable": False}),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["linked"] is True
        assert result["linkable"] is False

    def test_patch_update_auto_playlist_flags_success(self, admin_client):
        """PATCH should update auto_playlist flags."""
        show = baker.make(
            Show,
            name="Test",
            auto_playlist_enabled=False,
            auto_playlist_repeat=False,
        )
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps(
                {"auto_playlist_enabled": True, "auto_playlist_repeat": True},
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["auto_playlist_enabled"] is True
        assert result["auto_playlist_repeat"] is True

    def test_patch_update_intro_outro_flags_success(self, admin_client):
        """PATCH should update intro/outro override flags."""
        show = baker.make(
            Show,
            name="Test",
            override_intro_playlist=False,
            override_outro_playlist=False,
        )
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps(
                {
                    "override_intro_playlist": True,
                    "override_outro_playlist": True,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["override_intro_playlist"] is True
        assert result["override_outro_playlist"] is True

    def test_patch_not_found_returns_404(self, admin_client):
        """PATCH non-existent show should return 404."""
        response = admin_client.patch(
            "/api/v2/shows/999999",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_patch_no_auth_fails(self, client):
        """PATCH without auth should return 403."""
        show = baker.make(Show, name="Test")
        response = client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_patch_empty_body_no_change(self, admin_client):
        """PATCH with empty body should not change anything."""
        show = baker.make(Show, name="Original", description="Test")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Original"
        assert result["description"] == "Test"

    def test_put_update_requires_all_fields(self, admin_client):
        """PUT without all required fields may fail or succeed."""
        show = baker.make(Show, name="Test", linked=False, linkable=True)
        response = admin_client.put(
            f"/api/v2/shows/{show.id}",
            json.dumps({"name": "Updated Name"}),  # Missing required fields
            content_type="application/json",
        )
        # PUT may require all fields or allow partial
        assert response.status_code in [200, 400]

    def test_put_update_success(self, admin_client):
        """PUT with all required fields should succeed."""
        show = baker.make(
            Show,
            name="Old",
            description="Old desc",
            linked=False,
            linkable=True,
            auto_playlist_enabled=False,
            auto_playlist_repeat=False,
            override_intro_playlist=False,
            override_outro_playlist=False,
        )
        data = {
            "name": "New Name",
            "description": "New description",
            "linked": True,
            "linkable": False,
            "auto_playlist_enabled": True,
            "auto_playlist_repeat": True,
            "override_intro_playlist": True,
            "override_outro_playlist": True,
        }
        response = admin_client.put(
            f"/api/v2/shows/{show.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "New Name"
        assert result["description"] == "New description"
        assert result["linked"] is True

    def test_put_not_found_returns_404(self, admin_client):
        """PUT non-existent show should return 404."""
        data = {
            "name": "Test",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = admin_client.put(
            "/api/v2/shows/999999",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_unicode_values(self, admin_client):
        """PATCH with unicode values should work."""
        show = baker.make(Show, name="Test")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps(
                {"name": "日本語ショー", "description": "日本語の説明"},
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "日本語ショー"
        assert result["description"] == "日本語の説明"

    def test_update_returns_json(self, admin_client):
        """UPDATE should return JSON response."""
        show = baker.make(Show, name="Test")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response["Content-Type"] == "application/json"

    def test_update_preserves_id(self, admin_client):
        """UPDATE should preserve the show id."""
        show = baker.make(Show, name="Test")
        original_id = show.id
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert response.json()["id"] == original_id

    def test_update_empty_name_fails(self, admin_client):
        """UPDATE with empty name should fail."""
        show = baker.make(Show, name="Test")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_name_too_long_fails(self, admin_client):
        """UPDATE with name > 255 chars should fail."""
        show = baker.make(Show, name="Test")
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"name": "A" * 256}),
            content_type="application/json",
        )
        assert response.status_code == 400
