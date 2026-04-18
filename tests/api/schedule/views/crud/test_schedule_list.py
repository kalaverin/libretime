"""Tests for Schedule LIST endpoint (T250)."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleViewSetList:
    """Test Schedule LIST endpoint - GET /api/v2/schedule."""

    def setup_method(self):
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testsched").delete()

    def test_list_empty_returns_200(self, guest_client):
        response = guest_client.get("/api/v2/schedule")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_file_schedule(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get("/api/v2/schedule")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["file"] == file_obj.id
        assert data[0]["instance"] == instance.id

    def test_list_single_stream_schedule(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance,
            stream=stream,
            file=None,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get("/api/v2/schedule")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["stream"] == stream.id
        assert data[0]["file"] is None

    def test_list_returns_computed_cue_out(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get("/api/v2/schedule")
        assert response.status_code == 200
        assert "cue_out" in response.json()[0]

    def test_list_returns_computed_ends_at(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get("/api/v2/schedule")
        assert response.status_code == 200
        assert "ends_at" in response.json()[0]

    def test_list_filter_by_instance(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance1 = baker.make(ShowInstance, show=show)
        instance2 = baker.make(ShowInstance, show=show)
        file1 = baker.make(
            File,
            name="file1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="file2.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance1,
            file=file1,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        baker.make(
            Schedule,
            instance=instance2,
            file=file2,
            starts_at=start_time + timedelta(minutes=10),
            ends_at=start_time + timedelta(minutes=15),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get(f"/api/v2/schedule?instance={instance1.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["instance"] == instance1.id

    def test_list_filter_starts_after(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get(
            f"/api/v2/schedule?starts_after={format_datetime(start_time - timedelta(hours=1))}",
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_filter_starts_before(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get(
            f"/api/v2/schedule?starts_before={format_datetime(start_time + timedelta(hours=1))}",
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_filter_overbooked(self, guest_client):
        user = baker.make(User, username="testsched_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )
        response = guest_client.get("/api/v2/schedule?overbooked=false")
        assert response.status_code == 200

    def test_list_no_auth_fails(self, client):
        response = client.get("/api/v2/schedule")
        assert response.status_code == 403
