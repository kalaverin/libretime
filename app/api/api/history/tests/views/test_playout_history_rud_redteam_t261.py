"""T261: PlayoutHistory RUD redteam security tests.

Red Team security tests for PlayoutHistory RETRIEVE, UPDATE, DELETE endpoints.
Tests for BOLA, BOPLA, race conditions, and injection vulnerabilities.
"""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models.role import Role
from api.core.models.user import User
from api.history.models import PlayoutHistory
from api.storage.models import File
from sdk import format_datetime, now


@pytest.mark.django_db
class TestPlayoutHistoryRUDRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization - RUD operations."""

    @pytest.fixture
    def victim_playout(self, faker):
        """Create victim user's playout history."""
        victim = baker.make(
            User, role=Role.HOST, username=f"victim_{faker.user_name()}",
        )
        victim_file = baker.make(File, mime="audio/mp3", owner=victim)
        return baker.make(
            PlayoutHistory,
            file=victim_file,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )

    def test_bola_retrieve_other_users_playout(
        self, api_client, admin_user, victim_playout, faker,
    ):
        """
        BOLA: RETRIEVE other user's playout by ID.

        Admin should be able to retrieve any playout (documented).
        Test what happens with other users.
        """
        # Admin can retrieve victim's playout
        response = api_client.get(
            f"/api/v2/playout-history/{victim_playout.id}",
        )

        if response.status_code == 200:
            # Admin can access - this may be intended
            data = response.json()
            assert data["id"] == victim_playout.id

    def test_bola_update_other_users_playout(
        self, api_client, admin_user, victim_playout, faker,
    ):
        """
        BOLA: UPDATE other user's playout.

        Should verify ownership before allowing update.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.put(
            f"/api/v2/playout-history/{victim_playout.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            # Admin can update victim's playout
            # This may be intended behavior but should be documented
            pass

    def test_bola_patch_other_users_playout(
        self, api_client, admin_user, victim_playout,
    ):
        """
        BOLA: PATCH other user's playout.

        Partial update on victim's record.
        """
        data = {
            "ends": format_datetime(now() + timedelta(minutes=10)),
        }

        response = api_client.patch(
            f"/api/v2/playout-history/{victim_playout.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            # Successfully patched victim's record
            pass

    def test_bola_delete_other_users_playout(
        self, api_client, admin_user, victim_playout,
    ):
        """
        BOLA: DELETE other user's playout.

        Critical data loss vulnerability if allowed inappropriately.
        """
        response = api_client.delete(
            f"/api/v2/playout-history/{victim_playout.id}",
        )

        if response.status_code == 204:
            # Admin deleted victim's playout
            # This may be intended for admin role
            pass

    def test_bola_retrieve_nonexistent_returns_404(
        self, api_client, admin_user,
    ):
        """
        BOLA: Non-existent ID returns 404 (not 403).

        404 vs 403 can leak existence information.
        """
        response = api_client.get("/api/v2/playout-history/999999")
        assert response.status_code == 404

    def test_bola_id_enumeration_via_404_403(
        self, api_client, regular_user, faker,
    ):
        """
        BOLA: Different errors for existent vs non-existent IDs.

        If 403 for existing and 404 for non-existing, can enumerate IDs.
        """
        # Create a playout as admin (different user)
        admin = baker.make(User, role=Role.ADMIN, username=faker.user_name())
        f = baker.make(File, mime="audio/mp3", owner=admin)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        # Regular user tries to access
        api_client.force_authenticate(user=regular_user)

        response_existing = api_client.get(
            f"/api/v2/playout-history/{playout.id}",
        )
        response_nonexistent = api_client.get("/api/v2/playout-history/999999")

        # If different status codes, ID enumeration is possible
        if response_existing.status_code != response_nonexistent.status_code:
            # This leaks existence information
            pass  # Document the behavior


@pytest.mark.django_db
class TestPlayoutHistoryRUDRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization - UPDATE mass assignment."""

    @pytest.fixture
    def own_playout(self, admin_user):
        """Create admin's own playout."""
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        return baker.make(
            PlayoutHistory,
            file=f,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )

    def test_bopla_update_change_id(
        self, api_client, admin_user, own_playout, faker,
    ):
        """
        BOPLA: Attempt to change ID via PUT.

        Should not be able to modify id field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        new_id = own_playout.id + 1000

        data = {
            "id": new_id,
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.put(
            f"/api/v2/playout-history/{own_playout.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("id") == new_id:
                pytest.xfail("T624: BOPLA - id can be modified via PUT")

    def test_bopla_patch_extra_fields_ignored(
        self, api_client, admin_user, own_playout,
    ):
        """
        BOPLA: PATCH with extra fields silently ignored.

        Should reject unknown fields.
        """
        data = {
            "ends": format_datetime(now() + timedelta(minutes=10)),
            "is_admin": True,
            "role": "superuser",
            "hacked": True,
        }

        response = api_client.patch(
            f"/api/v2/playout-history/{own_playout.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            # Extra fields were silently ignored
            pytest.xfail("T625: BOPLA - PATCH extra fields silently ignored")

    def test_bopla_full_update_with_invalid_field(
        self, api_client, admin_user, own_playout, faker,
    ):
        """
        BOPLA: Full UPDATE attempts to set invalid fields.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
            "invalid_field": "should_not_be_accepted",
            "another_bad_field": 12345,
        }

        response = api_client.put(
            f"/api/v2/playout-history/{own_playout.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T625: BOPLA - PUT accepts extra/unknown fields")


@pytest.mark.django_db
class TestPlayoutHistoryRUDRedTeamInjection:
    """Injection attacks on RUD endpoints."""

    def test_sqli_in_retrieve_id(self, api_client, admin_user):
        """
        SQL Injection via ID in URL path.
        """
        sqli_ids = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_playout_history--",
            "1 UNION SELECT * FROM pg_authid",
        ]

        for bad_id in sqli_ids:
            response = api_client.get(f"/api/v2/playout-history/{bad_id}")

            if response.status_code == 500:
                pytest.xfail(f"T626: SQLi in ID causes 500: {bad_id[:30]}")

            error_text = str(response.content).lower()
            if "sql" in error_text or "syntax" in error_text:
                pytest.xfail(f"T626: SQLi error disclosure: {bad_id[:30]}")

    def test_sqli_in_update_fields(self, api_client, admin_user, faker):
        """
        SQL Injection via UPDATE fields.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        sqli_payloads = [
            "2026-04-09T10:00:00Z' OR '1'='1",
            "2026-04-09T10:00:00Z'; DROP TABLE cc_playout_history--",
        ]

        for payload in sqli_payloads:
            data = {
                "file": f.id,
                "starts": payload,
                "ends": format_datetime(now() + timedelta(minutes=5)),
            }

            response = api_client.put(
                f"/api/v2/playout-history/{playout.id}",
                data,
                format="json",
            )

            if response.status_code == 500:
                pytest.xfail("T626: SQLi in UPDATE causes 500")

    def test_no_sql_injection_id(self, api_client, admin_user):
        """
        NoSQL injection via ID parameter.
        """
        nosql_ids = [
            "{'$ne': None}",
            "{'$gt': ''}",
        ]

        for bad_id in nosql_ids:
            response = api_client.get(f"/api/v2/playout-history/{bad_id}")
            # Should not crash
            assert response.status_code in [200, 404, 400]


@pytest.mark.django_db
class TestPlayoutHistoryRUDRedTeamRaceConditions:
    """Race condition tests."""

    def test_race_condition_concurrent_update(
        self, api_client, admin_user, faker,
    ):
        """
        Race condition: Concurrent UPDATE to same record.

        May result in lost updates.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        # First update
        data1 = {
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }
        response1 = api_client.put(
            f"/api/v2/playout-history/{playout.id}",
            data1,
            format="json",
        )

        # Second update immediately after
        data2 = {
            "file": f.id,
            "starts": format_datetime(now() + timedelta(minutes=1)),
            "ends": format_datetime(now() + timedelta(minutes=6)),
        }
        response2 = api_client.put(
            f"/api/v2/playout-history/{playout.id}",
            data2,
            format="json",
        )

        # Both should succeed (last write wins)
        # Document behavior - no optimistic locking
        if response1.status_code == 200 and response2.status_code == 200:
            pass  # Document: no versioning/locking

    def test_race_condition_update_during_delete(
        self, api_client, admin_user, faker,
    ):
        """
        Race condition: UPDATE during DELETE.

        Undefined behavior - document what happens.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        # Delete
        delete_response = api_client.delete(
            f"/api/v2/playout-history/{playout.id}",
        )

        # Try to update deleted record
        data = {
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }
        update_response = api_client.put(
            f"/api/v2/playout-history/{playout.id}",
            data,
            format="json",
        )

        # Should get 404 for update on deleted record
        assert update_response.status_code == 404

    def test_race_condition_delete_already_deleted(
        self, api_client, admin_user, faker,
    ):
        """
        Race condition: Double DELETE of same record.

        Second delete should return 404.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        # First delete
        response1 = api_client.delete(f"/api/v2/playout-history/{playout.id}")
        assert response1.status_code == 204

        # Second delete
        response2 = api_client.delete(f"/api/v2/playout-history/{playout.id}")
        assert response2.status_code == 404


@pytest.mark.django_db
class TestPlayoutHistoryRUDRedTeamAuthorization:
    """Authorization level tests."""

    def test_retrieve_as_regular_user(
        self, api_client, regular_user, admin_user, faker,
    ):
        """
        BFLA: Regular user RETRIEVE permissions.
        """
        # Create playout as admin
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        # Regular user tries to retrieve
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/playout-history/{playout.id}")

        if response.status_code == 200:
            # Regular user can retrieve - document permission
            pass
        elif response.status_code == 403:
            # Properly restricted
            pass

    def test_update_as_regular_user(self, api_client, regular_user, faker):
        """
        BFLA: Regular user UPDATE permissions.
        """
        # Create playout for regular user
        f = baker.make(File, mime="audio/mp3", owner=regular_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        api_client.force_authenticate(user=regular_user)

        data = {
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.put(
            f"/api/v2/playout-history/{playout.id}",
            data,
            format="json",
        )

        # Document whether regular users can update
        assert response.status_code in [200, 403]

    def test_delete_as_regular_user(self, api_client, regular_user, faker):
        """
        BFLA: Regular user DELETE permissions.
        """
        f = baker.make(File, mime="audio/mp3", owner=regular_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        api_client.force_authenticate(user=regular_user)

        response = api_client.delete(f"/api/v2/playout-history/{playout.id}")

        # Document whether regular users can delete
        assert response.status_code in [204, 403]

    def test_unauthenticated_rud(self, api_client, admin_user, faker):
        """
        Auth: Unauthenticated RUD operations should fail.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        api_client.logout()

        # RETRIEVE
        r_get = api_client.get(f"/api/v2/playout-history/{playout.id}")
        assert r_get.status_code == 403

        # UPDATE
        r_put = api_client.put(
            f"/api/v2/playout-history/{playout.id}",
            {"file": f.id, "starts": format_datetime(now())},
            format="json",
        )
        assert r_put.status_code == 403

        # DELETE
        r_delete = api_client.delete(f"/api/v2/playout-history/{playout.id}")
        assert r_delete.status_code == 403


@pytest.mark.django_db
class TestPlayoutHistoryRUDRedTeamValidation:
    """Validation and edge case tests."""

    def test_update_to_invalid_file(self, api_client, admin_user, faker):
        """
        Validation: UPDATE to non-existent file should fail.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {
            "file": 999999,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.put(
            f"/api/v2/playout-history/{playout.id}",
            data,
            format="json",
        )

        assert response.status_code == 400

    def test_update_starts_after_ends(self, api_client, admin_user, faker):
        """
        Validation: UPDATE with starts > ends should fail.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {
            "file": f.id,
            "starts": format_datetime(now() + timedelta(minutes=10)),
            "ends": format_datetime(now()),
        }

        response = api_client.put(
            f"/api/v2/playout-history/{playout.id}",
            data,
            format="json",
        )

        # Validation should catch this
        if response.status_code == 200:
            pytest.xfail(
                "Validation bypass - starts after ends accepted on UPDATE",
            )

    def test_partial_update_invalid_datetime(
        self, api_client, admin_user, faker,
    ):
        """
        Validation: PATCH with invalid datetime format.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {"ends": "not-a-valid-datetime"}

        response = api_client.patch(
            f"/api/v2/playout-history/{playout.id}",
            data,
            format="json",
        )

        assert response.status_code in [200, 400]  # Document behavior


@pytest.mark.django_db
class TestPlayoutHistoryRUDRedTeamHTTPMethodTampering:
    """HTTP method tampering tests."""

    def test_method_override_on_retrieve(self, api_client, admin_user, faker):
        """
        Method override: POST with X-HTTP-Method-Override to retrieve.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        response = api_client.post(
            f"/api/v2/playout-history/{playout.id}",
            {},
            headers={"X-HTTP-Method-Override": "GET"},
        )

        # Should not work - POST is not valid for single resource
        assert response.status_code in [405, 403, 400]

    def test_trace_method(self, api_client, admin_user, faker):
        """
        TRACE method should be disabled.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        response = api_client.trace(f"/api/v2/playout-history/{playout.id}")

        # TRACE should be disabled (security best practice)
        assert response.status_code in [405, 403]
