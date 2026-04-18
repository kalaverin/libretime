"""Tests for ShowDays RETRIEVE, UPDATE, DELETE endpoints (T209)."""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowDays
from api.schedule.models.show import Record


@pytest.mark.django_db(transaction=True)
class TestShowDaysViewSetRUD:
    """Test ShowDays RETRIEVE, UPDATE, DELETE endpoints."""

    def setup_method(self):
        """Clean up show days before each test."""
        ShowDays.objects.all().delete()
        Show.objects.all().delete()

    # ==================== RETRIEVE ====================

    def test_retrieve_show_days_success(self, guest_client):
        """RETRIEVE should return show day details."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        response = guest_client.get(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 200
        assert response.json()["id"] == day.id

    def test_retrieve_show_days_contains_all_fields(self, guest_client):
        """RETRIEVE should include all fields."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            last_show_on=date(2026, 6, 1),
            start_time=time(14, 30),
            timezone="America/New_York",
            duration="01:30:00",
            week_day=ShowDays.WeekDay.FRIDAY,
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
            record_enabled=Record.YES,
            repeat_next_on=date(2026, 4, 8),
        )

        response = guest_client.get(f"/api/v2/show-days/{day.id}")
        result = response.json()
        assert result["show"] == show.id
        assert result["first_show_on"] == "2026-04-01"
        assert result["last_show_on"] == "2026-06-01"
        assert result["start_time"] == "14:30:00"
        assert result["timezone"] == "America/New_York"
        assert result["duration"] == "01:30:00"
        assert result["week_day"] == ShowDays.WeekDay.FRIDAY
        assert result["repeat_kind"] == ShowDays.RepeatKind.WEEKLY
        assert result["record_enabled"] == Record.YES
        assert result["repeat_next_on"] == "2026-04-08"

    def test_retrieve_show_days_not_found_returns_404(self, guest_client):
        """RETRIEVE non-existent show day should return 404."""
        response = guest_client.get("/api/v2/show-days/999999")
        assert response.status_code == 404

    def test_retrieve_show_days_no_auth_fails(self, client):
        """RETRIEVE without auth should return 403."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        response = client.get(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 403

    # ==================== UPDATE ====================

    def test_patch_update_start_time_success(self, guest_client):
        """PATCH should update start_time."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        response = guest_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"start_time": "16:30:00"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["start_time"] == "16:30:00"

    def test_patch_update_duration_success(self, guest_client):
        """PATCH should update duration."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            duration="01:00:00",
        )

        response = guest_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"duration": "02:00:00"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["duration"] == "02:00:00"

    def test_patch_update_timezone_success(self, guest_client):
        """PATCH should update timezone."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            timezone="UTC",
        )

        response = guest_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"timezone": "Europe/London"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["timezone"] == "Europe/London"

    def test_patch_update_week_day_success(self, guest_client):
        """PATCH should update week_day."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            week_day=ShowDays.WeekDay.MONDAY,
        )

        response = guest_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"week_day": ShowDays.WeekDay.FRIDAY}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["week_day"] == ShowDays.WeekDay.FRIDAY

    def test_patch_update_repeat_kind_success(self, guest_client):
        """PATCH should update repeat_kind."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

        response = guest_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"repeat_kind": ShowDays.RepeatKind.MONTHLY}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["repeat_kind"] == ShowDays.RepeatKind.MONTHLY

    def test_patch_update_last_show_on_success(self, guest_client):
        """PATCH should update last_show_on."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            last_show_on=None,
        )

        response = guest_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"last_show_on": "2026-12-31"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["last_show_on"] == "2026-12-31"

    def test_patch_not_found_returns_404(self, guest_client):
        """PATCH non-existent show day should return 404."""
        response = guest_client.patch(
            "/api/v2/show-days/999999",
            json.dumps({"start_time": "16:00:00"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_patch_no_auth_fails(self, client):
        """PATCH without auth should return 403."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        response = client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({"start_time": "16:00:00"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_patch_empty_body_no_change(self, guest_client):
        """PATCH with empty body should not change anything."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
            timezone="UTC",
        )

        response = guest_client.patch(
            f"/api/v2/show-days/{day.id}",
            json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["timezone"] == "UTC"
        assert result["start_time"] == "14:00:00"

    # ==================== DELETE ====================

    def test_delete_show_days_success_returns_204(self, guest_client):
        """DELETE should return 204 on successful deletion."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        response = guest_client.delete(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 204

    def test_delete_show_days_removes_from_db(self, guest_client):
        """DELETE should remove show day from database."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        guest_client.delete(f"/api/v2/show-days/{day.id}")
        assert ShowDays.objects.filter(id=day.id).count() == 0

    def test_delete_show_days_not_found_returns_404(self, guest_client):
        """DELETE non-existent show day should return 404."""
        response = guest_client.delete("/api/v2/show-days/999999")
        assert response.status_code == 404

    def test_delete_show_days_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        response = client.delete(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 403

    def test_delete_show_days_double_delete_returns_404(self, guest_client):
        """DELETE already deleted show day should return 404."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        guest_client.delete(f"/api/v2/show-days/{day.id}")
        response = guest_client.delete(f"/api/v2/show-days/{day.id}")
        assert response.status_code == 404

    def test_delete_show_days_returns_empty_body(self, guest_client):
        """DELETE should return empty response body."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        day = baker.make(
            ShowDays,
            show=show,
            first_show_on=date(2026, 4, 1),
            start_time=time(14, 0),
        )

        response = guest_client.delete(f"/api/v2/show-days/{day.id}")
        assert response.content == b""
