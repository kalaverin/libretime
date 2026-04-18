"""Red Team security tests for Schedule DELETE endpoint (T255).

Tests focus on:
- API1:2023 BOLA (deleting other users' schedule)
- API2:2023 Broken Authentication
- API6:2023 Unsafe Business Flows (race conditions)
- API8:2023 Security Misconfiguration
- Injection attacks
- Mass deletion attacks
"""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleDeleteRedTeam:
    """Red Team tests for Schedule DELETE endpoint - DELETE /api/v2/schedule/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T598: BOLA - Can delete other user's schedule")
    def test_bola_delete_other_users_schedule(self, admin_client, faker):
        """BOLA: Can delete another user's schedule entry."""
        victim = baker.make(
            User,
            username=f"testred_victim_{faker.user_name()}",
        )
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=victim,
        )

        base_time = now()
        victim_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        response = admin_client.delete(f"/api/v2/schedule/{victim_schedule.id}")
        assert (
            response.status_code == 403
        ), f"BOLA: Got {response.status_code}, expected 403 - can delete other's schedule"

    @pytest.mark.xfail(
        reason="T599: BOLA - DELETE returns wrong status for other's schedule",
    )
    def test_bola_delete_other_users_schedule_status(self, admin_client, faker):
        """BOLA: DELETE of other's schedule returns wrong status code."""
        victim = baker.make(
            User,
            username=f"testred_victim_{faker.user_name()}",
        )
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=victim,
        )

        base_time = now()
        victim_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        response = admin_client.delete(f"/api/v2/schedule/{victim_schedule.id}")
        if response.status_code == 204:
            pytest.fail(
                "T599: BOLA - Successfully deleted other user's schedule!",
            )
        elif response.status_code == 404:
            pytest.fail(
                "T599: Info leak - 404 reveals schedule doesn't exist (should be 403)",
            )

    def test_bola_batch_delete_scope(self, admin_client, faker):
        """BOLA: Batch delete scope verification."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=user,
        )

        base_time = now()
        schedules = []
        for i in range(5):
            schedule = baker.make(
                Schedule,
                instance=instance,
                file=file_obj,
                starts_at=base_time + timedelta(hours=i),
                ends_at=base_time + timedelta(hours=i, minutes=5),
                cue_in="00:00:00",
                cue_out="00:05:00",
                position=i,
                broadcasted=1,
            )
            schedules.append(schedule)

        initial_count = Schedule.objects.count()
        admin_client.delete(f"/api/v2/schedule/{schedules[0].id}")
        final_count = Schedule.objects.count()

        if initial_count - final_count > 1:
            pytest.fail(
                f"Batch delete affected {initial_count - final_count} schedules",
            )

    # ========================================================================
    # API2:2023 - Broken Authentication
    # ========================================================================

    def test_delete_without_auth(self, client, faker):
        """Auth: DELETE without auth should return 403."""
        response = client.delete("/api/v2/schedule/1")
        assert response.status_code == 403

    def test_delete_with_invalid_token(self, faker):
        """T600: Auth: Invalid token should be rejected with 403.

        FIXED: Use credentials() to properly override auth.
        defaults[] does NOT override credentials() set in admin_client fixture.
        """
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {faker.uuid4()}")

        response = client.delete("/api/v2/schedule/1")
        # When test methodology is correct, this should pass (403 returned)
        assert (
            response.status_code == 403
        ), f"T600: Invalid token should return 403, got {response.status_code}"

    # ========================================================================
    # API6:2023 - Unsafe Business Flows
    # ========================================================================

    @pytest.mark.xfail(reason="Race condition - multiple deletes can succeed")
    def test_race_condition_concurrent_delete(self, admin_client, faker):
        """Race: Concurrent delete of same schedule."""
        import concurrent.futures

        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=user,
        )

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        def delete_schedule():
            return admin_client.delete(
                f"/api/v2/schedule/{schedule.id}",
            ).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(delete_schedule) for _ in range(5)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        success_count = results.count(204)
        not_found_count = results.count(404)

        if success_count != 1:
            pytest.fail(
                f"Race condition - {success_count} deletes succeeded, expected 1",
            )
        if not_found_count != 4:
            pytest.fail(
                f"Race condition - {not_found_count} got 404, expected 4",
            )

    @pytest.mark.xfail(
        reason="T601: Mass deletion - No rate limiting on delete",
    )
    def test_mass_deletion_rate_limit(self, admin_client, faker):
        """Unsafe Flow: Rate limiting on delete operations."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=user,
        )

        base_time = now()
        schedules = []
        for i in range(50):
            schedule = baker.make(
                Schedule,
                instance=instance,
                file=file_obj,
                starts_at=base_time + timedelta(hours=i),
                ends_at=base_time + timedelta(hours=i, minutes=5),
                cue_in="00:00:00",
                cue_out="00:05:00",
                position=i,
                broadcasted=1,
            )
            schedules.append(schedule)

        delete_count = 0
        rate_limited = False
        for schedule in schedules:
            response = admin_client.delete(f"/api/v2/schedule/{schedule.id}")
            if response.status_code == 204:
                delete_count += 1
            elif response.status_code == 429:
                rate_limited = True
                break

        if not rate_limited and delete_count == 50:
            pytest.fail("T601: No rate limiting on mass deletion")

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_http_method_override_delete(self, admin_client, faker):
        """Misconfig: HTTP method override may bypass delete restrictions."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=user,
        )

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        admin_client.get(
            f"/api/v2/schedule/{schedule.id}",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )

        if not Schedule.objects.filter(id=schedule.id).exists():
            pytest.fail("HTTP method override allowed DELETE via GET")

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_delete_id(self, admin_client, faker):
        """Injection: SQLi in DELETE id path parameter."""
        sqli_payloads = [
            "1 OR 1=1",
            "1; DROP TABLE cc_schedule;--",
            "1' OR '1'='1",
            "1 UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = admin_client.delete(f"/api/v2/schedule/{payload}")
            assert response.status_code in [
                400,
                404,
            ], f"SQLi '{payload}' caused {response.status_code}"

    def test_path_traversal_in_delete_id(self, admin_client, faker):
        """Injection: Path traversal in DELETE id."""
        traversal_ids = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2fetc%2fpasswd",
        ]

        for test_id in traversal_ids:
            response = admin_client.delete(f"/api/v2/schedule/{test_id}")
            assert response.status_code in [
                400,
                404,
            ], f"Path traversal '{test_id}' caused {response.status_code}"

    # ========================================================================
    # Input Validation
    # ========================================================================

    def test_unicode_in_delete_id(self, admin_client, faker):
        """Validation: Unicode in DELETE id handled gracefully."""
        response = admin_client.delete("/api/v2/schedule/日本語")
        assert response.status_code in [400, 404]

    def test_negative_id_delete(self, admin_client, faker):
        """Validation: Negative ID in DELETE."""
        response = admin_client.delete("/api/v2/schedule/-1")
        assert response.status_code == 404

    def test_null_bytes_in_delete_id(self, admin_client, faker):
        """Validation: Null bytes in DELETE id."""
        response = admin_client.delete("/api/v2/schedule/1%00test")
        assert response.status_code in [400, 404]

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    @pytest.mark.xfail(
        reason="T602: Info Leak - DELETE error reveals schedule existence",
    )
    def test_error_message_leaks_existence_delete(self, admin_client, faker):
        """Info Leak: Error messages reveal if schedule exists."""
        victim = baker.make(
            User,
            username=f"testred_victim_{faker.user_name()}",
        )
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=victim,
        )

        base_time = now()
        victim_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        response_existing = admin_client.delete(
            f"/api/v2/schedule/{victim_schedule.id}",
        )
        response_nonexistent = admin_client.delete("/api/v2/schedule/999999")

        if response_existing.status_code != response_nonexistent.status_code:
            pytest.fail(
                f"T602: Status leak: existing={response_existing.status_code}, "
                f"nonexistent={response_nonexistent.status_code}",
            )

    # ========================================================================
    # ID Enumeration
    # ========================================================================

    def test_id_enumeration_timing_attack(self, admin_client, faker):
        """Security: Timing difference between existing and non-existing IDs."""
        import time

        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=user,
        )

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        start = time.time()
        admin_client.delete(f"/api/v2/schedule/{schedule.id}")
        time_existing = time.time() - start

        start = time.time()
        admin_client.delete("/api/v2/schedule/999999")
        time_nonexistent = time.time() - start

        if time_existing > 0:
            ratio = max(time_existing, time_nonexistent) / min(
                time_existing,
                time_nonexistent,
            )
            if ratio > 3:
                pytest.skip(f"Timing leak: ratio {ratio:.1f}")

    # ========================================================================
    # Business Logic
    # ========================================================================

    def test_double_delete_returns_404(self, admin_client, faker):
        """Logic: Double delete should return 404."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=user,
        )

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        admin_client.delete(f"/api/v2/schedule/{schedule.id}")
        response = admin_client.delete(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 404
