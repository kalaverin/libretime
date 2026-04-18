"""T259: PlayoutHistory LIST endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import (
    format_datetime,
    reformat_datetime,
)

from api.history.models import PlayoutHistory
from api.schedule.models import Show
from api.schedule.models.show import ShowInstance
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestPlayoutHistoryViewSetList:
    """Test PlayoutHistory LIST endpoint - GET /api/v2/playout-history."""

    def test_list_empty_returns_200(self, admin_client):
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        assert response.json() == []

    def test_list_single_file_playout(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        history_start = now()
        history_end = history_start + timedelta(minutes=5)
        history = baker.make(
            PlayoutHistory,
            file=file_obj,
            starts=history_start,
            ends=history_end,
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        data = response.json()
        assert len(data) == 1
        assert data[0]["file"] == file_obj.id
        assert reformat_datetime(data[0]["starts"]) == format_datetime(
            history_start,
        )
        assert reformat_datetime(data[0]["ends"]) == format_datetime(
            history_end,
        )

    def test_list_multiple_playouts(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file1 = baker.make(
            File,
            name="test1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="test2.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start1 = now()
        start2 = start1 + timedelta(minutes=5)
        baker.make(
            PlayoutHistory,
            file=file1,
            starts=start1,
            ends=start1 + timedelta(minutes=5),
        )
        baker.make(
            PlayoutHistory,
            file=file2,
            starts=start2,
            ends=start2 + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        data = response.json()
        assert len(data) == 2

    def test_list_playout_with_instance(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        history = baker.make(
            PlayoutHistory,
            file=file_obj,
            instance=instance,
            starts=start_time,
            ends=start_time + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        data = response.json()
        assert len(data) == 1
        assert data[0]["instance"] == instance.id

    def test_list_playout_without_ends(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(PlayoutHistory, file=file_obj, starts=start_time, ends=None)
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        data = response.json()
        assert len(data) == 1
        assert data[0]["ends"] is None

    def test_list_returns_all_fields(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            PlayoutHistory,
            file=file_obj,
            starts=start_time,
            ends=start_time + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        data = response.json()
        assert "id" in data[0]
        assert "file" in data[0]
        assert "starts" in data[0]
        assert "ends" in data[0]
        assert "instance" in data[0]

    def test_list_no_auth_fails(self, admin_client):
        admin_client.logout()
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403

    def test_list_pagination_respected(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        base_time = now()
        for i in range(5):
            file_obj = baker.make(
                File,
                name=f"test{i}.mp3",
                mime="audio/mp3",
                owner=user,
            )
            start = base_time + timedelta(minutes=i)
            baker.make(
                PlayoutHistory,
                file=file_obj,
                starts=start,
                ends=start + timedelta(minutes=1),
            )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        data = response.json()
        assert len(data) == 5

    def test_list_ordered_by_starts(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file1 = baker.make(
            File,
            name="test1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="test2.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start1 = now() + timedelta(hours=2)
        start2 = now()
        baker.make(
            PlayoutHistory,
            file=file2,
            starts=start1,
            ends=start1 + timedelta(minutes=5),
        )
        baker.make(
            PlayoutHistory,
            file=file1,
            starts=start2,
            ends=start2 + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403
        data = response.json()
        assert len(data) == 2


@pytest.mark.django_db
class TestPlayoutHistoryViewSetList:
    """Test PlayoutHistory LIST endpoint - GET /api/v2/playout-history."""

    def test_list_empty_returns_200(self, admin_client):
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_file_playout(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        history_start = now()
        history_end = history_start + timedelta(minutes=5)
        history = baker.make(
            PlayoutHistory,
            file=file_obj,
            starts=history_start,
            ends=history_end,
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["file"] == file_obj.id
        assert reformat_datetime(data[0]["starts"]) == format_datetime(
            history_start,
        )
        assert reformat_datetime(data[0]["ends"]) == format_datetime(
            history_end,
        )

    def test_list_multiple_playouts(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file1 = baker.make(
            File,
            name="test1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="test2.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start1 = now()
        start2 = start1 + timedelta(minutes=5)
        baker.make(
            PlayoutHistory,
            file=file1,
            starts=start1,
            ends=start1 + timedelta(minutes=5),
        )
        baker.make(
            PlayoutHistory,
            file=file2,
            starts=start2,
            ends=start2 + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_playout_with_instance(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        history = baker.make(
            PlayoutHistory,
            file=file_obj,
            instance=instance,
            starts=start_time,
            ends=start_time + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["instance"] == instance.id

    def test_list_playout_without_ends(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(PlayoutHistory, file=file_obj, starts=start_time, ends=None)
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ends"] is None

    def test_list_returns_all_fields(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start_time = now()
        baker.make(
            PlayoutHistory,
            file=file_obj,
            starts=start_time,
            ends=start_time + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data[0]
        assert "file" in data[0]
        assert "starts" in data[0]
        assert "ends" in data[0]
        assert "instance" in data[0]

    def test_list_no_auth_fails(self, admin_client):
        admin_client.logout()
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 403

    def test_list_pagination_respected(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        base_time = now()
        for i in range(5):
            file_obj = baker.make(
                File,
                name=f"test{i}.mp3",
                mime="audio/mp3",
                owner=user,
            )
            start = base_time + timedelta(minutes=i)
            baker.make(
                PlayoutHistory,
                file=file_obj,
                starts=start,
                ends=start + timedelta(minutes=1),
            )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_list_ordered_by_starts(self, admin_client):
        user = baker.make("core.User", username="testhistory_user")
        file1 = baker.make(
            File,
            name="test1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="test2.mp3",
            mime="audio/mp3",
            owner=user,
        )
        start1 = now() + timedelta(hours=2)
        start2 = now()
        baker.make(
            PlayoutHistory,
            file=file2,
            starts=start1,
            ends=start1 + timedelta(minutes=5),
        )
        baker.make(
            PlayoutHistory,
            file=file1,
            starts=start2,
            ends=start2 + timedelta(minutes=5),
        )
        response = admin_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
