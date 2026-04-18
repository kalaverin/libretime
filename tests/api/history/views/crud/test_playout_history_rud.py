"""T261: PlayoutHistory RETRIEVE, UPDATE, DELETE endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime, reformat_datetime

from api.history.models import PlayoutHistory
from api.schedule.models import Show
from api.schedule.models.show import ShowInstance
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestPlayoutHistoryViewSetRUD:
    """Test PlayoutHistory RETRIEVE, UPDATE, DELETE endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, admin_client, admin_user):
        """Set up test fixtures."""
        self.admin_client = admin_client
        self.user = admin_user

        # Create show and instance with aware datetime
        show = baker.make(Show, name="Test Show")
        instance_start = now()
        instance_end = instance_start + timedelta(hours=2)
        self.show_instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=instance_start,
            ends_at=instance_end,
        )

        # Create files
        self.file = baker.make(File, mime="audio/mp3", owner=self.user)
        self.file2 = baker.make(File, mime="audio/mp3", owner=self.user)

        # Create base playout history with aware datetime
        self.history_start = now()
        self.history_end = self.history_start + timedelta(minutes=5)
        self.history = baker.make(
            PlayoutHistory,
            file=self.file,
            instance=self.show_instance,
            starts=self.history_start,
            ends=self.history_end,
        )

    # === RETRIEVE Tests ===

    def test_retrieve_file_playout_success(self):
        """Successfully retrieve file playout history."""
        response = self.admin_client.get(
            f"/api/v2/playout-history/{self.history.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.history.id
        assert data["file"] == self.file.id
        assert reformat_datetime(data["starts"]) == format_datetime(
            self.history_start,
        )
        assert reformat_datetime(data["ends"]) == format_datetime(
            self.history_end,
        )

    def test_retrieve_not_found(self):
        """Return 404 for non-existent playout history."""
        response = self.admin_client.get("/api/v2/playout-history/99999")
        assert response.status_code == 404

    def test_retrieve_no_auth_fails(self):
        """Return 403 without authentication."""
        self.admin_client.logout()
        response = self.admin_client.get(
            f"/api/v2/playout-history/{self.history.id}",
        )
        assert response.status_code == 403

    def test_retrieve_includes_all_fields(self):
        """Retrieve includes all playout history fields."""
        response = self.admin_client.get(
            f"/api/v2/playout-history/{self.history.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "file" in data
        assert "instance" in data
        assert "starts" in data
        assert "ends" in data

    # === UPDATE Tests ===

    def test_update_change_file_success(self):
        """Successfully update playout to different file."""
        data = {
            "file": self.file2.id,
            "instance": self.show_instance.id,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }

        response = self.admin_client.put(
            f"/api/v2/playout-history/{self.history.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["file"] == self.file2.id

    def test_update_change_times_success(self):
        """Successfully update playout times."""
        new_start = self.history_start + timedelta(hours=2)
        new_end = new_start + timedelta(minutes=5)
        data = {
            "file": self.file.id,
            "instance": self.show_instance.id,
            "starts": format_datetime(new_start),
            "ends": format_datetime(new_end),
        }

        response = self.admin_client.put(
            f"/api/v2/playout-history/{self.history.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert reformat_datetime(data["starts"]) == format_datetime(new_start)
        assert reformat_datetime(data["ends"]) == format_datetime(new_end)

    def test_update_partial_change_ends(self):
        """Partial update ends with PATCH."""
        new_end = self.history_end + timedelta(minutes=5)
        data = {
            "ends": format_datetime(new_end),
        }

        response = self.admin_client.patch(
            f"/api/v2/playout-history/{self.history.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert reformat_datetime(data["ends"]) == format_datetime(new_end)
        assert data["file"] == self.file.id  # Unchanged

    def test_update_invalid_file_fails(self):
        """Update with invalid file fails with 400."""
        data = {
            "file": 99999,
            "instance": self.show_instance.id,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }

        response = self.admin_client.put(
            f"/api/v2/playout-history/{self.history.id}",
            data,
            format="json",
        )

        assert response.status_code == 400

    def test_update_not_found(self):
        """Update non-existent playout returns 404."""
        data = {
            "file": self.file.id,
            "instance": self.show_instance.id,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }

        response = self.admin_client.put(
            "/api/v2/playout-history/99999",
            data,
            format="json",
        )
        assert response.status_code == 404

    def test_update_no_auth_fails(self):
        """Update without authentication returns 403."""
        self.admin_client.logout()
        data = {
            "file": self.file.id,
            "instance": self.show_instance.id,
            "starts": format_datetime(self.history_start),
            "ends": format_datetime(self.history_end),
        }

        response = self.admin_client.put(
            f"/api/v2/playout-history/{self.history.id}",
            data,
            format="json",
        )
        assert response.status_code == 403

    # === DELETE Tests ===

    def test_delete_playout_success(self):
        """Successfully delete playout history."""
        history_id = self.history.id
        response = self.admin_client.delete(
            f"/api/v2/playout-history/{history_id}",
        )

        assert response.status_code == 204
        assert PlayoutHistory.objects.filter(id=history_id).count() == 0

    def test_delete_not_found(self):
        """Delete non-existent playout returns 404."""
        response = self.admin_client.delete("/api/v2/playout-history/99999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        """Delete without authentication returns 403."""
        self.admin_client.logout()
        response = self.admin_client.delete(
            f"/api/v2/playout-history/{self.history.id}",
        )
        assert response.status_code == 403

    def test_delete_other_playouts_preserved(self):
        """Deleting one playout preserves others."""
        start_time = now().replace(minute=0, second=0, microsecond=0)
        history2 = baker.make(
            PlayoutHistory,
            file=self.file2,
            starts=start_time,
            ends=start_time + timedelta(minutes=5),
        )

        response = self.admin_client.delete(
            f"/api/v2/playout-history/{self.history.id}",
        )
        assert response.status_code == 204

        # Second should still exist
        assert PlayoutHistory.objects.filter(id=history2.id).count() == 1
