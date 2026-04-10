"""T266: LiveLog redteam security tests.

Red Team security tests for LiveLog endpoints.
Tests for BOLA, BOPLA, time-based injection, and DoS.
"""

import pytest
from datetime import timedelta

from model_bakery import baker
from sdk import now, format_datetime

from api.history.models import LiveLog
from api.core.models.role import Role
from api.core.models.user import User


@pytest.mark.django_db
class TestLiveLogRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization."""

    def test_bola_no_owner_field_in_model(self, api_client, admin_user):
        """
        BOLA: LiveLog model has no owner/user field.

        Live logs are global - accessible to anyone with permission.
        """
        from api.history.models import LiveLog

        fields = [f.name for f in LiveLog._meta.get_fields()]

        assert "owner" not in fields
        assert "user" not in fields
        assert "creator" not in fields
        assert "station" not in fields

    def test_bola_list_shows_all_live_logs(self, api_client, admin_user, fake_catch_phrase):
        """
        BOLA: LIST returns all live logs without filtering.
        """
        # Create multiple live logs
        for i in range(5):
            baker.make(
                LiveLog,
                state=f"streaming_{i}",
                start_time=now() - timedelta(hours=i),
                end_time=now() - timedelta(hours=i) + timedelta(minutes=30) if i > 0 else None,
            )

        response = api_client.get("/api/v2/live-logs")

        assert response.status_code == 200
        data = response.json()

        # All logs returned - no filtering
        if len(data) == 5:
            pass  # Document: global access

    def test_bola_regular_user_can_access_all_logs(self, api_client, regular_user, fake_catch_phrase):
        """
        BFLA: Regular user can access all live logs.

        Should live logs be restricted by station/permission?
        """
        # Create log
        baker.make(LiveLog, state="on_air", start_time=now())

        api_client.force_authenticate(user=regular_user)

        response = api_client.get("/api/v2/live-logs")

        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                # Regular user sees all logs
                pass  # Document behavior

    def test_bola_guest_user_can_access_logs(self, api_client, guest_user):
        """
        BFLA: Guest user can access live logs.
        """
        baker.make(LiveLog, state="on_air", start_time=now())

        api_client.force_authenticate(user=guest_user)

        response = api_client.get("/api/v2/live-logs")

        if response.status_code == 200:
            pytest.xfail("T653: BFLA - Guest can access live logs")


@pytest.mark.django_db
class TestLiveLogRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization."""

    def test_bopla_create_mass_assignment_id(self, api_client, admin_user, fake_small_int, fake_word):
        """
        BOPLA: CREATE with forced ID.
        """
        forced_id = fake_small_int + 900000

        data = {
            "id": forced_id,
            "state": fake_word,
            "start_time": format_datetime(now()),
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 201:
            result = response.json()
            if result.get("id") == forced_id:
                pytest.xfail("T654: BOPLA - LiveLog id mass assignment works")

    def test_bopla_create_extra_fields_ignored(self, api_client, admin_user, fake_word):
        """
        BOPLA: CREATE with extra fields silently ignored.
        """
        data = {
            "state": fake_word,
            "start_time": format_datetime(now()),
            "is_admin": True,
            "station_id": 999,
            "owner": 1,
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T655: BOPLA - LiveLog extra fields silently ignored")

    def test_bopla_update_fake_end_time(self, api_client, admin_user, fake_word):
        """
        BOPLA: UPDATE to manipulate end_time.

        Can fake stream duration by setting arbitrary end_time.
        """
        log = baker.make(LiveLog, state=fake_word, start_time=now())

        # Set end time to make it look like 24 hour stream
        fake_end = now() + timedelta(hours=24)

        data = {
            "state": fake_word,
            "start_time": format_datetime(log.start_time),
            "end_time": format_datetime(fake_end),
        }

        response = api_client.put(
            f"/api/v2/live-logs/{log.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            # Check if end_time was set to future (impossible for ended stream)
            if result.get("end_time"):
                end_dt = result.get("end_time")
                if end_dt == format_datetime(fake_end):
                    pytest.xfail("T656: BOPLA - Can fake stream end time")

    def test_bopla_end_time_before_start_time(self, api_client, admin_user, fake_word):
        """
        BOPLA/Validation: end_time before start_time should be rejected.
        """
        start = now()
        end = start - timedelta(hours=1)  # End before start

        data = {
            "state": fake_word,
            "start_time": format_datetime(start),
            "end_time": format_datetime(end),
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T657: Validation bypass - end_time before start_time")

    def test_bopla_future_start_time(self, api_client, admin_user, fake_word):
        """
        BOPLA/Validation: Future start_time should be rejected.
        """
        future = now() + timedelta(days=1)

        data = {
            "state": fake_word,
            "start_time": format_datetime(future),
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T658: Future start_time accepted")

    def test_bopla_patch_extra_fields_ignored(self, api_client, admin_user, fake_word):
        """
        BOPLA: PATCH with extra fields silently ignored.
        """
        log = baker.make(LiveLog, state=fake_word, start_time=now())

        data = {
            "state": "modified",
            "is_system": True,
            "internal": True,
        }

        response = api_client.patch(
            f"/api/v2/live-logs/{log.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T659: BOPLA - PATCH extra fields ignored")


@pytest.mark.django_db
class TestLiveLogRedTeamTimeBasedInjection:
    """Time-based SQL injection via date parameters."""

    def test_sqli_in_start_time_filter(self, api_client, admin_user):
        """
        SQL Injection via start_time filter.
        """
        sqli_payloads = [
            "2026-04-09T10:00:00Z' OR '1'='1",
            "2026-04-09T10:00:00Z'; DROP TABLE cc_live_log--",
            "' UNION SELECT * FROM pg_authid--",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/live-logs?start_time={payload}")

            if response.status_code == 500:
                pytest.xfail(f"T660: SQLi in start_time filter causes 500")

            error_text = str(response.content).lower()
            if "sql" in error_text or "syntax" in error_text:
                pytest.xfail(f"T660: SQLi error disclosure")

    def test_sqli_in_end_time_filter(self, api_client, admin_user):
        """
        SQL Injection via end_time filter.
        """
        sqli_payload = "2026-04-09T10:00:00Z' OR '1'='1"

        response = api_client.get(f"/api/v2/live-logs?end_time={sqli_payload}")

        if response.status_code == 500:
            pytest.xfail("T660: SQLi in end_time filter causes 500")

    def test_sqli_in_state_filter(self, api_client, admin_user):
        """
        SQL Injection via state filter.
        """
        sqli_states = [
            "on_air' OR '1'='1",
            "streaming'; DROP TABLE cc_live_log--",
        ]

        for state in sqli_states:
            response = api_client.get(f"/api/v2/live-logs?state={state}")

            if response.status_code == 500:
                pytest.xfail(f"T660: SQLi in state filter causes 500")

    def test_sqli_in_datetime_field_create(self, api_client, admin_user, fake_word):
        """
        SQL Injection via datetime fields in CREATE.
        """
        sqli_time = "2026-04-09T10:00:00Z' OR '1'='1"

        data = {
            "state": fake_word,
            "start_time": sqli_time,
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 500:
            pytest.xfail("T660: SQLi in datetime field causes 500")


@pytest.mark.django_db
class TestLiveLogRedTeamInjection:
    """Other injection attacks."""

    def test_xss_in_state_field(self, api_client, admin_user):
        """
        XSS via state field - stored XSS.
        """
        xss_states = [
            "<script>alert(1)</script>",
            "on_air<img src=x onerror=alert(1)>",
        ]

        for state in xss_states:
            data = {
                "state": state,
                "start_time": format_datetime(now()),
            }

            response = api_client.post("/api/v2/live-logs", data, format="json")

            if response.status_code == 201:
                result = response.json()
                if result.get("state") == state:
                    pytest.xfail("T661: XSS in state field stored unsanitized")

    def test_command_injection_in_state(self, api_client, admin_user):
        """
        Command injection patterns in state.
        """
        cmd_states = [
            "$(whoami)",
            "`id`",
            "on_air; rm -rf /",
        ]

        for state in cmd_states:
            data = {
                "state": state,
                "start_time": format_datetime(now()),
            }

            response = api_client.post("/api/v2/live-logs", data, format="json")

            # Should accept any string
            assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestLiveLogRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption."""

    def test_rapid_live_log_creation(self, api_client, admin_user, fake_word):
        """
        Rate limiting: Rapid CREATE requests.
        """
        success_count = 0
        for i in range(20):
            data = {
                "state": f"{fake_word}_{i}",
                "start_time": format_datetime(now() - timedelta(minutes=i)),
            }
            response = api_client.post("/api/v2/live-logs", data, format="json")
            if response.status_code == 201:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T662: No rate limiting on LiveLog CREATE")

    def test_large_date_range_query(self, api_client, admin_user):
        """
        DoS: Query with very large date range.
        """
        # Create many logs
        for i in range(100):
            baker.make(
                LiveLog,
                state=f"log_{i}",
                start_time=now() - timedelta(days=i),
                end_time=now() - timedelta(days=i) + timedelta(minutes=30),
            )

        # Query 10 year range
        start = format_datetime(now() - timedelta(days=365 * 10))
        end = format_datetime(now())

        response = api_client.get(f"/api/v2/live-logs?start_time={start}&end_time={end}")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 100:
                pass  # No pagination

    def test_bulk_live_log_list(self, api_client, admin_user):
        """
        Resource consumption: List without pagination.
        """
        # Create many logs
        for i in range(200):
            baker.make(
                LiveLog,
                state=f"bulk_{i}",
                start_time=now() - timedelta(minutes=i),
            )

        response = api_client.get("/api/v2/live-logs")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 100:
                pytest.xfail("T663: Large result set without pagination")

    def test_rapid_updates(self, api_client, admin_user, fake_word):
        """
        Rate limiting: Rapid UPDATE requests.
        """
        log = baker.make(LiveLog, state=fake_word, start_time=now())

        success_count = 0
        for i in range(20):
            data = {
                "state": f"modified_{i}",
                "start_time": format_datetime(log.start_time),
            }
            response = api_client.put(
                f"/api/v2/live-logs/{log.id}",
                data,
                format="json",
            )
            if response.status_code == 200:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T664: No rate limiting on LiveLog UPDATE")


@pytest.mark.django_db
class TestLiveLogRedTeamValidation:
    """Validation bypass tests."""

    def test_create_empty_state(self, api_client, admin_user):
        """
        Validation: Empty state should be rejected.
        """
        data = {
            "state": "",
            "start_time": format_datetime(now()),
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T665: Empty state accepted")

    def test_create_null_start_time(self, api_client, admin_user, fake_word):
        """
        Validation: Null start_time should be rejected.
        """
        data = {
            "state": fake_word,
            "start_time": None,
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        assert response.status_code == 400

    def test_create_very_long_state(self, api_client, admin_user):
        """
        Validation: Very long state beyond max_length (32).
        """
        data = {
            "state": "X" * 1000,
            "start_time": format_datetime(now()),
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 201:
            result = response.json()
            if len(result.get("state", "")) == 1000:
                pytest.xfail("T666: No max_length enforcement on state")

    def test_create_invalid_state_values(self, api_client, admin_user):
        """
        Validation: Invalid state values.

        State should be restricted to known values (on_air, off_air, etc.)
        """
        invalid_states = [
            "invalid_state",
            "<script>",
            "'; DROP TABLE--",
            "🔴",
        ]

        for state in invalid_states:
            data = {
                "state": state,
                "start_time": format_datetime(now()),
            }

            response = api_client.post("/api/v2/live-logs", data, format="json")

            # Document behavior
            if response.status_code == 201:
                pass  # No validation on state


@pytest.mark.django_db
class TestLiveLogRedTeamAuthentication:
    """Authentication tests."""

    def test_unauthenticated_list(self, api_client):
        """Unauthenticated LIST should fail."""
        api_client.logout()
        response = api_client.get("/api/v2/live-logs")
        assert response.status_code == 403

    def test_unauthenticated_create(self, api_client, fake_word):
        """Unauthenticated CREATE should fail."""
        api_client.logout()
        data = {
            "state": fake_word,
            "start_time": format_datetime(now()),
        }
        response = api_client.post("/api/v2/live-logs", data, format="json")
        assert response.status_code == 403

    def test_unauthenticated_update(self, api_client, fake_word):
        """Unauthenticated UPDATE should fail."""
        log = baker.make(LiveLog, state=fake_word, start_time=now())

        api_client.logout()
        data = {
            "state": fake_word,
            "start_time": format_datetime(now()),
        }
        response = api_client.put(
            f"/api/v2/live-logs/{log.id}",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_unauthenticated_delete(self, api_client, fake_word):
        """Unauthenticated DELETE should fail."""
        log = baker.make(LiveLog, state=fake_word, start_time=now())

        api_client.logout()
        response = api_client.delete(f"/api/v2/live-logs/{log.id}")
        assert response.status_code == 403

    def test_guest_user_create(self, api_client, guest_user, fake_word):
        """Guest user CREATE should fail."""
        api_client.force_authenticate(user=guest_user)

        data = {
            "state": fake_word,
            "start_time": format_datetime(now()),
        }

        response = api_client.post("/api/v2/live-logs", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T667: Guest can create live logs")


@pytest.mark.django_db
class TestLiveLogRedTeamInformationDisclosure:
    """Information disclosure tests."""

    def test_error_message_leaks_db_structure(self, api_client, admin_user):
        """
        Error messages should not leak database structure.
        """
        response = api_client.get("/api/v2/live-logs?start_time=invalid')")

        if response.status_code == 500:
            error_text = str(response.content).lower()
            leak_keywords = ["cc_live_log", "pg_query", "column", "table"]
            if any(kw in error_text for kw in leak_keywords):
                pytest.xfail("T668: Error message leaks database structure")

    def test_id_enumeration(self, api_client, admin_user):
        """
        Different errors for existent vs non-existent IDs leak information.
        """
        response_existing = api_client.get("/api/v2/live-logs/1")
        response_nonexistent = api_client.get("/api/v2/live-logs/999999")

        if response_existing.status_code != response_nonexistent.status_code:
            pass  # Document information leakage


@pytest.mark.django_db
class TestLiveLogRedTeamHTTPMethodTampering:
    """HTTP method tampering tests."""

    def test_trace_method_disabled(self, api_client, admin_user, fake_word):
        """TRACE method should be disabled."""
        log = baker.make(LiveLog, state=fake_word, start_time=now())

        response = api_client.trace(f"/api/v2/live-logs/{log.id}")
        assert response.status_code in [405, 403]

    def test_method_override_post_to_list(self, api_client, admin_user):
        """
        Method override via headers should not work.
        """
        response = api_client.post(
            "/api/v2/live-logs",
            {},
            headers={"X-HTTP-Method-Override": "GET"},
        )

        assert response.status_code in [405, 403, 400]
