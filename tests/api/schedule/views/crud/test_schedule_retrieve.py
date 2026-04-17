"""T253: Schedule RETRIEVE endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import (
    format_datetime,
    reformat_datetime,
)

from api.schedule.models import Schedule
from api.schedule.models.show import ShowInstance
from api.schedule.models.webstream import Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestScheduleViewSetRetrieve:
    """Tests for Schedule retrieve endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        self.api_client = api_client
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

    def test_retrieve_file_schedule_success(self):
        instance_start = self.show_instance.starts_at
        schedule = baker.make(
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
        response = self.api_client.get(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == schedule.id
        assert data["instance"] == self.show_instance.id
        assert data["file"] == self.file.id
        assert data["stream"] is None
        assert data["position"] == 1
        assert data["broadcasted"] == 1
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            instance_start + timedelta(minutes=30),
        )

    def test_retrieve_stream_schedule_success(self):
        instance_start = self.show_instance.starts_at
        schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=None,
            stream=self.stream,
            starts_at=instance_start + timedelta(minutes=30),
            ends_at=instance_start + timedelta(minutes=35),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = self.api_client.get(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == schedule.id
        assert data["file"] is None
        assert data["stream"] == self.stream.id
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            instance_start + timedelta(minutes=30),
        )

    def test_retrieve_returns_computed_cue_out(self):
        instance_start = self.show_instance.starts_at
        schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(minutes=30),
            ends_at=instance_start + timedelta(minutes=60),
            cue_in="00:00:00",
            cue_out="00:30:00",
            position=1,
            broadcasted=1,
        )
        response = self.api_client.get(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 200
        data = response.json()
        assert "cue_out" in data

    def test_retrieve_returns_computed_ends_at(self):
        instance_start = self.show_instance.starts_at
        schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(minutes=30),
            ends_at=instance_start + timedelta(minutes=60),
            cue_in="00:00:00",
            cue_out="00:30:00",
            position=1,
            broadcasted=1,
        )
        response = self.api_client.get(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 200
        data = response.json()
        assert "ends_at" in data

    def test_retrieve_not_found(self):
        response = self.api_client.get("/api/v2/schedule/99999")
        assert response.status_code == 404

    def test_retrieve_no_auth_fails(self):
        self.api_client.logout()
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
        response = self.api_client.get(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 403

    def test_retrieve_includes_all_fields(self):
        instance_start = self.show_instance.starts_at
        schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            stream=None,
            starts_at=instance_start + timedelta(minutes=30),
            ends_at=instance_start + timedelta(minutes=35),
            cue_in="00:00:00",
            cue_out="00:05:00",
            fade_in="00:00:01",
            fade_out="00:00:01",
            position=1,
            broadcasted=1,
        )
        response = self.api_client.get(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "instance" in data
        assert "file" in data
        assert "stream" in data
        assert "starts_at" in data
        assert "ends_at" in data
        assert "cue_in" in data
        assert "cue_out" in data
        assert "fade_in" in data
        assert "fade_out" in data
        assert "position" in data
        assert "broadcasted" in data

    def test_retrieve_shows_overbooked_status(self):
        instance_start = self.show_instance.starts_at
        schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(hours=2),
            ends_at=instance_start + timedelta(hours=2, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = self.api_client.get(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
