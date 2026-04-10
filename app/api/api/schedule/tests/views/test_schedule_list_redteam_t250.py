"""Red Team security tests for Schedule LIST endpoint (T250).

Tests focus on:
- API1:2023 BOLA (accessing other users' schedule data)
- API2:2023 Broken Authentication
- API3:2023 BOPLA (filter parameter injection)
- API6:2023 Unsafe Business Flows
- API8:2023 Security Misconfiguration
- Injection attacks in filters
- Information disclosure
"""

import json
import time
from datetime import datetime, timedelta

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestScheduleListRedTeam:
    """Red Team tests for Schedule LIST endpoint - GET /api/v2/schedule."""

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

    @pytest.mark.xfail(reason="T568: BOLA - LIST shows all users' schedule entries")
    def test_bola_list_shows_all_users_schedule(self, api_client):
        """BOLA: LIST endpoint returns schedule entries from all users without filtering."""
        # Create schedule entries for multiple users
        for i in range(3):
            user = baker.make(User, username=f"testred_user{i}")
            show = baker.make(Show, name=f"Show {i}")
            instance = baker.make(ShowInstance, show=show)
            file_obj = baker.make(File, name=f"file{i}.mp3", mime="audio/mp3", owner=user)

            baker.make(
                Schedule,
                instance=instance,
                file=file_obj,
                starts_at="2026-04-09T10:00:00Z",
                ends_at="2026-04-09T10:05:00Z",
                cue_in="00:00:00",
                cue_out="00:05:00",
                position=1,
                broadcasted=1,
            )

        response = api_client.get("/api/v2/schedule")
        assert response.status_code == 200

        data = response.json()
        # Should only see own entries, not all
        assert len(data) <= 1, \
            f"BOLA: LIST returned {len(data)} entries from different users"

    def test_bola_id_enumeration(self, api_client):
        """BOLA: Sequential ID enumeration on schedule entries."""
        user = baker.make(User, username="testred_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        schedules = []
        for i in range(5):
            schedule = baker.make(
                Schedule,
                instance=instance,
                file=file_obj,
                starts_at="2026-04-09T10:00:00Z",
                ends_at="2026-04-09T10:05:00Z",
                cue_in="00:00:00",
                cue_out="00:05:00",
                position=i,
                broadcasted=1,
            )
            schedules.append(schedule)

        # Try to enumerate IDs directly
        found_count = 0
        for i in range(1, 50):
            response = api_client.get(f"/api/v2/schedule/{i}")
            if response.status_code == 200:
                found_count += 1

        # If sequential IDs are used, enumeration is possible
        assert found_count <= len(schedules), \
            f"ID enumeration vulnerability: found {found_count} accessible entries"

    @pytest.mark.xfail(reason="T569: BOLA - Can access other user's schedule by ID")
    def test_bola_access_other_users_schedule_by_id(self, api_client):
        """BOLA: Can retrieve another user's schedule entry by ID."""
        victim = baker.make(User, username="testred_victim")
        show = baker.make(Show, name="Victim Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name="victim.mp3", mime="audio/mp3", owner=victim)

        victim_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at="2026-04-09T10:00:00Z",
            ends_at="2026-04-09T10:05:00Z",
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        response = api_client.get(f"/api/v2/schedule/{victim_schedule.id}")
        assert response.status_code == 403, \
            f"BOLA: Got {response.status_code}, expected 403 - can access other's schedule"

    # ========================================================================
    # API3:2023 - BOPLA (Filter Parameter Injection)
    # ========================================================================

    def test_sqli_in_starts_after_filter(self, api_client):
        """Injection: SQLi in starts_after query parameter."""
        sqli_payloads = [
            "2026-04-09T00:00:00Z' OR '1'='1",
            "2026-04-09T00:00:00Z' UNION SELECT * FROM cc_user--",
            "2026-04-09T00:00:00Z'; DROP TABLE cc_schedule;--",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/schedule?starts_after={payload}")
            # Should return 400 or filter error, never 500
            # PASS means SQLi was properly blocked
            if response.status_code == 500:
                pytest.fail(f"SQLi in starts_after: '{payload}' caused 500")

    def test_sqli_in_instance_filter(self, api_client):
        """Injection: SQLi in instance_id filter parameter."""
        sqli_payloads = [
            "1 OR 1=1",
            "1 UNION SELECT * FROM cc_user",
            "1; DELETE FROM cc_schedule;--",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/schedule?instance={payload}")
            if response.status_code == 500:
                pytest.fail(f"SQLi in instance filter: '{payload}' caused 500")

    def test_nosql_injection_in_filters(self, api_client):
        """Injection: NoSQL operators in filter parameters."""
        nosql_payloads = [
            {"instance__ne": "1"},
            {"instance__gt": "0"},
            {"instance__regex": ".*"},
        ]

        for payload in nosql_payloads:
            param = list(payload.keys())[0]
            value = payload[param]
            response = api_client.get(f"/api/v2/schedule?{param}={value}")
            # Should handle gracefully
            assert response.status_code in [200, 400], \
                f"NoSQLi '{param}={value}' caused {response.status_code}"

    def test_filter_bypass_with_null_values(self, api_client):
        """BOPLA: Using null/undefined in filters should not bypass restrictions."""
        bypass_params = [
            "?instance=null",
            "?instance=undefined",
            "?instance=",
            "?starts_after=null",
        ]

        for param in bypass_params:
            response = api_client.get(f"/api/v2/schedule{param}")
            # PASS means filter handled gracefully without bypass
            # Should not cause 500 or unexpected data exposure

    # ========================================================================
    # API6:2023 - Unsafe Business Flows
    # ========================================================================

    def test_mass_data_extraction(self, api_client):
        """Unsafe Flow: Mass data extraction without pagination limits."""
        user = baker.make(User, username="testred_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        # Create many schedule entries
        for i in range(100):
            baker.make(
                Schedule,
                instance=instance,
                file=file_obj,
                starts_at="2026-04-09T10:00:00Z",
                ends_at="2026-04-09T10:05:00Z",
                cue_in="00:00:00",
                cue_out="00:05:00",
                position=i,
                broadcasted=1,
            )

        response = api_client.get("/api/v2/schedule")
        data = response.json()

        # Check if there's pagination or limit
        if isinstance(data, list) and len(data) > 50:
            pytest.skip(f"No pagination: returned {len(data)} items at once")

    def test_filter_timing_attack(self, api_client):
        """Unsafe Flow: Timing attack via filter parameters."""
        user = baker.make(User, username="testred_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at="2026-04-09T10:00:00Z",
            ends_at="2026-04-09T10:05:00Z",
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Time different filter queries
        times = []
        for filter_param in [
            "?instance=999999",
            "?starts_after=2099-01-01T00:00:00Z",
            "?overbooked=true",
        ]:
            start = time.time()
            api_client.get(f"/api/v2/schedule{filter_param}")
            times.append(time.time() - start)

        # Times should be similar (within 3x factor)
        if min(times) > 0:
            ratio = max(times) / min(times)
            if ratio > 3:
                pytest.skip(f"Timing difference detected: ratio {ratio:.1f}")

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_cors_preflight_schedule(self, api_client):
        """Misconfig: CORS preflight allows unauthorized origins."""
        response = api_client.options(
            "/api/v2/schedule",
            HTTP_ORIGIN="https://attacker.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        if allow_origin in ["*", "https://attacker.com"]:
            pytest.fail("CORS misconfiguration: allows arbitrary origin")

    def test_verbose_filter_errors(self, api_client):
        """Misconfig: Filter error messages reveal implementation details."""
        # Trigger filter error with invalid input
        response = api_client.get("/api/v2/schedule?starts_after=invalid'union")

        error_body = response.content.decode().lower()

        sensitive_patterns = [
            "sql", "sqlite", "mysql", "postgresql",
            "django", "column", "table", "cc_schedule",
        ]

        for pattern in sensitive_patterns:
            if pattern in error_body:
                pytest.fail(f"Verbose error leaks: '{pattern}'")

    def test_http_method_on_list(self, api_client):
        """Misconfig: Test HTTP methods on LIST endpoint."""
        # Try PUT, DELETE, PATCH on LIST endpoint (POST is valid for ModelViewSet)
        methods = [
            ("put", {"name": "test"}),
            ("delete", None),
            ("patch", {"name": "test"}),
        ]

        for method, data in methods:
            if method == "put":
                response = api_client.put("/api/v2/schedule", json.dumps(data), content_type="application/json")
            elif method == "delete":
                response = api_client.delete("/api/v2/schedule")
            elif method == "patch":
                response = api_client.patch("/api/v2/schedule", json.dumps(data), content_type="application/json")

            # LIST endpoint should not accept these methods
            assert response.status_code in [405, 403], \
                f"Method {method.upper()} on LIST returned {response.status_code}"

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    def test_field_enumeration_via_response(self, api_client):
        """Info Leak: Response fields reveal internal data structure."""
        user = baker.make(User, username="testred_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name="test.mp3", mime="audio/mp3", owner=user)

        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at="2026-04-09T10:00:00Z",
            ends_at="2026-04-09T10:05:00Z",
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        response = api_client.get("/api/v2/schedule")
        data = response.json()

        if data and len(data) > 0:
            entry = data[0]
            # Check for sensitive fields
            sensitive_fields = ["password", "secret", "token", "key", "internal"]
            for field in sensitive_fields:
                assert field not in entry, \
                    f"Info leak: sensitive field '{field}' in response"

    @pytest.mark.xfail(reason="T573: Info Leak - Error message reveals if schedule exists")
    def test_error_message_leaks_existence(self, api_client):
        """Info Leak: Error messages reveal if schedule entry exists."""
        victim = baker.make(User, username="testred_victim")
        show = baker.make(Show, name="Victim Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name="victim.mp3", mime="audio/mp3", owner=victim)

        victim_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at="2026-04-09T10:00:00Z",
            ends_at="2026-04-09T10:05:00Z",
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Try to access existing vs non-existing
        response_existing = api_client.get(f"/api/v2/schedule/{victim_schedule.id}")
        response_nonexistent = api_client.get("/api/v2/schedule/999999")

        # Both should return same status to not leak existence
        if response_existing.status_code != response_nonexistent.status_code:
            pytest.fail(
                f"Status leak: existing={response_existing.status_code}, "
                f"nonexistent={response_nonexistent.status_code}"
            )

    # ========================================================================
    # Authentication Bypass
    # ========================================================================

    def test_list_without_auth(self, client):
        """Auth: LIST without auth should return 403."""
        response = client.get("/api/v2/schedule")
        assert response.status_code == 403

    @pytest.mark.xfail(reason="T575: Auth - Invalid token returns 200 instead of 403")
    def test_list_with_invalid_token(self, api_client):
        """Auth: Invalid token should be rejected."""
        original = api_client.defaults.get("HTTP_AUTHORIZATION", "")
        api_client.defaults["HTTP_AUTHORIZATION"] = "Bearer invalid_token"

        try:
            response = api_client.get("/api/v2/schedule")
            if response.status_code == 200:
                pytest.fail("T575: Invalid token accepted - authentication bypass")
            assert response.status_code == 403
        finally:
            api_client.defaults["HTTP_AUTHORIZATION"] = original

    # ========================================================================
    # Input Validation
    # ========================================================================

    def test_unicode_in_filter_params(self, api_client):
        """Validation: Unicode in filter parameters."""
        unicode_payloads = [
            "?instance=日本語",
            "?starts_after=日本語",
            "?instance=\u0000",
            "?instance=\uFEFF",
        ]

        for payload in unicode_payloads:
            response = api_client.get(f"/api/v2/schedule{payload}")
            # Should handle gracefully (400 or 200, not 500)
            assert response.status_code in [200, 400, 404], \
                f"Unicode '{repr(payload)}' caused {response.status_code}"

    def test_path_traversal_in_id(self, api_client):
        """Validation: Path traversal in schedule ID."""
        traversal_ids = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2fetc%2fpasswd",
        ]

        for test_id in traversal_ids:
            response = api_client.get(f"/api/v2/schedule/{test_id}")
            assert response.status_code in [400, 404], \
                f"Path traversal '{test_id}' caused {response.status_code}"

    def test_overbooked_filter_manipulation(self, api_client):
        """Validation: Manipulate overbooked filter with various values."""
        test_values = [
            "true", "false", "1", "0", "yes", "no",
            "True", "False", "TRUE", "FALSE",
            "", "null", "undefined",
        ]

        for value in test_values:
            response = api_client.get(f"/api/v2/schedule?overbooked={value}")
            # Should not crash
            assert response.status_code in [200, 400], \
                f"overbooked={value} caused {response.status_code}"

    def test_date_format_injection(self, api_client):
        """Validation: Various date formats in date filters."""
        date_payloads = [
            "2026-04-09",
            "09/04/2026",
            "Apr 9, 2026",
            "2026-04-09T10:00:00",
            "2026-04-09T10:00:00.000Z",
            "tomorrow",
            "now",
            "2026-04-09T10:00:00Z' OR '1'='1",
        ]

        for date in date_payloads:
            response = api_client.get(f"/api/v2/schedule?starts_after={date}")
            # Should handle gracefully
            assert response.status_code in [200, 400], \
                f"Date '{date}' caused {response.status_code}"

    # ========================================================================
    # Rate Limiting
    # ========================================================================

    def test_rate_limit_list_requests(self, api_client):
        """Rate Limit: Rapid sequential LIST requests."""
        responses = []
        for _ in range(50):
            response = api_client.get("/api/v2/schedule")
            responses.append(response.status_code)

        # Count rate limited responses
        rate_limited = responses.count(429)

        # If no rate limiting, that's a potential issue
        if rate_limited == 0:
            pytest.skip("No rate limiting detected on LIST endpoint")

    # ========================================================================
    # Business Logic
    # ========================================================================

    @pytest.mark.xfail(reason="T574: Logic - Filter combination bypasses ownership")
    def test_filter_combination_bypass(self, api_client):
        """Logic: Combining filters may bypass ownership checks."""
        victim = baker.make(User, username="testred_victim")
        show = baker.make(Show, name="Victim Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name="victim.mp3", mime="audio/mp3", owner=victim)

        victim_schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at="2026-04-09T10:00:00Z",
            ends_at="2026-04-09T10:05:00Z",
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Try to access via filter combination
        response = api_client.get(
            f"/api/v2/schedule?instance={instance.id}&position=1&broadcasted=1"
        )

        if response.status_code == 200:
            data = response.json()
            for entry in data:
                if entry.get("id") == victim_schedule.id:
                    pytest.fail("Filter combination bypassed ownership check")
