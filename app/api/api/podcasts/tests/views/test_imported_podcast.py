"""T275-T276: ImportedPodcast endpoint tests."""

import pytest

from api.podcasts.models import ImportedPodcast, Podcast
from model_bakery import baker


@pytest.mark.django_db
class TestImportedPodcastViewSet:
    """Test ImportedPodcast LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

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
        self.imported = baker.make(
            ImportedPodcast,
            podcast=self.podcast,
            override_album=True,
            auto_ingest=True,
        )

    def test_list_imported_podcasts(self):
        """LIST imported podcasts."""
        response = self.api_client.get("/api/v2/imported-podcasts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_create_imported_podcast(self):
        """CREATE imported podcast."""
        new_podcast = baker.make(
            Podcast,
            url="https://example.com/new.rss",
            title="New",
        )
        data = {
            "podcast": new_podcast.id,
            "override_album": False,
            "auto_ingest": False,
        }

        response = self.api_client.post(
            "/api/v2/imported-podcasts",
            data,
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["podcast"] == new_podcast.id
        assert data["override_album"] is False

    def test_retrieve_imported_podcast(self):
        """RETRIEVE imported podcast."""
        response = self.api_client.get(
            f"/api/v2/imported-podcasts/{self.imported.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.imported.id
        assert data["override_album"] is True

    def test_update_auto_ingest(self):
        """UPDATE auto_ingest flag."""
        data = {
            "podcast": self.podcast.id,
            "override_album": self.imported.override_album,
            "auto_ingest": False,
        }

        response = self.api_client.put(
            f"/api/v2/imported-podcasts/{self.imported.id}",
            data,
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["auto_ingest"] is False

    def test_delete_imported_podcast(self):
        """DELETE imported podcast."""
        response = self.api_client.delete(
            f"/api/v2/imported-podcasts/{self.imported.id}",
        )
        assert response.status_code == 204
        assert ImportedPodcast.objects.filter(id=self.imported.id).count() == 0

    def test_no_auth_fails(self):
        """Operations without auth fail."""
        self.api_client.logout()
        response = self.api_client.get("/api/v2/imported-podcasts")
        assert response.status_code == 403
