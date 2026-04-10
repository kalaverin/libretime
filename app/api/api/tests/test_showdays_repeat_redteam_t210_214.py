"""
RED TEAM: T210-T214 - ShowDays repeat patterns security tests.

Attack vectors:
- Repeat kind manipulation (switching between weekly/monthly)
- Week day mismatch with repeat pattern
- End date bypass for infinite repeats
- Repeat interval abuse (very large values)
- Timezone manipulation with repeat patterns
"""

import json
import pytest
from model_bakery import baker

from api.schedule.models import Show, ShowDays


@pytest.mark.django_db(transaction=True)
class TestShowDaysRepeatKindAbuse:
    """Repeat kind manipulation attacks."""

    def test_create_invalid_repeat_kind_value(self, api_client):
        """Try to create with integer outside valid choices."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": 999,
        }
        response = api_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Invalid repeat_kind integer accepted")

    def test_create_null_repeat_kind(self, api_client):
        """Try to create with null repeat_kind."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": None,
        }
        response = api_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Null repeat_kind accepted")


@pytest.mark.django_db(transaction=True)
class TestShowDaysWeekDayMismatch:
    """Week day vs repeat pattern mismatch attacks."""

    def test_week_day_with_monthly_mismatch(self, api_client):
        """Try week_day that doesn't match first_show_on with monthly."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        # 2026-04-01 is Wednesday (week_day=2), but we try Friday (week_day=4)
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "week_day": 4,  # Friday, but Apr 1 is Wednesday
            "repeat_kind": ShowDays.RepeatKind.MONTHLY,
        }
        response = api_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        # Document behavior - should ideally validate
        assert response.status_code in [201, 400]

    def test_invalid_week_day_for_weekly(self, api_client):
        """Try invalid week_day with weekly repeat."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        invalid_days = [-1, 7, 8, 100]
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
            response = api_client.post(
                "/api/v2/show-days",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 201:
                pytest.fail(f"BUG: Invalid week_day {day} accepted")


@pytest.mark.django_db(transaction=True)
class TestShowDaysRepeatIntervalAbuse:
    """Repeat interval abuse attacks."""

    def test_very_long_duration_with_repeat(self, api_client):
        """Try extremely long duration with repeating show."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "last_show_on": "2126-04-01",  # 100 years
            "start_time": "00:00:00",
            "timezone": "UTC",
            "duration": "23:59:59",  # Almost 24 hours
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = api_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        # Should limit duration or date range
        assert response.status_code in [201, 400]

    def test_overlap_with_24h_duration(self, api_client):
        """Try 24+ hour duration causing overlap."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "12:00:00",
            "timezone": "UTC",
            "duration": "25:00:00",  # More than 24 hours
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = api_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Duration > 24h accepted, causes overlap")


@pytest.mark.django_db(transaction=True)
class TestShowDaysEndDateBypass:
    """End date bypass attacks."""

    @pytest.mark.xfail(reason="T396: Can remove last_show_on via PATCH")
    def test_remove_last_show_on_via_patch(self, api_client):
        """Try to remove end date via PATCH to create infinite repeat.""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(
            ShowDays,
            show=show,
            first_show_on="2026-04-01",
            last_show_on="2026-06-01",
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        api_client.force_authenticate(user=baker.make("core.User"))
        
        data = {"last_show_on": None}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("last_show_on") is None:
                pytest.fail("BUG: Can remove last_show_on to create infinite repeat")

    def test_far_future_last_show_on(self, api_client):
        """Try end date very far in future."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "last_show_on": "3026-04-01",  # 1000 years later
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = api_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        # Should limit future date
        assert response.status_code in [201, 400]


@pytest.mark.django_db(transaction=True)
class TestShowDaysRepeatFilterAbuse:
    """Repeat pattern filter abuse."""

    def test_filter_by_invalid_repeat_kind(self, api_client):
        """Try to filter by invalid repeat_kind."""
        api_client.force_authenticate(user=baker.make("core.User"))
        
        response = api_client.get("/api/v2/show-days?repeat_kind=invalid")
        if response.status_code == 500:
            pytest.fail("BUG: Filter by invalid repeat_kind causes crash")

    def test_filter_by_sql_injection_in_repeat_kind(self, api_client):
        """Try SQL injection in repeat_kind filter."""
        api_client.force_authenticate(user=baker.make("core.User"))
        
        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_show_days--",
            "weekly' UNION SELECT * FROM cc_subjs--",
        ]
        
        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/show-days?repeat_kind={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in repeat_kind filter: {payload}")


@pytest.mark.django_db(transaction=True)
class TestShowDaysRepeatTimezoneAbuse:
    """Timezone manipulation with repeat patterns."""

    def test_timezone_change_breaks_repeat(self, api_client):
        """Try changing timezone that breaks repeat calculation."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(
            ShowDays,
            show=show,
            first_show_on="2026-04-01",
            start_time="23:30:00",
            timezone="UTC",
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        api_client.force_authenticate(user=baker.make("core.User"))
        
        # Change to timezone where start_time crosses day boundary
        data = {"timezone": "Pacific/Auckland"}  # UTC+12
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )
        # Should validate timezone change doesn't break logic
        assert response.status_code in [200, 400]

    def test_invalid_timezone_with_repeat(self, api_client):
        """Try invalid timezone with repeating show."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))
        
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "InvalidTimezone123",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = api_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        # Document behavior
        assert response.status_code in [201, 400]


@pytest.mark.django_db(transaction=True)
class TestShowDaysRepeatSwitchAbuse:
    """Switching repeat patterns abuse."""

    def test_switch_weekly_to_monthly_invalid_day(self, api_client):
        """Try switching repeat kind with incompatible week_day."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(
            ShowDays,
            show=show,
            first_show_on="2026-04-01",  # Wednesday
            week_day=2,  # Wednesday
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        api_client.force_authenticate(user=baker.make("core.User"))
        
        # Switch to monthly but keep wrong week_day
        data = {
            "repeat_kind": ShowDays.RepeatKind.MONTHLY,
            "week_day": 5,  # Saturday - not matching first_show_on
        }
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )
        # Should validate consistency
        assert response.status_code in [200, 400]

    def test_rapid_repeat_kind_switching(self, api_client):
        """Try rapid switching between repeat kinds."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(
            ShowDays,
            show=show,
            first_show_on="2026-04-01",
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        api_client.force_authenticate(user=baker.make("core.User"))
        
        kinds = [
            ShowDays.RepeatKind.WEEKLY_2,
            ShowDays.RepeatKind.WEEKLY_3,
            ShowDays.RepeatKind.WEEKLY_4,
            ShowDays.RepeatKind.MONTHLY,
            ShowDays.RepeatKind.WEEKLY,
        ]
        
        for kind in kinds:
            response = api_client.patch(
                f"/api/v2/show-days/{show_days.id}",
                json.dumps({"repeat_kind": kind}),
                content_type="application/json",
            )
            assert response.status_code in [200, 400], f"Failed at kind {kind}"
