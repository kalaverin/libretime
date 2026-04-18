"""Red Team security tests for Schedule overbooked filter (T257).

Tests focus on:
- API1:2023 BOLA (filter bypasses)
- API3:2023 BOPLA (filter parameter injection)
- API6:2023 Unsafe Business Flows
- API8:2023 Security Misconfiguration
- Filter manipulation attacks
"""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleOverbookedFilterRedTeam:
    """Red Team tests for Schedule overbooked filter - T257."""

    def setup_method(self):
        """Clean up before each test."""
        Schedule.objects.all().delete()
        File.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # Filter Parameter Manipulation
    # ========================================================================

    @pytest.mark.xfail(reason="T613: Filter - overbooked parameter injection")
    def test_overbooked_sql_injection(self, guest_client, faker):
        """Injection: SQLi in overbooked filter parameter."""
        sqli_payloads = [
            "1 OR 1=1",
            "1' OR '1'='1",
            "1; DROP TABLE cc_schedule;--",
            "true UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = guest_client.get(f"/api/v2/schedule?overbooked={payload}")
            if response.status_code == 500:
                pytest.fail(f"SQLi in overbooked: '{payload}' caused 500")

    def test_overbooked_nosql_injection(self, guest_client, faker):
        """Injection: NoSQL in overbooked filter."""
        nosql_payloads = [
            {"overbooked": {"$ne": None}},
            {"overbooked": {"$exists": True}},
        ]

        for payload in nosql_payloads:
            response = guest_client.get("/api/v2/schedule", payload)
            assert response.status_code in [
                200,
                400,
            ], f"NoSQLi caused {response.status_code}"

    @pytest.mark.xfail(reason="T614: Filter - overbooked bypass using null")
    def test_overbooked_null_bypass(self, guest_client, faker):
        """Filter: Using null/undefined to bypass overbooked filter."""
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
        # Create overbooked schedule
        overbooked = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=instance.ends_at + timedelta(minutes=5),
            ends_at=instance.ends_at + timedelta(minutes=10),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Try to bypass filter with null
        response = guest_client.get("/api/v2/schedule?overbooked=null")
        data = response.json()

        # Should not return data when filter is bypassed
        ids = [s["id"] for s in data]
        if overbooked.id in ids:
            pytest.fail(
                "T614: Filter bypass with null returned overbooked schedule",
            )

    # ========================================================================
    # Filter Logic Bypass
    # ========================================================================

    @pytest.mark.xfail(reason="T615: Filter - overbooked logic bypass")
    def test_overbooked_logic_bypass(self, guest_client, faker):
        """Filter: Logic bypass in overbooked calculation."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())

        base_time = now()
        # Create instance with no ends_at
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=base_time,
            ends_at=None,  # No end time
        )

        file_obj = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=user,
        )

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

        # Query overbooked with null ends_at
        response = guest_client.get("/api/v2/schedule?overbooked=1")
        # Should handle gracefully, not crash
        assert response.status_code in [
            200,
            500,
        ], f"Unexpected status: {response.status_code}"

    # ========================================================================
    # BOLA via Filter
    # ========================================================================

    @pytest.mark.xfail(
        reason="T616: BOLA - overbooked filter reveals other users' schedules",
    )
    def test_overbooked_bola_info_leak(self, guest_client, faker):
        """BOLA: overbooked filter reveals other users' schedules."""
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
        # Victim's overbooked schedule
        victim_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=instance.ends_at + timedelta(minutes=5),
            ends_at=instance.ends_at + timedelta(minutes=10),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Attacker queries overbooked
        response = guest_client.get("/api/v2/schedule?overbooked=1")
        data = response.json()

        ids = [s["id"] for s in data]
        if victim_schedule.id in ids:
            pytest.fail(
                "T616: overbooked filter reveals other user's schedule",
            )

    # ========================================================================
    # Filter Combination Attacks
    # ========================================================================

    def test_overbooked_with_other_filters(self, guest_client, faker):
        """Filter: Combining overbooked with other filters."""
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
        baker.make(
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

        # Combine filters
        response = guest_client.get(
            "/api/v2/schedule?overbooked=1&position=1&broadcasted=1",
        )
        assert response.status_code == 200

    @pytest.mark.xfail(reason="T617: Filter - overbooked with instance bypass")
    def test_overbooked_instance_bypass(self, guest_client, faker):
        """Filter: Using instance filter to bypass overbooked."""
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
            starts_at=instance.ends_at + timedelta(minutes=5),
            ends_at=instance.ends_at + timedelta(minutes=10),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Try to bypass using instance filter
        response = guest_client.get(
            f"/api/v2/schedule?overbooked=0&instance={instance.id}",
        )
        data = response.json()

        ids = [s["id"] for s in data]
        if victim_schedule.id in ids:
            pytest.fail("T617: Instance filter bypassed overbooked filter")

    # ========================================================================
    # Input Validation
    # ========================================================================

    def test_overbooked_invalid_values(self, guest_client, faker):
        """Validation: Invalid overbooked parameter values."""
        invalid_values = [
            "true",
            "false",
            "yes",
            "no",
            "",
            "null",
            "undefined",
            "2",
            "-1",
            "999",
        ]

        for value in invalid_values:
            response = guest_client.get(f"/api/v2/schedule?overbooked={value}")
            # Should handle gracefully
            assert response.status_code in [
                200,
                400,
            ], f"overbooked={value} caused {response.status_code}"

    def test_overbooked_unicode(self, guest_client, faker):
        """Validation: Unicode in overbooked parameter."""
        response = guest_client.get("/api/v2/schedule?overbooked=日本語")
        assert response.status_code in [200, 400]

    # ========================================================================
    # Performance / DoS
    # ========================================================================

    @pytest.mark.xfail(
        reason="T618: DoS - overbooked filter performance issue",
    )
    def test_overbooked_performance_dos(self, guest_client, faker):
        """DoS: overbooked filter with large dataset."""
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
        # Create many schedules
        for i in range(100):
            baker.make(
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

        start = time.time()
        response = guest_client.get("/api/v2/schedule?overbooked=1")
        duration = time.time() - start

        if duration > 3:
            pytest.fail(f"T618: overbooked filter slow: {duration:.2f}s")

    # ========================================================================
    # Business Logic
    # ========================================================================

    @pytest.mark.xfail(reason="T619: Logic - overbooked filter inconsistency")
    def test_overbooked_logic_consistency(self, guest_client, faker):
        """Logic: overbooked filter consistency check."""
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
        # Schedule exactly at show end (edge case)
        edge_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=instance.ends_at,  # Exactly at end
            ends_at=instance.ends_at + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Query overbooked=true
        response_true = guest_client.get("/api/v2/schedule?overbooked=1")
        data_true = response_true.json()
        ids_true = [s["id"] for s in data_true]

        # Query overbooked=false
        response_false = guest_client.get("/api/v2/schedule?overbooked=0")
        data_false = response_false.json()
        ids_false = [s["id"] for s in data_false]

        # Schedule should be in exactly one of them
        in_true = edge_schedule.id in ids_true
        in_false = edge_schedule.id in ids_false

        if in_true and in_false:
            pytest.fail(
                "T619: Schedule appears in both overbooked=true and false",
            )
        if not in_true and not in_false:
            pytest.fail("T619: Schedule missing from both filters")
