"""T260: PlayoutHistory CREATE endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import (
    format_datetime,
    reformat_datetime,
)

from api.schedule.models import Show
from api.schedule.models.show import ShowInstance
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestPlayoutHistoryViewSetCreate:
    """Test PlayoutHistory CREATE endpoint - POST /api/v2/playout-history."""

    @pytest.fixture(autouse=True)
    def setup(self, admin_client, admin_user):
        """Set up test fixtures."""
        self.admin_client = admin_client
        self.user = admin_user
        show = baker.make(Show, name="Test Show")
        instance_start = now()
        self.show_instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=instance_start,
            ends_at=instance_start + timedelta(hours=2),
        )
        self.file = baker.make(File, mime="audio/mp3", owner=self.user)
        self.history_start = now() + timedelta(hours=2)
        self.history_end = self.history_start + timedelta(minutes=5)

    def test_create_file_playout_success(self):
        """Successfully create playout history for file."""
        data = {
            "file": self.file.id,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["file"] == self.file.id
        assert reformat_datetime(data["starts"]) == format_datetime(
            self.history_start,
        )
        assert reformat_datetime(data["ends"]) == format_datetime(
            self.history_end,
        )

    def test_create_with_instance_success(self):
        """Successfully create playout history linked to show instance."""
        data = {
            "file": self.file.id,
            "instance": self.show_instance.id,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["instance"] == self.show_instance.id
        assert reformat_datetime(data["starts"]) == format_datetime(
            self.history_start,
        )

    def test_create_without_ends_success(self):
        """Successfully create playout history without ends (currently playing)."""
        data = {
            "file": self.file.id,
            "starts": format_datetime(self.history_start),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert reformat_datetime(data["starts"]) == format_datetime(
            self.history_start,
        )
        assert data["ends"] is None

    def test_create_missing_file_success(self):
        """Create without file (stream playout) should work."""
        data = {
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["file"] is None

    def test_create_missing_starts_fails(self):
        """Create without starts should fail."""
        data = {
            "file": self.file.id,
            "ends": format_datetime(self.history_end),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_invalid_file_fails(self):
        """Create with non-existent file should fail."""
        data = {
            "file": 99999,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_invalid_instance_fails(self):
        """Create with non-existent instance should fail."""
        data = {
            "file": self.file.id,
            "instance": 99999,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self):
        """Create without authentication should fail."""
        self.admin_client.logout()
        data = {
            "file": self.file.id,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_create_ends_before_starts_fails(self):
        """Create with ends before starts should fail validation."""
        data = {
            "file": self.file.id,
            "starts": format_datetime(self.history_end),
            "ends": format_datetime(self.history_start),
        }
        response = self.admin_client.post(
            "/api/v2/playout-history",
            data,
            format="json",
        )
        assert response.status_code == 400
