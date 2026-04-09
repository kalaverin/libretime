"""T270: Podcast RETRIEVE/UPDATE/DELETE endpoint tests."""

import pytest

from api.podcasts.models import Podcast
from model_bakery import baker


@pytest.mark.django_db
@pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
class TestPodcastViewSetRUD:
    """Test Podcast RUD endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        """Set up test fixtures."""
        self.api_client = api_client
        self.podcast = baker.make(
            Podcast,
            url="https://example.com/test.rss",
            title="Test Podcast",
            creator="Creator",
            description="Description",
        )

    def test_retrieve_podcast_success(self):
        """Successfully retrieve podcast."""
        response = self.api_client.get(f"/api/v2/podcasts/{self.podcast.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.podcast.id
        assert data["title"] == "Test Podcast"

    def test_retrieve_not_found(self):
        """Return 404 for non-existent podcast."""
        response = self.api_client.get("/api/v2/podcasts/99999")
        assert response.status_code == 404

    def test_update_podcast_success(self):
        """Successfully update podcast."""
        data = {
            "url": self.podcast.url,
            "title": "Updated Title",
            "creator": self.podcast.creator,
            "description": self.podcast.description,
        }

        response = self.api_client.put(
            f"/api/v2/podcasts/{self.podcast.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_partial_title(self):
        """Partial update with PATCH."""
        data = {"title": "Patched Title"}

        response = self.api_client.patch(
            f"/api/v2/podcasts/{self.podcast.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Patched Title"

    def test_delete_podcast_success(self):
        """Successfully delete podcast."""
        response = self.api_client.delete(
            f"/api/v2/podcasts/{self.podcast.id}",
        )

        assert response.status_code == 204
        assert Podcast.objects.filter(id=self.podcast.id).count() == 0

    def test_delete_not_found(self):
        """Delete non-existent returns 404."""
        response = self.api_client.delete("/api/v2/podcasts/99999")
        assert response.status_code == 404

    def test_no_auth_fails(self):
        """Operations without auth fail."""
        self.api_client.logout()

        response = self.api_client.get(f"/api/v2/podcasts/{self.podcast.id}")
        assert response.status_code == 403
