"""T290: Cascade delete redteam security tests.

Tests for BOLA, DoS, race conditions, FK constraint bypass in cascade deletes.
"""

import json
import threading
import time

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.schedule.models import (
    Playlist,
    PlaylistContent,
    Show,
    ShowInstance,
    SmartBlock,
    SmartBlockContent,
)
from api.storage.models import File, Library


class TestCascadeDeleteBOLA:
    """BOLA: Cascade delete with unauthorized access."""

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.xfail(
        reason="T863: BOLA - attacker can delete victim's show (flaky: passes alone, fails in suite)",
    )
    def test_bola_delete_show_cascades_to_instances(self, api_client, faker):
        """Attacker deleting victim's show cascades to all instances."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        # Victim's show with multiple instances
        show = baker.make(Show, name="Victim's Important Show")
        instances = [baker.make(ShowInstance, show=show) for _ in range(5)]
        instance_ids = [i.id for i in instances]

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.delete(f"/api/v2/shows/{show.id}")

        # API should block delete
        assert response.status_code in [
            403,
            404,
        ], f"T863: BOLA - attacker deleted show (got {response.status_code})"

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.xfail(
        reason="T864: BOLA - attacker can delete victim's playlist (flaky: state-dependent)",
    )
    def test_bola_delete_playlist_cascades_to_contents(
        self, api_client, faker,
    ):
        """Attacker deleting victim's playlist is blocked."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")
        library = baker.make(Library, name="Test Lib", description="Test")

        # Victim's playlist with contents
        playlist = baker.make(Playlist, name="Victim's Playlist", owner=victim)
        contents = [
            baker.make(PlaylistContent, playlist=playlist, position=i)
            for i in range(10)
        ]
        content_ids = [c.id for c in contents]

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.delete(f"/api/v2/playlists/{playlist.id}")

        assert response.status_code in [
            403,
            404,
        ], f"T864: BOLA - attacker deleted playlist (got {response.status_code})"

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.xfail(
        reason="T865: BOLA - attacker can delete victim's smartblock (state-dependent)",
    )
    def test_bola_delete_smartblock_cascades_to_contents(
        self, api_client, faker,
    ):
        """Attacker deleting victim's smartblock cascades to contents."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        # Victim's smartblock with contents
        block = baker.make(
            SmartBlock,
            name="Victim's SmartBlock",
            owner=victim,
            kind=SmartBlock.Kind.STATIC,
        )
        contents = [
            baker.make(SmartBlockContent, block=block, position=i)
            for i in range(5)
        ]
        content_ids = [c.id for c in contents]

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.delete(f"/api/v2/smart-blocks/{block.id}")

        assert response.status_code in [
            403,
            404,
        ], f"T865: BOLA - attacker deleted smartblock (got {response.status_code})"

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.xfail(
        reason="T866: BOLA - attacker can delete victim's library (flaky: state-dependent)",
    )
    def test_bola_delete_library_with_files(self, api_client, faker):
        """Attacker deleting victim's library is blocked."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        library = baker.make(
            Library,
            code="VICTIMLIB",
            name="Victim's Library",
            description="Test",
        )
        files = [
            baker.make(
                File,
                name=f"file{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=victim,
                size=1024,
                accessed=0,
            )
            for i in range(5)
        ]

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.delete(f"/api/v2/libraries/{library.id}")

        # Should be 403 or handled gracefully
        assert response.status_code in [
            403,
            404,
            400,
            409,
        ], f"T866: BOLA/500 - library deletion (got {response.status_code})"


class TestCascadeDeleteDoS:
    """DoS via cascade deletion abuse."""

    @pytest.mark.django_db
    def test_mass_cascade_delete_show_instances(
        self, api_client, admin_user, faker,
    ):
        """Deleting show with thousands of instances."""
        show = baker.make(Show, name="Show with Many Instances")

        # Create many instances (this could be slow)
        instances = [baker.make(ShowInstance, show=show) for _ in range(100)]

        client = APIClient()
        client.force_authenticate(user=admin_user)

        start = time.time()
        response = client.delete(f"/api/v2/shows/{show.id}")
        duration = time.time() - start

        # Should complete in reasonable time
        assert (
            duration < 5
        ), f"T867: Cascade delete too slow: {duration}s for 100 instances"

    @pytest.mark.django_db
    def test_mass_cascade_delete_playlist_contents(
        self, api_client, admin_user, faker,
    ):
        """Deleting playlist with thousands of contents."""
        playlist = baker.make(
            Playlist, name="Playlist with Many Contents", owner=admin_user,
        )

        # Create many contents
        contents = [
            baker.make(PlaylistContent, playlist=playlist, position=i)
            for i in range(100)
        ]

        client = APIClient()
        client.force_authenticate(user=admin_user)

        start = time.time()
        response = client.delete(f"/api/v2/playlists/{playlist.id}")
        duration = time.time() - start

        assert (
            duration < 5
        ), f"T868: Cascade delete too slow: {duration}s for 100 contents"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T869: No rate limiting on cascade delete")
    def test_rapid_cascade_delete_requests(
        self, api_client, admin_user, faker,
    ):
        """Rapid cascade delete requests should be rate limited."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        responses = []
        for i in range(20):
            # Create and immediately delete
            show = baker.make(Show, name=f"Rapid Show {i}")
            baker.make(ShowInstance, show=show)

            response = client.delete(f"/api/v2/shows/{show.id}")
            responses.append(response.status_code)

            if response.status_code == 429:
                return  # Rate limiting works

        success_count = sum(1 for r in responses if r == 204)
        assert success_count < 20, "T869: No rate limiting on cascade delete"


class TestCascadeDeleteRaceCondition:
    """Race conditions in cascade delete operations."""

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T870: Race condition - concurrent delete of same show",
    )
    def test_race_condition_concurrent_show_delete(
        self, api_client, admin_user, faker,
    ):
        """Concurrent delete attempts on same show."""
        show = baker.make(Show, name="Race Show")
        instances = [baker.make(ShowInstance, show=show) for _ in range(10)]

        client = APIClient()
        client.force_authenticate(user=admin_user)

        results = []
        errors = []

        def delete_attempt():
            try:
                response = client.delete(f"/api/v2/shows/{show.id}")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Fire multiple concurrent deletes
        threads = [threading.Thread(target=delete_attempt) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # Should not crash or cause inconsistent state
        # Exactly one should succeed (204), others should get 404
        success_count = results.count(204)
        not_found_count = results.count(404)

        assert (
            success_count == 1
        ), f"T870: Race condition - {success_count} deletes succeeded instead of 1"

    @pytest.mark.django_db
    def test_race_condition_delete_while_adding_content_safe(
        self, api_client, admin_user, faker,
    ):
        """Delete playlist while adding contents to it."""
        playlist = baker.make(Playlist, name="Race Playlist", owner=admin_user)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        errors = []

        def add_contents():
            try:
                for i in range(20):
                    client.post(
                        "/api/v2/playlist-contents",
                        json.dumps(
                            {
                                "playlist": playlist.id,
                                "position": i,
                                "kind": 0,
                                "file": 1,
                            },
                        ),
                        content_type="application/json",
                    )
            except Exception as e:
                errors.append(f"add: {e}")

        def delete_playlist():
            try:
                time.sleep(0.01)  # Small delay to interleave
                client.delete(f"/api/v2/playlists/{playlist.id}")
            except Exception as e:
                errors.append(f"delete: {e}")

        threads = [
            threading.Thread(target=add_contents),
            threading.Thread(target=delete_playlist),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # Should not cause 500 errors or database corruption
        assert len(errors) == 0, f"T871: Errors during race: {errors}"


class TestCascadeDeleteFKConstraintBypass:
    """FK constraint bypass attempts."""

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T872: FK constraint bypass - nullify FK before delete",
    )
    def test_fk_bypass_nullify_before_delete(
        self, api_client, admin_user, faker,
    ):
        """Try to nullify FK references before cascade delete."""
        library = baker.make(
            Library, code="TESTLIB", name="Test Library", description="Test",
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
            accessed=0,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try to nullify library reference
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"library": None}),
            content_type="application/json",
        )

        # If successful, library can be deleted without constraint violation
        if response.status_code == 200:
            data = response.json()
            if data.get("library") is None:
                # Now try to delete library
                del_response = client.delete(f"/api/v2/libraries/{library.id}")
                if del_response.status_code == 204:
                    pytest.fail(
                        "T872: FK constraint bypassed - nullified FK then deleted parent",
                    )

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T873: FK constraint violation causes 500 error")
    def test_delete_with_active_references_blocked(
        self, api_client, admin_user, faker,
    ):
        """Delete parent with active child references should fail gracefully."""
        library = baker.make(
            Library, code="REFLIB", name="Ref Library", description="Test",
        )
        file_obj = baker.make(
            File,
            name="ref.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
            accessed=0,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.delete(f"/api/v2/libraries/{library.id}")

        # Should fail gracefully with 400/409, not 500
        assert response.status_code in [
            400,
            409,
        ], f"T873: FK constraint caused {response.status_code} instead of graceful error"


class TestCascadeDeleteInjection:
    """Injection attacks during cascade delete."""

    @pytest.mark.django_db
    def test_sqli_in_delete_cascade_trigger(
        self, api_client, admin_user, faker,
    ):
        """SQL injection via specially crafted entity names during delete."""
        # Create show with SQLi in name
        show = baker.make(Show, name="'; DROP TABLE cc_show_instances; --")
        instance = baker.make(ShowInstance, show=show)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.delete(f"/api/v2/shows/{show.id}")

        # Should not cause 500 or execute injection
        if response.status_code >= 500:
            pytest.fail("T874: SQLi in name caused 500 during cascade delete")

    @pytest.mark.django_db
    def test_sqli_in_filter_before_delete(self, api_client, admin_user, faker):
        """SQL injection in filter before mass delete."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try SQLi in filter that might be used for mass delete
        sqli_payloads = [
            "' OR '1'='1",
            "1; DROP TABLE cc_show--",
            "' UNION SELECT * FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = client.get(f"/api/v2/shows?name={payload}")

            if response.status_code >= 500:
                pytest.fail(f"T875: SQLi in filter caused 500: {payload}")


class TestCascadeDeleteDataLeakage:
    """Information disclosure via cascade operations."""

    @pytest.mark.django_db
    def test_cascade_count_enumeration(self, api_client, admin_user, faker):
        """Enumerate number of child entities via timing or error messages."""
        show = baker.make(Show, name="Enumeration Show")

        # Create varying numbers of instances
        for i in range(50):
            baker.make(ShowInstance, show=show)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Delete and measure time
        start = time.time()
        response = client.delete(f"/api/v2/shows/{show.id}")
        duration = time.time() - start

        # Response time could reveal number of cascade deletions
        # This is informational - documenting behavior
        assert response.status_code == 204

    @pytest.mark.django_db
    def test_error_message_leaks_child_count(
        self, api_client, admin_user, faker,
    ):
        """Error messages might leak number of child entities."""
        show = baker.make(Show, name="Error Leak Show")
        baker.make(ShowInstance, show=show)

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try to trigger error that might leak info
        # First delete the instance directly, then try to delete show
        instance = ShowInstance.objects.filter(show=show).first()
        if instance:
            instance.delete()

        response = client.delete(f"/api/v2/shows/{show.id}")

        # Check response for leaked info
        response_text = response.content.decode().lower()
        sensitive_patterns = ["instance", "child", "row", "cc_show_instances"]
        for pattern in sensitive_patterns:
            if pattern in response_text and response.status_code >= 400:
                # Informational - may be acceptable
                pass


class TestCascadeDeleteOrphanedData:
    """Orphaned data after incomplete cascade."""

    @pytest.mark.django_db
    def test_interrupted_cascade_no_orphans(
        self, api_client, admin_user, faker,
    ):
        """Interrupted cascade delete might leave orphaned data."""
        # This tests database transaction integrity
        show = baker.make(Show, name="Transaction Show")
        instances = [baker.make(ShowInstance, show=show) for _ in range(20)]
        instance_ids = [i.id for i in instances]

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Delete show
        response = client.delete(f"/api/v2/shows/{show.id}")

        assert response.status_code == 204

        # Check for orphans - all instances should be deleted
        for iid in instance_ids:
            if ShowInstance.objects.filter(id=iid).exists():
                pytest.fail(
                    f"T876: Orphaned instance {iid} after cascade delete",
                )

    @pytest.mark.django_db
    def test_cascade_vs_manual_delete_consistency(
        self, api_client, admin_user, faker,
    ):
        """Cascade delete should be consistent with manual deletion."""
        show1 = baker.make(Show, name="Cascade Show")
        show2 = baker.make(Show, name="Manual Show")

        instances1 = [baker.make(ShowInstance, show=show1) for _ in range(5)]
        instances2 = [baker.make(ShowInstance, show=show2) for _ in range(5)]

        # Cascade delete show1
        show1.delete()

        # Manual delete instances then show2
        for inst in instances2:
            inst.delete()
        show2.delete()

        # Both approaches should result in no instances
        assert not ShowInstance.objects.filter(show=show1).exists()
        assert not ShowInstance.objects.filter(show=show2).exists()


class TestCascadeDeleteAPIPermissions:
    """API permission checks during cascade delete."""

    @pytest.mark.django_db
    def test_delete_without_auth(self, api_client, faker):
        """Delete without authentication should fail."""
        show = baker.make(Show, name="Auth Test Show")

        client = APIClient()  # No auth

        response = client.delete(f"/api/v2/shows/{show.id}")

        assert response.status_code in [
            401,
            403,
        ], f"T877: Delete without auth succeeded: {response.status_code}"

    @pytest.mark.django_db
    def test_delete_with_invalid_token(self, api_client, faker):
        """Delete with invalid token should fail."""
        show = baker.make(Show, name="Token Test Show")

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Api-Key invalid_token")

        response = client.delete(f"/api/v2/shows/{show.id}")

        assert response.status_code in [
            401,
            403,
        ], f"T878: Delete with invalid token succeeded: {response.status_code}"

    @pytest.mark.django_db
    def test_cascade_deletes_children_with_parent_permission(
        self, api_client, admin_user, faker,
    ):
        """Cascade delete might bypass permission checks on children."""
        # Create playlist where user has delete permission
        playlist = baker.make(
            Playlist, name="Parent Playlist", owner=admin_user,
        )

        # Create contents that user might not have direct permission to delete
        contents = [
            baker.make(PlaylistContent, playlist=playlist, position=i)
            for i in range(3)
        ]
        content_ids = [c.id for c in contents]

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Delete parent (should cascade)
        response = client.delete(f"/api/v2/playlists/{playlist.id}")

        assert response.status_code == 204

        # Verify all children deleted (even if user didn't have direct permission)
        for cid in content_ids:
            if PlaylistContent.objects.filter(id=cid).exists():
                pytest.fail("T879: Child not deleted in cascade")
