"""
RED TEAM: T208 - ShowDays CREATE endpoint security tests.

Attack vectors:
- Anonymous CREATE (authentication bypass)
- BOLA: create for other user's show
- Mass assignment: id, created_at manipulation
- SQL injection in all fields
- Time field manipulation
- Repeat options abuse
- Record enabled escalation
"""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowDays
from api.schedule.models.show import Record


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateAuthentication:
    """Authentication bypass attacks."""

    @pytest.mark.xfail(reason="Anonymous creation allowed")
    def test_create_without_auth(self, admin_client):
        """Anonymous CREATE should fail."""
        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can CREATE show days")
        assert response.status_code in [401, 403]


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateBOLA:
    """Broken Object Level Authorization attacks."""

    @pytest.mark.xfail(reason="BOLA: Can create show day for other user's show")
    def test_create_for_other_user_show(
        self,
        admin_client,
        regular_user,
        admin_user,
    ):
        """Create show day for another user's show."""
        show = baker.make(Show, name="Admin Show")

        admin_client.force_authenticate(user=regular_user)
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail(
                "CRITICAL BUG: Can CREATE show day for other user's show (BOLA)",
            )


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateMassAssignment:
    """Mass assignment attacks via __all__ fields."""

    def test_create_with_id_field(self, admin_client):
        """Try to set id field during CREATE."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "id": 99999,
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201 and response.json().get("id") == 99999:
            pytest.fail("CRITICAL BUG: Mass assignment - id field accepted")

    def test_create_with_created_at(self, admin_client):
        """Try to manipulate created_at timestamp."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            "created_at": "2020-01-01T00:00:00Z",
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("created_at", "").startswith("2020"):
                pytest.fail(
                    "CRITICAL BUG: Mass assignment - created_at manipulated",
                )


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateSQLInjection:
    """SQL injection attacks in all fields."""

    sqli_payloads = [
        "1' OR '1'='1",
        "1; DROP TABLE cc_show_days;--",
        "1 UNION SELECT * FROM cc_subjs--",
        "1' AND 1=1--",
        "1' AND 1=2--",
    ]

    def test_sqli_in_first_show_on(self, admin_client, admin_user):
        """SQL injection in first_show_on field."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=admin_user)

        for payload in self.sqli_payloads:
            data = {
                "show": show.id,
                "first_show_on": payload,
                "start_time": "14:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
                "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            }
            response = admin_client.post(
                "/api/v2/show-days",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi crash in first_show_on: {payload}")

    def test_sqli_in_start_time(self, admin_client, admin_user):
        """SQL injection in start_time field."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=admin_user)

        for payload in self.sqli_payloads:
            data = {
                "show": show.id,
                "first_show_on": "2026-04-01",
                "start_time": payload,
                "timezone": "UTC",
                "duration": "01:00:00",
                "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            }
            response = admin_client.post(
                "/api/v2/show-days",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi crash in start_time: {payload}")

    def test_sqli_in_timezone(self, admin_client, admin_user):
        """SQL injection in timezone field."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=admin_user)

        for payload in self.sqli_payloads:
            data = {
                "show": show.id,
                "first_show_on": "2026-04-01",
                "start_time": "14:00:00",
                "timezone": payload,
                "duration": "01:00:00",
                "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            }
            response = admin_client.post(
                "/api/v2/show-days",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi crash in timezone: {payload}")

    def test_sqli_in_repeat_kind(self, admin_client, admin_user):
        """SQL injection in repeat_kind field."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=admin_user)

        for payload in self.sqli_payloads:
            data = {
                "show": show.id,
                "first_show_on": "2026-04-01",
                "start_time": "14:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
                "repeat_kind": payload,
            }
            response = admin_client.post(
                "/api/v2/show-days",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi crash in repeat_kind: {payload}")


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateTimeManipulation:
    """Time field manipulation attacks."""

    def test_negative_duration(self, admin_client):
        """Try to create with negative duration."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "-01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Negative duration accepted")

    @pytest.mark.xfail(reason="Zero duration accepted")
    def test_zero_duration(self, admin_client):
        """Try to create with zero duration."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "00:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Zero duration accepted")

    def test_invalid_timezone(self, admin_client):
        """Try to create with invalid timezone."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "Invalid/Timezone/That/Does/Not/Exist",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        # Document behavior
        assert response.status_code in [201, 400, 403]

    def test_invalid_week_day(self, admin_client):
        """Try to create with out-of-range week_day."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        invalid_days = [-1, 7, 8, 99, 999]
        for day in invalid_days:
            data = {
                "show": show.id,
                "first_show_on": "2026-04-01",
                "start_time": "14:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
                "week_day": day,
                "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            }
            response = admin_client.post(
                "/api/v2/show-days",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 201:
                pytest.fail(f"BUG: Invalid week_day {day} accepted")

    @pytest.mark.xfail(reason="last_show_on before first_show_on accepted")
    def test_last_show_before_first(self, admin_client):
        """Try to create where last_show_on < first_show_on."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-06-01",
            "last_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: last_show_on before first_show_on accepted")


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateRepeatAbuse:
    """Repeat options abuse attacks."""

    def test_invalid_repeat_kind(self, admin_client):
        """Try to create with invalid repeat_kind."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": "INVALID_REPEAT_KIND",
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Invalid repeat_kind accepted")

    @pytest.mark.xfail(reason="repeat_next_on can be manipulated by user")
    def test_repeat_next_on_manipulation(self, admin_client):
        """Try to manipulate repeat_next_on date."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            "repeat_next_on": "2030-12-31",
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            result = response.json()
            # repeat_next_on should be auto-calculated, not user-set
            if result.get("repeat_next_on") == "2030-12-31":
                pytest.fail("BUG: repeat_next_on can be manipulated by user")


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateRecordEscalation:
    """Recording privilege escalation attacks."""

    @pytest.mark.xfail(reason="record_enabled can be set without permissions")
    def test_record_enabled_without_permission(self, admin_client, regular_user):
        """Try to enable recording without proper permissions."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=regular_user)

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            "record_enabled": Record.YES,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            result = response.json()
            if result.get("record_enabled") == Record.YES:
                pytest.fail(
                    "BUG: record_enabled can be set without permissions",
                )

    def test_record_enabled_invalid_value(self, admin_client):
        """Try to set invalid record_enabled value."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            "record_enabled": 999,  # Invalid value
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Invalid record_enabled value accepted")


@pytest.mark.django_db(transaction=True)
class TestShowDaysCreateEdgeCases:
    """Edge case and input validation attacks."""

    def test_null_show(self, admin_client):
        """Try to create with null show."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": None,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Null show accepted")

    def test_nonexistent_show(self, admin_client):
        """Try to create with non-existent show ID."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": 99999,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Non-existent show ID accepted")

    def test_malformed_json(self, admin_client):
        """Try to send malformed JSON."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        response = admin_client.post(
            "/api/v2/show-days",
            '{"invalid json',  # Malformed
            content_type="application/json",
        )
        if response.status_code == 500:
            pytest.fail("BUG: Malformed JSON causes server error")

    def test_extra_fields_ignored(self, admin_client):
        """Check if extra fields are ignored or cause error."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            "hacker_field": "malicious_value",
            "__proto__": {"isAdmin": True},
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        # Should either reject or ignore extra fields
        assert response.status_code in [201, 400, 403]
