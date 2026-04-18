"""T256: Schedule permissions endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime

from api.schedule.models import Schedule
from api.schedule.models.show import ShowInstance
from api.schedule.models.webstream import Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestScheduleViewSetPermissions:
    """Tests for Schedule permission checks."""

    @pytest.fixture(autouse=True)
    def setup(self, guest_client, admin_user, host_client):
        self.guest_client = guest_client
        self.admin_user = admin_user
        self.host_client = host_client
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
            owner=admin_user,
        )

    def test_list_allows_anonymous(self, guest_client):
        response = guest_client.get("/api/v2/schedule")
        assert response.status_code == 200

    def test_create_requires_auth(self, guest_client):
        start_time = now()
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "starts_at": format_datetime(start_time),
            "ends_at": format_datetime(start_time + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = guest_client.post("/api/v2/schedule", data, format="json")
        assert response.status_code == 403

    def test_admin_can_create_schedule(self):
        start_time = now()
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "starts_at": format_datetime(start_time),
            "ends_at": format_datetime(start_time + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.guest_client.post(
            "/api/v2/schedule",
            data,
            format="json",
        )
        assert response.status_code == 201

    @pytest.mark.xfail(reason="T338: Host user cannot create schedule")
    def test_host_can_create_schedule(self):
        start_time = now()
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "starts_at": format_datetime(start_time),
            "ends_at": format_datetime(start_time + timedelta(minutes=5)),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.host_client.post(
            "/api/v2/schedule",
            data,
            format="json",
        )
        assert response.status_code == 201

    def test_admin_can_delete_schedule(self):
        instance_start = self.show_instance.starts_at
        schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(minutes=30),
            ends_at=instance_start + timedelta(minutes=35),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = self.guest_client.delete(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 204

    def test_list_admin_sees_all_schedules(self):
        instance_start = self.show_instance.starts_at
        baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(minutes=30),
            ends_at=instance_start + timedelta(minutes=35),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            stream=None,
            starts_at=instance_start + timedelta(minutes=40),
            ends_at=instance_start + timedelta(minutes=45),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        response = self.guest_client.get("/api/v2/schedule")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
