"""T273-T274: StationPodcast endpoint tests."""

import pytest

from api.podcasts.models import Podcast, StationPodcast
from model_bakery import baker


@pytest.mark.django_db
@pytest.mark.xfail(
    reason="T340: Podcast owner field DB schema mismatch",
    strict=False,
)
class TestStationPodcastViewSet:
    """Test StationPodcast LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        """Set up test fixtures."""
        self.api_client = api_client
        self.user = admin_user
        self.podcast = baker.make(
            Podcast,
            url="https://example.com/test.rss",
            title="Test Podcast",
        )
        self.station = baker.make(StationPodcast, podcast=self.podcast)

    def test_list_station_podcasts(self):
        """LIST station podcasts."""
        response = self.api_client.get("/api/v2/station-podcasts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_create_station_podcast(self):
        """CREATE station podcast."""
        new_podcast = baker.make(
            Podcast,
            url="https://example.com/new.rss",
            title="New",
        )
        data = {"podcast": new_podcast.id}

        response = self.api_client.post(
            "/api/v2/station-podcasts",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["podcast"] == new_podcast.id

    def test_retrieve_station_podcast(self):
        """RETRIEVE station podcast."""
        response = self.api_client.get(
            f"/api/v2/station-podcasts/{self.station.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.station.id

    def test_delete_station_podcast(self):
        """DELETE station podcast."""
        response = self.api_client.delete(
            f"/api/v2/station-podcasts/{self.station.id}",
        )
        assert response.status_code == 204
        assert StationPodcast.objects.filter(id=self.station.id).count() == 0

    def test_no_auth_fails(self):
        """Operations without auth fail."""
        self.api_client.logout()
        response = self.api_client.get("/api/v2/station-podcasts")
        assert response.status_code == 403
