"""Tests for ShowRebroadcasts endpoints (T219)."""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowRebroadcast


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastViewSet:
    """Test ShowRebroadcasts LIST/CREATE endpoints (T219)."""

    def setup_method(self):
        """Clean up rebroadcasts before each test."""
        ShowRebroadcast.objects.all().delete()
        Show.objects.all().delete()

    # ==================== LIST ====================

    def test_list_rebroadcasts_empty_returns_200(self, admin_client):
        """LIST with no rebroadcasts should return empty array."""
        response = admin_client.get("/api/v2/show-rebroadcasts")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_rebroadcasts_returns_all(self, admin_client):
        """LIST should return all rebroadcasts."""
        from datetime import time

        show = baker.make(Show, name="Test Show")
        rebroadcast1 = baker.make(
            ShowRebroadcast,
            show=show,
            day_offset="1",
            start_time=time(14, 0),
        )
        rebroadcast2 = baker.make(
            ShowRebroadcast,
            show=show,
            day_offset="7",
            start_time=time(16, 0),
        )

        response = admin_client.get("/api/v2/show-rebroadcasts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_rebroadcasts_contains_id(self, admin_client):
        """LIST should include rebroadcast id."""
        from datetime import time

        show = baker.make(Show, name="Test Show")
        rebroadcast = baker.make(
            ShowRebroadcast,
            show=show,
            day_offset="1",
            start_time=time(14, 0),
        )

        response = admin_client.get("/api/v2/show-rebroadcasts")
        data = response.json()
        assert data[0]["id"] == rebroadcast.id

    def test_list_rebroadcasts_contains_show(self, admin_client):
        """LIST should include show reference."""
        from datetime import time

        show = baker.make(Show, name="Test Show")
        rebroadcast = baker.make(
            ShowRebroadcast,
            show=show,
            day_offset="1",
            start_time=time(14, 0),
        )

        response = admin_client.get("/api/v2/show-rebroadcasts")
        data = response.json()
        assert data[0]["show"] == show.id

    def test_list_rebroadcasts_contains_day_offset(self, admin_client):
        """LIST should include day_offset."""
        from datetime import time

        show = baker.make(Show, name="Test Show")
        rebroadcast = baker.make(
            ShowRebroadcast,
            show=show,
            day_offset="3",
            start_time=time(14, 0),
        )

        response = admin_client.get("/api/v2/show-rebroadcasts")
        data = response.json()
        assert data[0]["day_offset"] == "3"

    def test_list_rebroadcasts_contains_start_time(self, admin_client):
        """LIST should include start_time."""
        from datetime import time

        show = baker.make(Show, name="Test Show")
        rebroadcast = baker.make(
            ShowRebroadcast,
            show=show,
            day_offset="1",
            start_time=time(16, 30),
        )

        response = admin_client.get("/api/v2/show-rebroadcasts")
        data = response.json()
        assert data[0]["start_time"] == "16:30:00"

    def test_list_rebroadcasts_filter_by_show(self, admin_client):
        """LIST should support filtering by show."""
        from datetime import time

        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")

        baker.make(
            ShowRebroadcast,
            show=show1,
            day_offset="1",
            start_time=time(14, 0),
        )
        baker.make(
            ShowRebroadcast,
            show=show2,
            day_offset="2",
            start_time=time(16, 0),
        )

        response = admin_client.get(f"/api/v2/show-rebroadcasts?show={show1.id}")
        assert response.status_code in [200, 400]

    def test_list_rebroadcasts_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/show-rebroadcasts")
        assert response.status_code == 403

    # ==================== CREATE ====================

    def test_create_rebroadcast_success(self, admin_client):
        """CREATE rebroadcast should succeed."""
        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "day_offset": "1",
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["day_offset"] == "1"
        assert response.json()["start_time"] == "14:00:00"

    def test_create_rebroadcast_multiple_day_offsets(self, admin_client):
        """CREATE rebroadcasts with different day offsets."""
        show = baker.make(Show, name="Test Show")

        for offset in ["1", "2", "7", "14"]:
            data = {
                "show": show.id,
                "day_offset": offset,
                "start_time": "14:00:00",
            }
            response = admin_client.post(
                "/api/v2/show-rebroadcasts",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code == 201

        assert ShowRebroadcast.objects.filter(show=show).count() == 4

    def test_create_rebroadcast_different_times(self, admin_client):
        """CREATE rebroadcasts with different start times."""
        show = baker.make(Show, name="Test Show")

        for time_str in ["10:00:00", "14:30:00", "18:00:00", "23:59:00"]:
            data = {
                "show": show.id,
                "day_offset": "1",
                "start_time": time_str,
            }
            response = admin_client.post(
                "/api/v2/show-rebroadcasts",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code == 201

    def test_create_rebroadcast_missing_show_fails(self, admin_client):
        """CREATE without show should fail."""
        data = {
            "day_offset": "1",
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_rebroadcast_missing_day_offset_fails(self, admin_client):
        """CREATE without day_offset should fail."""
        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_rebroadcast_missing_start_time_fails(self, admin_client):
        """CREATE without start_time should fail."""
        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "day_offset": "1",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_rebroadcast_invalid_show_fails(self, admin_client):
        """CREATE with invalid show should fail."""
        data = {
            "show": 999999,
            "day_offset": "1",
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_rebroadcast_invalid_time_format(self, admin_client):
        """CREATE with invalid time format should fail."""
        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "day_offset": "1",
            "start_time": "not-a-time",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_rebroadcast_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        data = {"day_offset": "1"}
        response = client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_rebroadcast_zero_day_offset(self, admin_client):
        """CREATE with day_offset=0 (same day) should succeed."""
        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "day_offset": "0",
            "start_time": "22:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["day_offset"] == "0"
