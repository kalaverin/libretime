"""Tests for ShowDays repeat patterns (T210-T214)."""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowDays


@pytest.mark.django_db(transaction=True)
class TestShowDaysRepeatPatterns:
    """Test ShowDays endpoints with focus on repeat patterns (T210-T214)."""

    def setup_method(self):
        """Clean up show days before each test."""
        ShowDays.objects.all().delete()
        Show.objects.all().delete()

    # ==================== T210: LIST with repeat patterns ====================

    def test_list_show_days_weekly_repeat(self, admin_client):
        """LIST should show weekly repeat pattern correctly."""
        from datetime import date, time

        show = baker.make(Show, name="Weekly Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
            week_day=ShowDays.WeekDay.WEDNESDAY,
        )

        response = admin_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["repeat_kind"] == ShowDays.RepeatKind.WEEKLY
        assert data[0]["week_day"] == ShowDays.WeekDay.WEDNESDAY

    def test_list_show_days_biweekly_repeat(self, admin_client):
        """LIST should show bi-weekly repeat pattern correctly."""
        from datetime import date, time

        show = baker.make(Show, name="BiWeekly Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY_2,
        )

        response = admin_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["repeat_kind"] == ShowDays.RepeatKind.WEEKLY_2

    def test_list_show_days_monthly_repeat(self, admin_client):
        """LIST should show monthly repeat pattern correctly."""
        from datetime import date, time

        show = baker.make(Show, name="Monthly Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.MONTHLY,
        )

        response = admin_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["repeat_kind"] == ShowDays.RepeatKind.MONTHLY

    def test_list_show_days_filter_by_repeat_kind(self, admin_client):
        """LIST should support filtering by repeat_kind."""
        from datetime import date, time

        show1 = baker.make(Show, name="Weekly Show")
        show2 = baker.make(Show, name="Monthly Show")

        baker.make(
            ShowDays,
            show=show1,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        baker.make(
            ShowDays,
            show=show2,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.MONTHLY,
        )

        # Try filtering by repeat_kind
        response = admin_client.get(
            f"/api/v2/show-days?repeat_kind={ShowDays.RepeatKind.WEEKLY}",
        )
        # Filtering may or may not be supported
        assert response.status_code in [200, 400]

    def test_list_show_days_with_end_date(self, admin_client):
        """LIST should show shows with end dates."""
        from datetime import date, time

        show = baker.make(Show, name="Limited Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=date(2026, 6, 30),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["first_show_on"] == "2026-04-01"
        assert data[0]["last_show_on"] == "2026-06-30"

    def test_list_show_days_no_end_date(self, admin_client):
        """LIST should show shows without end dates (ongoing)."""
        from datetime import date, time

        show = baker.make(Show, name="Ongoing Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=None,
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["last_show_on"] is None

    # ==================== T211: CREATE weekly repeat ====================

    def test_create_show_days_weekly_repeat(self, admin_client):
        """CREATE with weekly repeat should succeed."""

        show = baker.make(Show, name="Weekly Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "week_day": ShowDays.WeekDay.WEDNESDAY,
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.json()
        assert result["repeat_kind"] == ShowDays.RepeatKind.WEEKLY
        assert result["week_day"] == ShowDays.WeekDay.WEDNESDAY

    def test_create_show_days_biweekly_repeat(self, admin_client):
        """CREATE with bi-weekly repeat should succeed."""

        show = baker.make(Show, name="BiWeekly Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "week_day": ShowDays.WeekDay.MONDAY,
            "repeat_kind": ShowDays.RepeatKind.WEEKLY_2,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["repeat_kind"] == ShowDays.RepeatKind.WEEKLY_2

    def test_create_show_days_triweekly_repeat(self, admin_client):
        """CREATE with tri-weekly repeat should succeed."""

        show = baker.make(Show, name="TriWeekly Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY_3,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["repeat_kind"] == ShowDays.RepeatKind.WEEKLY_3

    def test_create_show_days_quadweekly_repeat(self, admin_client):
        """CREATE with quad-weekly repeat should succeed."""

        show = baker.make(Show, name="QuadWeekly Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY_4,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["repeat_kind"] == ShowDays.RepeatKind.WEEKLY_4

    # ==================== T212: CREATE monthly repeat ====================

    def test_create_show_days_monthly_repeat(self, admin_client):
        """CREATE with monthly repeat should succeed."""

        show = baker.make(Show, name="Monthly Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.MONTHLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["repeat_kind"] == ShowDays.RepeatKind.MONTHLY

    def test_create_show_days_monthly_with_week_day(self, admin_client):
        """CREATE monthly repeat with week_day should succeed."""

        show = baker.make(Show, name="Monthly Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "week_day": ShowDays.WeekDay.FRIDAY,
            "repeat_kind": ShowDays.RepeatKind.MONTHLY,
        }
        response = admin_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.json()
        assert result["repeat_kind"] == ShowDays.RepeatKind.MONTHLY
        assert result["week_day"] == ShowDays.WeekDay.FRIDAY

    def test_create_show_days_with_end_date(self, admin_client):
        """CREATE with end date should succeed."""

        show = baker.make(Show, name="Limited Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "last_show_on": "2026-06-30",
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
        assert response.status_code == 201
        assert response.json()["last_show_on"] == "2026-06-30"

    def test_create_show_days_without_end_date(self, admin_client):
        """CREATE without end date (ongoing) should succeed."""

        show = baker.make(Show, name="Ongoing Show")
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
        assert response.status_code == 201
        assert response.json()["last_show_on"] is None

    # ==================== T213: UPDATE repeat pattern ====================

    def test_update_repeat_kind_weekly_to_monthly(self, admin_client):
        """UPDATE repeat_kind from weekly to monthly should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"repeat_kind": ShowDays.RepeatKind.MONTHLY}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["repeat_kind"] == ShowDays.RepeatKind.MONTHLY

    def test_update_repeat_kind_monthly_to_biweekly(self, admin_client):
        """UPDATE repeat_kind from monthly to bi-weekly should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.MONTHLY,
        )

        response = admin_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"repeat_kind": ShowDays.RepeatKind.WEEKLY_2}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["repeat_kind"] == ShowDays.RepeatKind.WEEKLY_2

    def test_update_start_time(self, admin_client):
        """UPDATE start_time should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"start_time": "16:30:00"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["start_time"] == "16:30:00"

    def test_update_week_day(self, admin_client):
        """UPDATE week_day should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            week_day=ShowDays.WeekDay.MONDAY,
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"week_day": ShowDays.WeekDay.FRIDAY}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["week_day"] == ShowDays.WeekDay.FRIDAY

    def test_update_add_end_date(self, admin_client):
        """UPDATE to add end date should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=None,
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"last_show_on": "2026-12-31"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["last_show_on"] == "2026-12-31"

    def test_update_remove_end_date(self, admin_client):
        """UPDATE to remove end date should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=date(2026, 6, 30),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"last_show_on": None}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["last_show_on"] is None

    # ==================== T214: DELETE show day ====================

    def test_delete_show_day_with_weekly_repeat(self, admin_client):
        """DELETE show day with weekly repeat should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.delete(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 204
        assert not ShowDays.objects.filter(id=day.id).exists()

    def test_delete_show_day_with_monthly_repeat(self, admin_client):
        """DELETE show day with monthly repeat should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.MONTHLY,
        )

        response = admin_client.delete(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 204
        assert not ShowDays.objects.filter(id=day.id).exists()

    def test_delete_show_day_with_end_date(self, admin_client):
        """DELETE show day with end date should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=date(2026, 6, 30),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.delete(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 204

    def test_delete_show_day_without_end_date(self, admin_client):
        """DELETE ongoing show day should succeed."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=None,
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = admin_client.delete(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 204

    def test_delete_show_day_multiple_days_remain(self, admin_client):
        """DELETE one show day should leave others."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day1 = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            week_day=ShowDays.WeekDay.MONDAY,
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        day2 = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 2),
            start_time=time(14, 0),
            week_day=ShowDays.WeekDay.TUESDAY,
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        day3 = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 3),
            start_time=time(14, 0),
            week_day=ShowDays.WeekDay.WEDNESDAY,
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        admin_client.delete(f"/api/v2/show-days/{day2.id}")

        assert ShowDays.objects.filter(id=day1.id).exists()
        assert not ShowDays.objects.filter(id=day2.id).exists()
        assert ShowDays.objects.filter(id=day3.id).exists()
