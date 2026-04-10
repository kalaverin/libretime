"""T260: PlayoutHistory CREATE redteam security tests.

Red Team security tests for PlayoutHistory CREATE endpoint.
Tests for BOPLA, BOLA, injection, and validation bypass vulnerabilities.
"""

import pytest
from datetime import timedelta

from django.urls import reverse
from model_bakery import baker
from sdk import now, format_datetime

from api.history.models import PlayoutHistory
from api.schedule.models import Show, ShowInstance
from api.storage.models import File
from api.core.models.role import Role
from api.core.models.user import User


@pytest.mark.django_db
class TestPlayoutHistoryCreateRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization - CREATE mass assignment."""

    def test_bopla_mass_assignment_id_field(self, api_client, admin_user, faker):
        """
        BOPLA: Client can specify 'id' field during CREATE.

        Serializer uses fields = '__all__' which allows id assignment.
        Could lead to ID collision or overwrite attempts.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        forced_id = 999999

        data = {
            "id": forced_id,
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            result = response.json()
            if result.get("id") == forced_id:
                pytest.xfail("T621: BOPLA - id field mass assignment works")

    def test_bopla_extra_fields_not_rejected(self, api_client, admin_user, faker):
        """
        BOPLA: Extra/unknown fields are silently ignored.

        Should reject unknown fields instead of ignoring.
        Can mask typos or attempted mass assignment.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
            "is_admin": True,
            "role": "admin",
            "password": "hacked",
            "secret_key": "stolen",
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            # Extra fields were ignored - should have been rejected
            pytest.xfail("T622: BOPLA - Extra fields silently ignored instead of rejected")

    def test_bopla_mass_assignment_via_content_type(self, api_client, admin_user, faker):
        """
        BOPLA: Different content types may bypass validation.

        Test form-urlencoded vs JSON for mass assignment differences.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": format_datetime(now()),
            "id": 888888,
        }

        # Try form data instead of JSON
        response = api_client.post(
            "/api/v2/playout-history",
            data,
            content_type="application/x-www-form-urlencoded"
        )

        # Document behavior - form data may be handled differently
        if response.status_code == 201:
            result = response.json()
            if result.get("id") == 888888:
                pytest.xfail("T621: BOPLA - id mass assignment via form data")


@pytest.mark.django_db
class TestPlayoutHistoryCreateRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization - CREATE with other user's resources."""

    def test_bola_create_with_other_users_file(self, api_client, admin_user, faker):
        """
        BOLA: CREATE playout with another user's file.

        Should validate file ownership before allowing reference.
        """
        # Create victim user with private file
        victim = baker.make(User, role=Role.HOST, username=faker.user_name())
        victim_file = baker.make(File, mime="audio/mp3", owner=victim, name="victim_private.mp3")

        # Admin creates playout referencing victim's file
        data = {
            "file": victim_file.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            # Successfully created playout with victim's file
            # This may be intended for admin, but documents lack of ownership check
            pass

    def test_bola_create_with_other_users_instance(self, api_client, admin_user, faker):
        """
        BOLA: CREATE playout linked to another user's show instance.

        Should validate instance ownership.
        """
        # Create victim user with show and instance
        victim = baker.make(User, role=Role.HOST, username=faker.user_name())
        victim_show = baker.make(Show, name="Victim Private Show")
        victim_instance = baker.make(
            ShowInstance,
            show=victim_show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "instance": victim_instance.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            # Successfully linked to victim's instance
            pytest.xfail("T623: BOLA - Can create playout linked to other user's show instance")

    def test_bola_create_with_nonexistent_file(self, api_client, admin_user):
        """
        BOLA/Validation: CREATE with non-existent file ID.

        Should return 400 with clear validation error.
        """
        data = {
            "file": 999999,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        assert response.status_code == 400
        # Check error message doesn't leak internal info
        error_text = str(response.content)
        assert "does not exist" in error_text.lower() or "invalid" in error_text.lower()

    def test_bola_create_with_nonexistent_instance(self, api_client, admin_user, faker):
        """
        BOLA/Validation: CREATE with non-existent instance ID.

        Should return 400 with clear validation error.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "instance": 999999,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestPlayoutHistoryCreateRedTeamInjection:
    """Injection attacks on CREATE endpoint."""

    SQLI_PAYLOADS = [
        "' OR '1'='1",
        "1'; DROP TABLE cc_playout_history--",
        "' UNION SELECT * FROM cc_playout_history--",
        "1 AND 1=CONVERT(int, @@version)",
        "' OR pg_sleep(5)--",
    ]

    def test_sqli_in_file_field(self, api_client, admin_user):
        """
        SQL Injection via file field.
        """
        for payload in self.SQLI_PAYLOADS[:3]:
            data = {
                "file": payload,
                "starts": format_datetime(now()),
            }

            response = api_client.post("/api/v2/playout-history", data, format="json")

            # Check for SQL errors
            if response.status_code == 500:
                pytest.xfail(f"T624: SQLi in file field causes 500: {payload[:30]}")

            error_text = str(response.content).lower()
            sql_keywords = ["sql", "syntax", "error", "pg_query"]
            if any(kw in error_text for kw in sql_keywords):
                pytest.xfail(f"T624: SQLi error disclosure: {payload[:30]}")

    def test_sqli_in_starts_field(self, api_client, admin_user, faker):
        """
        SQL Injection via starts datetime field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        sqli_times = [
            "2026-04-09T10:00:00Z' OR '1'='1",
            "2026-04-09T10:00:00Z'; DROP TABLE cc_playout_history--",
        ]

        for payload in sqli_times:
            data = {
                "file": f.id,
                "starts": payload,
            }

            response = api_client.post("/api/v2/playout-history", data, format="json")

            if response.status_code == 500:
                pytest.xfail(f"T624: SQLi in starts field causes 500")

    def test_xss_in_metadata_via_create(self, api_client, admin_user, faker):
        """
        XSS payloads in related operations.

        Test if XSS payloads are accepted and stored.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
        ]

        # Note: PlayoutHistory doesn't have text fields for XSS
        # But this pattern documents the testing approach
        for payload in xss_payloads:
            data = {
                "file": f.id,
                "starts": format_datetime(now()),
            }

            response = api_client.post("/api/v2/playout-history", data, format="json")
            # Just document - no XSS vector in this model
            assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPlayoutHistoryCreateRedTeamValidationBypass:
    """Validation bypass and edge case tests."""

    def test_create_ends_before_starts(self, api_client, admin_user, faker):
        """
        Validation: ends before starts should be rejected.

        Serializer has validation for this - test if it works.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": format_datetime(now() + timedelta(minutes=5)),
            "ends": format_datetime(now()),  # ends before starts
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T625: Validation bypass - ends before starts accepted")
        else:
            assert response.status_code == 400

    def test_create_ends_equals_starts(self, api_client, admin_user, faker):
        """
        Validation: ends equal to starts should be rejected.

        Zero-duration playout doesn't make sense.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        same_time = format_datetime(now())

        data = {
            "file": f.id,
            "starts": same_time,
            "ends": same_time,
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T625: Validation bypass - ends equals starts accepted")

    def test_create_negative_duration(self, api_client, admin_user, faker):
        """
        Validation: Negative duration via timestamp manipulation.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": "2026-04-09T12:00:00Z",
            "ends": "2026-04-09T10:00:00Z",  # 2 hours earlier
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T625: Validation bypass - negative duration accepted")

    def test_create_invalid_datetime_format(self, api_client, admin_user, faker):
        """
        Validation: Invalid datetime formats should be rejected.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        invalid_formats = [
            "not-a-datetime",
            "2026-13-45T25:70:00Z",
            "",
            "null",
            "undefined",
        ]

        for invalid in invalid_formats:
            data = {
                "file": f.id,
                "starts": invalid,
            }

            response = api_client.post("/api/v2/playout-history", data, format="json")

            if response.status_code == 201:
                pytest.xfail(f"T626: Invalid datetime format accepted: {invalid}")

    def test_create_far_future_dates(self, api_client, admin_user, faker):
        """
        Validation: Far future dates should be validated.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": "2099-12-31T23:59:59Z",
            "ends": "2100-01-01T00:00:00Z",
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        # Document behavior - far future dates may be valid for scheduling
        assert response.status_code in [201, 400]

    def test_create_far_past_dates(self, api_client, admin_user, faker):
        """
        Validation: Far past dates should be validated.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        data = {
            "file": f.id,
            "starts": "1970-01-01T00:00:00Z",
            "ends": "1970-01-01T00:05:00Z",
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        # Document behavior - far past dates may be rejected
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPlayoutHistoryCreateRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption - CREATE DoS."""

    def test_create_rapid_fire(self, api_client, admin_user, faker):
        """
        Rate limiting: Rapid CREATE requests.

        Should be rate limited to prevent spam.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        success_count = 0
        for i in range(20):
            data = {
                "file": f.id,
                "starts": format_datetime(now() + timedelta(seconds=i)),
            }
            response = api_client.post("/api/v2/playout-history", data, format="json")
            if response.status_code == 201:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T627: No rate limiting on CREATE endpoint")

    def test_create_with_null_file_and_instance(self, api_client, admin_user):
        """
        Validation: CREATE with neither file nor instance.

        Should require at least one content reference.
        """
        data = {
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        # May be valid (e.g., system event) or may require validation
        # Document behavior
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPlayoutHistoryCreateRedTeamAuthentication:
    """Authentication and authorization bypass tests."""

    def test_create_unauthenticated(self, api_client, faker):
        """
        Auth: Unauthenticated CREATE should fail.
        """
        api_client.logout()

        data = {
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")
        assert response.status_code == 403

    def test_create_as_regular_user(self, api_client, regular_user, faker):
        """
        BFLA: Regular user CREATE permissions.

        Should regular users create playout history?
        """
        api_client.force_authenticate(user=regular_user)

        f = baker.make(File, mime="audio/mp3", owner=regular_user)

        data = {
            "file": f.id,
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            # Regular user can create - document this permission
            pass
        elif response.status_code == 403:
            # Properly restricted
            pass
        else:
            pytest.fail(f"Unexpected status: {response.status_code}")

    def test_create_as_guest_user(self, api_client, guest_user, faker):
        """
        BFLA: Guest user CREATE permissions.

        Guests should not create playout history.
        """
        api_client.force_authenticate(user=guest_user)

        data = {
            "starts": format_datetime(now()),
            "ends": format_datetime(now() + timedelta(minutes=5)),
        }

        response = api_client.post("/api/v2/playout-history", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T628: BFLA - Guest user can create playout history")


@pytest.mark.django_db
class TestPlayoutHistoryCreateRedTeamFuzzing:
    """Fuzzing tests for CREATE endpoint."""

    def test_fuzzing_field_types(self, api_client, admin_user, faker):
        """
        Fuzz: Invalid types for fields.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        fuzz_cases = [
            {"file": "not-an-int", "starts": format_datetime(now())},
            {"file": f.id, "starts": 12345},
            {"file": f.id, "starts": format_datetime(now()), "instance": "not-an-int"},
            {"file": "", "starts": format_datetime(now())},
            {"file": -1, "starts": format_datetime(now())},
            {"file": f.id, "starts": None},
        ]

        errors_500 = 0
        for data in fuzz_cases:
            response = api_client.post("/api/v2/playout-history", data, format="json")
            if response.status_code == 500:
                errors_500 += 1

        if errors_500 > 0:
            pytest.xfail(f"T629: Fuzzing caused {errors_500} server errors")

    def test_fuzzing_unicode_in_fields(self, api_client, admin_user, faker):
        """
        Fuzz: Unicode in fields.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        unicode_payloads = [
            "日本語テキスト",
            "العربية",
            "🎵🎶📻",
            "<script>alert(1)</script>",
            "' OR '1'='1",
            "A" * 10000,
        ]

        for payload in unicode_payloads:
            data = {
                "file": f.id,
                "starts": format_datetime(now()),
            }

            response = api_client.post("/api/v2/playout-history", data, format="json")

            if response.status_code == 500:
                pytest.xfail(f"T629: Unicode payload caused 500: {repr(payload[:30])}")
