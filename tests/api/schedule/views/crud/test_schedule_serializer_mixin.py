"""
T284: ReadWriteSerializerMixin behavior tests.

Tests that Schedule GET vs POST use different serializers.
Read excludes cue_out (uses computed), write allows it.
"""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime, reformat_datetime

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance
from api.storage.models import File, Library
from sdk import now


@pytest.mark.django_db
class TestReadWriteSerializerMixin:
    """Test that GET uses ReadScheduleSerializer and POST uses WriteScheduleSerializer."""

    @pytest.fixture
    def show_instance(self):
        """Create a show instance for testing."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        return baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=2),
        )

    @pytest.fixture
    def test_file(self):
        """Create a test file for scheduling."""
        library = baker.make(Library, name="Test Library", description="Test")
        user = baker.make(User, username="testuser")
        return baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

    def test_get_uses_read_serializer_with_computed_cue_out(
        self,
        guest_client,
        show_instance,
        test_file,
    ):
        """GET uses ReadScheduleSerializer which returns computed cue_out."""
        start_time = now()
        schedule = baker.make(
            Schedule,
            instance=show_instance,
            file=test_file,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=30),
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=30),
            position=1,
            broadcasted=1,
        )

        response = guest_client.get(f"/api/v2/schedule/{schedule.id}")

        assert response.status_code == 200
        data = response.json()
        # ReadScheduleSerializer includes computed cue_out
        assert "cue_out" in data
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T349)
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )

    def test_post_uses_write_serializer_allows_cue_out(
        self,
        guest_client,
        show_instance,
        test_file,
    ):
        """POST uses WriteScheduleSerializer which allows setting cue_out."""
        import json

        start_time = now()
        response = guest_client.post(
            "/api/v2/schedule",
            json.dumps(
                {
                    "instance": show_instance.id,
                    "file": test_file.id,
                    "starts_at": format_datetime(start_time),
                    "ends_at": format_datetime(
                        start_time + timedelta(minutes=30),
                    ),
                    "cue_in": "00:00:00",
                    "cue_out": "00:30:00",
                    "position": 1,
                    "broadcasted": 1,
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        # WriteScheduleSerializer allows setting cue_out
        assert data["cue_out"] == "00:30:00"
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T349)
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )

    def test_list_uses_read_serializer(
        self,
        guest_client,
        show_instance,
        test_file,
    ):
        """LIST (GET collection) uses ReadScheduleSerializer."""
        start_time = now()
        baker.make(
            Schedule,
            instance=show_instance,
            file=test_file,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=30),
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=30),
            position=1,
            broadcasted=1,
        )

        response = guest_client.get("/api/v2/schedule")

        assert response.status_code == 200
        data = response.json()
        # List returns array directly (no pagination wrapper)
        assert len(data) > 0
        # ReadScheduleSerializer used for list
        assert "cue_out" in data[0]
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T349)
        assert reformat_datetime(data[0]["starts_at"]) == format_datetime(
            start_time,
        )

    def test_patch_uses_write_serializer(
        self,
        guest_client,
        show_instance,
        test_file,
    ):
        """PATCH uses WriteScheduleSerializer (allows updates)."""
        import json

        start_time = now()
        schedule = baker.make(
            Schedule,
            instance=show_instance,
            file=test_file,
            starts_at=start_time,
            ends_at=start_time + timedelta(minutes=30),
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=30),
            position=1,
            broadcasted=1,
        )

        response = guest_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps(
                {
                    "position": 2,
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        # WriteSerializer allows updates
        assert data["position"] == 2
        # Reformat API response datetime - triggers TimezoneExpectedError if naive (T349)
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )
