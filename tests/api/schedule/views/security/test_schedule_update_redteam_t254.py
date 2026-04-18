"""Red Team security tests for Schedule UPDATE endpoint (T254).

Tests focus on:
- API1:2023 BOLA (updating other users' schedule)
- API2:2023 Broken Authentication
- API3:2023 BOPLA (mass assignment on update)
- API6:2023 Unsafe Business Flows
- API7:2023 SSRF via stream change
- API8:2023 Security Misconfiguration
- Injection attacks
"""

import json

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleUpdateRedTeam:
    """Red Team tests for Schedule UPDATE endpoint - PUT/PATCH /api/v2/schedule/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    def _get_update_data(
        self,
        instance,
        file_obj=None,
        stream=None,
        **overrides,
    ):
        """Helper to generate valid update data with proper datetime formatting."""
        base_time = now() + timedelta(hours=1)

        data = {
            "instance": instance.id,
            "starts_at": format_datetime(base_time),
            "ends_at": format_datetime(base_time + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }

        if file_obj:
            data["file"] = file_obj.id
        else:
            data["file"] = None

        if stream:
            data["stream"] = stream.id
        else:
            data["stream"] = None

        data.update(overrides)
        return data

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T592: BOLA - Can update other user's schedule")
    def test_bola_update_other_users_schedule(self, guest_client, faker):
        """BOLA: Can update another user's schedule entry."""
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

        # Attacker tries to update victim's schedule
        data = self._get_update_data(instance, file_obj=file_obj, position=999)
        response = guest_client.patch(
            f"/api/v2/schedule/{victim_schedule.id}",
            json.dumps(data),
            content_type="application/json",
        )

        assert (
            response.status_code == 403
        ), f"BOLA: Got {response.status_code}, expected 403 - can update other's schedule"

    @pytest.mark.xfail(
        reason="T593: BOLA - Can change schedule to other user's file",
    )
    def test_bola_update_to_other_user_file(self, guest_client, faker):
        """BOLA: Can update schedule to use another user's file."""
        victim = baker.make(
            User,
            username=f"testred_victim_{faker.user_name()}",
        )
        attacker = baker.make(
            User,
            username=f"testred_attacker_{faker.user_name()}",
        )
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)

        attacker_file = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=attacker,
        )
        victim_file = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=victim,
        )

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=attacker_file,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Try to change to victim's file
        data = self._get_update_data(instance, file_obj=victim_file)
        response = guest_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("BOLA: Can change schedule to other user's file")

    @pytest.mark.xfail(
        reason="T594: BOLA - Can change schedule to other user's stream",
    )
    def test_bola_update_to_other_user_stream(self, guest_client, faker):
        """BOLA: Can update schedule to use another user's stream."""
        victim = baker.make(
            User,
            username=f"testred_victim_{faker.user_name()}",
        )
        attacker = baker.make(
            User,
            username=f"testred_attacker_{faker.user_name()}",
        )
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)

        attacker_stream = baker.make(
            Webstream,
            name=faker.catch_phrase(),
            url=faker.url(),
            owner=attacker,
        )
        victim_stream = baker.make(
            Webstream,
            name=faker.catch_phrase(),
            url=faker.url(),
            owner=victim,
        )

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            stream=attacker_stream,
            file=None,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Try to change to victim's stream
        data = self._get_update_data(instance, stream=victim_stream)
        response = guest_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("BOLA: Can change schedule to other user's stream")

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    def test_bopla_mass_assignment_id_update(self, guest_client, faker):
        """BOPLA: Check if ID can be changed during UPDATE."""
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

        old_id = schedule.id
        fake_id = faker.random_int(min=100000, max=999999)

        data = self._get_update_data(instance, file_obj=file_obj, id=fake_id)
        response = guest_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            resp_data = response.json()
            if resp_data.get("id") != old_id:
                pytest.fail("BOPLA: Can change ID during UPDATE")

    # ========================================================================
    # API6:2023 - Unsafe Business Flows
    # ========================================================================

    @pytest.mark.xfail(
        reason="T595: Logic - Can create schedule overlap via update",
    )
    def test_business_logic_overlap_via_update(self, guest_client, faker):
        """Logic: Can create overlapping schedules via UPDATE."""
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

        # Create first schedule
        schedule1 = baker.make(
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

        # Create second schedule
        schedule2 = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=2),
            ends_at=base_time + timedelta(hours=2, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )

        # Try to update second schedule to overlap with first
        data = self._get_update_data(
            instance,
            file_obj=file_obj,
            starts_at=format_datetime(
                base_time + timedelta(minutes=3),
            ),  # Overlaps
            ends_at=format_datetime(base_time + timedelta(minutes=8)),
        )
        response = guest_client.patch(
            f"/api/v2/schedule/{schedule2.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("Logic: Overlap created via UPDATE")

    # ========================================================================
    # API7:2023 - SSRF
    # ========================================================================

    @pytest.mark.xfail(reason="T596: SSRF - Can update to internal stream URL")
    def test_ssrf_update_to_internal_stream(self, guest_client, faker):
        """SSRF: Can update schedule to use internal stream."""
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

        # Create internal stream
        internal_stream = baker.make(
            Webstream,
            name=faker.catch_phrase(),
            url="http://169.254.169.254/latest/meta-data/",
            owner=user,
        )

        data = self._get_update_data(instance, stream=internal_stream)
        response = guest_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("SSRF: Can update to internal stream URL")

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_update_without_auth(self, client, faker):
        """Auth: UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/schedule/1",
            json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_with_invalid_token(self, faker):
        """T597: Auth: Invalid token should be rejected with 403.

        FIXED: Use credentials() to properly override auth.
        defaults[] does NOT override credentials() set in guest_client fixture.
        """
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {faker.uuid4()}")

        response = client.patch(
            "/api/v2/schedule/1",
            json.dumps({}),
            content_type="application/json",
        )
        assert (
            response.status_code == 403
        ), f"T597: Invalid token should return 403, got {response.status_code}"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_update_fields(self, guest_client, faker):
        """Injection: SQLi in UPDATE fields."""
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

        sqli_payloads = [
            "00:00:00' OR '1'='1",
            "00:00:00'; DROP TABLE cc_schedule;--",
        ]

        for payload in sqli_payloads:
            data = self._get_update_data(
                instance,
                file_obj=file_obj,
                cue_in=payload,
            )
            response = guest_client.patch(
                f"/api/v2/schedule/{schedule.id}",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 500:
                pytest.fail(f"SQLi in cue_in: '{payload}' caused 500")

    def test_nosql_injection_in_update(self, guest_client, faker):
        """Injection: NoSQL operators in UPDATE fields."""
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

        # Try NoSQL injection via JSON
        base_time = now() + timedelta(hours=1)
        data = {
            "instance": {"$ne": None},
            "file": {"$exists": True},
            "starts_at": format_datetime(base_time),
            "ends_at": format_datetime(base_time + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = guest_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            200,
            400,
        ], f"NoSQLi caused unexpected {response.status_code}"

    # ========================================================================
    # Input Validation
    # ========================================================================

    def test_unicode_in_update_fields(self, guest_client, faker):
        """Validation: Unicode in UPDATE fields."""
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

        data = self._get_update_data(
            instance,
            file_obj=file_obj,
            cue_in="日本語",
        )
        response = guest_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            200,
            400,
        ], f"Unicode caused unexpected {response.status_code}"

    # ========================================================================
    # Race Condition
    # ========================================================================

    def test_race_condition_concurrent_update(self, guest_client, faker):
        """Race: Concurrent UPDATE of same schedule."""
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

        def update_schedule(position):
            data = self._get_update_data(
                instance,
                file_obj=file_obj,
                position=position,
            )
            return guest_client.patch(
                f"/api/v2/schedule/{schedule.id}",
                json.dumps(data),
                content_type="application/json",
            ).status_code

        # Fire 5 concurrent updates
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_schedule, i) for i in range(5)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        success_count = results.count(200)
        # Should be consistent
        if success_count != 5 and success_count != 0:
            pytest.fail(
                f"Race condition: {success_count}/5 updates succeeded inconsistently",
            )
