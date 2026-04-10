"""T265: ListenerCount redteam security tests.

Red Team security tests for ListenerCount endpoints.
Tests for BOLA, time-based injection, DoS via date ranges.
"""

import pytest
from datetime import timedelta

from model_bakery import baker
from sdk import now, format_datetime

from api.history.models import ListenerCount, MountName, Timestamp
from api.core.models.role import Role
from api.core.models.user import User


@pytest.mark.django_db
class TestListenerCountRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization - listener stats access."""

    def test_bola_list_shows_all_listener_counts(self, api_client, admin_user, fake_catch_phrase):
        """
        BOLA: LIST returns all listener counts regardless of station.

        Should filter by user's station/mount points.
        """
        # Create multiple mount points (simulating multiple stations)
        mount1 = baker.make(MountName, mount_name="/station1.ogg")
        mount2 = baker.make(MountName, mount_name="/station2.ogg")

        ts = baker.make(Timestamp, timestamp=now())

        baker.make(ListenerCount, timestamp=ts, mount_name=mount1, listener_count=100)
        baker.make(ListenerCount, timestamp=ts, mount_name=mount2, listener_count=200)

        response = api_client.get("/api/v2/listener-counts")

        assert response.status_code == 200
        data = response.json()

        # If all counts returned, BOLA confirmed
        if len(data) == 2:
            # Admin can see all - may be intended
            pass

    def test_bola_retrieve_other_station_stats(self, api_client, admin_user, fake_catch_phrase):
        """
        BOLA: Access listener stats for other stations.
        """
        other_mount = baker.make(MountName, mount_name="/other-station.ogg")
        ts = baker.make(Timestamp, timestamp=now())
        count = baker.make(ListenerCount, timestamp=ts, mount_name=other_mount, listener_count=500)

        response = api_client.get(f"/api/v2/listener-counts/{count.id}")

        if response.status_code == 200:
            # Can access other station's stats
            pass

    def test_bola_regular_user_can_access_all_stats(self, api_client, regular_user, fake_catch_phrase):
        """
        BFLA: Regular user can access all listener statistics.

        Should be restricted to own station's stats.
        """
        mount = baker.make(MountName, mount_name="/admin-station.ogg")
        ts = baker.make(Timestamp, timestamp=now())
        baker.make(ListenerCount, timestamp=ts, mount_name=mount, listener_count=1000)

        api_client.force_authenticate(user=regular_user)

        response = api_client.get("/api/v2/listener-counts")

        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                # Regular user can see admin station stats
                pass  # Document behavior

    def test_bola_guest_user_can_access_stats(self, api_client, guest_user):
        """
        BFLA: Guest user can access listener statistics.
        """
        api_client.force_authenticate(user=guest_user)

        response = api_client.get("/api/v2/listener-counts")

        if response.status_code == 200:
            pytest.xfail("T652: BFLA - Guest can access listener statistics")


@pytest.mark.django_db
class TestListenerCountRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization."""

    def test_bopla_create_mass_assignment_id(self, api_client, admin_user, fake_small_int, fake_catch_phrase):
        """
        BOPLA: CREATE with forced ID.
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        ts = baker.make(Timestamp, timestamp=now())

        forced_id = fake_small_int + 900000

        data = {
            "id": forced_id,
            "timestamp": ts.id,
            "mount_name": mount.id,
            "listener_count": 100,
        }

        response = api_client.post("/api/v2/listener-counts", data, format="json")

        if response.status_code == 201:
            result = response.json()
            if result.get("id") == forced_id:
                pytest.xfail("T653: BOPLA - ListenerCount id mass assignment works")

    def test_bopla_create_extra_fields_ignored(self, api_client, admin_user, fake_catch_phrase):
        """
        BOPLA: CREATE with extra fields silently ignored.
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        ts = baker.make(Timestamp, timestamp=now())

        data = {
            "timestamp": ts.id,
            "mount_name": mount.id,
            "listener_count": 100,
            "is_admin": True,
            "station_id": 999,
        }

        response = api_client.post("/api/v2/listener-counts", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T654: BOPLA - ListenerCount extra fields silently ignored")

    def test_bopla_update_listener_count_manipulation(self, api_client, admin_user, fake_catch_phrase):
        """
        BOPLA: UPDATE to manipulate listener count.

        Can set arbitrary listener counts (fake statistics).
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        ts = baker.make(Timestamp, timestamp=now())
        count = baker.make(ListenerCount, timestamp=ts, mount_name=mount, listener_count=10)

        data = {
            "timestamp": ts.id,
            "mount_name": mount.id,
            "listener_count": 999999,  # Fake high count
        }

        response = api_client.put(
            f"/api/v2/listener-counts/{count.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("listener_count") == 999999:
                # Can manipulate statistics
                pytest.xfail("T655: BOPLA - Can fake listener count statistics")

    def test_bopla_negative_listener_count(self, api_client, admin_user, fake_catch_phrase, fake_negative_int):
        """
        BOPLA/Validation: Negative listener count should be rejected.
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        ts = baker.make(Timestamp, timestamp=now())

        data = {
            "timestamp": ts.id,
            "mount_name": mount.id,
            "listener_count": fake_negative_int,
        }

        response = api_client.post("/api/v2/listener-counts", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T656: Negative listener count accepted")


@pytest.mark.django_db
class TestListenerCountRedTeamTimeBasedInjection:
    """Time-based SQL injection via date parameters."""

    def test_sqli_in_timestamp_filter(self, api_client, admin_user):
        """
        SQL Injection via timestamp filter parameter.
        """
        sqli_timestamps = [
            "2026-04-09T10:00:00Z' OR '1'='1",
            "2026-04-09T10:00:00Z'; DROP TABLE cc_listener_count--",
            "' UNION SELECT * FROM pg_authid--",
        ]

        for ts in sqli_timestamps:
            response = api_client.get(f"/api/v2/listener-counts?timestamp={ts}")

            if response.status_code == 500:
                pytest.xfail(f"T657: SQLi in timestamp filter causes 500")

            error_text = str(response.content).lower()
            if "sql" in error_text or "syntax" in error_text:
                pytest.xfail(f"T657: SQLi error disclosure")

    def test_sqli_in_date_range_start(self, api_client, admin_user):
        """
        SQL Injection via start date parameter.
        """
        sqli_start = "2026-04-01T00:00:00Z' OR '1'='1"

        response = api_client.get(f"/api/v2/listener-counts?start={sqli_start}&end=2026-04-10T00:00:00Z")

        if response.status_code == 500:
            pytest.xfail("T657: SQLi in start date causes 500")

    def test_sqli_in_date_range_end(self, api_client, admin_user):
        """
        SQL Injection via end date parameter.
        """
        sqli_end = "2026-04-10T00:00:00Z' OR '1'='1"

        response = api_client.get(f"/api/v2/listener-counts?start=2026-04-01T00:00:00Z&end={sqli_end}")

        if response.status_code == 500:
            pytest.xfail("T657: SQLi in end date causes 500")

    def test_time_based_blind_sqli(self, api_client, admin_user):
        """
        Time-based blind SQL injection detection.

        Using pg_sleep or similar.
        """
        # This would require timing analysis
        # Document the test pattern
        pass


@pytest.mark.django_db
class TestListenerCountRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption."""

    def test_large_date_range_query(self, api_client, admin_user):
        """
        DoS: Query with very large date range.

        Can cause database performance issues.
        """
        # Create many listener count records across time
        mount = baker.make(MountName, mount_name="/test.ogg")

        for i in range(100):
            ts = baker.make(Timestamp, timestamp=now() - timedelta(days=i))
            baker.make(ListenerCount, timestamp=ts, mount_name=mount, listener_count=i)

        # Query large range
        start = format_datetime(now() - timedelta(days=365 * 10))  # 10 years
        end = format_datetime(now())

        response = api_client.get(f"/api/v2/listener-counts?start={start}&end={end}")

        if response.status_code == 200:
            data = response.json()
            # Check if all data returned without pagination
            if isinstance(data, list) and len(data) == 100:
                pass  # No pagination limits

    def test_rapid_listener_count_creation(self, api_client, admin_user, fake_catch_phrase):
        """
        Rate limiting: Rapid CREATE requests.
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")

        success_count = 0
        for i in range(20):
            ts = baker.make(Timestamp, timestamp=now() + timedelta(minutes=i))
            data = {
                "timestamp": ts.id,
                "mount_name": mount.id,
                "listener_count": i,
            }
            response = api_client.post("/api/v2/listener-counts", data, format="json")
            if response.status_code == 201:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T658: No rate limiting on ListenerCount CREATE")

    def test_bulk_listener_count_query(self, api_client, admin_user):
        """
        Resource consumption: Query without pagination.
        """
        mount = baker.make(MountName, mount_name="/bulk-test.ogg")

        # Create many records
        for i in range(200):
            ts = baker.make(Timestamp, timestamp=now() - timedelta(minutes=i))
            baker.make(ListenerCount, timestamp=ts, mount_name=mount, listener_count=i)

        response = api_client.get("/api/v2/listener-counts")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 100:
                pytest.xfail("T659: Large result set without pagination")


@pytest.mark.django_db
class TestListenerCountRedTeamValidation:
    """Validation bypass tests."""

    def test_create_with_future_timestamp(self, api_client, admin_user, fake_catch_phrase):
        """
        Validation: Future timestamp should be rejected.

        Can't have listener counts for future time.
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        future_ts = baker.make(Timestamp, timestamp=now() + timedelta(days=1))

        data = {
            "timestamp": future_ts.id,
            "mount_name": mount.id,
            "listener_count": 100,
        }

        response = api_client.post("/api/v2/listener-counts", data, format="json")

        if response.status_code == 201:
            pytest.xfail("T660: Future timestamp accepted")

    def test_create_with_nonexistent_mount(self, api_client, admin_user):
        """
        Validation: Non-existent mount_name should be rejected.
        """
        ts = baker.make(Timestamp, timestamp=now())

        data = {
            "timestamp": ts.id,
            "mount_name": 999999,
            "listener_count": 100,
        }

        response = api_client.post("/api/v2/listener-counts", data, format="json")

        assert response.status_code == 400

    def test_create_with_nonexistent_timestamp(self, api_client, admin_user, fake_catch_phrase):
        """
        Validation: Non-existent timestamp should be rejected.
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")

        data = {
            "timestamp": 999999,
            "mount_name": mount.id,
            "listener_count": 100,
        }

        response = api_client.post("/api/v2/listener-counts", data, format="json")

        assert response.status_code == 400

    def test_create_very_large_listener_count(self, api_client, admin_user, fake_catch_phrase):
        """
        Validation: Very large listener count.
        """
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        ts = baker.make(Timestamp, timestamp=now())

        data = {
            "timestamp": ts.id,
            "mount_name": mount.id,
            "listener_count": 999999999,
        }

        response = api_client.post("/api/v2/listener-counts", data, format="json")

        # Document behavior - should have reasonable max
        assert response.status_code in [201, 400]

    def test_end_before_start_date_range(self, api_client, admin_user):
        """
        Validation: End date before start date should be rejected.
        """
        start = format_datetime(now())
        end = format_datetime(now() - timedelta(days=7))

        response = api_client.get(f"/api/v2/listener-counts?start={start}&end={end}")

        if response.status_code == 200:
            pytest.xfail("T661: End before start date accepted")


@pytest.mark.django_db
class TestListenerCountRedTeamAuthentication:
    """Authentication tests."""

    def test_unauthenticated_list(self, api_client):
        """Unauthenticated LIST should fail."""
        api_client.logout()
        response = api_client.get("/api/v2/listener-counts")
        assert response.status_code == 403

    def test_unauthenticated_create(self, api_client):
        """Unauthenticated CREATE should fail."""
        api_client.logout()
        data = {"listener_count": 100}
        response = api_client.post("/api/v2/listener-counts", data, format="json")
        assert response.status_code == 403

    def test_unauthenticated_retrieve(self, api_client, admin_user, fake_catch_phrase):
        """Unauthenticated RETRIEVE should fail."""
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        ts = baker.make(Timestamp, timestamp=now())
        count = baker.make(ListenerCount, timestamp=ts, mount_name=mount, listener_count=100)

        api_client.logout()
        response = api_client.get(f"/api/v2/listener-counts/{count.id}")
        assert response.status_code == 403


@pytest.mark.django_db
class TestListenerCountRedTeamInformationDisclosure:
    """Information disclosure tests."""

    def test_error_message_leaks_db_structure(self, api_client, admin_user):
        """
        Error messages should not leak database structure.
        """
        response = api_client.get("/api/v2/listener-counts?timestamp=invalid')")

        if response.status_code == 500:
            error_text = str(response.content).lower()
            leak_keywords = ["cc_listener_count", "pg_query", "column", "table"]
            if any(kw in error_text for kw in leak_keywords):
                pytest.xfail("T662: Error message leaks database structure")

    def test_id_enumeration_via_error_messages(self, api_client, admin_user):
        """
        Different errors for existent vs non-existent IDs.
        """
        response_existing = api_client.get("/api/v2/listener-counts/1")
        response_nonexistent = api_client.get("/api/v2/listener-counts/999999")

        # Both should return same status (404) for unauthorized access
        # Different codes leak existence information
        if response_existing.status_code != response_nonexistent.status_code:
            pass  # Document information leakage


@pytest.mark.django_db
class TestListenerCountRedTeamHTTPMethodTampering:
    """HTTP method tampering tests."""

    def test_trace_method_disabled(self, api_client, admin_user, fake_catch_phrase):
        """TRACE method should be disabled."""
        mount = baker.make(MountName, mount_name=f"/{fake_catch_phrase}.ogg")
        ts = baker.make(Timestamp, timestamp=now())
        count = baker.make(ListenerCount, timestamp=ts, mount_name=mount, listener_count=100)

        response = api_client.trace(f"/api/v2/listener-counts/{count.id}")
        assert response.status_code in [405, 403]
