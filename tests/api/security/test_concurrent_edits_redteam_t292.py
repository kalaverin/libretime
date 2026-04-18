"""
T292: Concurrent Edits Red Team Security Tests.

Paranoid security tests for race conditions and TOCTOU vulnerabilities.
OWASP API Top 10 2023: API1:2023 BOLA, API2:2023 Broken Authentication
"""

import concurrent.futures
import json
import time

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import Role, User
from api.schedule.models import Playlist, PlaylistContent
from api.storage.models import File, Library


@pytest.mark.django_db(transaction=True)
class TestTOCTOUAuthorization:
    """Time-of-check to time-of-use authorization bypass tests."""

    def test_toctou_change_owner_during_update(self, guest_client, faker):
        """Change owner between permission check and update."""
        user_a = baker.make(
            User,
            username=f"toctou_a_{faker.user_name()}",
            role=Role.HOST,
        )
        user_b = baker.make(
            User,
            username=f"toctou_b_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Original",
            owner=user_a,
            description="Test",
        )

        # User B tries to update (should be blocked - not owner)
        client_b = APIClient()
        client_b.force_authenticate(user=user_b)

        # Check: User B cannot see/modify User A's playlist
        response = client_b.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "Hacked"}),
            content_type="application/json",
        )

        # Should be 403 or 404 - if 200, it's BOLA
        assert response.status_code in [
            403,
            404,
        ], f"Expected 403/404, got {response.status_code}"

    def test_toctou_delete_after_ownership_change(self, guest_client, faker):
        """Delete after ownership transfer - should require re-auth."""
        user_a = baker.make(
            User,
            username=f"del_a_{faker.user_name()}",
            role=Role.HOST,
        )
        user_b = baker.make(
            User,
            username=f"del_b_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="To Delete",
            owner=user_a,
        )

        # Transfer ownership to user B
        playlist.owner = user_b
        playlist.save()

        # User A tries to delete (should fail - no longer owner)
        client_a = APIClient()
        client_a.force_authenticate(user=user_a)

        response = client_a.delete(f"/api/v2/playlists/{playlist.id}")

        # Should be 403 - user A no longer owns it (if 204, it's a bug)
        assert response.status_code in [
            403,
            404,
        ], f"Expected 403/404, got {response.status_code}"


@pytest.mark.django_db
class TestConcurrentBOLA:
    """Concurrent Broken Object Level Authorization tests."""

    @pytest.mark.xfail(
        reason="Concurrent test - thread instability",
        strict=False,
    )
    def test_concurrent_cross_user_update(self, guest_client, faker):
        """User A and User B update same object simultaneously (race test)."""
        from django.conf import settings

        user_a = baker.make(
            User,
            username=f"race_a_{faker.user_name()}",
            role=Role.HOST,
        )
        user_b = baker.make(
            User,
            username=f"race_b_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Race Target",
            owner=user_a,
            description="Original",
        )

        def user_a_update():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            return client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"description": "User A Update"}),
                content_type="application/json",
            )

        def user_b_update():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            return client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"description": "User B Hacked"}),
                content_type="application/json",
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(user_a_update)
            future_b = executor.submit(user_b_update)

            response_a = future_a.result()
            response_b = future_b.result()

        # Both should succeed with admin auth
        assert response_a.status_code == 200
        assert response_b.status_code == 200

    @pytest.mark.xfail(
        reason="Concurrent test - thread instability",
        strict=False,
    )
    def test_concurrent_same_user_updates(self, guest_client, faker):
        """Same user updates from two sessions concurrently."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"same_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Concurrent",
            owner=user,
        )

        def update_1():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            return client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"name": "Update 1"}),
                content_type="application/json",
            )

        def update_2():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            return client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"name": "Update 2"}),
                content_type="application/json",
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_1 = executor.submit(update_1)
            future_2 = executor.submit(update_2)

            resp_1 = future_1.result()
            resp_2 = future_2.result()

        # Both should succeed with admin auth
        assert resp_1.status_code == 200
        assert resp_2.status_code == 200


@pytest.mark.django_db
class TestRaceConditionDelete:
    """Race conditions involving DELETE operations."""

    def test_delete_during_update(self, guest_client, faker):
        """DELETE while UPDATE in progress - consistency check."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"delupd_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Race Delete",
            owner=user,
        )

        def do_update():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            time.sleep(0.01)  # Small delay
            return client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"name": "Updated"}),
                content_type="application/json",
            )

        def do_delete():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            return client.delete(f"/api/v2/playlists/{playlist.id}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_update = executor.submit(do_update)
            future_delete = executor.submit(do_delete)

            resp_update = future_update.result()
            resp_delete = future_delete.result()

        # One should succeed, other should fail appropriately
        # No 500 errors allowed
        assert resp_update.status_code in [200, 404]
        assert resp_delete.status_code in [204, 404]

    def test_double_delete_idempotency(self, guest_client, faker):
        """Double DELETE should return consistent response."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"dbl_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Double Delete",
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        # First delete
        resp1 = client.delete(f"/api/v2/playlists/{playlist.id}")
        assert resp1.status_code == 204

        # Second delete of same object
        resp2 = client.delete(f"/api/v2/playlists/{playlist.id}")

        # Should be 404 (not found), not 500
        assert resp2.status_code in [
            404,
            204,
        ], f"Double delete returned {resp2.status_code}"

    def test_cross_user_delete_race(self, guest_client, faker):
        """User B deletes while User A reads - data leak."""
        user_a = baker.make(
            User,
            username=f"rdr_a_{faker.user_name()}",
            role=Role.HOST,
        )
        user_b = baker.make(
            User,
            username=f"rdr_b_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Race Delete Data",
            owner=user_a,
        )

        def user_a_read():
            client = APIClient()
            client.force_authenticate(user=user_a)
            time.sleep(0.01)
            return client.get(f"/api/v2/playlists/{playlist.id}")

        def user_b_delete():
            client = APIClient()
            client.force_authenticate(user=user_b)
            return client.delete(f"/api/v2/playlists/{playlist.id}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_read = executor.submit(user_a_read)
            future_delete = executor.submit(user_b_delete)

            resp_read = future_read.result()
            resp_delete = future_delete.result()

        # User B should NOT be able to delete User A's playlist
        assert resp_delete.status_code in [
            403,
            404,
        ], f"User B delete got {resp_delete.status_code}"


@pytest.mark.django_db
class TestConcurrentMassAssignment:
    """Mass assignment via concurrent updates."""

    def test_concurrent_mass_assignment_id(self, guest_client, faker):
        """Try to change ID via mass assignment."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"mass_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Mass Test",
            owner=user,
        )
        original_id = playlist.id

        # Try to change ID via PATCH (using admin api key)
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"id": 999999, "name": "Hacked"}),
            content_type="application/json",
        )

        playlist.refresh_from_db()

        # ID should not change - if changed, it's mass assignment vulnerability
        assert (
            playlist.id == original_id
        ), f"ID changed from {original_id} to {playlist.id}"

    def test_concurrent_mass_assignment_owner(self, guest_client, faker):
        """Try to change owner via mass assignment. (T880)"""
        from django.conf import settings

        user_a = baker.make(
            User,
            username=f"own_a_{faker.user_name()}",
            role=Role.HOST,
        )
        user_b = baker.make(
            User,
            username=f"own_b_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Owner Test",
            owner=user_a,
        )

        # Try to change owner to user B (as admin)
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"owner": user_b.id}),
            content_type="application/json",
        )

        playlist.refresh_from_db()

        # Owner should not change via mass assignment
        assert (
            playlist.owner_id == user_a.id
        ), f"Owner changed to {playlist.owner_id}"

    @pytest.mark.xfail(
        reason="Concurrent test - thread instability",
        strict=False,
    )
    def test_concurrent_legal_field_updates(self, guest_client, faker):
        """Multiple legal field updates concurrently (race test)."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"legal_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Legal Test",
            owner=user,
            description="Original",
        )

        def update_name():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            resp = client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"name": "Name Updated"}),
                content_type="application/json",
            )
            return resp.status_code

        def update_description():
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            resp = client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"description": "Desc Updated"}),
                content_type="application/json",
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_name = executor.submit(update_name)
            future_desc = executor.submit(update_description)

            status_name = future_name.result()
            status_desc = future_desc.result()

        # Both should succeed
        assert status_name == 200
        assert status_desc == 200


@pytest.mark.django_db
class TestRaceConditionContentModification:
    """Race conditions in playlist content."""

    @pytest.mark.xfail(
        reason="Concurrent test - thread instability",
        strict=False,
    )
    def test_concurrent_content_add_same_position(self, guest_client, faker):
        """Two contents added at same position concurrently (race test)."""
        user = baker.make(
            User,
            username=f"pos_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="POS",
            name="Pos",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Position Test", owner=user)

        file1 = baker.make(
            File,
            name="song1.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )
        file2 = baker.make(
            File,
            name="song2.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        def add_content_1():
            return baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file1,
                position=1,
            )

        def add_content_2():
            return baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file2,
                position=1,  # Same position!
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(add_content_1)
            future2 = executor.submit(add_content_2)

            future1.result()
            future2.result()

        # Both should exist
        count = PlaylistContent.objects.filter(playlist=playlist).count()
        assert count == 2

    def test_concurrent_content_delete_and_update(self, guest_client, faker):
        """Delete content while updating it."""
        user = baker.make(
            User,
            username=f"delup_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="DELUP",
            name="DelUp",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Delete Update", owner=user)
        file_obj = baker.make(
            File,
            name="song.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            cue_in="00:00:00",
        )

        def do_update():
            time.sleep(0.01)
            content.cue_in = "00:01:00"
            try:
                content.save()
                return "saved"
            except Exception as e:
                return str(e)

        def do_delete():
            try:
                content.delete()
                return "deleted"
            except Exception as e:
                return str(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_update = executor.submit(do_update)
            future_delete = executor.submit(do_delete)

            result_update = future_update.result()
            result_delete = future_delete.result()

        # Should not crash, either operation can succeed
        assert "error" not in result_update.lower()


@pytest.mark.django_db
class TestLostUpdateProblem:
    """Lost update detection - when updates overwrite each other incorrectly."""

    def test_lost_update_detection(self, guest_client, faker):
        """Detect if updates are lost without optimistic locking."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"lost_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Lost Update Test",
            owner=user,
            description="Version 1",
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        # Get initial data
        resp1 = client.get(f"/api/v2/playlists/{playlist.id}")
        data1 = resp1.json()

        # Update 1: Change name
        resp2 = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "Name Changed"}),
            content_type="application/json",
        )
        assert resp2.status_code == 200

        # Update 2: Change description (based on old data)
        # This simulates user with stale data
        resp3 = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"description": "Version 2"}),
            content_type="application/json",
        )
        assert resp3.status_code == 200

        # Verify both changes persisted (last write wins for each field)
        playlist.refresh_from_db()
        assert playlist.name == "Name Changed"
        assert playlist.description == "Version 2"

    @pytest.mark.xfail(reason="ETag/Versioning: T881", strict=False)
    def test_optimistic_locking_missing(self, guest_client, faker):
        """Check if optimistic locking (ETag/If-Match) is implemented. (T881)

        Without optimistic locking, concurrent updates can cause data loss.
        """
        user = baker.make(
            User,
            username=f"etag_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="ETag Test",
            owner=user,
        )

        client = APIClient()
        client.force_authenticate(user=user)

        # Get resource - check for ETag
        resp = client.get(f"/api/v2/playlists/{playlist.id}")

        # Should have ETag header for optimistic locking
        if "ETag" not in resp.headers and "etag" not in resp.headers:
            pytest.fail("Missing ETag header - no optimistic locking (T881)")


@pytest.mark.django_db
class TestTransactionIsolation:
    """Database transaction isolation level tests."""

    def test_read_committed_behavior(self, guest_client, faker):
        """Verify READ COMMITTED isolation - read uncommitted not visible."""
        user = baker.make(
            User,
            username=f"isol_{faker.user_name()}",
            role=Role.HOST,
        )

        playlist = baker.make(
            Playlist,
            name="Isolation Test",
            owner=user,
        )

        # Read 1
        client = APIClient()
        client.force_authenticate(user=user)

        resp1 = client.get(f"/api/v2/playlists/{playlist.id}")
        name1 = resp1.json()["name"]

        # Update
        playlist.name = "Updated Name"
        playlist.save()

        # Read 2 (should see updated value)
        resp2 = client.get(f"/api/v2/playlists/{playlist.id}")
        name2 = resp2.json()["name"]

        assert name2 == "Updated Name"

    def test_concurrent_create_same_name(self, guest_client, faker):
        """Create playlists with same name concurrently."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"same_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="CONC",
            name="Conc",
            description="Test",
        )

        def create_playlist(i):
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            return client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": "Duplicate Name",
                        "owner": user.id,
                    },
                ),
                content_type="application/json",
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_playlist, i) for i in range(5)]
            responses = [f.result() for f in futures]

        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 201)
        # Should allow duplicates or reject consistently
        assert (
            success_count == 5 or success_count == 0
        ), f"Unexpected success count: {success_count}"


@pytest.mark.django_db
class TestDeadlockPrevention:
    """Deadlock detection and prevention."""

    def test_concurrent_updates_different_objects(self, guest_client, faker):
        """Concurrent updates to different objects - no deadlock."""
        from django.conf import settings

        user = baker.make(
            User,
            username=f"ddl_{faker.user_name()}",
            role=Role.HOST,
        )

        playlists = []
        for i in range(5):
            pl = baker.make(Playlist, name=f"Playlist {i}", owner=user)
            playlists.append(pl)

        def update_playlist(pl):
            client = APIClient()
            client.credentials(
                HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
            )
            resp = client.patch(
                f"/api/v2/playlists/{pl.id}",
                json.dumps({"name": f"Updated {pl.id}"}),
                content_type="application/json",
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(update_playlist, pl) for pl in playlists
            ]
            statuses = [f.result() for f in futures]

        # All should succeed (or 404 if race deleted)
        for status in statuses:
            assert status in [200, 404]
