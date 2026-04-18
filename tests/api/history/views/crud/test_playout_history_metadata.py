"""T262: PlayoutHistoryMetadata endpoint tests."""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.history.models import PlayoutHistory, PlayoutHistoryMetadata
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestPlayoutHistoryMetadataViewSet:
    """Test PlayoutHistoryMetadata LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

    @pytest.fixture(autouse=True)
    def setup(self, admin_client, admin_user):
        """Set up test fixtures."""
        self.admin_client = admin_client
        self.user = admin_user
        self.file = baker.make(File, mime="audio/mp3", owner=self.user)
        start_time = now()
        self.history = baker.make(
            PlayoutHistory,
            file=self.file,
            starts=start_time,
            ends=start_time + timedelta(minutes=5),
        )

    def test_list_empty_returns_200(self):
        response = self.admin_client.get("/api/v2/playout-history-metadata")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_metadata(self):
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="artist",
            value="Test Artist",
        )
        response = self.admin_client.get("/api/v2/playout-history-metadata")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["history"] == self.history.id
        assert data[0]["key"] == "artist"
        assert data[0]["value"] == "Test Artist"

    def test_list_multiple_metadata(self):
        baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="artist",
            value="Artist 1",
        )
        baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="title",
            value="Song Title",
        )
        response = self.admin_client.get("/api/v2/playout-history-metadata")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_no_auth_fails(self):
        self.admin_client.logout()
        response = self.admin_client.get("/api/v2/playout-history-metadata")
        assert response.status_code == 403

    def test_create_metadata_success(self):
        data = {
            "history": self.history.id,
            "key": "album",
            "value": "Test Album",
        }
        response = self.admin_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["history"] == self.history.id
        assert data["key"] == "album"
        assert data["value"] == "Test Album"

    def test_create_missing_history_fails(self):
        data = {"key": "artist", "value": "Test"}
        response = self.admin_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_invalid_history_fails(self):
        data = {"history": 99999, "key": "artist", "value": "Test"}
        response = self.admin_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self):
        self.admin_client.logout()
        data = {"history": self.history.id, "key": "artist", "value": "Test"}
        response = self.admin_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_retrieve_metadata_success(self):
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="genre",
            value="Rock",
        )
        response = self.admin_client.get(
            f"/api/v2/playout-history-metadata/{metadata.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == metadata.id
        assert data["key"] == "genre"
        assert data["value"] == "Rock"

    def test_retrieve_not_found(self):
        response = self.admin_client.get(
            "/api/v2/playout-history-metadata/99999",
        )
        assert response.status_code == 404

    def test_update_value_success(self):
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="artist",
            value="Old Artist",
        )
        data = {
            "history": self.history.id,
            "key": "artist",
            "value": "New Artist",
        }
        response = self.admin_client.put(
            f"/api/v2/playout-history-metadata/{metadata.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "New Artist"

    def test_update_partial_value(self):
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="title",
            value="Old Title",
        )
        data = {"value": "New Title"}
        response = self.admin_client.patch(
            f"/api/v2/playout-history-metadata/{metadata.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "New Title"
        assert data["key"] == "title"

    def test_delete_metadata_success(self):
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="temp",
            value="value",
        )
        response = self.admin_client.delete(
            f"/api/v2/playout-history-metadata/{metadata.id}",
        )
        assert response.status_code == 204
        assert (
            PlayoutHistoryMetadata.objects.filter(id=metadata.id).count() == 0
        )

    def test_delete_not_found(self):
        response = self.admin_client.delete(
            "/api/v2/playout-history-metadata/99999",
        )
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=self.history,
            key="test",
            value="value",
        )
        self.admin_client.logout()
        response = self.admin_client.delete(
            f"/api/v2/playout-history-metadata/{metadata.id}",
        )
        assert response.status_code == 403
