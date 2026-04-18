"""T257: Schedule overbooked filter endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime

from api.schedule.models import Schedule
from api.schedule.models.show import ShowInstance
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestScheduleViewSetOverbookedFilter:
    """Tests for Schedule overbooked filter."""

    @pytest.fixture(autouse=True)
    def setup(self, guest_client, admin_user):
        self.guest_client = guest_client
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

    def test_filter_overbooked_true(self):
        instance_start = self.show_instance.starts_at
        normal_schedule = baker.make(
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
        overbooked_schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(hours=2),
            ends_at=instance_start + timedelta(hours=2, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        response = self.guest_client.get("/api/v2/schedule?overbooked=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == overbooked_schedule.id

    def test_filter_overbooked_false(self):
        instance_start = self.show_instance.starts_at
        normal_schedule = baker.make(
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
        overbooked_schedule = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(hours=2),
            ends_at=instance_start + timedelta(hours=2, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        response = self.guest_client.get("/api/v2/schedule?overbooked=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == normal_schedule.id

    def test_filter_overbooked_no_results(self):
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
        response = self.guest_client.get("/api/v2/schedule?overbooked=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_filter_overbooked_combines_with_time_filters(self):
        instance_start = self.show_instance.starts_at
        baker.make(
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
        overbooked_before = baker.make(
            Schedule,
            instance=self.show_instance,
            file=self.file,
            starts_at=instance_start + timedelta(hours=2, minutes=15),
            ends_at=instance_start + timedelta(hours=2, minutes=20),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=2,
            broadcasted=1,
        )
        response = self.guest_client.get(
            f"/api/v2/schedule?overbooked=1&starts_after={format_datetime(instance_start + timedelta(hours=2, minutes=10))}",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == overbooked_before.id
