"""T255: Schedule DELETE endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.schedule.models import Schedule
from api.schedule.models.show import ShowInstance
from api.schedule.models.webstream import Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestScheduleViewSetDelete:
    """Tests for Schedule delete endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self, admin_client, admin_user):
        self.admin_client = admin_client
        self.user = admin_user
        show = baker.make("schedule.Show", name="Test Show")
        instance_start = now()
        self.show_instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=instance_start,
            ends_at=instance_start + timedelta(hours=2),
        )
        self.file = baker.make(File, mime="audio/mp3")
        self.stream = baker.make(
            Webstream,
            name="Test Stream",
            owner=self.user,
        )
        self.schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            stream=None,
            starts_at=instance_start + timedelta(minutes=30),
            ends_at=instance_start + timedelta(minutes=35),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

    def test_delete_file_schedule_success(self):
        schedule_id = self.schedule.id
        response = self.admin_client.delete(f"/api/v2/schedule/{schedule_id}")
        assert response.status_code == 204
        assert Schedule.objects.filter(id=schedule_id).count() == 0

    def test_delete_stream_schedule_success(self):
        instance_start = self.show_instance.starts_at
        stream_schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=None,
            stream=self.stream,
            starts_at=instance_start + timedelta(minutes=40),
            ends_at=instance_start + timedelta(minutes=45),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        schedule_id = stream_schedule.id
        response = self.admin_client.delete(f"/api/v2/schedule/{schedule_id}")
        assert response.status_code == 204
        assert Schedule.objects.filter(id=schedule_id).count() == 0

    def test_delete_not_found(self):
        response = self.admin_client.delete("/api/v2/schedule/99999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        self.admin_client.logout()
        response = self.admin_client.delete(
            f"/api/v2/schedule/{self.schedule.id}",
        )
        assert response.status_code == 403

    def test_delete_other_schedules_preserved(self):
        instance_start = self.show_instance.starts_at
        schedule2 = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            stream=None,
            starts_at=instance_start + timedelta(minutes=50),
            ends_at=instance_start + timedelta(minutes=55),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        response = self.admin_client.delete(
            f"/api/v2/schedule/{self.schedule.id}",
        )
        assert response.status_code == 204
        assert Schedule.objects.filter(id=schedule2.id).count() == 1
