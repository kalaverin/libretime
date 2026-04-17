"""
T291: Pagination tests.

Tests for pagination behavior across API endpoints.
Note: Most endpoints return all results without pagination.
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist, Show
from api.storage.models import File, Library


@pytest.mark.django_db
class TestPaginationNotEnabled:
    """Test that pagination is not enabled (returns all results)."""

    def test_files_list_no_pagination(self, api_client):
        """Files endpoint returns all results without pagination."""
        user = baker.make(User, username="file_test")
        library = baker.make(
            Library,
            code="TEST",
            name="Test",
            description="Test",
        )

        # Create multiple files
        for i in range(5):
            baker.make(
                File,
                name=f"file{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )

        response = api_client.get("/api/v2/files")

        assert response.status_code == 200
        data = response.json()
        # Returns array directly, not paginated response
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_playlists_list_no_pagination(self, api_client):
        """Playlists endpoint returns all results without pagination."""
        user = baker.make(User, username="playlist_test")

        # Create multiple playlists
        for i in range(5):
            baker.make(Playlist, name=f"Playlist {i}", owner=user)

        response = api_client.get("/api/v2/playlists")

        assert response.status_code == 200
        data = response.json()
        # Returns array directly
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_shows_list_no_pagination(self, api_client):
        """Shows endpoint returns all results without pagination."""
        # Create multiple shows
        for i in range(5):
            baker.make(Show, name=f"Show {i}")

        response = api_client.get("/api/v2/shows")

        assert response.status_code == 200
        data = response.json()
        # Returns array directly
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_response_has_no_pagination_fields(self, api_client):
        """Response should not have pagination fields (count, next, previous)."""
        user = baker.make(User, username="test")
        library = baker.make(
            Library,
            code="TEST2",
            name="Test",
            description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        response = api_client.get("/api/v2/files")

        assert response.status_code == 200
        data = response.json()
        # Should be list, not dict with pagination
        assert isinstance(data, list)
        # No pagination fields
        if isinstance(data, dict):
            assert "count" not in data
            assert "next" not in data
            assert "previous" not in data
            assert "results" not in data


@pytest.mark.django_db
class TestListFilteringWithoutPagination:
    """Test that filtering works without pagination."""

    def test_filtered_list_returns_matching(self, api_client):
        """Filtered list returns matching results without pagination."""
        user = baker.make(User, username="filter_test")
        library = baker.make(
            Library,
            code="TEST3",
            name="Test",
            description="Test",
        )

        # Create files
        for i in range(5):
            baker.make(
                File,
                name=f"file{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )

        # Filter by mime type
        response = api_client.get("/api/v2/files?mime=audio/mp3")

        assert response.status_code == 200
        data = response.json()
        # Returns array directly, not paginated
        assert isinstance(data, list)
        # All matching files returned
        assert len(data) >= 5
