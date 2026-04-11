"""
Comprehensive test matrix for DETAIL (single object retrieval) operations.

Tests that all roles can retrieve specific objects by ID.

Permission Matrix (DETAIL - GET /{entity}/{id}):
| Entity      | GUEST | HOST | MANAGER | ADMIN |
|-------------|-------|------|---------|-------|
| Show        | 200   | 200  | 200     | 200   |
| Playlist    | 200   | 200  | 200     | 200   |
| SmartBlock  | 200   | 200  | 200     | 200   |
| File        | 200   | 200  | 200     | 200   |
| Webstream   | 200   | 200  | 200     | 200   |
| Podcast     | 200   | 200  | 200     | 200   |

Key Principle: All authenticated users can view any object by ID.
Difference is in modification permissions, not view.

Usage:
    cd app/api && uv run pytest api/tests/test_role_detail_matrix.py -v
"""

from typing import Any

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.podcasts.models import Podcast
from api.schedule.models import Playlist, Show, SmartBlock, Webstream
from api.storage.models import File


# =============================================================================
# Test Data Generators
# =============================================================================

def create_test_entity(entity_type: str, owner: User | None = None, faker=None):
    """Create a test entity of given type."""
    if entity_type == "show":
        return baker.make(
            Show,
            name=f"Test Show {faker.uuid4()[:8] if faker else 'test'}",
            description="Test description",
            genre="Music",
            background_color="FFFFFF",
            foreground_color="000000",
            linked=False,
            linkable=False,
            auto_playlist_enabled=False,
            auto_playlist_repeat=False,
            override_intro_playlist=False,
            override_outro_playlist=False,
        )
    elif entity_type == "playlist":
        return baker.make(
            Playlist,
            name=f"Test Playlist {faker.uuid4()[:8] if faker else 'test'}",
            owner=owner,
        )
    elif entity_type == "smartblock":
        return baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8] if faker else 'test'}",
            owner=owner,
            kind="static",
        )
    elif entity_type == "webstream":
        return baker.make(
            Webstream,
            name=f"Test Stream {faker.uuid4()[:8] if faker else 'test'}",
            url=faker.url() if faker else "http://test.com/stream",
            owner=owner,
        )
    elif entity_type == "podcast":
        return baker.make(
            Podcast,
            title=f"Test Podcast {faker.uuid4()[:8] if faker else 'test'}",
            url=faker.url() if faker else "http://test.com/podcast",
            owner=owner,
        )
    elif entity_type == "file":
        return baker.make(File, owner=owner)
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")


# =============================================================================
# Base Test Class
# =============================================================================

@pytest.mark.django_db
class TestDetailPermissionMatrix:
    """
    Test matrix: DETAIL (GET single object) for all roles.
    
    All authenticated roles can retrieve any object by ID.
    """

    # ==========================================================================
    # GUEST Role Tests - Can Retrieve Any Object
    # ==========================================================================

    def test_guest_can_retrieve_show_detail(self, guest_client, faker):
        """GUEST can retrieve show by ID."""
        show = create_test_entity("show", faker=faker)
        
        response = guest_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        assert response.data["id"] == show.id
        assert response.data["name"] == show.name

    def test_guest_can_retrieve_playlist_detail(self, guest_client, faker):
        """GUEST can retrieve any playlist by ID."""
        owner = baker.make(User, role=Role.HOST)
        playlist = create_test_entity("playlist", owner=owner, faker=faker)
        
        response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id

    def test_guest_can_retrieve_smartblock_detail(self, guest_client, faker):
        """GUEST can retrieve any smartblock by ID."""
        owner = baker.make(User, role=Role.HOST)
        block = create_test_entity("smartblock", owner=owner, faker=faker)
        
        response = guest_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200
        assert response.data["id"] == block.id

    def test_guest_can_retrieve_webstream_detail(self, guest_client, faker):
        """GUEST can retrieve any webstream by ID."""
        owner = baker.make(User, role=Role.HOST)
        stream = create_test_entity("webstream", owner=owner, faker=faker)
        
        response = guest_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 200
        assert response.data["id"] == stream.id

    def test_guest_can_retrieve_podcast_detail(self, guest_client, faker):
        """GUEST can retrieve any podcast by ID."""
        owner = baker.make(User, role=Role.HOST)
        podcast = create_test_entity("podcast", owner=owner, faker=faker)
        
        response = guest_client.get(f"/api/v2/podcasts/{podcast.id}")
        assert response.status_code == 200
        assert response.data["id"] == podcast.id

    def test_guest_can_retrieve_file_detail(self, guest_client, faker):
        """GUEST can retrieve any file by ID."""
        owner = baker.make(User, role=Role.HOST)
        file_obj = create_test_entity("file", owner=owner, faker=faker)
        
        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        assert response.data["id"] == file_obj.id

    # ==========================================================================
    # HOST Role Tests - Can Retrieve Any Object (Not Just Own)
    # ==========================================================================

    def test_host_can_retrieve_own_playlist_detail(self, host_client, host_user, faker):
        """HOST can retrieve own playlist by ID."""
        playlist = create_test_entity("playlist", owner=host_user, faker=faker)
        
        response = host_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id

    def test_host_can_retrieve_other_playlist_detail(self, host_client, faker):
        """HOST can retrieve other user's playlist by ID."""
        other_user = baker.make(User, role=Role.HOST)
        playlist = create_test_entity("playlist", owner=other_user, faker=faker)
        
        response = host_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id

    def test_host_can_retrieve_other_smartblock_detail(self, host_client, faker):
        """HOST can retrieve other user's smartblock by ID."""
        other_user = baker.make(User, role=Role.HOST)
        block = create_test_entity("smartblock", owner=other_user, faker=faker)
        
        response = host_client.get(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 200
        assert response.data["id"] == block.id

    def test_host_can_retrieve_other_webstream_detail(self, host_client, faker):
        """HOST can retrieve other user's webstream by ID."""
        other_user = baker.make(User, role=Role.HOST)
        stream = create_test_entity("webstream", owner=other_user, faker=faker)
        
        response = host_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 200
        assert response.data["id"] == stream.id

    def test_host_can_retrieve_other_podcast_detail(self, host_client, faker):
        """HOST can retrieve other user's podcast by ID."""
        other_user = baker.make(User, role=Role.HOST)
        podcast = create_test_entity("podcast", owner=other_user, faker=faker)
        
        response = host_client.get(f"/api/v2/podcasts/{podcast.id}")
        assert response.status_code == 200
        assert response.data["id"] == podcast.id

    def test_host_can_retrieve_other_file_detail(self, host_client, faker):
        """HOST can retrieve other user's file by ID."""
        other_user = baker.make(User, role=Role.HOST)
        file_obj = create_test_entity("file", owner=other_user, faker=faker)
        
        response = host_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        assert response.data["id"] == file_obj.id

    # ==========================================================================
    # MANAGER Role Tests - Can Retrieve Any Object
    # ==========================================================================

    def test_manager_can_retrieve_host_playlist_detail(self, manager_client, faker):
        """MANAGER can retrieve HOST's playlist by ID."""
        host = baker.make(User, role=Role.HOST)
        playlist = create_test_entity("playlist", owner=host, faker=faker)
        
        response = manager_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id

    def test_manager_can_retrieve_any_file_detail(self, manager_client, faker):
        """MANAGER can retrieve any file by ID."""
        host = baker.make(User, role=Role.HOST)
        file_obj = create_test_entity("file", owner=host, faker=faker)
        
        response = manager_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        assert response.data["id"] == file_obj.id

    # ==========================================================================
    # ADMIN Role Tests - Can Retrieve Any Object
    # ==========================================================================

    def test_admin_can_retrieve_any_playlist_detail(self, admin_client, faker):
        """ADMIN can retrieve any playlist by ID."""
        host = baker.make(User, role=Role.HOST)
        playlist = create_test_entity("playlist", owner=host, faker=faker)
        
        response = admin_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        assert response.data["id"] == playlist.id

    def test_admin_can_retrieve_any_show_detail(self, admin_client, faker):
        """ADMIN can retrieve any show by ID."""
        show = create_test_entity("show", faker=faker)
        
        response = admin_client.get(f"/api/v2/shows/{show.id}")
        assert response.status_code == 200
        assert response.data["id"] == show.id


# =============================================================================
# Cross-Role Detail Consistency Tests
# =============================================================================

@pytest.mark.django_db
class TestDetailCrossRoleConsistency:
    """
    Verify all roles see the same object data in detail view.
    """

    def test_all_roles_see_same_playlist_data(
        self, guest_client, host_client, manager_client, admin_client, faker
    ):
        """All roles retrieve identical playlist data."""
        owner = baker.make(User, role=Role.HOST)
        playlist = create_test_entity("playlist", owner=owner, faker=faker)
        
        # Each role retrieves
        guest_data = guest_client.get(f"/api/v2/playlists/{playlist.id}").data
        host_data = host_client.get(f"/api/v2/playlists/{playlist.id}").data
        manager_data = manager_client.get(f"/api/v2/playlists/{playlist.id}").data
        admin_data = admin_client.get(f"/api/v2/playlists/{playlist.id}").data
        
        # All see same data
        assert guest_data["id"] == host_data["id"] == manager_data["id"] == admin_data["id"]
        assert guest_data["name"] == host_data["name"] == manager_data["name"] == admin_data["name"]

    def test_all_roles_see_same_show_data(
        self, guest_client, host_client, manager_client, admin_client, faker
    ):
        """All roles retrieve identical show data."""
        show = create_test_entity("show", faker=faker)
        
        guest_data = guest_client.get(f"/api/v2/shows/{show.id}").data
        host_data = host_client.get(f"/api/v2/shows/{show.id}").data
        manager_data = manager_client.get(f"/api/v2/shows/{show.id}").data
        admin_data = admin_client.get(f"/api/v2/shows/{show.id}").data
        
        assert guest_data["id"] == host_data["id"] == manager_data["id"] == admin_data["id"]
        assert guest_data["name"] == host_data["name"] == manager_data["name"] == admin_data["name"]


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.django_db
class TestDetailEdgeCases:
    """Edge cases for detail retrieval."""

    def test_retrieve_nonexistent_object_returns_404(self, guest_client):
        """GET non-existent ID returns 404 (not 403)."""
        response = guest_client.get("/api/v2/playlists/999999")
        assert response.status_code == 404

    def test_retrieve_with_invalid_id_format(self, guest_client):
        """GET with invalid ID format returns 404."""
        response = guest_client.get("/api/v2/playlists/invalid-id")
        assert response.status_code == 404

    def test_detail_contains_full_object_data(self, guest_client, faker):
        """Detail view returns complete object data."""
        owner = baker.make(User, role=Role.HOST)
        playlist = create_test_entity("playlist", owner=owner, faker=faker)
        
        response = guest_client.get(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code == 200
        
        # Should have essential fields
        assert "id" in response.data
        assert "name" in response.data
        assert "owner" in response.data
        assert "created_at" in response.data or "updated_at" in response.data
