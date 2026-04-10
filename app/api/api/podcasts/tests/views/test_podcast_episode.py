"""T271-T272: PodcastEpisode endpoint tests."""

import pytest

from api.podcasts.models import Podcast, PodcastEpisode
from api.storage.models import File
from model_bakery import baker
from sdk.datetime import format_datetime

from sdk import now


@pytest.mark.django_db
class TestPodcastEpisodeViewSet:
    """Test PodcastEpisode LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

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
        self.file = baker.make(File, mime="audio/mp3", owner=self.user)
        self.episode = baker.make(
            PodcastEpisode,
            podcast=self.podcast,
            file=self.file,
            published_at=format_datetime(now()),
            download_url="https://example.com/episode.mp3",
            episode_guid="guid-123",
            episode_title="Episode Title",
            episode_description="Episode Description",
        )

    def test_list_episodes(self):
        response = self.api_client.get("/api/v2/podcast-episodes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_no_auth_fails(self):
        self.api_client.logout()
        response = self.api_client.get("/api/v2/podcast-episodes")
        assert response.status_code == 403

    def test_create_episode_success(self):
        data = {
            "podcast": self.podcast.id,
            "file": self.file.id,
            "published_at": format_datetime(now()),
            "download_url": "https://example.com/new.mp3",
            "episode_guid": "guid-new",
            "episode_title": "New Episode",
            "episode_description": "New Description",
        }
        response = self.api_client.post(
            "/api/v2/podcast-episodes",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["episode_title"] == "New Episode"

    def test_create_no_auth_fails(self):
        self.api_client.logout()
        data = {"podcast": self.podcast.id, "episode_title": "Test"}
        response = self.api_client.post(
            "/api/v2/podcast-episodes",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_retrieve_episode_success(self):
        response = self.api_client.get(
            f"/api/v2/podcast-episodes/{self.episode.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.episode.id
        assert data["episode_title"] == "Episode Title"

    def test_update_episode_success(self):
        data = {
            "podcast": self.podcast.id,
            "episode_title": "Updated Title",
            "episode_description": self.episode.episode_description,
            "download_url": self.episode.download_url,
            "episode_guid": self.episode.episode_guid,
            "published_at": format_datetime(now()),
        }
        response = self.api_client.put(
            f"/api/v2/podcast-episodes/{self.episode.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["episode_title"] == "Updated Title"

    def test_delete_episode_success(self):
        response = self.api_client.delete(
            f"/api/v2/podcast-episodes/{self.episode.id}",
        )
        assert response.status_code == 204
        assert PodcastEpisode.objects.filter(id=self.episode.id).count() == 0
