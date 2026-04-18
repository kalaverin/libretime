"""Tests for Schedule CREATE endpoint (T251-T252)."""

import json

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleViewSetCreate:
    """Test Schedule CREATE endpoint - POST /api/v2/schedule."""

    def setup_method(self):
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testsched").delete()

    def test_create_file_schedule_success(self, admin_client):
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
        response = admin_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "instance": instance.id,
                    "file": file_obj.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=5),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:05:00",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["file"] == file_obj.id
        assert data["instance"] == instance.id

    def test_create_stream_schedule_success(self, admin_client):
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
        response = admin_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "instance": instance.id,
                    "stream": stream.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=5),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:05:00",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["stream"] == stream.id
        assert data["file"] is None

    def test_create_with_cue_out_write_serializer(self, admin_client):
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
        response = admin_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "instance": instance.id,
                    "file": file_obj.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=5),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:04:30",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_create_missing_instance_fails(self, admin_client):
        user = baker.make(User, username="testsched_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        response = admin_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "file": file_obj.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=5),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:05:00",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_missing_file_and_stream_fails(self, admin_client):
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        start_time = now()
        response = admin_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "instance": instance.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=5),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:05:00",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_invalid_instance_fails(self, admin_client):
        user = baker.make(User, username="testsched_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        response = admin_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "instance": 999999,
                    "file": file_obj.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=5),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:05:00",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self, client):
        response = client.post(
            "/api/v2/schedule",
            json.dumps({"position": 1}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_with_fade_times(self, admin_client):
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
        response = admin_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "instance": instance.id,
                    "file": file_obj.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=5),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:05:00",
                    "fade_in": "00:00:02",
                    "fade_out": "00:00:03",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["fade_in"] == "00:00:02"
        assert data["fade_out"] == "00:00:03"
