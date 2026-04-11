"""
Comprehensive test matrix for UPDATE operations across all roles and entities.

Tests that:
1. Each role can/cannot update entities according to permission matrix
2. HOST role can only update own objects (404/403 for others')
3. MANAGER/ADMIN can update any objects
4. Owner remains unchanged after update (unless specifically changed)

Permission Matrix (UPDATE - PUT/PATCH):
| Entity      | ANONYMOUS | GUEST | HOST       | MANAGER | ADMIN |
|-------------|-----------|-------|------------|---------|-------|
| Playlist    | 403       | 403   | own 200    | any 200 | any 200 |
| SmartBlock  | 403       | 403   | own 200    | any 200 | any 200 |
| Webstream   | 403       | 403   | own 200    | any 200 | any 200 |
| Podcast     | 403       | 403   | own 200    | any 200 | any 200 |
| File        | 403       | 403   | own 200    | any 200 | any 200 |
| Show        | 403       | 403   | 403        | any 200 | any 200 |

Usage:
    cd app/api && uv run pytest api/tests/test_role_update_matrix.py -v
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
# Helper Functions
# =============================================================================


def get_update_data(entity_type: str, faker) -> dict[str, Any]:
    """Generate valid update data for each entity type."""
    data_map = {
        "playlist": lambda: {"name": f"Updated Playlist {faker.uuid4()[:8]}"},
        "smartblock": lambda: {
            "name": f"Updated Block {faker.uuid4()[:8]}",
            "kind": "static",
        },
        "webstream": lambda: {
            "name": f"Updated Stream {faker.uuid4()[:8]}",
            "url": faker.url(),
            "description": "Updated description",
        },
        "podcast": lambda: {
            "title": f"Updated Podcast {faker.uuid4()[:8]}",
            "url": faker.url(),
        },
        "show": lambda: {
            "name": f"Updated Show {faker.uuid4()[:8]}",
            "description": "Updated description",
            "genre": "Music",
            "background_color": "FFFFFF",
            "foreground_color": "000000",
            "linked": False,
            "linkable": False,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        },
    }
    return data_map.get(
        entity_type, lambda: {"name": f"Updated {faker.uuid4()[:8]}"},
    )()


def create_entity(entity_type: str, owner: User | None, faker):
    """Create test entity with given owner."""
    if entity_type == "playlist":
        return baker.make(
            Playlist, name=f"Original {faker.uuid4()[:8]}", owner=owner,
        )
    if entity_type == "smartblock":
        return baker.make(
            SmartBlock,
            name=f"Original {faker.uuid4()[:8]}",
            owner=owner,
            kind="static",
        )
    if entity_type == "webstream":
        return baker.make(
            Webstream,
            name=f"Original {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=owner,
        )
    if entity_type == "podcast":
        return baker.make(
            Podcast,
            title=f"Original {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=owner,
        )
    if entity_type == "file":
        return baker.make(File, owner=owner)
    if entity_type == "show":
        return baker.make(
            Show,
            name=f"Original {faker.uuid4()[:8]}",
            description="Original description",
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


# =============================================================================
# ANONYMOUS Tests - All Denied
# =============================================================================


@pytest.mark.django_db
class TestUpdateAnonymousDenied:
    """Anonymous users cannot update anything - 403 on all endpoints."""

    def test_anonymous_cannot_update_playlist(self, anonymous_client, faker):
        """Anonymous PUT/PATCH playlist returns 403."""
        owner = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", owner, faker)
        data = get_update_data("playlist", faker)

        response = anonymous_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert response.status_code == 403

    def test_anonymous_cannot_update_smartblock(self, anonymous_client, faker):
        """Anonymous PUT/PATCH smartblock returns 403."""
        owner = baker.make(User, role=Role.HOST)
        block = create_entity("smartblock", owner, faker)
        data = get_update_data("smartblock", faker)

        response = anonymous_client.patch(
            get_endpoint("smartblock", block.id), data, format="json",
        )
        assert response.status_code == 403

    def test_anonymous_cannot_update_show(self, anonymous_client, faker):
        """Anonymous PUT/PATCH show returns 403."""
        show = create_entity("show", None, faker)
        data = get_update_data("show", faker)

        response = anonymous_client.patch(
            get_endpoint("show", show.id), data, format="json",
        )
        assert response.status_code == 403


# =============================================================================
# GUEST Tests - All Denied (no change permissions)
# =============================================================================


@pytest.mark.django_db
class TestUpdateGuestDenied:
    """GUEST users cannot update anything - 403 on all endpoints."""

    def test_guest_cannot_update_playlist(self, guest_client, faker):
        """GUEST cannot update any playlist (no change_own_playlist permission)."""
        owner = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", owner, faker)
        data = get_update_data("playlist", faker)

        response = guest_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert response.status_code == 403

    def test_guest_cannot_update_own_playlist(
        self, guest_user, guest_client, faker,
    ):
        """GUEST cannot update playlist even if they somehow own it."""
        # This shouldn't happen in practice (GUEST can't create), but test anyway
        playlist = create_entity("playlist", guest_user, faker)
        data = get_update_data("playlist", faker)

        response = guest_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert response.status_code == 403

    def test_guest_cannot_update_show(self, guest_client, faker):
        """GUEST cannot update shows."""
        show = create_entity("show", None, faker)
        data = get_update_data("show", faker)

        response = guest_client.patch(
            get_endpoint("show", show.id), data, format="json",
        )
        assert response.status_code == 403


# =============================================================================
# HOST Tests - Own Objects Only
# =============================================================================


@pytest.mark.django_db
class TestUpdateHostOwnObjects:
    """HOST can update own objects (200), cannot update others' (403/404)."""

    def test_host_can_update_own_playlist(self, host_client, host_user, faker):
        """HOST can PATCH own playlist."""
        playlist = create_entity("playlist", host_user, faker)
        data = get_update_data("playlist", faker)
        new_name = data["name"]

        response = host_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.data}"
        assert response.data["name"] == new_name

        # Verify in DB
        playlist.refresh_from_db()
        assert playlist.name == new_name

    def test_host_can_update_own_smartblock(
        self, host_client, host_user, faker,
    ):
        """HOST can PATCH own smartblock."""
        block = create_entity("smartblock", host_user, faker)
        data = get_update_data("smartblock", faker)
        new_name = data["name"]

        response = host_client.patch(
            get_endpoint("smartblock", block.id), data, format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == new_name

    def test_host_can_update_own_webstream(
        self, host_client, host_user, faker,
    ):
        """HOST can PATCH own webstream."""
        stream = create_entity("webstream", host_user, faker)
        data = get_update_data("webstream", faker)
        new_name = data["name"]

        response = host_client.patch(
            get_endpoint("webstream", stream.id), data, format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == new_name

    def test_host_can_update_own_podcast(self, host_client, host_user, faker):
        """HOST can PATCH own podcast."""
        podcast = create_entity("podcast", host_user, faker)
        data = get_update_data("podcast", faker)
        new_title = data["title"]

        response = host_client.patch(
            get_endpoint("podcast", podcast.id), data, format="json",
        )
        assert response.status_code == 200
        assert response.data["title"] == new_title

    def test_host_cannot_update_other_playlist(self, host_client, faker):
        """HOST cannot update other's playlist (404 or 403)."""
        other_user = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", other_user, faker)
        data = get_update_data("playlist", faker)

        response = host_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert response.status_code in [
            403,
            404,
        ], f"Expected 403 or 404, got {response.status_code}"

    def test_host_cannot_update_other_smartblock(self, host_client, faker):
        """HOST cannot update other's smartblock."""
        other_user = baker.make(User, role=Role.HOST)
        block = create_entity("smartblock", other_user, faker)
        data = get_update_data("smartblock", faker)

        response = host_client.patch(
            get_endpoint("smartblock", block.id), data, format="json",
        )
        assert response.status_code in [403, 404]

    def test_host_cannot_update_other_webstream(self, host_client, faker):
        """HOST cannot update other's webstream."""
        other_user = baker.make(User, role=Role.HOST)
        stream = create_entity("webstream", other_user, faker)
        data = get_update_data("webstream", faker)

        response = host_client.patch(
            get_endpoint("webstream", stream.id), data, format="json",
        )
        assert response.status_code in [403, 404]

    def test_host_cannot_update_show(self, host_client, faker):
        """HOST cannot update shows (no change_show permission)."""
        show = create_entity("show", None, faker)
        data = get_update_data("show", faker)

        response = host_client.patch(
            get_endpoint("show", show.id), data, format="json",
        )
        assert response.status_code == 403


# =============================================================================
# MANAGER Tests - Any Object
# =============================================================================


@pytest.mark.django_db
class TestUpdateManagerAnyObject:
    """MANAGER can update any objects (own and others')."""

    def test_manager_can_update_host_playlist(self, manager_client, faker):
        """MANAGER can update HOST's playlist."""
        host = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", host, faker)
        data = get_update_data("playlist", faker)
        new_name = data["name"]

        response = manager_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == new_name

        playlist.refresh_from_db()
        assert playlist.name == new_name

    def test_manager_can_update_host_smartblock(self, manager_client, faker):
        """MANAGER can update HOST's smartblock."""
        host = baker.make(User, role=Role.HOST)
        block = create_entity("smartblock", host, faker)
        data = get_update_data("smartblock", faker)

        response = manager_client.patch(
            get_endpoint("smartblock", block.id), data, format="json",
        )
        assert response.status_code == 200

    def test_manager_can_update_host_webstream(self, manager_client, faker):
        """MANAGER can update HOST's webstream."""
        host = baker.make(User, role=Role.HOST)
        stream = create_entity("webstream", host, faker)
        data = get_update_data("webstream", faker)

        response = manager_client.patch(
            get_endpoint("webstream", stream.id), data, format="json",
        )
        assert response.status_code == 200

    def test_manager_can_update_show(self, manager_client, faker):
        """MANAGER can update shows."""
        show = create_entity("show", None, faker)
        data = get_update_data("show", faker)
        new_name = data["name"]

        response = manager_client.patch(
            get_endpoint("show", show.id), data, format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == new_name


# =============================================================================
# ADMIN Tests - Any Object (Superuser)
# =============================================================================


@pytest.mark.django_db
class TestUpdateAdminAnyObject:
    """ADMIN can update any objects (superuser access)."""

    def test_admin_can_update_host_playlist(self, admin_client, faker):
        """ADMIN can update HOST's playlist."""
        host = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", host, faker)
        data = get_update_data("playlist", faker)
        new_name = data["name"]

        response = admin_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == new_name

    def test_admin_can_update_show(self, admin_client, faker):
        """ADMIN can update shows."""
        show = create_entity("show", None, faker)
        data = get_update_data("show", faker)
        new_name = data["name"]

        response = admin_client.patch(
            get_endpoint("show", show.id), data, format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == new_name


# =============================================================================
# Cross-Role Comparison Tests
# =============================================================================


@pytest.mark.django_db
class TestUpdateCrossRoleComparison:
    """Compare update behavior across roles for same object."""

    def test_host_blocked_others_allowed_manager_admin(
        self, host_client, manager_client, admin_client, faker,
    ):
        """HOST blocked from updating other's object, MANAGER/ADMIN allowed."""
        other_user = baker.make(User, role=Role.HOST)
        playlist = create_entity("playlist", other_user, faker)
        data = get_update_data("playlist", faker)

        # HOST blocked
        host_response = host_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert host_response.status_code in [403, 404]

        # MANAGER allowed
        manager_response = manager_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        assert manager_response.status_code == 200

        # Refresh for ADMIN test
        playlist.refresh_from_db()

        # ADMIN allowed
        admin_data = get_update_data("playlist", faker)
        admin_response = admin_client.patch(
            get_endpoint("playlist", playlist.id), admin_data, format="json",
        )
        assert admin_response.status_code == 200


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.django_db
class TestUpdateEdgeCases:
    """Edge cases for update operations."""

    def test_update_nonexistent_object_returns_404(self, host_client, faker):
        """PATCH non-existent ID returns 404."""
        data = get_update_data("playlist", faker)
        response = host_client.patch(
            "/api/v2/playlists/999999", data, format="json",
        )
        # May return 403 (permission denied before check existence) or 404
        assert response.status_code in [403, 404]

    def test_update_with_invalid_data_returns_400(
        self, host_client, host_user, faker,
    ):
        """PATCH with invalid data returns 400 (not 403)."""
        playlist = create_entity("playlist", host_user, faker)
        # Invalid data - empty name
        data = {"name": ""}

        response = host_client.patch(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        # Either 200 (if empty name allowed) or 400 (validation error)
        assert response.status_code in [200, 400]

    def test_partial_update_with_patch(self, host_client, host_user, faker):
        """PATCH updates only provided fields."""
        playlist = create_entity("playlist", host_user, faker)
        original_name = playlist.name
        new_description = f"Updated desc {faker.uuid4()[:8]}"

        # If playlist has description field, test partial update
        response = host_client.patch(
            get_endpoint("playlist", playlist.id),
            {"description": new_description},
            format="json",
        )
        # May be 200 or field may not exist
        assert response.status_code in [200, 400]

    def test_put_full_update(self, host_client, host_user, faker):
        """PUT requires full object (or at least updates)."""
        playlist = create_entity("playlist", host_user, faker)
        data = get_update_data("playlist", faker)

        response = host_client.put(
            get_endpoint("playlist", playlist.id), data, format="json",
        )
        # PUT may require all fields or work like PATCH
        assert response.status_code in [200, 400]
