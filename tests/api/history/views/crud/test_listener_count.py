"""T265: ListenerCount endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime

from api.history.models import ListenerCount, MountName, Timestamp
from sdk import now


@pytest.mark.django_db
class TestListenerCountViewSet:
    """Test ListenerCount LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        """Set up test fixtures."""
        self.api_client = api_client
        self.user = admin_user
        self.mount = baker.make(MountName, mount_name="/main")
        self.timestamp = baker.make(
            Timestamp,
            timestamp=format_datetime(now()),
        )

    def test_list_empty_returns_200(self):
        response = self.api_client.get("/api/v2/listener-counts")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_count(self):
        count = baker.make(
            ListenerCount,
            timestamp=self.timestamp,
            mount_name=self.mount,
            listener_count=42,
        )
        response = self.api_client.get("/api/v2/listener-counts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == self.timestamp.id
        assert data[0]["mount_name"] == self.mount.id
        assert data[0]["listener_count"] == 42

    def test_list_multiple_counts(self):
        mount2 = baker.make(MountName, mount_name="/live")
        timestamp2 = baker.make(
            Timestamp,
            timestamp=format_datetime(now() + timedelta(hours=1)),
        )
        baker.make(
            ListenerCount,
            timestamp=self.timestamp,
            mount_name=self.mount,
            listener_count=42,
        )
        baker.make(
            ListenerCount,
            timestamp=timestamp2,
            mount_name=mount2,
            listener_count=100,
        )
        response = self.api_client.get("/api/v2/listener-counts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_no_auth_fails(self):
        self.api_client.logout()
        response = self.api_client.get("/api/v2/listener-counts")
        assert response.status_code == 403

    def test_create_count_success(self):
        data = {
            "timestamp": self.timestamp.id,
            "mount_name": self.mount.id,
            "listener_count": 50,
        }
        response = self.api_client.post(
            "/api/v2/listener-counts",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["timestamp"] == self.timestamp.id
        assert data["mount_name"] == self.mount.id
        assert data["listener_count"] == 50

    def test_create_missing_timestamp_fails(self):
        data = {"mount_name": self.mount.id, "listener_count": 50}
        response = self.api_client.post(
            "/api/v2/listener-counts",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_missing_mount_fails(self):
        data = {"timestamp": self.timestamp.id, "listener_count": 50}
        response = self.api_client.post(
            "/api/v2/listener-counts",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_negative_count_allowed(self):
        data = {
            "timestamp": self.timestamp.id,
            "mount_name": self.mount.id,
            "listener_count": -5,
        }
        response = self.api_client.post(
            "/api/v2/listener-counts",
            data,
            format="json",
        )
        assert response.status_code == 201

    def test_create_no_auth_fails(self):
        self.api_client.logout()
        data = {
            "timestamp": self.timestamp.id,
            "mount_name": self.mount.id,
            "listener_count": 50,
        }
        response = self.api_client.post(
            "/api/v2/listener-counts",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_retrieve_count_success(self):
        count = baker.make(
            ListenerCount,
            timestamp=self.timestamp,
            mount_name=self.mount,
            listener_count=75,
        )
        response = self.api_client.get(f"/api/v2/listener-counts/{count.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == count.id
        assert data["listener_count"] == 75

    def test_retrieve_not_found(self):
        response = self.api_client.get("/api/v2/listener-counts/99999")
        assert response.status_code == 404

    def test_update_count_success(self):
        count = baker.make(
            ListenerCount,
            timestamp=self.timestamp,
            mount_name=self.mount,
            listener_count=10,
        )
        data = {
            "timestamp": self.timestamp.id,
            "mount_name": self.mount.id,
            "listener_count": 99,
        }
        response = self.api_client.put(
            f"/api/v2/listener-counts/{count.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["listener_count"] == 99

    def test_update_partial_count(self):
        count = baker.make(
            ListenerCount,
            timestamp=self.timestamp,
            mount_name=self.mount,
            listener_count=10,
        )
        data = {"listener_count": 55}
        response = self.api_client.patch(
            f"/api/v2/listener-counts/{count.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["listener_count"] == 55

    def test_delete_count_success(self):
        count = baker.make(
            ListenerCount,
            timestamp=self.timestamp,
            mount_name=self.mount,
            listener_count=10,
        )
        response = self.api_client.delete(
            f"/api/v2/listener-counts/{count.id}",
        )
        assert response.status_code == 204
        assert ListenerCount.objects.filter(id=count.id).count() == 0

    def test_delete_not_found(self):
        response = self.api_client.delete("/api/v2/listener-counts/99999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        count = baker.make(
            ListenerCount,
            timestamp=self.timestamp,
            mount_name=self.mount,
            listener_count=10,
        )
        self.api_client.logout()
        response = self.api_client.delete(
            f"/api/v2/listener-counts/{count.id}",
        )
        assert response.status_code == 403
