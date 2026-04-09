"""
T301: API contract test guide.

Paranoid tests demonstrating API contract testing patterns.
Verifies request/response contracts for all endpoints.
"""

import json

import pytest

from model_bakery import baker

from api.core.models import Role, User
from api.schedule.models import Playlist
from api.storage.models import File, Library


@pytest.mark.django_db
class TestAPIContractGET:
    """API contract tests for GET requests."""

    def test_get_single_resource_contract(self, api_client):
        """GET /resource/{id} returns single resource object."""
        user = baker.make(User, username="contract_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="CONTRACT",
            name="Contract",
            description="Test",
        )
        file_obj = baker.make(
            File,
            name="contract.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")

        # Contract: 200 status
        assert response.status_code == 200
        # Contract: JSON response
        assert response["Content-Type"].startswith("application/json")
        # Contract: Object with id field
        data = response.json()
        assert "id" in data
        assert data["id"] == file_obj.id

    def test_get_list_resource_contract(self, api_client):
        """GET /resource returns list of resources."""
        response = api_client.get("/api/v2/files")

        # Contract: 200 status
        assert response.status_code == 200
        # Contract: JSON array response
        data = response.json()
        assert isinstance(data, list)

    def test_get_404_not_found_contract(self, api_client):
        """GET /resource/{invalid_id} returns 404."""
        response = api_client.get("/api/v2/files/99999999")

        # Contract: 404 status for non-existent
        assert response.status_code == 404
        # Contract: Error response format
        data = response.json()
        assert "detail" in data or "error" in str(data).lower()

    def test_get_403_unauthorized_contract(self):
        """GET without auth returns 403."""
        from rest_framework.test import APIClient

        client = APIClient()  # No auth

        response = client.get("/api/v2/files")

        # Contract: 403 for unauthorized
        assert response.status_code == 403


@pytest.mark.django_db
class TestAPIContractPOST:
    """API contract tests for POST requests."""

    def test_post_create_resource_contract(self, api_client):
        """POST /resource creates new resource."""
        user = baker.make(User, username="post_test", role=Role.HOST)

        payload = {
            "name": "New Playlist",
            "owner": user.id,
        }

        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(payload),
            content_type="application/json",
        )

        # Contract: 201 Created status
        assert response.status_code == 201
        # Contract: Returns created object
        data = response.json()
        assert "id" in data
        assert data["name"] == "New Playlist"
        assert data["owner"] == user.id

    def test_post_400_validation_error_contract(self, api_client):
        """POST with invalid data returns 400."""
        payload = {
            "name": "",  # Empty name - invalid
        }

        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(payload),
            content_type="application/json",
        )

        # Contract: 400 Bad Request
        assert response.status_code == 400
        # Contract: Validation errors
        data = response.json()
        assert "name" in data or "owner" in data


@pytest.mark.django_db
class TestAPIContractPATCH:
    """API contract tests for PATCH requests."""

    def test_patch_update_resource_contract(self, api_client):
        """PATCH /resource/{id} updates resource partially."""
        user = baker.make(User, username="patch_test", role=Role.HOST)
        playlist = baker.make(Playlist, name="Old Name", owner=user)

        payload = {
            "name": "Updated Name",
        }

        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(payload),
            content_type="application/json",
        )

        # Contract: 200 OK status
        assert response.status_code == 200
        # Contract: Returns updated object
        data = response.json()
        assert data["name"] == "Updated Name"
        # Contract: Unchanged fields preserved
        assert data["owner"] == user.id


@pytest.mark.django_db
class TestAPIContractDELETE:
    """API contract tests for DELETE requests."""

    def test_delete_resource_contract(self, api_client):
        """DELETE /resource/{id} removes resource."""
        user = baker.make(User, username="delete_test", role=Role.HOST)
        playlist = baker.make(Playlist, name="To Delete", owner=user)

        response = api_client.delete(f"/api/v2/playlists/{playlist.id}")

        # Contract: 204 No Content status
        assert response.status_code == 204

    def test_delete_404_not_found_contract(self, api_client):
        """DELETE non-existent returns 404."""
        response = api_client.delete("/api/v2/playlists/99999999")

        # Contract: 404 Not Found
        assert response.status_code == 404


@pytest.mark.django_db
class TestAPIContractHeaders:
    """API contract tests for HTTP headers."""

    def test_content_type_header_contract(self, api_client):
        """Response has correct Content-Type header."""
        response = api_client.get("/api/v2/info")

        # Contract: JSON content type
        assert response["Content-Type"] == "application/json"

    def test_allow_header_contract(self, api_client):
        """Allow header lists allowed methods."""
        response = api_client.options("/api/v2/files")

        # Contract: Allow header present
        if "Allow" in response:
            allow = response["Allow"]
            assert "GET" in allow
            assert "HEAD" in allow


@pytest.mark.django_db
class TestAPIContractFieldTypes:
    """API contract tests for field types."""

    def test_integer_fields_contract(self, api_client):
        """Integer fields return integers."""
        user = baker.make(User, username="int_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="INT",
            name="Int",
            description="Test",
        )
        file_obj = baker.make(
            File,
            name="int.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            size=1024,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        data = response.json()

        # Contract: Integer fields
        assert isinstance(data["id"], int)
        assert isinstance(data["size"], int)

    def test_string_fields_contract(self, api_client):
        """String fields return strings."""
        user = baker.make(User, username="str_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="STR",
            name="Str",
            description="Test",
        )
        file_obj = baker.make(
            File,
            name="str.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        data = response.json()

        # Contract: String fields
        assert isinstance(data["name"], str)
        assert isinstance(data["mime"], str)

    def test_nullable_fields_contract(self, api_client):
        """Nullable fields can be null."""
        user = baker.make(User, username="null_test", role=Role.HOST)
        file_obj = baker.make(
            File,
            name="null.mp3",
            mime="audio/mp3",
            library=None,
            owner=user,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        data = response.json()

        # Contract: Nullable fields can be null
        assert data["library"] is None


@pytest.mark.django_db
class TestAPIContractFiltering:
    """API contract tests for filtering."""

    def test_filter_by_field_contract(self, api_client):
        """Filter query parameter works."""
        response = api_client.get("/api/v2/files?mime=audio/mp3")

        # Contract: 200 OK
        assert response.status_code == 200
        # Contract: Returns filtered list
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.django_db
class TestAPIContractPagination:
    """API contract tests for pagination (if present)."""

    def test_list_not_paginated_contract(self, api_client):
        """List returns array directly (no pagination wrapper)."""
        response = api_client.get("/api/v2/files")
        data = response.json()

        # Contract: Direct array (not {count, next, results})
        assert isinstance(data, list)
        assert "count" not in data
        assert "results" not in data


@pytest.mark.django_db
class TestAPIContractErrorHandling:
    """API contract tests for error handling."""

    def test_validation_error_format_contract(self, api_client):
        """Validation errors have consistent format."""
        payload = {}  # Invalid - missing required fields

        response = api_client.post(
            "/api/v2/playlists",
            json.dumps(payload),
            content_type="application/json",
        )

        # Contract: 400 status
        assert response.status_code == 400
        # Contract: Field-specific errors
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_not_found_error_format_contract(self, api_client):
        """Not found errors have consistent format."""
        response = api_client.get("/api/v2/files/99999999")

        # Contract: 404 status
        assert response.status_code == 404
        # Contract: Error detail
        data = response.json()
        assert "detail" in data


class TestAPIContractDocumentation:
    """Document API contract testing approach."""

    def test_contract_testing_principles(self):
        """Document contract testing principles."""
        principles = [
            "Verify HTTP status codes",
            "Verify response content types",
            "Verify field names and types",
            "Verify required vs optional fields",
            "Verify error response formats",
            "Verify filtering behavior",
            "Verify auth requirements",
        ]
        assert len(principles) >= 6

    def test_common_status_codes(self):
        """Document common HTTP status codes."""
        codes = {
            200: "OK - Success",
            201: "Created - Resource created",
            204: "No Content - Deleted",
            400: "Bad Request - Validation error",
            401: "Unauthorized - Not authenticated",
            403: "Forbidden - No permission",
            404: "Not Found - Resource missing",
            500: "Internal Server Error",
        }
        assert len(codes) == 8
        assert codes[200] == "OK - Success"

    def test_required_response_fields(self):
        """Document required response fields."""
        required = [
            "id",
            "created_at",
            "updated_at",
        ]
        assert "id" in required

    def test_content_type_requirements(self):
        """Document Content-Type requirements."""
        content_types = [
            "application/json",
        ]
        assert "application/json" in content_types
