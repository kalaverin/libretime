"""Tests for ShowDays CREATE endpoint (T208)."""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowDays
from api.schedule.models.show import Record


@pytest.mark.django_db(transaction=True)
class TestShowDaysViewSetCreate:
    """Test ShowDays CREATE endpoint - POST /api/v2/show-days."""

    def setup_method(self):
        """Clean up show days before each test."""
        ShowDays.objects.all().delete()
        Show.objects.all().delete()

    def test_create_show_days_minimal_success(self, guest_client):
        """CREATE with minimal required fields should succeed."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["show"] == show.id

    def test_create_show_days_with_last_show_on(self, guest_client):
        """CREATE with last_show_on should succeed."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "last_show_on": "2026-06-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["last_show_on"] == "2026-06-01"

    def test_create_show_days_with_week_day(self, guest_client):
        """CREATE with week_day should succeed."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "week_day": ShowDays.WeekDay.FRIDAY,
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["week_day"] == ShowDays.WeekDay.FRIDAY

    def test_create_show_days_with_record_enabled(self, guest_client):
        """CREATE with record_enabled should succeed."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            "record_enabled": Record.YES,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["record_enabled"] == Record.YES

    def test_create_show_days_with_repeat_next_on(self, guest_client):
        """CREATE with repeat_next_on should succeed."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            "repeat_next_on": "2026-04-08",
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["repeat_next_on"] == "2026-04-08"

    def test_create_show_days_missing_show_fails(self, guest_client):
        """CREATE without show should fail."""

        data = {
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_days_missing_first_show_on_fails(self, guest_client):
        """CREATE without first_show_on should fail."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_days_missing_start_time_fails(self, guest_client):
        """CREATE without start_time should fail."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_days_returns_json(self, guest_client):
        """CREATE should return JSON response."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response["Content-Type"] == "application/json"

    def test_create_show_days_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        data = {"first_show_on": "2026-04-01"}
        response = client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_show_days_invalid_show_fails(self, guest_client):
        """CREATE with invalid show id should fail."""

        data = {
            "show": 999999,
            "first_show_on": "2026-04-01",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_days_invalid_date_format(self, guest_client):
        """CREATE with invalid date format should fail."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "not-a-date",
            "start_time": "14:00:00",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_days_invalid_time_format(self, guest_client):
        """CREATE with invalid time format should fail."""

        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "not-a-time",
            "timezone": "UTC",
            "duration": "01:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = guest_client.post(
            "/api/v2/show-days",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_days_multiple_for_same_show(self, guest_client):
        """CREATE multiple show days for same show should succeed."""

        show = baker.make(Show, name="Test Show")

        for day in [
            ShowDays.WeekDay.MONDAY,
            ShowDays.WeekDay.WEDNESDAY,
            ShowDays.WeekDay.FRIDAY,
        ]:
            data = {
                "show": show.id,
                "first_show_on": "2026-04-01",
                "start_time": "14:00:00",
                "timezone": "UTC",
                "duration": "01:00:00",
                "week_day": day,
                "repeat_kind": ShowDays.RepeatKind.WEEKLY,
            }
            response = guest_client.post(
                "/api/v2/show-days",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code == 201

        assert ShowDays.objects.filter(show=show).count() == 3
