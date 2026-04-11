"""
RED TEAM: T378/T382/T384/T387 - Show Anonymous Access Security Tests.

Verifies that anonymous (unauthenticated) access to Show endpoints is blocked.
These tests confirm the fixes for:
- T378: Anonymous cannot CREATE shows
- T382: Anonymous cannot RETRIEVE shows
- T384: Anonymous cannot UPDATE shows
- T387: Anonymous cannot DELETE shows
"""

import pytest

from model_bakery import baker

from api.schedule.models import Show


@pytest.mark.django_db
class TestShowAnonymousCreate:
    """T378: Verify anonymous CREATE is blocked."""

    def test_anonymous_create_show_blocked(self, anonymous_client):
        """Anonymous user cannot create shows - returns 403."""
        data = {
            "name": "Anonymous Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = anonymous_client.post(
            "/api/v2/shows",
            data,
            format="json",
        )
        # Should be rejected - either 403 (permission denied) or 401 (unauthorized)
        assert response.status_code in [
            401,
            403,
        ], f"T378 NOT FIXED: Anonymous CREATE returned {response.status_code}, expected 401/403"

    def test_anonymous_create_show_with_extra_fields_blocked(
        self, anonymous_client,
    ):
        """Anonymous cannot create shows even with extra fields."""
        data = {
            "name": "Hacked Show",
            "description": "Created by anonymous",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
            "id": 99999,  # Try to force ID
        }
        response = anonymous_client.post("/api/v2/shows", data, format="json")
        assert response.status_code in [
            401,
            403,
        ], f"T378 NOT FIXED: Anonymous CREATE with extras returned {response.status_code}"


@pytest.mark.django_db
class TestShowAnonymousRetrieve:
    """T382: Verify anonymous RETRIEVE is blocked."""

    def test_anonymous_list_shows_blocked(self, anonymous_client):
        """Anonymous user cannot list shows - returns 403."""
        # Create a show first
        baker.make(Show, name="Test Show")

        response = anonymous_client.get("/api/v2/shows")
        # Should be rejected
        assert response.status_code in [
            401,
            403,
        ], f"T382 NOT FIXED: Anonymous LIST returned {response.status_code}, expected 401/403"

    def test_anonymous_retrieve_single_show_blocked(self, anonymous_client):
        """Anonymous user cannot retrieve individual show - returns 403."""
        show = baker.make(Show, name="Test Show")

        response = anonymous_client.get(f"/api/v2/shows/{show.id}")
        # Should be rejected
        assert response.status_code in [
            401,
            403,
        ], f"T382 NOT FIXED: Anonymous RETRIEVE returned {response.status_code}, expected 401/403"

    def test_anonymous_retrieve_nonexistent_blocked(self, anonymous_client):
        """Anonymous cannot retrieve even non-existent shows."""
        response = anonymous_client.get("/api/v2/shows/99999")
        assert response.status_code in [
            401,
            403,
        ], f"T382 NOT FIXED: Anonymous RETRIEVE returned {response.status_code}, expected 401/403"


@pytest.mark.django_db
class TestShowAnonymousUpdate:
    """T384: Verify anonymous UPDATE is blocked."""

    def test_anonymous_patch_show_blocked(self, anonymous_client):
        """Anonymous user cannot PATCH shows - returns 403."""
        show = baker.make(Show, name="Original Name")

        response = anonymous_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "Hacked Name"},
            format="json",
        )
        assert response.status_code in [
            401,
            403,
        ], f"T384 NOT FIXED: Anonymous PATCH returned {response.status_code}, expected 401/403"
        # Verify show was not modified
        show.refresh_from_db()
        assert (
            show.name == "Original Name"
        ), "T384: Show was modified despite blocked request"

    def test_anonymous_put_show_blocked(self, anonymous_client):
        """Anonymous user cannot PUT shows - returns 403."""
        show = baker.make(Show, name="Original Name")

        response = anonymous_client.put(
            f"/api/v2/shows/{show.id}",
            {
                "name": "Hacked Name",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )
        assert response.status_code in [
            401,
            403,
        ], f"T384 NOT FIXED: Anonymous PUT returned {response.status_code}, expected 401/403"
        # Verify show was not modified
        show.refresh_from_db()
        assert (
            show.name == "Original Name"
        ), "T384: Show was modified despite blocked request"


@pytest.mark.django_db
class TestShowAnonymousDelete:
    """T387: Verify anonymous DELETE is blocked."""

    def test_anonymous_delete_show_blocked(self, anonymous_client):
        """Anonymous user cannot DELETE shows - returns 403."""
        show = baker.make(Show, name="Show to Delete")
        show_id = show.id

        response = anonymous_client.delete(f"/api/v2/shows/{show_id}")
        assert response.status_code in [
            401,
            403,
        ], f"T387 NOT FIXED: Anonymous DELETE returned {response.status_code}, expected 401/403"
        # Verify show still exists
        assert Show.objects.filter(
            id=show_id,
        ).exists(), "T387: Show was deleted despite blocked request"

    def test_anonymous_delete_all_shows_blocked(self, anonymous_client):
        """Anonymous cannot enumerate and delete all shows."""
        # Create multiple shows
        shows = [baker.make(Show, name=f"Show {i}") for i in range(3)]
        show_ids = [s.id for s in shows]

        # Try to delete each one
        for show_id in show_ids:
            response = anonymous_client.delete(f"/api/v2/shows/{show_id}")
            assert response.status_code in [
                401,
                403,
            ], f"T387 NOT FIXED: Anonymous DELETE returned {response.status_code}"

        # Verify all shows still exist
        for show_id in show_ids:
            assert Show.objects.filter(
                id=show_id,
            ).exists(), f"T387: Show {show_id} was deleted"


@pytest.mark.django_db
class TestShowAnonymousAccessComprehensive:
    """Comprehensive anonymous access tests."""

    def test_anonymous_no_access_to_any_endpoint(self, anonymous_client):
        """Anonymous has no access to any Show endpoint."""
        show = baker.make(Show, name="Test Show")

        endpoints = [
            ("GET", "/api/v2/shows"),
            ("GET", f"/api/v2/shows/{show.id}"),
            ("POST", "/api/v2/shows"),
            ("PATCH", f"/api/v2/shows/{show.id}"),
            ("PUT", f"/api/v2/shows/{show.id}"),
            ("DELETE", f"/api/v2/shows/{show.id}"),
        ]

        for method, url in endpoints:
            if method == "GET":
                response = anonymous_client.get(url)
            elif method == "POST":
                response = anonymous_client.post(url, {})
            elif method == "PATCH":
                response = anonymous_client.patch(url, {})
            elif method == "PUT":
                response = anonymous_client.put(url, {})
            elif method == "DELETE":
                response = anonymous_client.delete(url)

            assert response.status_code in [
                401,
                403,
            ], f"T378/T382/T384/T387: Anonymous {method} {url} returned {response.status_code}"

    def test_authenticated_users_have_access(self, api_client):
        """Authenticated users (via API-Key) have proper access."""
        # LIST
        response = api_client.get("/api/v2/shows")
        assert response.status_code == 200, "Authenticated LIST should work"

        # CREATE
        data = {
            "name": "Auth Show",
            "linked": False,
            "linkable": True,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }
        response = api_client.post("/api/v2/shows", data, format="json")
        assert response.status_code == 201, "Authenticated CREATE should work"
