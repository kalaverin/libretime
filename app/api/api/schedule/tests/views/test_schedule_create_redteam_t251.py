"""Red Team security tests for Schedule CREATE endpoint (T251-T252).

Tests focus on:
- API1:2023 BOLA (creating schedule for other users' shows)
- API2:2023 Broken Authentication
- API3:2023 BOPLA (mass assignment on create)
- API6:2023 Unsafe Business Flows
- API7:2023 SSRF via stream URLs
- API8:2023 Security Misconfiguration
- Injection attacks in create fields
"""

import json
from datetime import timedelta

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File
from sdk import now
from sdk.datetime import format_datetime, reformat_datetime


@pytest.mark.django_db(transaction=True)
class TestScheduleCreateRedTeam:
    """Red Team tests for Schedule CREATE endpoint - POST /api/v2/schedule."""

    def setup_method(self):
        """Clean up before each test."""
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    def _get_schedule_data(self, instance, file_obj=None, stream=None, **overrides):
        """Helper to generate valid schedule data with proper datetime formatting."""
        base_time = now()
        starts_at = base_time + timedelta(hours=1)
        ends_at = starts_at + timedelta(minutes=5)

        data = {
            "instance": instance.id,
            "starts_at": format_datetime(starts_at),
            "ends_at": format_datetime(ends_at),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }

        if file_obj:
            data["file"] = file_obj.id
        if stream:
            data["stream"] = stream.id

        data.update(overrides)
        return data

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T576: BOLA - Can create schedule for other user's show")
    def test_bola_create_schedule_for_other_user_show(self, api_client, faker):
        """BOLA: Can create schedule entry in another user's show instance."""
        victim = baker.make(User, username=f"testred_victim_{faker.user_name()}")
        attacker_file = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=victim,
        )

        # Victim's show and instance
        victim_show = baker.make(Show, name=faker.catch_phrase())
        victim_instance = baker.make(ShowInstance, show=victim_show)

        # Attacker tries to create schedule in victim's show
        data = self._get_schedule_data(victim_instance, file_obj=attacker_file)
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"BOLA: Got {response.status_code}, expected 403 - can create schedule in other's show"

    @pytest.mark.xfail(reason="T577: BOLA - Can create schedule using other user's file")
    def test_bola_create_schedule_with_other_user_file(self, api_client, faker):
        """BOLA: Can create schedule using another user's file without permission."""
        victim = baker.make(User, username=f"testred_victim_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)

        # Victim's file
        victim_file = baker.make(
            File,
            name=faker.file_name(),
            mime=faker.mime_type(),
            owner=victim,
        )

        # Attacker tries to use victim's file
        data = self._get_schedule_data(instance, file_obj=victim_file)
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"BOLA: Got {response.status_code}, expected 403 - can use other's file"

    @pytest.mark.xfail(reason="T578: BOLA - Can create schedule using other user's stream")
    def test_bola_create_schedule_with_other_user_stream(self, api_client, faker):
        """BOLA: Can create schedule using another user's webstream."""
        victim = baker.make(User, username=f"testred_victim_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)

        # Victim's stream
        victim_stream = baker.make(
            Webstream,
            name=faker.catch_phrase(),
            url=faker.url(),
            owner=victim,
        )

        # Attacker tries to use victim's stream
        data = self._get_schedule_data(instance, stream=victim_stream)
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"BOLA: Got {response.status_code}, expected 403 - can use other's stream"

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    def test_bopla_mass_assignment_id(self, api_client, faker):
        """BOPLA: Check if custom ID can be set during CREATE."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        fake_id = faker.random_int(min=100000, max=999999)
        data = self._get_schedule_data(instance, file_obj=file_obj, id=fake_id)

        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            resp_data = response.json()
            if resp_data.get("id") == fake_id:
                pytest.fail(f"BOPLA: Can set custom ID during CREATE (id={fake_id})")

    def test_bopla_mass_assignment_readonly(self, api_client, faker):
        """BOPLA: Check if read-only fields can be mass assigned."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        data = self._get_schedule_data(
            instance,
            file_obj=file_obj,
            position_status=999,  # Should not be writable
        )

        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            resp_data = response.json()
            if resp_data.get("position_status") == 999:
                pytest.fail("BOPLA: Can set invalid position_status")

    # ========================================================================
    # API6:2023 - Unsafe Business Flows
    # ========================================================================

    @pytest.mark.xfail(reason="T581: Business Logic - No schedule overlap validation")
    def test_business_logic_schedule_overlap(self, api_client, faker):
        """Logic: Can create overlapping schedule entries."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        base_time = now() + timedelta(hours=1)

        # Create first schedule
        data1 = self._get_schedule_data(
            instance,
            file_obj=file_obj,
            starts_at=format_datetime(base_time),
            ends_at=format_datetime(base_time + timedelta(minutes=5)),
        )
        api_client.post(
            "/api/v2/schedule",
            json.dumps(data1),
            content_type="application/json",
        )

        # Try to create overlapping schedule
        data2 = self._get_schedule_data(
            instance,
            file_obj=file_obj,
            starts_at=format_datetime(base_time + timedelta(minutes=2)),  # Overlaps
            ends_at=format_datetime(base_time + timedelta(minutes=7)),
            position=2,
        )
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data2),
            content_type="application/json",
        )

        # Should reject overlapping schedules
        if response.status_code == 201:
            pytest.fail("Logic: Overlapping schedules allowed")

    @pytest.mark.xfail(reason="T582: Business Logic - No show time boundary validation")
    def test_business_logic_outside_show_time(self, api_client, faker):
        """Logic: Can create schedule outside show time boundaries."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())

        base_time = now()
        # Instance with specific time
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=base_time,
            ends_at=base_time + timedelta(hours=1),
        )

        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        # Try to create schedule outside show time
        data = self._get_schedule_data(
            instance,
            file_obj=file_obj,
            starts_at=format_datetime(base_time + timedelta(hours=2)),  # Outside show time
            ends_at=format_datetime(base_time + timedelta(hours=2, minutes=5)),
        )
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            pytest.fail("Logic: Schedule outside show time allowed")

    # ========================================================================
    # API7:2023 - SSRF via Stream URLs
    # ========================================================================

    @pytest.mark.xfail(reason="T583: SSRF - Schedule created with internal stream URL")
    def test_ssrf_create_schedule_with_internal_stream(self, api_client, faker):
        """SSRF: Can create schedule with internal stream URL."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)

        # Create stream with internal URL
        internal_stream = baker.make(
            Webstream,
            name=faker.catch_phrase(),
            url="http://169.254.169.254/latest/meta-data/",
            owner=user,
        )

        data = self._get_schedule_data(instance, stream=internal_stream)
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            pytest.fail("SSRF: Schedule created with internal stream URL")

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_create_without_auth(self, client):
        """Auth: CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/schedule",
            json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 403

    @pytest.mark.xfail(reason="T584: Auth - Invalid token returns 200 instead of 403")
    def test_create_with_invalid_token(self, api_client, faker):
        """Auth: Invalid token should be rejected."""
        original = api_client.defaults.get("HTTP_AUTHORIZATION", "")
        api_client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {faker.uuid4()}"

        try:
            response = api_client.post(
                "/api/v2/schedule",
                json.dumps({}),
                content_type="application/json",
            )
            if response.status_code == 200:
                pytest.fail("T584: Invalid token accepted - authentication bypass")
            assert response.status_code == 403
        finally:
            api_client.defaults["HTTP_AUTHORIZATION"] = original

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_create_fields(self, api_client, faker):
        """Injection: SQLi in CREATE fields."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        sqli_payloads = [
            "00:00:00' OR '1'='1",
            "00:00:00'; DROP TABLE cc_schedule;--",
        ]

        for payload in sqli_payloads:
            data = self._get_schedule_data(instance, file_obj=file_obj, cue_in=payload)
            response = api_client.post(
                "/api/v2/schedule",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 500:
                pytest.fail(f"SQLi in cue_in: '{payload}' caused 500")

    def test_nosql_injection_in_create(self, api_client, faker):
        """Injection: NoSQL operators in CREATE fields."""
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)

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
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )
        # Should not crash
        assert response.status_code in [200, 201, 400], \
            f"NoSQLi caused unexpected {response.status_code}"

    # ========================================================================
    # Input Validation
    # ========================================================================

    def test_unicode_in_create_fields(self, api_client, faker):
        """Validation: Unicode in CREATE fields."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        data = self._get_schedule_data(instance, file_obj=file_obj, cue_in="日本語")
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )
        # Should handle gracefully
        assert response.status_code in [200, 201, 400], \
            f"Unicode caused unexpected {response.status_code}"

    def test_negative_position(self, api_client, faker):
        """Validation: Negative position values."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        data = self._get_schedule_data(instance, file_obj=file_obj, position=-999)
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )
        # Should validate position range
        assert response.status_code in [201, 400], \
            f"Negative position returned {response.status_code}"

    def test_invalid_date_formats(self, api_client, faker):
        """Validation: Invalid date formats."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        invalid_dates = [
            "not-a-date",
            "2026-13-45T25:00:00Z",
            "",
        ]

        for date_str in invalid_dates:
            data = self._get_schedule_data(
                instance,
                file_obj=file_obj,
                starts_at=date_str,
            )
            response = api_client.post(
                "/api/v2/schedule",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code in [201, 400], \
                f"Date '{date_str}' caused unexpected {response.status_code}"

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    def test_create_error_reveals_field_info(self, api_client, faker):
        """Info Leak: Check if CREATE errors reveal field information."""
        show = baker.make(Show, name=faker.catch_phrase())
        base_time = now() + timedelta(hours=1)

        data = {
            "instance": 999999,
            "file": 999999,
            "starts_at": format_datetime(base_time),
            "ends_at": format_datetime(base_time + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(data),
            content_type="application/json",
        )

        # Just check it doesn't crash with 500
        assert response.status_code in [201, 400]

    # ========================================================================
    # Race Condition
    # ========================================================================

    @pytest.mark.xfail(reason="T586: Race condition - concurrent CREATE same slot")
    def test_race_condition_concurrent_create(self, api_client, faker):
        """Race: Concurrent CREATE for same time slot."""
        import concurrent.futures

        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        def create_schedule():
            data = self._get_schedule_data(instance, file_obj=file_obj)
            return api_client.post(
                "/api/v2/schedule",
                json.dumps(data),
                content_type="application/json",
            ).status_code

        # Fire 5 concurrent creates
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_schedule) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = results.count(201)
        # Should only allow one or reject all consistently
        if success_count > 1:
            pytest.fail(f"Race condition: {success_count}/5 concurrent creates succeeded")
