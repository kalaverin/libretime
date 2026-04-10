"""T254: Schedule UPDATE endpoint tests."""

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
class TestScheduleViewSetUpdate:
    """Tests for Schedule update endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        self.api_client = api_client
        self.user = admin_user
        show = baker.make("schedule.Show", name="Test Show")
        start_time = now()
        self.show_instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=2),
        )
        self.file = baker.make(File, mime="audio/mp3")
        self.file2 = baker.make(File, mime="audio/mp3")
        self.stream = baker.make(
            Webstream,
            name="Test Stream",
            owner=self.user,
        )
        self.stream2 = baker.make(
            Webstream,
            name="Test Stream 2",
            owner=self.user,
        )
        self.schedule_start = now()
        self.schedule_end = self.schedule_start + timedelta(minutes=5)
        self.schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            stream=None,
            starts_at=self.schedule_start,
            ends_at=self.schedule_end,
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

    def test_update_file_to_stream_success(self):
        data = {
            "instance": self.show_instance.id,
            "file": None,
            "stream": self.stream.id,
            "starts_at": format_datetime(self.schedule_start),
            "ends_at": format_datetime(self.schedule_end),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file"] is None
        assert data["stream"] == self.stream.id

    def test_update_stream_to_file_success(self):
        stream_schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=None,
            stream=self.stream,
            starts_at=self.schedule_start + timedelta(minutes=10),
            ends_at=self.schedule_start + timedelta(minutes=15),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "stream": None,
            "starts_at": format_datetime(
                self.schedule_start + timedelta(minutes=10),
            ),
            "ends_at": format_datetime(
                self.schedule_start + timedelta(minutes=15),
            ),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 2,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{stream_schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file"] == self.file.id
        assert data["stream"] is None

    @pytest.mark.xfail(
        raises=AssertionError,
        reason="T352: ends_at not saved via API due to get_ends_at() method conflict",
    )
    def test_update_change_times_success(self):
        """Test updating schedule times.

        Note: This test is expected to fail due to T352 - DRF does not correctly
        handle the ends_at field when there's a get_ends_at method on the model.
        """
        new_start = self.schedule_start + timedelta(minutes=30)
        new_end = self.schedule_start + timedelta(minutes=35)
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "stream": None,
            "starts_at": format_datetime(new_start),
            "ends_at": format_datetime(new_end),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        response_start = reformat_datetime(data["starts_at"])
        response_end = reformat_datetime(data["ends_at"])
        assert response_start == format_datetime(new_start)
        assert response_end == format_datetime(new_end)

    def test_update_change_file_success(self):
        data = {
            "instance": self.show_instance.id,
            "file": self.file2.id,
            "stream": None,
            "starts_at": format_datetime(self.schedule_start),
            "ends_at": format_datetime(self.schedule_end),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file"] == self.file2.id

    def test_update_change_stream_success(self):
        stream_schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=None,
            stream=self.stream,
            starts_at=self.schedule_start + timedelta(minutes=10),
            ends_at=self.schedule_start + timedelta(minutes=15),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        data = {
            "instance": self.show_instance.id,
            "file": None,
            "stream": self.stream2.id,
            "starts_at": format_datetime(
                self.schedule_start + timedelta(minutes=10),
            ),
            "ends_at": format_datetime(
                self.schedule_start + timedelta(minutes=15),
            ),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 2,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{stream_schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stream"] == self.stream2.id

    def test_update_partial_change_position(self):
        data = {"position": 5}
        response = self.api_client.patch(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 5

    def test_update_partial_change_broadcasted(self):
        data = {"broadcasted": 0}
        response = self.api_client.patch(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["broadcasted"] == 0

    @pytest.mark.xfail(
        raises=AssertionError, reason="T337: cue_out not updated via API",
    )
    def test_update_change_cue_times(self):
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "stream": None,
            "starts_at": format_datetime(self.schedule_start),
            "ends_at": format_datetime(
                self.schedule_start + timedelta(minutes=10),
            ),
            "cue_in": "00:00:05",
            "cue_out": "00:10:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cue_in"] == "00:00:05"
        assert data["cue_out"] == "00:10:00"

    def test_update_invalid_instance_fails(self):
        data = {
            "instance": 99999,
            "file": self.file.id,
            "stream": None,
            "starts_at": format_datetime(self.schedule_start),
            "ends_at": format_datetime(self.schedule_end),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_update_not_found(self):
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "stream": None,
            "starts_at": format_datetime(self.schedule_start),
            "ends_at": format_datetime(self.schedule_end),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            "/api/v2/schedule/99999",
            data,
            format="json",
        )
        assert response.status_code == 404

    def test_update_no_auth_fails(self):
        self.api_client.logout()
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "stream": None,
            "starts_at": format_datetime(self.schedule_start),
            "ends_at": format_datetime(self.schedule_end),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_update_fade_times(self):
        data = {
            "instance": self.show_instance.id,
            "file": self.file.id,
            "stream": None,
            "starts_at": format_datetime(self.schedule_start),
            "ends_at": format_datetime(self.schedule_end),
            "cue_in": "00:00:00",
            "cue_out": "00:05:00",
            "fade_in": "00:00:02",
            "fade_out": "00:00:02",
            "position": 1,
            "broadcasted": 1,
        }
        response = self.api_client.put(
            f"/api/v2/schedule/{self.schedule.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fade_in"] == "00:00:02"
        assert data["fade_out"] == "00:00:02"
