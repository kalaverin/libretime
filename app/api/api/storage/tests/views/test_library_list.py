"""Tests for Library LIST endpoint (T197)."""

import json

import pytest

from model_bakery import baker

from api.storage.models import Library


@pytest.mark.django_db(transaction=True)
class TestLibraryViewSetList:
    """Test Libraries LIST endpoint - GET /api/v2/libraries."""

    def setup_method(self):
        """Clean up libraries before each test."""
        Library.objects.all().delete()

    def test_list_libraries_endpoint_available(self, api_client):
        """LIST endpoint should be accessible with API key."""
        response = api_client.get("/api/v2/libraries")
        assert response.status_code == 200

    def test_list_returns_json(self, api_client):
        """LIST should return JSON response."""
        response = api_client.get("/api/v2/libraries")
        assert response["Content-Type"] == "application/json"

    def test_list_empty_when_no_libraries(self, api_client):
        """LIST should return empty list when no libraries exist."""
        response = api_client.get("/api/v2/libraries")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_all_libraries(self, api_client):
        """LIST should return all existing libraries."""
        lib1 = baker.make(
            Library,
            code="music",
            name="Music",
            description="Music library",
        )
        lib2 = baker.make(
            Library,
            code="podcast",
            name="Podcast",
            description="Podcast library",
        )
        lib3 = baker.make(
            Library,
            code="ads",
            name="Ads",
            description="Ads library",
        )

        response = api_client.get("/api/v2/libraries")
        data = response.json()
        assert len(data) == 3
        codes = {item["code"] for item in data}
        assert codes == {"music", "podcast", "ads"}

    def test_list_response_structure(self, api_client):
        """LIST response should have all model fields."""
        baker.make(Library, code="test", name="Test", description="Test lib")

        response = api_client.get("/api/v2/libraries")
        data = response.json()
        assert len(data) == 1
        lib_data = data[0]

        assert "id" in lib_data
        assert "code" in lib_data
        assert "name" in lib_data
        assert "description" in lib_data
        assert "enabled" in lib_data
        assert "analyze_cue_points" in lib_data

    def test_list_field_types(self, api_client):
        """LIST should return correct data types."""
        baker.make(
            Library,
            code="test",
            name="Test Library",
            description="A test lib",
            enabled=True,
            analyze_cue_points=False,
        )

        response = api_client.get("/api/v2/libraries")
        data = response.json()[0]

        assert isinstance(data["id"], int)
        assert isinstance(data["code"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["description"], (str, type(None)))
        assert isinstance(data["enabled"], bool)
        assert isinstance(data["analyze_cue_points"], bool)

    def test_list_code_unique_constraint(self, api_client):
        """Library code should be unique."""
        baker.make(
            Library,
            code="unique",
            name="First",
            description="First lib",
        )
        # Creating another with same code should fail
        with pytest.raises(Exception):  # IntegrityError
            baker.make(
                Library,
                code="unique",
                name="Second",
                description="Second lib",
            )

    def test_list_enabled_filtering(self, api_client):
        """Test listing with enabled/disabled libraries."""
        enabled_lib = baker.make(
            Library,
            code="enabled",
            name="Enabled",
            description="Enabled lib",
            enabled=True,
        )
        disabled_lib = baker.make(
            Library,
            code="disabled",
            name="Disabled",
            description="Disabled lib",
            enabled=False,
        )

        response = api_client.get("/api/v2/libraries")
        data = response.json()

        # Both should be listed (no filtering by default)
        codes = {item["code"] for item in data}
        assert "enabled" in codes
        assert "disabled" in codes

    def test_list_analyze_cue_points_field(self, api_client):
        """Test analyze_cue_points field in response."""
        lib = baker.make(
            Library,
            code="cue",
            name="Cue Library",
            description="Cue lib",
            analyze_cue_points=True,
        )
        response = api_client.get("/api/v2/libraries")
        data = response.json()[0]
        assert data["analyze_cue_points"] is True

    def test_list_empty_description(self, api_client):
        """Library description can be empty."""
        lib = baker.make(
            Library,
            code="nodesc",
            name="No Desc",
            description="",
        )
        response = api_client.get("/api/v2/libraries")
        data = response.json()[0]
        assert data["description"] == ""

    def test_list_no_auth_returns_403(self, client):
        """LIST should return 403 without authentication."""
        response = client.get("/api/v2/libraries")
        assert response.status_code == 403

    def test_list_post_creates_library(self, api_client):
        """POST on LIST endpoint creates new library (ModelViewSet)."""
        data = {
            "code": "newlib",
            "name": "New Library",
            "description": "New lib",
        }
        response = api_client.post(
            "/api/v2/libraries",
            json.dumps(data),
            content_type="application/json",
        )
        # POST creates a new library (201), not 405
        assert response.status_code == 201

    def test_list_put_not_allowed(self, api_client):
        """PUT should not be allowed on LIST endpoint."""
        response = api_client.put(
            "/api/v2/libraries",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_list_patch_not_allowed(self, api_client):
        """PATCH should not be allowed on LIST endpoint."""
        response = api_client.patch(
            "/api/v2/libraries",
            {},
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_list_delete_not_allowed(self, api_client):
        """DELETE should not be allowed on LIST endpoint."""
        response = api_client.delete("/api/v2/libraries")
        assert response.status_code == 405

    def test_list_unicode_in_name(self, api_client):
        """LIST should handle unicode in library names."""
        lib = baker.make(
            Library,
            code="unicode",
            name="日本語",
            description="日本語説明",
        )
        response = api_client.get("/api/v2/libraries")
        data = response.json()[0]
        assert data["name"] == "日本語"
        assert data["description"] == "日本語説明"

    def test_list_long_code(self, api_client):
        """LIST should handle library with long code (up to 16 chars)."""
        lib = baker.make(
            Library,
            code="a" * 16,
            name="Long Code",
            description="Long code lib",
        )
        response = api_client.get("/api/v2/libraries")
        data = response.json()[0]
        assert data["code"] == "a" * 16
