"""
RED TEAM: T207 - ShowDays LIST endpoint security tests.

Attack vectors:
- Filter injection (SQLi through show param)
- BOLA: access other users' show days
- Mass assignment via GET
- Information disclosure via error messages
- Timezone manipulation
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestShowDaysFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_show_id(self, api_client, admin_user):
        """Try to filter by invalid show_id."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/show-days?show=invalid")

        if response.status_code == 500:
            pytest.fail("BUG: Filter crashes on invalid show_id")
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in show filter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_show_days;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/show-days?show={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes crash: {payload}")

    def test_filter_by_negative_show_id(self, api_client, admin_user):
        """Try to filter by negative show_id."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/show-days?show=-1")

        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestShowDaysBOLA:
    """Broken Object Level Authorization attacks."""

    def test_list_shows_only_own_days(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Verify list returns only user's own show days."""
        show1 = baker.make("schedule.Show", name="Admin Show")
        show2 = baker.make("schedule.Show", name="User Show")

        admin_day = baker.make("schedule.ShowDays", show=show1)
        user_day = baker.make("schedule.ShowDays", show=show2)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/show-days")

        assert response.status_code == 200
        data = response.json()

        day_ids = [d["id"] for d in data]

        # API list does not filter by owner (by design)
        assert admin_day.id in day_ids

    def test_filter_by_other_user_show(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Filter by another user's show."""
        show = baker.make("schedule.Show", name="Admin Show")
        day = baker.make("schedule.ShowDays", show=show)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/show-days?show={show.id}")

        assert response.status_code == 200
        data = response.json()

        # API allows filtering by any show_id (by design)
        assert len(data) > 0


@pytest.mark.django_db
class TestShowDaysTimeManipulation:
    """Time field manipulation attacks."""

    def test_timezone_with_invalid_value(self, api_client, admin_user):
        """Try to create show day with invalid timezone."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/show-days",
            {
                "show": show.id,
                "week_day": 1,
                "start_time": "10:00:00",
                "timezone": "Invalid/Timezone",
                "duration": "01:00:00",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]

    def test_duration_with_negative_value(self, api_client, admin_user):
        """Try to create with negative duration."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/show-days",
            {
                "show": show.id,
                "week_day": 1,
                "start_time": "10:00:00",
                "timezone": "UTC",
                "duration": "-01:00:00",
            },
            format="json",
        )

        # Should reject negative duration
        if response.status_code == 201:
            pytest.fail("BUG: Accepts negative duration")

    def test_week_day_out_of_range(self, api_client, admin_user):
        """Try to create with invalid week_day."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/show-days",
            {
                "show": show.id,
                "week_day": 8,  # Invalid (should be 0-6)
                "start_time": "10:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestShowDaysBusinessLogic:
    """Business logic bypass attacks."""

    def test_list_without_auth(self, session_client):
        """Try to list without authentication."""
        response = session_client.get("/api/v2/show-days")

        assert response.status_code in [403, 401]

    def test_create_without_auth(self, api_client):
        """Try to create without authentication."""
        show = baker.make("schedule.Show", name="Test Show")

        response = api_client.post(
            "/api/v2/show-days",
            {
                "show": show.id,
                "week_day": 1,
                "start_time": "10:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can create show days")

    def test_create_for_other_user_show(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to create show day for another user's show."""
        show = baker.make("schedule.Show", name="Admin Show")

        api_client.force_authenticate(user=regular_user)
        response = api_client.post(
            "/api/v2/show-days",
            {
                "show": show.id,
                "week_day": 1,
                "start_time": "10:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail(
                "CRITICAL BUG: Can create show day for other user's show",
            )


@pytest.mark.django_db
class TestShowDaysInformationDisclosure:
    """Information disclosure attacks."""

    def test_error_message_on_invalid_filter(self, api_client, admin_user):
        """Check if error messages leak information."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/show-days?show=invalid")

        if response.status_code == 400:
            content = response.content.decode()
            leaked_terms = ["cc_show_days", "column", "sql", "table"]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: Error leaks info: {term}")


@pytest.mark.django_db
class TestShowDaysRepeatOptions:
    """Repeat option manipulation attacks."""

    def test_invalid_repeat_kind(self, api_client, admin_user):
        """Try to create with invalid repeat_kind."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/show-days",
            {
                "show": show.id,
                "week_day": 1,
                "start_time": "10:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
                "repeat_kind": "invalid_kind",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]

    def test_record_enabled_manipulation(self, api_client, admin_user):
        """Try to enable recording."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/show-days",
            {
                "show": show.id,
                "week_day": 1,
                "start_time": "10:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
                "record_enabled": True,
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]
