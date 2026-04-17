"""T266: LiveLog endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime, reformat_datetime

from api.history.models import LiveLog
from sdk import now


@pytest.mark.django_db
class TestLiveLogViewSet:
    """Test LiveLog LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

    def setup_method(self):
        """Clean up LiveLog before each test."""
        LiveLog.objects.all().delete()

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        """Set up test fixtures."""
        self.api_client = api_client
        self.user = admin_user

    # === LIST Tests ===

    def test_list_empty_returns_200(self):
        """LIST empty should return 200 with empty list."""
        response = self.api_client.get("/api/v2/live-logs")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_log(self):
        """LIST should return single live log."""
        start_time = now()
        end_time = start_time + timedelta(hours=1)
        log = baker.make(
            LiveLog,
            state="connected",
            start_time=start_time,
            end_time=end_time,
        )

        response = self.api_client.get("/api/v2/live-logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["state"] == "connected"
        assert reformat_datetime(data[0]["start_time"]) == format_datetime(
            start_time,
        )
        assert reformat_datetime(data[0]["end_time"]) == format_datetime(
            end_time,
        )

    def test_list_multiple_logs(self):
        """LIST should return multiple logs."""
        baker.make(
            LiveLog,
            state="connected",
            start_time=now(),
            end_time=now() + timedelta(hours=1),
        )
        baker.make(
            LiveLog,
            state="disconnected",
            start_time=now() + timedelta(hours=2),
            end_time=None,
        )

        response = self.api_client.get("/api/v2/live-logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_log_without_end(self):
        """LIST should handle ongoing live stream (no end_time)."""
        log = baker.make(
            LiveLog,
            state="connected",
            start_time=now(),
            end_time=None,
        )

        response = self.api_client.get("/api/v2/live-logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["end_time"] is None

    def test_list_no_auth_fails(self):
        """LIST without auth should fail."""
        self.api_client.logout()
        response = self.api_client.get("/api/v2/live-logs")
        assert response.status_code == 403

    # === CREATE Tests ===

    def test_create_log_success(self):
        """Successfully create live log."""
        start_time = now()
        data = {
            "state": "connected",
            "start_time": format_datetime(start_time),
            "end_time": format_datetime(start_time + timedelta(hours=1)),
        }

        response = self.api_client.post(
            "/api/v2/live-logs",
            data,
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["state"] == "connected"
        assert reformat_datetime(data["start_time"]) == format_datetime(
            start_time,
        )
        assert reformat_datetime(data["end_time"]) == format_datetime(
            start_time + timedelta(hours=1),
        )

    def test_create_without_end_success(self):
        """Create without end_time (ongoing)."""
        data = {
            "state": "connected",
            "start_time": format_datetime(now()),
        }

        response = self.api_client.post(
            "/api/v2/live-logs",
            data,
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["state"] == "connected"
        assert data["end_time"] is None

    def test_create_missing_state_fails(self):
        """Create without state should fail."""
        data = {
            "start_time": format_datetime(now()),
        }

        response = self.api_client.post(
            "/api/v2/live-logs",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_missing_start_time_fails(self):
        """Create without start_time should fail."""
        data = {
            "state": "connected",
        }

        response = self.api_client.post(
            "/api/v2/live-logs",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self):
        """Create without auth should fail."""
        self.api_client.logout()
        data = {
            "state": "connected",
            "start_time": format_datetime(now()),
        }

        response = self.api_client.post(
            "/api/v2/live-logs",
            data,
            format="json",
        )
        assert response.status_code == 403

    # === RETRIEVE Tests ===

    def test_retrieve_log_success(self):
        """Successfully retrieve live log."""
        start_time = now()
        end_time = start_time + timedelta(hours=1)
        log = baker.make(
            LiveLog,
            state="disconnected",
            start_time=start_time,
            end_time=end_time,
        )

        response = self.api_client.get(f"/api/v2/live-logs/{log.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log.id
        assert data["state"] == "disconnected"
        assert reformat_datetime(data["start_time"]) == format_datetime(
            start_time,
        )
        assert reformat_datetime(data["end_time"]) == format_datetime(end_time)

    def test_retrieve_not_found(self):
        """Return 404 for non-existent log."""
        response = self.api_client.get("/api/v2/live-logs/99999")
        assert response.status_code == 404

    # === UPDATE Tests ===

    def test_update_state_success(self):
        """Successfully update state."""
        start_time = now()
        end_time = start_time + timedelta(hours=1)
        log = baker.make(
            LiveLog,
            state="connected",
            start_time=start_time,
            end_time=None,
        )

        data = {
            "state": "disconnected",
            "start_time": format_datetime(start_time),
            "end_time": format_datetime(end_time),
        }

        response = self.api_client.put(
            f"/api/v2/live-logs/{log.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "disconnected"
        assert reformat_datetime(data["start_time"]) == format_datetime(
            start_time,
        )
        assert reformat_datetime(data["end_time"]) == format_datetime(end_time)

    def test_update_partial_end_time(self):
        """Partial update end_time with PATCH."""
        start_time = now()
        end_time = start_time + timedelta(hours=1)
        log = baker.make(
            LiveLog,
            state="connected",
            start_time=start_time,
            end_time=None,
        )

        data = {"end_time": format_datetime(end_time)}

        response = self.api_client.patch(
            f"/api/v2/live-logs/{log.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert reformat_datetime(data["start_time"]) == format_datetime(
            start_time,
        )
        assert reformat_datetime(data["end_time"]) == format_datetime(end_time)
        assert data["state"] == "connected"  # Unchanged

    # === DELETE Tests ===

    def test_delete_log_success(self):
        """Successfully delete live log."""
        log = baker.make(
            LiveLog,
            state="test",
            start_time=now(),
        )

        response = self.api_client.delete(f"/api/v2/live-logs/{log.id}")

        assert response.status_code == 204
        assert LiveLog.objects.filter(id=log.id).count() == 0

    def test_delete_not_found(self):
        """Delete non-existent returns 404."""
        response = self.api_client.delete("/api/v2/live-logs/99999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        """Delete without auth fails."""
        log = baker.make(
            LiveLog,
            state="test",
            start_time=now(),
        )

        self.api_client.logout()
        response = self.api_client.delete(f"/api/v2/live-logs/{log.id}")
        assert response.status_code == 403
