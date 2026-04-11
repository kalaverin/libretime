"""
Comprehensive test matrix for VIEW (READ) operations across all roles.

LibreTime Permission Model:
- GUEST: Read-only viewer, sees ALL public content (schedule, shows, files, playlists, etc.)
- HOST: Sees ALL content + can CREATE/MODIFY own objects only
- MANAGER/ADMIN: Full access

All authenticated roles see the same content for VIEW operations.
Difference is in CREATE/UPDATE/DELETE permissions.

Usage:
    cd app/api && uv run pytest api/tests/test_role_view_matrix.py -v
"""

from typing import Any

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.podcasts.models import Podcast
from api.schedule.models import (
    Playlist,
    Show,
    SmartBlock,
    Webstream,
)
from api.storage.models import File


# =============================================================================
# Helper Functions
# =============================================================================

def get_results(response) -> list[dict[str, Any]]:
    """Extract results from response (handles paginated and non-paginated)."""
    if isinstance(response.data, dict):
        return response.data.get("results", [])
    return response.data


# =============================================================================
# Base Test Class
# =============================================================================

@pytest.mark.django_db
class TestViewPermissionMatrix:
    """
    Test matrix: VIEW operations for all roles.

    Key Principle: All authenticated users see the SAME content.
    Difference is in modification permissions, not view.
    """

    # ==========================================================================
    # GUEST Role Tests
    # ==========================================================================

    def test_guest_can_view_shows(self, guest_client, faker):
        """GUEST can view shows (public broadcast schedule)."""
        show = baker.make(Show, name=f"Public Show {faker.uuid4()[:8]}")

        response = guest_client.get("/api/v2/shows")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == show.id for item in results)

    def test_guest_can_view_playlists(self, guest_client, faker):
        """GUEST can view all playlists (public content)."""
        owner = baker.make(User, role=Role.HOST)
        playlist = baker.make(
            Playlist, name=f"Playlist {faker.uuid4()[:8]}", owner=owner
        )

        response = guest_client.get("/api/v2/playlists")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == playlist.id for item in results)

    def test_guest_can_view_smartblocks(self, guest_client, faker):
        """GUEST can view all smart blocks."""
        owner = baker.make(User, role=Role.HOST)
        block = baker.make(
            SmartBlock, name=f"Block {faker.uuid4()[:8]}", owner=owner
        )

        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == block.id for item in results)

    def test_guest_can_view_webstreams(self, guest_client, faker):
        """GUEST can view all webstreams (public content)."""
        owner = baker.make(User, role=Role.HOST)
        stream = baker.make(
            Webstream,
            name=f"Stream {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=owner,
        )

        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == stream.id for item in results)

    def test_guest_can_view_podcasts(self, guest_client, faker):
        """GUEST can view all podcasts."""
        owner = baker.make(User, role=Role.HOST)
        podcast = baker.make(
            Podcast,
            title=f"Podcast {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=owner,
        )

        response = guest_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == podcast.id for item in results)

    def test_guest_can_view_files(self, guest_client, faker):
        """GUEST can view all files (public media library)."""
        owner = baker.make(User, role=Role.HOST)
        file_obj = baker.make(File, owner=owner)

        response = guest_client.get("/api/v2/files")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == file_obj.id for item in results)

    # ==========================================================================
    # HOST Role Tests - Sees ALL (same as GUEST)
    # ==========================================================================

    def test_host_can_view_all_playlists(self, host_client, host_user, faker):
        """HOST can view ALL playlists (not just own) - same as GUEST."""
        # Create playlist by other user
        other_user = baker.make(User, role=Role.HOST)
        other_playlist = baker.make(
            Playlist,
            name=f"Other Playlist {faker.uuid4()[:8]}",
            owner=other_user,
        )

        response = host_client.get("/api/v2/playlists")
        assert response.status_code == 200
        results = get_results(response)

        # HOST sees ALL playlists (public content)
        assert any(
            item["id"] == other_playlist.id for item in results
        ), "HOST should see ALL playlists"

    def test_host_can_view_all_smartblocks(self, host_client, faker):
        """HOST can view ALL smart blocks."""
        other_user = baker.make(User, role=Role.HOST)
        block = baker.make(
            SmartBlock,
            name=f"Block {faker.uuid4()[:8]}",
            owner=other_user,
            kind="static",
        )

        response = host_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == block.id for item in results)

    def test_host_can_view_all_webstreams(self, host_client, faker):
        """HOST can view ALL webstreams (public content)."""
        other_user = baker.make(User, role=Role.HOST)
        stream = baker.make(
            Webstream,
            name=f"Stream {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=other_user,
        )

        response = host_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == stream.id for item in results)

    def test_host_can_view_all_files(self, host_client, faker):
        """HOST can view ALL files."""
        other_user = baker.make(User, role=Role.HOST)
        file_obj = baker.make(File, owner=other_user)

        response = host_client.get("/api/v2/files")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == file_obj.id for item in results)

    # ==========================================================================
    # MANAGER Role Tests - Also Sees ALL
    # ==========================================================================

    def test_manager_can_view_all_playlists(self, manager_client, faker):
        """MANAGER sees all playlists (same view as GUEST/HOST)."""
        host = baker.make(User, role=Role.HOST)
        playlist = baker.make(
            Playlist, name=f"Host Playlist {faker.uuid4()[:8]}", owner=host
        )

        response = manager_client.get("/api/v2/playlists")
        assert response.status_code == 200
        results = get_results(response)
        assert any(item["id"] == playlist.id for item in results)

    def test_manager_can_view_all_files(self, manager_client, faker):
        """MANAGER sees all files."""
        host = baker.make(User, role=Role.HOST)
        file_obj = baker.make(File, owner=host)

        response = manager_client.get("/api/v2/files")
        assert response.status_code == 200
        results = get_results(response)
        assert file_obj.id in [item["id"] for item in results]

    # ==========================================================================
    # Cross-Role Comparison - All See Same Content
    # ==========================================================================

    def test_all_roles_see_same_content_for_view(
        self, guest_client, host_client, manager_client, faker
    ):
        """GUEST, HOST, MANAGER all see the same content when viewing."""
        # Create test data
        host = baker.make(User, role=Role.HOST)
        playlist = baker.make(Playlist, owner=host)
        show = baker.make(Show)

        # GUEST sees
        guest_playlists = get_results(guest_client.get("/api/v2/playlists"))
        guest_shows = get_results(guest_client.get("/api/v2/shows"))

        # HOST sees
        host_playlists = get_results(host_client.get("/api/v2/playlists"))
        host_shows = get_results(host_client.get("/api/v2/shows"))

        # MANAGER sees
        manager_playlists = get_results(manager_client.get("/api/v2/playlists"))
        manager_shows = get_results(manager_client.get("/api/v2/shows"))

        # All see the same objects
        guest_ids = {p["id"] for p in guest_playlists}
        host_ids = {p["id"] for p in host_playlists}
        manager_ids = {p["id"] for p in manager_playlists}

        assert playlist.id in guest_ids
        assert playlist.id in host_ids
        assert playlist.id in manager_ids

        assert show.id in {s["id"] for s in guest_shows}
        assert show.id in {s["id"] for s in host_shows}
        assert show.id in {s["id"] for s in manager_shows}


# =============================================================================
# Single Object Retrieval Tests
# =============================================================================

@pytest.mark.django_db
class TestViewSingleObject:
    """Tests for retrieving single objects (detail view)."""

    def test_guest_can_retrieve_any_playlist(self, guest_client, faker):
        """GUEST can retrieve any playlist by ID."""
        owner = baker.make(User, role=Role.HOST)
        playlist = baker.make(Playlist, owner=owner)

        response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id

    def test_host_can_retrieve_any_playlist(self, host_client, faker):
        """HOST can retrieve any playlist (not just own)."""
        other_user = baker.make(User, role=Role.HOST)
        playlist = baker.make(Playlist, owner=other_user)

        response = host_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id

    def test_manager_can_retrieve_any_playlist(self, manager_client, faker):
        """MANAGER can retrieve any playlist."""
        host = baker.make(User, role=Role.HOST)
        playlist = baker.make(Playlist, owner=host)

        response = manager_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id


# =============================================================================
# List vs Detail Consistency
# =============================================================================

@pytest.mark.django_db
class TestViewListDetailConsistency:
    """Ensure list and detail views show consistent data."""

    def test_object_in_list_is_accessible_in_detail(self, guest_client, faker):
        """Any object visible in list should be accessible by ID."""
        owner = baker.make(User, role=Role.HOST)
        playlist = baker.make(Playlist, owner=owner)

        # Get list
        list_response = guest_client.get("/api/v2/playlists")
        list_results = get_results(list_response)
        list_ids = {item["id"] for item in list_results}

        # Should be in list
        assert playlist.id in list_ids

        # Should be accessible by ID
        detail_response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        assert detail_response.status_code == 200
        assert detail_response.data["id"] == playlist.id
