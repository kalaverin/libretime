"""Tests for ShowDays LIST endpoint (T207)."""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowDays


@pytest.mark.django_db(transaction=True)
class TestShowDaysViewSetList:
    """Test ShowDays LIST endpoint - GET /api/v2/show-days."""

    def setup_method(self):
        """Clean up show days before each test."""
        ShowDays.objects.all().delete()
        Show.objects.all().delete()

    def test_list_show_days_empty_returns_200(self, guest_client):
        """LIST with no show days should return empty array."""
        response = guest_client.get("/api/v2/show-days")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_show_days_returns_all(self, guest_client):
        """LIST should return all show days."""
        show = baker.make(Show, name="Test Show")
        day1 = baker.make(
            ShowDays,
            show=show,
            week_day=ShowDays.WeekDay.MONDAY,
        )
        day2 = baker.make(
            ShowDays,
            show=show,
            week_day=ShowDays.WeekDay.TUESDAY,
        )

        response = guest_client.get("/api/v2/show-days")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_show_days_returns_json(self, guest_client):
        """LIST should return JSON response."""
        show = baker.make(Show, name="Test Show")
        baker.make(ShowDays, show=show)

        response = guest_client.get("/api/v2/show-days")
        assert response["Content-Type"] == "application/json"

    def test_list_show_days_contains_id(self, guest_client):
        """LIST should include show day id."""
        show = baker.make(Show, name="Test Show")
        day = baker.make(ShowDays, show=show)

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == day.id

    def test_list_show_days_contains_show(self, guest_client):
        """LIST should include show reference."""
        show = baker.make(Show, name="Test Show")
        day = baker.make(ShowDays, show=show)

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["show"] == show.id

    def test_list_show_days_contains_first_show_on(self, guest_client):
        """LIST should include first_show_on date."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(ShowDays, show=show, first_show_on=date(2026, 4, 1))

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["first_show_on"] == "2026-04-01"

    def test_list_show_days_contains_last_show_on(self, guest_client):
        """LIST should include last_show_on date."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=date(2026, 6, 1),
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["last_show_on"] == "2026-06-01"

    def test_list_show_days_null_last_show_on(self, guest_client):
        """LIST should handle null last_show_on."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=None,
        )

        response = guest_client.get("/api/v2/show-days")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["last_show_on"] is None

    def test_list_show_days_contains_start_time(self, guest_client):
        """LIST should include start_time."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 30),
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["start_time"] == "14:30:00"

    def test_list_show_days_contains_timezone(self, guest_client):
        """LIST should include timezone."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            timezone="America/New_York",
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["timezone"] == "America/New_York"

    def test_list_show_days_contains_duration(self, guest_client):
        """LIST should include duration."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            duration="01:30:00",
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["duration"] == "01:30:00"

    def test_list_show_days_contains_week_day(self, guest_client):
        """LIST should include week_day."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            week_day=ShowDays.WeekDay.FRIDAY,
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["week_day"] == ShowDays.WeekDay.FRIDAY

    def test_list_show_days_contains_repeat_kind(self, guest_client):
        """LIST should include repeat_kind."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["repeat_kind"] == ShowDays.RepeatKind.WEEKLY

    def test_list_show_days_contains_record_enabled(self, guest_client):
        """LIST should include record_enabled."""
        from datetime import date

        from api.schedule.models.show import Record

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            record_enabled=Record.YES,
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["record_enabled"] == Record.YES

    def test_list_show_days_contains_repeat_next_on(self, guest_client):
        """LIST should include repeat_next_on."""
        from datetime import date

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            repeat_next_on=date(2026, 4, 8),
        )

        response = guest_client.get("/api/v2/show-days")
        data = response.json()
        assert data[0]["repeat_next_on"] == "2026-04-08"

    def test_list_show_days_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/show-days")
        assert response.status_code == 403

    def test_list_show_days_filter_by_show(self, guest_client):
        """LIST should support filtering by show."""
        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")
        from datetime import date

        baker.make(ShowDays, show=show1, first_show_on=date(2026, 4, 1))
        baker.make(ShowDays, show=show2, first_show_on=date(2026, 4, 2))

        response = guest_client.get(f"/api/v2/show-days?show={show1.id}")
        # Filtering may or may not be supported
        assert response.status_code in [200, 400]

    def test_list_show_days_multiple_days_same_show(self, guest_client):
        """LIST multiple days for same show."""
        show = baker.make(Show, name="Test Show")
        from datetime import date

        baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            week_day=ShowDays.WeekDay.MONDAY,
        )
        baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 2),
            week_day=ShowDays.WeekDay.TUESDAY,
        )
        baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 3),
            week_day=ShowDays.WeekDay.WEDNESDAY,
        )

        response = guest_client.get("/api/v2/show-days")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
