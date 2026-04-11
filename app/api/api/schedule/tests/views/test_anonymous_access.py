"""Anonymous access tests - all endpoints should return 403.

Tests that unauthenticated users receive 403 Forbidden on all operations.
"""

from datetime import timedelta

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.schedule.models import (
    Playlist,
    Schedule,
    Show,
    ShowHost,
    ShowInstance,
)
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleAnonymousAccess:
    """Anonymous access tests for Schedule endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, faker):
        """Set up test data."""
        self.client = APIClient()
        user = baker.make(User, username=f"anon_sched_{faker.uuid4()[:8]}")
        show = baker.make(Show, name=f"Test Show {faker.uuid4()[:8]}")
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        self.schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=now(),
            ends_at=now() + timedelta(minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

    def test_list_returns_403(self):
        """Anonymous LIST should return 403."""
        response = self.client.get("/api/v2/schedule")
        assert response.status_code == 403

    def test_retrieve_returns_403(self):
        """Anonymous RETRIEVE should return 403."""
        response = self.client.get(f"/api/v2/schedule/{self.schedule.id}")
        assert response.status_code == 403

    def test_create_returns_403(self):
        """Anonymous CREATE should return 403."""
        response = self.client.post(
            "/api/v2/schedule",
            {
                "instance": self.schedule.instance.id,
                "file": self.schedule.file.id,
                "starts_at": "2026-04-11T10:00:00Z",
                "ends_at": "2026-04-11T10:05:00Z",
                "cue_in": "00:00:00",
                "cue_out": "00:05:00",
                "position": 1,
                "broadcasted": 1,
            },
            format="json",
        )
        assert response.status_code == 403

    def test_update_returns_403(self):
        """Anonymous UPDATE should return 403."""
        response = self.client.patch(
            f"/api/v2/schedule/{self.schedule.id}",
            {"position": 2},
            format="json",
        )
        assert response.status_code == 403

    def test_delete_returns_403(self):
        """Anonymous DELETE should return 403."""
        response = self.client.delete(f"/api/v2/schedule/{self.schedule.id}")
        assert response.status_code == 403


@pytest.mark.django_db(transaction=True)
class TestShowHostAnonymousAccess:
    """Anonymous access tests for ShowHost endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, faker):
        """Set up test data."""
        self.client = APIClient()
        user = baker.make(User, username=f"anon_host_{faker.uuid4()[:8]}")
        show = baker.make(Show, name=f"Test Show {faker.uuid4()[:8]}")
        self.show_host = baker.make(ShowHost, show=show, user=user)

    def test_list_returns_403(self):
        """Anonymous LIST should return 403."""
        response = self.client.get("/api/v2/show-hosts")
        assert response.status_code == 403

    def test_retrieve_returns_403(self):
        """Anonymous RETRIEVE should return 403."""
        response = self.client.get(f"/api/v2/show-hosts/{self.show_host.id}")
        assert response.status_code == 403

    def test_create_returns_403(self):
        """Anonymous CREATE should return 403."""
        response = self.client.post(
            "/api/v2/show-hosts",
            {"show": self.show_host.show.id, "user": self.show_host.user.id},
            format="json",
        )
        assert response.status_code == 403

    def test_update_returns_403(self):
        """Anonymous UPDATE should return 403."""
        response = self.client.patch(
            f"/api/v2/show-hosts/{self.show_host.id}",
            {},
            format="json",
        )
        assert response.status_code == 403

    def test_delete_returns_403(self):
        """Anonymous DELETE should return 403."""
        response = self.client.delete(
            f"/api/v2/show-hosts/{self.show_host.id}",
        )
        assert response.status_code == 403


@pytest.mark.django_db(transaction=True)
class TestPlaylistAnonymousAccess:
    """Anonymous access tests for Playlist endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, faker):
        """Set up test data."""
        self.client = APIClient()
        user = baker.make(User, username=f"anon_pl_{faker.uuid4()[:8]}")
        self.playlist = baker.make(
            Playlist, name=f"Test Playlist {faker.uuid4()[:8]}", owner=user,
        )

    def test_list_returns_403(self):
        """Anonymous LIST should return 403."""
        response = self.client.get("/api/v2/playlists")
        assert response.status_code == 403

    def test_retrieve_returns_403(self):
        """Anonymous RETRIEVE should return 403."""
        response = self.client.get(f"/api/v2/playlists/{self.playlist.id}")
        assert response.status_code == 403

    def test_create_returns_403(self):
        """Anonymous CREATE should return 403."""
        response = self.client.post(
            "/api/v2/playlists",
            {"name": "New Playlist"},
            format="json",
        )
        assert response.status_code == 403

    def test_update_returns_403(self):
        """Anonymous UPDATE should return 403."""
        response = self.client.patch(
            f"/api/v2/playlists/{self.playlist.id}",
            {"name": "Updated Playlist"},
            format="json",
        )
        assert response.status_code == 403

    def test_delete_returns_403(self):
        """Anonymous DELETE should return 403."""
        response = self.client.delete(f"/api/v2/playlists/{self.playlist.id}")
        assert response.status_code == 403
