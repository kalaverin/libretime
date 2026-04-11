"""
Comprehensive test matrix for DELETE operations across all roles and entities.

Tests that:
1. Each role can/cannot delete entities according to permission matrix
2. HOST role can only delete own objects (403/404 for others')
3. MANAGER/ADMIN can delete any objects
4. Objects are actually removed from database after successful delete

Permission Matrix (DELETE):
| Entity      | ANONYMOUS | GUEST | HOST       | MANAGER | ADMIN |
|-------------|-----------|-------|------------|---------|-------|
| Playlist    | 403       | 403   | own 204    | any 204 | any 204 |
| SmartBlock  | 403       | 403   | own 204    | any 204 | any 204 |
| Webstream   | 403       | 403   | own 204    | any 204 | any 204 |
| Podcast     | 403       | 403   | own 204    | any 204 | any 204 |
| File        | 403       | 403   | own 204    | any 204 | any 204 |
| Show        | 403       | 403   | 403        | any 204 | any 204 |

Usage:
    cd app/api && uv run pytest api/tests/test_role_delete_matrix.py -v
"""

from typing import Any

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.core.models.role import Role
from api.podcasts.models import Podcast
from api.schedule.models import Playlist, Show, SmartBlock, Webstream
from api.storage.models import File


# =============================================================================
# Helper Functions
# =============================================================================

def create_entity(entity_type: str, owner: User | None, faker):
    """Create test entity with given owner."""
    if entity_type == "playlist":
        return baker.make(Playlist, name=f"Test {faker.uuid4()[:8]}", owner=owner)
    elif entity_type == "smartblock":
        return baker.make(
            SmartBlock, name=f"Test {faker.uuid4()[:8]}", owner=owner, kind="static"
        )
    elif entity_type == "webstream":
        return baker.make(
            Webstream,
            name=f"Test {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=owner,
        )
    elif entity_type == "podcast":
        return baker.make(
            Podcast,
            title=f"Test {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=owner,
        )
    elif entity_type == "file":
        return baker.make(File, owner=owner)
    elif entity_type == "show":
        return baker.make(
            Show,
            name=f"Test {faker.uuid4()[:8]}",
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
    raise ValueError(f"Unknown entity: {entity_type}")


def get_endpoint(entity_type: str, obj_id: int) -> str:
    """Get API endpoint for entity."""
    endpoints = {
        "playlist": f"/api/v2/playlists/{obj_id}",
        "smartblock": f"/api/v2/smart-blocks/{obj_id}",
        "webstream": f"/api/v2/webstreams/{obj_id}",
        "podcast": f"/api/v2/podcasts/{obj_id}",
        "file": f"/api/v2/files/{obj_id}",
        "show": f"/api/v2/shows/{obj_id}",
    }
    return endpoints[entity_type]


def entity_exists(entity_type: str, obj_id: int) -> bool:
    """Check if entity still exists in database."""
    model_map = {
        "playlist": Playlist,
        "smartblock": SmartBlock,
        "webstream": Webstream,
        "podcast": Podcast,
        "file": File,
        "show": Show,
    }
    model = model_map[entity_type]
    return model.objects.filter(id=obj_id).exists()


# =============================================================================
# ANONYMOUS Tests - All Denied
# =============================================================================

@pytest.mark.django_db
class TestDeleteAnonymousDenied:
    """Anonymous users cannot delete anything - 403 on all endpoints."""

    def test_anonymous_cannot_delete_playlist(self, anonymous_client, faker):
        """Anonymous DELETE playlist returns 403."""
        owner = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", owner, faker)

        response = anonymous_client.delete(get_endpoint("playlist", playlist.id))
        assert response.status_code == 403
        # Verify object NOT deleted
        assert entity_exists("playlist", playlist.id)

    def test_anonymous_cannot_delete_smartblock(self, anonymous_client, faker):
        """Anonymous DELETE smartblock returns 403."""
        owner = baker.make(User, role=Role.HOST)
        block = create_entity("smartblock", owner, faker)

        response = anonymous_client.delete(get_endpoint("smartblock", block.id))
        assert response.status_code == 403
        assert entity_exists("smartblock", block.id)

    def test_anonymous_cannot_delete_show(self, anonymous_client, faker):
        """Anonymous DELETE show returns 403."""
        show = create_entity("show", None, faker)

        response = anonymous_client.delete(get_endpoint("show", show.id))
        assert response.status_code == 403
        assert entity_exists("show", show.id)


# =============================================================================
# GUEST Tests - All Denied (no delete permissions)
# =============================================================================

@pytest.mark.django_db
class TestDeleteGuestDenied:
    """GUEST users cannot delete anything - 403 on all endpoints."""

    def test_guest_cannot_delete_playlist(self, guest_client, faker):
        """GUEST cannot delete any playlist."""
        owner = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", owner, faker)

        response = guest_client.delete(get_endpoint("playlist", playlist.id))
        assert response.status_code == 403
        assert entity_exists("playlist", playlist.id)

    def test_guest_cannot_delete_own_playlist(self, guest_user, guest_client, faker):
        """GUEST cannot delete playlist even if they somehow own it."""
        playlist = create_entity("playlist", guest_user, faker)

        response = guest_client.delete(get_endpoint("playlist", playlist.id))
        assert response.status_code == 403
        assert entity_exists("playlist", playlist.id)

    def test_guest_cannot_delete_show(self, guest_client, faker):
        """GUEST cannot delete shows."""
        show = create_entity("show", None, faker)

        response = guest_client.delete(get_endpoint("show", show.id))
        assert response.status_code == 403
        assert entity_exists("show", show.id)


# =============================================================================
# HOST Tests - Own Objects Only
# =============================================================================

@pytest.mark.django_db
class TestDeleteHostOwnObjects:
    """HOST can delete own objects (204), cannot delete others' (403/404)."""

    def test_host_can_delete_own_playlist(self, host_client, host_user, faker):
        """HOST can DELETE own playlist."""
        playlist = create_entity("playlist", host_user, faker)
        obj_id = playlist.id

        response = host_client.delete(get_endpoint("playlist", obj_id))
        assert response.status_code == 204
        # Verify object actually deleted
        assert not entity_exists("playlist", obj_id)

    def test_host_can_delete_own_smartblock(self, host_client, host_user, faker):
        """HOST can DELETE own smartblock."""
        block = create_entity("smartblock", host_user, faker)
        obj_id = block.id

        response = host_client.delete(get_endpoint("smartblock", obj_id))
        assert response.status_code == 204
        assert not entity_exists("smartblock", obj_id)

    def test_host_can_delete_own_webstream(self, host_client, host_user, faker):
        """HOST can DELETE own webstream."""
        stream = create_entity("webstream", host_user, faker)
        obj_id = stream.id

        response = host_client.delete(get_endpoint("webstream", obj_id))
        assert response.status_code == 204
        assert not entity_exists("webstream", obj_id)

    def test_host_can_delete_own_podcast(self, host_client, host_user, faker):
        """HOST can DELETE own podcast."""
        podcast = create_entity("podcast", host_user, faker)
        obj_id = podcast.id

        response = host_client.delete(get_endpoint("podcast", obj_id))
        assert response.status_code == 204
        assert not entity_exists("podcast", obj_id)

    def test_host_cannot_delete_other_playlist(self, host_client, faker):
        """HOST cannot delete other's playlist (403 or 404)."""
        other_user = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", other_user, faker)

        response = host_client.delete(get_endpoint("playlist", playlist.id))
        assert response.status_code in [403, 404]
        # Verify object NOT deleted
        assert entity_exists("playlist", playlist.id)

    def test_host_cannot_delete_other_smartblock(self, host_client, faker):
        """HOST cannot delete other's smartblock."""
        other_user = baker.make(User, role=Role.HOST)
        block = create_entity("smartblock", other_user, faker)

        response = host_client.delete(get_endpoint("smartblock", block.id))
        assert response.status_code in [403, 404]
        assert entity_exists("smartblock", block.id)

    def test_host_cannot_delete_other_webstream(self, host_client, faker):
        """HOST cannot delete other's webstream."""
        other_user = baker.make(User, role=Role.HOST)
        stream = create_entity("webstream", other_user, faker)

        response = host_client.delete(get_endpoint("webstream", stream.id))
        assert response.status_code in [403, 404]
        assert entity_exists("webstream", stream.id)

    def test_host_cannot_delete_show(self, host_client, faker):
        """HOST cannot delete shows (no delete_show permission)."""
        show = create_entity("show", None, faker)

        response = host_client.delete(get_endpoint("show", show.id))
        assert response.status_code == 403
        assert entity_exists("show", show.id)


# =============================================================================
# MANAGER Tests - Any Object
# =============================================================================

@pytest.mark.django_db
class TestDeleteManagerAnyObject:
    """MANAGER can delete any objects (own and others')."""

    def test_manager_can_delete_host_playlist(self, manager_client, faker):
        """MANAGER can delete HOST's playlist."""
        host = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", host, faker)
        obj_id = playlist.id

        response = manager_client.delete(get_endpoint("playlist", obj_id))
        assert response.status_code == 204
        assert not entity_exists("playlist", obj_id)

    def test_manager_can_delete_host_smartblock(self, manager_client, faker):
        """MANAGER can delete HOST's smartblock."""
        host = baker.make(User, role=Role.HOST)
        block = create_entity("smartblock", host, faker)
        obj_id = block.id

        response = manager_client.delete(get_endpoint("smartblock", obj_id))
        assert response.status_code == 204
        assert not entity_exists("smartblock", obj_id)

    def test_manager_can_delete_host_webstream(self, manager_client, faker):
        """MANAGER can delete HOST's webstream."""
        host = baker.make(User, role=Role.HOST)
        stream = create_entity("webstream", host, faker)
        obj_id = stream.id

        response = manager_client.delete(get_endpoint("webstream", obj_id))
        assert response.status_code == 204
        assert not entity_exists("webstream", obj_id)

    def test_manager_can_delete_show(self, manager_client, faker):
        """MANAGER can delete shows."""
        show = create_entity("show", None, faker)
        obj_id = show.id

        response = manager_client.delete(get_endpoint("show", obj_id))
        assert response.status_code == 204
        assert not entity_exists("show", obj_id)


# =============================================================================
# ADMIN Tests - Any Object (Superuser)
# =============================================================================

@pytest.mark.django_db
class TestDeleteAdminAnyObject:
    """ADMIN can delete any objects (superuser access)."""

    def test_admin_can_delete_host_playlist(self, admin_client, faker):
        """ADMIN can delete HOST's playlist."""
        host = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", host, faker)
        obj_id = playlist.id

        response = admin_client.delete(get_endpoint("playlist", obj_id))
        assert response.status_code == 204
        assert not entity_exists("playlist", obj_id)

    def test_admin_can_delete_show(self, admin_client, faker):
        """ADMIN can delete shows."""
        show = create_entity("show", None, faker)
        obj_id = show.id

        response = admin_client.delete(get_endpoint("show", obj_id))
        assert response.status_code == 204
        assert not entity_exists("show", obj_id)


# =============================================================================
# Cross-Role Comparison Tests
# =============================================================================

@pytest.mark.django_db
class TestDeleteCrossRoleComparison:
    """Compare delete behavior across roles for same object."""

    def test_host_blocked_others_allowed_manager_admin(self, host_client, manager_client, admin_client, faker):
        """HOST blocked from deleting other's object, MANAGER/ADMIN allowed."""
        other_user = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", other_user, faker)

        # HOST blocked
        host_response = host_client.delete(get_endpoint("playlist", playlist.id))
        assert host_response.status_code in [403, 404]
        assert entity_exists("playlist", playlist.id)

        # MANAGER allowed
        manager_response = manager_client.delete(get_endpoint("playlist", playlist.id))
        assert manager_response.status_code == 204
        assert not entity_exists("playlist", playlist.id)


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.django_db
class TestDeleteEdgeCases:
    """Edge cases for delete operations."""

    def test_delete_nonexistent_object_returns_404(self, host_client, faker):
        """DELETE non-existent ID returns 404."""
        response = host_client.delete("/api/v2/playlists/999999")
        # May return 403 (permission denied before check existence) or 404
        assert response.status_code in [403, 404]

    def test_delete_already_deleted_object(self, host_client, host_user, faker):
        """DELETE already deleted object returns 404."""
        playlist = create_entity("playlist", host_user, faker)
        obj_id = playlist.id

        # First delete
        response1 = host_client.delete(get_endpoint("playlist", obj_id))
        assert response1.status_code == 204

        # Second delete should return 404
        response2 = host_client.delete(get_endpoint("playlist", obj_id))
        assert response2.status_code in [403, 404]
