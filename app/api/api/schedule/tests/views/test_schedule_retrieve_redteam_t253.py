"""Red Team security tests for Schedule RETRIEVE endpoint (T253).

Tests focus on:
- API1:2023 BOLA (retrieving other users' schedule)
- API2:2023 Broken Authentication
- API3:2023 BOPLA (field exposure)
- API8:2023 Security Misconfiguration
- Information disclosure
- Injection in path
"""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleRetrieveRedTeam:
    """Red Team tests for Schedule RETRIEVE endpoint - GET /api/v2/schedule/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T587: BOLA - Can retrieve other user's schedule",
    )
    def test_bola_retrieve_other_users_schedule(self, api_client, faker):
        """BOLA: Can retrieve another user's schedule entry."""
        victim = baker.make(
            User, username=f"testred_victim_{faker.user_name()}",
        )
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File, name=faker.file_name(), mime=faker.mime_type(), owner=victim,
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

        response = api_client.get(f"/api/v2/schedule/{victim_schedule.id}")
        assert (
            response.status_code == 403
        ), f"BOLA: Got {response.status_code}, expected 403 - can retrieve other's schedule"

    def test_bola_id_enumeration_retrieve(self, api_client, faker):
        """BOLA: Sequential ID enumeration on retrieve."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File, name=faker.file_name(), mime=faker.mime_type(), owner=user,
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

        # Try to enumerate IDs
        found_count = 0
        for i in range(1, 50):
            response = api_client.get(f"/api/v2/schedule/{i}")
            if response.status_code == 200:
                found_count += 1

        assert found_count <= len(
            schedules,
        ), f"ID enumeration: found {found_count} accessible entries"

    # ========================================================================
    # API2:2023 - Broken Authentication
    # ========================================================================

    def test_retrieve_without_auth(self, client, faker):
        """Auth: RETRIEVE without auth should return 403."""
        response = client.get("/api/v2/schedule/1")
        assert response.status_code == 403

    @pytest.mark.xfail(reason="T589: Auth - Invalid token returns 200")
    def test_retrieve_with_invalid_token(self, api_client, faker):
        """Auth: Invalid token should be rejected."""
        original = api_client.defaults.get("HTTP_AUTHORIZATION", "")
        api_client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {faker.uuid4()}"

        try:
            response = api_client.get("/api/v2/schedule/1")
            if response.status_code == 200:
                pytest.fail("T589: Invalid token accepted")
            assert response.status_code == 403
        finally:
            api_client.defaults["HTTP_AUTHORIZATION"] = original

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    def test_bopla_sensitive_fields_exposed(self, api_client, faker):
        """BOPLA: Check if sensitive fields are exposed in retrieve response."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File, name=faker.file_name(), mime=faker.mime_type(), owner=user,
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

        response = api_client.get(f"/api/v2/schedule/{schedule.id}")
        data = response.json()

        # Check for sensitive fields that shouldn't be exposed
        sensitive_fields = [
            "password",
            "secret",
            "token",
            "key",
            "internal_notes",
        ]
        for field in sensitive_fields:
            if field in data:
                pytest.fail(
                    f"Sensitive field '{field}' exposed in retrieve response",
                )

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_retrieve_http_method_override(self, api_client, faker):
        """Misconfig: HTTP method override on retrieve."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File, name=faker.file_name(), mime=faker.mime_type(), owner=user,
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

        # Try to override GET with DELETE
        response = api_client.get(
            f"/api/v2/schedule/{schedule.id}",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )

        # Verify schedule still exists
        assert Schedule.objects.filter(
            id=schedule.id,
        ).exists(), "Method override allowed DELETE via GET"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_retrieve_id(self, api_client, faker):
        """Injection: SQLi in retrieve path ID."""
        sqli_payloads = [
            "1 OR 1=1",
            "1; DROP TABLE cc_schedule;--",
            "1 UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/schedule/{payload}")
            assert response.status_code in [
                400,
                404,
            ], f"SQLi '{payload}' caused {response.status_code}"

    def test_path_traversal_in_retrieve_id(self, api_client, faker):
        """Injection: Path traversal in retrieve ID."""
        traversal_ids = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2fetc%2fpasswd",
        ]

        for test_id in traversal_ids:
            response = api_client.get(f"/api/v2/schedule/{test_id}")
            assert response.status_code in [
                400,
                404,
            ], f"Path traversal '{test_id}' caused {response.status_code}"

    # ========================================================================
    # Input Validation
    # ========================================================================

    def test_unicode_in_retrieve_id(self, api_client, faker):
        """Validation: Unicode in retrieve ID."""
        response = api_client.get("/api/v2/schedule/日本語")
        assert response.status_code in [
            400,
            404,
        ], f"Unicode ID caused {response.status_code}"

    def test_negative_id_retrieve(self, api_client, faker):
        """Validation: Negative ID in retrieve."""
        response = api_client.get("/api/v2/schedule/-1")
        assert response.status_code == 404

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    @pytest.mark.xfail(
        reason="T591: Info Leak - Error reveals if schedule exists",
    )
    def test_error_message_leaks_existence_retrieve(self, api_client, faker):
        """Info Leak: Error messages reveal schedule existence."""
        victim = baker.make(
            User, username=f"testred_victim_{faker.user_name()}",
        )
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File, name=faker.file_name(), mime=faker.mime_type(), owner=victim,
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

        # Try to access existing vs non-existing
        response_existing = api_client.get(
            f"/api/v2/schedule/{victim_schedule.id}",
        )
        response_nonexistent = api_client.get("/api/v2/schedule/999999")

        if response_existing.status_code != response_nonexistent.status_code:
            pytest.fail(
                f"Status leak: existing={response_existing.status_code}, "
                f"nonexistent={response_nonexistent.status_code}",
            )

    def test_field_enumeration_via_response_retrieve(self, api_client, faker):
        """Info Leak: Check response field structure."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File, name=faker.file_name(), mime=faker.mime_type(), owner=user,
        )
        stream = baker.make(
            Webstream, name=faker.catch_phrase(), url=faker.url(), owner=user,
        )

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=None,
            stream=stream,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        response = api_client.get(f"/api/v2/schedule/{schedule.id}")
        data = response.json()

        # Verify expected fields
        expected_fields = [
            "id",
            "instance",
            "file",
            "stream",
            "starts_at",
            "ends_at",
            "cue_in",
            "cue_out",
            "position",
        ]
        for field in expected_fields:
            assert field in data, f"Expected field '{field}' not in response"
